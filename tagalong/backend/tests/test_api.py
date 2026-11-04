from fastapi.testclient import TestClient
from tagalong.app import create_app
from tagalong.core import MemoryRepository, Actor


def test_auth_and_isolation():
    repo = MemoryRepository()
    app = create_app(repo=repo, authenticate=lambda token: Actor(token, token+'@test.com', token))
    c = TestClient(app)
    assert c.get('/v1/plans').status_code == 401
    a = {'Authorization':'Bearer alice'}
    p = c.post('/v1/plans', headers=a, json={'title':'Weekend','kind':'trip','start':'2026-11-05','end':'2026-11-07','participants':'Bob'}).json()
    assert p['members'][0]['name'] == 'alice'
    assert c.get('/v1/plans/'+p['id'],headers={'Authorization':'Bearer bob'}).status_code == 404
    assert c.put('/v1/plans/'+p['id'],headers=a,json={'plan':p,'expected_revision':99}).status_code == 409
