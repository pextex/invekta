import pytest
from fastapi import HTTPException
from starlette.requests import Request
from app.security import require_origin


def request(origin: str | None, fetch_site: str | None = None) -> Request:
    headers = []
    if origin is not None:
        headers.append((b"origin", origin.encode()))
    if fetch_site is not None:
        headers.append((b"sec-fetch-site", fetch_site.encode()))
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "https",
        "path": "/api/auth/login",
        "raw_path": b"/api/auth/login",
        "query_string": b"",
        "headers": headers,
        "client": ("127.0.0.1", 12345),
        "server": ("example.test", 443),
        "root_path": "",
    }
    return Request(scope)


def test_exact_local_origin_allowlist_does_not_need_fetch_metadata():
    require_origin(request("http://localhost:5173"))


def test_unknown_public_origin_requires_browser_same_origin_metadata():
    require_origin(request("https://preview.example.com", "same-origin"))
    with pytest.raises(HTTPException) as error:
        require_origin(request("https://preview.example.com", "same-site"))
    assert error.value.status_code == 403


@pytest.mark.parametrize(
    "origin,fetch_site",
    [
        (None, "same-origin"),
        ("null", "same-origin"),
        ("https://attacker.example/path", "same-origin"),
        ("http://attacker.example", "same-origin"),
        ("https://attacker.example", "same-site"),
    ],
)
def test_invalid_or_non_same_origin_request_is_rejected(origin, fetch_site):
    with pytest.raises(HTTPException) as error:
        require_origin(request(origin, fetch_site))
    assert error.value.status_code == 403
