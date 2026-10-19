"""Real profile API, session and password hashing against an isolated memory database."""
from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from app.main import app
from app.db import get_db
from app.models import User, LoginSession, LoginAttempt
from app.security import COOKIE_NAME, hash_password, token_hash, verify_password

ORIGIN = {"Origin": "http://localhost:5173"}
OLD = "profile-test-old-password"
NEW = "profile-test-new-password"

@pytest.fixture
def profile_client():
    engine = create_engine('sqlite://', connect_args={'check_same_thread':False}, poolclass=StaticPool)
    for model in (User, LoginSession, LoginAttempt):
        model.__table__.create(engine)
    with Session(engine) as db:
        db.add_all([User(id=i, username=f'profile{i}', email=f'profile{i}@example.com', name=f'User {i}', password_hash=hash_password(OLD)) for i in (1,2)])
        db.add_all([LoginSession(token_hash=token_hash(token),user_id=uid, expires_at=datetime.now(timezone.utc)+timedelta(hours=1)) for token,uid in [('current',1),('other-device',1),('other-user',2)]])
        db.commit()
    def connection():
        with Session(engine) as db: yield db
    app.dependency_overrides[get_db]=connection
    try:
        with TestClient(app) as client:
            client.cookies.set(COOKIE_NAME,'current',path='/api')
            yield client,engine
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def test_own_phone_persists_is_clearable_and_cannot_change_roles_or_other_users(profile_client):
    client,engine=profile_client
    assert client.get('/api/profile').json()=={'name':'User 1','email':'profile1@example.com','phone':None}
    result=client.patch('/api/profile',json={'phone':'+381 60 123 4567'},headers=ORIGIN)
    assert result.status_code==200 and result.json()['phone']=='+381 60 123 4567'
    assert client.get('/api/profile').json()['phone']=='+381 60 123 4567'
    for payload in [{'phone':'<script>bad</script>'},{'phone':'123'},{'phone':'123456','id':2},{'phone':'123456','is_platform_admin':True}]:
        assert client.patch('/api/profile',json=payload,headers=ORIGIN).status_code==422
    with Session(engine) as db:
        assert db.get(User,2).phone is None and db.get(User,1).is_platform_admin is False
    assert client.patch('/api/profile',json={'phone':'   '},headers=ORIGIN).json()['phone'] is None
    assert client.patch('/api/profile',json={'phone':'123456'}).status_code==403
    client.cookies.clear()
    assert client.get('/api/profile').status_code==401
    assert client.patch('/api/profile',json={'phone':'123456'},headers=ORIGIN).status_code==401


def test_password_requires_current_and_confirmation_then_revokes_only_other_sessions(profile_client):
    client,engine=profile_client
    payload={'current_password':OLD,'new_password':NEW,'confirm_password':NEW}
    assert client.post('/api/profile/password',json={**payload,'current_password':'wrong'},headers=ORIGIN).status_code==400
    assert client.post('/api/profile/password',json={**payload,'confirm_password':'does-not-match-password'},headers=ORIGIN).status_code==422
    assert client.post('/api/profile/password',json={**payload,'new_password':'short','confirm_password':'short'},headers=ORIGIN).status_code==422
    assert client.post('/api/profile/password',json=payload).status_code==403
    result=client.post('/api/profile/password',json=payload,headers=ORIGIN)
    assert result.status_code==200
    assert OLD not in result.text and NEW not in result.text
    with Session(engine) as db:
        assert verify_password(NEW,db.get(User,1).password_hash)
        assert not verify_password(OLD,db.get(User,1).password_hash)
        assert verify_password(OLD,db.get(User,2).password_hash)
        assert db.get(LoginSession,token_hash('current')) is not None
        assert db.get(LoginSession,token_hash('other-device')) is None
        assert db.get(LoginSession,token_hash('other-user')) is not None
        assert list(db.scalars(select(LoginAttempt)))==[]
    assert client.get('/api/profile').status_code==200
    client.cookies.set(COOKIE_NAME,'other-device',path='/api')
    assert client.get('/api/profile').status_code==401
    assert client.post('/api/auth/login',json={'email':'profile1@example.com','password':OLD},headers=ORIGIN).status_code==401
    assert client.post('/api/auth/login',json={'email':'profile1@example.com','password':NEW},headers=ORIGIN).status_code==200


def test_wrong_current_password_is_rate_limited_and_secrets_are_not_echoed(profile_client):
    client,engine=profile_client
    payload={'current_password':'wrong-password','new_password':NEW,'confirm_password':NEW}
    for _ in range(5): assert client.post('/api/profile/password',json=payload,headers=ORIGIN).status_code==400
    result=client.post('/api/profile/password',json={**payload,'current_password':OLD},headers=ORIGIN)
    assert result.status_code==429
    with Session(engine) as db: assert verify_password(OLD,db.get(User,1).password_hash)
    result=client.post('/api/profile/password',json={**payload,'unexpected':'secret-value'},headers=ORIGIN)
    assert result.status_code==422 and 'secret-value' not in result.text and NEW not in result.text
