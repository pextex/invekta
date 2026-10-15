from sqlalchemy.dialects import mysql, postgresql
from sqlalchemy.schema import CreateTable
from app.models import AiBrandKnowledge, Membership, User

ORIGIN = {"Origin": "http://localhost:5173"}
BASE = "/api/units/101/ai/knowledge"


def login(client, username="sales"):
    assert client.post("/api/auth/login", json={"username": username, "password": "test-password-only-123"}, headers=ORIGIN).status_code == 200


def test_knowledge_is_admin_managed_shared_with_members_and_separated_by_brand(client, db):
    assert client.get(BASE).status_code == 401
    login(client)
    assert client.get(BASE).json()["content"] == ""
    for username in ("sales", "manager"):
        login(client, username)
        assert client.put(BASE, json={"content": "Not permitted"}, headers=ORIGIN).status_code == 403
    db.get(Membership, (101, 101)).role = "admin"
    db.commit()
    response = client.put(BASE, json={"content": "  Proverene usluge LUU  "}, headers=ORIGIN)
    assert response.status_code == 200
    row = response.json()
    assert row["content"] == "Proverene usluge LUU" and row["version"] == 1
    login(client, "sales")
    assert client.get(BASE).json() == row
    assert client.put(BASE, json={"content": "Changed", "version": 1}, headers=ORIGIN).status_code == 403
    assert client.get("/api/units/102/ai/knowledge").status_code == 403
    login(client, "outsider")
    assert client.get(BASE).status_code == 403
    assert client.get("/api/units/102/ai/knowledge").json()["content"] == ""
    db.get(Membership, (104, 102)).enabled = False
    db.commit()
    assert client.get("/api/units/102/ai/knowledge").status_code == 403


def test_knowledge_versions_input_limits_and_origin_preserve_saved_content(client, db):
    db.get(Membership, (101, 101)).role = "admin"
    db.commit()
    login(client, "manager")
    data = {"content": "Činjenice", "version": None}
    assert client.put(BASE, json=data).status_code == 403
    assert client.put(BASE, json=data, headers={"Origin": "https://other.example"}).status_code == 403
    assert client.put(BASE, json={**data, "version": 1}, headers=ORIGIN).status_code == 409
    assert client.put(BASE, json=data, headers=ORIGIN).json()["version"] == 1
    assert client.put(BASE, json=data, headers=ORIGIN).status_code == 409
    for body in ({"content": "x" * 12001, "version": 1}, {"content": "x", "version": 0}, {"content": "x", "version": 1, "secret": "invalid"}):
        assert client.put(BASE, json=body, headers=ORIGIN).status_code == 422
    assert client.get(BASE).json()["content"] == "Činjenice"
    response = client.put(BASE, json={"content": "Nova verzija", "version": 1}, headers=ORIGIN)
    assert response.status_code == 200 and response.json()["version"] == 2
    assert client.put(BASE, json={"content": "stale", "version": 1}, headers=ORIGIN).status_code == 409
    assert client.put(BASE, json={"content": "", "version": 2}, headers=ORIGIN).json()["content"] == ""


def test_platform_admin_still_requires_active_brand_membership(client, db):
    db.get(User, 101).is_platform_admin = True
    db.commit()
    login(client, "manager")
    assert client.put(BASE, json={"content": "Approved"}, headers=ORIGIN).status_code == 200
    db.get(Membership, (101, 101)).enabled = False
    db.commit()
    assert client.put(BASE, json={"content": "Blocked", "version": 1}, headers=ORIGIN).status_code == 403
    assert client.get(BASE).status_code == 403


def test_knowledge_storage_compiles_for_both_production_and_local_databases():
    for dialect in (mysql.dialect(), postgresql.dialect()):
        sql = str(CreateTable(AiBrandKnowledge.__table__).compile(dialect=dialect))
        assert "content TEXT NOT NULL" in sql
        assert "PRIMARY KEY (business_unit_id)" in sql


def test_bundled_website_knowledge_is_read_only_until_explicit_admin_save(client, db):
    from sqlalchemy import select
    from app.models import BusinessUnit
    unit_id = db.scalar(select(BusinessUnit.id).where(BusinessUnit.code == "LUU"))
    assert unit_id is not None
    db.add(Membership(user_id=101, business_unit_id=unit_id, role="admin"))
    db.commit()
    path = f"/api/units/{unit_id}/ai/knowledge"
    login(client, "manager")
    initial = client.get(path).json()
    assert initial["version"] is None and "https://luu.rs/" in initial["content"]
    assert db.get(AiBrandKnowledge, unit_id) is None  # No seeding on GET/startup.
    assert client.put(path, json={"content": "", "version": None}, headers=ORIGIN).status_code == 200
    assert client.get(path).json()["content"] == ""  # Explicit clearing overrides bundled facts.
