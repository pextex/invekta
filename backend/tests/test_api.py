from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from app.models import Company, LoginSession
from app.security import COOKIE_NAME

ORIGIN = {"Origin": "http://localhost:5173"}
PAYLOAD = {
    "name": "Nova test kompanija",
    "city": "Beograd",
    "sector": "Usluge",
    "stage": "Kontakt",
    "potential_value": "12500.50",
}


def login(client, username="manager", password="test-password-only-123"):
    return client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
        headers=ORIGIN,
    )


def test_readiness_and_unauthenticated_access(client):
    assert client.get("/api/health").json() == {"status": "ok"}
    assert client.get("/api/ready").status_code == 200
    assert client.get("/api/units/101/companies").status_code == 401
    assert (
        client.post(
            "/api/units/101/companies", json=PAYLOAD, headers=ORIGIN
        ).status_code
        == 401
    )


def test_login_logout_and_cookie(client):
    assert login(client, password="wrong").status_code == 401
    response = login(client)
    assert response.status_code == 200
    cookie = response.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=strict" in cookie
    assert len(client.get("/api/auth/me").json()["units"]) == 2
    assert client.post("/api/auth/logout", headers=ORIGIN).status_code == 200
    assert client.get("/api/auth/me").status_code == 401


def test_business_unit_access(client):
    login(client, "sales")
    assert client.get("/api/units/102/companies").status_code == 403
    assert (
        client.post(
            "/api/units/102/companies", json=PAYLOAD, headers=ORIGIN
        ).status_code
        == 403
    )
    assert (
        client.patch(
            "/api/units/102/companies/103", json=PAYLOAD, headers=ORIGIN
        ).status_code
        == 403
    )


def test_owner_and_manager_scope(client):
    login(client, "sales")
    assert [c["id"] for c in client.get("/api/units/101/companies").json()] == [101]
    assert (
        client.patch(
            "/api/units/101/companies/102", json=PAYLOAD, headers=ORIGIN
        ).status_code
        == 404
    )
    login(client)
    assert len(client.get("/api/units/101/companies").json()) == 2
    assert len(client.get("/api/units/102/companies").json()) == 1
    assert (
        client.patch(
            "/api/units/101/companies/103", json=PAYLOAD, headers=ORIGIN
        ).status_code
        == 404
    )


def test_create_update_persistence(client, db):
    login(client, "sales")
    response = client.post("/api/units/101/companies", json=PAYLOAD, headers=ORIGIN)
    assert response.status_code == 201
    record = response.json()
    assert record["owner_id"] == 102 and record["business_unit_id"] == 101
    assert record["potential_value"] == "12500.50" and record["is_demo"] is False
    assert db.get(Company, record["id"]).name == PAYLOAD["name"]
    assert (
        client.post(
            "/api/units/101/companies", json=PAYLOAD, headers=ORIGIN
        ).status_code
        == 409
    )
    changed = {**PAYLOAD, "name": "Izmenjena kompanija", "stage": "Ponuda"}
    assert (
        client.patch(
            f"/api/units/101/companies/{record['id']}", json=changed, headers=ORIGIN
        ).status_code
        == 200
    )
    client.post("/api/auth/logout", headers=ORIGIN)
    login(client, "sales")
    matches = client.get("/api/units/101/companies?search=Izmenjena").json()
    assert len(matches) == 1 and matches[0]["stage"] == "Ponuda"


def test_validation_and_ownership_injection(client):
    login(client)
    for changes in [
        {"name": "  "},
        {"potential_value": "-1"},
        {"owner_id": 103},
        {"business_unit_id": 102},
        {"potential_value": "0.001"},
    ]:
        assert (
            client.post(
                "/api/units/101/companies", json={**PAYLOAD, **changes}, headers=ORIGIN
            ).status_code
            == 422
        )


def test_csrf_and_search_wildcards(client):
    assert (
        client.post(
            "/api/auth/login",
            json={"username": "manager", "password": "test-password-only-123"},
        ).status_code
        == 403
    )
    login(client)
    assert (
        client.post(
            "/api/units/101/companies",
            json=PAYLOAD,
            headers={"Origin": "https://evil.example"},
        ).status_code
        == 403
    )
    assert client.get("/api/units/101/companies", params={"search": "%"}).json() == []
    assert (
        client.get("/api/units/101/companies", params={"search": " beograd "}).json()[
            0
        ]["id"]
        == 101
    )


def test_expired_and_revoked_session(client, db):
    login(client)
    session = db.scalar(select(LoginSession))
    session.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    db.commit()
    assert client.get("/api/auth/me").status_code == 401
    client.cookies.set(COOKIE_NAME, "forged", path="/api")
    assert client.get("/api/auth/me").status_code == 401


def test_failed_login_throttle(client):
    for _ in range(5):
        assert login(client, password="wrong").status_code == 401
    assert login(client).status_code == 429


def test_session_token_is_hashed_in_database(client, db):
    from app.security import token_hash

    login(client)
    cookie = next(
        cookie.value for cookie in client.cookies.jar if cookie.name == COOKIE_NAME
    )
    session = db.scalar(select(LoginSession))
    assert session.token_hash != cookie
    assert session.token_hash == token_hash(cookie)


def test_secure_cookie_when_https_configured(client, monkeypatch):
    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "crm_cookie_secure", True)
    response = login(client)
    assert "secure" in response.headers["set-cookie"].lower()


def test_database_blocks_owner_from_other_unit(db, data):
    import pytest
    from sqlalchemy.exc import IntegrityError

    db.add(
        Company(
            business_unit_id=101,
            owner_id=104,
            name="Invalid cross-unit company",
            city="Beograd",
            sector="Test",
        )
    )
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


def test_company_details_contacts_and_scoped_search(client, db):
    login(client, "sales")
    payload = {**PAYLOAD, "address": "Test ulica 12", "pib": "123456789",
               "contacts": [{"name": "Petar Test", "position": "Direktor",
                             "phone": "+381601234567", "email": "petar@example.com"}]}
    response = client.post("/api/units/101/companies", json=payload, headers=ORIGIN)
    assert response.status_code == 201
    record = response.json()
    assert record["address"] == payload["address"] and record["pib"] == payload["pib"]
    url = f"/api/units/101/companies/{record['id']}"
    contacts = client.get(url + "/contacts").json()
    assert len(contacts) == 1
    assert all(contacts[0][key] == value for key, value in payload["contacts"][0].items())
    assert client.get("/api/units/101/companies?search=123456789").json()[0]["id"] == record["id"]
    login(client, "other")
    assert client.get(url).status_code == 404
    assert client.get(url + "/contacts").status_code == 404
    assert client.get("/api/units/101/companies?search=123456789").json() == []
    login(client, "manager")
    assert client.get(url).status_code == 200
    assert client.get(url + "/contacts").json()[0]["name"] == "Petar Test"
    update = {**PAYLOAD, "address": "Nova adresa 3", "pib": "987654321"}
    assert client.patch(url, json=update, headers=ORIGIN).status_code == 200
    assert client.get(url).json()["pib"] == "987654321"
    assert len(client.get(url + "/contacts").json()) == 1


def test_invalid_company_details_do_not_create_partial_records(client, db):
    login(client, "sales")
    for extra in [{"pib": "123"}, {"pib": "abcdefghi"}, {"address": " "},
                  {"contacts": [{"name": "Test", "email": "invalid"}]}]:
        response = client.post("/api/units/101/companies", json={**PAYLOAD, **extra}, headers=ORIGIN)
        assert response.status_code == 422
    assert db.scalar(select(Company).where(Company.name == PAYLOAD["name"])) is None
