import hashlib
import hmac
import secrets
from datetime import datetime, timezone
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session
from .config import get_settings
from .db import get_db
from .models import LoginSession, Membership, User

COOKIE_NAME = "crm_session"
ITERATIONS = 600_000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt.encode(), ITERATIONS
    ).hex()
    return f"pbkdf2_sha256${ITERATIONS}${salt}${digest}"


def verify_password(password: str, encoded: str) -> bool:
    algorithm, iterations, salt, expected = encoded.split("$")
    if algorithm != "pbkdf2_sha256":
        return False
    actual = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt.encode(), int(iterations)
    ).hex()
    return hmac.compare_digest(actual, expected)


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


# Uniform work for unknown accounts; no real account credentials here.
DUMMY_HASH = hash_password(secrets.token_urlsafe(32))


def require_origin(request: Request):
    # Writes require JSON plus an explicit configured browser origin.
    if request.headers.get("origin") not in get_settings().allowed_origins:
        raise HTTPException(403, "Nedozvoljeno poreklo zahteva.")


def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get(COOKIE_NAME)
    session = db.get(LoginSession, token_hash(token)) if token else None
    if session is None or session.expires_at <= datetime.now(timezone.utc):
        raise HTTPException(401, "Prijavite se da biste nastavili.")
    user = db.get(User, session.user_id)
    if user is None or not user.active:
        raise HTTPException(401, "Prijavite se da biste nastavili.")
    return user


def membership(db: Session, user: User, unit_id: int) -> Membership:
    member = db.get(Membership, (user.id, unit_id))
    if member is None:
        raise HTTPException(403, "Nemate pristup ovoj poslovnoj jedinici.")
    return member
