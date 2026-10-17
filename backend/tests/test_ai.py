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
    settings = get_settings().model_copy(update={"crm_ai_enabled": False, "crm_gemini_api_key": ""})
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
            "crm_gemini_api_key": "test-placeholder",
            "crm_gemini_model": "gemini-test-model",
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
    assert set(draft) == {"subject", "body", "recipient", "recipients", "model"}
    assert draft["recipients"] == [{"id": contact.id, "name": "Test Contact", "position": "Direktor", "email": "recipient@example.com"}]
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
        lambda: get_settings().model_copy(update={"crm_ai_enabled": True, "crm_gemini_api_key": ""}),
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


def test_gemini_protocol_and_invalid_outputs(monkeypatch):
    monkeypatch.setattr(ai_provider, "get_settings", lambda: get_settings().model_copy(
        update={"crm_ai_enabled": True, "crm_gemini_api_key": "test-gemini-placeholder", "crm_gemini_model": "gemini-test-model"}))
    captured = []
    response = {"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": json.dumps({"subject": "Subject", "body": "Body"})}]}}]}

    def transport(request, timeout):
        captured.append(json.loads(request.data))
        assert request.full_url == "https://generativelanguage.googleapis.com/v1beta/models/gemini-test-model:generateContent"
        assert request.get_header("X-goog-api-key") == "test-gemini-placeholder"
        assert request.get_header("Authorization") is None
        assert "test-gemini-placeholder" not in request.full_url
        assert request.get_header("User-agent") == "InvektaCRM/0.4"
        assert request.get_header("Accept") == "application/json"
        assert timeout == 45
        return io.BytesIO(json.dumps(response).encode())

    monkeypatch.setattr(ai_provider, "urlopen", transport)
    assert ai_provider.generate({"instructions": "Write an email"}).subject == "Subject"
    assert captured[0]["generationConfig"]["responseMimeType"] == "application/json"
    assert captured[0]["generationConfig"]["responseJsonSchema"]["required"] == ["subject", "body"]
    assert "Invekta AI" in captured[0]["systemInstruction"]["parts"][0]["text"]
    assert "tools" not in captured[0]
    assert json.loads(captured[0]["contents"][0]["parts"][0]["text"])["instructions"] == "Write an email"
    for finish in ("MAX_TOKENS", "SAFETY", "RECITATION", None):
        response["candidates"][0]["finishReason"] = finish
        with pytest.raises(HTTPException) as error:
            ai_provider.generate({})
        assert error.value.status_code == 502
    response["candidates"][0]["finishReason"] = "STOP"
    for content in ('{"subject":"x","body":"y","send":true}', '{"subject":" ","body":"y"}', 'not JSON', None):
        response["candidates"][0]["content"]["parts"] = [{"text": content}]
        with pytest.raises(HTTPException):
            ai_provider.generate({})
    response["candidates"] = []
    with pytest.raises(HTTPException):
        ai_provider.generate({})

    for code, status in ((400, 503), (401, 503), (403, 503), (404, 503), (429, 503), (500, 502)):
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


def test_legacy_openai_key_is_never_sent_to_gemini(monkeypatch):
    monkeypatch.setattr(ai_provider, "get_settings", lambda: get_settings().model_copy(
        update={"crm_ai_enabled": True, "crm_ai_api_key": "legacy-test-placeholder", "crm_gemini_api_key": ""}))
    def forbidden(*args, **kwargs):
        raise AssertionError("A legacy key must not be sent to another provider")
    monkeypatch.setattr(ai_provider, "urlopen", forbidden)
    with pytest.raises(HTTPException) as error:
        ai_provider.generate({})
    assert error.value.status_code == 503


def test_gemini_access_failure_is_safe_in_real_api(client, db, monkeypatch):
    settings = get_settings().model_copy(update={
        "crm_ai_enabled": True, "crm_gemini_api_key": "private-test-placeholder",
    })
    monkeypatch.setattr(ai, "get_settings", lambda: settings)
    monkeypatch.setattr(ai_provider, "get_settings", lambda: settings)

    def transport(request, timeout):
        raise HTTPError(request.full_url, 403, "private-test-placeholder", {}, io.BytesIO(
            b'{"error":{"status":"PERMISSION_DENIED","message":"private-test-placeholder"}}'))

    monkeypatch.setattr(ai_provider, "urlopen", transport)
    login(client)
    response = client.post(BASE + "/generate", json=payload(), headers=ORIGIN)
    assert response.status_code == 503
    assert "dozvole" in response.json()["detail"]
    assert "private-test-placeholder" not in response.text
    assert db.scalar(select(func.count()).select_from(AiDraft)) == 0
    assert db.scalar(select(func.count()).select_from(AiAttempt)) == 1


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
    assert response.json()["model"] == "gemini-test-model"
    assert provider[0]["brand_knowledge"] == {"brand": "Test LUU", "content": "Approved LUU offering"}
    assert "Other brand knowledge" not in json.dumps(provider[0])
    status = client.get(BASE + "/status").json()
    assert status["engine"] == "gemini" and status["configured"] is True
    assert "test-placeholder" not in json.dumps(status)


def test_two_field_compose_automatically_uses_real_company_contacts_without_exposing_emails_to_model(client, db, provider):
    people = [
        Contact(company_id=101, business_unit_id=101, name="Jelena", position="Direktor", email="jelena@example.com"),
        Contact(company_id=101, business_unit_id=101, name="Marko", position="Nabavka", email="marko@example.com"),
        Contact(company_id=101, business_unit_id=101, name="Duplikat", email="JELENA@example.com"),
        Contact(company_id=101, business_unit_id=101, name="Bez emaila"),
        Contact(company_id=101, business_unit_id=101, name="Stari neispravan unos", email="not-an-email"),
        Contact(company_id=102, business_unit_id=101, name="Tuđ kontakt", email="other@example.com"),
        Contact(company_id=103, business_unit_id=102, name="Drugi brend", email="brand@example.com"),
    ]
    db.add_all(people)
    db.commit()
    login(client)
    path = BASE + "/companies/101/recipients"
    preview = client.get(path)
    assert preview.status_code == 200
    assert [item["email"] for item in preview.json()] == ["jelena@example.com", "marko@example.com"]
    response = client.post(BASE + "/generate", json={"company_id": 101, "instructions": "Napiši kratak odgovor na engleskom."}, headers=ORIGIN)
    assert response.status_code == 200
    output = response.json()
    assert output["recipient"] == "jelena@example.com, marko@example.com"
    assert output["recipients"] == preview.json()
    context = provider[0]
    assert context["contact"] is None
    assert context["contacts"] == [{"name": "Jelena", "position": "Direktor"}, {"name": "Marko", "position": "Nabavka"}]
    assert all(context[key] == "auto" for key in ("mode", "goal", "tone", "language"))
    assert "@example.com" not in json.dumps(context)
    assert "Tuđ kontakt" not in json.dumps(context) and "Drugi brend" not in json.dumps(context)
    assert db.scalar(select(func.count()).select_from(AiDraft)) == 0
    # An explicit contact_id from an older API client still narrows recipients.
    narrowed = client.post(BASE + "/generate", json=payload(contact_id=people[1].id), headers=ORIGIN)
    assert narrowed.status_code == 200 and narrowed.json()["recipient"] == "marko@example.com"
    assert provider[1]["contact"]["name"] == "Marko"


def test_recipient_preview_requires_company_access_and_enabled_membership(client, db):
    from app.models import Membership
    db.add(Contact(company_id=102, business_unit_id=101, name="Other company contact", email="other@example.com"))
    db.commit()
    path = BASE + "/companies/102/recipients"
    assert client.get(path).status_code == 401
    login(client)
    assert client.get(path).status_code == 404
    assert client.get("/api/units/102/ai/companies/103/recipients").status_code == 403
    login(client, "manager")
    assert client.get(path).json()[0]["email"] == "other@example.com"
    assert client.get(BASE + "/companies/103/recipients").status_code == 404
    db.get(Membership, (101, 101)).enabled = False
    db.commit()
    assert client.get(path).status_code == 403


def test_missing_contact_email_stays_empty_and_blank_simple_instructions_are_rejected(client, db, provider):
    db.add(Contact(company_id=101, business_unit_id=101, name="Kontakt bez emaila"))
    db.commit()
    login(client)
    assert client.get(BASE + "/companies/101/recipients").json() == []
    for instructions in ("", "   "):
        assert client.post(BASE + "/generate", json=payload(instructions=instructions), headers=ORIGIN).status_code == 422
    assert not provider
    result = client.post(BASE + "/generate", json=payload(), headers=ORIGIN)
    assert result.status_code == 200 and result.json()["recipient"] is None
    assert result.json()["recipients"] == [] and provider[0]["contacts"] == []


def test_recipient_addresses_are_refreshed_after_generation_and_new_owner_blocks_response(client, db, provider, monkeypatch):
    from app.models import Company
    person = Contact(company_id=101, business_unit_id=101, name="Kontakt", email="old@example.com")
    db.add(person)
    db.commit()
    login(client)
    def change_address(context):
        person.email = "current@example.com"
        db.commit()
        return GeneratedDraft(subject="Subject", body="Body")
    monkeypatch.setattr(ai, "generate", change_address)
    result = client.post(BASE + "/generate", json=payload(), headers=ORIGIN)
    assert result.status_code == 200 and result.json()["recipient"] == "current@example.com"
    def transfer_company(context):
        db.get(Company, 101).owner_id = 103
        db.commit()
        return GeneratedDraft(subject="Private", body="Must not be returned")
    monkeypatch.setattr(ai, "generate", transfer_company)
    result = client.post(BASE + "/generate", json=payload(), headers=ORIGIN)
    assert result.status_code == 404 and "Must not be returned" not in result.text
    assert db.scalar(select(func.count()).select_from(AiDraft)) == 0


def test_two_field_compose_keeps_offline_templates_available_without_network(client, db, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Disabled Gemini must not use the network")
    monkeypatch.setattr(ai_provider, "urlopen", forbidden)
    db.add(Contact(company_id=101, business_unit_id=101, name="Test", email="recipient@example.com"))
    db.commit()
    login(client)
    result = client.post(BASE + "/generate", json={"company_id": 101, "instructions": "Predstavi našu ponudu."}, headers=ORIGIN)
    assert result.status_code == 200
    assert result.json()["recipient"] == "recipient@example.com"
    assert result.json()["model"] == "local-templates"
    assert result.json()["body"].strip()
    assert db.scalar(select(func.count()).select_from(AiDraft)) == 0
