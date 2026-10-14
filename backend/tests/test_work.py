from datetime import datetime, timedelta, timezone
from test_crm import login, ORIGIN

TASK = {
    "company_id": 101,
    "assignee_id": 102,
    "title": "Pozvati nabavku",
    "due_at": "2026-10-14T10:00:00+02:00",
    "priority": "normal",
    "notes": "Dogovoriti obilazak",
}


def create(client, **values):
    response = client.post(
        "/api/units/101/tasks", json={**TASK, **values}, headers=ORIGIN
    )
    assert response.status_code == 201
    return response.json()


def test_tasks_persist_summary_history_and_roles(client):
    login(client, "sales")
    task = create(client)
    assert task["assignee_name"] == "sales" and task["version"] == 1
    assert client.get("/api/units/101/work/summary").json()["tasks"]["open"] == 1
    path = f"/api/units/101/tasks/{task['id']}"
    response = client.patch(
        path, json={**TASK, "status": "done", "version": 1}, headers=ORIGIN
    )
    assert response.status_code == 200 and response.json()["completed_at"]
    assert (
        client.patch(
            path, json={**TASK, "status": "open", "version": 1}, headers=ORIGIN
        ).status_code
        == 409
    )
    history = client.get(path + "/history").json()
    assert (
        len(history) == 2
        and history[-1]["actor_name"] == "sales"
        and history[-1]["changed_at"]
    )
    assert history[-1]["changes"]["status"]["to"] == "done"
    client.post("/api/auth/logout", json={}, headers=ORIGIN)
    login(client, "sales")
    assert (
        client.get("/api/units/101/tasks?company_id=101").json()["items"][0]["status"]
        == "done"
    )
    login(client)
    assert client.get("/api/units/101/work/summary").json()["tasks"]["done"] == 1
    login(client, "other")
    assert client.get("/api/units/101/tasks").json()["total"] == 0
    assert client.get(path + "/history").status_code == 404
    assert client.get("/api/units/102/tasks").status_code == 403


def test_context_assignment_and_timezone_validation(client, db):
    from app.models import Opportunity

    db.add(
        Opportunity(id=4001, company_id=102, business_unit_id=101, title="Tuđa prilika")
    )
    db.commit()
    login(client, "sales")
    for values in (
        {"company_id": 102},
        {"assignee_id": 103},
        {"assignee_id": 104},
        {"opportunity_id": 4001},
    ):
        assert client.post(
            "/api/units/101/tasks", json={**TASK, **values}, headers=ORIGIN
        ).status_code in (404, 422)
    assert (
        client.post(
            "/api/units/101/tasks",
            json={**TASK, "due_at": "2026-10-14T10:00:00"},
            headers=ORIGIN,
        ).status_code
        == 422
    )
    assert client.post("/api/units/101/tasks", json=TASK).status_code == 403
    assert [
        u["id"]
        for u in client.get("/api/units/101/work/assignees?company_id=101").json()
    ] == [102]
    login(client)
    assert create(client, company_id=102, assignee_id=103)["assignee_id"] == 103
    assert (
        client.post(
            "/api/units/101/tasks", json={**TASK, "assignee_id": 103}, headers=ORIGIN
        ).status_code
        == 422
    )


def test_activity_schedule_completion_history(client):
    login(client, "sales")
    body = {
        **TASK,
        "kind": "call",
        "status": "planned",
        "scheduled_at": "2026-10-15T12:00:00+02:00",
    }
    for key in ("due_at", "priority"):
        body.pop(key)
    response = client.post("/api/units/101/activities", json=body, headers=ORIGIN)
    assert response.status_code == 201
    record = response.json()
    path = f"/api/units/101/activities/{record['id']}"
    assert (
        client.get("/api/units/101/work/summary").json()["activities"]["planned"] == 1
    )
    response = client.patch(
        path,
        json={**body, "status": "done", "outcome": "Dogovoren sastanak", "version": 1},
        headers=ORIGIN,
    )
    assert response.status_code == 200 and response.json()["occurred_at"]
    assert client.get("/api/units/101/work/summary").json()["completed_calls"] == 1
    assert (
        client.get(path + "/history").json()[-1]["changes"]["outcome"]["to"]
        == "Dogovoren sastanak"
    )


def test_reminders_idempotent_private_and_cancelled(client, db):
    from app.reminders import deliver_due

    login(client, "sales")
    now = datetime.now(timezone.utc)
    create(
        client,
        due_at=(now + timedelta(hours=1)).isoformat(),
        remind_at=(now - timedelta(seconds=1)).isoformat(),
    )
    assert deliver_due(db, now) == 1
    db.commit()
    assert deliver_due(db, now) == 0
    db.commit()
    items = client.get("/api/units/101/reminders").json()["items"]
    assert len(items) == 1 and items[0]["status"] == "delivered"
    path = f"/api/units/101/reminders/{items[0]['id']}/read"
    assert client.patch(path, json={}, headers=ORIGIN).json()["read_at"]
    task = create(
        client,
        title="Otkazan zadatak",
        due_at=(now + timedelta(hours=1)).isoformat(),
        remind_at=(now - timedelta(seconds=1)).isoformat(),
    )
    assert (
        client.patch(
            f"/api/units/101/tasks/{task['id']}",
            json={**TASK, "status": "cancelled", "version": 1},
            headers=ORIGIN,
        ).status_code
        == 200
    )
    assert deliver_due(db, now) == 0
    login(client, "other")
    assert client.get("/api/units/101/reminders").json()["total"] == 0


def test_revoked_assignee_not_notified(client, db):
    from app.models import Membership
    from app.reminders import deliver_due

    login(client)
    now = datetime.now(timezone.utc)
    create(
        client,
        due_at=(now + timedelta(hours=1)).isoformat(),
        remind_at=(now - timedelta(seconds=1)).isoformat(),
    )
    db.get(Membership, (102, 101)).enabled = False
    db.commit()
    assert deliver_due(db, now) == 0
    db.commit()
    login(client, "sales")
    assert client.get("/api/units/101/reminders").status_code == 403


def test_activity_reminder_and_archiving_preserve_history(client, db):
    from app.reminders import deliver_due

    login(client, "sales")
    now = datetime.now(timezone.utc)
    body = {
        "company_id": 101,
        "assignee_id": 102,
        "title": "Sastanak u objektu",
        "kind": "meeting",
        "scheduled_at": (now + timedelta(hours=1)).isoformat(),
        "remind_at": (now - timedelta(seconds=1)).isoformat(),
    }
    response = client.post("/api/units/101/activities", json=body, headers=ORIGIN)
    assert response.status_code == 201
    activity = response.json()
    assert deliver_due(db, now) == 1
    db.commit()
    notice = client.get("/api/units/101/reminders").json()["items"][0]
    assert notice["activity_id"] == activity["id"] and notice["task_id"] is None
    path = f"/api/units/101/activities/{activity['id']}"
    assert client.delete(path + "?version=1", headers=ORIGIN).status_code == 200
    assert client.get("/api/units/101/activities").json()["total"] == 0
    assert len(client.get(path + "/history").json()) == 2


def test_work_period_totals_and_database_context_constraints(client, db, data):
    from app.work_models import Task
    from app.models import Opportunity
    from sqlalchemy.exc import IntegrityError
    import pytest

    login(client, "sales")
    create(client)
    result = client.get(
        "/api/units/101/work/summary?start_date=2026-10-14&end_date=2026-10-14"
    ).json()
    assert (
        result["tasks"]["open"] == 1
        and result["assignee_results"][0]["open_tasks"] == 1
    )
    assert (
        client.get(
            "/api/units/101/work/summary?start_date=2020-01-01&end_date=2020-01-02"
        ).json()["tasks"]["open"]
        == 0
    )
    assert client.get("/api/units/101/work/summary?owner_id=103").status_code == 404
    db.add(
        Opportunity(
            id=5001, company_id=102, business_unit_id=101, title="Drugi klijent"
        )
    )
    db.flush()
    db.add(
        Task(
            company_id=101,
            business_unit_id=101,
            opportunity_id=5001,
            assignee_id=102,
            creator_id=102,
            title="Pogrešna veza",
            due_at=datetime.now(timezone.utc),
        )
    )
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


def test_profile_reminder_list_is_company_scoped(client, db):
    from app.reminders import deliver_due

    login(client)
    now = datetime.now(timezone.utc)
    first = create(
        client,
        assignee_id=101,
        due_at=(now + timedelta(hours=1)).isoformat(),
        remind_at=(now - timedelta(seconds=1)).isoformat(),
    )
    create(
        client,
        company_id=102,
        assignee_id=101,
        title="Druga firma",
        due_at=(now + timedelta(hours=1)).isoformat(),
        remind_at=(now - timedelta(seconds=1)).isoformat(),
    )
    assert deliver_due(db, now) == 2
    db.commit()
    rows = client.get("/api/units/101/reminders?company_id=101").json()
    assert rows["total"] == 1 and rows["items"][0]["task_id"] == first["id"]


def test_work_validation_explains_dates_without_echoing_inputs(client):
    login(client, "sales")
    response = client.post(
        "/api/units/101/tasks",
        json={**TASK, "due_at": "bad-private-input"},
        headers=ORIGIN,
    )
    assert response.status_code == 422
    assert "datume" in response.json()["detail"]
    assert "bad-private-input" not in response.text


def test_archived_task_can_be_found_and_restored_without_reactivation(client):
    login(client, "sales")
    task = create(client)
    path = f"/api/units/101/tasks/{task['id']}"
    response = client.delete(path + "?version=1", headers=ORIGIN)
    assert response.status_code == 200
    assert client.get("/api/units/101/tasks").json()["total"] == 0
    archived = client.get("/api/units/101/tasks?include_archived=true").json()
    assert archived["total"] == 1 and archived["items"][0]["archived_at"]
    restored = client.post(path + "/restore?version=2", headers=ORIGIN)
    assert restored.status_code == 200 and restored.json()["archived_at"] is None
    assert (
        restored.json()["status"] == "cancelled"
    )  # Restore must not reschedule a past reminder.
    assert client.get("/api/units/101/tasks").json()["total"] == 1
    assert len(client.get(path + "/history").json()) == 3


def test_worker_retries_database_failure_and_delivers_once(client, db):
    from app.reminders import serve
    from app.work_models import Reminder
    from sqlalchemy import select
    from sqlalchemy.exc import OperationalError
    from contextlib import contextmanager
    from threading import Event

    login(client, "sales")
    now = datetime.now(timezone.utc)
    create(
        client,
        due_at=(now + timedelta(hours=1)).isoformat(),
        remind_at=(now - timedelta(seconds=1)).isoformat(),
    )
    stop = Event()
    attempts = []

    @contextmanager
    def sessions():
        attempts.append(1)
        if len(attempts) == 1:
            raise OperationalError("test", {}, Exception("temporary database outage"))
        yield db
        stop.set()

    assert serve(sessions, stop=stop, interval=0) is True
    assert len(attempts) == 2
    assert db.scalar(select(Reminder)).status == "delivered"


def test_history_resolves_assignment_names_without_losing_raw_ids(client):
    login(client)
    task = create(client)
    path = f"/api/units/101/tasks/{task['id']}"
    assert (
        client.patch(
            path, json={**TASK, "assignee_id": 101, "version": 1}, headers=ORIGIN
        ).status_code
        == 200
    )
    event = client.get(path + "/history").json()[-1]
    assert event["changes"]["assignee_id"] == {"from": 102, "to": 101}
    assert event["display_changes"]["assignee_id"] == {"from": "sales", "to": "manager"}


def test_completed_activity_pagination_uses_execution_time(client):
    login(client, "sales")
    body = {"company_id": 101, "assignee_id": 102, "kind": "call", "status": "done"}
    first = client.post(
        "/api/units/101/activities",
        json={
            **body,
            "title": "Prvi izvršeni poziv",
            "scheduled_at": "2026-12-20T12:00:00+01:00",
            "occurred_at": "2026-01-01T12:00:00+01:00",
        },
        headers=ORIGIN,
    )
    assert first.status_code == 201
    second = client.post(
        "/api/units/101/activities",
        json={
            **body,
            "title": "Drugi izvršeni poziv",
            "scheduled_at": "2026-01-01T12:00:00+01:00",
            "occurred_at": "2026-01-02T12:00:00+01:00",
        },
        headers=ORIGIN,
    )
    assert second.status_code == 201
    page = client.get("/api/units/101/activities?status=done&limit=1").json()
    assert page["items"][0]["id"] == first.json()["id"]


def test_archiving_a_completed_task_records_all_changed_fields(client):
    login(client, "sales")
    task = create(client, status="done")
    path = f"/api/units/101/tasks/{task['id']}"
    archived = client.delete(path + "?version=1", headers=ORIGIN).json()
    event = client.get(path + "/history").json()[-1]
    assert datetime.fromisoformat(
        event["changes"]["archived_at"]["to"]
    ) == datetime.fromisoformat(archived["archived_at"])
    assert datetime.fromisoformat(
        event["changes"]["completed_at"]["from"]
    ) == datetime.fromisoformat(task["completed_at"])
    assert event["changes"]["completed_at"]["to"] is None


def test_work_list_batches_related_names_for_a_full_page(client, db):
    from app.work_models import Task
    from sqlalchemy import event

    login(client, "sales")
    db.add_all(
        [
            Task(
                business_unit_id=101,
                company_id=101,
                assignee_id=102,
                creator_id=102,
                title=f"Batch {i}",
                due_at=datetime.now(timezone.utc),
            )
            for i in range(200)
        ]
    )
    db.commit()
    statements = []

    def counted(conn, cursor, statement, params, context, many):
        if statement.lstrip().upper().startswith("SELECT"):
            statements.append(statement)

    event.listen(db.bind, "before_cursor_execute", counted)
    try:
        response = client.get("/api/units/101/tasks?limit=200")
    finally:
        event.remove(db.bind, "before_cursor_execute", counted)
    assert response.status_code == 200 and len(response.json()["items"]) == 200
    assert response.json()["items"][0]["company_name"] == "Test firma A"
    assert len(statements) <= 12
