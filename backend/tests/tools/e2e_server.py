"""Disposable browser-test backend. Never seed or migrate the business database."""

import os
import subprocess
import sys
from uuid import uuid4
import psycopg
from psycopg import sql
from sqlalchemy import create_engine, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
import uvicorn
from app.config import get_settings


def main():
    original = make_url(get_settings().database_url)
    name = f"crm_browser_{uuid4().hex[:12]}_test"
    assert name != original.database and name.endswith("_test")
    target = original.set(database=name)
    admin = target.set(drivername="postgresql", database="postgres").render_as_string(
        hide_password=False
    )
    with psycopg.connect(admin, autocommit=True) as connection:
        connection.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
    os.environ["DATABASE_URL"] = target.render_as_string(hide_password=False)
    os.environ["CRM_COOKIE_SECURE"] = "false"
    get_settings.cache_clear()
    try:
        subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True)
        from app.models import BusinessUnit, Company, Membership, Opportunity, User
        from app.security import hash_password

        engine = create_engine(target)
        with Session(engine) as db:
            units = {u.code: u.id for u in db.scalars(select(BusinessUnit))}
            assert units == {"LUU": 1, "INVEKTA": 2, "CENOBOTS": 3}
            digest = hash_password("Browser-test-only-123!")
            db.add_all(
                [
                    User(
                        id=i,
                        username=n,
                        email=n + "@example.com",
                        name=n.title(),
                        password_hash=digest,
                    )
                    for i, n in enumerate(("sales", "manager", "outsider", "other"), 1)
                ]
            )
            db.flush()
            db.add_all(
                [
                    Membership(user_id=1, business_unit_id=1, role="sales"),
                    Membership(user_id=3, business_unit_id=2, role="sales"),
                    Membership(user_id=4, business_unit_id=1, role="sales"),
                ]
            )
            db.add_all(
                [
                    Membership(user_id=2, business_unit_id=i, role="manager")
                    for i in (1, 2, 3)
                ]
            )
            db.flush()
            db.add_all(
                [
                    Company(
                        id=i,
                        business_unit_id=u,
                        owner_id=o,
                        name=n,
                        city="Beograd",
                        sector="Test",
                    )
                    for i, u, o, n in [
                        (1, 1, 1, "Browser Firma A"),
                        (2, 1, 4, "Browser Firma B"),
                        (3, 2, 3, "Browser Firma C"),
                    ]
                ]
            )
            db.flush()
            db.add_all(
                [
                    Opportunity(
                        id=i,
                        company_id=i,
                        business_unit_id=u,
                        title=n,
                        amount=a,
                        stage=s,
                    )
                    for i, u, n, a, s in [
                        (1, 1, "Browser ponuda", "12500.55", "Ponuda"),
                        (2, 1, "Drugi komercijalista", "200.20", "Ponuda"),
                        (3, 2, "Druga jedinica", "300.30", "Dobijeno"),
                    ]
                ]
            )
            db.commit()
            for table, last in [("companies", 3), ("users", 4), ("opportunities", 3)]:
                db.execute(
                    text(f"SELECT setval('{table}_id_seq', :last, true)"),
                    {"last": last},
                )
            db.commit()
        engine.dispose()
        print("Browser tests: fresh disposable PostgreSQL database ready.", flush=True)
        uvicorn.run("app.main:app", host="127.0.0.1", port=18000, log_level="warning")
    finally:
        from app.db import engine as app_engine

        app_engine.dispose()
        with psycopg.connect(admin, autocommit=True) as connection:
            connection.execute(
                sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(name))
            )


if __name__ == "__main__":
    main()
