import copy
import pytest
from fastapi.testclient import TestClient
from tagalong.app import create_app
from tagalong.core import MemoryRepository, Actor
from tagalong.worker import process_one

class FakeAI:
    def __init__(self): self.matches=[]; self.sources=[]; self.fail=False; self.indexed=[]
    def retrieve(self,pid,message): return self.matches
    def answer(self,plan,message,resolve_sources):
        sources=resolve_sources(self.matches) if any(w in message.lower() for w in ('earlier','history','document','remember','said','discussed')) else []
        if self.fail: raise RuntimeError('secret')
        self.sources=sources
        return {'text':'Evidence considered','preferences':['Vegetarian'],'source_ids':[s['id'] for s in sources]},sources
    def upsert(self,s): self.indexed.append(s)
    def delete(self,s): self.indexed.append(s)

@pytest.fixture
def env():
    repo=MemoryRepository(); ai=FakeAI()
    c=TestClient(create_app(repo,lambda t:Actor(t,t+'@test.com',t),ai))
    a={'Authorization':'Bearer alice'}; b={'Authorization':'Bearer bob'}
    p=c.post('/v1/plans',headers=a,json={'title':'Trip','kind':'trip','start':'x','end':'y'}).json()
    return c,repo,ai,a,b,p

def share(env):
    c,r,ai,a,b,p=env
    c.get('/v1/me',headers=b)
    assert c.post('/v1/plans/'+p['id']+'/members',headers=a,json={'email':'bob@test.com'}).status_code==200
    return c.get('/v1/plans/'+p['id'],headers=a).json()

def test_sharing_and_identity(env):
    c,r,ai,a,b,p=env; p=share(env); url='/v1/plans/'+p['id']
    assert c.get(url,headers=b).json()['role']=='member'
    assert c.post(url+'/members',headers=b,json={'email':'alice@test.com'}).status_code==403
    p['messages'].append({'id':'fake','author':'alice','user_id':'alice','text':'Forged','time':'now'})
    assert c.put(url,headers=b,json={'plan':p,'expected_revision':p['revision']}).status_code==403
    p['messages']=[]; p['members']=[]
    assert c.put(url,headers=a,json={'plan':p,'expected_revision':p['revision']}).status_code==403

def test_vote_replacement_and_other_votes(env):
    c,r,ai,a,b,p=env; p=share(env); url='/v1/plans/'+p['id']
    p['polls']=[{'id':'poll','question':'Q','options':['A','B'],'votes':{'alice':0}}]
    p=c.put(url,headers=a,json={'plan':p,'expected_revision':p['revision']}).json()
    p['polls'][0]['votes']['alice']=1
    p=c.put(url,headers=a,json={'plan':p,'expected_revision':p['revision']}).json()
    assert p['polls'][0]['votes']=={'alice':1}
    p['polls'][0]['votes']={'bob':0}
    assert c.put(url,headers=b,json={'plan':p,'expected_revision':p['revision']}).status_code==403

def test_proposals_confirm_and_protected_snapshot(env):
    c,r,ai,a,b,p=env; url='/v1/plans/'+p['id']
    out=c.post(url+'/assistant',headers=a,json={'message':'Food?'}).json()
    assert out['preferences']==[{'label':'Vegetarian','confirmed':False}]
    p=c.get(url,headers=a).json(); assert p['preferences']==[{'label':'Vegetarian','confirmed':False}]
    proposal=out['proposal_ids'][0]
    assert c.post(url+'/proposals/'+proposal+'/confirm',headers=b,json={}).status_code==404
    p=c.post(url+'/proposals/'+proposal+'/confirm',headers=a,json={}).json()
    assert p['preferences']==[{'label':'Vegetarian','confirmed':True}]
    p['messages'][1]['text']='Tampered'
    assert c.put(url,headers=a,json={'plan':p,'expected_revision':p['revision']}).status_code==403

def test_evidence_stale_and_namespace(env):
    c,r,ai,a,b,p=env; url='/v1/plans/'+p['id']
    doc=c.post(url+'/documents',headers=a,json={'title':'Notes','text':'Private evidence'}).json()
    ai.matches=[{'id':doc['id'],'version':1},{'id':'foreign','version':1}]
    out=c.post(url+'/assistant',headers=a,json={'message':'document history'}).json()
    assert len(out['sources'])==1
    assert c.delete(url+'/documents/'+doc['id'],headers=a).status_code==200
    assert c.post(url+'/assistant',headers=a,json={'message':'document history'}).json()['sources']==[]
    ai.fail=True
    response=c.post(url+'/assistant',headers=a,json={'message':'Help'})
    assert response.status_code==502 and 'secret' not in response.text

def test_jobs_retries_and_delete(env):
    c,r,ai,a,b,p=env; url='/v1/plans/'+p['id']
    d=c.post(url+'/documents',headers=a,json={'title':'Doc','text':'Text'}).json()
    assert process_one(r,ai,lambda:1000)
    assert ai.indexed[0]['id']==d['id']
    c.delete(url+'/documents/'+d['id'],headers=a)
    assert process_one(r,ai,lambda:1001)
    assert ai.indexed[-1]['deleted']
    class Broken:
        def upsert(self,s): raise ValueError('secret')
    c.post(url+'/documents',headers=a,json={'title':'Fail','text':'Text'})
    process_one(r,Broken(),lambda:2000)
    assert any(j['status']=='pending' and j['attempts']==1 for j in r.state['jobs'].values())

def test_invalid_snapshot_is_client_error(env):
    c,r,ai,a,b,p=env; p['messages']=[{'id':'x','author':'alice','user_id':'alice','text':'ok','time':'now'}]
    p['polls']=[{'id':'p','votes':[],'options':['x']}]
    assert c.put('/v1/plans/'+p['id'],headers=a,json={'plan':p,'expected_revision':1}).status_code==422

def test_missing_configuration_never_simulates_success():
    c=TestClient(create_app(repo=MemoryRepository(),authenticate=None))
    assert c.get('/v1/plans',headers={'Authorization':'Bearer anything'}).status_code==503


def test_supabase_auth_verifies_remotely(monkeypatch):
    import httpx
    from tagalong.providers import SupabaseAuth
    calls=[]
    def request(url,**kw):
        calls.append((url,kw))
        return httpx.Response(401,request=httpx.Request('GET',url))
    monkeypatch.setattr(httpx,'get',request)
    c=TestClient(create_app(MemoryRepository(),SupabaseAuth('https://example.test','private-key')))
    r=c.get('/v1/me',headers={'Authorization':'Bearer forged.jwt.token'})
    assert r.status_code==401
    assert calls[0][0].endswith('/auth/v1/user')
    assert calls[0][1]['timeout']==10
    assert 'private-key' not in r.text


def test_inflight_source_job_prevents_competing_lease(env):
    c,r,ai,a,b,p=env
    d=c.post('/v1/plans/'+p['id']+'/documents',headers=a,json={'title':'Doc','text':'one'}).json()
    from tagalong.core import source
    first=next(iter(r.state['jobs'].values())); first['status']='running'; first['lease_until']=10000
    r.transact(lambda s:source(s,p['id'],d['id'],'Doc','two'))
    assert process_one(r,ai,lambda:1000) is False

def test_pending_preferences_and_single_user_message(env):
    c,r,ai,a,b,p=env; url='/v1/plans/'+p['id']
    p['messages']=[{'id':'user-1','author':'alice','user_id':'alice','text':'Food?','time':'now'}]
    p=c.put(url,headers=a,json={'plan':p,'expected_revision':p['revision']}).json()
    out=c.post(url+'/assistant',headers=a,json={'message':'Food?'}).json()
    p=c.get(url,headers=a).json()
    assert sum(m['text']=='Food?' for m in p['messages'])==1
    assert p['preferences']==[{'label':'Vegetarian','confirmed':False}]
    p['budget']=100
    saved=c.put(url,headers=a,json={'plan':p,'expected_revision':p['revision']})
    assert saved.status_code==200
    p=c.post(url+'/proposals/'+out['proposal_ids'][0]+'/confirm',headers=a,json={}).json()
    assert p['preferences']==[{'label':'Vegetarian','confirmed':True}]


def test_budget_and_role_are_authoritative(env):
    c,r,ai,a,b,p=env; p=share(env); url='/v1/plans/'+p['id']
    p['budget']=-10
    assert c.put(url,headers=b,json={'plan':p,'expected_revision':p['revision']}).status_code==422
    p['budget']=200; p['role']='owner'
    assert c.put(url,headers=b,json={'plan':p,'expected_revision':p['revision']}).status_code==403


def test_langgraph_routes_exact_facts_without_retrieval():
    from tagalong.providers import ConnectedAI
    ai=ConnectedAI.__new__(ConnectedAI)
    calls=[]
    ai.retrieve=lambda pid,message: calls.append(pid) or [{'id':'source','version':1}]
    ai.generate=lambda s:{'output':{'text':'Budget is 100','preferences':[],'source_ids':[]}}
    ai.graph=ai.build_graph()
    resolve=lambda matches:[{'id':'source','text':'Verified'}]
    output,sources=ai.answer({'id':'plan','budget':100},'What is our budget?',resolve)
    assert calls==[] and sources==[]
    output,sources=ai.answer({'id':'plan','budget':100},'What did the document say?',resolve)
    assert calls==['plan'] and sources[0]['id']=='source'


def test_assistant_request_budget(env):
    c,r,ai,a,b,p=env; url='/v1/plans/'+p['id']+'/assistant'
    for _ in range(10): assert c.post(url,headers=a,json={'message':'Food'}).status_code==200
    assert c.post(url,headers=a,json={'message':'Food'}).status_code==429
