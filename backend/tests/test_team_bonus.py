from datetime import date, datetime, timezone
from decimal import Decimal
from sqlalchemy import select
from app.models import Membership, MonthlyTarget, Opportunity, OpportunityStageChange, TeamBonus, User
from test_api import login, ORIGIN

PAYLOAD = {"month": "2026-10", "target_amount": "300.00", "reward_note": "Zajednički bonus tima", "version": None}


def test_collective_bonus_admin_only_and_visible_to_brand_salespeople(client, db):
    assert client.get("/api/units/101/team-bonus?month=2026-10").status_code == 401
    login(client)
    assert client.put("/api/units/101/team-bonus", json=PAYLOAD, headers=ORIGIN).status_code == 403
    db.get(Membership, (101, 101)).role = "admin"
    db.commit()
    result = client.put("/api/units/101/team-bonus", json=PAYLOAD, headers=ORIGIN)
    assert result.status_code == 200 and result.json()["version"] == 1
    assert client.put("/api/units/101/team-bonus", json=PAYLOAD, headers=ORIGIN).status_code == 409
    update = {**PAYLOAD, "version": 1, "target_amount": "400.00"}
    assert client.put("/api/units/101/team-bonus", json=update, headers=ORIGIN).status_code == 200
    login(client, "sales")
    own = client.get("/api/units/101/team-bonus?month=2026-10").json()
    assert own["target_amount"] == "400.00" and own["reward_note"] == PAYLOAD["reward_note"]
    assert own["can_manage"] is False
    assert "salespeople" not in own and "companies" not in own
    assert client.put("/api/units/101/team-bonus", json=update, headers=ORIGIN).status_code == 403
    assert client.get("/api/units/102/team-bonus?month=2026-10").status_code == 403
    login(client, "other")
    assert client.get("/api/units/101/team-bonus?month=2026-10").json()["target_amount"] == "400.00"
    assert client.get("/api/units/101/team-bonus?month=2026-11").json()["target_amount"] is None


def test_collective_target_sums_individual_goals_and_realizations_without_exposing_peers(client, db):
    db.add_all([MonthlyTarget(user_id=owner, business_unit_id=101, period=date(2026, 10, 1), category="sale", target_amount=Decimal("200.00")) for owner in (102, 103)])
    db.add(TeamBonus(business_unit_id=101, period=date(2026, 10, 1), target_amount=Decimal("300.00"), reward_note="Tim"))
    for number, company, amount in [(9101, 101, "100.10"), (9102, 102, "200.20")]:
        db.add(Opportunity(id=number, business_unit_id=101, company_id=company, title="Test tim", amount=Decimal(amount), stage="Dobijeno", business_type="sale"))
        db.flush()
        db.add(OpportunityStageChange(opportunity_id=number, business_unit_id=101, actor_id=101, from_stage="Ponuda", to_stage="Dobijeno", amount=Decimal(amount), business_type="sale", changed_at=datetime(2026, 10, 15, 12, tzinfo=timezone.utc)))
    db.commit()
    login(client, "sales")
    result = client.get("/api/units/101/team-bonus?month=2026-10").json()
    assert result["individual_targets_total"] == "400.00"
    assert result["achieved_amount"] == "300.30" and result["my_achieved_amount"] == "100.10"
    assert result["salespeople_count"] == result["achieved_count"] == 2 and result["unlocked"] is True
    assert [p["user_id"] for p in client.get("/api/units/101/targets?month=2026-10").json()["salespeople"]] == [102]
    db.get(Opportunity, 9102).stage = "Pregovori"
    db.commit()
    assert client.get("/api/units/101/team-bonus?month=2026-10").json()["unlocked"] is False


def test_collective_bonus_validation_csrf_and_disabled_membership(client, db):
    login(client)
    db.get(Membership, (101, 101)).role = "admin"
    db.commit()
    assert client.put("/api/units/101/team-bonus", json=PAYLOAD).status_code == 403
    for extra in [{"target_amount": "-1"}, {"month": "2026-13"}, {"reward_note": "x" * 1001}, {"business_unit_id": 102}, {"target_amount": "0.001"}]:
        assert client.put("/api/units/101/team-bonus", json={**PAYLOAD, **extra}, headers=ORIGIN).status_code == 422
    assert db.scalar(select(TeamBonus)) is None
    login(client, "sales")
    db.get(Membership, (102, 101)).enabled = False
    db.commit()
    assert client.get("/api/units/101/team-bonus?month=2026-10").status_code == 403
