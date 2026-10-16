"""One generic generation through the production client; no DB, CRM data or raw output."""
import json

from fastapi import HTTPException
from pydantic import ValidationError

from .ai_provider import generate
from .config import get_settings
from .groq_errors import GroqProviderError


def main() -> int:
    try:
        settings = get_settings()
    except ValidationError:
        print(json.dumps({"ok": False, "category": "configuration_invalid"}))
        return 2
    if not settings.crm_ai_enabled or not settings.crm_groq_api_key:
        category = "ai_disabled" if not settings.crm_ai_enabled else "groq_key_missing"
        print(json.dumps({"ok": False, "category": category}))
        return 2
    try:
        generate({"instructions": 'Provera veze bez klijentskih podataka. Vrati subject "Provera" i body "Veza radi.".'})
    except GroqProviderError as error:
        failure = error.failure
        print(json.dumps({
            "ok": False,
            "http_status": failure.http_status,
            "category": failure.category,
            "response_format": failure.response_format,
            "error_code": failure.error_code,
        }))
        return 1
    except HTTPException as error:
        # These are local transport/validation failures, not an observed upstream status.
        category = "timeout" if error.status_code == 504 else "connection_or_response_invalid"
        print(json.dumps({"ok": False, "http_status": None, "category": category}))
        return 1
    print(json.dumps({"ok": True, "http_status": 200, "category": "generation_validated"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
