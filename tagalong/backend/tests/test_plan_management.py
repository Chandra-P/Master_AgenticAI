from fastapi.testclient import TestClient
from tagalong.app import create_app
from tagalong.core import Actor, MemoryRepository


def setup():
    repo=MemoryRepository();c=TestClient(create_app(repo,lambda t:Actor(t,t+'@test.com',t)))
    owner={'Authorization':'Bearer alice'};member={'Authorization':'Bearer bob'}
    plan=c.post('/v1/plans',headers=owner,json={'title':'Owned plan','kind':'outing','start':'2026-12-12','end':'2026-12-12'}).json()
    c.get('/v1/me',headers=member)
    c.post('/v1/plans/'+plan['id']+'/members',headers=owner,json={'email':'bob@test.com'})
    return repo,c,owner,member,c.get('/v1/plans/'+plan['id'],headers=owner).json()


def test_transfer_only_to_existing_active_member_and_old_owner_loses_authority():
    repo,c,owner,member,p=setup();url='/v1/plans/'+p['id']+'/owner'
    payload={'user_id':'bob','expected_revision':p['revision']}
    assert c.post(url,headers=member,json=payload).status_code==403
    assert c.post(url,headers=owner,json={**payload,'user_id':'stranger'}).status_code==422
    assert c.post(url,headers=owner,json={**payload,'expected_revision':0}).status_code in (409,422)
    repo.state['suspended_users']={'bob':True}
    assert c.post(url,headers=owner,json=payload).status_code==409
    repo.state['suspended_users']={}
    result=c.post(url,headers=owner,json=payload)
    assert result.status_code==200 and result.json()['role']=='member'
    assert c.get('/v1/plans/'+p['id'],headers=member).json()['role']=='owner'
    assert c.post('/v1/plans/'+p['id']+'/invitation',headers=owner).status_code==403
    assert repo.state['plan_events'][-1]['action']=='transfer_owner'


def test_delete_requires_owner_revision_and_exact_confirmation_and_revokes_links():
    repo,c,owner,member,p=setup();url='/v1/plans/'+p['id']
    token=c.post(url+'/invitation',headers=owner).json()['token']
    doc=c.post(url+'/documents',headers=owner,json={'title':'Source','text':'Review only'}).json()
    payload={'confirmation':p['title'],'expected_revision':p['revision']}
    assert c.request('DELETE',url,headers=member,json=payload).status_code==403
    assert c.request('DELETE',url,headers=owner,json={**payload,'confirmation':'wrong'}).status_code==422
    assert c.request('DELETE',url,headers=owner,json={**payload,'expected_revision':1}).status_code==409
    assert c.request('DELETE',url,headers=owner,json=payload).status_code==200
    assert c.request('DELETE',url,headers=owner,json=payload).status_code==200
    for headers in (owner,member):
        assert c.get(url,headers=headers).status_code==404
        assert c.get(url+'/documents',headers=headers).status_code==404
        assert c.get('/v1/plans',headers=headers).json()==[]
    assert repo.state['sources'][p['id']+':'+doc['id']]['deleted'] is True
    assert c.post('/v1/invitations/accept',headers=member,json={'token':token}).status_code==404
    assert repo.state['plans'][p['id']]['messages']==[]  # Retained record, not permanent erasure.


def test_admin_only_qa_plan_cannot_be_orphaned_by_transfer_to_nonadmin():
    repo,c,owner,member,p=setup()
    repo.state['qa_runs']={'alice':{'plan_ids':[p['id']]}}
    repo.state['app_admins']={'alice':{}}
    admin={**owner,'X-Workspace-Mode':'admin'}
    payload={'expected_revision':p['revision'],'user_id':'bob'}
    assert c.post('/v1/plans/'+p['id']+'/owner',headers=admin,json=payload).status_code==422
    repo.state['app_admins']['bob']={}
    assert c.post('/v1/plans/'+p['id']+'/owner',headers=admin,json=payload).status_code==200
    assert c.get('/v1/plans/'+p['id'],headers={**member,'X-Workspace-Mode':'admin'}).json()['role']=='owner'
