from sqlalchemy import select, func
from app.models import User, Membership, LoginSession, Company, BusinessUnit
from app.security import COOKIE_NAME, verify_password

ORIGIN = {"Origin": "http://localhost:5173"}
PASSWORD = "new-profile-password-123"


def login(client, username):
    return client.post(
        "/api/auth/login",
        json={"username": username, "password": "test-password-only-123"},
        headers=ORIGIN,
    )


def admin(client, db):
    actor = db.get(User, 101)
    actor.is_platform_admin = True
    db.commit()
    assert login(client, "manager").status_code == 200


def profile(**extra):
    return {
        "email": "new@example.com",
        "name": "New User",
        "password": PASSWORD,
        "units": [{"code": "LUU", "role": "sales"}],
        **extra,
    }


def test_organization_admin_cannot_manage_users(client, db):
    assert client.get("/api/admin/users").status_code == 401
    login(client, "manager")  # Has admin role in TEST_INVEKTA, not platform admin.
    assert client.get("/api/admin/users").status_code == 403
    assert (
        client.post("/api/admin/users", json=profile(), headers=ORIGIN).status_code
        == 403
    )


def test_create_scoped_user_and_prevent_privilege_injection(client, db):
    admin(client, db)
    assert (
        client.post(
            "/api/admin/users", json=profile(is_platform_admin=True), headers=ORIGIN
        ).status_code
        == 422
    )
    invalid = client.post(
        "/api/admin/users",
        json=profile(password="secret-too-short"[:5]),
        headers=ORIGIN,
    )
    assert invalid.status_code == 422
    assert "secre" not in invalid.text
    result = client.post("/api/admin/users", json=profile(), headers=ORIGIN)
    assert result.status_code == 201
    data = result.json()
    assert data["units"] == [{"code": "LUU", "role": "sales"}]
    assert not data["is_platform_admin"]
    assert "password" not in data and "password_hash" not in data
    assert verify_password(PASSWORD, db.get(User, data["id"]).password_hash)
    assert (
        client.post(
            "/api/admin/users", json=profile(email="NEW@example.com"), headers=ORIGIN
        ).status_code
        == 409
    )
    assert (
        client.post(
            "/api/admin/users",
            json=profile(
                email="other@example.com", units=[{"code": "LUU", "role": "sales"}] * 2
            ),
            headers=ORIGIN,
        ).status_code
        == 422
    )
    client.post("/api/auth/logout", headers=ORIGIN)
    creds = {
        "email": "new@example.com",
        "password": PASSWORD,
        "business_unit_code": "CENOBOTS",
    }
    assert client.post("/api/auth/login", json=creds, headers=ORIGIN).status_code == 403
    creds["business_unit_code"] = "LUU"
    assert client.post("/api/auth/login", json=creds, headers=ORIGIN).status_code == 200
    assert [u["code"] for u in client.get("/api/auth/me").json()["units"]] == ["LUU"]
    assert client.get("/api/admin/users").status_code == 403


def test_revoke_owner_access_preserves_data_and_revokes_session(client, db):
    assert login(client, "sales").status_code == 200
    old_cookie = client.cookies.get(COOKIE_NAME)
    client.cookies.clear()
    admin(client, db)
    target = next(
        u for u in client.get("/api/admin/users").json()["items"] if u["id"] == 102
    )
    body = {
        "name": target["name"],
        "active": True,
        "units": [],
        "version": target["version"],
    }
    response = client.patch("/api/admin/users/102", json=body, headers=ORIGIN)
    assert response.status_code == 200
    assert db.get(Company, 101).owner_id == 102
    assert db.get(Membership, (102, 101)).enabled is False
    assert (
        db.scalar(
            select(func.count())
            .select_from(LoginSession)
            .where(LoginSession.user_id == 102)
        )
        == 0
    )
    assert (
        client.patch("/api/admin/users/102", json=body, headers=ORIGIN).status_code
        == 409
    )
    client.cookies.clear()
    client.cookies.set(COOKIE_NAME, old_cookie)
    assert client.get("/api/auth/me").status_code == 401
    client.cookies.clear()
    login(client, "sales")
    assert client.get("/api/units/101/companies").status_code == 403
    assert client.get("/api/units/101/summary").status_code == 403
    assert client.get("/api/auth/me").json()["units"] == []


def test_reset_password_disable_account_and_protect_platform_owner(client, db):
    admin(client, db)
    result = client.post("/api/admin/users", json=profile(), headers=ORIGIN).json()
    user_id = result["id"]
    body = {
        "name": "Updated",
        "active": False,
        "units": [],
        "version": result["version"],
        "password": "replacement-password-123",
    }
    assert (
        client.patch(
            f"/api/admin/users/{user_id}", json=body, headers=ORIGIN
        ).status_code
        == 200
    )
    assert verify_password(body["password"], db.get(User, user_id).password_hash)
    self_body = {
        "name": "Self",
        "active": False,
        "units": [],
        "version": db.get(User, 101).version,
    }
    assert (
        client.patch("/api/admin/users/101", json=self_body, headers=ORIGIN).status_code
        == 403
    )
    assert client.get("/api/admin/users?offset=0&limit=1").json()["total"] == 5
    assert len(client.get("/api/admin/users?limit=1").json()["items"]) == 1
    client.post("/api/auth/logout", headers=ORIGIN)
    assert (
        client.post(
            "/api/auth/login",
            json={"email": "new@example.com", "password": body["password"]},
            headers=ORIGIN,
        ).status_code
        == 401
    )
