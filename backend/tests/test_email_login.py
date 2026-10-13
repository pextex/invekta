from sqlalchemy import select
from app.models import User

ORIGIN = {"Origin": "http://localhost:5173"}


def test_email_password_session_logout_and_permissions(client, db):
    user = db.scalar(select(User).where(User.username == "manager"))
    user.email = "manager@example.com"
    db.commit()
    body = {"email": "MANAGER@example.com", "password": "wrong"}
    assert client.post("/api/auth/login", json=body, headers=ORIGIN).status_code == 401
    assert client.get("/api/auth/me").status_code == 401
    body["password"] = "test-password-only-123"
    response = client.post("/api/auth/login", json=body, headers=ORIGIN)
    assert response.status_code == 200
    assert "HttpOnly" in response.headers["set-cookie"]
    assert client.get("/api/auth/me").status_code == 200
    assert client.get("/api/units/101/companies").status_code == 200
    client.post("/api/auth/logout", headers=ORIGIN)
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/units/101/companies").status_code == 401


def test_invalid_email_or_ambiguous_identifier_rejected(client):
    for body in [
        {"email": "invalid", "password": "x"},
        {"email": "a@example.com", "username": "manager", "password": "x"},
        {"password": "x"},
    ]:
        assert (
            client.post("/api/auth/login", json=body, headers=ORIGIN).status_code == 422
        )


def test_email_login_checks_selected_organization(client, db):
    user = db.scalar(select(User).where(User.username == "manager"))
    user.email = "manager@example.com"
    db.commit()
    response = client.post(
        "/api/auth/login",
        json={
            "email": user.email,
            "password": "test-password-only-123",
            "business_unit_code": "CENOBOTS",
        },
        headers=ORIGIN,
    )
    assert response.status_code == 403
    assert "set-cookie" not in response.headers
