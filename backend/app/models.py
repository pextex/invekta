from datetime import datetime
from decimal import Decimal
from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, ForeignKeyConstraint, Index, Integer, Numeric, String, UniqueConstraint, func
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
    name: Mapped[str] = mapped_column(String(150))
    password_hash: Mapped[str] = mapped_column(String(300))
    active: Mapped[bool] = mapped_column(Boolean, default=True)

class Membership(Base):
    __tablename__ = "memberships"
    __table_args__ = (CheckConstraint("role IN ('sales', 'manager', 'admin')", name="valid_membership_role"),)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    business_unit_id: Mapped[int] = mapped_column(ForeignKey("business_units.id"), primary_key=True)
    role: Mapped[str] = mapped_column(String(20))

class LoginSession(Base):
    __tablename__ = "login_sessions"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

class LoginAttempt(Base):
    __tablename__ = "login_attempts"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(100))
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (Index("ix_attempt_username_time", "username", "attempted_at"),)

class Company(Base):
    __tablename__ = "companies"
    __table_args__ = (
        ForeignKeyConstraint(["owner_id", "business_unit_id"], ["memberships.user_id", "memberships.business_unit_id"]),
        CheckConstraint("stage IN ('Kontakt', 'Ponuda', 'Pregovori')", name="valid_company_stage"),
        CheckConstraint("potential_value >= 0", name="nonnegative_company_value"),
        UniqueConstraint("business_unit_id", "name", name="unique_company_name_per_unit"),
        Index("ix_company_unit_owner", "business_unit_id", "owner_id"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    business_unit_id: Mapped[int] = mapped_column(ForeignKey("business_units.id"))
    owner_id: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(200))
    city: Mapped[str] = mapped_column(String(100))
    sector: Mapped[str] = mapped_column(String(100))
    stage: Mapped[str] = mapped_column(String(30), default="Kontakt")
    potential_value: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
