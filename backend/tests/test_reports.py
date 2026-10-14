from datetime import datetime, timezone
from decimal import Decimal
from app.models import Opportunity, OpportunityStageChange
from test_crm import login, sales_records, ORIGIN


def add_event(db, id, opportunity_id, actor, before, after, timestamp):
    db.add(OpportunityStageChange(id=id, opportunity_id=opportunity_id, business_unit_id=101,
        actor_id=actor, from_stage=before, to_stage=after,
        changed_at=datetime.fromisoformat(timestamp), amount=Decimal("100.10")))


def test_reports_use_event_date_belgrade_scope_and_full_month(client, db, sales_records):
    add_event(db, 4001, 2001, 102, "Kontaktiran", "Ponuda", "2026-10-13T21:59:59+00:00")
    add_event(db, 4002, 2001, 102, "Ponuda", "Pregovori", "2026-10-13T22:00:00+00:00")
    add_event(db, 4003, 2001, 102, "Pregovori", "Dobijeno", "2026-10-14T21:59:59+00:00")
    add_event(db, 4004, 2001, 102, "Dobijeno", "Izgubljeno", "2026-10-14T22:00:00+00:00")
    add_event(db, 4005, 2002, 103, "Ponuda", "Dobijeno", "2026-10-14T12:00:00+00:00")
    db.commit()
    params = {"date_from": "2026-10-14", "date_to": "2026-10-14"}
    assert client.get("/api/units/101/reports", params=params).status_code == 401
    login(client, "sales")
    report = client.get("/api/units/101/reports", params=params).json()
    assert report["total"] == 2 and report["opportunity_count"] == 1
    assert [row["id"] for row in report["items"]] == [4003, 4002]
    assert report["realized_count"] == 1 and report["stage_change_count"] == 2
    assert report["items"][0]["amount"] == "100.10"
    assert client.get("/api/units/102/reports", params=params).status_code == 403
    login(client)
    assert client.get("/api/units/101/reports", params=params).json()["total"] == 3
    monthly = client.get("/api/units/101/reports", params={"date_from": "2026-10-01", "date_to": "2026-10-31"}).json()
    assert monthly["total"] == 5 and monthly["opportunity_count"] == 2
    db.get(Opportunity, 2002).is_demo = True
    db.commit()
    assert client.get("/api/units/101/reports", params=params).json()["total"] == 2
    assert client.get("/api/units/101/reports", params={**params, "include_demo": True}).json()["total"] == 3
    assert client.get("/api/units/101/reports", params={"date_from": "2026-10-31", "date_to": "2026-10-01"}).status_code == 422
    empty = client.get("/api/units/101/reports", params={"date_from": "2025-01-01", "date_to": "2025-01-01"}).json()
    assert empty["total"] == 0 and empty["items"] == []


def test_reports_paginate_all_changes_and_keep_amount_snapshot(client, db, sales_records):
    for index in range(53):
        add_event(db, 5000 + index, 2001, 102, "Kontaktiran", "Ponuda", "2026-10-14T12:00:00+00:00")
    db.commit()
    login(client, "sales")
    params = {"date_from": "2026-10-14", "date_to": "2026-10-14"}
    first = client.get("/api/units/101/reports", params=params).json()
    second = client.get("/api/units/101/reports", params={**params, "offset": 50}).json()
    assert first["total"] == second["total"] == 53
    assert len(first["items"]) == 50 and len(second["items"]) == 3
    assert len({row["id"] for row in first["items"] + second["items"]}) == 53
    db.get(Opportunity, 2001).amount = Decimal("999.99")
    db.commit()
    assert client.get("/api/units/101/reports", params=params).json()["items"][0]["amount"] == "100.10"


def test_edits_and_creations_are_logged_without_false_noop_events(client, db, sales_records):
    from test_crm import OPPORTUNITY
    from sqlalchemy import select
    login(client, "sales")
    created = client.post("/api/units/101/opportunities", json=OPPORTUNITY, headers=ORIGIN).json()
    history = client.get(f"/api/units/101/opportunities/{created['id']}/stage-history").json()
    assert len(history) == 1
    entry = db.get(OpportunityStageChange, history[0]["id"])
    assert entry.amount == Decimal("12500.55") and entry.changes["title"]["after"] == OPPORTUNITY["title"]
    payload = {key: value for key, value in OPPORTUNITY.items() if key != "company_id"}
    payload.update(version=1, amount="45.67", notes="Nova beleška")
    path = f"/api/units/101/opportunities/{created['id']}"
    assert client.patch(path, json=payload, headers=ORIGIN).status_code == 200
    rows = db.scalars(select(OpportunityStageChange).where(OpportunityStageChange.opportunity_id == created["id"]).order_by(OpportunityStageChange.id)).all()
    assert len(rows) == 2
    assert rows[-1].from_stage == rows[-1].to_stage == "Novi lead"
    assert rows[-1].amount == Decimal("45.67")
    assert rows[-1].changes["amount"] == {"before": "12500.55", "after": "45.67"}
    payload["version"] = 2
    assert client.patch(path, json=payload, headers=ORIGIN).status_code == 200
    assert len(client.get(path + "/stage-history").json()) == 2
