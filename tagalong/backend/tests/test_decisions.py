from fastapi.testclient import TestClient
from tagalong.app import create_app
from tagalong.core import Actor, MemoryRepository


def setup():
    repo=MemoryRepository(); c=TestClient(create_app(repo,lambda t:Actor(t,t+'@test.com',t)))
    h={'Authorization':'Bearer owner'}; m={'Authorization':'Bearer member'}
    p=c.post('/v1/plans',headers=h,json={'title':'Dinner','kind':'outing','start':'2026-12-12','end':'2026-12-12'}).json()
    return repo,c,h,m,'/v1/plans/'+p['id']


def test_legacy_seed_is_proposed_authorized_and_persistent():
    repo,c,h,m,url=setup()
    r=c.get(url+'/decisions',headers=h)
    assert r.status_code==200
    data=r.json(); assert len(data['decisions'])==4 and data['score']==0 and not data['finalized']
    assert all(d['confirmation'] is None for d in data['decisions'])
    assert c.get(url+'/decisions',headers=h).json()==data
    assert c.get(url+'/decisions',headers=m).status_code==404


def test_full_consent_versions_comments_and_finalization():
    repo,c,h,m,url=setup()
    c.get('/v1/me',headers=m); c.post(url+'/members',headers=h,json={'email':'member@test.com'})
    data=c.get(url+'/decisions',headers=h).json()
    def command(path,body,headers=h,method='post'):
        nonlocal data
        result=getattr(c,method)(url+path,headers=headers,json={'expected_revision':data['plan_revision'],**body})
        if result.status_code==200:data=result.json()
        return result
    for decision in list(data['decisions']):
        did=decision['id']; base='/decisions/'+did
        assert command(base,{'expected_version':1,'options':['Candidate']},method='patch').status_code==200
        version=2
        assert command(base+'/confirm',{'expected_version':version,'option_id':data['decisions'][0]['options'][0]['id']}).status_code==409
        d=next(d for d in data['decisions'] if d['id']==did); option=d['options'][0]['id']
        assert command(base+'/response',{'expected_version':1,'option_id':option,'response':'support'},method='put').status_code==409
        assert command(base+'/response',{'expected_version':version,'option_id':option,'response':'support','memberId':'member'},method='put').status_code==422
        assert command(base+'/response',{'expected_version':version,'option_id':option,'response':'support'},method='put').status_code==200
        assert command(base+'/comments',{'expected_version':version,'text':'Parking concern'},headers=m).status_code==200
        assert command(base+'/confirm',{'expected_version':version,'option_id':option}).status_code==409
        assert command(base+'/response',{'expected_version':version,'option_id':None,'response':'abstain'},headers=m,method='put').status_code==200
        assert command(base+'/confirm',{'expected_version':version,'option_id':option},headers=m).status_code==403
        assert command(base+'/confirm',{'expected_version':version,'option_id':option}).status_code==200
    assert data['score']==99
    payload={'expected_revision':data['plan_revision'],'idempotency_key':'final-1','reviewed':True}
    result=c.post(url+'/finalize',headers=h,json=payload); assert result.status_code==200
    data=result.json(); assert data['score']==100 and data['finalized']
    assert c.post(url+'/finalize',headers=h,json=payload).json()==data
    assert len(c.get(url+'/decisions',headers=m).json()['comments'])==4
    c.delete(url+'/members/member',headers=h)
    fresh=c.get(url+'/decisions',headers=h).json()
    assert not fresh['finalized'] and all(d['confirmation'] is None for d in fresh['decisions'])
    assert c.get(url+'/decisions',headers=m).status_code==404

def test_objections_split_options_optional_and_empty_required():
    repo,c,h,m,url=setup();c.get('/v1/me',headers=m);c.post(url+'/members',headers=h,json={'email':'member@test.com'})
    data=c.get(url+'/decisions',headers=h).json()
    def cmd(path,body,headers=h,method='post'):
        nonlocal data
        r=getattr(c,method)(url+path,headers=headers,json={'expected_revision':data['plan_revision'],**body})
        if r.status_code==200:data=r.json()
        return r
    d=data['decisions'][0];base='/decisions/'+d['id']
    cmd(base,{'expected_version':1,'options':['A','B']},method='patch');d=data['decisions'][0];a,b=[o['id'] for o in d['options']]
    cmd(base+'/response',{'expected_version':2,'option_id':a,'response':'support'},method='put')
    cmd(base+'/response',{'expected_version':2,'option_id':b,'response':'support'},m,'put')
    assert data['decisions'][0]['status']=='needs_discussion'
    assert cmd(base+'/confirm',{'expected_version':2,'option_id':a}).status_code==409
    cmd(base+'/response',{'expected_version':2,'option_id':a,'response':'object'},m,'put')
    assert cmd(base+'/confirm',{'expected_version':2,'option_id':a}).status_code==409
    assert cmd('/finalize',{'idempotency_key':'bad','reviewed':True}).status_code==409
    for d in list(data['decisions']):cmd('/decisions/'+d['id'],{'expected_version':d['version'],'required':False},method='patch')
    assert data['score']==0
    assert cmd('/finalize',{'idempotency_key':'empty','reviewed':True}).status_code==409


def test_outline_invalidation_forgery_cross_plan_and_evidence():
    repo,c,h,m,url=setup();data=c.get(url+'/decisions',headers=h).json();d=data['decisions'][0]
    result=c.post(url+'/decisions/'+d['id']+'/comments',headers=h,json={'expected_revision':data['plan_revision'],'expected_version':1,'text':'Synthetic concern'})
    assert result.status_code==200
    assert any(s['kind']=='decision_comment' for s in repo.state['sources'].values())
    p=c.get(url,headers=h).json()
    forged=c.put(url,headers=h,json={'expected_revision':p['revision'],'plan':{**p,'finalized':True}})
    assert forged.status_code==403
    p['location']='Synthetic place';assert c.put(url,headers=h,json={'expected_revision':p['revision'],'plan':p}).status_code==200
    fresh=c.get(url+'/decisions',headers=h).json();assert all(x['version']==2 for x in fresh['decisions'])
    other=c.post('/v1/plans',headers=h,json={'title':'Other','kind':'outing','start':'2026-12-12','end':'2026-12-12'}).json()
    r=c.post('/v1/plans/'+other['id']+'/decisions/'+d['id']+'/comments',headers=h,json={'expected_revision':1,'expected_version':2,'text':'Wrong plan'})
    assert r.status_code==404
    from tagalong.decisions import context
    ctx=context(repo.state,p['id']);assert len(__import__('json').dumps(ctx))<=12000

def test_structured_context_is_bounded_and_does_not_include_contacts():
    repo,c,h,m,url=setup();c.get(url+'/decisions',headers=h)
    pid=url.split('/')[-1]
    from tagalong.decisions import new_decision,context
    r=repo.state['decision_state'][pid]
    r['decisions']=[new_decision(pid,'x'*120,'activity',True,['Label '+str(i)+'x'*280 for i in range(12)],['owner']) for _ in range(20)]
    r['comments']=[{'id':str(i),'text':'c'*2000,'authorId':'owner'} for i in range(100)]
    import json
    result=context(repo.state,pid)
    assert isinstance(result,dict) and result['decisions']
    assert len(json.dumps(result))<=12000
    assert 'email' not in json.dumps(context(repo.state,pid))

def test_consensus_arithmetic_boundaries_all_abstain_and_optional():
    from tagalong.decisions import snapshot,new_decision,ensure
    repo=MemoryRepository();a=Actor('owner','owner@test.com','owner')
    from tagalong.core import create
    from tagalong.models import Create
    p=repo.transact(lambda s:create(s,a,Create(title='Synthetic',kind='outing',start='2026-12-12',end='2026-12-12')));pid=p['id']
    members=['owner']+['member'+str(i) for i in range(99)];repo.state['members'][pid]=members
    r=ensure(repo.state,pid);d=new_decision(pid,'Required','place',True,['A','B'],members);r['decisions']=[d]
    for replies in (0,30,31,70,71,99,100):
        d['ballots']=[{'memberId':mid,'optionId':d['options'][0]['id'],'response':'support','decisionVersion':1,'updatedAt':'2026-11-06'} for mid in members[:replies]]
        assert snapshot(repo.state,pid,a)['score']==min(99,replies)
    d['ballots']=[{'memberId':mid,'optionId':None,'response':'abstain','decisionVersion':1,'updatedAt':'2026-11-06'} for mid in members]
    from tagalong.decisions import consent
    assert snapshot(repo.state,pid,a)['score']==0 and not consent(d,d['options'][0]['id'])
    d['required']=False;assert snapshot(repo.state,pid,a)['score']==0

def test_current_decisions_and_comments_reach_all_three_ai_boundaries():
    class EvidenceAI:
        def __init__(self):self.seen={}
        def answer(self,plan,message,resolve_sources):
            self.seen['assistant']=plan['decision_context']
            sources=resolve_sources([])
            return {'text':'Synthetic response','preferences':[],'source_ids':[s['id'] for s in sources]},sources
        def coordinate(self,ctx):
            self.seen['coordination']=ctx['decision_context']
            return {'summary':'Synthetic summary','decisions_made':[],'open_questions':[],'next_step':ctx['health']['next_step'],'reason':ctx['health']['reason']}
        def retrieve(self,pid,query):return []
        def assess_group_fit(self,option,evidence):
            import json
            self.seen['group_fit']=json.loads(next(e['text'] for e in evidence if e['id']=='plan-facts'))['decision_context']
            return {'verdict':'needs_info','summary':'Synthetic assessment','matches':[],'conflicts':[],'unknowns':['Verify supplied details']}
    ai=EvidenceAI();repo=MemoryRepository();c=TestClient(create_app(repo,lambda t:Actor(t,t+'@test.com',t),ai));h={'Authorization':'Bearer owner'}
    p=c.post('/v1/plans',headers=h,json={'title':'Dinner','kind':'outing','start':'2026-12-12','end':'2026-12-12'}).json();url='/v1/plans/'+p['id']
    data=c.get(url+'/decisions',headers=h).json();d=data['decisions'][0]
    r=c.post(url+'/decisions/'+d['id']+'/comments',headers=h,json={'expected_revision':data['plan_revision'],'expected_version':1,'text':'Synthetic parking concern'});assert r.status_code==200
    for endpoint in ('assistant','coordination','group_fit'):
        if endpoint=='assistant':response=c.post(url+'/assistant',headers=h,json={'message':'Review current evidence'})
        elif endpoint=='coordination':response=c.get(url+'/coordination',headers=h)
        else:
            revision=c.get(url,headers=h).json()['revision']
            response=c.post(url+'/group-fit',headers=h,json={'expected_revision':revision,'option':{'name':'Synthetic option','details':'Review only'}})
        assert response.status_code==200,response.text
        ctx=ai.seen[endpoint]
        assert isinstance(ctx,dict) and ctx['decisions'][0]['id']==d['id']
        assert ctx['comments'][0]['text']=='Synthetic parking concern'

def test_finalized_decisions_survive_server_booking_but_real_outline_edits_reopen():
    from tests.test_demo_bookings import setup as booking_setup,quote,confirm
    repo,app,c,h,p,base=booking_setup();url='/v1/plans/'+p['id'];data=c.get(url+'/decisions',headers=h).json()
    for d in list(data['decisions']):
        body={'expected_revision':data['plan_revision'],'expected_version':d['version'],'required':False}
        data=c.patch(url+'/decisions/'+d['id'],headers=h,json=body).json()
    d=data['decisions'][0]
    data=c.patch(url+'/decisions/'+d['id'],headers=h,json={'expected_revision':data['plan_revision'],'expected_version':d['version'],'required':True,'options':['Austin']}).json();d=data['decisions'][0]
    data=c.put(url+'/decisions/'+d['id']+'/response',headers=h,json={'expected_revision':data['plan_revision'],'expected_version':d['version'],'option_id':d['options'][0]['id'],'response':'support'}).json()
    data=c.post(url+'/decisions/'+d['id']+'/confirm',headers=h,json={'expected_revision':data['plan_revision'],'expected_version':d['version'],'option_id':d['options'][0]['id']}).json()
    data=c.post(url+'/finalize',headers=h,json={'expected_revision':data['plan_revision'],'idempotency_key':'booked-outline','reviewed':True}).json();assert data['finalized']
    qid=quote(c,h,base);book=confirm(c,h,base,qid);assert book.status_code==200,book.text
    after=c.get(url+'/decisions',headers=h).json();assert after['finalized'] and after['decisions'][0]['confirmation']==data['decisions'][0]['confirmation']
    import copy
    plan=c.get(url,headers=h).json();forged=copy.deepcopy(plan);forged['itinerary'][-1]['title']='Forged reservation'
    assert c.put(url,headers=h,json={'expected_revision':plan['revision'],'plan':forged}).status_code==403
    booking_id=book.json()['booking']['id']
    assert c.post(base+'/'+booking_id+'/cancel',headers=h,json={'confirmed':True}).status_code==200
    assert c.get(url+'/decisions',headers=h).json()['finalized']
    plan=c.get(url,headers=h).json();plan['itinerary'].append({'id':'genuine-outline','title':'New working activity','time':'Noon','category':'Activity','location':'Austin'})
    assert c.put(url,headers=h,json={'expected_revision':plan['revision'],'plan':plan}).status_code==200
    assert not c.get(url+'/decisions',headers=h).json()['finalized']

def test_decision_summaries_are_current_authorized_validated_and_cached():
    class SummaryAI:
        def __init__(self):self.calls=0;self.hook=None;self.bad=False
        def coordinate(self,ctx):
            self.calls+=1
            assert ctx['decision_context']['decisions'][0]['title']=='Place'
            if self.hook:self.hook()
            if self.bad:return {'summary':123}
            return {'summary':'Synthetic contextual summary','decisions_made':[],'open_questions':[],'next_step':'Review decision responses','reason':'Current evidence'}
    ai=SummaryAI();repo=MemoryRepository();c=TestClient(create_app(repo,lambda t:Actor(t,t+'@test.com',t),ai));h={'Authorization':'Bearer owner'}
    p=c.post('/v1/plans',headers=h,json={'title':'Dinner','kind':'outing','start':'2026-12-12','end':'2026-12-12'}).json();url='/v1/plans/'+p['id'];data=c.get(url+'/decisions',headers=h).json();d=data['decisions'][0]
    target=url+'/decisions/'+d['id']+'/summary';payload={'expected_revision':data['plan_revision'],'expected_version':d['version']}
    assert c.post(target,headers={'Authorization':'Bearer stranger'},json=payload).status_code==404
    result=c.post(target,headers=h,json=payload);assert result.status_code==200,result.text
    summary=result.json();assert summary['providerStatus']=='live' and summary['text']=='Synthetic contextual summary' and summary['sources']
    assert c.post(target,headers=h,json=payload).json()==summary and ai.calls==1
    assert c.post(target,headers=h,json={**payload,'expected_version':99}).status_code==409
    repo.state['decision_summary_cache']={};repo.state['decision_summary_attempts']={};ai.bad=True
    assert c.post(target,headers=h,json=payload).json()['providerStatus']=='unavailable'
    repo.state['decision_summary_cache']={};repo.state['decision_summary_attempts']={};ai.bad=False
    ai.hook=lambda:repo.transact(lambda s:s['plans'][p['id']].update(revision=2))
    assert c.post(target,headers=h,json=payload).status_code==409
    repo2,c2,h2,_,url2=setup();snap=c2.get(url2+'/decisions',headers=h2).json();d2=snap['decisions'][0]
    assert c2.post(url2+'/decisions/'+d2['id']+'/summary',headers=h2,json={'expected_revision':snap['plan_revision'],'expected_version':1}).json()['providerStatus']=='unavailable'
