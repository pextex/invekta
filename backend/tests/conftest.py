import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from app.db import get_db
from app.main import app
from app.models import BusinessUnit, Company, Membership, User
from app.security import hash_password


@pytest.fixture
def db():
    url = os.environ.get("CRM_TEST_DATABASE_URL")
    if not url or not make_url(url).database.endswith("_test"):
        pytest.fail(
            "CRM_TEST_DATABASE_URL mora pokazivati na izdvojenu bazu sa sufiksom _test."
        )
    engine = create_engine(url)
    with engine.connect() as connection:
        transaction = connection.begin()
        session = Session(
            bind=connection,
            join_transaction_mode="create_savepoint",
            expire_on_commit=False,
        )
        try:
            yield session
        finally:
            session.close()
            transaction.rollback()
    engine.dispose()


@pytest.fixture
def data(db):
    db.add_all(
        [
            BusinessUnit(id=101, code="TEST_LUU", name="Test LUU"),
            BusinessUnit(id=102, code="TEST_INVEKTA", name="Test Invekta"),
        ]
    )
    digest = hash_password("test-password-only-123")
    db.add_all(
        [
            User(id=i, username=name, name=name, password_hash=digest)
            for i, name in [
                (101, "manager"),
                (102, "sales"),
                (103, "other"),
                (104, "outsider"),
            ]
        ]
    )
    db.flush()
    db.add_all(
        [
            Membership(user_id=101, business_unit_id=101, role="manager"),
            Membership(user_id=101, business_unit_id=102, role="admin"),
            Membership(user_id=102, business_unit_id=101, role="sales"),
            Membership(user_id=103, business_unit_id=101, role="sales"),
            Membership(user_id=104, business_unit_id=102, role="sales"),
        ]
    )
    db.flush()
    db.add_all(
        [
            Company(
                id=101,
                business_unit_id=101,
                owner_id=102,
                name="Test firma A",
                city="Beograd",
                sector="Industrija",
            ),
            Company(
                id=102,
                business_unit_id=101,
                owner_id=103,
                name="Test firma B",
                city="Niš",
                sector="Hotelijerstvo",
            ),
            Company(
                id=103,
                business_unit_id=102,
                owner_id=104,
                name="Test firma C",
                city="Novi Sad",
                sector="Industrija",
            ),
        ]
    )
    db.commit()


@pytest.fixture
def client(db, data):
    def override():
        yield db

    app.dependency_overrides[get_db] = override
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
