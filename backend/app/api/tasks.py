from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from ..access import visible_company, visible_query
from ..db import get_db
from ..models import Company, Task, User
from ..schemas import TaskFields, TaskOutput, TaskPage, TaskStatusInput, TaskUpdate
from ..security import current_user, membership, require_origin

router = APIRouter(prefix="/api/units/{unit_id}/tasks", tags=["Zadaci"])


def visible_tasks(db: Session, user: User, unit_id: int):
    member = membership(db, user, unit_id)
    query = select(Task).where(Task.business_unit_id == unit_id)
    if member.role == "sales":
        companies = visible_query(db, user, unit_id).with_only_columns(Company.id)
        query = query.where(Task.owner_id == user.id,
                            or_(Task.company_id.is_(None), Task.company_id.in_(companies)))
    return query


def visible_task(db: Session, user: User, unit_id: int, task_id: int):
    record = db.scalar(visible_tasks(db, user, unit_id).where(Task.id == task_id).with_for_update())
    if record is None:
        raise HTTPException(404, "Zadatak nije pronađen.")
    return record


def task_output(db: Session, task: Task):
    owner = db.get(User, task.owner_id)
    company = db.get(Company, task.company_id) if task.company_id else None
    return TaskOutput.model_validate({**task.__dict__, "owner_name": owner.name if owner else "",
                                      "company_name": company.name if company else None})


@router.get("", response_model=TaskPage)
def list_tasks(unit_id: int, date_from: date, date_to: date,
               limit: int = Query(200, ge=1, le=200), offset: int = Query(0, ge=0),
               user: User = Depends(current_user), db: Session = Depends(get_db)):
    if date_from > date_to or (date_to - date_from).days > 366:
        raise HTTPException(422, "Izaberite period do godinu dana.")
    query = visible_tasks(db, user, unit_id).where(Task.due_date >= date_from, Task.due_date <= date_to)
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    records = db.scalars(query.order_by(Task.due_date, Task.due_time, Task.id).limit(limit).offset(offset)).all()
    return {"total": total, "items": [task_output(db, task) for task in records]}


@router.post("", response_model=TaskOutput, status_code=201, dependencies=[Depends(require_origin)])
def create_task(unit_id: int, data: TaskFields,
                user: User = Depends(current_user), db: Session = Depends(get_db)):
    membership(db, user, unit_id)
    if data.company_id:
        visible_company(db, user, unit_id, data.company_id)
    record = Task(**data.model_dump(), owner_id=user.id, business_unit_id=unit_id)
    db.add(record)
    db.commit()
    db.refresh(record)
    return task_output(db, record)


def apply_change(db: Session, task: Task, values: dict, version: int):
    if task.version != version:
        raise HTTPException(409, "Zadatak je u međuvremenu izmenjen. Osvežite kalendar.")
    for key, value in values.items():
        setattr(task, key, value)
    task.version += 1
    db.commit()
    db.refresh(task)
    return task_output(db, task)


@router.patch("/{task_id}", response_model=TaskOutput, dependencies=[Depends(require_origin)])
def update_task(unit_id: int, task_id: int, data: TaskUpdate,
                user: User = Depends(current_user), db: Session = Depends(get_db)):
    record = visible_task(db, user, unit_id, task_id)
    if data.company_id:
        visible_company(db, user, unit_id, data.company_id)
    return apply_change(db, record, data.model_dump(exclude={"version"}), data.version)


@router.patch("/{task_id}/status", response_model=TaskOutput, dependencies=[Depends(require_origin)])
def change_status(unit_id: int, task_id: int, data: TaskStatusInput,
                  user: User = Depends(current_user), db: Session = Depends(get_db)):
    record = visible_task(db, user, unit_id, task_id)
    return apply_change(db, record, {"status": data.status}, data.version)
