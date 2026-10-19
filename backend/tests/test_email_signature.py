import io
import json
import pytest
from app import ai_provider
from app.config import get_settings
from app.email_signature import signature
from app.message_templates import generate as template


@pytest.mark.parametrize('code', ['LUU','INVEKTA','CENOBOTS'])
def test_account_signature_is_complete_brand_scoped_and_appended_after_generation(monkeypatch,code):
    sender={'name':'Marko Petrović','phone':'+381 60 123 4567','organization':code,'organization_code':code}
    expected=f'Marko Petrović\n{code}\n+381 60 123 4567\nhttps://{code.lower()}.rs/\nJablanička 184, Beograd'
    assert signature(sender)==expected
    context={'sender':sender,'company':{'name':'Primer klijenta'},'mode':'email','goal':'meeting','language':'sr'}
    assert template(context).body.endswith(expected)
    settings=get_settings().model_copy(update={'crm_ai_enabled':True,'crm_gemini_api_key':'test-placeholder'})
    monkeypatch.setattr(ai_provider,'get_settings',lambda:settings)
    response={'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':json.dumps({'subject':'Predlog saradnje','body':'Poštovani,\n\nPredlažem razgovor.\n\nSrdačan pozdrav,'})}]}}]}
    def transport(request, **kwargs):
        sent=json.loads(request.data)['contents'][0]['parts'][0]['text']
        assert sender['name'] not in sent and sender['phone'] not in sent
        return io.BytesIO(json.dumps(response).encode())
    monkeypatch.setattr(ai_provider,'urlopen',transport)
    draft=ai_provider.generate(context)
    assert draft.body.endswith('Srdačan pozdrav,\n'+expected)
    assert draft.body.count('Marko Petrović')==1
    assert all(f'https://{other.lower()}.rs/' not in draft.body for other in ['LUU','INVEKTA','CENOBOTS'] if other!=code)


def test_missing_phone_is_explicit_and_unknown_brand_address_is_never_guessed():
    result=signature({'name':'Ana Anić','organization':'Other'})
    assert '[Dopunite telefon u Moj profil]' in result
    assert 'Jablanička' not in result and 'https://' not in result
    assert '[Add phone number in My profile]' in signature({'name':'Ana Anić'},english=True)
