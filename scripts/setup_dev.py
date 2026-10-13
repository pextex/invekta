"""Prepare private local development configuration; never prints credentials."""
from pathlib import Path
import secrets

root = Path(__file__).resolve().parents[1]
path = root / ".env"
if not path.exists():
    password = secrets.token_hex(24)
    path.write_text(
        f"POSTGRES_PASSWORD={password}\n"
        f"DATABASE_URL=postgresql+psycopg://crm:{password}@127.0.0.1:5432/crm\n"
        "CRM_COOKIE_SECURE=false\n"
        "CRM_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173\n"
    )
    path.chmod(0o600)
    print("Kreirana razvojna .env konfiguracija. Lozinke nisu prikazane.")
else:
    print("Postojeća .env konfiguracija je sačuvana bez izmena.")
