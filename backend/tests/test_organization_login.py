import pytest
from sqlalchemy import select, func
from app.models import (
    BusinessUnit,
    Membership,
    Company,
    Contact,
    Opportunity,
    LoginSession,
)

ORIGIN = {"Origin": "http://localhost:5173"}


@pytest.fixture
def organizations(db, data):
    units = {
        u.code: u
        for u in db.scalars(
            select(BusinessUnit).where(
                BusinessUnit.code.in_(["LUU", "INVEKTA", "CENOBOTS"])
            )
        )
    }
    assert set(units) == {"LUU", "INVEKTA", "CENOBOTS"}
    db.add(Membership(user_id=101, business_unit_id=units["LUU"].id, role="manager"))
    db.add(Membership(user_id=104, business_unit_id=units["CENOBOTS"].id, role="sales"))
    db.flush()
    company = Company(
        name="Cenobots test company",
        city="Beograd",
        sector="Test",
        business_unit_id=units["CENOBOTS"].id,
        owner_id=104,
    )
    db.add(company)
    db.flush()
    db.add(
        Contact(
            company_id=company.id,
            business_unit_id=company.business_unit_id,
            name="Cenobots test contact",
        )
    )
    db.add(
        Opportunity(
            company_id=company.id,
            business_unit_id=company.business_unit_id,
            title="Cenobots test opportunity",
        )
    )
    db.commit()
    return units, company


def sign_in(client, code, username="manager", password="test-password-only-123"):
    return client.post(
        "/api/auth/login",
        json={"username": username, "password": password, "business_unit_code": code},
        headers=ORIGIN,
    )


def test_selected_unit_is_checked_before_creating_session(client, organizations, db):
    response = sign_in(client, "CENOBOTS")
    assert response.status_code == 403
    assert "set-cookie" not in response.headers
    assert db.scalar(select(func.count()).select_from(LoginSession)) == 0
    assert client.get("/api/auth/me").status_code == 401
    assert sign_in(client, "CENOBOTS", password="wrong").status_code == 401
    allowed = sign_in(client, "LUU")
    assert allowed.status_code == 200
    assert allowed.json()["unit_id"] == organizations[0]["LUU"].id


def test_cenobots_login_and_data_are_isolated(client, organizations):
    units, company = organizations
    response = sign_in(client, "CENOBOTS", username="outsider")
    assert (
        response.status_code == 200
        and response.json()["unit_id"] == units["CENOBOTS"].id
    )
    base = f"/api/units/{units['CENOBOTS'].id}"
    assert client.get(base + "/companies").json()[0]["id"] == company.id
    assert len(client.get(base + f"/companies/{company.id}/contacts").json()) == 1
    assert client.get(base + "/opportunities").json()["total"] == 1
    assert client.get(base + "/summary").json()["company_count"] == 1
    assert client.get(f"/api/units/{units['LUU'].id}/companies").status_code == 403
    client.post("/api/auth/logout", headers=ORIGIN)
    sign_in(client, "LUU")
    assert client.get(base + "/companies").status_code == 403
    assert client.get(base + f"/companies/{company.id}/contacts").status_code == 403
    assert client.get(base + "/opportunities").status_code == 403
    assert client.get(base + "/summary").status_code == 403


def test_invalid_organization_and_privilege_injection_rejected(client, organizations):
    assert sign_in(client, "UNKNOWN").status_code == 422
    body = {
        "username": "manager",
        "password": "test-password-only-123",
        "business_unit_code": "CENOBOTS",
        "role": "admin",
    }
    assert client.post("/api/auth/login", json=body, headers=ORIGIN).status_code == 422
