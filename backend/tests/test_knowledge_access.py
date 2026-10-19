"""Enforce knowledge visibility independently from edit permission and active unit access."""
from types import SimpleNamespace
from unittest.mock import MagicMock
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from app.api import ai, ai_knowledge
from app.main import app
from app.db import get_db
from app.security import current_user

@pytest.mark.parametrize('role,platform_admin,view,edit', [
    ('sales',False,False,False),('manager',False,True,False),
    ('admin',False,True,True),('sales',True,True,True),
])
def test_knowledge_view_edit_and_unit_boundaries(monkeypatch,role,platform_admin,view,edit):
    user=SimpleNamespace(id=1,is_platform_admin=platform_admin)
    db=MagicMock()
    db.get.return_value=None
    def member(db,user,unit_id):
        if unit_id!=101: raise HTTPException(403,'Inactive membership')
        return SimpleNamespace(role=role)
    monkeypatch.setattr(ai,'membership',member)
    monkeypatch.setattr(ai_knowledge,'membership',member)
    app.dependency_overrides[current_user]=lambda:user
    app.dependency_overrides[get_db]=lambda:db
    try:
        with TestClient(app) as client:
            flags=client.get('/api/units/101/ai/status').json()
            assert flags['can_view_knowledge'] is view
            assert flags['can_manage_knowledge'] is edit
            response=client.get('/api/units/101/ai/knowledge')
            assert response.status_code==(200 if view else 403)
            if not view: db.get.assert_not_called()
            if not edit:
                assert client.put('/api/units/101/ai/knowledge',json={'content':'Changed'},headers={'Origin':'http://localhost:5173'}).status_code==403
            assert client.get('/api/units/102/ai/knowledge').status_code==403
            assert client.get('/api/units/102/ai/status').status_code==403
    finally:
        app.dependency_overrides.clear()
