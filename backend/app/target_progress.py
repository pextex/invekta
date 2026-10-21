from decimal import Decimal
from datetime import date, datetime, time
from zoneinfo import ZoneInfo
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from .models import Company, Opportunity, OpportunityStageChange, MarketingOrder

def month_bounds(value: str):
    try:
        first = date.fromisoformat(value + "-01")
        if first.year >= 9999:
            raise ValueError
        after = date(first.year + 1, 1, 1) if first.month == 12 else date(first.year, first.month + 1, 1)
    except ValueError:
        raise HTTPException(422, "Izaberite ispravan mesec.")
    return first, after


def achievement_totals(db: Session, unit_id: int, first: date, after: date, ids: list[int]):
    history = OpportunityStageChange
    # Use the most recent actual transition into Realizovano for each currently
    # realized opportunity. Metadata edits and repeated visits cannot duplicate it.
    latest = select(history.opportunity_id.label("opportunity_id"), func.max(history.id).label("history_id")).where(
        history.business_unit_id == unit_id, history.to_stage == "Dobijeno",
        (history.from_stage.is_(None) | (history.from_stage != history.to_stage))
    ).group_by(history.opportunity_id).subquery()
    zone = ZoneInfo("Europe/Belgrade")
    category = func.coalesce(history.business_type, Opportunity.business_type)
    amounts = db.execute(select(Company.owner_id, category, func.sum(history.amount), func.count())
        .select_from(Opportunity).join(Company, Company.id == Opportunity.company_id)
        .join(latest, latest.c.opportunity_id == Opportunity.id)
        .join(history, history.id == latest.c.history_id)
        .where(Opportunity.business_unit_id == unit_id, Company.owner_id.in_(ids),
               Opportunity.stage == "Dobijeno", Opportunity.is_demo.is_(False), Company.is_demo.is_(False),
               history.amount.is_not(None), history.changed_at >= datetime.combine(first, time.min, zone),
               history.changed_at < datetime.combine(after, time.min, zone))
        .group_by(Company.owner_id, category)).all()
    totals = {(owner, kind): (amount or Decimal("0"), count) for owner, kind, amount, count in amounts}
    orders = db.execute(select(MarketingOrder.owner_id, MarketingOrder.business_type,
        func.sum(MarketingOrder.amount), func.count()).where(
            MarketingOrder.business_unit_id == unit_id, MarketingOrder.owner_id.in_(ids),
            MarketingOrder.status == "won", MarketingOrder.amount.is_not(None),
            MarketingOrder.business_type.is_not(None),
            MarketingOrder.realized_at >= datetime.combine(first, time.min, zone),
            MarketingOrder.realized_at < datetime.combine(after, time.min, zone)
        ).group_by(MarketingOrder.owner_id, MarketingOrder.business_type)).all()
    for owner, kind, amount, count in orders:
        previous, previous_count = totals.get((owner, kind), (Decimal("0"), 0))
        totals[(owner, kind)] = (previous + (amount or Decimal("0")), previous_count + count)
    return totals
