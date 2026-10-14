from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from ..db import get_db
from ..security import current_user, require_origin, membership
from ..access import visible_company
from ..models import User, Membership
from ..metrics import MetricFilters
from ..work_models import Task, Activity, Reminder
from ..work_schemas import (
    TaskInput,
    TaskUpdate,
    TaskOutput,
    ActivityInput,
    ActivityUpdate,
    ActivityOutput,
)
from .. import work
from ..work_metrics import summary

router = APIRouter(prefix="/api/units/{unit_id}", tags=["Tasks and activities"])


@router.get("/tasks")
def tasks(
    unit_id: int,
    company_id: int | None = Query(None, gt=0),
    assignee_id: int | None = Query(None, gt=0),
    status: str | None = None,
    include_archived: bool = False,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    if status and status not in ("open", "doing", "done", "cancelled"):
        raise HTTPException(422, "Nepoznat status.")
    return work.page(
        db,
        user,
        unit_id,
        Task,
        company_id,
        assignee_id,
        status,
        offset,
        limit,
        include_archived,
    )


@router.post(
    "/tasks",
    response_model=TaskOutput,
    status_code=201,
    dependencies=[Depends(require_origin)],
)
def create_task(
    unit_id: int,
    data: TaskInput,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    return work.save(db, user, unit_id, Task, data)


@router.patch(
    "/tasks/{id}", response_model=TaskOutput, dependencies=[Depends(require_origin)]
)
def update_task(
    unit_id: int,
    id: int,
    data: TaskUpdate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    return work.save(
        db,
        user,
        unit_id,
        Task,
        data,
        work.record(db, user, unit_id, Task, id, lock=True),
    )


@router.delete(
    "/tasks/{id}", response_model=TaskOutput, dependencies=[Depends(require_origin)]
)
def archive_task(
    unit_id: int,
    id: int,
    version: int = Query(..., ge=1),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    return work.archive(
        db, user, work.record(db, user, unit_id, Task, id, lock=True), version
    )


@router.get("/tasks/{id}/history")
def task_history(
    unit_id: int,
    id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    return work.history(db, user, unit_id, Task, id)


@router.get("/activities")
def activities(
    unit_id: int,
    company_id: int | None = Query(None, gt=0),
    assignee_id: int | None = Query(None, gt=0),
    status: str | None = None,
    include_archived: bool = False,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    if status and status not in ("planned", "done", "cancelled"):
        raise HTTPException(422, "Nepoznat status.")
    return work.page(
        db,
        user,
        unit_id,
        Activity,
        company_id,
        assignee_id,
        status,
        offset,
        limit,
        include_archived,
    )


@router.post(
    "/activities",
    response_model=ActivityOutput,
    status_code=201,
    dependencies=[Depends(require_origin)],
)
def create_activity(
    unit_id: int,
    data: ActivityInput,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    return work.save(db, user, unit_id, Activity, data)


@router.patch(
    "/activities/{id}",
    response_model=ActivityOutput,
    dependencies=[Depends(require_origin)],
)
def update_activity(
    unit_id: int,
    id: int,
    data: ActivityUpdate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    return work.save(
        db,
        user,
        unit_id,
        Activity,
        data,
        work.record(db, user, unit_id, Activity, id, lock=True),
    )


@router.delete(
    "/activities/{id}",
    response_model=ActivityOutput,
    dependencies=[Depends(require_origin)],
)
def archive_activity(
    unit_id: int,
    id: int,
    version: int = Query(..., ge=1),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    return work.archive(
        db, user, work.record(db, user, unit_id, Activity, id, lock=True), version
    )


@router.get("/activities/{id}/history")
def activity_history(
    unit_id: int,
    id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    return work.history(db, user, unit_id, Activity, id)


@router.get("/work/assignees")
def assignees(
    unit_id: int,
    company_id: int = Query(..., gt=0),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    company = visible_company(db, user, unit_id, company_id)
    member = membership(db, user, unit_id)
    query = (
        select(User.id, User.name, Membership.role)
        .join(Membership, Membership.user_id == User.id)
        .where(
            Membership.business_unit_id == unit_id,
            Membership.enabled.is_(True),
            User.active.is_(True),
        )
    )
    if member.role == "sales":
        query = query.where(User.id == user.id)
    else:
        query = query.where(
            (Membership.role != "sales") | (User.id == company.owner_id)
        )
    return [
        dict(id=id, name=name, role=role)
        for id, name, role in db.execute(query.order_by(User.name, User.id))
    ]


@router.get("/work/summary")
def work_summary(
    unit_id: int,
    filters: MetricFilters = Depends(),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    return summary(db, user, unit_id, filters)


@router.get("/reminders")
def reminders(
    unit_id: int,
    company_id: int | None = Query(None, gt=0),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    query = work.reminder_scope(db, user, unit_id, company_id).where(
        Reminder.status != "cancelled"
    )
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    rows = db.scalars(
        query.order_by(Reminder.fire_at.desc(), Reminder.id.desc())
        .offset(offset)
        .limit(limit)
    )
    return {"items": [work.reminder_output(db, row) for row in rows], "total": total}


@router.patch("/reminders/{id}/read", dependencies=[Depends(require_origin)])
def read_reminder(
    unit_id: int,
    id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    from datetime import datetime, timezone

    row = db.scalar(
        work.reminder_scope(db, user, unit_id)
        .where(Reminder.id == id, Reminder.status == "delivered")
        .with_for_update()
    )
    if row is None:
        raise HTTPException(404, "Podsetnik nije pronađen.")
    row.read_at = row.read_at or datetime.now(timezone.utc)
    db.commit()
    db.refresh(row)
    return work.reminder_output(db, row)


@router.post(
    "/tasks/{id}/restore",
    response_model=TaskOutput,
    dependencies=[Depends(require_origin)],
)
def restore_task(
    unit_id: int,
    id: int,
    version: int = Query(..., ge=1),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    return work.restore(
        db,
        user,
        work.record(db, user, unit_id, Task, id, lock=True, include_archived=True),
        version,
    )


@router.post(
    "/activities/{id}/restore",
    response_model=ActivityOutput,
    dependencies=[Depends(require_origin)],
)
def restore_activity(
    unit_id: int,
    id: int,
    version: int = Query(..., ge=1),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    return work.restore(
        db,
        user,
        work.record(db, user, unit_id, Activity, id, lock=True, include_archived=True),
        version,
    )
