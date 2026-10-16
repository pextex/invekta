"""Import the actual engine with provider URI formats, without making a connection."""
import os
from pathlib import Path
import subprocess
import sys

import pytest


@pytest.mark.parametrize("scheme", ["postgres", "postgresql", "postgresql+psycopg"])
def test_provider_uri_uses_locked_psycopg_and_preserves_tls(scheme):
    # Reserved .invalid host and placeholder credentials, never a real database.
    env = {**os.environ, "DATABASE_URL": scheme + "://test:placeholder@database.invalid/crm_test?sslmode=require"}
    result = subprocess.run([sys.executable, "-c", '''
from app.db import engine, url
assert engine.dialect.name == 'postgresql' and engine.dialect.driver == 'psycopg'
assert url.query['sslmode'] == 'require'
assert url.host == 'database.invalid' and url.database == 'crm_test'
assert url.password == 'placeholder'
engine.dispose()
'''], cwd=Path(__file__).resolve().parents[1], env=env, capture_output=True, text=True)
    assert result.returncode == 0, "Provider URI configuration failed; private output suppressed."
