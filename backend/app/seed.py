"""Explicit, idempotent development-only seed. Never runs during startup."""

import os
import sys
from getpass import getpass
from sqlalchemy import delete, select
from .db import SessionLocal
from .models import (
    BusinessUnit,
    Company,
    Contact,
    Opportunity,
    LoginSession,
    Membership,
    User,
)
from .security import hash_password


def main():
    password = os.environ.get("CRM_DEMO_PASSWORD", "")
    if not password and sys.stdin.isatty():
        password = getpass("Lozinka demo naloga (najmanje 12 znakova): ")
    if len(password) < 12:
        raise SystemExit(
            "Postavite CRM_DEMO_PASSWORD (najmanje 12 znakova); vrednost se ne prikazuje."
        )
    with SessionLocal.begin() as db:
        user = db.scalar(select(User).where(User.username == "demo"))
        if user is None:
            user = User(
                username="demo",
                name="Demo menadžer",
                password_hash=hash_password(password),
            )
            db.add(user)
            db.flush()
        elif "--reset-password" in sys.argv:
            user.password_hash = hash_password(password)
            db.execute(delete(LoginSession).where(LoginSession.user_id == user.id))
        for code, name in [("LUU", "LUU"), ("INVEKTA", "Invekta")]:
            unit = db.scalar(select(BusinessUnit).where(BusinessUnit.code == code))
            if unit is None:
                unit = BusinessUnit(code=code, name=name)
                db.add(unit)
                db.flush()
            if db.get(Membership, (user.id, unit.id)) is None:
                db.add(
                    Membership(
                        user_id=user.id, business_unit_id=unit.id, role="manager"
                    )
                )
                db.flush()
            for company_name, city, sector, value, stage in (
                [
                    ("Demo Hotel Dunav", "Beograd", "Hotelijerstvo", 185000, "Ponuda"),
                    ("Demo Studio Javor", "Novi Sad", "Kancelarije", 72000, "Kontakt"),
                    ("Demo Restoran Lipa", "Niš", "Ugostiteljstvo", 96000, "Pregovori"),
                ]
                if code == "LUU"
                else [
                    (
                        "Demo Poslovni centar",
                        "Beograd",
                        "Poslovni objekti",
                        420000,
                        "Ponuda",
                    ),
                    ("Demo Park Sever", "Novi Sad", "Industrija", 280000, "Kontakt"),
                    ("Demo Tržni centar", "Niš", "Maloprodaja", 350000, "Pregovori"),
                ]
            ):
                existing = db.scalar(
                    select(Company).where(
                        Company.business_unit_id == unit.id,
                        Company.name == company_name,
                    )
                )
                if existing is None:
                    existing = Company(
                        business_unit_id=unit.id,
                        owner_id=user.id,
                        name=company_name,
                        city=city,
                        sector=sector,
                        potential_value=value,
                        stage=stage,
                        is_demo=True,
                    )
                    db.add(existing)
                    db.flush()
                if existing.is_demo:
                    if (
                        db.scalar(
                            select(Contact).where(Contact.company_id == existing.id)
                        )
                        is None
                    ):
                        db.add(
                            Contact(
                                company_id=existing.id,
                                business_unit_id=unit.id,
                                name="Demo kontakt — " + company_name,
                                position="Demonstracioni kontakt",
                                email=f"demo-{existing.id}@example.com",
                                is_demo=True,
                            )
                        )
                    if (
                        db.scalar(
                            select(Opportunity).where(
                                Opportunity.company_id == existing.id
                            )
                        )
                        is None
                    ):
                        db.add(
                            Opportunity(
                                company_id=existing.id,
                                business_unit_id=unit.id,
                                title="Demo prilika — " + company_name,
                                amount=value,
                                stage="Kontaktiran" if stage == "Kontakt" else stage,
                                is_demo=True,
                            )
                        )
    print("Demo podaci su pripremljeni. Postojeći nalozi i zapisi nisu menjani.")


if __name__ == "__main__":
    main()
