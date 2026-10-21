from datetime import datetime, timezone
from decimal import Decimal
import pytest
from sqlalchemy import select
from app.models import BusinessUnit, Company, Membership, MonthlyTarget, Opportunity, OpportunityStageChange
from test_api import login, ORIGIN


def goal(user=102, kind="sale", amount="1000.00", version=None):
    return {"month": "2026-10", "user_id": user, "targets": [{"category": kind, "target_amount": amount, "version": version}]}


def test_goal_permissions_conflicts_and_month_isolation(client, db):
    assert client.get("/api/units/101/targets?month=2026-10").status_code == 401
    login(client)
    response = client.put("/api/units/101/targets", json=goal(), headers=ORIGIN)
    assert response.status_code == 200
    person = next(p for p in response.json()["salespeople"] if p["user_id"] == 102)
    assert person["targets"][0]["target_amount"] == "1000.00" and person["targets"][0]["version"] == 1
    assert client.put("/api/units/101/targets", json=goal(), headers=ORIGIN).status_code == 409
    assert client.put("/api/units/101/targets", json=goal(amount="1500.50", version=1), headers=ORIGIN).status_code == 200
    assert client.put("/api/units/101/targets", json=goal(version=1), headers=ORIGIN).status_code == 409
    login(client, "sales")
    own = client.get("/api/units/101/targets?month=2026-10").json()
    assert not own["can_manage"] and [p["user_id"] for p in own["salespeople"]] == [102]
    assert own["salespeople"][0]["targets"][0]["target_amount"] == "1500.50"
    assert client.put("/api/units/101/targets", json=goal(version=2), headers=ORIGIN).status_code == 403
    assert client.get("/api/units/102/targets?month=2026-10").status_code == 403
    assert client.get("/api/units/101/targets?month=2026-11").json()["salespeople"][0]["targets"][0]["target_amount"] is None
    login(client, "other")
    assert [p["user_id"] for p in client.get("/api/units/101/targets?month=2026-10").json()["salespeople"]] == [103]


def test_achievement_counts_latest_realization_once_and_freezes_value(client, db):
    login(client)
    db.add(Opportunity(id=8001, company_id=101, business_unit_id=101, title="Realizacija", amount=Decimal("9999"), stage="Dobijeno", business_type="sale"))
    db.flush()
    for i, before, after, stamp, amount in [(8101, "Ponuda", "Dobijeno", "2026-10-13T21:59:59+00:00", "100"),
        (8102, "Dobijeno", "Pregovori", "2026-10-14T11:00:00+00:00", "100"),
        (8103, "Pregovori", "Dobijeno", "2026-10-14T12:00:00+00:00", "200.25"),
        (8104, "Dobijeno", "Dobijeno", "2026-10-14T13:00:00+00:00", "9999")]:
        db.add(OpportunityStageChange(id=i, opportunity_id=8001, business_unit_id=101, actor_id=102, from_stage=before, to_stage=after,
            changed_at=datetime.fromisoformat(stamp), amount=Decimal(amount), business_type="sale"))
    db.commit()
    def progress():
        data = client.get("/api/units/101/targets?month=2026-10").json()
        return next(p for p in data["salespeople"] if p["user_id"] == 102)["targets"][0]
    assert progress()["achieved_count"] == 1 and progress()["achieved_amount"] == "200.25"
    db.get(Opportunity, 8001).stage = "Pregovori"
    db.commit()
    assert progress()["achieved_count"] == 0
    db.get(Opportunity, 8001).stage = "Dobijeno"
    db.get(Opportunity, 8001).is_demo = True
    db.commit()
    assert progress()["achieved_count"] == 0


def test_cenobots_categories_are_separate_and_atomic(client, db):
    unit = db.scalar(select(BusinessUnit).where(BusinessUnit.code == "CENOBOTS"))
    assert unit
    db.add_all([Membership(user_id=101, business_unit_id=unit.id, role="manager"), Membership(user_id=102, business_unit_id=unit.id, role="sales")])
    db.flush()
    db.add(Company(id=8200, business_unit_id=unit.id, owner_id=102, name="Test Cenobots", city="Beograd", sector="Test"))
    db.commit()
    login(client)
    payload = {"month": "2026-10", "user_id": 102, "targets": [{"category": kind, "target_amount": "100", "version": None} for kind in ("sale", "leasing", "rental")]}
    response = client.put(f"/api/units/{unit.id}/targets", json=payload, headers=ORIGIN)
    assert response.status_code == 200 and response.json()["categories"] == ["sale", "leasing", "rental"]
    bad = {**payload, "targets": [{"category": "sale", "target_amount": "200", "version": 1}, {"category": "leasing", "target_amount": "200", "version": 99}]}
    assert client.put(f"/api/units/{unit.id}/targets", json=bad, headers=ORIGIN).status_code == 409
    db.expire_all()
    assert db.scalar(select(MonthlyTarget).where(MonthlyTarget.business_unit_id == unit.id, MonthlyTarget.category == "sale")).target_amount == Decimal("100")
    opportunity = {"company_id": 8200, "title": "Test najam", "stage": "Dobijeno", "amount": "55.50"}
    assert client.post(f"/api/units/{unit.id}/opportunities", json=opportunity, headers=ORIGIN).status_code == 422
    assert client.post(f"/api/units/{unit.id}/opportunities", json={**opportunity, "business_type": "contracted"}, headers=ORIGIN).status_code == 422
    created = client.post(f"/api/units/{unit.id}/opportunities", json={**opportunity, "business_type": "rental"}, headers=ORIGIN)
    assert created.status_code == 201
    record = created.json()
    row = db.scalar(select(OpportunityStageChange).where(OpportunityStageChange.opportunity_id == record["id"]))
    row.changed_at = datetime(2026, 10, 14, 12, tzinfo=timezone.utc)
    db.commit()
    data = client.get(f"/api/units/{unit.id}/targets?month=2026-10").json()["salespeople"][0]["targets"]
    assert next(t for t in data if t["category"] == "rental")["achieved_amount"] == "55.50"
    assert all(t["achieved_count"] == 0 for t in data if t["category"] != "rental")


def test_goal_validation_and_csrf(client, db):
    login(client)
    for changes in [{"user_id": 104}, {"user_id": 101}, {"month": "2026-13"}, {"month": "0000-01"},
                    {"targets": [{"category": "sale", "target_amount": "-1"}]},
                    {"targets": [{"category": "sale", "target_amount": "0.001"}]},
                    {"targets": [{"category": "rental", "target_amount": "100"}]}]:
        assert client.put("/api/units/101/targets", json={**goal(), **changes}, headers=ORIGIN).status_code == 422
    assert client.put("/api/units/101/targets", json=goal()).status_code == 403
    assert db.scalar(select(MonthlyTarget)) is None


def test_invekta_allows_only_contracted_targets_and_daily_timezone_boundary(client, db):
    unit = db.scalar(select(BusinessUnit).where(BusinessUnit.code == "INVEKTA"))
    assert unit
    db.add_all([Membership(user_id=101, business_unit_id=unit.id, role="manager"), Membership(user_id=102, business_unit_id=unit.id, role="sales")])
    db.flush()
    db.add(Company(id=8300, business_unit_id=unit.id, owner_id=102, name="Test ugovor", city="Beograd", sector="Test"))
    db.flush()
    db.add(Opportunity(id=8301, company_id=8300, business_unit_id=unit.id, title="Ugovor", amount=Decimal("99.99"), stage="Dobijeno", business_type="contracted"))
    db.flush()
    db.add(OpportunityStageChange(id=8302, opportunity_id=8301, business_unit_id=unit.id, actor_id=102, from_stage="Ponuda", to_stage="Dobijeno", changed_at=datetime.fromisoformat("2026-09-30T22:00:00+00:00"), amount=Decimal("99.99"), business_type="contracted"))
    db.commit()
    login(client)
    assert client.put(f"/api/units/{unit.id}/targets", json=goal(kind="sale"), headers=ORIGIN).status_code == 422
    report = client.put(f"/api/units/{unit.id}/targets", json=goal(kind="contracted"), headers=ORIGIN).json()
    assert report["categories"] == ["contracted"]
    assert report["salespeople"][0]["targets"][0]["achieved_amount"] == "99.99"
    previous = client.get(f"/api/units/{unit.id}/targets?month=2026-09").json()
    assert previous["salespeople"][0]["targets"][0]["achieved_count"] == 0


def test_realized_marketing_orders_merge_with_sales_in_personal_and_team_targets(client, db):
    from app.models import MarketingOrder
    # Exercise the migrated PostgreSQL schema and both public target endpoints.
    db.get(Membership, (103, 101)).role = 'marketing'
    db.add(Opportunity(id=8401, company_id=101, business_unit_id=101, title='Sale', amount=Decimal('100'), stage='Dobijeno', business_type='sale'))
    db.flush()
    stamp = datetime(2026, 10, 14, 12, tzinfo=timezone.utc)
    db.add(OpportunityStageChange(id=8402, opportunity_id=8401, business_unit_id=101, actor_id=102, from_stage='Ponuda', to_stage='Dobijeno', changed_at=stamp, amount=Decimal('100'), business_type='sale'))
    db.add(MarketingOrder(business_unit_id=101, owner_id=103, first_name='Test', last_name='Buyer', phone='0601234567', source='phone', status='won', amount=Decimal('250.25'), business_type='sale', realized_at=stamp))
    db.commit()
    login(client, 'other')
    personal = client.get('/api/units/101/targets?month=2026-10').json()['salespeople']
    assert len(personal) == 1 and personal[0]['user_id'] == 103
    assert personal[0]['targets'][0]['achieved_amount'] == '250.25'
    team = client.get('/api/units/101/team-bonus?month=2026-10').json()
    assert team['achieved_amount'] == '350.25' and team['my_achieved_amount'] == '250.25'
    assert team['achieved_count'] == 2
