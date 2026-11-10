import copy
from dataclasses import replace
import pytest
from fastapi.testclient import TestClient
from tagalong.app import create_app
from tagalong.core import Actor, MemoryRepository, identity
from tests.test_groups import body

A={'Authorization':'Bearer alice'}
B={'Authorization':'Bearer bob'}
C={'Authorization':'Bearer carol'}


@pytest.fixture
def env():
    repo=MemoryRepository()
    accounts={name:Actor(name,name+'@example.test',name,name.title(),email_verified=True)
              for name in ('alice','bob','carol')}
    c=TestClient(create_app(repo,accounts.__getitem__))
    draft=body()
    draft['members'][1]['email']=' BOB@EXAMPLE.TEST '
    draft['members'].append({'id':'carol','preferredName':'Carol','color':'#fff'})
    g=c.post('/v1/groups',headers=A,json=draft).json()
    return c,repo,accounts,g,draft


def share(c,g,shared=True,headers=None):
    return c.post('/v1/groups/'+g['id']+'/sharing',headers=headers or A,
                  json={'shared':shared,'expected_revision':g['revision']})


def test_explicit_sharing_redacts_contacts_and_never_grants_plan_access(env):
    c,r,accounts,g,draft=env
    url='/v1/groups/'+g['id']
    assert not g['shared'] and g['role']=='owner'
    assert c.get('/v1/groups',headers=B).json()==[]
    assert c.get(url,headers=B).status_code==404
    shared=share(c,g).json()
    assert shared['shared'] and shared['revision']==2
    view=c.get(url,headers=B).json()
    assert c.get('/v1/groups',headers=B).json()==[view]
    assert view['role']=='member' and view['ownerName']=='Alice'
    assert view['members'][1]=={'id':'contact','preferredName':'River','color':'#c6d5c4'}
    assert 'email' not in str(view) and 'firstName' not in str(view) and 'lastName' not in str(view)
    assert c.get(url,headers=A).json()['members'][1]['firstName']=='Private'
    assert c.get(url,headers=C).status_code==404  # An alias/roster ID is not identity.
    plan={'title':'Private plan','kind':'outing','start':'2027-05-14','end':'2027-05-14',
          'group_id':g['id'],'expected_group_revision':2}
    p=c.post('/v1/plans',headers=A,json=plan).json()
    assert c.get('/v1/plans/'+p['id'],headers=B).status_code==404
    assert c.post('/v1/plans',headers=B,json=plan).status_code==404
    assert c.get('/v1/plans',headers=B).json()==[]
    assert c.patch(url,headers=B,json={**draft,'archived':False,'expected_revision':2}).status_code==404
    assert share(c,shared,False,B).status_code==404
    assert c.request('DELETE',url,headers=B,json={'expected_revision':2}).status_code==404
    assert 'BOB@EXAMPLE.TEST' not in str(r.state['group_events'])


def test_sharing_requires_trusted_verified_email_each_request(env):
    c,r,accounts,g,draft=env
    share(c,g)
    url='/v1/groups/'+g['id']
    accounts['bob']=replace(accounts['bob'],email_verified=False)
    assert c.get(url,headers=B).status_code==404
    accounts['bob']=replace(accounts['bob'],email_verified=True,email='other@example.test')
    assert c.get('/v1/groups',headers=B).json()==[]
    accounts['bob']=replace(accounts['bob'],email='bob@example.test')
    assert c.get(url,headers=B).status_code==200
    r.state['suspended_users']={'bob':True}
    assert c.get(url,headers=B).status_code==403


def test_revocation_roster_changes_and_stale_approval(env):
    c,r,accounts,g,draft=env
    url='/v1/groups/'+g['id']
    shared=share(c,g).json()
    assert share(c,g,False).status_code==409
    private=share(c,shared,False).json()
    assert c.get(url,headers=B).status_code==404
    shared=share(c,private).json()
    changed=copy.deepcopy(draft)
    changed['members'][1]['email']='carol@example.test'
    updated=c.patch(url,headers=A,json={**changed,'archived':False,'expected_revision':shared['revision']}).json()
    assert updated['shared']
    assert c.get(url,headers=B).status_code==404
    assert c.get(url,headers=C).status_code==200
    archived=c.patch(url,headers=A,json={**changed,'archived':True,'expected_revision':updated['revision']}).json()
    assert c.get(url,headers=C).json()['archived']
    assert c.request('DELETE',url,headers=A,json={'expected_revision':archived['revision']}).status_code==200
    assert c.get(url,headers=C).status_code==404


def test_legacy_group_stays_private_and_sharing_validates_owner_and_revision(env):
    c,r,accounts,g,draft=env
    r.state['groups'][g['id']].pop('shared')
    assert c.get('/v1/groups',headers=B).json()==[]
    assert share(c,g,headers=B).status_code==404
    url='/v1/groups/'+g['id']+'/sharing'
    assert c.post(url,json={'shared':True,'expected_revision':1}).status_code==401
    assert c.post(url,headers=A,json={'shared':'true','expected_revision':1}).status_code==422
    assert c.post(url,headers=A,json={'shared':True,'expected_revision':True}).status_code==422
    assert share(c,g).status_code==200


def test_identity_trusts_only_provider_confirmation_not_editable_metadata():
    data={'id':'bob','email':'bob@example.test','user_metadata':{'email_verified':True,'email_confirmed_at':'fake'}}
    assert not identity(data).email_verified
    assert not identity({**data,'confirmed_at':'2026-01-01T00:00:00Z'}).email_verified
    assert identity({**data,'email_confirmed_at':'2026-01-01T00:00:00Z'}).email_verified
    assert not identity({**data,'email':'','email_confirmed_at':'2026-01-01T00:00:00Z'}).email_verified
