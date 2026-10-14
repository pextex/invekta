from fastapi import HTTPException
from sqlalchemy.orm import Session
from .models import BusinessUnit

BUSINESS_TYPES = {"LUU": ("sale",), "INVEKTA": ("contracted",), "CENOBOTS": ("sale", "leasing", "rental")}


def unit_categories(db: Session, unit_id: int) -> tuple[str, ...]:
    unit = db.get(BusinessUnit, unit_id)
    if unit is None:
        raise HTTPException(404, "Firma nije pronađena.")
    return BUSINESS_TYPES.get(unit.code, ("sale",))


def resolve_business_type(db: Session, unit_id: int, value: str | None) -> str | None:
    categories = unit_categories(db, unit_id)
    if value is None:
        return categories[0] if len(categories) == 1 else None
    if value not in categories:
        raise HTTPException(422, "Vrsta posla nije dozvoljena za ovu firmu.")
    return value
