import hashlib
import hmac
import secrets
from datetime import datetime, timezone
from urllib.parse import urlsplit
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


def _valid_origin(value: str) -> bool:
    if value != value.strip() or any(character.isspace() for character in value):
        return False
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        return False
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path
        or parsed.query
        or parsed.fragment
    ):
        return False
    if parsed.scheme == "http" and parsed.hostname.lower() not in {
        "localhost",
        "127.0.0.1",
        "::1",
    }:
        return False
    return port is None or 1 <= port <= 65535


def require_origin(request: Request):
    origin = request.headers.get("origin")
    if not origin or origin == "null" or not _valid_origin(origin):
        raise HTTPException(403, "Nedozvoljeno poreklo zahteva.")
    if origin in get_settings().allowed_origins:
        return
    # WebDev Preview rebases Host to the internal listener, so do not derive
    # the public origin from request.url/Host. Browser Fetch Metadata is
    # forbidden to page JavaScript: accept only a syntactically valid explicit
    # origin paired with same-origin, never the weaker same-site value.
    if request.headers.get("sec-fetch-site") == "same-origin":
        return
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
    if member is None or not member.enabled:
        raise HTTPException(403, "Nemate pristup ovoj poslovnoj jedinici.")
    return member
