"""Bounded, allowlisted Groq diagnostics; never expose upstream text or headers."""
from dataclasses import dataclass
import json
import re
from typing import Literal
from urllib.error import HTTPError

from fastapi import HTTPException


@dataclass(frozen=True)
class GroqFailure:
    http_status: int
    category: str
    response_format: Literal["json", "html", "text", "empty", "unknown"]
    error_code: str | None = None


class GroqProviderError(HTTPException):
    def __init__(self, failure: GroqFailure):
        self.failure = failure
        messages = {
            "authentication": "Groq nije prihvatio autentifikaciju (HTTP 401). Administrator treba da proveri API ključ.",
            "model_permission_blocked_org": "Groq organizacija ne dozvoljava izabrani model. Administrator treba da proveri Organization Limits u Groq Console.",
            "model_permission_blocked_project": "Groq projekat ne dozvoljava izabrani model. Administrator treba da proveri Project Limits u Groq Console.",
            "edge_block": "Groq je vratio zaštitni odgovor (HTTP 403). Administrator treba da proveri pristup sa servera.",
            "forbidden_unknown": "Groq je odbio pristup (HTTP 403). Uzrok nije potvrđen; potrebna je serverska provera.",
            "rate_limit": "Groq je dostigao limit. Sačekajte i pokušajte kasnije.",
        }
        super().__init__(
            503 if failure.http_status in (401, 403, 429) else 502,
            messages.get(failure.category, "Groq nije odgovorio. Administrator treba da proveri vezu i izabrani model."),
        )


def classify_http_error(error: HTTPError) -> GroqFailure:
    """Consume at most 8 KiB. Unknown codes/messages are deliberately discarded."""
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
    edge = False
    if readable and len(raw) <= 8192:
        text = raw.decode("utf-8", errors="replace").strip()
        if not text:
            response_format = "empty"
        else:
            try:
                result = json.loads(text)
                response_format = "json"
                detail = result.get("error") if isinstance(result, dict) else None
                candidate = detail.get("code") if isinstance(detail, dict) else None
                if isinstance(candidate, str) and candidate in (
                    "model_permission_blocked_org", "model_permission_blocked_project",
                ):
                    code = candidate
            except (ValueError, RecursionError):
                lower = text.lower()
                response_format = "html" if lower.startswith(("<!doctype html", "<html")) else "text"
                # HTML alone does not prove a Cloudflare block. Keep ambiguous 403s unknown.
                if re.search(r"\berror\s*(?:code\s*)?:?\s*1010\b", lower):
                    edge, code = True, "cloudflare_1010"
                elif response_format == "html" and "cloudflare" in lower and any(
                    marker in lower for marker in ("access denied", "cf-chl-", "challenge-platform", "browser's signature")
                ):
                    edge = True

    category = "provider_error"
    if error.code == 401:
        category, code = "authentication", None
    elif error.code == 429:
        category, code = "rate_limit", None
    elif error.code == 403:
        category = code if code in ("model_permission_blocked_org", "model_permission_blocked_project") else (
            "edge_block" if edge else "forbidden_unknown"
        )
    else:
        code = None
    return GroqFailure(error.code, category, response_format, code)
