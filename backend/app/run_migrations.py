"""Serialize startup migrations across overlapping or autoscaled instances."""

import subprocess
import sys
from pathlib import Path
from sqlalchemy import text
from .db import engine

LOCK_NAME = "invekta_crm_schema"
LOCK_KEY = 8_274_105_169
LOCK_WAIT_SECONDS = 120


def acquire(connection):
    if engine.dialect.name == "mysql":
        acquired = connection.scalar(
            text("SELECT GET_LOCK(:lock_name, :timeout)"),
            {"lock_name": LOCK_NAME, "timeout": LOCK_WAIT_SECONDS},
        )
        return acquired == 1
    if engine.dialect.name == "postgresql":
        connection.execute(
            text("SELECT pg_advisory_lock(:lock_key)"), {"lock_key": LOCK_KEY}
        )
        return True
    raise RuntimeError(f"Unsupported migration database: {engine.dialect.name}")


def release(connection):
    if engine.dialect.name == "mysql":
        connection.execute(
            text("SELECT RELEASE_LOCK(:lock_name)"), {"lock_name": LOCK_NAME}
        )
    elif engine.dialect.name == "postgresql":
        connection.execute(
            text("SELECT pg_advisory_unlock(:lock_key)"), {"lock_key": LOCK_KEY}
        )
    connection.commit()


def main():
    working_directory = Path(__file__).resolve().parents[1]
    with engine.connect() as connection:
        if not acquire(connection):
            raise SystemExit("Timed out while waiting for the CRM migration lock.")
        # The MySQL named lock and PostgreSQL session advisory lock survive this
        # transaction boundary while Alembic uses its own database connection.
        connection.commit()
        try:
            subprocess.run(
                [sys.executable, "-m", "alembic", "upgrade", "head"],
                cwd=working_directory,
                check=True,
            )
        finally:
            release(connection)


if __name__ == "__main__":
    main()
