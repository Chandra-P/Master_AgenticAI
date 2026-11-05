from concurrent.futures import ThreadPoolExecutor
import hashlib
from fastapi.testclient import TestClient
from tagalong.app import create_app
from tagalong.core import Actor, MemoryRepository


def setup():
    repo = MemoryRepository()
    client = TestClient(create_app(repo=repo, authenticate=lambda t: Actor(t, t+'@test.com', t)))
    owner = {'Authorization': 'Bearer owner'}
    plan = client.post('/v1/plans', headers=owner, json={'title':'Private weekend','kind':'trip','start':'2026-11-05','end':'2026-11-07','participants':''}).json()
    return repo, client, owner, plan['id']


def test_link_authorization_and_explicit_join():
    repo, c, owner, pid = setup()
    path = '/v1/plans/'+pid+'/invitation'
    assert c.post(path).status_code == 401
    assert c.post(path, headers={'Authorization':'Bearer stranger'}).status_code == 404
    link = c.post(path, headers=owner).json()
    token = link['token']
    assert len(token) >= 43
    assert token not in str(repo.state)
    assert hashlib.sha256(token.encode()).hexdigest() in str(repo.state)
    assert c.post('/v1/invitations/accept', json={'token':token}).status_code == 401
    member = {'Authorization':'Bearer recipient'}
    assert c.get('/v1/plans/'+pid, headers=member).status_code == 404
    for _ in range(2):
        assert c.post('/v1/invitations/accept',headers=member,json={'token':token}).json() == {'plan_id':pid}
    shared = c.get('/v1/plans/'+pid,headers=member).json()
    assert shared['role'] == 'member'
    assert len(shared['members']) == 2
    assert 'invitations' not in shared
    assert c.post(path,headers=member).status_code == 403
    assert c.delete(path,headers=member).status_code == 403


def test_replacement_expiry_revocation_and_validation():
    repo,c,owner,pid = setup()
    path = '/v1/plans/'+pid+'/invitation'
    first = c.post(path,headers=owner).json()['token']
    second = c.post(path,headers=owner).json()['token']
    accept=lambda t:c.post('/v1/invitations/accept',headers={'Authorization':'Bearer recipient'},json={'token':t})
    assert accept(first).status_code == 404
    repo.state['invitations'][pid]['expires_at'] = 0
    assert accept(second).status_code == 404
    third=c.post(path,headers=owner).json()['token']
    assert c.delete(path,headers=owner).status_code == 200
    assert accept(third).status_code == 404
    assert accept('x').status_code == 422
    assert accept('x'*1000).status_code == 422


def test_concurrent_join_and_member_limit():
    repo,c,owner,pid=setup()
    token=c.post('/v1/plans/'+pid+'/invitation',headers=owner).json()['token']
    def join(_):
        return c.post('/v1/invitations/accept',headers={'Authorization':'Bearer recipient'},json={'token':token}).status_code
    with ThreadPoolExecutor(max_workers=4) as pool:
        assert list(pool.map(join, range(4))) == [200]*4
    assert repo.state['members'][pid].count('recipient') == 1
    from tagalong.models import MAX_MEMBERS
    repo.state['members'][pid]=['owner']+[str(n) for n in range(MAX_MEMBERS-1)]
    assert join(0) == 409


def test_acceptance_rate_limit():
    _,c,owner,_=setup()
    for _ in range(20):
        assert c.post('/v1/invitations/accept',headers=owner,json={'token':'x'*43}).status_code == 404
    assert c.post('/v1/invitations/accept',headers=owner,json={'token':'x'*43}).status_code == 429


def test_preferred_name_is_display_only():
    from tagalong.core import identity, view
    original=identity({'id':'real-account','email':'person@test.com'})
    actor=identity({'id':'real-account','email':'person@test.com','user_metadata':{'display_name':'  Sam  '}})
    assert actor.name == original.name
    assert actor.display_name == 'Sam'
    repo,c,owner,pid=setup()
    token=c.post('/v1/plans/'+pid+'/invitation',headers=owner).json()['token']
    from tagalong.invitations import accept
    accept(repo.state,token,actor)
    projected=view(repo.state,repo.state['plans'][pid],actor)
    assert projected['members'][-1]['name']=='Sam'
    assert projected['members'][-1]['user_id']=='real-account'
