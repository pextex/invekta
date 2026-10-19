from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, aliased
from ..business_types import resolve_business_type
from ..access import visible_company, visible_query
from ..constants import CLOSED_STAGES, OPPORTUNITY_STAGES
from ..db import get_db
from ..models import Company, Contact, Opportunity, OpportunityStageChange, User
from ..schemas import (
    SalesReport,
    CompanyOutput,
    ContactInput,
    ContactOutput,
    OpportunityCreate,
    OpportunityOutput,
    OpportunityPage,
    OpportunityStageInput,
    OpportunityUpdate,
    StageChangeOutput,
    UnitSummary,
)
from ..security import current_user, membership, require_origin

router = APIRouter(prefix="/api/units/{unit_id}", tags=["CRM"])


def company_ids(db, user, unit_id):
    return visible_query(db, user, unit_id).with_only_columns(Company.id)


def opportunities_query(db, user, unit_id):
    return select(Opportunity).where(
        Opportunity.business_unit_id == unit_id,
        Opportunity.company_id.in_(company_ids(db, user, unit_id)),
    )


def visible_opportunity(db, user, unit_id, opportunity_id, lock=False):
    query = opportunities_query(db, user, unit_id).where(
        Opportunity.id == opportunity_id
    )
    if lock:
        query = query.with_for_update()
    record = db.scalar(query)
    if record is None:
        raise HTTPException(404, "Prodajna prilika nije pronađena.")
    return record


def opportunity_output(db, record):
    company = db.get(Company, record.company_id)
    owner = db.get(User, company.owner_id)
    return OpportunityOutput.model_validate(
        {**record.__dict__, "company_name": company.name, "owner_name": owner.name}
    )


@router.get("/companies/{company_id}", response_model=CompanyOutput)
def get_company(
    unit_id: int,
    company_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    return visible_company(db, user, unit_id, company_id)


@router.get("/companies/{company_id}/contacts", response_model=list[ContactOutput])
def list_contacts(
    unit_id: int,
    company_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    visible_company(db, user, unit_id, company_id)
    return db.scalars(
        select(Contact)
        .where(Contact.company_id == company_id, Contact.business_unit_id == unit_id)
        .order_by(Contact.name)
    ).all()


@router.post(
    "/companies/{company_id}/contacts",
    response_model=ContactOutput,
    status_code=201,
    dependencies=[Depends(require_origin)],
)
def create_contact(
    unit_id: int,
    company_id: int,
    data: ContactInput,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    visible_company(db, user, unit_id, company_id)
    record = Contact(
        **data.model_dump(),
        company_id=company_id,
        business_unit_id=unit_id,
        is_demo=False,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.patch(
    "/companies/{company_id}/contacts/{contact_id}",
    response_model=ContactOutput,
    dependencies=[Depends(require_origin)],
)
def update_contact(
    unit_id: int,
    company_id: int,
    contact_id: int,
    data: ContactInput,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    visible_company(db, user, unit_id, company_id)
    record = db.scalar(
        select(Contact).where(
            Contact.id == contact_id,
            Contact.company_id == company_id,
            Contact.business_unit_id == unit_id,
        )
    )
    if record is None:
        raise HTTPException(404, "Kontakt nije pronađen.")
    for key, value in data.model_dump().items():
        setattr(record, key, value)
    db.commit()
    db.refresh(record)
    return record


@router.get("/opportunities", response_model=OpportunityPage)
def list_opportunities(
    unit_id: int,
    company_id: int | None = Query(None, gt=0),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    query = opportunities_query(db, user, unit_id)
    if company_id is not None:
        visible_company(db, user, unit_id, company_id)
        query = query.where(Opportunity.company_id == company_id)
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    records = db.scalars(
        query.order_by(Opportunity.id.desc()).offset(offset).limit(limit)
    ).all()
    # Batch company/owner lookups; no one-query-per-card cost.
    companies = {
        c.id: c
        for c in db.scalars(
            select(Company).where(Company.id.in_([r.company_id for r in records]))
        )
    }
    owners = {
        u.id: u.name
        for u in db.scalars(
            select(User).where(User.id.in_([c.owner_id for c in companies.values()]))
        )
    }
    items = [
        OpportunityOutput.model_validate(
            {
                **r.__dict__,
                "company_name": companies[r.company_id].name,
                "owner_name": owners[companies[r.company_id].owner_id],
            }
        )
        for r in records
    ]
    return {"items": items, "total": total}


@router.post(
    "/opportunities",
    response_model=OpportunityOutput,
    status_code=201,
    dependencies=[Depends(require_origin)],
)
def create_opportunity(
    unit_id: int,
    data: OpportunityCreate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    visible_company(db, user, unit_id, data.company_id)
    values = data.model_dump()
    values["business_type"] = resolve_business_type(db, unit_id, data.business_type)
    record = Opportunity(**values, business_unit_id=unit_id, is_demo=False)
    if record.stage == "Dobijeno" and record.business_type is None:
        raise HTTPException(422, "Izaberite vrstu posla pre realizacije.")
    db.add(record)
    db.flush()
    db.add(
        OpportunityStageChange(
            opportunity_id=record.id,
            business_unit_id=unit_id,
            actor_id=user.id,
            from_stage=None,
            to_stage=record.stage,
            amount=record.amount,
            business_type=record.business_type,
            changes={key: {"before": None, "after": str(value) if value is not None else None}
                     for key, value in values.items() if key != "company_id"},
        )
    )
    db.commit()
    db.refresh(record)
    return opportunity_output(db, record)


def apply_opportunity_change(db, user, record, values, version):
    if record.version != version:
        raise HTTPException(
            409,
            "Priliku je u međuvremenu izmenio drugi korisnik. Osvežite prikaz i pokušajte ponovo.",
        )
    previous = record.stage
    if values.get("stage", record.stage) == "Dobijeno" and (previous != "Dobijeno" or "business_type" in values):
        kind = resolve_business_type(db, record.business_unit_id, values.get("business_type", record.business_type))
        if kind is None:
            raise HTTPException(422, "Izaberite vrstu posla pre realizacije.")
        values["business_type"] = kind
    changes = {key: {"before": str(getattr(record, key)) if getattr(record, key) is not None else None,
                     "after": str(value) if value is not None else None}
               for key, value in values.items() if getattr(record, key) != value}
    for key, value in values.items():
        setattr(record, key, value)
    record.version += 1
    if changes:
        db.add(
            OpportunityStageChange(
                opportunity_id=record.id,
                business_unit_id=record.business_unit_id,
                actor_id=user.id,
                from_stage=previous,
                to_stage=record.stage,
                amount=record.amount,
                business_type=record.business_type,
                changes=changes,
            )
        )
    db.commit()
    db.refresh(record)
    return opportunity_output(db, record)


@router.patch(
    "/opportunities/{opportunity_id}",
    response_model=OpportunityOutput,
    dependencies=[Depends(require_origin)],
)
def update_opportunity(
    unit_id: int,
    opportunity_id: int,
    data: OpportunityUpdate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    record = visible_opportunity(db, user, unit_id, opportunity_id, lock=True)
    values = data.model_dump(exclude={"version"})
    if "business_type" not in data.model_fields_set:
        values.pop("business_type", None)
    else:
        values["business_type"] = resolve_business_type(db, unit_id, data.business_type)
    return apply_opportunity_change(db, user, record, values, data.version)


@router.patch(
    "/opportunities/{opportunity_id}/stage",
    response_model=OpportunityOutput,
    dependencies=[Depends(require_origin)],
)
def change_stage(
    unit_id: int,
    opportunity_id: int,
    data: OpportunityStageInput,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    record = visible_opportunity(db, user, unit_id, opportunity_id, lock=True)
    return apply_opportunity_change(
        db, user, record, {"stage": data.stage}, data.version
    )


@router.get(
    "/opportunities/{opportunity_id}/stage-history",
    response_model=list[StageChangeOutput],
)
def stage_history(
    unit_id: int,
    opportunity_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    member = membership(db, user, unit_id)
    if not user.is_platform_admin and member.role not in ("manager", "admin"):
        raise HTTPException(403, "Hronologija promena je dostupna samo menadžerima i administratorima.")
    visible_opportunity(db, user, unit_id, opportunity_id)
    result = db.execute(
        select(OpportunityStageChange, User.name)
        .join(User, User.id == OpportunityStageChange.actor_id)
        .where(
            OpportunityStageChange.opportunity_id == opportunity_id,
            OpportunityStageChange.business_unit_id == unit_id,
        )
        .order_by(OpportunityStageChange.id)
    ).all()
    return [
        {
            "id": row.id,
            "from_stage": row.from_stage,
            "to_stage": row.to_stage,
            "actor_name": actor,
            "changed_at": row.changed_at,
        }
        for row, actor in result
    ]


@router.get("/summary", response_model=UnitSummary)
def summary(
    unit_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)
):
    ids = company_ids(db, user, unit_id)
    query = opportunities_query(db, user, unit_id)
    rows = db.execute(
        select(Opportunity.stage, func.count(), func.sum(Opportunity.amount))
        .where(Opportunity.id.in_(query.with_only_columns(Opportunity.id)))
        .group_by(Opportunity.stage)
    ).all()
    counts = {stage: 0 for stage in OPPORTUNITY_STAGES}
    values = {stage: Decimal("0") for stage in OPPORTUNITY_STAGES}
    for stage, count, value in rows:
        counts[stage] = count
        values[stage] = value
    return {
        "company_count": db.scalar(
            select(func.count()).select_from(Company).where(Company.id.in_(ids))
        ),
        "contact_count": db.scalar(
            select(func.count())
            .select_from(Contact)
            .where(Contact.company_id.in_(ids), Contact.business_unit_id == unit_id)
        ),
        "opportunity_count": sum(counts.values()),
        "open_count": sum(
            counts[s] for s in OPPORTUNITY_STAGES if s not in CLOSED_STAGES
        ),
        "open_value": sum(
            (values[s] for s in OPPORTUNITY_STAGES if s not in CLOSED_STAGES),
            Decimal("0"),
        ),
        "won_count": counts["Dobijeno"],
        "won_value": values["Dobijeno"],
        "stages": counts,
    }


@router.get("/reports", response_model=SalesReport)
def sales_report(
    unit_id: int,
    date_from: date,
    date_to: date,
    include_demo: bool = False,
    include_history: bool = False,
    owner_id: int | None = Query(None, gt=0),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    if date_from > date_to or date_to == date.max:
        raise HTTPException(422, "Proverite početak i kraj perioda.")
    member = membership(db, user, unit_id)
    if include_history and not user.is_platform_admin and member.role not in ("manager", "admin"):
        raise HTTPException(403, "Hronologija promena je dostupna samo menadžerima i administratorima.")
    if member.role == "sales" and owner_id is not None and owner_id != user.id:
        raise HTTPException(403, "Možete pregledati samo svoj izveštaj.")
    company_scope = visible_query(db, user, unit_id)
    people = db.execute(select(User.id, User.name).where(User.id.in_(
        company_scope.with_only_columns(Company.owner_id))).order_by(User.name, User.id)).all()
    if owner_id is not None and owner_id not in [person.id for person in people]:
        raise HTTPException(404, "Komercijalista nije pronađen u ovoj firmi.")
    zone = ZoneInfo("Europe/Belgrade")
    visible = opportunities_query(db, user, unit_id)
    if owner_id is not None:
        visible = visible.where(Opportunity.company_id.in_(company_scope.where(Company.owner_id == owner_id).with_only_columns(Company.id)))
    if not include_demo:
        visible = visible.where(Opportunity.is_demo.is_(False))
    history = OpportunityStageChange
    criteria = (
        history.business_unit_id == unit_id,
        or_(history.from_stage.is_(None), history.from_stage != history.to_stage),
        history.opportunity_id.in_(visible.with_only_columns(Opportunity.id)),
        history.changed_at >= datetime.combine(date_from, time.min, zone),
        history.changed_at < datetime.combine(date_to + timedelta(days=1), time.min, zone),
    )
    grouped = db.execute(
        select(history.from_stage, history.to_stage, func.count())
        .where(*criteria).group_by(history.from_stage, history.to_stage)
    ).all()
    total = sum(count for _, _, count in grouped)
    owner = aliased(User)
    by_owner = db.execute(select(Company.owner_id, owner.name, history.from_stage, history.to_stage, func.count())
        .select_from(history).join(Opportunity, Opportunity.id == history.opportunity_id)
        .join(Company, Company.id == Opportunity.company_id).join(owner, owner.id == Company.owner_id)
        .where(*criteria).group_by(Company.owner_id, owner.name, history.from_stage, history.to_stage)
        .order_by(owner.name, Company.owner_id)).all()
    owners = {}
    for person_id, name, before, after, count in by_owner:
        person = owners.setdefault(person_id, {"user_id": person_id, "user_name": name, "total": 0,
            "created_count": 0, "stage_change_count": 0, "edit_count": 0, "realized_count": 0, "unrealized_count": 0})
        person["total"] += count
        person["created_count" if before is None else "edit_count" if before == after else "stage_change_count"] += count
        if before != after and after == "Dobijeno": person["realized_count"] += count
        if before != after and after == "Izgubljeno": person["unrealized_count"] += count
    rows = db.execute(
        select(history, Opportunity.title, Company.name, User.name, Company.owner_id, owner.name)
        .join(Opportunity, Opportunity.id == history.opportunity_id)
        .join(Company, Company.id == Opportunity.company_id)
        .join(User, User.id == history.actor_id)
        .join(owner, owner.id == Company.owner_id)
        .where(*criteria).order_by(history.changed_at.desc(), history.id.desc())
        .limit(limit).offset(offset)
    ).all() if include_history else []
    return {
        "people": [{"id": person.id, "name": person.name} for person in people],
        "owners": list(owners.values()),
        "total": total,
        "opportunity_count": db.scalar(select(func.count(func.distinct(history.opportunity_id))).where(*criteria)),
        "created_count": sum(n for before, _, n in grouped if before is None),
        "stage_change_count": sum(n for before, after, n in grouped if before is not None and before != after),
        "edit_count": sum(n for before, after, n in grouped if before == after),
        "realized_count": sum(n for before, after, n in grouped if after == "Dobijeno" and before != after),
        "unrealized_count": sum(n for before, after, n in grouped if after == "Izgubljeno" and before != after),
        "stage_counts": {stage: sum(n for before, after, n in grouped if after == stage and before != after)
                         for stage in OPPORTUNITY_STAGES},
        "items": [{"id": row.id, "changed_at": row.changed_at, "company_name": company,
                   "opportunity_id": row.opportunity_id, "title": title, "amount": row.amount,
                   "from_stage": row.from_stage, "to_stage": row.to_stage,
                   "actor_name": actor, "changes": row.changes, "owner_id": person_id, "owner_name": person_name}
                  for row, title, company, actor, person_id, person_name in rows],
    }
