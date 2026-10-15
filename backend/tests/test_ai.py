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


@pytest.fixture(autouse=True)
def local_ai_settings(monkeypatch):
    # Tests never inherit enabled AI/key bindings from a developer environment.
    settings = get_settings().model_copy(update={"crm_ai_enabled": False, "crm_groq_api_key": ""})
    monkeypatch.setattr(ai, "get_settings", lambda: settings)
    monkeypatch.setattr(ai_provider, "get_settings", lambda: settings)



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
        update={
            "crm_ai_enabled": True,
            "crm_groq_api_key": "test-placeholder",
            "crm_groq_model": "test-model",
        }
    )
    monkeypatch.setattr(ai, "get_settings", lambda: settings)
    monkeypatch.setattr(ai_provider, "get_settings", lambda: settings)

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


def test_selected_context_and_message_response_are_not_persisted(client, db, provider):
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
        BASE + "/generate",
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
    assert result.status_code == 200
    draft = result.json()
    assert draft["recipient"] == "recipient@example.com"
    assert provider[0]["company"]["name"] == "Test firma A"
    assert provider[0]["opportunity"]["title"] == "Selected opportunity"
    assert provider[0]["language"] == "en"
    assert "recipient@example.com" not in json.dumps(provider[0])
    assert "Test firma B" not in json.dumps(provider[0])
    assert set(draft) == {"subject", "body", "recipient", "model"}
    assert db.scalar(select(func.count()).select_from(AiDraft)) == 0
    assert db.scalar(select(func.count()).select_from(AiAttempt)) == 1
    assert client.get(BASE + "/drafts").json()["total"] == 0


def test_retired_writes_cannot_save_content_and_legacy_records_remain_private(client, db, provider):
    old = AiDraft(actor_id=102, business_unit_id=101, company_id=101, mode="email",
                  subject="Historical", body="Existing body", model="local-templates")
    db.add(old)
    db.commit()
    login(client)
    assert client.post(BASE + "/drafts", json=payload(), headers=ORIGIN).status_code == 410
    assert client.patch(BASE + f"/drafts/{old.id}", json={"subject": "overwrite", "body": "new", "recipient": None, "version": 1}, headers=ORIGIN).status_code == 410
    assert not provider
    assert db.scalar(select(func.count()).select_from(AiAttempt)) == 0
    db.refresh(old)
    assert old.body == "Existing body" and old.version == 1
    assert client.get(BASE + "/drafts").json()["total"] == 1
    login(client, "manager")
    assert client.get(BASE + "/drafts").json()["total"] == 0
    assert client.patch(BASE + f"/drafts/{old.id}", json={}, headers=ORIGIN).status_code == 404
    assert client.post(BASE + "/drafts", json=payload(), headers={"Origin": "https://evil.example"}).status_code == 403


def test_access_context_validation_and_disabled_generation(
    client, db, provider, monkeypatch
):
    login(client)
    assert (
        client.post(
            BASE + "/generate", json=payload(company_id=102), headers=ORIGIN
        ).status_code
        == 404
    )
    assert (
        client.post(
            "/api/units/102/ai/generate", json=payload(company_id=103), headers=ORIGIN
        ).status_code
        == 403
    )
    foreign = Contact(company_id=102, business_unit_id=101, name="Other company")
    foreign_opp = Opportunity(company_id=102, business_unit_id=101, title="Other deal")
    db.add_all([foreign, foreign_opp])
    db.commit()
    assert (
        client.post(
            BASE + "/generate", json=payload(contact_id=foreign.id), headers=ORIGIN
        ).status_code
        == 404
    )
    assert (
        client.post(
            BASE + "/generate",
            json=payload(opportunity_id=foreign_opp.id),
            headers=ORIGIN,
        ).status_code
        == 404
    )
    assert (
        client.post(
            BASE + "/generate", json=payload(mode="reply"), headers=ORIGIN
        ).status_code
        == 422
    )
    assert (
        client.post(
            BASE + "/generate", json=payload(send=True), headers=ORIGIN
        ).status_code
        == 422
    )
    assert (
        client.post(
            BASE + "/generate", json=payload(), headers={"Origin": "https://evil.example"}
        ).status_code
        == 403
    )
    assert not provider
    monkeypatch.setattr(
        ai,
        "get_settings",
        lambda: get_settings().model_copy(update={"crm_ai_enabled": True, "crm_groq_api_key": ""}),
    )
    assert client.get(BASE + "/status").json()["configured"] is False
    assert (
        client.post(BASE + "/generate", json=payload(), headers=ORIGIN).status_code == 503
    )
    assert db.scalar(select(func.count()).select_from(AiDraft)) == 0
    assert db.scalar(select(func.count()).select_from(AiAttempt)) == 0


def test_generation_budget_failure_and_session_revocation(
    client, db, provider, monkeypatch
):
    login(client)

    def fail(context):
        raise HTTPException(502, "Upstream unavailable")

    monkeypatch.setattr(ai, "generate", fail)
    assert (
        client.post(BASE + "/generate", json=payload(), headers=ORIGIN).status_code == 502
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
        client.post(BASE + "/generate", json=payload(), headers=ORIGIN).status_code == 429
    )
    db.execute(delete(AiAttempt))
    db.commit()

    def revoked(context):
        db.execute(delete(LoginSession).where(LoginSession.user_id == 102))
        db.commit()
        return GeneratedDraft(subject="Subject", body="Body")

    monkeypatch.setattr(ai, "generate", revoked)
    assert (
        client.post(BASE + "/generate", json=payload(), headers=ORIGIN).status_code == 401
    )
    assert db.scalar(select(func.count()).select_from(AiDraft)) == 0


def test_groq_protocol_and_invalid_outputs(monkeypatch):
    monkeypatch.setattr(ai_provider, "get_settings", lambda: get_settings().model_copy(
        update={"crm_ai_enabled": True, "crm_groq_api_key": "test-groq-placeholder", "crm_groq_model": "test-model"}))
    captured = []
    response = {"choices": [{"finish_reason": "stop", "message": {"content": json.dumps({"subject": "Subject", "body": "Body"})}}]}

    def transport(request, timeout):
        captured.append(json.loads(request.data))
        assert request.full_url == "https://api.groq.com/openai/v1/chat/completions"
        assert request.get_header("Authorization") == "Bearer test-groq-placeholder"
        assert timeout == 45
        return io.BytesIO(json.dumps(response).encode())

    monkeypatch.setattr(ai_provider, "urlopen", transport)
    assert ai_provider.generate({"instructions": "Write an email"}).subject == "Subject"
    assert captured[0]["response_format"] == {"type": "json_object"}
    assert captured[0]["model"] == "test-model"
    assert captured[0]["messages"][0]["role"] == "system"
    assert "Invekta AI" in captured[0]["messages"][0]["content"]
    assert "tools" not in captured[0]
    assert json.loads(captured[0]["messages"][1]["content"])["instructions"] == "Write an email"
    for finish in ("length", "content_filter", None):
        response["choices"][0]["finish_reason"] = finish
        with pytest.raises(HTTPException) as error:
            ai_provider.generate({})
        assert error.value.status_code == 502
    response["choices"][0]["finish_reason"] = "stop"
    for content in ('{"subject":"x","body":"y","send":true}', '{"subject":" ","body":"y"}', 'not JSON', None):
        response["choices"][0]["message"]["content"] = content
        with pytest.raises(HTTPException):
            ai_provider.generate({})
    response["choices"] = []
    with pytest.raises(HTTPException):
        ai_provider.generate({})

    for code, status in ((429, 503), (401, 503), (403, 503), (500, 502)):
        def limited(request, timeout):
            raise HTTPError(request.full_url, code, "private upstream details", {}, None)
        monkeypatch.setattr(ai_provider, "urlopen", limited)
        with pytest.raises(HTTPException) as error:
            ai_provider.generate({})
        assert error.value.status_code == status
        assert "private upstream details" not in error.value.detail

    def timeout(request, timeout):
        raise TimeoutError()
    monkeypatch.setattr(ai_provider, "urlopen", timeout)
    with pytest.raises(HTTPException) as error:
        ai_provider.generate({})
    assert error.value.status_code == 504



def test_free_assistant_never_calls_paid_provider(client, monkeypatch):
    settings = get_settings().model_copy(
        update={"crm_ai_enabled": False, "crm_ai_api_key": "test-placeholder"}
    )
    monkeypatch.setattr(ai_provider, "get_settings", lambda: settings)
    monkeypatch.setattr(ai, "get_settings", lambda: settings)

    def forbidden(*args, **kwargs):
        raise AssertionError("Free assistant must never call a paid provider")

    monkeypatch.setattr(ai_provider, "urlopen", forbidden)
    login(client)
    assert client.get(BASE + "/status").json()["engine"] == "templates"
    response = client.post(
        BASE + "/generate", json=payload(goal="introduction", personalization={"offering":"održavanje poslovnih prostora", "sender_name":"Test Sender"}), headers=ORIGIN
    )
    assert response.status_code == 200
    assert response.json()["model"] == "local-templates"
    assert "Test LUU" in response.json()["body"]
    assert "održavanje poslovnih prostora" in response.json()["body"]
    assert "Test Sender" in response.json()["body"]
    with pytest.raises(HTTPException) as error:
        ai_provider.generate({})
    assert error.value.status_code == 503


def test_legacy_openai_key_is_never_sent_to_groq(monkeypatch):
    monkeypatch.setattr(ai_provider, "get_settings", lambda: get_settings().model_copy(
        update={"crm_ai_enabled": True, "crm_ai_api_key": "legacy-test-placeholder", "crm_groq_api_key": ""}))
    def forbidden(*args, **kwargs):
        raise AssertionError("A legacy key must not be sent to another provider")
    monkeypatch.setattr(ai_provider, "urlopen", forbidden)
    with pytest.raises(HTTPException) as error:
        ai_provider.generate({})
    assert error.value.status_code == 503


def test_only_current_brand_knowledge_and_selected_client_reach_provider(client, db, provider):
    from app.models import AiBrandKnowledge
    db.add_all([
        AiBrandKnowledge(business_unit_id=101, content="Approved LUU offering", updated_by_id=101),
        AiBrandKnowledge(business_unit_id=102, content="Other brand knowledge", updated_by_id=101),
    ])
    db.commit()
    login(client)
    response = client.post(BASE + "/generate", json=payload(), headers=ORIGIN)
    assert response.status_code == 200
    assert response.json()["model"] == "test-model"
    assert provider[0]["brand_knowledge"] == {"brand": "Test LUU", "content": "Approved LUU offering"}
    assert "Other brand knowledge" not in json.dumps(provider[0])
    status = client.get(BASE + "/status").json()
    assert status["engine"] == "groq" and status["configured"] is True
    assert "test-placeholder" not in json.dumps(status)
