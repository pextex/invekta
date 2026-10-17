"""Bounded Gemini error diagnostics. Discard upstream messages, details and headers."""
from dataclasses import dataclass
import json
from typing import Literal
from urllib.error import HTTPError

from fastapi import HTTPException


@dataclass(frozen=True)
class GeminiFailure:
    http_status: int
    category: str
    response_format: Literal["json", "html", "text", "empty", "unknown"]
    error_code: str | None = None


class GeminiProviderError(HTTPException):
    def __init__(self, failure: GeminiFailure):
        self.failure = failure
        messages = {
            "authentication": "Gemini nije prihvatio API ključ. Administrator treba da proveri serversku konfiguraciju.",
            "permission_denied": "Gemini je odbio pristup. Administrator treba da proveri dozvole ključa i pristup modelu.",
            "model_not_found": "Podešeni Gemini model nije dostupan. Administrator treba da proveri naziv modela.",
            "rate_limit": "Gemini je dostigao limit. Sačekajte i pokušajte kasnije.",
            "account_unavailable": "Gemini nije dostupan za podešeni nalog ili region. Proverite dostupnost besplatnog API pristupa.",
            "invalid_request": "Gemini nije prihvatio zahtev. Administrator treba da proveri model i API konfiguraciju.",
        }
        super().__init__(
            503 if failure.http_status in (400, 401, 402, 403, 404, 429) else 502,
            messages.get(failure.category, "Gemini trenutno nije dostupan. Pokušajte kasnije."),
        )


def classify_http_error(error: HTTPError) -> GeminiFailure:
    raw = b""
    readable = True
    try:
        raw = error.read(8193)
    except (OSError, ValueError, TypeError):
        readable = False
    finally:
        error.close()

    response_format: Literal["json", "html", "text", "empty", "unknown"] = "unknown"
    code = None
    if readable and len(raw) <= 8192:
        text = raw.decode("utf-8", errors="replace").strip()
        if not text:
            response_format = "empty"
        else:
            try:
                result = json.loads(text)
                response_format = "json"
                detail = result.get("error") if isinstance(result, dict) else None
                candidate = detail.get("status") if isinstance(detail, dict) else None
                if isinstance(candidate, str) and candidate == {
                    400: "FAILED_PRECONDITION", 401: "UNAUTHENTICATED",
                    403: "PERMISSION_DENIED", 404: "NOT_FOUND", 429: "RESOURCE_EXHAUSTED",
                }.get(error.code):
                    code = candidate
                if error.code == 400 and isinstance(detail, dict):
                    details = detail.get("details", [])
                    if isinstance(details, list) and any(
                        isinstance(item, dict) and item.get("reason") == "API_KEY_INVALID" for item in details
                    ):
                        code = "API_KEY_INVALID"
            except (ValueError, RecursionError):
                response_format = "html" if text.lower().startswith(("<!doctype html", "<html")) else "text"

    category = {
        400: "invalid_request", 401: "authentication", 402: "account_unavailable",
        403: "permission_denied", 404: "model_not_found", 429: "rate_limit",
    }.get(error.code, "provider_error")
    if code == "API_KEY_INVALID":
        category = "authentication"
    elif code == "FAILED_PRECONDITION":
        category = "account_unavailable"
    return GeminiFailure(error.code, category, response_format, code)
