"""Live, scoped contract reminders; no duplicated tasks or background mail jobs."""
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from ..access import visible_query
from ..db import get_db
from ..models import Company, User
from ..security import current_user

router = APIRouter(prefix='/api/units/{unit_id}/contract-reminders', tags=['Ugovori'])


def contract_today() -> date:
    return datetime.now(ZoneInfo('Europe/Belgrade')).date()


class ContractReminder(BaseModel):
    company_id: int
    company_name: str
    contract_signed_on: date | None
    contract_expires_on: date
    days_remaining: int


class ContractReminders(BaseModel):
    today: date
    reminder_days: int
    total: int
    items: list[ContractReminder]


@router.get('', response_model=ContractReminders)
def reminders(unit_id: int, limit: int = Query(5, ge=1, le=100), offset: int = Query(0, ge=0),
               user: User = Depends(current_user), db: Session = Depends(get_db)):
    today = contract_today()
    query = visible_query(db, user, unit_id).where(
        Company.is_demo.is_(False), Company.contract_expires_on.is_not(None),
        Company.contract_expires_on <= today + timedelta(days=30))
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    companies = db.scalars(query.order_by(Company.contract_expires_on, Company.id).limit(limit).offset(offset)).all()
    return {'today': today, 'reminder_days': 30, 'total': total, 'items': [
        {'company_id': c.id, 'company_name': c.name, 'contract_signed_on': c.contract_signed_on,
         'contract_expires_on': c.contract_expires_on, 'days_remaining': (c.contract_expires_on-today).days}
        for c in companies]}
