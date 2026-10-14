from datetime import datetime, timezone
from decimal import Decimal
import pytest
from app.models import Opportunity, OpportunityStageChange
from test_crm import login, ORIGIN, sales_records as seed_sales_records


@pytest.fixture
def sales_records(db, data):
    seed_sales_records.__wrapped__(db, data)


def metrics(client, suffix=''):
    response = client.get('/api/units/101/summary' + suffix)
    assert response.status_code == 200
    return response.json()


def test_won_status_and_amount_propagate_and_persist(client, sales_records):
    login(client, 'sales')
    before = metrics(client)
    assert before['lost_count'] == 0
    change = client.patch('/api/units/101/opportunities/2001/stage',
                          json={'stage': 'Dobijeno', 'version': 1}, headers=ORIGIN)
    assert change.status_code == 200
    after = metrics(client)
    assert after['open_count'] == 0 and after['won_count'] == 1
    assert Decimal(after['won_value']) == Decimal('100.10')
    assert Decimal(after['stage_values']['Dobijeno']) == Decimal('100.10')
    assert after['sales_results'][0]['owner_id'] == 102
    assert after['company_results'][0]['company_id'] == 101
    transition = next(t for t in after['transitions'] if t['to_stage'] == 'Dobijeno')
    assert transition['count'] == 1 and transition['source_count'] == 1
    assert transition['rate'] == 100
    assert after['timeline'][0]['count'] == 1
    history = client.get('/api/units/101/opportunities/2001/stage-history').json()
    assert history[0]['actor_name'] == 'sales'
    assert history[0]['changed_at']
    assert client.patch('/api/units/101/opportunities/2001/stage',
                        json={'stage': 'Izgubljeno', 'version': 1}, headers=ORIGIN).status_code == 409
    body = {'title': 'Prilika A', 'amount': '155.55', 'stage': 'Dobijeno',
            'expected_close_date': '2027-01-01', 'notes': None, 'version': 2}
    assert client.patch('/api/units/101/opportunities/2001', json=body, headers=ORIGIN).status_code == 200
    client.post('/api/auth/logout', json={}, headers=ORIGIN)
    assert client.get('/api/units/101/summary').status_code == 401
    login(client, 'sales')
    assert Decimal(metrics(client)['won_value']) == Decimal('155.55')
    profile = client.get('/api/units/101/opportunities?company_id=101').json()
    assert profile['items'][0]['stage'] == 'Dobijeno'
    login(client)
    result = metrics(client)
    assert result['opportunity_count'] == 2 and result['won_count'] == 1
    assert Decimal(result['open_value']) == Decimal('200.20')
    login(client, 'outsider')
    assert client.get('/api/units/101/summary').status_code == 403
    own = client.get('/api/units/102/summary').json()
    assert Decimal(own['won_value']) == Decimal('300.30')


def test_owner_filters_never_expand_sales_scope(client, sales_records):
    login(client, 'sales')
    assert client.get('/api/units/101/summary?owner_id=103').status_code == 404
    assert client.get('/api/units/101/opportunities?owner_id=103').status_code == 404
    assert {u['id'] for u in metrics(client)['owners']} == {102}
    login(client)
    result = metrics(client, '?owner_id=103')
    assert result['company_count'] == 1 and result['contact_count'] == 1
    assert result['opportunity_count'] == 1
    assert Decimal(result['open_value']) == Decimal('200.20')
    assert client.get('/api/units/101/opportunities?owner_id=103').json()['total'] == 1
    assert client.get('/api/units/101/summary?owner_id=104').status_code == 404


def test_date_cohort_inclusive_belgrade_and_shared_with_pipeline(client, db, sales_records):
    db.get(Opportunity, 2001).created_at = datetime(2026, 10, 13, 22, 0, tzinfo=timezone.utc)
    db.get(Opportunity, 2002).created_at = datetime(2026, 10, 14, 22, 0, tzinfo=timezone.utc)
    db.commit()
    login(client)
    query = '?start_date=2026-10-14&end_date=2026-10-14'
    result = metrics(client, query)
    assert result['opportunity_count'] == 1
    assert Decimal(result['open_value']) == Decimal('100.10')
    assert client.get('/api/units/101/opportunities' + query).json()['total'] == 1
    assert result['transitions'] == [] and result['timeline'] == []
    empty = metrics(client, '?start_date=2020-01-01&end_date=2020-01-02')
    assert empty['opportunity_count'] == 0 and empty['won_count'] == 0
    assert empty['company_count'] == 2  # Stock total, independent of opportunity cohort dates.


@pytest.mark.parametrize('query', ['?start_date=2027-01-02&end_date=2027-01-01',
                                   '?owner_id=0', '?start_date=bad'])
def test_filter_validation(client, query):
    login(client)
    assert client.get('/api/units/101/summary' + query).status_code == 422
    assert client.get('/api/units/101/opportunities' + query).status_code == 422


def test_conversion_counts_distinct_opportunities_not_repeated_moves(client, db, sales_records):
    for source, target in [('Kontaktiran', 'Ponuda'), ('Ponuda', 'Kontaktiran'), ('Kontaktiran', 'Ponuda')]:
        db.add(OpportunityStageChange(opportunity_id=2001, business_unit_id=101,
                                      actor_id=102, from_stage=source, to_stage=target))
    db.commit()
    login(client, 'sales')
    row = next(t for t in metrics(client)['transitions'] if t['from_stage'] == 'Kontaktiran')
    assert row['count'] == row['source_count'] == 1 and row['rate'] == 100
