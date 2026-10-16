"""Resolve real company email recipients without asking a model to invent addresses."""
from pydantic import BaseModel, EmailStr, TypeAdapter, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import Contact

EMAIL = TypeAdapter(EmailStr)


class AiRecipient(BaseModel):
    id: int
    name: str
    position: str | None
    email: EmailStr


def company_recipients(db: Session, unit_id: int, company_id: int,
                       contact_id: int | None = None) -> list[AiRecipient]:
    # The caller must authorize the company first. Both keys remain constrained
    # here so contact resolution cannot cross either boundary.
    base = select(Contact).where(Contact.business_unit_id == unit_id, Contact.company_id == company_id)
    if contact_id is not None:
        base = base.where(Contact.id == contact_id)
    recipients = []
    seen = set()
    for contact in db.scalars(base.order_by(Contact.id)):
        try:
            email = EMAIL.validate_python(contact.email)
        except ValidationError:
            continue  # Blank/invalid historical email values must never become recipients.
        key = email.casefold()
        if key in seen:
            continue
        seen.add(key)
        recipients.append(AiRecipient(id=contact.id, name=contact.name, position=contact.position, email=email))
    return recipients
