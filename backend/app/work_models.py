"""Tenant-bound work records. Imported by models for Alembic metadata."""

from datetime import datetime
from sqlalchemy import (
    DateTime,
    Integer,
    String,
    Text,
    ForeignKeyConstraint,
    CheckConstraint,
    UniqueConstraint,
    Index,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base


def constraints(name):
    return (
        ForeignKeyConstraint(["business_unit_id"], ["business_units.id"]),
        ForeignKeyConstraint(
            ["company_id", "business_unit_id"],
            ["companies.id", "companies.business_unit_id"],
        ),
        ForeignKeyConstraint(
            ["opportunity_id", "company_id", "business_unit_id"],
            [
                "opportunities.id",
                "opportunities.company_id",
                "opportunities.business_unit_id",
            ],
        ),
        ForeignKeyConstraint(
            ["assignee_id", "business_unit_id"],
            ["memberships.user_id", "memberships.business_unit_id"],
        ),
        ForeignKeyConstraint(
            ["creator_id", "business_unit_id"],
            ["memberships.user_id", "memberships.business_unit_id"],
        ),
        UniqueConstraint("id", "business_unit_id", name=f"unique_{name}_id_unit"),
        CheckConstraint("version >= 1", name=f"positive_{name}_version"),
        Index(f"ix_{name}_unit_assignee", "business_unit_id", "assignee_id"),
        Index(f"ix_{name}_company", "company_id"),
    )


class WorkFields:
    id: Mapped[int] = mapped_column(primary_key=True)
    business_unit_id: Mapped[int] = mapped_column(Integer)
    company_id: Mapped[int] = mapped_column(Integer)
    opportunity_id: Mapped[int | None] = mapped_column(Integer)
    assignee_id: Mapped[int] = mapped_column(Integer)
    creator_id: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(200))
    notes: Mapped[str | None] = mapped_column(Text)
    remind_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Task(WorkFields, Base):
    __tablename__ = "tasks"
    __table_args__ = (
        *constraints("task"),
        CheckConstraint(
            "status IN ('open','doing','done','cancelled')", name="valid_task_status"
        ),
        CheckConstraint(
            "priority IN ('low','normal','high')", name="valid_task_priority"
        ),
        CheckConstraint(
            "(status='done') = (completed_at IS NOT NULL)",
            name="task_completion_consistent",
        ),
        Index("ix_task_due", "business_unit_id", "status", "due_at"),
    )
    status: Mapped[str] = mapped_column(
        String(20), default="open", server_default="open"
    )
    priority: Mapped[str] = mapped_column(
        String(20), default="normal", server_default="normal"
    )
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Activity(WorkFields, Base):
    __tablename__ = "activities"
    __table_args__ = (
        *constraints("activity"),
        CheckConstraint(
            "status IN ('planned','done','cancelled')", name="valid_activity_status"
        ),
        CheckConstraint(
            "kind IN ('call','meeting','note')", name="valid_activity_kind"
        ),
        CheckConstraint(
            "status!='planned' OR scheduled_at IS NOT NULL",
            name="activity_schedule_required",
        ),
        CheckConstraint(
            "(status='done') = (occurred_at IS NOT NULL)",
            name="activity_completion_consistent",
        ),
        Index("ix_activity_schedule", "business_unit_id", "status", "scheduled_at"),
    )
    kind: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(
        String(20), default="planned", server_default="planned"
    )
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    occurred_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    outcome: Mapped[str | None] = mapped_column(Text)


class Reminder(Base):
    __tablename__ = "reminders"
    __table_args__ = (
        ForeignKeyConstraint(
            ["task_id", "business_unit_id"], ["tasks.id", "tasks.business_unit_id"]
        ),
        ForeignKeyConstraint(
            ["activity_id", "business_unit_id"],
            ["activities.id", "activities.business_unit_id"],
        ),
        CheckConstraint(
            "(task_id IS NULL) != (activity_id IS NULL)", name="one_reminder_context"
        ),
        ForeignKeyConstraint(
            ["recipient_id", "business_unit_id"],
            ["memberships.user_id", "memberships.business_unit_id"],
        ),
        CheckConstraint(
            "status IN ('pending','delivered','cancelled')",
            name="valid_reminder_status",
        ),
        CheckConstraint(
            "read_at IS NULL OR status='delivered'", name="reminder_read_delivered"
        ),
        Index("ix_reminder_due", "status", "fire_at"),
        Index("ix_reminder_recipient", "business_unit_id", "recipient_id"),
        Index(
            "unique_task_pending_reminder",
            "task_id",
            unique=True,
            postgresql_where="status = 'pending'",
        ),
        Index(
            "unique_activity_pending_reminder",
            "activity_id",
            unique=True,
            postgresql_where="status = 'pending'",
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    business_unit_id: Mapped[int] = mapped_column(Integer)
    task_id: Mapped[int | None] = mapped_column(Integer)
    activity_id: Mapped[int | None] = mapped_column(Integer)
    recipient_id: Mapped[int] = mapped_column(Integer)
    fire_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(
        String(20), default="pending", server_default="pending"
    )
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class WorkEvent(Base):
    __tablename__ = "work_events"
    __table_args__ = (
        ForeignKeyConstraint(
            ["task_id", "business_unit_id"], ["tasks.id", "tasks.business_unit_id"]
        ),
        ForeignKeyConstraint(
            ["activity_id", "business_unit_id"],
            ["activities.id", "activities.business_unit_id"],
        ),
        ForeignKeyConstraint(
            ["actor_id", "business_unit_id"],
            ["memberships.user_id", "memberships.business_unit_id"],
        ),
        CheckConstraint(
            "(task_id IS NULL) != (activity_id IS NULL)", name="one_work_event_context"
        ),
        Index("ix_work_event_task", "task_id", "id"),
        Index("ix_work_event_activity", "activity_id", "id"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    business_unit_id: Mapped[int] = mapped_column(Integer)
    task_id: Mapped[int | None] = mapped_column(Integer)
    activity_id: Mapped[int | None] = mapped_column(Integer)
    actor_id: Mapped[int] = mapped_column(Integer)
    action: Mapped[str] = mapped_column(String(20))
    changes: Mapped[dict] = mapped_column(JSONB)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
