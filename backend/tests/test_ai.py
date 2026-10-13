import io
import json
from datetime import datetime, timezone
from urllib.error import HTTPError
import pytest
from fastapi import HTTPException
from sqlalchemy import select, func, delete
from app.api import ai
from app import ai_provider
from app.ai_provider import GeneratedDraft
from app.config import get_settings
from app.models import AiDraft, AiAttempt, Contact, Opportunity, LoginSession

ORIGIN = {"Origin": "http://localhost:5173"}
BASE = "/api/units/101/ai"


def login(client, username="sales"):
    assert (
        client.post(
            "/api/auth/login",
            json={"username": username, "password": "test-password-only-123"},
            headers=ORIGIN,
        ).status_code
        == 200
    )


@pytest.fixture
def provider(monkeypatch):
    calls = []
    settings = get_settings().model_copy(
        update={"crm_ai_api_key": "test-placeholder", "crm_ai_model": "test-model"}
    )
    monkeypatch.setattr(ai, "get_settings", lambda: settings)

    def generate(context):
        calls.append(context)
        return GeneratedDraft(
            subject="Predlog sastanka",
            body="Poštovani, predlažemo kratak sastanak.\nSales · Test LUU",
        )

    monkeypatch.setattr(ai, "generate", generate)
    return calls


def payload(**extra):
    return {"company_id": 101, "instructions": "Predloži kratak sastanak", **extra}


def test_context_and_persistent_editable_private_draft(client, db, provider):
    contact = Contact(
        company_id=101,
        business_unit_id=101,
        name="Test Contact",
        email="recipient@example.com",
        position="Direktor",
    )
    opportunity = Opportunity(
        company_id=101,
        business_unit_id=101,
        title="Selected opportunity",
        stage="Ponuda",
        amount=45000,
        notes="Only selected notes",
    )
    db.add_all([contact, opportunity])
    db.commit()
    login(client)
    result = client.post(
        BASE + "/drafts",
        json=payload(
            contact_id=contact.id,
            opportunity_id=opportunity.id,
            mode="reply",
            incoming_message="Molim termin sastanka",
            tone="friendly",
            language="en",
        ),
        headers=ORIGIN,
    )
    assert result.status_code == 201
    draft = result.json()
    assert draft["recipient"] == "recipient@example.com"
    assert provider[0]["company"]["name"] == "Test firma A"
    assert provider[0]["opportunity"]["title"] == "Selected opportunity"
    assert provider[0]["language"] == "en"
    assert "recipient@example.com" not in json.dumps(provider[0])
    assert "Test firma B" not in json.dumps(provider[0])
    assert client.get(BASE + "/drafts").json()["total"] == 1
    body = {
        "subject": "Revised",
        "body": "Edited draft",
        "recipient": None,
        "version": draft["version"],
    }
    assert (
        client.patch(
            BASE + f"/drafts/{draft['id']}", json=body, headers=ORIGIN
        ).status_code
        == 200
    )
    assert (
        client.patch(
            BASE + f"/drafts/{draft['id']}", json=body, headers=ORIGIN
        ).status_code
        == 409
    )
    assert client.get(BASE + "/drafts").json()["items"][0]["body"] == "Edited draft"
    login(client, "manager")
    assert client.get(BASE + "/drafts").json()["total"] == 0
    assert (
        client.patch(
            BASE + f"/drafts/{draft['id']}", json={**body, "version": 2}, headers=ORIGIN
        ).status_code
        == 404
    )


def test_access_context_validation_and_disabled_generation(
    client, db, provider, monkeypatch
):
    login(client)
    assert (
        client.post(
            BASE + "/drafts", json=payload(company_id=102), headers=ORIGIN
        ).status_code
        == 404
    )
    assert (
        client.post(
            "/api/units/102/ai/drafts", json=payload(company_id=103), headers=ORIGIN
        ).status_code
        == 403
    )
    foreign = Contact(company_id=102, business_unit_id=101, name="Other company")
    foreign_opp = Opportunity(company_id=102, business_unit_id=101, title="Other deal")
    db.add_all([foreign, foreign_opp])
    db.commit()
    assert (
        client.post(
            BASE + "/drafts", json=payload(contact_id=foreign.id), headers=ORIGIN
        ).status_code
        == 404
    )
    assert (
        client.post(
            BASE + "/drafts",
            json=payload(opportunity_id=foreign_opp.id),
            headers=ORIGIN,
        ).status_code
        == 404
    )
    assert (
        client.post(
            BASE + "/drafts", json=payload(mode="reply"), headers=ORIGIN
        ).status_code
        == 422
    )
    assert (
        client.post(
            BASE + "/drafts", json=payload(send=True), headers=ORIGIN
        ).status_code
        == 422
    )
    assert (
        client.post(
            BASE + "/drafts", json=payload(), headers={"Origin": "https://evil.example"}
        ).status_code
        == 403
    )
    assert not provider
    monkeypatch.setattr(
        ai,
        "get_settings",
        lambda: get_settings().model_copy(update={"crm_ai_api_key": ""}),
    )
    assert client.get(BASE + "/status").json()["configured"] is False
    assert (
        client.post(BASE + "/drafts", json=payload(), headers=ORIGIN).status_code == 503
    )
    assert db.scalar(select(func.count()).select_from(AiDraft)) == 0


def test_generation_budget_failure_and_session_revocation(
    client, db, provider, monkeypatch
):
    login(client)

    def fail(context):
        raise HTTPException(502, "Upstream unavailable")

    monkeypatch.setattr(ai, "generate", fail)
    assert (
        client.post(BASE + "/drafts", json=payload(), headers=ORIGIN).status_code == 502
    )
    assert db.scalar(select(func.count()).select_from(AiDraft)) == 0
    db.add_all(
        [
            AiAttempt(actor_id=102, created_at=datetime.now(timezone.utc))
            for _ in range(19)
        ]
    )
    db.commit()
    assert (
        client.post(BASE + "/drafts", json=payload(), headers=ORIGIN).status_code == 429
    )
    db.execute(delete(AiAttempt))
    db.commit()

    def revoked(context):
        db.execute(delete(LoginSession).where(LoginSession.user_id == 102))
        db.commit()
        return GeneratedDraft(subject="Subject", body="Body")

    monkeypatch.setattr(ai, "generate", revoked)
    assert (
        client.post(BASE + "/drafts", json=payload(), headers=ORIGIN).status_code == 401
    )
    assert db.scalar(select(func.count()).select_from(AiDraft)) == 0


def test_responses_protocol_and_invalid_outputs(monkeypatch):
    monkeypatch.setattr(
        ai_provider,
        "get_settings",
        lambda: get_settings().model_copy(
            update={"crm_ai_api_key": "test-placeholder"}
        ),
    )
    captured = []
    response = {
        "status": "completed",
        "output": [
            {
                "type": "message",
                "content": [
                    {
                        "type": "output_text",
                        "text": json.dumps({"subject": "Subject", "body": "Body"}),
                    }
                ],
            }
        ],
    }

    def transport(request, timeout):
        captured.append(json.loads(request.data))
        assert request.full_url == "https://api.openai.com/v1/responses"
        assert timeout == 45
        return io.BytesIO(json.dumps(response).encode())

    monkeypatch.setattr(ai_provider, "urlopen", transport)
    result = ai_provider.generate({"instructions": "Write an email"})
    assert result.subject == "Subject"
    assert captured[0]["store"] is False
    assert captured[0]["text"]["format"]["strict"] is True
    assert "tools" not in captured[0]
    response["status"] = "incomplete"
    with pytest.raises(HTTPException) as error:
        ai_provider.generate({})
    assert error.value.status_code == 502
    response["status"] = "completed"
    response["output"][0]["content"][0]["text"] = (
        '{"subject":"x","body":"y","send":true}'
    )
    with pytest.raises(HTTPException):
        ai_provider.generate({})

    def limited(request, timeout):
        raise HTTPError(request.full_url, 429, "limited", {}, None)

    monkeypatch.setattr(ai_provider, "urlopen", limited)
    with pytest.raises(HTTPException) as error:
        ai_provider.generate({})
    assert error.value.status_code == 503

    def timeout(request, timeout):
        raise TimeoutError()

    monkeypatch.setattr(ai_provider, "urlopen", timeout)
    with pytest.raises(HTTPException) as error:
        ai_provider.generate({})
    assert error.value.status_code == 504
