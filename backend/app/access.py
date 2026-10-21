from fastapi import HTTPException
from sqlalchemy import select, false
from sqlalchemy.orm import Session
from .models import Company, User
from .security import membership


def visible_query(db: Session, user: User, unit_id: int):
    member = membership(db, user, unit_id)
    if member.role == "marketing":
        return select(Company).where(Company.business_unit_id == unit_id, false())
    query = select(Company).where(Company.business_unit_id == unit_id)
    if member.role in ("sales", "marketing"):
        query = query.where(Company.owner_id == user.id)
    return query


def visible_company(db: Session, user: User, unit_id: int, company_id: int) -> Company:
    company = db.scalar(
        visible_query(db, user, unit_id).where(Company.id == company_id)
    )
    if company is None:
        raise HTTPException(404, "Kompanija nije pronađena.")
    return company
