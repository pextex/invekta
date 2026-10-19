"""Self-service profile. Identity is always taken from the authenticated session."""
import re
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import User, LoginSession, LoginAttempt
from ..security import COOKIE_NAME, current_user, require_origin, token_hash, hash_password, verify_password

router = APIRouter(prefix="/api/profile", tags=["My profile"])


class PhoneInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    phone: str | None = Field(default=None, max_length=40)

    @field_validator("phone")
    @classmethod
    def valid_phone(cls, value):
        if value is None or not value.strip():
            return None
        value = value.strip()
        if not re.fullmatch(r"\+?[0-9 ()/.-]+", value) or not 6 <= len(re.sub(r"\D", "", value)) <= 15:
            raise ValueError("Unesite ispravan broj telefona.")
        return value


class PasswordInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    current_password: str = Field(min_length=1, max_length=256)
    new_password: str = Field(min_length=12, max_length=256)
    confirm_password: str = Field(min_length=12, max_length=256)

    @model_validator(mode="after")
    def confirmed(self):
        if self.new_password != self.confirm_password or self.new_password == self.current_password:
            raise ValueError("Potvrdite novu lozinku različitu od trenutne.")
        return self


def output(user):
    return {"name": user.name, "email": user.email, "phone": user.phone}


@router.get("")
def read_profile(user: User = Depends(current_user)):
    return output(user)


@router.patch("", dependencies=[Depends(require_origin)])
def update_phone(data: PhoneInput, user: User = Depends(current_user), db: Session = Depends(get_db)):
    # Serialize with administrative updates without writing role or account fields.
    user = db.scalar(select(User).where(User.id == user.id).with_for_update().execution_options(populate_existing=True))
    if user is None or not user.active:
        raise HTTPException(401, "Prijavite se da biste nastavili.")
    user.phone = data.phone
    user.version += 1
    db.commit()
    return output(user)


@router.post("/password", dependencies=[Depends(require_origin)])
def change_password(data: PasswordInput, request: Request, user: User = Depends(current_user), db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.id == user.id).with_for_update().execution_options(populate_existing=True))
    if user is None or not user.active:
        raise HTTPException(401, "Prijavite se da biste nastavili.")
    key = f"profile-password:{user.id}"
    now = datetime.now(timezone.utc)
    attempts = db.scalar(select(func.count()).select_from(LoginAttempt).where(
        LoginAttempt.username == key, LoginAttempt.attempted_at > now - timedelta(minutes=15))) or 0
    if attempts >= 5:
        raise HTTPException(429, "Previše pokušaja. Pokušajte ponovo za 15 minuta.")
    if not verify_password(data.current_password, user.password_hash):
        db.add(LoginAttempt(username=key))
        db.commit()
        raise HTTPException(400, "Trenutna lozinka nije ispravna.")
    user.password_hash = hash_password(data.new_password)
    user.version += 1
    # Preserve this session and revoke other browsers/devices after a password change.
    current = token_hash(request.cookies.get(COOKIE_NAME, ""))
    db.execute(delete(LoginSession).where(LoginSession.user_id == user.id, LoginSession.token_hash != current))
    db.execute(delete(LoginAttempt).where(LoginAttempt.username == key))
    db.commit()
    return {"status": "ok"}
