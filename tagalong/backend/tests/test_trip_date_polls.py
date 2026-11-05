import pytest
from fastapi.testclient import TestClient
from tagalong.app import create_app
from tagalong.core import Actor, MemoryRepository


@pytest.mark.parametrize('start,end,options', [
    ('2026-12-12', '2026-12-14', ['Dec 12 - Dec 14', 'Suggest another date range']),
    ('2026-12-31', '2027-01-02', ['Dec 31, 2026 - Jan 2, 2027', 'Suggest another date range']),
    ('2026-12-12', '2026-12-12', ['Dec 12', 'Suggest another date']),
])
def test_date_poll_offers_the_complete_planned_dates(start, end, options):
    client = TestClient(create_app(MemoryRepository(), lambda token: Actor('alice', 'alice@test.com', 'Alice')))
    response = client.post('/v1/plans', headers={'Authorization': 'Bearer alice'}, json={
        'title': 'Winter trip', 'kind': 'trip', 'start': start, 'end': end,
    })
    assert response.status_code == 200
    poll = response.json()['polls'][0]
    assert poll['options'] == options
    assert poll['question'] == ('Which date range works best?' if start != end else 'Which date works best?')
    assert poll['votes'] == {}
