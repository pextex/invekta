"""Explicitly provision or activate the one-time platform-owner account."""

import argparse
import os
import secrets
from getpass import getpass
from pydantic import EmailStr, TypeAdapter
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from .db import SessionLocal
from .models import BusinessUnit, User, Membership, LoginSession
from .security import hash_password

UNIT_CODES = {"LUU", "INVEKTA", "CENOBOTS"}


def _business_units(db: Session) -> list[BusinessUnit]:
    # Lock stable rows so concurrent first-admin bootstrap attempts serialize.
    units = list(
        db.scalars(
            select(BusinessUnit)
            .where(BusinessUnit.code.in_(UNIT_CODES))
            .order_by(BusinessUnit.code)
            .with_for_update()
        )
    )
    if {unit.code for unit in units} != UNIT_CODES:
        raise SystemExit("Pokrenite migracije pre kreiranja administratora.")
    return units


def _assert_admin_memberships(
    db: Session, user: User, units: list[BusinessUnit]
) -> None:
    memberships = list(db.scalars(select(Membership).where(Membership.user_id == user.id)))
    by_unit = {membership.business_unit_id: membership for membership in memberships}
    expected_ids = {unit.id for unit in units}
    if set(by_unit) != expected_ids or any(
        membership.role != "admin" or not membership.enabled
        for membership in memberships
    ):
        raise SystemExit("Početni administrator nema tačno potrebna aktivna članstva.")


def _activation_password() -> str:
    password = os.environ.get("CRM_ACCOUNT_PASSWORD")
    if password is None:
        password = getpass("Lozinka administratora (najmanje 12 znakova): ")
        if password != getpass("Ponovite lozinku: "):
            raise SystemExit("Lozinke se ne poklapaju.")
    if not 12 <= len(password) <= 256:
        raise SystemExit("Lozinka mora imati 12–256 znakova.")
    return password


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--activate", action="store_true")
    args = parser.parse_args()
    email = str(TypeAdapter(EmailStr).validate_python(args.email.strip())).lower()  # pyright: ignore[reportArgumentType]
    name = args.name.strip()
    if not name or len(name) > 150 or len(email) > 254:
        raise SystemExit("Proverite ime i email.")

    result = ""
    with SessionLocal.begin() as db:
        user = db.scalar(select(User).where(User.email == email).with_for_update())

        if args.activate:
            if (
                user is None
                or not user.is_platform_admin
                or not user.bootstrap_pending
                or user.active
            ):
                raise SystemExit(
                    "Aktivacija je dozvoljena samo za postojeći neaktivan početni administratorski nalog."
                )
            units = _business_units(db)
            _assert_admin_memberships(db, user, units)
            password = _activation_password()
            user.password_hash = hash_password(password)
            user.active = True
            user.bootstrap_pending = False
            user.version += 1
            db.execute(delete(LoginSession).where(LoginSession.user_id == user.id))
            result = "Početni administrator je aktiviran; ova aktivacija je potrošena."
        elif user is not None:
            if (
                user.is_platform_admin
                and user.bootstrap_pending
                and not user.active
            ):
                units = _business_units(db)
                _assert_admin_memberships(db, user, units)
                result = "Početni administrator već čeka bezbednu aktivaciju; nalog nije menjan."
            else:
                raise SystemExit(
                    "Početni administrator već postoji ili nalog nije podoban za bootstrap."
                )
        else:
            # Acquire the shared tenant-row lock before checking for any admin.
            units = _business_units(db)
            existing_admin = db.scalar(
                select(User.id).where(User.is_platform_admin.is_(True)).limit(1)
            )
            if existing_admin is not None:
                raise SystemExit(
                    "Bootstrap je dozvoljen samo pre kreiranja prvog administratora platforme."
                )
            user = User(
                email=email,
                username="account_" + secrets.token_hex(16),
                name=name,
                active=False,
                is_platform_admin=True,
                bootstrap_pending=True,
                password_hash=hash_password(secrets.token_urlsafe(48)),
            )
            db.add(user)
            db.flush()
            for unit in units:
                db.add(
                    Membership(
                        user_id=user.id,
                        business_unit_id=unit.id,
                        role="admin",
                        enabled=True,
                    )
                )
            result = "Administratorski profil je pripremljen i čeka jednokratnu bezbednu aktivaciju."

    print(result)


if __name__ == "__main__":
    main()
