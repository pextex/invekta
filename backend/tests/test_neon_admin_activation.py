"""The one-time helper must target only the new DB and preserve credential privacy."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import sys

import pytest

spec = importlib.util.spec_from_file_location("activate_neon_admin", Path(__file__).resolve().parents[2] / "scripts/activate_neon_admin.py")
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


def test_activation_url_requires_expected_direct_database_and_tls():
    host = "database.example.invalid"
    valid = f"postgresql://owner:placeholder@{host}/crm?sslmode=require"
    assert helper.activation_url(valid, host, "crm") == valid.replace("postgresql://", "postgresql+psycopg://")
    for value in (
        "not-a-url", valid.replace(host, "localhost"), valid.replace("/crm?", "/other?"),
        valid.replace("postgresql://", "mysql://"), valid.replace("sslmode=require", "sslmode=disable"),
        valid.replace(host, host + ":6432"),
    ):
        with pytest.raises(ValueError) as error:
            helper.activation_url(value, host, "crm")
        assert "placeholder" not in str(error.value)


def test_pooler_is_normalized_only_for_the_recorded_production_endpoint():
    host = "production.example.invalid"
    pooler = "production-pooler.example.invalid"
    value = f"postgresql://owner:placeholder@{pooler}/crm?sslmode=require&channel_binding=require"
    result = helper.activation_url(value, host, "crm", pooler)
    assert helper.make_url(result) == helper.make_url(value).set(host=host, drivername="postgresql+psycopg")
    with pytest.raises(ValueError, match="endpoint nije CRM production"):
        helper.activation_url(value.replace(pooler, "preview-pooler.example.invalid"), host, "crm", pooler)


@pytest.mark.parametrize("wrapper", ["{}", "'{}'", '"{}"', "psql '{}'", 'psql "{}"'])
def test_connection_copy_formats_are_parsed_without_running_a_shell(wrapper):
    host = "production.example.invalid"
    value = f"postgresql://owner:placeholder@{host}/crm?sslmode=require"
    assert helper.activation_url(wrapper.format(value), host, "crm") == value.replace("postgresql://", "postgresql+psycopg://")


@pytest.mark.parametrize(("value", "message"), [
    ("postgresql://private:secret@other.example.invalid/crm?sslmode=require", "endpoint nije CRM production"),
    ("postgresql://private:secret@production.example.invalid/neondb?sslmode=require", "Database: crm"),
    ("postgresql://private:secret@production.example.invalid:6432/crm?sslmode=require", "port 5432"),
    ("postgresql://private:secret@production.example.invalid:bad/crm?sslmode=require", "Neispravan connection URL"),
    ("psql 'postgresql://private:secret@production.example.invalid/crm' ; echo private", "Neispravan connection URL"),
])
def test_input_errors_explain_the_field_without_disclosing_values(value, message):
    with pytest.raises(ValueError, match=message) as error:
        helper.activation_url(value, "production.example.invalid", "crm")
    assert "private" not in str(error.value) and "secret" not in str(error.value)
    assert value not in str(error.value)


@pytest.mark.parametrize("returncode", [0, 1])
def test_helper_uses_existing_activation_and_never_echoes_credentials(monkeypatch, capsys, tmp_path, returncode):
    config = tmp_path / "neon.json"
    config.write_text('{"production":{"direct_host":"database.example.invalid"},"database_name":"crm"}')
    monkeypatch.setattr(helper, "DEPLOYMENT", config)
    monkeypatch.setattr(sys, "argv", ["activate", "--email", "owner@example.com", "--name", "Owner"])
    monkeypatch.setattr(sys, "stdin", SimpleNamespace(isatty=lambda: True))
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    monkeypatch.setenv("CRM_ACCOUNT_PASSWORD", "inherited-private-value")
    url = "postgresql://owner:placeholder@database.example.invalid/crm?sslmode=require"
    monkeypatch.setattr(helper, "getpass", lambda prompt: url)
    calls = []

    def run(command, **kwargs):
        calls.append((command, kwargs))
        assert kwargs["env"]["DATABASE_URL"].startswith("postgresql+psycopg://")
        assert "CRM_ACCOUNT_PASSWORD" not in kwargs["env"]
        assert "placeholder" not in " ".join(command)
        return SimpleNamespace(returncode=returncode, stdout="private upstream output", stderr="private upstream output")

    monkeypatch.setattr(helper.subprocess, "run", run)
    assert helper.main() == (0 if returncode == 0 else 1)
    assert len(calls) == 1 and calls[0][0][1:3] == ["-m", "app.bootstrap_admin"]
    assert "--activate" in calls[0][0]
    printed = capsys.readouterr().out
    assert all(value not in printed for value in ("placeholder", "private upstream", "inherited-private-value"))


def test_noninteractive_invocation_does_not_read_or_send_credentials(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["activate", "--email", "owner@example.com", "--name", "Owner"])
    monkeypatch.setattr(sys, "stdin", SimpleNamespace(isatty=lambda: False))

    def forbidden(*args, **kwargs):
        raise AssertionError("No credential input or database call outside a private terminal")

    monkeypatch.setattr(helper, "getpass", forbidden)
    monkeypatch.setattr(helper.subprocess, "run", forbidden)
    assert helper.main() == 2
    assert "interaktivnom terminalu" in capsys.readouterr().out
