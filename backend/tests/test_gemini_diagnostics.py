"""Simulated Gemini protocol, diagnostics and provider-boundary regressions."""
import io
import json
from urllib.error import HTTPError, URLError

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app import ai_provider, check_ai_connection
from app.config import Settings, get_settings
from app.gemini_errors import GeminiProviderError, classify_http_error


@pytest.fixture
def configured(monkeypatch):
    settings = get_settings().model_copy(update={
        "crm_ai_enabled": True, "crm_gemini_api_key": "gemini-test-placeholder",
        "crm_gemini_model": "gemini-3.1-flash-lite",
    })
    monkeypatch.setattr(ai_provider, "get_settings", lambda: settings)
    monkeypatch.setattr(check_ai_connection, "get_settings", lambda: settings)
    return settings


@pytest.mark.parametrize("status,body,category,code,format", [
    (400, b'{"error":{"status":"INVALID_ARGUMENT","details":[{"reason":"API_KEY_INVALID"}]}}', "authentication", "API_KEY_INVALID", "json"),
    (400, b'{"error":{"status":"FAILED_PRECONDITION"}}', "account_unavailable", "FAILED_PRECONDITION", "json"),
    (400, b'{"error":{"status":"INVALID_ARGUMENT"}}', "invalid_request", None, "json"),
    (401, b'{"error":{"status":"UNAUTHENTICATED"}}', "authentication", "UNAUTHENTICATED", "json"),
    (402, b'private billing text', "account_unavailable", None, "text"),
    (403, b'{"error":{"status":"PERMISSION_DENIED","message":"CRM confidential text"}}', "permission_denied", "PERMISSION_DENIED", "json"),
    (403, b'{"error":{"status":"private-test-placeholder"}}', "permission_denied", None, "json"),
    (403, b'{"error":{"status":["PERMISSION_DENIED"]}}', "permission_denied", None, "json"),
    (403, b'<html>private-test-placeholder</html>', "permission_denied", None, "html"),
    (403, b'', "permission_denied", None, "empty"),
    (403, b'x' * 8193, "permission_denied", None, "unknown"),
    (404, b'{"error":{"status":"NOT_FOUND"}}', "model_not_found", "NOT_FOUND", "json"),
    (429, b'{"error":{"status":"RESOURCE_EXHAUSTED"}}', "rate_limit", "RESOURCE_EXHAUSTED", "json"),
    (500, b'{"error":{"status":"PERMISSION_DENIED"}}', "provider_error", None, "json"),
])
def test_safe_classification_and_closed_response(status, body, category, code, format):
    stream = io.BytesIO(body)
    error = HTTPError("https://generativelanguage.googleapis.com/", status, "private reason", {"X-Private": "gemini-test-placeholder"}, stream)
    failure = classify_http_error(error)
    assert (failure.category, failure.error_code, failure.response_format) == (category, code, format)
    assert failure.http_status == status and stream.closed
    public = GeminiProviderError(failure)
    assert public.status_code == (503 if status in (400, 401, 402, 403, 404, 429) else 502)
    assert all(text not in str(public.detail) for text in ("placeholder", "CRM confidential", "private reason", "billing text"))


def test_unreadable_and_oversized_errors_are_bounded():
    class Broken(io.BytesIO):
        def read(self, size=-1):
            assert size == 8193
            raise OSError("private transport failure")

    stream = Broken()
    failure = classify_http_error(HTTPError("https://generativelanguage.googleapis.com/", 403, "private", {}, stream))
    assert failure.response_format == "unknown" and failure.category == "permission_denied" and stream.closed
    reads = []

    class Counting(io.BytesIO):
        def read(self, size=-1):
            reads.append(size)
            return super().read(size)

    stream = Counting(b'x' * 100000)
    classify_http_error(HTTPError("https://generativelanguage.googleapis.com/", 403, "private", {}, stream))
    assert reads == [8193] and stream.closed


def test_diagnostic_uses_same_client_and_one_generic_request(configured, monkeypatch, capsys):
    calls = []

    def transport(request, timeout):
        payload = json.loads(request.data)
        calls.append(payload)
        assert request.full_url == "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent"
        assert request.get_header("X-goog-api-key") == "gemini-test-placeholder"
        assert request.get_header("Accept") == "application/json" and timeout == 45
        assert set(json.loads(payload["contents"][0]["parts"][0]["text"])) == {"instructions"}
        return io.BytesIO(json.dumps({"candidates": [{"finishReason": "STOP", "content": {"parts": [{
            "text": json.dumps({"subject": "Private generated subject", "body": "Private generated body"})
        }]}}]}).encode())

    monkeypatch.setattr(ai_provider, "urlopen", transport)
    assert check_ai_connection.main() == 0 and len(calls) == 1
    assert json.loads(capsys.readouterr().out) == {"ok": True, "http_status": 200, "category": "generation_validated"}


def test_diagnostic_does_not_print_arbitrary_error_or_secret(configured, monkeypatch, capsys):
    def transport(request, timeout):
        raise HTTPError(request.full_url, 403, "gemini-test-placeholder", {"X-goog-api-key": "secret"}, io.BytesIO(
            b'{"error":{"status":"PERMISSION_DENIED","message":"CRM confidential text"}}'))

    monkeypatch.setattr(ai_provider, "urlopen", transport)
    assert check_ai_connection.main() == 1
    assert json.loads(capsys.readouterr().out) == {
        "ok": False, "http_status": 403, "category": "permission_denied",
        "response_format": "json", "error_code": "PERMISSION_DENIED",
    }


@pytest.mark.parametrize("enabled,key,category", [(False, "unused", "ai_disabled"), (True, "", "gemini_key_missing")])
def test_unconfigured_diagnostic_never_calls_network(configured, monkeypatch, capsys, enabled, key, category):
    settings = configured.model_copy(update={"crm_ai_enabled": enabled, "crm_gemini_api_key": key})
    monkeypatch.setattr(check_ai_connection, "get_settings", lambda: settings)
    monkeypatch.setattr(ai_provider, "get_settings", lambda: settings)

    def forbidden(*args, **kwargs):
        raise AssertionError("No network without separate enabled Gemini configuration")

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


@pytest.mark.parametrize("response", [
    {"promptFeedback": {"blockReason": "SAFETY"}},
    {"candidates": [{"finishReason": "STOP", "content": {"parts": [{"functionCall": {}}]}}]},
    {"candidates": [{"finishReason": "STOP", "content": {"parts": [{"thought": True, "text": '{"subject":"private","body":"private"}'}]}}]},
    {"candidates": [{"finishReason": "STOP", "content": {"parts": []}}]},
    {"candidates": [None]}, {"promptFeedback": None}, [], None,
])
def test_blocked_and_malformed_results_are_never_returned(configured, monkeypatch, response):
    monkeypatch.setattr(ai_provider, "urlopen", lambda *args, **kwargs: io.BytesIO(json.dumps(response).encode()))
    with pytest.raises(HTTPException) as error:
        ai_provider.generate({})
    assert error.value.status_code == 502 and "private" not in error.value.detail


def test_oversized_success_response_is_bounded_and_not_returned(configured, monkeypatch):
    reads = []

    class Counting(io.BytesIO):
        def read(self, size=-1):
            reads.append(size)
            return super().read(size)

    stream = Counting(b'x' * 300000)
    monkeypatch.setattr(ai_provider, "urlopen", lambda *args, **kwargs: stream)
    with pytest.raises(HTTPException):
        ai_provider.generate({})
    assert reads == [200001] and stream.closed


def test_old_provider_keys_never_enable_gemini_or_leave_backend(monkeypatch):
    monkeypatch.setenv("CRM_GROQ_API_KEY", "old-groq-placeholder")
    monkeypatch.setenv("CRM_AI_API_KEY", "old-openai-placeholder")
    monkeypatch.setenv("CRM_GEMINI_API_KEY", "")
    settings = Settings(database_url="postgresql://unused.example.invalid/unused", crm_ai_enabled=True)
    monkeypatch.setattr(ai_provider, "get_settings", lambda: settings)
    monkeypatch.setattr(ai_provider, "urlopen", lambda *args, **kwargs: pytest.fail("Legacy keys must never be sent"))
    with pytest.raises(HTTPException) as error:
        ai_provider.generate({})
    assert error.value.status_code == 503


def test_model_configuration_rejects_paths_and_preserves_requested_default():
    assert Settings(database_url="postgresql://unused.example.invalid/unused", _env_file=None).crm_gemini_model == "gemini-3.1-flash-lite"
    for model in ("../private", "gemini-name?key=private", "gemini-name/other", "https://other.invalid", "gemini-" + "x" * 100):
        with pytest.raises(ValidationError):
            Settings(database_url="postgresql://unused.example.invalid/unused", crm_gemini_model=model, _env_file=None)
