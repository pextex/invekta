from datetime import datetime, timedelta, timezone
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator
from sqlalchemy import select, func, delete
from sqlalchemy.orm import Session
from ..access import visible_company, visible_query
from ..ai_provider import generate
from ..message_templates import generate as generate_template
from ..config import get_settings
from ..brand_knowledge import content_for
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

router = APIRouter(prefix="/api/units/{unit_id}/ai", tags=["AI drafts"])


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
    goal: Literal["meeting", "introduction", "information", "proposal"] = "meeting"
    mode: Literal["email", "reply", "follow_up"] = "email"
    tone: Literal["professional", "friendly", "concise"] = "professional"
    language: Literal["sr", "en"] = "sr"
    instructions: str = Field(default="", max_length=4000)
    incoming_message: str = Field(default="", max_length=10000)

    @model_validator(mode="after")
    def valid_text(self):
        if self.mode == "reply" and not self.incoming_message.strip():
            raise ValueError("Unesite instrukcije i poruku na koju odgovarate.")
        return self


class EditInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    subject: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=20000)
    recipient: EmailStr | None = Field(default=None, max_length=254)
    version: int = Field(ge=1)

    @model_validator(mode="after")
    def not_blank(self):
        if not self.subject.strip() or not self.body.strip():
            raise ValueError("Nacrt ne može biti prazan.")
        return self


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
        "configured": bool(settings.crm_groq_api_key) if settings.crm_ai_enabled else True,
        "disabled": not settings.crm_ai_enabled,
        "model": settings.crm_groq_model if settings.crm_ai_enabled else "local-templates",
        "engine": "groq" if settings.crm_ai_enabled else "templates",
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


@router.post("/drafts", status_code=201, dependencies=[Depends(require_origin)])
def create_draft(
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
    context = {
        "sender": {
            "name": user.name,
            "organization": business_unit.name,
        },
        "company": {
            "name": company.name,
            "city": company.city,
            "sector": company.sector,
        },
        "contact": {"name": contact.name, "position": contact.position}
        if contact
        else None,
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
    if settings.crm_ai_enabled and not settings.crm_groq_api_key:
        raise HTTPException(503, "Invekta AI nije povezan. Administrator treba da podesi Groq ključ na serveru.")
    knowledge = db.get(AiBrandKnowledge, unit_id)
    context["brand_knowledge"] = {
        "brand": business_unit.name,
        "content": content_for(business_unit, knowledge),
    }
    recipient = contact.email if contact else None
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
    result = generate(context) if settings.crm_ai_enabled else generate_template(context)
    # Recheck after the external call: a revoked session must not save a draft.
    db.expire_all()
    verified = current_user(request, db)
    visible_company(db, verified, unit_id, data.company_id)
    draft = AiDraft(
        actor_id=actor_id,
        business_unit_id=unit_id,
        company_id=data.company_id,
        mode=data.mode,
        subject=result.subject,
        body=result.body,
        recipient=recipient,
        model=settings.crm_groq_model if settings.crm_ai_enabled else "local-templates",
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return output(draft)


@router.patch("/drafts/{draft_id}", dependencies=[Depends(require_origin)])
def update_draft(
    unit_id: int,
    draft_id: int,
    data: EditInput,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    draft = db.scalar(
        query(db, user, unit_id).where(AiDraft.id == draft_id).with_for_update()
    )
    if draft is None:
        raise HTTPException(404, "Nacrt nije pronađen.")
    if draft.version != data.version:
        raise HTTPException(
            409, "Nacrt je promenjen u drugom prozoru. Ponovo ga otvorite iz spiska."
        )
    draft.subject = data.subject
    draft.body = data.body
    draft.recipient = str(data.recipient) if data.recipient else None
    draft.version += 1
    db.commit()
    db.refresh(draft)
    return output(draft)
