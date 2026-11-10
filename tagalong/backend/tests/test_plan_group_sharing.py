from dataclasses import replace
from datetime import datetime,timezone
import pytest
from fastapi.testclient import TestClient
from tagalong.app import create_app
from tagalong.core import Actor,MemoryRepository
from tests.test_coordination import AI

A={'Authorization':'Bearer alice'};B={'Authorization':'Bearer bob'};C={'Authorization':'Bearer carol'}

@pytest.fixture
def env():
    r=MemoryRepository()
    accounts={name:Actor(name,name+'@example.test',name,name.title(),email_verified=True) for name in ('alice','bob','carol')}
    c=TestClient(create_app(r,accounts.__getitem__,AI()))
    draft={'name':'Weekend group','theme':'Weekend friends','members':[
        {'id':'alice','preferredName':'Alice','color':'#fff'},
        {'id':'roster-bob','preferredName':'Bobby','color':'#ccc','email':'BOB@example.test','firstName':'Private'},
        {'id':'roster-carol','preferredName':'Carol alias','color':'#ddd'}]}
    g=c.post('/v1/groups',headers=A,json=draft).json()
    return c,r,accounts,g,draft

def create(c,g,shared=True):
    response=c.post('/v1/plans',headers=A,json={'title':'Dinner with group','kind':'outing','start':'2027-05-14','end':'2027-05-14','group_id':g['id'],'expected_group_revision':g['revision'],'share_with_group':shared})
    assert response.status_code==200,response.text
    return response.json()

def approve(c,g,p,headers=A):
    return c.post('/v1/plans/'+p['id']+'/group-sharing',headers=headers,json={'group_id':g['id'],'expected_group_revision':g['revision'],'expected_revision':p['revision'],'share_with_group':True})

def test_creation_private_by_default_or_explicit_recipient_approval(env):
    c,r,accounts,g,draft=env
    private=create(c,g,False)
    assert c.get('/v1/plans/'+private['id'],headers=B).status_code==404
    p=create(c,g)
    assert r.state['members'][p['id']]==['alice']  # Verified identity not seen yet.
    listed=c.get('/v1/plans',headers=B).json()
    assert [x['id'] for x in listed]==[p['id']]
    assert listed[0]['role']=='member'
    assert 'BOB@example.test' not in str(listed) and 'Private' not in str(listed)
    assert c.get('/v1/plans/'+p['id'],headers=C).status_code==404
    assert c.get('/v1/plans/'+p['id']+'/group-sharing',headers=B).status_code==403
    assert c.request('DELETE','/v1/plans/'+p['id'],headers=B,json={}).status_code in (403,422)

def test_verified_current_identity_not_cached_account_or_alias(env):
    c,r,accounts,g,draft=env;p=create(c,g)
    accounts['bob']=replace(accounts['bob'],email_verified=False)
    assert c.get('/v1/plans',headers=B).json()==[]
    accounts['bob']=replace(accounts['bob'],email_verified=True,email='different@example.test')
    assert c.get('/v1/plans',headers=B).json()==[]
    accounts['bob']=replace(accounts['bob'],email='bob@example.test')
    assert len(c.get('/v1/plans',headers=B).json())==1
    assert r.state['members'][p['id']]==['alice','bob']

def test_notifications_are_durable_deduplicated_and_private(env):
    c,r,accounts,g,draft=env;p=create(c,g)
    notices=c.get('/v1/notifications',headers=B).json()
    assert len(notices)==1 and notices[0]['title']==p['title'] and not notices[0]['read']
    nid=notices[0]['id']
    for _ in range(3):assert c.get('/v1/notifications',headers=B).json()==notices
    assert len(r.state['members'][p['id']])==2
    assert c.get('/v1/notifications',headers=A).json()==[]
    assert c.post('/v1/notifications/'+nid+'/read',headers=C).status_code==404
    assert c.post('/v1/notifications/'+nid+'/read',headers=B).status_code==200
    assert TestClient(c.app).get('/v1/notifications',headers=B).json()[0]['read']
    assert c.get('/v1/notifications').status_code==401
    assert 'email' not in str(notices)

def test_existing_plan_explicit_sharing_checks_owner_and_revisions(env):
    c,r,accounts,g,draft=env;p=create(c,g,False)
    assert approve(c,g,p,headers=B).status_code==404
    assert approve(c,{**g,'revision':99},p).status_code==409
    assert approve(c,g,{**p,'revision':99}).status_code==409
    assert approve(c,g,p).status_code==200
    assert approve(c,g,p).status_code==409
    assert c.get('/v1/plans/'+p['id'],headers=B).status_code==200
    assert c.get('/v1/plans/'+p['id'],headers=A).json()['group']==p['group']

def test_pending_revocation_and_removed_member_never_silently_rejoin(env):
    c,r,accounts,g,draft=env;p=create(c,g)
    url='/v1/plans/'+p['id']
    recipients=c.get(url+'/group-sharing',headers=A).json()
    grant=recipients['recipients'][0]
    assert c.request('DELETE',url+'/group-sharing/'+grant['id'],headers=A,json={'expected_revision':p['revision']}).status_code==200
    assert c.get('/v1/plans',headers=B).json()==[]
    p=c.get(url,headers=A).json();assert approve(c,g,p).status_code==200
    assert c.get(url,headers=B).status_code==200
    assert c.delete(url+'/members/bob',headers=A).status_code==200
    for _ in range(2):
        assert c.get('/v1/plans',headers=B).json()==[]
        assert c.get('/v1/notifications',headers=B).json()==[]
    p=c.get(url,headers=A).json();assert approve(c,g,p).status_code==200
    assert c.get(url,headers=B).status_code==200

def test_old_unclaimed_grants_cannot_restore_removed_account_after_email_change(env):
    c,r,accounts,g,draft=env;p=create(c,g)
    # Bob joined through a separate channel, with an updated current account email.
    r.state['members'][p['id']].append('bob')
    r.state['plans'][p['id']]['members'].append({'user_id':'bob','name':'bob','color':'#fff'})
    assert c.delete('/v1/plans/'+p['id']+'/members/bob',headers=A).status_code==200
    assert c.get('/v1/plans',headers=B).json()==[]

def test_group_edits_do_not_expand_approved_plan_recipients(env):
    c,r,accounts,g,draft=env;p=create(c,g)
    draft['members'][1]['email']='carol@example.test'
    c.patch('/v1/groups/'+g['id'],headers=A,json={**draft,'archived':False,'expected_revision':1})
    assert c.get('/v1/plans',headers=C).json()==[]
    assert c.get('/v1/plans/'+p['id'],headers=B).status_code==200
    c.request('DELETE','/v1/groups/'+g['id'],headers=A,json={'expected_revision':2})
    assert c.get('/v1/plans/'+p['id'],headers=B).status_code==200

def test_deleted_plan_and_suspended_identity_never_redeem(env):
    c,r,accounts,g,draft=env;p=create(c,g)
    r.state['suspended_users']={'bob':True}
    assert c.get('/v1/notifications',headers=B).status_code==403
    r.state['suspended_users']={}
    assert c.request('DELETE','/v1/plans/'+p['id'],headers=A,json={'expected_revision':p['revision'],'confirmation':p['title']}).status_code==200
    assert c.get('/v1/notifications',headers=B).json()==[]
    assert c.get('/v1/plans',headers=B).json()==[]

def test_creation_rejects_sharing_without_group_and_alias_only_group(env):
    c,r,accounts,g,draft=env
    assert c.post('/v1/plans',headers=A,json={'title':'Invalid','kind':'outing','start':'2027-05-14','end':'2027-05-14','share_with_group':True}).status_code==422
    draft['members'][1].pop('email')
    c.patch('/v1/groups/'+g['id'],headers=A,json={**draft,'archived':False,'expected_revision':1})
    assert c.post('/v1/plans',headers=A,json={'title':'Invalid','kind':'outing','start':'2027-05-14','end':'2027-05-14','group_id':g['id'],'expected_group_revision':2,'share_with_group':True}).status_code==422
    assert r.state['plans']=={}

def test_generated_draft_sharing_and_retry_do_not_duplicate_or_change_approval(env):
    c,r,accounts,g,draft=env
    d=c.post('/v1/plans/generate',headers=A,json={'prompt':'Dinner with our group','local_date':datetime.now(timezone.utc).date().isoformat()}).json()
    data={'draft_id':d['draft_id'],'title':'Reviewed dinner','kind':'outing','location':'Austin','start':'2027-05-14','end':'2027-05-14','group_id':g['id'],'expected_group_revision':1,'share_with_group':True}
    result=c.post('/v1/plans/from-draft',headers=A,json=data)
    assert result.status_code==200,result.text
    p=result.json()
    assert c.post('/v1/plans/from-draft',headers=A,json=data).json()['id']==p['id']
    assert c.post('/v1/plans/from-draft',headers=A,json={**data,'share_with_group':False}).status_code==409
    assert len(c.get('/v1/notifications',headers=B).json())==1
    assert len(r.state['plans'])==1


def test_transfer_revokes_pending_approvals_but_keeps_existing_members(env):
    c,r,accounts,g,draft=env
    draft['members'][2]['email']='carol@example.test'
    g=c.patch('/v1/groups/'+g['id'],headers=A,json={**draft,'archived':False,'expected_revision':1}).json()
    p=create(c,g);assert c.get('/v1/plans/'+p['id'],headers=B).status_code==200
    p=c.get('/v1/plans/'+p['id'],headers=A).json()
    result=c.post('/v1/plans/'+p['id']+'/owner',headers=A,json={'user_id':'bob','expected_revision':p['revision']})
    assert result.status_code==200,result.text
    assert c.get('/v1/plans/'+p['id'],headers=C).status_code==404
    assert c.get('/v1/plans/'+p['id'],headers=B).json()['role']=='owner'


def test_deleted_plan_does_not_leak_notification_title_or_allow_marking(env):
    c,r,accounts,g,draft=env;p=create(c,g)
    notice=c.get('/v1/notifications',headers=B).json()[0]
    p=c.get('/v1/plans/'+p['id'],headers=A).json()
    assert c.request('DELETE','/v1/plans/'+p['id'],headers=A,json={'expected_revision':p['revision'],'confirmation':p['title']}).status_code==200
    assert c.get('/v1/notifications',headers=B).json()==[]
    assert c.post('/v1/notifications/'+notice['id']+'/read',headers=B).status_code==404


def test_member_capacity_failure_rolls_back_creation_and_private_grants(env,monkeypatch):
    c,r,accounts,g,draft=env
    monkeypatch.setattr('tagalong.plan_group_sharing.MAX_MEMBERS',1)
    result=c.post('/v1/plans',headers=A,json={'title':'Too many','kind':'outing','start':'2027-05-14','end':'2027-05-14','group_id':g['id'],'expected_group_revision':1,'share_with_group':True})
    assert result.status_code==409
    assert r.state['plans']=={} and r.state.get('plan_group_grants',{})=={}
