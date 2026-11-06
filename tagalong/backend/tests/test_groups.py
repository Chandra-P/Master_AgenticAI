import copy
import pytest
from fastapi.testclient import TestClient
from tagalong.app import create_app
from tagalong.core import Actor, MemoryRepository

A={'Authorization':'Bearer alice'}
B={'Authorization':'Bearer bob'}

@pytest.fixture
def env():
    repo=MemoryRepository()
    client=TestClient(create_app(repo,lambda token:Actor(token,token+'@example.test',token,token.title())))
    return client,repo


def body(name='Sunday supper · Our circle',owner='alice'):
    return {'name':name,'theme':'Sunday supper','members':[
        {'id':owner,'preferredName':owner.title(),'color':'#edc6b3'},
        {'id':'contact','preferredName':'River','color':'#c6d5c4','email':'private@example.test','firstName':'Private','lastName':'Adult'}]}


def create(client):
    response=client.post('/v1/groups',headers=A,json=body())
    assert response.status_code==200,response.text
    return response.json()


def test_owner_isolation_and_persistence(env):
    c,r=env
    assert c.get('/v1/groups').status_code==401
    g=create(c)
    assert g['ownerId']=='alice' and g['revision']==1
    assert TestClient(c.app).get('/v1/groups',headers=A).json()==[g]
    assert c.get('/v1/groups',headers=B).json()==[]
    assert c.get('/v1/groups/'+g['id'],headers=B).status_code==404
    edit={**body(),'expected_revision':1,'archived':False}
    assert c.patch('/v1/groups/'+g['id'],headers=B,json=edit).status_code==404
    assert c.request('DELETE','/v1/groups/'+g['id'],headers=B,json={'expected_revision':1}).status_code==404
    assert c.post('/v1/groups',headers=A,json={**body(),'ownerId':'bob'}).status_code==422
    assert c.post('/v1/groups',headers=A,json=body('Other circle',owner='bob')).status_code==422
    assert c.post('/v1/groups',headers=B,json=body(owner='bob')).status_code==200
    assert 'private@example.test' not in str(r.state['group_events'])
    r.state['suspended_users']={'alice':True}
    assert c.get('/v1/groups',headers=A).status_code==403


def test_validation_and_revision_guard(env):
    c,r=env;g=create(c);url='/v1/groups/'+g['id']
    assert c.post('/v1/groups',headers=A,json=body(' SUNDAY   supper · Our circle ')).status_code==409
    edit={**body(),'expected_revision':1,'archived':True}
    g=c.patch(url,headers=A,json=edit).json();assert g['archived'] and g['revision']==2
    assert c.patch(url,headers=A,json=edit).status_code==409
    assert c.request('DELETE',url,headers=A,json={'expected_revision':1}).status_code==409
    for change in ({'theme':' '},{'name':' '},{'members':[]},{'members':body()['members']*7}):
        assert c.post('/v1/groups',headers=A,json={**body('Different'),**change}).status_code==422
    for field,value in [('email','invalid'),('preferredName','alice')]:
        invalid=body('Different');invalid['members'][1][field]=value
        assert c.post('/v1/groups',headers=A,json=invalid).status_code==422
    assert c.request('DELETE',url,headers=A,json={'expected_revision':2}).status_code==200
    assert c.get('/v1/groups',headers=A).json()==[]
    assert c.get(url,headers=A).status_code==404


def test_plan_snapshot_does_not_grant_access_or_leak_contacts(env):
    c,r=env;g=create(c)
    data={'title':'Group supper','kind':'outing','start':'2027-05-14','end':'2027-05-14','group_id':g['id'],'expected_group_revision':1}
    assert c.post('/v1/plans',headers=B,json=data).status_code==404
    p=c.post('/v1/plans',headers=A,json=data).json()
    assert p['group']['participants']==['Alice','River']
    assert 'private@example.test' not in str(p) and 'Private' not in str(p)
    assert len(p['members'])==1 and r.state['members'][p['id']]==['alice']
    assert c.get('/v1/plans/'+p['id'],headers=B).status_code==404
    forged=copy.deepcopy(p);forged['group']['participants'].append('Fake')
    assert c.put('/v1/plans/'+p['id'],headers=A,json={'plan':forged,'expected_revision':p['revision']}).status_code==403
    assert c.patch('/v1/plans/'+p['id'],headers=A,json={'patches':[{'op':'remove','path':['group']}],'expected_revision':p['revision']}).status_code==403
    c.request('DELETE','/v1/groups/'+g['id'],headers=A,json={'expected_revision':1})
    assert c.get('/v1/plans/'+p['id'],headers=A).json()==p
    assert c.put('/v1/plans/'+p['id'],headers=A,json={'plan':p,'expected_revision':p['revision']}).status_code==200
    assert c.get('/v1/me',headers=B).status_code==200
    assert c.post('/v1/plans/'+p['id']+'/members',headers=A,json={'email':'bob@example.test'}).status_code==200
    assert c.get('/v1/plans/'+p['id'],headers=B).status_code==200


def test_plan_rejects_missing_revision_archived_or_stale_group(env):
    c,r=env;g=create(c)
    data={'title':'Supper','kind':'outing','start':'2027-05-14','end':'2027-05-14','group_id':g['id']}
    assert c.post('/v1/plans',headers=A,json=data).status_code==422
    assert c.post('/v1/plans',headers=A,json={**data,'expected_group_revision':True}).status_code==422
    c.patch('/v1/groups/'+g['id'],headers=A,json={**body(),'expected_revision':1,'archived':True})
    for revision in (1,2):
        assert c.post('/v1/plans',headers=A,json={**data,'expected_group_revision':revision}).status_code==409
    assert r.state['plans']=={}


def test_generated_draft_retains_group_snapshot(env):
    from tests.http_fixture import app_factory
    c=TestClient(app_factory());a={'Authorization':'Bearer test-alice'}
    g=c.post('/v1/groups',headers=a,json={**body(),'members':[{'id':'alice','preferredName':'alice','color':'#fff'}]}).json()
    from datetime import datetime,timezone
    d=c.post('/v1/plans/generate',headers=a,json={'prompt':'A relaxed weekend','local_date':datetime.now(timezone.utc).date().isoformat()}).json()
    data={'draft_id':d['draft_id'],'title':'Reviewed supper','kind':'outing','location':'Austin','start':'2027-05-14','end':'2027-05-14','group_id':g['id'],'expected_group_revision':1}
    response=c.post('/v1/plans/from-draft',headers=a,json=data)
    assert response.status_code==200,response.text
    p=response.json();assert p['group']['id']==g['id'] and len(p['members'])==1
    assert c.post('/v1/plans/from-draft',headers=a,json=data).json()['id']==p['id']
