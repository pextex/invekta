"""Idempotent in-app reminder dispatcher; no network mail provider."""

import argparse
import logging
import math
import signal
from threading import Event
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from .models import Company, Membership, User
from .work_models import Task, Activity, Reminder


def deliver_due(db, now=None):
    now = now or datetime.now(timezone.utc)
    delivered = 0
    for model, column in ((Task, Reminder.task_id), (Activity, Reminder.activity_id)):
        rows = db.scalars(
            select(model)
            .join(Reminder, column == model.id)
            .where(Reminder.status == "pending", Reminder.fire_at <= now)
            .order_by(Reminder.fire_at, model.id)
            .limit(100)
            .with_for_update(of=model, skip_locked=True)
        ).all()
        for parent in rows:
            reminder = db.scalar(
                select(Reminder)
                .where(column == parent.id, Reminder.status == "pending")
                .with_for_update()
            )
            if reminder is None:
                continue
            member = db.get(
                Membership, (reminder.recipient_id, parent.business_unit_id)
            )
            user = db.get(User, reminder.recipient_id)
            company = db.get(Company, parent.company_id)
            active = (
                parent.status in ("open", "doing")
                if model is Task
                else parent.status == "planned"
            )
            allowed = (
                member
                and member.enabled
                and user
                and user.active
                and (member.role != "sales" or company.owner_id == user.id)
            )
            if (
                not active
                or parent.archived_at
                or not allowed
                or parent.assignee_id != reminder.recipient_id
            ):
                reminder.status = "cancelled"
            else:
                reminder.status = "delivered"
                reminder.delivered_at = now
                delivered += 1
    return delivered


def serve(session_factory, *, stop=None, interval=20, once=False):
    stop = stop or Event()
    while not stop.is_set():
        try:
            with session_factory() as db:
                deliver_due(db)
                db.commit()
        except SQLAlchemyError:
            logging.getLogger(__name__).warning(
                "Reminder database unavailable; transaction rolled back, retry scheduled."
            )
            if once:
                return False
        else:
            if once:
                return True
        stop.wait(interval)
    return True


def main():
    from .db import SessionLocal

    parser = argparse.ArgumentParser(description="Deliver due in-app reminders.")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--interval", type=float, default=20)
    args = parser.parse_args()
    if not math.isfinite(args.interval) or args.interval < 1:
        parser.error("interval must be finite and >= 1 second")
    stop = Event()
    for name in (signal.SIGTERM, signal.SIGINT):
        signal.signal(name, lambda *_: stop.set())
    if not serve(SessionLocal, stop=stop, interval=args.interval, once=args.once):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
