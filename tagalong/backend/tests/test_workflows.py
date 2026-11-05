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
    p=c.post('/v1/plans',headers=a,json={'title':'Trip','kind':'trip','start':'2026-12-04','end':'2026-12-06'}).json()
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
    assert 'AI_INTERNAL; reference ' in response.json()['detail']
    assert c.get('/health').json()['assistant_diagnostics']==1
    assert c.get('/health').json()['assistant_citation_policy']=='evidence-only'

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
    p=c.get(url,headers=b).json()
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

def test_create_validates_and_has_renderable_defaults(env):
    c,r,ai,a,b,p=env
    p=c.post('/v1/plans',headers=a,json={'title':'  Weekend away  ','kind':'trip','start':'2026-12-04','end':'2026-12-06'}).json()
    assert p['title']=='Weekend away'
    assert p['image']=='/images/coast.jpg' and p['location'] and p['date']!='2026-12-04'
    assert p['polls'][0]['datePoll'] and len(p['polls'][0]['options'])>=2
    for payload in ({'title':'   '},{'start':'not-a-date'},{'start':'2026-12-10','end':'2026-12-02'}):
        body={'title':'Test','kind':'outing','start':'2026-12-04','end':'2026-12-06',**payload}
        assert c.post('/v1/plans',headers=a,json=body).status_code==422


def test_poll_options_cannot_change_meaning_of_votes(env):
    c,r,ai,a,b,p=env; url='/v1/plans/'+p['id']
    p['polls']=[{'id':'poll','question':'Where?','options':['A','B'],'votes':{'alice':0}}]
    p=c.put(url,headers=a,json={'plan':p,'expected_revision':p['revision']}).json()
    p['polls'][0]['options']=['B','A']
    assert c.put(url,headers=a,json={'plan':p,'expected_revision':p['revision']}).status_code==409

@pytest.mark.parametrize('options',[['One'],['A','A'],['A','  '],['A','a']])
def test_invalid_poll_options(env,options):
    c,r,ai,a,b,p=env
    p['polls']=[{'id':'poll','question':'Where?','options':options,'votes':{}}]
    assert c.put('/v1/plans/'+p['id'],headers=a,json={'plan':p,'expected_revision':p['revision']}).status_code==422


def test_owner_revokes_member_read_and_rag_access(env):
    c,r,ai,a,b,p=env; p=share(env); url='/v1/plans/'+p['id']
    assert c.delete(url+'/members/alice',headers=b).status_code==403
    assert c.delete(url+'/members/alice',headers=a).status_code==409
    assert c.delete(url+'/members/bob',headers=a).status_code==200
    assert c.get(url,headers=b).status_code==404
    assert c.post(url+'/assistant',headers=b,json={'message':'document history'}).status_code==404
    assert c.get(url+'/documents',headers=b).status_code==404


def test_invalid_provider_citation_rejected(env):
    c,r,ai,a,b,p=env
    ai.answer=lambda *args:({'text':'Unsupported assertion','preferences':[],'source_ids':['invented']},[])
    assert c.post('/v1/plans/'+p['id']+'/assistant',headers=a,json={'message':'Help'}).status_code==502


def test_assistant_rejects_oversized_provider_text(env):
    c,r,ai,a,b,p=env
    ai.answer=lambda *args:({'text':'x'*20001,'preferences':[],'source_ids':[]},[])
    assert c.post('/v1/plans/'+p['id']+'/assistant',headers=a,json={'message':'Help'}).status_code==502


@pytest.mark.parametrize('field,count',[('messages',1001),('polls',101),('tasks',201),('itinerary',201)])
def test_plan_collection_limits(env,field,count):
    c,r,ai,a,b,p=env
    template={'messages':{'id':'x','author':'alice','user_id':'alice','text':'Hi','time':'now'},'polls':{'id':'p','question':'Where?','options':['A','B'],'votes':{}},'tasks':{'label':'Task','done':False},'itinerary':{'id':'a','title':'A','time':'','category':'','location':''}}[field]
    p[field]=[dict(template,id=str(i)) if field!='tasks' else template for i in range(count)]
    assert c.put('/v1/plans/'+p['id'],headers=a,json={'plan':p,'expected_revision':p['revision']}).status_code==422


def test_member_revocation_during_rag_blocks_evidence(env):
    c,r,ai,a,b,p=env; p=share(env); url='/v1/plans/'+p['id']
    def revoked_answer(plan,message,resolve_sources):
        assert c.delete(url+'/members/bob',headers=a).status_code==200
        resolve_sources([])
        pytest.fail('Revoked actor must not reach generation')
    ai.answer=revoked_answer
    assert c.post(url+'/assistant',headers=b,json={'message':'document history'}).status_code==404


def test_simultaneous_snapshots_only_one_commits(env):
    from concurrent.futures import ThreadPoolExecutor
    c,r,ai,a,b,p=env
    url='/v1/plans/'+p['id']
    def save(title):
        draft=copy.deepcopy(p); draft['title']=title
        return c.put(url,headers=a,json={'plan':draft,'expected_revision':p['revision']}).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses=list(pool.map(save,['First','Second']))
    assert sorted(statuses)==[200,409]

def test_health_requires_database_readiness():
    class Unavailable(MemoryRepository):
        def health(self): return False
    c=TestClient(create_app(Unavailable(),lambda t:Actor(t,t+'@test.com',t)))
    response=c.get('/health')
    assert response.status_code==503
    assert response.json()['status']=='unavailable'
    assert not response.json()['capabilities']['plans']


def test_embedding_dimensions_are_explicit(monkeypatch):
    from types import SimpleNamespace
    from tagalong.providers import ConnectedAI
    monkeypatch.setenv('OPENAI_EMBEDDING_DIMENSIONS','768')
    calls=[]
    ai=ConnectedAI.__new__(ConnectedAI)
    ai.client=SimpleNamespace(embeddings=SimpleNamespace(create=lambda **kwargs:calls.append(kwargs) or SimpleNamespace(data=[SimpleNamespace(embedding=[0.0])])) )
    assert ai.embedding('Text')==[0.0]
    assert calls[0]['dimensions']==768

def test_index_dimension_check_rejects_mismatch(monkeypatch):
    from types import SimpleNamespace
    from tagalong.providers import ConnectedAI
    monkeypatch.setenv('OPENAI_EMBEDDING_DIMENSIONS','768')
    ai=ConnectedAI.__new__(ConnectedAI)
    ai.index=SimpleNamespace(describe_index_stats=lambda **kwargs:SimpleNamespace(dimension=1536))
    with pytest.raises(ValueError,match='dimension'):
        ai.verify_index_dimension()


def test_generation_bounds_context_and_preserves_budget():
    import json
    from types import SimpleNamespace
    from tagalong.providers import ConnectedAI
    ai=ConnectedAI.__new__(ConnectedAI); ai.model='test-model'; calls=[]
    ai.client=SimpleNamespace(responses=SimpleNamespace(create=lambda **kw:calls.append(kw) or SimpleNamespace(output_text='{"text":"Budget is 321","preferences":[],"source_ids":[]}')))
    plan={'budget':321,'messages':[{'author':'alice','text':'x'*20000,'time':'now'} for _ in range(1000)],'polls':[],'tasks':[],'itinerary':[],'preferences':[]}
    ai.generate({'plan':plan,'message':'Budget?','sources':[]})
    sent=json.loads(calls[0]['input'])
    assert sent['plan']['budget']==321 and len(calls[0]['input'])<41000
    assert calls[0]['max_output_tokens']==2000
    assert calls[0]['store'] is False


@pytest.mark.parametrize('sources', [[],[{'id':'verified-document','title':'Notes','text':'Synthetic evidence'}],[{'id':'chat-message','title':'Verified chat','text':'Synthetic evidence'}]])
def test_generation_citation_schema_excludes_plan_and_message_ids(sources):
    from types import SimpleNamespace
    from tagalong.providers import ConnectedAI
    ai=ConnectedAI.__new__(ConnectedAI); ai.model='test-model'; calls=[]
    ai.client=SimpleNamespace(responses=SimpleNamespace(create=lambda **kw:calls.append(kw) or SimpleNamespace(output_text='{"text":"Flying is a proposal","preferences":[],"source_ids":[]}')))
    ai.generate({'plan':{'id':'private-plan','messages':[{'id':'chat-message','author':'Member','text':'I will fly instead','time':'now'}]},'message':'I will fly instead','sources':sources})
    citations=calls[0]['text']['format']['schema']['properties']['source_ids']
    if sources:
        assert citations['items']['enum']==[source['id'] for source in sources]
        assert citations['maxItems']==6
    else:
        assert citations['maxItems']==0
    assert 'plan or message IDs' in calls[0]['instructions']
    assert 'unless explicitly included in evidence' in calls[0]['instructions']

def test_document_routes_exclude_and_protect_chat_sources(env):
    c,r,ai,a,b,p=env; url='/v1/plans/'+p['id']
    p['messages']=[{'id':'chat-source','author':'alice','user_id':'alice','text':'Chat text','time':'now'}]
    assert c.put(url,headers=a,json={'plan':p,'expected_revision':p['revision']}).status_code==200
    assert c.get(url+'/documents',headers=a).json()==[]
    assert c.delete(url+'/documents/chat-source',headers=a).status_code==404
    assert not r.state['sources'][p['id']+':chat-source']['deleted']
    doc=c.post(url+'/documents',headers=a,json={'title':'Private document','text':'Document text'}).json()
    listed=c.get(url+'/documents',headers=a).json()
    assert len(listed)==1 and listed[0]['id']==doc['id']
    assert listed[0]['text']=='Document text' and listed[0]['version']==1
    assert c.delete(url+'/documents/'+doc['id'],headers=a).status_code==200
    assert r.state['sources'][p['id']+':'+doc['id']]['kind']=='document'
    assert c.get(url+'/documents',headers=a).json()==[]


def test_legacy_untyped_sources_are_not_documents(env):
    from tagalong.core import source
    c,r,ai,a,b,p=env; url='/v1/plans/'+p['id']
    r.transact(lambda s:source(s,p['id'],'legacy','Untrusted title','Legacy text'))
    r.state['sources'][p['id']+':legacy'].pop('kind',None)
    assert c.get(url+'/documents',headers=a).json()==[]
    assert c.delete(url+'/documents/legacy',headers=a).status_code==404


def test_patch_large_plan_vote_and_append_message(env):
    c,r,ai,a,b,p=env; url='/v1/plans/'+p['id']
    def seed(s):
        s['plans'][p['id']]['messages']=[{'id':'old-'+str(i),'author':'alice','user_id':'alice','text':'x'*19000,'time':'now'} for i in range(20)]
        s['plans'][p['id']]['polls']=[{'id':'poll','question':'Where?','options':['A','B'],'votes':{}}]
    r.transact(seed)
    response=c.patch(url,headers=a,json={'expected_revision':1,'patches':[{'op':'add','path':['polls',0,'votes','alice'],'value':1}]})
    assert response.status_code==200
    saved=response.json(); assert saved['polls'][0]['votes']=={'alice':1}
    assert len(saved['messages'])==20
    message={'id':'new-message','author':'alice','user_id':'alice','text':'New chat','time':'now'}
    saved=c.patch(url,headers=a,json={'expected_revision':2,'patches':[{'op':'add','path':['messages',20],'value':message}]}).json()
    assert saved['messages'][-1]==message
    assert r.state['sources'][p['id']+':new-message']['text']=='New chat'


def test_patch_access_and_revision_guards(env):
    c,r,ai,a,b,p=env; url='/v1/plans/'+p['id']
    body={'expected_revision':1,'patches':[{'op':'replace','path':['budget'],'value':100}]}
    assert c.patch(url,headers=b,json=body).status_code==404
    assert c.patch(url,headers=a,json=body).status_code==200
    assert c.patch(url,headers=a,json=body).status_code==409
    assert c.patch(url,headers=a,json={'expected_revision':2,'patches':[{'op':'replace','path':['owner_id'],'value':'bob'}]}).status_code==403


@pytest.mark.parametrize('patch',[
    {'op':'replace','path':[],'value':1},
    {'op':'replace','path':['messages',True],'value':{}},
    {'op':'add','path':['messages',-1],'value':{}},
    {'op':'add','path':['messages',1],'value':{}},
    {'op':'replace','path':['tasks',0,'missing'],'value':True},
    {'op':'add','path':['budget'],'value':3},
    {'op':'replace','path':['budget',0],'value':3},
    {'op':'replace','path':['tasks',0,'done']},
    {'op':'replace','path':['tasks',0,'done']+['x']*11,'value':True},
])
def test_patch_malformed_paths_rejected(env,patch):
    c,r,ai,a,b,p=env
    response=c.patch('/v1/plans/'+p['id'],headers=a,json={'expected_revision':1,'patches':[patch]})
    assert response.status_code==422
    assert r.state['plans'][p['id']]['revision']==1


def test_patch_cannot_edit_other_member_vote(env):
    c,r,ai,a,b,p=env; p=share(env); url='/v1/plans/'+p['id']
    p['polls']=[{'id':'poll','question':'Where?','options':['A','B'],'votes':{'alice':0}}]
    p=c.put(url,headers=a,json={'plan':p,'expected_revision':p['revision']}).json()
    response=c.patch(url,headers=b,json={'expected_revision':p['revision'],'patches':[{'op':'replace','path':['polls',0,'votes','alice'],'value':1}]})
    assert response.status_code==403

@pytest.mark.parametrize('patch',[
    {'op':'remove','path':['polls',999]},
    {'op':'replace','path':['polls','0'],'value':{}},
    {'op':'add','path':['polls',0,'votes',0],'value':1},
    {'op':'unknown','path':['title'],'value':'Test'},
    {'op':{},'path':['title'],'value':'Test'},
    {'op':'replace','path':['title'],'value':[]},
])
def test_patch_additional_malformed_data_has_no_server_error(env,patch):
    c,r,ai,a,b,p=env
    assert c.patch('/v1/plans/'+p['id'],headers=a,json={'expected_revision':1,'patches':[patch]}).status_code==422


def test_patch_operation_limit_and_boolean_revision(env):
    c,r,ai,a,b,p=env; url='/v1/plans/'+p['id']
    patch={'op':'replace','path':['budget'],'value':100}
    assert c.patch(url,headers=a,json={'expected_revision':1,'patches':[patch]*201}).status_code==422
    assert c.patch(url,headers=a,json={'expected_revision':True,'patches':[patch]}).status_code==422


def test_patch_invariant_failure_rolls_back_all_operations(env):
    c,r,ai,a,b,p=env; url='/v1/plans/'+p['id']
    message={'id':'forged','author':'bob','user_id':'bob','text':'Impersonation','time':'now'}
    patches=[{'op':'replace','path':['budget'],'value':900},{'op':'add','path':['messages',0],'value':message}]
    assert c.patch(url,headers=a,json={'expected_revision':1,'patches':patches}).status_code==403
    unchanged=c.get(url,headers=a).json()
    assert unchanged['budget']==0 and unchanged['revision']==1 and unchanged['messages']==[]
