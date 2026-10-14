from sqlalchemy import select
from app.models import Membership, Task
from test_api import login, ORIGIN

PAYLOAD = {"title": "Pozvati klijenta", "due_date": "2026-10-14", "due_time": "09:30", "notes": "Proveriti ponudu", "company_id": 101}
PARAMS = {"date_from": "2026-10-01", "date_to": "2026-10-31"}


def test_tasks_persist_and_obey_company_owner_and_unit_access(client, db):
    assert client.get("/api/units/101/tasks", params=PARAMS).status_code == 401
    login(client, "sales")
    response = client.post("/api/units/101/tasks", json=PAYLOAD, headers=ORIGIN)
    assert response.status_code == 201
    task = response.json()
    assert task["owner_id"] == 102 and task["company_name"] == "Test firma A"
    assert task["due_time"] == "09:30:00" and task["status"] == "planned"
    assert db.get(Task, task["id"]).title == PAYLOAD["title"]
    login(client, "other")
    assert client.get("/api/units/101/tasks", params=PARAMS).json()["total"] == 0
    assert client.patch(f"/api/units/101/tasks/{task['id']}/status", json={"status": "done", "version": 1}, headers=ORIGIN).status_code == 404
    login(client, "sales")
    assert client.get("/api/units/102/tasks", params=PARAMS).status_code == 403
    for company in [102, 103]:
        assert client.post("/api/units/101/tasks", json={**PAYLOAD, "company_id": company}, headers=ORIGIN).status_code == 404
    assert client.post("/api/units/102/tasks", json=PAYLOAD, headers=ORIGIN).status_code == 403
    login(client, "manager")
    assert client.get("/api/units/101/tasks", params=PARAMS).json()["items"][0]["id"] == task["id"]
    assert client.get("/api/units/102/tasks", params=PARAMS).json()["total"] == 0


def test_task_edit_completion_conflicts_and_relogin(client, db):
    login(client, "sales")
    task = client.post("/api/units/101/tasks", json=PAYLOAD, headers=ORIGIN).json()
    path = f"/api/units/101/tasks/{task['id']}"
    response = client.patch(path, json={**PAYLOAD, "title": "Dogovoriti sastanak", "due_date": "2026-11-03", "version": 1}, headers=ORIGIN)
    assert response.status_code == 200 and response.json()["version"] == 2
    assert client.patch(path, json={**PAYLOAD, "version": 1}, headers=ORIGIN).status_code == 409
    assert client.get("/api/units/101/tasks", params=PARAMS).json()["total"] == 0
    assert client.patch(path + "/status", json={"status": "done", "version": 2}, headers=ORIGIN).json()["version"] == 3
    assert client.patch(path + "/status", json={"status": "planned", "version": 2}, headers=ORIGIN).status_code == 409
    client.post("/api/auth/logout", headers=ORIGIN)
    login(client, "sales")
    rows = client.get("/api/units/101/tasks", params={"date_from": "2026-11-01", "date_to": "2026-11-30"}).json()
    assert rows["items"][0]["status"] == "done"
    assert rows["items"][0]["title"] == "Dogovoriti sastanak"
    db.get(Membership, (102, 101)).enabled = False
    db.commit()
    assert client.get("/api/units/101/tasks", params=PARAMS).status_code == 403


def test_task_validation_origin_and_no_ownership_injection(client, db):
    login(client, "sales")
    for extra in [{"title": " "}, {"due_date": "2026-02-30"}, {"due_time": "25:00"},
                  {"due_time": "09:30:00+02:00"}, {"company_id": -1}, {"owner_id": 103},
                  {"business_unit_id": 102}, {"status": "done"}, {"notes": "x" * 2001}]:
        assert client.post("/api/units/101/tasks", json={**PAYLOAD, **extra}, headers=ORIGIN).status_code == 422
    assert client.post("/api/units/101/tasks", json=PAYLOAD).status_code == 403
    assert client.post("/api/units/101/tasks", json=PAYLOAD, headers={"Origin": "https://invalid.example"}).status_code == 403
    assert db.scalar(select(Task)) is None
    assert client.get("/api/units/101/tasks", params={"date_from": "2026-11-01", "date_to": "2026-10-01"}).status_code == 422


def test_personal_tasks_and_complete_month_pagination(client, db):
    login(client, "sales")
    for index in range(3):
        assert client.post("/api/units/101/tasks", json={**PAYLOAD, "title": f"Lični zadatak {index}", "company_id": None, "due_time": None}, headers=ORIGIN).status_code == 201
    first = client.get("/api/units/101/tasks", params={**PARAMS, "limit": 2}).json()
    second = client.get("/api/units/101/tasks", params={**PARAMS, "limit": 2, "offset": 2}).json()
    assert first["total"] == second["total"] == 3
    assert len(first["items"]) == 2 and len(second["items"]) == 1
    assert len({row["id"] for row in first["items"] + second["items"]}) == 3
    login(client, "manager")
    assert client.get("/api/units/101/tasks", params=PARAMS).json()["total"] == 3
    login(client, "other")
    assert client.get("/api/units/101/tasks", params=PARAMS).json()["total"] == 0


def test_database_rejects_task_linked_to_another_unit(db, data):
    import pytest
    from datetime import date
    from sqlalchemy.exc import IntegrityError
    db.add(Task(owner_id=102, business_unit_id=101, company_id=103, title="Invalid", due_date=date(2026, 10, 14)))
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()
