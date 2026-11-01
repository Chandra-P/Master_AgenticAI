import pytest
from fastapi.testclient import TestClient
from convene.api import create_app

BRIEF = dict(title='AI course celebration', city='Seattle', guests=40,
             budget=5000, event_date='2026-11-05', duration_hours=4,
             preferences='Accessible venue, vegetarian food')

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv('CONVENE_MODE', 'demo')
    monkeypatch.setenv('LANGSMITH_TRACING', 'false')
    return TestClient(create_app(str(tmp_path / 'test.db')))

def test_end_to_end_and_persistence(client):
    response = client.post('/plans', json=BRIEF)
    assert response.status_code == 201
    plan = response.json()
    assert plan['agent_steps'] == ['Requirements', 'Budget', 'Vendor', 'Schedule', 'Creative', 'Review']
    assert plan['mode'] == 'demo'
    assert plan['vendors']
    assert all(v['synthetic'] for v in plan['vendors'])
    assert plan['estimated_total'] <= BRIEF['budget']
    assert len(plan['schedule']) >= 3
    assert plan['review']['status'] == 'ready_for_human_review'
    assert client.get('/plans/' + plan['id']).json() == plan
    assert client.get('/plans').json()[0]['id'] == plan['id']

def test_low_budget_is_flagged(client):
    plan = client.post('/plans', json={**BRIEF, 'budget': 10}).json()
    assert plan['review']['status'] == 'needs_revision'
    assert plan['review']['warnings']

@pytest.mark.parametrize('changes', [dict(guests=0), dict(budget=-1), dict(title='  '),
    dict(event_date='not-a-date'), dict(duration_hours=0), dict(budget='NaN'), dict(city='')])
def test_invalid_brief(client, changes):
    assert client.post('/plans', json={**BRIEF, **changes}).status_code == 422

def test_missing_plan(client):
    assert client.get('/plans/missing').status_code == 404

def test_health(client):
    assert client.get('/health').json() == {'status': 'ok'}

def test_unknown_city_has_no_invented_vendors(client):
    plan = client.post('/plans', json={**BRIEF, 'city': 'Atlantis'}).json()
    assert plan['vendors'] == []
    assert plan['review']['status'] == 'needs_revision'

def test_live_mode_requires_configuration(client, monkeypatch):
    monkeypatch.setenv('CONVENE_MODE', 'live')
    for key in ('OPENAI_API_KEY', 'PINECONE_API_KEY', 'PINECONE_INDEX'):
        monkeypatch.delenv(key, raising=False)
    response = client.post('/plans', json=BRIEF)
    assert response.status_code == 503
    assert 'Live mode requires' in response.json()['detail']

def test_persists_across_app_instances(tmp_path, monkeypatch):
    monkeypatch.setenv('CONVENE_MODE', 'demo')
    monkeypatch.setenv('LANGSMITH_TRACING', 'false')
    path = str(tmp_path / 'persistent.db')
    first = TestClient(create_app(path)).post('/plans', json=BRIEF).json()
    assert TestClient(create_app(path)).get('/plans/' + first['id']).json() == first
