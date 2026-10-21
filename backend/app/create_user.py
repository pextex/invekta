"""Explicit account provisioning with hidden password input."""

import argparse
import os
import secrets
from getpass import getpass
from pydantic import EmailStr, TypeAdapter
from sqlalchemy import select
from .db import SessionLocal
from .models import BusinessUnit, Membership, User
from .security import hash_password


def main():
    parser = argparse.ArgumentParser(description="Create an email login account")
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument(
        "--unit", action="append", choices=["LUU", "INVEKTA", "CENOBOTS"], required=True
    )
    parser.add_argument(
        "--role", choices=["sales", "marketing", "manager", "admin"], default="sales"
    )
    args = parser.parse_args()
    email = str(TypeAdapter(EmailStr).validate_python(args.email.strip())).lower()  # pyright: ignore[reportArgumentType]
    if len(email) > 254 or not args.name.strip() or len(args.name.strip()) > 150:
        raise SystemExit("Proverite email i ime (najviše 150 znakova).")
    password = os.environ.get("CRM_ACCOUNT_PASSWORD")
    if password is None:
        password = getpass("Nova lozinka (najmanje 12 znakova): ")
        if password != getpass("Ponovite lozinku: "):
            raise SystemExit("Lozinke se ne poklapaju.")
    if not 12 <= len(password) <= 256:
        raise SystemExit("Lozinka mora imati 12–256 znakova.")
    with SessionLocal.begin() as db:
        if db.scalar(select(User).where(User.email == email)):
            raise SystemExit("Email već postoji. Postojeći nalog nije promenjen.")
        units = list(
            db.scalars(
                select(BusinessUnit).where(BusinessUnit.code.in_(set(args.unit)))
            )
        )
        if len(units) != len(set(args.unit)):
            raise SystemExit("Nedostaje poslovna jedinica; pokrenite migracije.")
        user = User(
            username="account_" + secrets.token_hex(16),
            email=email,
            name=args.name.strip(),
            password_hash=hash_password(password),
        )
        db.add(user)
        db.flush()
        for unit in units:
            db.add(
                Membership(user_id=user.id, business_unit_id=unit.id, role=args.role)
            )
    print("Nalog je kreiran. Lozinka se ne prikazuje.")


if __name__ == "__main__":
    main()
