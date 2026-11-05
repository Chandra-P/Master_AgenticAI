from fastapi.testclient import TestClient
from tagalong.app import create_app
from tagalong.core import Actor, MemoryRepository


def setup():
    repo=MemoryRepository()
    repo.state['app_admins']={'admin':{'granted_by':'bootstrap'}}
    c=TestClient(create_app(repo,lambda t:Actor(t,t+'@test.com',t)))
    return repo,c,{'Authorization':'Bearer admin','X-Workspace-Mode':'admin'},{'Authorization':'Bearer member'}


def make(c,who):
    return c.post('/v1/plans',headers=who,json={'title':'Private content','kind':'outing','start':'2026-11-21','end':'2026-11-21'}).json()


def test_admin_separate_from_membership_and_cannot_be_self_granted():
    repo,c,admin,member=setup()
    assert c.get('/v1/admin/overview').status_code==401
    assert c.get('/v1/admin/overview',headers=member).status_code==403
    assert not c.get('/v1/me',headers=member).json()['app_admin']
    assert c.get('/v1/me',headers=admin).json()['app_admin']
    p=make(c,member)
    assert c.get('/v1/plans/'+p['id'],headers=admin).status_code==404
    assert c.post('/v1/admin/plans/'+p['id']+'/inspect',headers=member,json={'reason':'Trying private access'}).status_code==403
    assert c.patch('/v1/plans/'+p['id'],headers=member,json={'expected_revision':1,'patches':[{'op':'add','path':['app_admins'],'value':{'member':True}}]}).status_code==403
    overview=c.get('/v1/admin/overview',headers=admin).json()
    assert 'messages' not in overview['plans'][0]
    assert c.post('/v1/admin/plans/'+p['id']+'/inspect',headers=admin,json={'reason':'  '}).status_code==422
    response=c.post('/v1/admin/plans/'+p['id']+'/inspect',headers=admin,json={'reason':'Investigate reported issue'})
    assert response.status_code==200
    assert repo.state['admin_audit'][-1]['action']=='inspect_plan'
    assert repo.state['admin_audit'][-1]['target']==p['id']
    assert c.get('/v1/plans/'+p['id'],headers=admin).status_code==404
    # Admin may also participate normally without changing authority.
    own=make(c,admin)
    assert own['role']=='owner'
    repo.state['members'][p['id']].append('admin')
    assert c.get('/v1/plans/'+p['id'],headers=admin).json()['role']=='member'


def test_profile_metadata_cannot_grant_admin():
    from tagalong.core import identity
    actor=identity({'id':'ordinary','email':'person@test.com','user_metadata':{'app_admin':True,'role':'admin','display_name':'Admin'}})
    repo=MemoryRepository();c=TestClient(create_app(repo,lambda t:actor))
    assert c.get('/v1/me',headers={'Authorization':'Bearer token'}).json()['app_admin'] is False
    assert c.get('/v1/admin/overview',headers={'Authorization':'Bearer token'}).status_code==403


def test_suspension_is_audited_and_blocks_existing_sessions():
    repo,c,admin,member=setup();p=make(c,member)
    path='/v1/admin/accounts/member/suspension'
    payload={'suspended':True,'reason':'Test suspension and restore'}
    assert c.post(path,headers=member,json=payload).status_code==403
    assert c.post(path,headers=admin,json=payload).status_code==200
    assert c.get('/v1/me',headers=member).status_code==403
    assert c.patch('/v1/plans/'+p['id'],headers=member,json={'expected_revision':1,'patches':[{'op':'replace','path':['title'],'value':'Change'}]}).status_code==403
    assert c.post('/v1/admin/accounts/admin/suspension',headers=admin,json=payload).status_code==409
    payload['suspended']=False
    assert c.post(path,headers=admin,json=payload).status_code==200
    assert c.get('/v1/me',headers=member).status_code==200
    assert [x['action'] for x in repo.state['admin_audit']]==['suspend_account','restore_account']


def test_qa_plans_persist_without_duplicate_runs_or_cross_plan_leaks():
    repo,c,admin,member=setup()
    first=c.post('/v1/admin/qa-plans',headers=admin,json={})
    assert first.status_code==200
    ids=first.json()['plan_ids'];assert len(ids)==3
    assert c.post('/v1/admin/qa-plans',headers=admin,json={}).json()['plan_ids']==ids
    assert c.post('/v1/admin/qa-plans',headers=member,json={}).status_code==403
    plans=[c.get('/v1/plans/'+pid,headers=admin).json() for pid in ids]
    assert len({p['budget'] for p in plans})==3
    assert all(p['title'].startswith('[QA Review]') and p['role']=='owner' for p in plans)
    for pid in ids:
        assert c.get('/v1/plans/'+pid,headers=member).status_code==404
        assert len(c.get('/v1/plans/'+pid+'/documents',headers=admin).json())==1
    assert len(repo.state['plans'])==3
