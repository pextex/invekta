"""Run migrations and tests against a separate PostgreSQL test database."""

import os
import subprocess
import sys
import psycopg
from psycopg import sql
from sqlalchemy.engine import make_url
from .config import get_settings


def main():
    original = make_url(get_settings().database_url)
    target = (
        make_url(os.environ["CRM_TEST_DATABASE_URL"])
        if os.environ.get("CRM_TEST_DATABASE_URL")
        else original.set(database=original.database + "_test")
    )
    if (
        not target.database
        or not target.database.endswith("_test")
        or target == original
    ):
        raise SystemExit("Testovi zahtevaju izdvojenu bazu sa sufiksom _test.")
    admin_url = target.set(
        drivername="postgresql", database="postgres"
    ).render_as_string(hide_password=False)
    with psycopg.connect(admin_url, autocommit=True) as connection:
        exists = connection.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s", (target.database,)
        ).fetchone()
        if not exists:
            connection.execute(
                sql.SQL("CREATE DATABASE {}").format(sql.Identifier(target.database))
            )
    url = target.render_as_string(hide_password=False)
    settings = {
        **os.environ,
        "DATABASE_URL": url,
        "CRM_TEST_DATABASE_URL": url,
        "CRM_COOKIE_SECURE": "false",
    }
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"], env=settings, check=True
    )
    subprocess.run([sys.executable, "-m", "pytest", "-q"], env=settings, check=True)


if __name__ == "__main__":
    main()
