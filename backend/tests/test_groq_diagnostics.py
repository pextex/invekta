"""Provider error/privacy regressions; requests are simulated, never sent to Groq."""
import io
import json
from urllib.error import HTTPError, URLError

import pytest

from app import ai_provider, check_ai_connection
from app.config import get_settings
from app.groq_errors import GroqProviderError, classify_http_error


@pytest.fixture
def configured(monkeypatch):
    settings = get_settings().model_copy(update={
        "crm_ai_enabled": True,
        "crm_groq_api_key": "groq-test-placeholder",
        "crm_groq_model": "openai/gpt-oss-120b",
    })
    monkeypatch.setattr(ai_provider, "get_settings", lambda: settings)
    monkeypatch.setattr(check_ai_connection, "get_settings", lambda: settings)
    return settings


@pytest.mark.parametrize("status,body,category,code,format", [
    (401, b'{"error":{"message":"groq-test-placeholder","code":"invalid_api_key"}}', "authentication", None, "json"),
    (403, b'{"error":{"code":"model_permission_blocked_org"}}', "model_permission_blocked_org", "model_permission_blocked_org", "json"),
    (403, b'{"error":{"code":"model_permission_blocked_project"}}', "model_permission_blocked_project", "model_permission_blocked_project", "json"),
    (403, b'<!DOCTYPE html><html>Cloudflare Access denied; Error code: 1010; groq-test-placeholder</html>', "edge_block", "cloudflare_1010", "html"),
    (403, b'error code: 1010', "edge_block", "cloudflare_1010", "text"),
    (403, b'<html>Cloudflare challenge-platform</html>', "edge_block", None, "html"),
    (403, b'<html>Proxy refused; groq-test-placeholder</html>', "forbidden_unknown", None, "html"),
    (403, b'{"error":{"code":"groq-test-placeholder","message":"CRM confidential text"}}', "forbidden_unknown", None, "json"),
    (403, b'{"error":{"code":["model_permission_blocked_org"]}}', "forbidden_unknown", None, "json"),
    (403, b'', "forbidden_unknown", None, "empty"),
    (403, b'x' * 8193, "forbidden_unknown", None, "unknown"),
    (429, b'groq-test-placeholder', "rate_limit", None, "text"),
    (500, b'{"error":{"code":"model_permission_blocked_org"}}', "provider_error", None, "json"),
])
def test_safe_classification_and_closed_response(status, body, category, code, format):
    stream = io.BytesIO(body)
    error = HTTPError("https://api.groq.com/", status, "private reason", {"X-Private": "groq-test-placeholder"}, stream)
    failure = classify_http_error(error)
    assert (failure.category, failure.error_code, failure.response_format) == (category, code, format)
    assert failure.http_status == status
    assert stream.closed
    public = GroqProviderError(failure)
    assert public.status_code == (503 if status in (401, 403, 429) else 502)
    assert "groq-test-placeholder" not in str(public.detail)
    assert "CRM confidential" not in str(public.detail)
    assert "private reason" not in str(public.detail)


def test_unreadable_and_oversized_errors_are_bounded():
    class Broken(io.BytesIO):
        def read(self, size=-1):
            assert size == 8193
            raise OSError("private transport failure")

    stream = Broken()
    failure = classify_http_error(HTTPError("https://api.groq.com/", 403, "private", {}, stream))
    assert failure.response_format == "unknown" and failure.category == "forbidden_unknown"
    assert stream.closed
    body = io.BytesIO(b'x' * 100000)
    reads = []

    class Counting(io.BytesIO):
        def read(self, size=-1):
            reads.append(size)
            return body.read(size)

    classify_http_error(HTTPError("https://api.groq.com/", 403, "private", {}, Counting()))
    assert reads == [8193] and body.tell() == 8193


def test_diagnostic_uses_same_client_and_one_generic_request(configured, monkeypatch, capsys):
    calls = []

    def transport(request, timeout):
        payload = json.loads(request.data)
        calls.append(payload)
        assert request.full_url == "https://api.groq.com/openai/v1/chat/completions"
        assert request.get_header("Authorization") == "Bearer groq-test-placeholder"
        assert request.get_header("User-agent") == "InvektaCRM/0.4"
        assert request.get_header("Accept") == "application/json" and timeout == 45
        assert payload["model"] == configured.crm_groq_model
        assert payload["reasoning_effort"] == "low"
        context = json.loads(payload["messages"][1]["content"])
        assert set(context) == {"instructions"}
        return io.BytesIO(json.dumps({"choices": [{"finish_reason": "stop", "message": {
            "content": json.dumps({"subject": "Private generated subject", "body": "Private generated body"})
        }}]}).encode())

    monkeypatch.setattr(ai_provider, "urlopen", transport)
    assert check_ai_connection.main() == 0 and len(calls) == 1
    assert json.loads(capsys.readouterr().out) == {"ok": True, "http_status": 200, "category": "generation_validated"}


def test_diagnostic_does_not_print_arbitrary_error_or_secret(configured, monkeypatch, capsys):
    def transport(request, timeout):
        raise HTTPError(request.full_url, 403, "groq-test-placeholder", {"Authorization": "secret"}, io.BytesIO(
            b'{"error":{"code":"model_permission_blocked_project","message":"CRM confidential text"}}'))

    monkeypatch.setattr(ai_provider, "urlopen", transport)
    assert check_ai_connection.main() == 1
    assert json.loads(capsys.readouterr().out) == {
        "ok": False, "http_status": 403, "category": "model_permission_blocked_project",
        "response_format": "json", "error_code": "model_permission_blocked_project",
    }


@pytest.mark.parametrize("enabled,key,category", [(False, "unused", "ai_disabled"), (True, "", "groq_key_missing")])
def test_unconfigured_diagnostic_never_calls_network(configured, monkeypatch, capsys, enabled, key, category):
    monkeypatch.setattr(check_ai_connection, "get_settings", lambda: configured.model_copy(update={
        "crm_ai_enabled": enabled, "crm_groq_api_key": key, "crm_ai_api_key": "legacy-key-must-not-be-used",
    }))

    def forbidden(*args, **kwargs):
        raise AssertionError("No network without separate enabled Groq configuration")

    monkeypatch.setattr(ai_provider, "urlopen", forbidden)
    assert check_ai_connection.main() == 2
    assert json.loads(capsys.readouterr().out) == {"ok": False, "category": category}


@pytest.mark.parametrize("failure,category", [(TimeoutError("private"), "timeout"), (URLError("private"), "connection_or_response_invalid")])
def test_transport_diagnostic_never_prints_raw_exception(configured, monkeypatch, capsys, failure, category):
    def transport(*args, **kwargs):
        raise failure

    monkeypatch.setattr(ai_provider, "urlopen", transport)
    assert check_ai_connection.main() == 1
    assert json.loads(capsys.readouterr().out) == {"ok": False, "http_status": None, "category": category}
