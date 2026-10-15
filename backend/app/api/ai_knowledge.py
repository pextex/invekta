"""Approved knowledge is shared within one brand; only its admins may edit."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import AiBrandKnowledge, BusinessUnit, User
from ..brand_knowledge import content_for
from ..security import current_user, membership, require_origin

router = APIRouter(prefix="/api/units/{unit_id}/ai", tags=["Invekta AI knowledge"])


class KnowledgeInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    content: str = Field(max_length=12000)
    version: int | None = Field(default=None, ge=1)


def output(knowledge, unit=None):
    return {
        "content": content_for(unit, knowledge),
        "version": knowledge.version if knowledge else None,
        "updated_at": knowledge.updated_at if knowledge else None,
    }


@router.get("/knowledge")
def knowledge(unit_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    membership(db, user, unit_id)
    return output(db.get(AiBrandKnowledge, unit_id), db.get(BusinessUnit, unit_id))


@router.put("/knowledge", dependencies=[Depends(require_origin)])
def save_knowledge(unit_id: int, data: KnowledgeInput,
                   user: User = Depends(current_user), db: Session = Depends(get_db)):
    member = membership(db, user, unit_id)
    if member.role != "admin" and not user.is_platform_admin:
        raise HTTPException(403, "Samo administrator može menjati znanje brenda.")
    row = db.scalar(select(AiBrandKnowledge).where(AiBrandKnowledge.business_unit_id == unit_id).with_for_update())
    if (row is None and data.version is not None) or (row is not None and row.version != data.version):
        raise HTTPException(409, "Znanje brenda je izmenjeno. Osvežite pregled pre čuvanja.")
    if row is None:
        row = AiBrandKnowledge(business_unit_id=unit_id, content=data.content, updated_by_id=user.id)
        db.add(row)
    else:
        row.content = data.content
        row.updated_by_id = user.id
        row.version += 1
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Znanje brenda je u međuvremenu dodato. Osvežite pregled.")
    db.refresh(row)
    return output(row)
