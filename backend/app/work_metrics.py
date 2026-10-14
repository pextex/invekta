from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo
from sqlalchemy import func, select, case
from .models import Company, User
from .metrics import scoped_companies
from .work_models import Task, Activity, Reminder
from .work import scope, reminder_scope, output


def summary(db, user, unit, filters):
    company_ids = scoped_companies(db, user, unit, filters).with_only_columns(
        Company.id
    )
    tasks = filters.period(
        scope(db, user, unit, Task).where(Task.company_id.in_(company_ids)), Task.due_at
    )
    activity_date = case(
        (Activity.status == "done", Activity.occurred_at), else_=Activity.scheduled_at
    )
    activities = filters.period(
        scope(db, user, unit, Activity).where(Activity.company_id.in_(company_ids)),
        activity_date,
    )
    task_ids = tasks.with_only_columns(Task.id)
    activity_ids = activities.with_only_columns(Activity.id)
    now = datetime.now(timezone.utc)
    day = now.astimezone(ZoneInfo("Europe/Belgrade")).date()
    start = datetime.combine(day, time.min, ZoneInfo("Europe/Belgrade"))
    end = datetime.combine(day, time.max, ZoneInfo("Europe/Belgrade"))
    t_scope = Task.id.in_(task_ids)
    a_scope = Activity.id.in_(activity_ids)
    active = Task.status.in_(["open", "doing"])

    def count(model, where):
        return db.scalar(select(func.count()).select_from(model).where(where))

    task_counts = dict.fromkeys(("open", "doing", "done", "cancelled"), 0)
    task_counts.update(
        dict(
            db.execute(
                select(Task.status, func.count()).where(t_scope).group_by(Task.status)
            ).all()
        )
    )
    activity_counts = dict.fromkeys(("planned", "done", "cancelled"), 0)
    activity_counts.update(
        dict(
            db.execute(
                select(Activity.status, func.count())
                .where(a_scope)
                .group_by(Activity.status)
            ).all()
        )
    )
    task_stats = db.execute(
        select(
            Task.assignee_id,
            User.name,
            func.count().filter(active),
            func.count().filter(Task.status == "done"),
            func.count().filter(active & (Task.due_at < now)),
        )
        .join(User, User.id == Task.assignee_id)
        .where(t_scope)
        .group_by(Task.assignee_id, User.name)
    ).all()
    groups = {
        id: dict(
            assignee_id=id,
            name=name,
            open_tasks=opened,
            done_tasks=done,
            overdue_tasks=overdue,
            planned_activities=0,
            completed_calls=0,
            completed_meetings=0,
        )
        for id, name, opened, done, overdue in task_stats
    }
    activity_stats = db.execute(
        select(
            Activity.assignee_id,
            User.name,
            func.count().filter(Activity.status == "planned"),
            func.count().filter(
                (Activity.status == "done") & (Activity.kind == "call")
            ),
            func.count().filter(
                (Activity.status == "done") & (Activity.kind == "meeting")
            ),
        )
        .join(User, User.id == Activity.assignee_id)
        .where(a_scope)
        .group_by(Activity.assignee_id, User.name)
    ).all()
    for id, name, planned, calls, meetings in activity_stats:
        entry = groups.setdefault(
            id,
            dict(
                assignee_id=id, name=name, open_tasks=0, done_tasks=0, overdue_tasks=0
            ),
        )
        entry.update(
            planned_activities=planned,
            completed_calls=calls,
            completed_meetings=meetings,
        )
    due = [
        output(db, row)
        for row in db.scalars(
            tasks.where(active, Task.due_at <= end)
            .order_by(Task.due_at, Task.id)
            .limit(5)
        )
    ]
    meetings = [
        output(db, row)
        for row in db.scalars(
            activities.where(Activity.status == "planned", Activity.scheduled_at <= end)
            .order_by(Activity.scheduled_at, Activity.id)
            .limit(5)
        )
    ]
    return dict(
        tasks=task_counts,
        activities=activity_counts,
        overdue_tasks=count(Task, t_scope & active & (Task.due_at < now)),
        due_today=count(
            Task, t_scope & active & (Task.due_at >= start) & (Task.due_at <= end)
        ),
        activities_today=count(
            Activity,
            a_scope
            & (Activity.status == "planned")
            & (Activity.scheduled_at >= start)
            & (Activity.scheduled_at <= end),
        ),
        overdue_activities=count(
            Activity,
            a_scope & (Activity.status == "planned") & (Activity.scheduled_at < now),
        ),
        completed_calls=count(
            Activity, a_scope & (Activity.status == "done") & (Activity.kind == "call")
        ),
        completed_meetings=count(
            Activity,
            a_scope & (Activity.status == "done") & (Activity.kind == "meeting"),
        ),
        unread_reminders=db.scalar(
            select(func.count()).select_from(
                reminder_scope(db, user, unit)
                .where(Reminder.status == "delivered", Reminder.read_at.is_(None))
                .subquery()
            )
        ),
        due_tasks=due,
        scheduled_activities=meetings,
        assignee_results=sorted(
            groups.values(), key=lambda r: (r["name"], r["assignee_id"])
        ),
    )
