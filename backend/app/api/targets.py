from datetime import date, datetime, time
from decimal import Decimal
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from ..business_types import unit_categories
from ..db import get_db
from ..models import Company, Membership, MonthlyTarget, Opportunity, OpportunityStageChange, User
from ..schemas import TargetsInput, TargetsOutput
from ..security import current_user, membership, require_origin

router = APIRouter(prefix="/api/units/{unit_id}/targets", tags=["Mesečni targeti"])


def month_bounds(value: str):
    try:
        first = date.fromisoformat(value + "-01")
        if first.year >= 9999:
            raise ValueError
        after = date(first.year + 1, 1, 1) if first.month == 12 else date(first.year, first.month + 1, 1)
    except ValueError:
        raise HTTPException(422, "Izaberite ispravan mesec.")
    return first, after


@router.get("", response_model=TargetsOutput)
def targets(unit_id: int, month: str = Query(pattern=r"^[0-9]{4}-(0[1-9]|1[0-2])$"),
            user: User = Depends(current_user), db: Session = Depends(get_db)):
    member = membership(db, user, unit_id)
    first, after = month_bounds(month)
    categories = unit_categories(db, unit_id)
    people_query = select(User).join(Membership, Membership.user_id == User.id).where(
        Membership.business_unit_id == unit_id, Membership.enabled.is_(True),
        Membership.role == "sales", User.active.is_(True))
    if member.role == "sales":
        people_query = people_query.where(User.id == user.id)
    people = db.scalars(people_query.order_by(User.name, User.id)).all()
    ids = [person.id for person in people]
    goals = db.scalars(select(MonthlyTarget).where(MonthlyTarget.business_unit_id == unit_id,
                      MonthlyTarget.period == first, MonthlyTarget.user_id.in_(ids))).all()
    lookup = {(goal.user_id, goal.category): goal for goal in goals}
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
    achieved = {(owner, kind): (amount, count) for owner, kind, amount, count in amounts}
    return {"month": month, "categories": list(categories), "can_manage": member.role in ("manager", "admin"),
            "salespeople": [{"user_id": person.id, "user_name": person.name, "targets": [
                {"category": kind,
                 "target_amount": lookup[(person.id, kind)].target_amount if (person.id, kind) in lookup else None,
                 "version": lookup[(person.id, kind)].version if (person.id, kind) in lookup else None,
                 "achieved_amount": achieved.get((person.id, kind), (Decimal("0"), 0))[0],
                 "achieved_count": achieved.get((person.id, kind), (Decimal("0"), 0))[1]}
                for kind in categories]} for person in people]}


@router.put("", response_model=TargetsOutput, dependencies=[Depends(require_origin)])
def set_targets(unit_id: int, data: TargetsInput,
                user: User = Depends(current_user), db: Session = Depends(get_db)):
    member = membership(db, user, unit_id)
    if member.role not in ("manager", "admin"):
        raise HTTPException(403, "Samo menadžer ili administrator firme može postavljati targete.")
    first, _ = month_bounds(data.month)
    owner = db.get(User, data.user_id)
    owner_member = db.get(Membership, (data.user_id, unit_id))
    if owner is None or not owner.active or owner_member is None or not owner_member.enabled or owner_member.role != "sales":
        raise HTTPException(422, "Izaberite aktivnog komercijalistu iz ove firme.")
    allowed = unit_categories(db, unit_id)
    if any(entry.category not in allowed for entry in data.targets):
        raise HTTPException(422, "Vrsta targeta nije dozvoljena za ovu firmu.")
    planned = []
    for entry in data.targets:
        goal = db.scalar(select(MonthlyTarget).where(MonthlyTarget.business_unit_id == unit_id,
            MonthlyTarget.user_id == data.user_id, MonthlyTarget.period == first,
            MonthlyTarget.category == entry.category).with_for_update())
        if (goal is None and entry.version is not None) or (goal is not None and entry.version != goal.version):
            raise HTTPException(409, "Target je u međuvremenu izmenjen. Osvežite pregled.")
        planned.append((entry, goal))
    for entry, goal in planned:
        if goal is None:
            db.add(MonthlyTarget(user_id=data.user_id, business_unit_id=unit_id, period=first,
                                category=entry.category, target_amount=entry.target_amount))
        else:
            goal.target_amount = entry.target_amount
            goal.version += 1
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Target je u međuvremenu dodat. Osvežite pregled.")
    return targets(unit_id, data.month, user, db)
