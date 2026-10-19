from decimal import Decimal
import pytest
from sqlalchemy.exc import IntegrityError
from app.models import Contact, Opportunity

ORIGIN = {"Origin": "http://localhost:5173"}
CONTACT = {
    "name": "Test kontakt",
    "position": "Nabavka",
    "email": "test@example.com",
    "phone": "+381 60 000 0000",
}
OPPORTUNITY = {
    "company_id": 101,
    "title": "Test ponuda",
    "amount": "12500.55",
    "stage": "Novi lead",
    "expected_close_date": "2026-12-31",
    "notes": "Test beleška",
}


def login(client, name="manager"):
    response = client.post(
        "/api/auth/login",
        json={"username": name, "password": "test-password-only-123"},
        headers=ORIGIN,
    )
    assert response.status_code == 200


@pytest.fixture
def sales_records(db, data):
    db.add_all(
        [
            Contact(
                id=1001,
                company_id=101,
                business_unit_id=101,
                name="Kontakt A",
                email="a@example.com",
            ),
            Contact(
                id=1002,
                company_id=102,
                business_unit_id=101,
                name="Kontakt B",
                email="b@example.com",
            ),
        ]
    )
    db.add_all(
        [
            Opportunity(
                id=2001,
                company_id=101,
                business_unit_id=101,
                title="Prilika A",
                amount=Decimal("100.10"),
                stage="Kontaktiran",
            ),
            Opportunity(
                id=2002,
                company_id=102,
                business_unit_id=101,
                title="Prilika B",
                amount=Decimal("200.20"),
                stage="Ponuda",
            ),
            Opportunity(
                id=2003,
                company_id=103,
                business_unit_id=102,
                title="Prilika C",
                amount=Decimal("300.30"),
                stage="Dobijeno",
            ),
        ]
    )
    db.commit()


def test_crm_requires_login(client):
    for path in [
        "/companies/101",
        "/companies/101/contacts",
        "/opportunities",
        "/summary",
        "/opportunities/2001/stage-history",
    ]:
        assert client.get("/api/units/101" + path).status_code == 401


def test_contact_create_update_and_optional_fields(client, db):
    login(client, "sales")
    response = client.post(
        "/api/units/101/companies/101/contacts", json=CONTACT, headers=ORIGIN
    )
    assert response.status_code == 201
    record = response.json()
    assert (
        record["company_id"] == 101
        and record["business_unit_id"] == 101
        and record["is_demo"] is False
    )
    assert db.get(Contact, record["id"]).email == "test@example.com"
    changed = {"name": "Izmenjen kontakt", "email": "", "position": "", "phone": ""}
    assert (
        client.patch(
            f"/api/units/101/companies/101/contacts/{record['id']}",
            json=changed,
            headers=ORIGIN,
        ).status_code
        == 200
    )
    items = client.get("/api/units/101/companies/101/contacts").json()
    assert items[0]["name"] == "Izmenjen kontakt" and items[0]["email"] is None


def test_contacts_follow_company_ownership(client, sales_records):
    login(client, "sales")
    assert len(client.get("/api/units/101/companies/101/contacts").json()) == 1
    for method, path, body in [
        ("get", "/api/units/101/companies/102/contacts", None),
        ("post", "/api/units/101/companies/102/contacts", CONTACT),
        ("patch", "/api/units/101/companies/102/contacts/1002", CONTACT),
    ]:
        assert (
            client.request(method, path, json=body, headers=ORIGIN).status_code == 404
        )
    assert (
        client.patch(
            "/api/units/101/companies/101/contacts/1002", json=CONTACT, headers=ORIGIN
        ).status_code
        == 404
    )
    assert client.get("/api/units/102/companies/103/contacts").status_code == 403
    login(client)
    assert client.get("/api/units/101/companies/102/contacts").status_code == 200


def test_contact_validation_and_csrf(client):
    login(client)
    for change in [
        {"name": " "},
        {"email": "bad-email"},
        {"company_id": 102},
        {"business_unit_id": 102},
    ]:
        assert (
            client.post(
                "/api/units/101/companies/101/contacts",
                json={**CONTACT, **change},
                headers=ORIGIN,
            ).status_code
            == 422
        )
    assert (
        client.post(
            "/api/units/101/companies/101/contacts",
            json=CONTACT,
            headers={"Origin": "https://evil.example"},
        ).status_code
        == 403
    )


def test_opportunity_creation_multiple_per_company_and_history(client, db):
    login(client, "sales")
    response = client.post(
        "/api/units/101/opportunities", json=OPPORTUNITY, headers=ORIGIN
    )
    assert response.status_code == 201
    record = response.json()
    assert record["owner_name"] == "sales" and record["company_name"] == "Test firma A"
    assert (
        record["amount"] == "12500.55"
        and record["version"] == 1
        and record["is_demo"] is False
    )
    assert db.get(Opportunity, record["id"]).amount == Decimal("12500.55")
    assert (
        client.post(
            "/api/units/101/opportunities",
            json={**OPPORTUNITY, "title": "Drugi posao"},
            headers=ORIGIN,
        ).status_code
        == 201
    )
    page = client.get("/api/units/101/opportunities", params={"company_id": 101}).json()
    assert page["total"] == 2
    login(client)
    history = client.get(
        f"/api/units/101/opportunities/{record['id']}/stage-history"
    ).json()
    assert (
        len(history) == 1
        and history[0]["from_stage"] is None
        and history[0]["actor_name"] == "sales"
    )


def test_opportunities_and_history_are_scoped(client, sales_records):
    login(client, "sales")
    page = client.get("/api/units/101/opportunities").json()
    assert page["total"] == 1 and page["items"][0]["id"] == 2001
    assert client.get("/api/units/101/opportunities?company_id=102").status_code == 404
    assert (
        client.post(
            "/api/units/101/opportunities",
            json={**OPPORTUNITY, "company_id": 102},
            headers=ORIGIN,
        ).status_code
        == 404
    )
    assert (
        client.post(
            "/api/units/101/opportunities",
            json={**OPPORTUNITY, "company_id": 103},
            headers=ORIGIN,
        ).status_code
        == 404
    )
    for target in [2002, 2003]:
        assert (
            client.get(
                f"/api/units/101/opportunities/{target}/stage-history"
            ).status_code
            == 403
        )
        assert (
            client.patch(
                f"/api/units/101/opportunities/{target}/stage",
                json={"stage": "Ponuda", "version": 1},
                headers=ORIGIN,
            ).status_code
            == 404
        )
    assert client.get("/api/units/102/opportunities").status_code == 403
    login(client)
    assert client.get("/api/units/101/opportunities").json()["total"] == 2
    assert client.get("/api/units/102/opportunities").json()["total"] == 1


def test_stage_change_version_conflict_and_history(client, sales_records):
    login(client, "sales")
    path = "/api/units/101/opportunities/2001/stage"
    response = client.patch(
        path, json={"stage": "Ponuda", "version": 1}, headers=ORIGIN
    )
    assert response.status_code == 200 and response.json()["version"] == 2
    assert (
        client.patch(
            path, json={"stage": "Dobijeno", "version": 1}, headers=ORIGIN
        ).status_code
        == 409
    )
    record = client.get("/api/units/101/opportunities").json()["items"][0]
    assert record["stage"] == "Ponuda"
    login(client)
    history = client.get("/api/units/101/opportunities/2001/stage-history").json()
    assert (
        len(history) == 1
        and history[0]["from_stage"] == "Kontaktiran"
        and history[0]["to_stage"] == "Ponuda"
    )
    assert (
        client.patch(
            path, json={"stage": "Ponuda", "version": 2}, headers=ORIGIN
        ).status_code
        == 200
    )
    assert (
        len(client.get("/api/units/101/opportunities/2001/stage-history").json()) == 1
    )


def test_edit_opportunity_preserves_company_and_precise_value(client, sales_records):
    login(client)
    body = {k: v for k, v in OPPORTUNITY.items() if k != "company_id"}
    body.update(version=1, amount="0.01", stage="Pregovori")
    response = client.patch(
        "/api/units/101/opportunities/2001", json=body, headers=ORIGIN
    )
    assert response.status_code == 200 and response.json()["amount"] == "0.01"
    assert response.json()["company_id"] == 101
    assert (
        client.patch(
            "/api/units/101/opportunities/2001", json=body, headers=ORIGIN
        ).status_code
        == 409
    )
    assert (
        client.patch(
            "/api/units/101/opportunities/2001",
            json={**body, "company_id": 102},
            headers=ORIGIN,
        ).status_code
        == 422
    )


def test_opportunity_validation_csrf_and_pagination(client, sales_records):
    login(client)
    for changes in [
        {"title": " "},
        {"amount": "-1"},
        {"amount": "0.001"},
        {"stage": "Nepoznata faza"},
        {"business_unit_id": 102},
        {"owner_id": 103},
        {"expected_close_date": "not-a-date"},
    ]:
        assert (
            client.post(
                "/api/units/101/opportunities",
                json={**OPPORTUNITY, **changes},
                headers=ORIGIN,
            ).status_code
            == 422
        )
    assert (
        client.patch(
            "/api/units/101/opportunities/2001/stage",
            json={"stage": "Ponuda", "version": 1},
            headers={"Origin": "https://evil.example"},
        ).status_code
        == 403
    )
    first = client.get("/api/units/101/opportunities", params={"limit": 1}).json()
    second = client.get(
        "/api/units/101/opportunities", params={"limit": 1, "offset": 1}
    ).json()
    assert (
        first["total"] == second["total"] == 2
        and first["items"][0]["id"] != second["items"][0]["id"]
    )


def test_summary_uses_exact_values_and_role_scope(client, sales_records):
    login(client, "sales")
    summary = client.get("/api/units/101/summary").json()
    assert (
        summary["company_count"] == 1
        and summary["contact_count"] == 1
        and summary["open_count"] == 1
    )
    assert Decimal(summary["open_value"]) == Decimal("100.10")
    assert client.get("/api/units/102/summary").status_code == 403
    login(client)
    summary = client.get("/api/units/101/summary").json()
    assert summary["opportunity_count"] == 2 and Decimal(
        summary["open_value"]
    ) == Decimal("300.30")
    won = client.get("/api/units/102/summary").json()
    assert (
        won["won_count"] == 1
        and won["open_count"] == 0
        and Decimal(won["won_value"]) == Decimal("300.30")
    )
    client.patch(
        "/api/units/101/opportunities/2002/stage",
        json={"stage": "Izgubljeno", "version": 1},
        headers=ORIGIN,
    )
    assert client.get("/api/units/101/summary").json()["open_count"] == 1


def test_database_blocks_cross_unit_contact(db, data):
    db.add(Contact(company_id=101, business_unit_id=102, name="Forbidden"))
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


def test_database_blocks_cross_unit_opportunity(db, data):
    db.add(Opportunity(company_id=101, business_unit_id=102, title="Forbidden"))
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


def test_company_edit_does_not_reset_legacy_estimate(client, db):
    from app.models import Company

    company = db.get(Company, 101)
    company.stage = "Ponuda"
    company.potential_value = Decimal("123.45")
    db.commit()
    login(client)
    response = client.patch(
        "/api/units/101/companies/101",
        json={"name": "Novi naziv", "city": "Beograd", "sector": "Usluge"},
        headers=ORIGIN,
    )
    assert response.status_code == 200
    assert (
        response.json()["stage"] == "Ponuda"
        and response.json()["potential_value"] == "123.45"
    )
