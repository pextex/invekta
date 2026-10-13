import pytest
from app.message_templates import generate


@pytest.mark.parametrize("language", ["sr", "en"])
def test_professional_reply_preserves_real_details_and_signature(language):
    result = generate(
        {
            "company": {"name": "Klijent Alfa"},
            "sender": {"name": "Petar", "organization": "Invekta"},
            "mode": "reply",
            "goal": "meeting",
            "tone": "professional",
            "language": language,
            "instructions": "Obilazak je moguć uz prethodnu najavu.",
            "personalization": {
                "topic": "održavanje kancelarija",
                "offering": "redovno održavanje poslovnog prostora",
                "meeting_time": "četvrtak u 10:00",
                "reply_text": "Radove možemo planirati van radnog vremena.",
                "sender_name": "Petar Milošević",
                "sender_title": "Menadžer prodaje",
                "sender_phone": "+381 11 123 456",
            },
        }
    )
    assert "Radove možemo planirati van radnog vremena." in result.body
    assert "četvrtak u 10:00" in result.body
    assert "Obilazak je moguć uz prethodnu najavu." in result.body
    assert "Petar Milošević\nMenadžer prodaje\nInvekta\n+381 11 123 456" in result.body
    assert "Poštovani/a" not in result.body
    assert "[Unesite" not in result.body and "[Add" not in result.body


def test_missing_facts_are_not_invented_and_concise_keeps_answer():
    context = {
        "company": {"name": "Klijent Alfa"},
        "sender": {"name": "Petar", "organization": "LUU"},
        "mode": "reply",
        "goal": "proposal",
        "tone": "concise",
        "language": "sr",
        "personalization": {"reply_text": "Potrebni su nam broj objekata i lokacije."},
    }
    result = generate(context)
    assert "Potrebni su nam broj objekata i lokacije." in result.body
    assert "EUR" not in result.body and "RSD" not in result.body
    assert "garant" not in result.body.lower()
    assert "Hvala Vam na vremenu" not in result.body
