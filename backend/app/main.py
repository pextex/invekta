import secrets
from datetime import datetime, timedelta, timezone
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from sqlalchemy import delete, func, select, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from .access import visible_query
from .api.sales import router as sales_router
from .config import get_settings
from .db import get_db
from .models import BusinessUnit, Company, LoginAttempt, LoginSession, Membership, User
from .schemas import CompanyInput, CompanyOutput, LoginInput
from .security import (
    COOKIE_NAME,
    DUMMY_HASH,
    current_user,
    membership,
    require_origin,
    token_hash,
    verify_password,
)

app = FastAPI(title="LUU × INVEKTA CRM", version="0.3.0")

app.include_router(sales_router)


@app.middleware("http")
async def private_responses(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/ready")
def ready(db: Session = Depends(get_db)):
    try:
        db.execute(
            text(
                "SELECT 1 FROM opportunities LEFT JOIN contacts ON FALSE LEFT JOIN opportunity_stage_changes ON FALSE LIMIT 1"
            )
        )
    except SQLAlchemyError:
        raise HTTPException(503, "Baza ili migracije nisu spremne.")
    return {"status": "ready"}


@app.post("/api/auth/login", dependencies=[Depends(require_origin)])
def login(
    data: LoginInput,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    username = data.username.strip().lower()
    now = datetime.now(timezone.utc)
    count = db.scalar(
        select(func.count())
        .select_from(LoginAttempt)
        .where(
            LoginAttempt.username == username,
            LoginAttempt.attempted_at > now - timedelta(minutes=15),
        )
    )
    if count >= 5:
        raise HTTPException(429, "Previše pokušaja. Pokušajte ponovo za 15 minuta.")
    user = db.scalar(select(User).where(User.username == username))
    valid = verify_password(data.password, user.password_hash if user else DUMMY_HASH)
    if not user or not user.active or not valid:
        db.add(LoginAttempt(username=username))
        db.commit()
        raise HTTPException(401, "Pogrešno korisničko ime ili lozinka.")
    db.execute(
        delete(LoginAttempt).where(
            (LoginAttempt.username == username)
            | (LoginAttempt.attempted_at < now - timedelta(minutes=15))
        )
    )
    db.execute(delete(LoginSession).where(LoginSession.expires_at <= now))
    previous = request.cookies.get(COOKIE_NAME)
    if previous:
        db.execute(
            delete(LoginSession).where(LoginSession.token_hash == token_hash(previous))
        )
    token = secrets.token_urlsafe(32)
    db.add(
        LoginSession(
            token_hash=token_hash(token),
            user_id=user.id,
            expires_at=now + timedelta(hours=8),
        )
    )
    db.commit()
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=8 * 3600,
        httponly=True,
        secure=get_settings().crm_cookie_secure,
        samesite="strict",
        path="/api",
    )
    return {"name": user.name}


@app.post("/api/auth/logout", dependencies=[Depends(require_origin)])
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get(COOKIE_NAME)
    if token:
        db.execute(
            delete(LoginSession).where(LoginSession.token_hash == token_hash(token))
        )
        db.commit()
    response.delete_cookie(
        COOKIE_NAME,
        path="/api",
        secure=get_settings().crm_cookie_secure,
        httponly=True,
        samesite="strict",
    )
    return {"status": "ok"}


@app.get("/api/auth/me")
def me(user: User = Depends(current_user), db: Session = Depends(get_db)):
    units = db.execute(
        select(BusinessUnit, Membership.role)
        .join(Membership, Membership.business_unit_id == BusinessUnit.id)
        .where(Membership.user_id == user.id)
        .order_by(BusinessUnit.id)
    ).all()
    return {
        "name": user.name,
        "units": [
            {"id": unit.id, "code": unit.code, "role": role} for unit, role in units
        ],
    }


@app.get("/api/units/{unit_id}/companies", response_model=list[CompanyOutput])
def list_companies(
    unit_id: int,
    search: str = Query("", max_length=200),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    query = visible_query(db, user, unit_id)
    if search.strip():
        term = (
            search.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        )
        pattern = f"%{term}%"
        query = query.where(
            Company.name.ilike(pattern, escape="\\")
            | Company.city.ilike(pattern, escape="\\")
            | Company.sector.ilike(pattern, escape="\\")
        )
    return db.scalars(query.order_by(Company.name).limit(200)).all()


@app.post(
    "/api/units/{unit_id}/companies",
    response_model=CompanyOutput,
    status_code=201,
    dependencies=[Depends(require_origin)],
)
def create_company(
    unit_id: int,
    data: CompanyInput,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    membership(db, user, unit_id)
    company = Company(
        **data.model_dump(), business_unit_id=unit_id, owner_id=user.id, is_demo=False
    )
    db.add(company)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            409, "Kompanija sa tim nazivom već postoji u ovoj jedinici."
        )
    db.refresh(company)
    return company


@app.patch(
    "/api/units/{unit_id}/companies/{company_id}",
    response_model=CompanyOutput,
    dependencies=[Depends(require_origin)],
)
def update_company(
    unit_id: int,
    company_id: int,
    data: CompanyInput,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    company = db.scalar(
        visible_query(db, user, unit_id).where(Company.id == company_id)
    )
    if company is None:
        raise HTTPException(404, "Kompanija nije pronađena.")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(company, key, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            409, "Kompanija sa tim nazivom već postoji u ovoj jedinici."
        )
    db.refresh(company)
    return company
