"""Global user management; organization admin alone does not grant this right."""

import secrets
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)
from sqlalchemy import select, delete, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import BusinessUnit, Membership, User, LoginSession
from ..security import current_user, require_origin, hash_password

router = APIRouter(prefix="/api/admin/users", tags=["Users"])


def administrator(user: User = Depends(current_user)):
    if not user.is_platform_admin:
        raise HTTPException(
            403, "Samo administrator platforme može upravljati korisnicima."
        )
    return user


class Grant(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: Literal["LUU", "INVEKTA", "CENOBOTS"]
    role: Literal["sales", "manager", "admin"]


class Profile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=150)
    active: bool = True
    units: list[Grant] = Field(max_length=3)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("Unesite ime.")
        return value

    @model_validator(mode="after")
    def unique_units(self):
        if len({u.code for u in self.units}) != len(self.units):
            raise ValueError("Firma može biti navedena samo jednom.")
        return self


class CreateProfile(Profile):
    email: EmailStr = Field(max_length=254)
    password: str = Field(min_length=12, max_length=256)


class UpdateProfile(Profile):
    version: int = Field(ge=1)
    password: str | None = Field(default=None, min_length=12, max_length=256)


def output(db, user):
    grants = db.execute(
        select(BusinessUnit.code, Membership.role)
        .join(Membership, Membership.business_unit_id == BusinessUnit.id)
        .where(Membership.user_id == user.id, Membership.enabled.is_(True))
        .order_by(BusinessUnit.id)
    ).all()
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "active": user.active,
        "is_platform_admin": user.is_platform_admin,
        "version": user.version,
        "units": [{"code": code, "role": role} for code, role in grants],
    }


def assign(db, user, grants):
    units = {
        u.code: u
        for u in db.scalars(
            select(BusinessUnit).where(BusinessUnit.code.in_([g.code for g in grants]))
        )
    }
    if len(units) != len(grants):
        raise HTTPException(422, "Firma nije registrovana.")
    # Preserve FK ownership references. A disabled membership denies login and
    # access without deleting customer records owned by this user.
    for member in db.scalars(select(Membership).where(Membership.user_id == user.id)):
        member.enabled = False
    for grant in grants:
        unit = units[grant.code]
        member = db.get(Membership, (user.id, unit.id))
        if member is None:
            member = Membership(
                user_id=user.id, business_unit_id=unit.id, role=grant.role
            )
            db.add(member)
        member.role = grant.role
        member.enabled = True


@router.get("")
def list_users(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    actor: User = Depends(administrator),
    db: Session = Depends(get_db),
):
    users = db.scalars(select(User).order_by(User.id).offset(offset).limit(limit))
    return {
        "total": db.scalar(select(func.count()).select_from(User)),
        "items": [output(db, u) for u in users],
    }


@router.post("", dependencies=[Depends(require_origin)], status_code=201)
def create_user(
    data: CreateProfile,
    actor: User = Depends(administrator),
    db: Session = Depends(get_db),
):
    email = str(data.email).lower()
    user = User(
        email=email,
        username="account_" + secrets.token_hex(16),
        name=data.name,
        password_hash=hash_password(data.password),
        active=data.active,
    )
    db.add(user)
    try:
        db.flush()
        assign(db, user, data.units)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Korisnik sa tom email adresom već postoji.")
    return output(db, user)


@router.patch("/{user_id}", dependencies=[Depends(require_origin)])
def update_user(
    user_id: int,
    data: UpdateProfile,
    actor: User = Depends(administrator),
    db: Session = Depends(get_db),
):
    user = db.scalar(select(User).where(User.id == user_id).with_for_update())
    if user is None:
        raise HTTPException(404, "Korisnik nije pronađen.")
    if user.is_platform_admin:
        raise HTTPException(
            403, "Glavni administratorski nalog ne menja se kroz ovaj ekran."
        )
    if user.version != data.version:
        raise HTTPException(
            409, "Profil je u međuvremenu promenjen. Osvežite spisak korisnika."
        )
    user.name = data.name
    user.active = data.active
    assign(db, user, data.units)
    if data.password is not None:
        user.password_hash = hash_password(data.password)
    user.version += 1
    db.execute(delete(LoginSession).where(LoginSession.user_id == user.id))
    db.commit()
    return output(db, user)
