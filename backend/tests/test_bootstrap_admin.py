from contextlib import contextmanager
from types import SimpleNamespace
import sys
import pytest
from sqlalchemy import func, select
from app import bootstrap_admin
from app.models import Membership, User
from app.security import verify_password


def install_session_factory(monkeypatch, db):
    @contextmanager
    def begin():
        transaction = db.begin_nested()
        try:
            yield db
        except BaseException:
            transaction.rollback()
            raise
        else:
            transaction.commit()

    monkeypatch.setattr(
        bootstrap_admin, "SessionLocal", SimpleNamespace(begin=begin)
    )


def run_cli(monkeypatch, email, *, activate=False, password=None):
    arguments = ["bootstrap_admin", "--email", email, "--name", "Test Owner"]
    if activate:
        arguments.append("--activate")
    monkeypatch.setattr(sys, "argv", arguments)
    if password is None:
        monkeypatch.delenv("CRM_ACCOUNT_PASSWORD", raising=False)
    else:
        monkeypatch.setenv("CRM_ACCOUNT_PASSWORD", password)
    bootstrap_admin.main()


def test_first_admin_activation_is_provisioned_and_single_use(db, monkeypatch):
    install_session_factory(monkeypatch, db)

    with pytest.raises(SystemExit, match="postojeći neaktivan"):
        run_cli(
            monkeypatch,
            "not-provisioned@example.com",
            activate=True,
            password="valid-password-123",
        )
    assert db.scalar(select(func.count()).select_from(User)) == 0

    run_cli(monkeypatch, "owner@example.com")
    owner = db.scalar(select(User).where(User.email == "owner@example.com"))
    assert owner is not None
    assert owner.is_platform_admin is True
    assert owner.active is False
    assert owner.bootstrap_pending is True
    assert db.scalar(
        select(func.count()).select_from(Membership).where(Membership.user_id == owner.id)
    ) == 3

    # Preparing the same pending owner is a no-op; it does not reset the profile.
    original_hash = owner.password_hash
    run_cli(monkeypatch, "owner@example.com")
    assert owner.password_hash == original_hash

    password = "owner-password-123"
    run_cli(monkeypatch, "owner@example.com", activate=True, password=password)
    assert owner.active is True
    assert owner.bootstrap_pending is False
    assert verify_password(password, owner.password_hash)
    activated_hash = owner.password_hash

    # A repeat must never reset the active owner's password or create another admin.
    with pytest.raises(SystemExit, match="postojeći neaktivan"):
        run_cli(
            monkeypatch,
            "owner@example.com",
            activate=True,
            password="different-password-456",
        )
    with pytest.raises(SystemExit, match="samo pre kreiranja"):
        run_cli(monkeypatch, "second-owner@example.com")

    assert owner.password_hash == activated_hash
    assert db.scalar(
        select(func.count()).select_from(User).where(User.is_platform_admin.is_(True))
    ) == 1
