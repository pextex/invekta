from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from ..business_types import unit_categories
from ..db import get_db
from ..models import Membership, MonthlyTarget, TeamBonus, User
from ..schemas import TeamBonusInput, TeamBonusOutput
from ..security import current_user, membership, require_origin
from ..target_progress import achievement_totals, month_bounds

router = APIRouter(prefix="/api/units/{unit_id}/team-bonus", tags=["Kolektivni bonus"])

@router.get("", response_model=TeamBonusOutput)
def team_bonus(unit_id: int, month: str = Query(pattern=r"^[0-9]{4}-(0[1-9]|1[0-2])$"),
               user: User = Depends(current_user), db: Session = Depends(get_db)):
    member = membership(db, user, unit_id)
    first, after = month_bounds(month)
    categories = unit_categories(db, unit_id)
    ids = list(db.scalars(select(User.id).join(Membership, Membership.user_id == User.id).where(
        Membership.business_unit_id == unit_id, Membership.enabled.is_(True), Membership.role == "sales", User.active.is_(True))).all())
    achieved = achievement_totals(db, unit_id, first, after, ids)
    relevant = [(owner, value, count) for (owner, kind), (value, count) in achieved.items() if kind in categories]
    total = sum((value for _, value, _ in relevant), Decimal("0"))
    own = sum((value for owner, value, _ in relevant if owner == user.id), Decimal("0"))
    allocated = db.scalar(select(func.sum(MonthlyTarget.target_amount)).where(
        MonthlyTarget.business_unit_id == unit_id, MonthlyTarget.period == first,
        MonthlyTarget.user_id.in_(ids), MonthlyTarget.category.in_(categories))) or Decimal("0")
    bonus = db.scalar(select(TeamBonus).where(TeamBonus.business_unit_id == unit_id, TeamBonus.period == first))
    return {"month": month, "target_amount": bonus.target_amount if bonus else None,
            "reward_note": bonus.reward_note if bonus else None, "version": bonus.version if bonus else None,
            "can_manage": member.role == "admin" or user.is_platform_admin,
            "individual_targets_total": allocated, "achieved_amount": total, "my_achieved_amount": own,
            "salespeople_count": len(ids), "achieved_count": sum(count for _, _, count in relevant),
            "unlocked": bool(bonus and bonus.target_amount > 0 and total >= bonus.target_amount)}

@router.put("", response_model=TeamBonusOutput, dependencies=[Depends(require_origin)])
def set_team_bonus(unit_id: int, data: TeamBonusInput,
                   user: User = Depends(current_user), db: Session = Depends(get_db)):
    member = membership(db, user, unit_id)
    if member.role != "admin" and not user.is_platform_admin:
        raise HTTPException(403, "Samo administrator može postavljati kolektivni cilj i bonus.")
    first, _ = month_bounds(data.month)
    bonus = db.scalar(select(TeamBonus).where(TeamBonus.business_unit_id == unit_id, TeamBonus.period == first).with_for_update())
    if (bonus is None and data.version is not None) or (bonus is not None and bonus.version != data.version):
        raise HTTPException(409, "Kolektivni cilj je izmenjen. Osvežite pregled.")
    if bonus is None:
        bonus = TeamBonus(business_unit_id=unit_id, period=first, target_amount=data.target_amount, reward_note=data.reward_note)
        db.add(bonus)
    else:
        bonus.target_amount = data.target_amount
        bonus.reward_note = data.reward_note
        bonus.version += 1
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Kolektivni cilj je u međuvremenu dodat. Osvežite pregled.")
    return team_bonus(unit_id, data.month, user, db)
