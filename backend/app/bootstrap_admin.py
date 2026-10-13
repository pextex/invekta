"""Explicitly provision or activate the platform owner, never on startup."""

import argparse
import os
import secrets
from getpass import getpass
from pydantic import EmailStr, TypeAdapter
from sqlalchemy import select, delete
from .db import SessionLocal
from .models import BusinessUnit, User, Membership, LoginSession
from .security import hash_password


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--activate", action="store_true")
    args = parser.parse_args()
    email = str(TypeAdapter(EmailStr).validate_python(args.email.strip())).lower()
    if not args.name.strip() or len(args.name.strip()) > 150 or len(email) > 254:
        raise SystemExit("Proverite ime i email.")
    password = None
    if args.activate:
        password = os.environ.get("CRM_ACCOUNT_PASSWORD")
        if password is None:
            password = getpass("Lozinka administratora (najmanje 12 znakova): ")
            if password != getpass("Ponovite lozinku: "):
                raise SystemExit("Lozinke se ne poklapaju.")
        if not 12 <= len(password) <= 256:
            raise SystemExit("Lozinka mora imati 12–256 znakova.")
    with SessionLocal.begin() as db:
        units = list(
            db.scalars(
                select(BusinessUnit).where(
                    BusinessUnit.code.in_(["LUU", "INVEKTA", "CENOBOTS"])
                )
            )
        )
        if len(units) != 3:
            raise SystemExit("Pokrenite migracije pre kreiranja administratora.")
        user = db.scalar(select(User).where(User.email == email).with_for_update())
        if user is None:
            user = User(
                email=email,
                username="account_" + secrets.token_hex(16),
                name=args.name.strip(),
                active=False,
                password_hash=hash_password(secrets.token_urlsafe(48)),
            )
            db.add(user)
            db.flush()
        user.is_platform_admin = True
        for unit in units:
            member = db.get(Membership, (user.id, unit.id))
            if member is None:
                member = Membership(
                    user_id=user.id, business_unit_id=unit.id, role="admin"
                )
                db.add(member)
            member.role = "admin"
            member.enabled = True
        if password is not None:
            user.password_hash = hash_password(password)
            user.active = True
        user.version += 1
        db.execute(delete(LoginSession).where(LoginSession.user_id == user.id))
    print(
        "Administrator je aktiviran."
        if args.activate
        else "Administratorski profil je pripremljen; novi nalog čeka bezbedno postavljanje lozinke."
    )


if __name__ == "__main__":
    main()
