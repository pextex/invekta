from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from ..target_progress import month_bounds, achievement_totals
from ..business_types import unit_categories
from ..db import get_db
from ..models import Membership, MonthlyTarget, User
from ..schemas import TargetsInput, TargetsOutput
from ..security import current_user, membership, require_origin

router = APIRouter(prefix="/api/units/{unit_id}/targets", tags=["Mesečni targeti"])


@router.get("", response_model=TargetsOutput)
def targets(unit_id: int, month: str = Query(pattern=r"^[0-9]{4}-(0[1-9]|1[0-2])$"),
            user: User = Depends(current_user), db: Session = Depends(get_db)):
    member = membership(db, user, unit_id)
    first, after = month_bounds(month)
    categories = unit_categories(db, unit_id)
    people_query = select(User).join(Membership, Membership.user_id == User.id).where(
        Membership.business_unit_id == unit_id, Membership.enabled.is_(True),
        Membership.role.in_(("sales", "marketing")), User.active.is_(True))
    if member.role in ("sales", "marketing"):
        people_query = people_query.where(User.id == user.id)
    people = db.scalars(people_query.order_by(User.name, User.id)).all()
    ids = [person.id for person in people]
    goals = db.scalars(select(MonthlyTarget).where(MonthlyTarget.business_unit_id == unit_id,
                      MonthlyTarget.period == first, MonthlyTarget.user_id.in_(ids))).all()
    lookup = {(goal.user_id, goal.category): goal for goal in goals}
    achieved = achievement_totals(db, unit_id, first, after, ids)
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
    if owner is None or not owner.active or owner_member is None or not owner_member.enabled or owner_member.role not in ("sales", "marketing"):
        raise HTTPException(422, "Izaberite aktivnog korisnika prodaje ili marketinga iz ove firme.")
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
