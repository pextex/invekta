from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models import Company, Membership
from app.security import COOKIE_NAME
from test_marketing_orders import orders, ORIGIN

BASE = '/api/units/1/companies'
FORM = {'name': 'Ugovor Test', 'city': 'Beograd', 'sector': 'Test',
        'contract_signed_on': '2026-01-01', 'contract_expires_on': '2026-10-29'}


def test_dates_create_edit_clear_validation_and_ownership(orders):
    client, engine = orders
    client.cookies.set(COOKIE_NAME, '3', path='/api')
    response = client.post(BASE, json=FORM, headers=ORIGIN)
    assert response.status_code == 201, response.text
    row = response.json()
    assert row['contract_signed_on'] == '2026-01-01' and row['contract_expires_on'] == '2026-10-29'
    id = row['id']
    assert client.get(f'{BASE}/{id}').json()['contract_expires_on'] == '2026-10-29'
    assert client.get(BASE).json()[0].get('contract_signed_on') is None  # Legacy company, no invented dates.
    invalid = {**FORM, 'name': 'Invalid', 'contract_expires_on': '2025-01-01'}
    assert client.post(BASE, json=invalid, headers=ORIGIN).status_code == 422
    assert client.post(BASE, json={**FORM, 'contract_expires_on': '2026-02-30'}, headers=ORIGIN).status_code == 422
    # PATCH must validate against the effective stored dates, including omitted fields.
    assert client.patch(f'{BASE}/{id}', json={**{k:v for k,v in FORM.items() if k != 'contract_signed_on'}, 'contract_expires_on': '2025-01-01'}, headers=ORIGIN).status_code == 422
    assert client.get(f'{BASE}/{id}').json()['contract_expires_on'] == '2026-10-29'
    assert client.patch(f'{BASE}/{id}', json={**FORM, 'contract_expires_on': '2027-10-29'}, headers=ORIGIN).json()['contract_expires_on'] == '2027-10-29'
    assert client.patch(f'{BASE}/{id}', json={**FORM, 'contract_signed_on': None, 'contract_expires_on': None}, headers=ORIGIN).json()['contract_expires_on'] is None
    client.cookies.set(COOKIE_NAME, '2', path='/api')
    assert client.patch(f'{BASE}/{id}', json=FORM, headers=ORIGIN).status_code == 404
    assert client.get(f'{BASE}/{id}').status_code == 404
    client.cookies.set(COOKIE_NAME, '3', path='/api')
    assert client.patch(f'{BASE}/{id}', json=FORM).status_code == 403


def test_reminders_scope_boundaries_pagination_and_renewal(orders, monkeypatch):
    from app.api import contracts
    today = date(2026, 10, 29)
    monkeypatch.setattr(contracts, 'contract_today', lambda: today)
    client, engine = orders
    with Session(engine) as db:
        for i, days in enumerate([-1, 0, 30, 31], 10):
            db.add(Company(id=i, business_unit_id=1, owner_id=3, name=f'Contract {i}', city='Test', sector='Test', contract_expires_on=today+timedelta(days=days)))
        db.add(Company(id=20, business_unit_id=1, owner_id=2, name='Other owner', city='Test', sector='Test', contract_expires_on=today))
        db.add(Company(id=21, business_unit_id=1, owner_id=3, name='Demo', city='Test', sector='Test', contract_expires_on=today, is_demo=True))
        db.add(Membership(user_id=3, business_unit_id=2, role='sales'));db.flush()
        db.add(Company(id=22, business_unit_id=2, owner_id=3, name='Other brand', city='Test', sector='Test', contract_expires_on=today))
        db.commit()
    endpoint = '/api/units/1/contract-reminders'
    client.cookies.set(COOKIE_NAME, '3', path='/api')
    response = client.get(endpoint).json()
    assert response['today'] == '2026-10-29' and response['reminder_days'] == 30
    assert response['total'] == 3 and [r['days_remaining'] for r in response['items']] == [-1, 0, 30]
    assert client.get(endpoint+'?limit=1&offset=1').json()['items'][0]['company_id'] == 11
    assert client.get(endpoint+'?limit=0').status_code == 422
    assert client.get(endpoint+'?offset=-1').status_code == 422
    with Session(engine) as db:
        db.get(Company, 11).contract_expires_on = today + timedelta(days=365);db.commit()
    assert client.get(endpoint).json()['total'] == 2
    for token in ['4', '5']:
        client.cookies.set(COOKIE_NAME, token, path='/api')
        assert client.get(endpoint).json()['total'] == 3
    client.cookies.set(COOKIE_NAME, '1', path='/api')
    assert client.get(endpoint).json() == {'today':'2026-10-29','reminder_days':30,'total':0,'items':[]}
    assert client.get('/api/units/2/contract-reminders').status_code == 403
    client.cookies.clear()
    assert client.get(endpoint).status_code == 401
