"""Activate the pending CRM owner with masked inputs, without saving credentials."""
import argparse
from getpass import getpass
import json
import os
from pathlib import Path
import subprocess
import sys

from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

ROOT = Path(__file__).resolve().parents[1]
DEPLOYMENT = ROOT / "deployment/neon.json"


def activation_url(value: str, host: str, database: str) -> str:
    try:
        url = make_url(value.strip())
    except (ArgumentError, ValueError, TypeError):
        raise ValueError("Neispravan connection URL; vrednost nije prikazana.") from None
    if (url.drivername not in ("postgres", "postgresql", "postgresql+psycopg")
            or url.host != host or url.database != database or url.port not in (None, 5432)):
        raise ValueError("Koristite direktnu vezu nove CRM production baze iz Neon projekta invekta-crm.")
    if url.query.get("sslmode") not in ("require", "verify-ca", "verify-full"):
        raise ValueError("Neon veza mora zadržati TLS (sslmode=require ili strože).")
    return url.set(drivername="postgresql+psycopg").render_as_string(hide_password=False)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", required=True)
    args = parser.parse_args()
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        print("Pokrenite komandu u privatnom interaktivnom terminalu, zbog skrivenog unosa.")
        return 2
    config = json.loads(DEPLOYMENT.read_text(encoding="utf-8"))
    print("U Neon Console izaberite invekta-crm → production → Connect i direktnu (ne pooled) vezu.")
    try:
        url = activation_url(getpass("Neon connection URL (skriven unos): "),
                             config["production"]["direct_host"], config["database_name"])
    except ValueError as error:
        print(str(error))
        return 2
    env = {**os.environ, "DATABASE_URL": url}
    # Always ask the owner for a new password; never reuse an unknown inherited value.
    env.pop("CRM_ACCOUNT_PASSWORD", None)
    print("Slede nova lozinka i potvrda kroz postojeću CRM aktivaciju (najmanje 12 znakova).", flush=True)
    result = subprocess.run([
        sys.executable, "-m", "app.bootstrap_admin", "--email", args.email,
        "--name", args.name, "--activate",
    ], cwd=ROOT / "backend", env=env, capture_output=True, text=True)
    # Never print a driver traceback or raw subprocess output with connection details.
    if result.returncode:
        print("Aktivacija nije završena. Proverite vezu i pending nalog; aktivnom nalogu se lozinka ne resetuje ovom komandom.")
        return 1
    print("Administrator je aktiviran. Connection URL i lozinka nisu sačuvani u fajl ili prikazani.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyboardInterrupt, EOFError):
        raise SystemExit("Aktivacija je prekinuta.") from None
