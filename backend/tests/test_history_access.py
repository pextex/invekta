"""Exercise history authorization at the API boundary without a database."""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.api import sales
from app.db import get_db
from app.main import app
from app.security import current_user


@pytest.mark.parametrize("role,platform_admin,allowed", [
    ("sales", False, False), ("manager", False, True),
    ("admin", False, True), ("sales", True, True),
])
def test_history_access_and_unit_membership(monkeypatch, role, platform_admin, allowed):
    user = SimpleNamespace(id=102, is_platform_admin=platform_admin)
    db = MagicMock()
    db.execute.return_value.all.return_value = []
    db.scalar.return_value = 0

    def member(db, user, unit_id):
        if unit_id != 101:
            raise HTTPException(403, "No unit access")
        return SimpleNamespace(role=role)

    monkeypatch.setattr(sales, "membership", member)
    monkeypatch.setattr(sales, "visible_query", lambda *args: MagicMock())
    monkeypatch.setattr(sales, "opportunities_query", lambda *args: MagicMock())
    monkeypatch.setattr(sales, "visible_opportunity", lambda *args: None)
    app.dependency_overrides[current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: db
    params = {"date_from": "2026-10-19", "date_to": "2026-10-19"}
    try:
        with TestClient(app) as client:
            summary = client.get("/api/units/101/reports", params=params)
            assert summary.status_code == 200 and summary.json()["items"] == []
            history = client.get("/api/units/101/reports", params={**params, "include_history": True})
            assert history.status_code == (200 if allowed else 403)
            assert client.get("/api/units/101/opportunities/2001/stage-history").status_code == (200 if allowed else 403)
            assert client.get("/api/units/102/reports", params={**params, "include_history": True}).status_code == 403
            assert client.get("/api/units/102/opportunities/2001/stage-history").status_code == 403
    finally:
        app.dependency_overrides.clear()
