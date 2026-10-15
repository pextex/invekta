"""Explicit first-run initialization, allowed only for an empty local database."""

import os
import subprocess
import sys

from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import SQLAlchemyError
from dev_database import ROOT, local_url


def initialize_empty_database():
    url = local_url()  # Reject managed/remote databases before connecting.
    engine = create_engine(url, connect_args={"connect_timeout": 5})
    try:
        with engine.connect() as connection:
            connection.exec_driver_sql("SET TRANSACTION READ ONLY")
            inspector = inspect(connection)
            for schema in inspector.get_schema_names():
                if schema == "information_schema" or schema.startswith("pg_"):
                    continue
                if (inspector.get_table_names(schema=schema)
                        or inspector.get_view_names(schema=schema)
                        or inspector.get_materialized_view_names(schema=schema)
                        or inspector.get_sequence_names(schema=schema)):
                    raise RuntimeError(
                        "Baza nije prazna. Inicijalizacija je odbijena; ništa nije migrirano. "
                        "Postojeću bazu prvo pregledajte i napravite backup. Ne koristite reset ili stamp."
                    )
    except SQLAlchemyError:
        raise RuntimeError("Provera prazne lokalne baze nije uspela; inicijalizacija nije pokrenuta.") from None
    finally:
        engine.dispose()
    print("Potvrđena je prazna lokalna PostgreSQL baza. Eksplicitno kreiram CRM šemu bez seed-a.", flush=True)
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=ROOT / "backend",
        env={**os.environ, "DATABASE_URL": url.render_as_string(hide_password=False)},
        check=True,
    )
    print("CRM šema je spremna. Korisnički nalozi i klijenti nisu dodavani. Uputstvo: docs/codespaces.md.", flush=True)


if __name__ == "__main__":
    try:
        if sys.argv[1:]:
            raise RuntimeError("Upotreba: backend/.venv/bin/python scripts/init_dev_database.py")
        initialize_empty_database()
    except RuntimeError as error:
        sys.exit(str(error))
    except subprocess.CalledProcessError as error:
        sys.exit(error.returncode)
