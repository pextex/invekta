from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from sqlalchemy import func, select
from app import seed
from app.models import Company, LoginSession, User
from app.security import verify_password


def test_seed_is_idempotent_and_reset_revokes_sessions(db, data, monkeypatch):
    @contextmanager
    def begin():
        yield db
        db.commit()
    monkeypatch.setattr(seed, 'SessionLocal', SimpleNamespace(begin=begin))
    monkeypatch.setenv('CRM_DEMO_PASSWORD', 'first-demo-test-password')
    monkeypatch.setattr(seed.sys, 'argv', ['seed'])
    seed.main()
    user = db.scalar(select(User).where(User.username == 'demo'))
    initial_hash = user.password_hash
    count = db.scalar(select(func.count()).select_from(Company))
    monkeypatch.setenv('CRM_DEMO_PASSWORD', 'second-demo-test-password')
    seed.main()
    assert db.scalar(select(func.count()).select_from(Company)) == count
    assert user.password_hash == initial_hash
    db.add(LoginSession(token_hash='a' * 64, user_id=user.id, expires_at=datetime.now(timezone.utc) + timedelta(hours=1)))
    db.commit()
    monkeypatch.setattr(seed.sys, 'argv', ['seed', '--reset-password'])
    seed.main()
    assert verify_password('second-demo-test-password', user.password_hash)
    assert db.scalar(select(LoginSession).where(LoginSession.user_id == user.id)) is None
