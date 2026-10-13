from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base


class BusinessUnit(Base):
    __tablename__ = "business_units"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True)
    name: Mapped[str] = mapped_column(String(100))


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True)
    email: Mapped[str | None] = mapped_column(String(254), unique=True)
    name: Mapped[str] = mapped_column(String(150))
    password_hash: Mapped[str] = mapped_column(String(300))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_platform_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    version: Mapped[int] = mapped_column(Integer, default=1)


class Membership(Base):
    __tablename__ = "memberships"
    __table_args__ = (
        CheckConstraint(
            "role IN ('sales', 'manager', 'admin')", name="valid_membership_role"
        ),
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    business_unit_id: Mapped[int] = mapped_column(
        ForeignKey("business_units.id"), primary_key=True
    )
    role: Mapped[str] = mapped_column(String(20))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class LoginSession(Base):
    __tablename__ = "login_sessions"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class LoginAttempt(Base):
    __tablename__ = "login_attempts"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(254))
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    __table_args__ = (Index("ix_attempt_username_time", "username", "attempted_at"),)


class Company(Base):
    __tablename__ = "companies"
    __table_args__ = (
        ForeignKeyConstraint(
            ["owner_id", "business_unit_id"],
            ["memberships.user_id", "memberships.business_unit_id"],
        ),
        CheckConstraint(
            "stage IN ('Kontakt', 'Ponuda', 'Pregovori')", name="valid_company_stage"
        ),
        CheckConstraint("potential_value >= 0", name="nonnegative_company_value"),
        UniqueConstraint(
            "business_unit_id", "name", name="unique_company_name_per_unit"
        ),
        UniqueConstraint("id", "business_unit_id", name="unique_company_id_unit"),
        Index("ix_company_unit_owner", "business_unit_id", "owner_id"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    business_unit_id: Mapped[int] = mapped_column(ForeignKey("business_units.id"))
    owner_id: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(200))
    city: Mapped[str] = mapped_column(String(100))
    sector: Mapped[str] = mapped_column(String(100))
    stage: Mapped[str] = mapped_column(String(30), default="Kontakt")
    potential_value: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), default=Decimal("0")
    )
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Contact(Base):
    __tablename__ = "contacts"
    __table_args__ = (
        ForeignKeyConstraint(
            ["company_id", "business_unit_id"],
            ["companies.id", "companies.business_unit_id"],
            name="contact_company_unit_fk",
        ),
        Index("ix_contact_company_unit", "company_id", "business_unit_id"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(Integer)
    business_unit_id: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(150))
    position: Mapped[str | None] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(254))
    phone: Mapped[str | None] = mapped_column(String(40))
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Opportunity(Base):
    __tablename__ = "opportunities"
    __table_args__ = (
        ForeignKeyConstraint(
            ["company_id", "business_unit_id"],
            ["companies.id", "companies.business_unit_id"],
            name="opportunity_company_unit_fk",
        ),
        UniqueConstraint("id", "business_unit_id", name="unique_opportunity_id_unit"),
        CheckConstraint(
            "stage IN ('Novi lead', 'Kontaktiran', 'Sastanak', 'Ponuda', 'Pregovori', 'Dobijeno', 'Izgubljeno')",
            name="valid_opportunity_stage",
        ),
        CheckConstraint("amount >= 0", name="nonnegative_opportunity_amount"),
        CheckConstraint("version >= 1", name="positive_opportunity_version"),
        Index("ix_opportunity_unit_stage", "business_unit_id", "stage"),
        Index("ix_opportunity_company", "company_id"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(Integer)
    business_unit_id: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(200))
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    stage: Mapped[str] = mapped_column(String(30), default="Novi lead")
    expected_close_date: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class OpportunityStageChange(Base):
    __tablename__ = "opportunity_stage_changes"
    __table_args__ = (
        ForeignKeyConstraint(
            ["opportunity_id", "business_unit_id"],
            ["opportunities.id", "opportunities.business_unit_id"],
            name="stage_change_opportunity_unit_fk",
        ),
        ForeignKeyConstraint(
            ["actor_id", "business_unit_id"],
            ["memberships.user_id", "memberships.business_unit_id"],
            name="stage_change_actor_unit_fk",
        ),
        CheckConstraint(
            "to_stage IN ('Novi lead', 'Kontaktiran', 'Sastanak', 'Ponuda', 'Pregovori', 'Dobijeno', 'Izgubljeno')",
            name="valid_history_to_stage",
        ),
        CheckConstraint(
            "from_stage IS NULL OR from_stage IN ('Novi lead', 'Kontaktiran', 'Sastanak', 'Ponuda', 'Pregovori', 'Dobijeno', 'Izgubljeno')",
            name="valid_history_from_stage",
        ),
        Index("ix_stage_change_opportunity", "opportunity_id"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    opportunity_id: Mapped[int] = mapped_column(Integer)
    business_unit_id: Mapped[int] = mapped_column(Integer)
    actor_id: Mapped[int] = mapped_column(Integer)
    from_stage: Mapped[str | None] = mapped_column(String(30))
    to_stage: Mapped[str] = mapped_column(String(30))
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class AiDraft(Base):
    __tablename__ = "ai_drafts"
    __table_args__ = (
        ForeignKeyConstraint(
            ["company_id", "business_unit_id"],
            ["companies.id", "companies.business_unit_id"],
        ),
        ForeignKeyConstraint(
            ["actor_id", "business_unit_id"],
            ["memberships.user_id", "memberships.business_unit_id"],
        ),
        CheckConstraint("version >= 1", name="positive_ai_draft_version"),
        Index("ix_ai_draft_actor_unit", "actor_id", "business_unit_id"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    business_unit_id: Mapped[int] = mapped_column(Integer)
    company_id: Mapped[int] = mapped_column(Integer)
    actor_id: Mapped[int] = mapped_column(Integer)
    mode: Mapped[str] = mapped_column(String(20))
    subject: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)
    recipient: Mapped[str | None] = mapped_column(String(254))
    model: Mapped[str] = mapped_column(String(100))
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class AiAttempt(Base):
    __tablename__ = "ai_attempts"
    id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    __table_args__ = (Index("ix_ai_attempt_actor_time", "actor_id", "created_at"),)
