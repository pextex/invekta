"""Shared work authorization, persistence, reminders and event history."""

from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy import select, func, or_, case
from .access import visible_query, visible_company
from .security import membership
from .models import Company, Membership, Opportunity, User
from .work_models import Task, Activity, Reminder, WorkEvent
from .work_schemas import TaskOutput, ActivityOutput


def scope(db, user, unit, model, include_archived=False):
    ids = visible_query(db, user, unit).with_only_columns(Company.id)
    query = select(model).where(
        model.business_unit_id == unit, model.company_id.in_(ids)
    )
    return query if include_archived else query.where(model.archived_at.is_(None))


def record(db, user, unit, model, id, lock=False, include_archived=False):
    query = scope(db, user, unit, model, include_archived).where(model.id == id)
    if lock:
        query = query.with_for_update()
    row = db.scalar(query)
    if row is None:
        raise HTTPException(404, "Zapis nije pronađen.")
    return row


def context(db, user, unit, data):
    company = visible_company(db, user, unit, data.company_id)
    role = membership(db, user, unit).role
    if role == "sales" and data.assignee_id != user.id:
        raise HTTPException(422, "Komercijalista može dodeliti obavezu samo sebi.")
    member = db.get(Membership, (data.assignee_id, unit))
    assigned = db.get(User, data.assignee_id)
    if (
        not member
        or not member.enabled
        or not assigned
        or not assigned.active
        or (member.role == "sales" and company.owner_id != assigned.id)
    ):
        raise HTTPException(422, "Odgovorna osoba nema pristup kompaniji.")
    if (
        data.opportunity_id
        and db.scalar(
            select(Opportunity.id).where(
                Opportunity.id == data.opportunity_id,
                Opportunity.company_id == company.id,
                Opportunity.business_unit_id == unit,
            )
        )
        is None
    ):
        raise HTTPException(422, "Prilika ne pripada izabranoj kompaniji.")


def output(db, row, related=None):
    if related is None:
        company_name = db.get(Company, row.company_id).name
        assignee_name = db.get(User, row.assignee_id).name
        opportunity = (
            db.get(Opportunity, row.opportunity_id) if row.opportunity_id else None
        )
        opportunity_title = opportunity.title if opportunity else None
    else:
        company_name = related["companies"][row.company_id]
        assignee_name = related["assignees"][row.assignee_id]
        opportunity_title = related["opportunities"].get(row.opportunity_id)
    schema = TaskOutput if isinstance(row, Task) else ActivityOutput
    return schema.model_validate(
        {
            **row.__dict__,
            "company_name": company_name,
            "assignee_name": assignee_name,
            "opportunity_title": opportunity_title,
        }
    )


def serial(value):
    return value.isoformat() if isinstance(value, datetime) else value


def event(db, user, row, action, changes):
    db.add(
        WorkEvent(
            business_unit_id=row.business_unit_id,
            actor_id=user.id,
            action=action,
            task_id=row.id if isinstance(row, Task) else None,
            activity_id=row.id if isinstance(row, Activity) else None,
            changes=changes,
        )
    )


def reminders(db, row):
    column = Reminder.task_id if isinstance(row, Task) else Reminder.activity_id
    return select(Reminder).where(
        column == row.id, Reminder.business_unit_id == row.business_unit_id
    )


def sync_reminder(db, row):
    active = (
        row.status in ("open", "doing")
        if isinstance(row, Task)
        else row.status == "planned"
    ) and row.archived_at is None
    latest = db.scalar(
        reminders(db, row).order_by(Reminder.id.desc()).limit(1).with_for_update()
    )
    same = (
        latest
        and latest.fire_at == row.remind_at
        and latest.recipient_id == row.assignee_id
    )
    if latest and latest.status == "pending" and (not active or not same):
        latest.status = "cancelled"
        db.flush()
    if (
        active
        and row.remind_at
        and (not latest or not same or latest.status == "cancelled")
    ):
        db.add(
            Reminder(
                business_unit_id=row.business_unit_id,
                task_id=row.id if isinstance(row, Task) else None,
                activity_id=row.id if isinstance(row, Activity) else None,
                recipient_id=row.assignee_id,
                fire_at=row.remind_at,
            )
        )


def save(db, user, unit, model, data, row=None):
    context(db, user, unit, data)
    fields = data.model_dump(exclude={"version"})
    now = datetime.now(timezone.utc)
    if row:
        if row.version != data.version:
            raise HTTPException(
                409,
                "Zapis je u međuvremenu izmenjen. Osvežite prikaz i ponovo otvorite formular.",
            )
        if row.company_id != data.company_id:
            raise HTTPException(
                422, "Kompanija postojećeg zapisa ne može se promeniti."
            )
    if model is Task:
        fields["completed_at"] = (
            (row.completed_at if row and row.status == "done" else now)
            if data.status == "done"
            else None
        )
    else:
        fields["occurred_at"] = (
            (
                fields["occurred_at"]
                or (row.occurred_at if row and row.status == "done" else now)
            )
            if data.status == "done"
            else None
        )
    changes = {
        key: {"from": serial(getattr(row, key)) if row else None, "to": serial(value)}
        for key, value in fields.items()
        if row is None or getattr(row, key) != value
    }
    if row:
        for key, value in fields.items():
            setattr(row, key, value)
        row.version += 1
    else:
        row = model(**fields, business_unit_id=unit, creator_id=user.id)
        db.add(row)
    db.flush()
    sync_reminder(db, row)
    event(
        db,
        user,
        row,
        "updated"
        if data.model_fields_set and "version" in data.model_fields_set
        else "created",
        changes,
    )
    db.commit()
    db.refresh(row)
    return output(db, row)


def archive(db, user, row, version):
    if row.version != version:
        raise HTTPException(409, "Zapis je u međuvremenu izmenjen.")
    timestamp = datetime.now(timezone.utc)
    completion = "completed_at" if isinstance(row, Task) else "occurred_at"
    changes = {
        "status": {"from": row.status, "to": "cancelled"},
        "archived_at": {"from": serial(row.archived_at), "to": serial(timestamp)},
        completion: {"from": serial(getattr(row, completion)), "to": None},
    }
    row.status = "cancelled"
    row.archived_at = timestamp
    row.version += 1
    setattr(row, completion, None)
    sync_reminder(db, row)
    event(db, user, row, "archived", changes)
    db.commit()
    db.refresh(row)
    return output(db, row)


def display_changes(db, changes):
    references = {
        "company_id": Company,
        "assignee_id": User,
        "opportunity_id": Opportunity,
    }

    def label(key, value):
        if value is None or key not in references:
            return value
        record = db.get(references[key], value)
        if record is None:
            return "Nedostupan zapis"
        return record.title if key == "opportunity_id" else record.name

    return {
        key: {side: label(key, value) for side, value in change.items()}
        for key, change in changes.items()
    }


def history(db, user, unit, model, id):
    record(db, user, unit, model, id, include_archived=True)
    column = WorkEvent.task_id if model is Task else WorkEvent.activity_id
    return [
        dict(
            id=e.id,
            action=e.action,
            actor_name=name,
            changed_at=e.changed_at,
            changes=e.changes,
            display_changes=display_changes(db, e.changes),
        )
        for e, name in db.execute(
            select(WorkEvent, User.name)
            .join(User, User.id == WorkEvent.actor_id)
            .where(column == id, WorkEvent.business_unit_id == unit)
            .order_by(WorkEvent.id)
        )
    ]


def date_column(model):
    return (
        model.due_at
        if model is Task
        else case(
            (Activity.status == "done", Activity.occurred_at),
            else_=Activity.scheduled_at,
        )
    )


def page(
    db,
    user,
    unit,
    model,
    company_id,
    assignee_id,
    status,
    offset,
    limit,
    include_archived=False,
):
    query = scope(db, user, unit, model, include_archived)
    if company_id:
        visible_company(db, user, unit, company_id)
        query = query.where(model.company_id == company_id)
    if assignee_id:
        query = query.where(model.assignee_id == assignee_id)
    if status:
        query = query.where(model.status == status)
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    date = date_column(model)
    rows = db.scalars(query.order_by(date, model.id).offset(offset).limit(limit)).all()
    related = {
        "companies": dict(
            db.execute(
                select(Company.id, Company.name).where(
                    Company.id.in_({row.company_id for row in rows})
                )
            ).all()
        ),
        "assignees": dict(
            db.execute(
                select(User.id, User.name).where(
                    User.id.in_({row.assignee_id for row in rows})
                )
            ).all()
        ),
        "opportunities": dict(
            db.execute(
                select(Opportunity.id, Opportunity.title).where(
                    Opportunity.id.in_(
                        {row.opportunity_id for row in rows if row.opportunity_id}
                    )
                )
            ).all()
        ),
    }
    return {"items": [output(db, row, related) for row in rows], "total": total}


def reminder_scope(db, user, unit, company_id=None):
    tasks = scope(db, user, unit, Task, True)
    activities = scope(db, user, unit, Activity, True)
    if company_id is not None:
        visible_company(db, user, unit, company_id)
        tasks = tasks.where(Task.company_id == company_id)
        activities = activities.where(Activity.company_id == company_id)
    return select(Reminder).where(
        Reminder.business_unit_id == unit,
        Reminder.recipient_id == user.id,
        or_(
            Reminder.task_id.in_(tasks.with_only_columns(Task.id)),
            Reminder.activity_id.in_(activities.with_only_columns(Activity.id)),
        ),
    )


def reminder_output(db, row):
    parent = (
        db.get(Task, row.task_id) if row.task_id else db.get(Activity, row.activity_id)
    )
    return dict(
        id=row.id,
        task_id=row.task_id,
        activity_id=row.activity_id,
        company_id=parent.company_id,
        title=parent.title,
        company_name=db.get(Company, parent.company_id).name,
        status=row.status,
        fire_at=row.fire_at,
        delivered_at=row.delivered_at,
        read_at=row.read_at,
    )


def restore(db, user, row, version):
    if row.version != version:
        raise HTTPException(409, "Zapis je u međuvremenu izmenjen.")
    if row.archived_at is not None:
        previous = row.archived_at
        row.archived_at = None
        row.version += 1
        event(
            db,
            user,
            row,
            "restored",
            {"archived_at": {"from": serial(previous), "to": None}},
        )
        db.commit()
        db.refresh(row)
    return output(db, row)
