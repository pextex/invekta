from urllib.parse import quote
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import SalesDocument, User
from ..sales_document_files import file_metadata, read_document
from ..schemas import SalesDocumentOutput, SalesDocumentPage
from ..security import current_user, membership, require_origin

router = APIRouter(prefix="/api/units/{unit_id}/sales-documents", tags=["Ponude i fajlovi"])


def document_output(db: Session, record: SalesDocument):
    uploader = db.get(User, record.uploaded_by_id)
    return SalesDocumentOutput.model_validate({
        "id": record.id, "business_unit_id": record.business_unit_id,
        "title": record.title, "filename": record.filename, "content_type": record.content_type,
        "size_bytes": record.size_bytes, "created_at": record.created_at,
        "uploaded_by_name": uploader.name if uploader else "Administrator",
    })


@router.get("", response_model=SalesDocumentPage)
def list_documents(unit_id: int, search: str = Query("", max_length=200),
                   limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0),
                   user: User = Depends(current_user), db: Session = Depends(get_db)):
    membership(db, user, unit_id)
    query = select(SalesDocument).where(SalesDocument.business_unit_id == unit_id)
    if search.strip():
        query = query.where(or_(func.lower(SalesDocument.title).contains(search.strip().lower(), autoescape=True),
                                func.lower(SalesDocument.filename).contains(search.strip().lower(), autoescape=True)))
    total = db.scalar(select(func.count()).select_from(query.with_only_columns(SalesDocument.id).subquery()))
    rows = db.scalars(query.order_by(SalesDocument.created_at.desc(), SalesDocument.id.desc()).limit(limit).offset(offset)).all()
    return {"items": [document_output(db, record) for record in rows], "total": total}


@router.post("", response_model=SalesDocumentOutput, status_code=201, dependencies=[Depends(require_origin)])
async def upload_document(request: Request, unit_id: int,
                          filename: str = Query(min_length=1, max_length=255),
                          title: str = Query("", max_length=200),
                          user: User = Depends(current_user), db: Session = Depends(get_db)):
    member = membership(db, user, unit_id)
    if member.role != "admin" and not user.is_platform_admin:
        raise HTTPException(403, "Samo administrator može da dodaje fajlove.")
    name, (content_type, signatures) = file_metadata(filename)
    data = await read_document(request)
    if not any(data.startswith(signature) for signature in signatures):
        raise HTTPException(422, "Sadržaj fajla ne odgovara izabranom tipu dokumenta.")
    record = SalesDocument(business_unit_id=unit_id, uploaded_by_id=user.id, title=title.strip() or name[:200],
                           filename=name, content_type=content_type, size_bytes=len(data), data=data)
    db.add(record)
    db.commit()
    db.refresh(record)
    return document_output(db, record)


@router.get("/{document_id}/download")
def download_document(unit_id: int, document_id: int,
                      user: User = Depends(current_user), db: Session = Depends(get_db)):
    membership(db, user, unit_id)
    record = db.scalar(select(SalesDocument).where(SalesDocument.id == document_id,
                                                  SalesDocument.business_unit_id == unit_id))
    if record is None:
        raise HTTPException(404, "Fajl nije pronađen.")
    extension = record.filename.rsplit(".", 1)[-1].lower()
    return Response(record.data, media_type="application/octet-stream", headers={
        "Content-Disposition": f"attachment; filename=\"document.{extension}\"; filename*=UTF-8''{quote(record.filename, safe='')}",
        "X-Content-Type-Options": "nosniff",
        "Cache-Control": "no-store",
    })
