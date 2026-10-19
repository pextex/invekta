from datetime import datetime, timedelta, timezone
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import select, func, delete
from sqlalchemy.orm import Session
from ..access import visible_company, visible_query
from ..ai_provider import GeneratedDraft, generate
from ..ai_recipients import AiRecipient, company_recipients
from ..message_templates import generate as generate_template
from ..config import get_settings
from ..brand_knowledge import content_for
from ..brand_sources import website_reference
from ..db import get_db
from ..models import (
    AiBrandKnowledge,
    AiDraft,
    AiAttempt,
    BusinessUnit,
    Contact,
    Opportunity,
    User,
    Company,
)
from ..security import current_user, require_origin, membership

router = APIRouter(prefix="/api/units/{unit_id}/ai", tags=["Invekta AI"])


class Personalization(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    topic: str = Field(default="", max_length=120)
    offering: str = Field(default="", max_length=600)
    need: str = Field(default="", max_length=600)
    meeting_time: str = Field(default="", max_length=120)
    reply_text: str = Field(default="", max_length=4000)
    greeting: str = Field(default="", max_length=150)
    sender_name: str = Field(default="", max_length=150)
    sender_title: str = Field(default="", max_length=150)
    sender_phone: str = Field(default="", max_length=80)
    sender_email: str = Field(default="", max_length=254)


class GenerateInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    personalization: Personalization = Field(default_factory=Personalization)
    company_id: int = Field(gt=0)
    contact_id: int | None = Field(default=None, gt=0)
    opportunity_id: int | None = Field(default=None, gt=0)
    goal: Literal["auto", "meeting", "introduction", "information", "proposal"] = "auto"
    mode: Literal["auto", "email", "reply", "follow_up"] = "auto"
    tone: Literal["auto", "professional", "friendly", "concise"] = "auto"
    language: Literal["auto", "sr", "en"] = "auto"
    instructions: str = Field(default="", max_length=4000)
    incoming_message: str = Field(default="", max_length=10000)

    @model_validator(mode="after")
    def valid_text(self):
        if self.mode == "auto" and not self.instructions.strip():
            raise ValueError("Napišite kakav mejl želite.")
        if self.mode == "reply" and not self.incoming_message.strip():
            raise ValueError("Unesite instrukcije i poruku na koju odgovarate.")
        return self


class GeneratedMessage(GeneratedDraft):
    recipient: str | None
    recipients: list[AiRecipient]
    model: str
    sources: list[str] = Field(default_factory=list)
    source_status: Literal["live", "cached", "snapshot", "unavailable"] = "unavailable"
    sources_checked_at: str | None = None


def output(draft):
    return {
        key: getattr(draft, key)
        for key in [
            "id",
            "company_id",
            "mode",
            "subject",
            "body",
            "recipient",
            "model",
            "version",
            "created_at",
            "updated_at",
        ]
    }


def query(db, user, unit_id):
    visible = visible_query(db, user, unit_id).with_only_columns(Company.id)
    return select(AiDraft).where(
        AiDraft.business_unit_id == unit_id,
        AiDraft.actor_id == user.id,
        AiDraft.company_id.in_(visible),
    )


@router.get("/status")
def status(
    unit_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)
):
    member = membership(db, user, unit_id)
    settings = get_settings()
    return {
        "configured": bool(settings.crm_gemini_api_key) if settings.crm_ai_enabled else True,
        "disabled": not settings.crm_ai_enabled,
        "model": settings.crm_gemini_model if settings.crm_ai_enabled else "local-templates",
        "engine": "gemini" if settings.crm_ai_enabled else "templates",
        "can_manage_knowledge": member.role == "admin" or user.is_platform_admin,
    }


@router.get("/drafts")
def list_drafts(
    unit_id: int,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    base = query(db, user, unit_id)
    total = db.scalar(select(func.count()).select_from(base.subquery()))
    return {
        "total": total,
        "items": [
            output(d)
            for d in db.scalars(
                base.order_by(AiDraft.id.desc()).offset(offset).limit(limit)
            )
        ],
    }


@router.get("/companies/{company_id}/recipients", response_model=list[AiRecipient])
def email_recipients(unit_id: int, company_id: int,
                     user: User = Depends(current_user), db: Session = Depends(get_db)):
    visible_company(db, user, unit_id, company_id)
    return company_recipients(db, unit_id, company_id)


@router.post("/generate", response_model=GeneratedMessage, dependencies=[Depends(require_origin)])
def generate_message(
    unit_id: int,
    data: GenerateInput,
    request: Request,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    company = visible_company(db, user, unit_id, data.company_id)
    contact = None
    opportunity = None
    if data.contact_id:
        contact = db.scalar(
            select(Contact).where(
                Contact.id == data.contact_id,
                Contact.company_id == company.id,
                Contact.business_unit_id == unit_id,
            )
        )
        if contact is None:
            raise HTTPException(404, "Kontakt nije pronađen u ovoj kompaniji.")
    if data.opportunity_id:
        opportunity = db.scalar(
            select(Opportunity).where(
                Opportunity.id == data.opportunity_id,
                Opportunity.company_id == company.id,
                Opportunity.business_unit_id == unit_id,
            )
        )
        if opportunity is None:
            raise HTTPException(
                404, "Prodajna prilika nije pronađena u ovoj kompaniji."
            )
    business_unit = db.get(BusinessUnit, unit_id)
    if business_unit is None:
        raise HTTPException(404, "Poslovna jedinica nije pronađena.")
    recipients = company_recipients(db, unit_id, company.id, data.contact_id)
    if contact is None and len(recipients) == 1:
        contact = db.get(Contact, recipients[0].id)
    context = {
        "sender": {
            "name": user.name,
            "organization": business_unit.name,
            "organization_code": business_unit.code,
            "phone": user.phone,
        },
        "company": {
            "name": company.name,
            "city": company.city,
            "sector": company.sector,
        },
        "contact": {"name": contact.name, "position": contact.position}
        if contact
        else None,
        "contacts": [{"name": person.name, "position": person.position} for person in recipients],
        "recipient_count": len(recipients),
        "opportunity": {
            "title": opportunity.title,
            "stage": opportunity.stage,
            "amount_rsd": str(opportunity.amount),
            "notes": (opportunity.notes or "")[:4000],
        }
        if opportunity
        else None,
        "personalization": data.personalization.model_dump(),
        "goal": data.goal,
        "mode": data.mode,
        "tone": data.tone,
        "language": data.language,
        "instructions": data.instructions,
        "incoming_message": data.incoming_message,
    }
    settings = get_settings()
    if settings.crm_ai_enabled and not settings.crm_gemini_api_key:
        raise HTTPException(503, "AI asistent nije povezan. Administrator treba da podesi Gemini ključ na serveru.")
    knowledge = db.get(AiBrandKnowledge, unit_id)
    context["brand_knowledge"] = {
        "brand": business_unit.name,
        "content": content_for(business_unit, knowledge),
    }
    actor_id = user.id
    db.scalar(select(User).where(User.id == actor_id).with_for_update())
    now = datetime.now(timezone.utc)
    count = db.scalar(
        select(func.count())
        .select_from(AiAttempt)
        .where(
            AiAttempt.actor_id == actor_id,
            AiAttempt.created_at > now - timedelta(minutes=15),
        )
    ) or 0
    if count >= 20:
        raise HTTPException(
            429, "Najviše 20 generisanja za 15 minuta. Pokušajte kasnije."
        )
    db.execute(delete(AiAttempt).where(AiAttempt.created_at < now - timedelta(days=1)))
    db.add(AiAttempt(actor_id=actor_id))
    db.commit()
    reference = website_reference(business_unit.code) if settings.crm_ai_enabled else {
        "status": "unavailable", "sources": [], "content": "", "checked_at": None,
    }
    context["website_reference"] = reference
    result = generate(context) if settings.crm_ai_enabled else generate_template(context)
    # Recheck after the external call: revoked access must not receive the content.
    db.expire_all()
    verified = current_user(request, db)
    visible_company(db, verified, unit_id, data.company_id)
    recipients = company_recipients(db, unit_id, data.company_id, data.contact_id)
    return {
        "subject": result.subject,
        "body": result.body,
        "recipient": ", ".join(str(person.email) for person in recipients) or None,
        "recipients": recipients,
        "model": settings.crm_gemini_model if settings.crm_ai_enabled else "local-templates",
        "sources": reference["sources"],
        "source_status": reference["status"],
        "sources_checked_at": reference["checked_at"],
    }


@router.post("/drafts", deprecated=True, dependencies=[Depends(require_origin)])
def retired_create_draft(unit_id: int, data: GenerateInput,
                         user: User = Depends(current_user), db: Session = Depends(get_db)):
    visible_company(db, user, unit_id, data.company_id)
    raise HTTPException(410, "Čuvanje nacrta je uklonjeno. Koristite AI asistenta za pripremu i kopiranje mejla.")


@router.patch("/drafts/{draft_id}", deprecated=True, dependencies=[Depends(require_origin)])
def retired_update_draft(unit_id: int, draft_id: int,
                         user: User = Depends(current_user), db: Session = Depends(get_db)):
    draft = db.scalar(query(db, user, unit_id).where(AiDraft.id == draft_id))
    if draft is None:
        raise HTTPException(404, "Nacrt nije pronađen.")
    raise HTTPException(410, "Čuvanje izmena nacrta je uklonjeno. Mejl uredite i kopirajte u odeljku AI asistenta.")
