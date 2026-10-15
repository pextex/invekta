"""Read-only local database guard, run using the locked backend environment."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError
from app.config import get_settings


def local_url():
    try:
        url = make_url(get_settings().database_url)
    except Exception:
        raise RuntimeError("Proverite lokalnu DATABASE_URL konfiguraciju; vrednost nije prikazana.") from None
    if (url.drivername != "postgresql+psycopg" or url.host not in ("127.0.0.1", "localhost")
            or url.port not in (None, 5432) or not url.database):
        raise RuntimeError(
            "Razvojna komanda dozvoljava samo lokalni PostgreSQL (127.0.0.1/localhost:5432). "
            "Managed/produkcijska baza nije dozvoljena. Postojeći .env nije promenjen."
        )
    return url


def check_schema(url):
    config = Config(str(ROOT / "backend/alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "backend/alembic"))
    script = ScriptDirectory.from_config(config)
    engine = create_engine(url, connect_args={"connect_timeout": 5})
    try:
        with engine.connect() as connection:
            # No Alembic upgrade, stamp, DDL, seed or writes here.
            connection.exec_driver_sql("SET TRANSACTION READ ONLY")
            current = MigrationContext.configure(connection).get_current_heads()
            if set(current) != set(script.get_heads()):
                print("Baza zahteva pregled migracija. Ništa nije migrirano.", flush=True)
                print("Trenutna revizija: " + (", ".join(current) or "bez Alembic revizije"), flush=True)
                try:
                    for revision in script.iterate_revisions(script.get_heads(), current):
                        print(f"  {revision.revision}: {revision.doc}", flush=True)
                except Exception:
                    print("Revizija nije prepoznata; proverite poreklo baze i granu koda.", flush=True)
                if not current:
                    print("Za novu praznu bazu postoji odvojena ručna komanda iz korena: backend/.venv/bin/python scripts/init_dev_database.py", flush=True)
                    print("Ta komanda odbija svaku bazu sa postojećim tabelama/pogledima/sekvencama.", flush=True)
                raise RuntimeError(
                    "Pokretanje je zaustavljeno. Pregledajte migracije i napravite backup pre ručnog odobrenog upgrade-a. "
                    "Uputstvo: docs/codespaces.md."
                )
            if not inspect(connection).has_table("users"):
                raise RuntimeError("Nedostaje tabela users uprkos Alembic reviziji; proverite šemu baze.")
    except SQLAlchemyError:
        raise RuntimeError("Lokalna baza nije dostupna. Proverite Docker i postojeću lokalnu konfiguraciju; vrednosti nisu prikazane.") from None
    finally:
        engine.dispose()
    print("Lokalni PostgreSQL: šema odgovara kodu; migracije i seed nisu pokretani.", flush=True)


if __name__ == "__main__":
    try:
        url = local_url()
        if sys.argv[1:] == ["check"]:
            check_schema(url)
        elif sys.argv[1:] != ["validate"]:
            raise RuntimeError("Upotreba: dev_database.py validate|check")
    except RuntimeError as error:
        sys.exit(str(error))
