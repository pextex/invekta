import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import delete, func, select, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from .access import visible_query
from .api.tasks import router as tasks_router
from .api.sales import router as sales_router
from .api.users import router as users_router
from .api.ai import router as ai_router
from .config import get_settings
from .db import get_db
from .models import Contact, BusinessUnit, Company, LoginAttempt, LoginSession, Membership, User
from .schemas import CompanyCreate, CompanyInput, CompanyOutput, LoginInput
from .security import (
    COOKIE_NAME,
    DUMMY_HASH,
    current_user,
    membership,
    require_origin,
    token_hash,
    verify_password,
)

app = FastAPI(title="LUU × INVEKTA × CENOBOTS CRM", version="0.4.0")

app.include_router(tasks_router)
app.include_router(sales_router)
app.include_router(users_router)
app.include_router(ai_router)


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    # Validation responses must not echo passwords or other submitted values.
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Proverite uneta polja, email, dužinu lozinke i pristup firmama."
        },
    )


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
        db.execute(text("SELECT address, pib FROM companies LIMIT 1"))
        db.execute(text("SELECT changes, amount FROM opportunity_stage_changes LIMIT 1"))
        db.execute(text("SELECT id, due_date FROM tasks LIMIT 1"))
        db.execute(
            text("SELECT 1 FROM ai_drafts LEFT JOIN ai_attempts ON FALSE LIMIT 1")
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
    username = str(data.email or data.username).strip().lower()
    now = datetime.now(timezone.utc)
    count = db.scalar(
        select(func.count())
        .select_from(LoginAttempt)
        .where(
            LoginAttempt.username == username,
            LoginAttempt.attempted_at > now - timedelta(minutes=15),
        )
    ) or 0
    if count >= 5:
        raise HTTPException(429, "Previše pokušaja. Pokušajte ponovo za 15 minuta.")
    user = db.scalar(
        select(User).where(
            User.email == username if data.email else User.username == username
        )
    )
    valid = verify_password(data.password, user.password_hash if user else DUMMY_HASH)
    if not user or not user.active or not valid:
        db.add(LoginAttempt(username=username))
        db.commit()
        raise HTTPException(401, "Pogrešan email ili lozinka.")
    selected_unit = None
    if data.business_unit_code:
        selected_unit = db.scalar(
            select(BusinessUnit).where(BusinessUnit.code == data.business_unit_code)
        )
        if (
            selected_unit is None
            or (member := db.get(Membership, (user.id, selected_unit.id))) is None
            or not member.enabled
        ):
            raise HTTPException(
                403, "Nemate pristup izabranoj kompaniji. Obratite se administratoru."
            )
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
        samesite="none" if get_settings().crm_cookie_secure else "strict",
        path="/api",
    )
    return {"name": user.name, "unit_id": selected_unit.id if selected_unit else None}


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
        samesite="none" if get_settings().crm_cookie_secure else "strict",
    )
    return {"status": "ok"}


@app.get("/api/auth/me")
def me(user: User = Depends(current_user), db: Session = Depends(get_db)):
    units = db.execute(
        select(BusinessUnit, Membership.role)
        .join(Membership, Membership.business_unit_id == BusinessUnit.id)
        .where(Membership.user_id == user.id, Membership.enabled.is_(True))
        .order_by(BusinessUnit.id)
    ).all()
    return {
        "name": user.name,
        "is_platform_admin": user.is_platform_admin,
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
            | Company.address.ilike(pattern, escape="\\")
            | Company.pib.ilike(pattern, escape="\\")
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
    data: CompanyCreate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    membership(db, user, unit_id)
    company = Company(
        **data.model_dump(exclude={"contacts"}), business_unit_id=unit_id, owner_id=user.id, is_demo=False
    )
    db.add(company)
    try:
        db.flush()
        for contact in data.contacts:
            db.add(Contact(**contact.model_dump(), company_id=company.id,
                           business_unit_id=unit_id, is_demo=False))
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


STATIC_DIR = Path(__file__).with_name("static")
if (STATIC_DIR / "index.html").is_file():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="frontend")
