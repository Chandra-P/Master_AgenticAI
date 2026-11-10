from datetime import datetime,timezone,timedelta
from fastapi.testclient import TestClient
from tagalong.app import create_app
from tagalong.core import Actor,MemoryRepository


class AI:
    def generate_plan(self,prompt,today):
        return {'title':'Friends weekend','type':'trip','location':'Austin','start':None,'end':None,'participant_count':4,'suggested_tasks':['Confirm attendees','Choose lodging'],'suggested_itinerary':[],'suggested_budget':{'amount':None,'basis':'unknown','currency':'USD','notes':'Agree a budget together'},'open_questions':['Which dates?']}
    def coordinate(self,context):
        return {'summary':'The group is planning a weekend.','decisions_made':context['approved_decisions'],'open_questions':['Choose lodging'],'next_step':'Choose lodging','reason':'The trip needs a place to stay.'}


def setup(ai=None):
    repo=MemoryRepository();c=TestClient(create_app(repo,lambda t:Actor(t,t+'@test.com',t),ai or AI()))
    owner={'Authorization':'Bearer alice'}
    return repo,c,owner


def test_natural_language_draft_is_reviewed_before_plan_creation():
    repo,c,a=setup()
    draft=c.post('/v1/plans/generate',headers=a,json={'prompt':'Weekend for four friends near Austin','local_date':datetime.now(timezone.utc).date().isoformat()})
    assert draft.status_code==200
    data=draft.json();assert data['draft']['start'] is None
    assert repo.state['plans']=={}
    payload={'draft_id':data['draft_id'],'title':'Our reviewed weekend','kind':'trip','location':'Austin','start':'2027-05-14','end':'2027-05-16','budget_per_person':350}
    assert c.post('/v1/plans/from-draft',headers={'Authorization':'Bearer bob'},json=payload).status_code==404
    created=c.post('/v1/plans/from-draft',headers=a,json=payload)
    assert created.status_code==200 and created.json()['budget']==350
    assert created.json()['tasks'][0]['label']=='Confirm attendees'
    assert len(repo.state['plans'])==1
    assert c.post('/v1/plans/from-draft',headers=a,json=payload).json()['id']==created.json()['id']


def test_generated_tasks_do_not_repeat_core_decisions():
    class Repetitive(AI):
        def generate_plan(self,prompt,today):
            result=super().generate_plan(prompt,today)
            result['suggested_tasks']=['Agree a budget','Finalize budget','Confirm attendees','Choose destination']
            return result
    repo,c,a=setup(Repetitive())
    draft=c.post('/v1/plans/generate',headers=a,json={'prompt':'Weekend in Austin','local_date':datetime.now(timezone.utc).date().isoformat()}).json()
    assert draft['draft']['suggested_tasks']==['Confirm attendees']
    created=c.post('/v1/plans/from-draft',headers=a,json={'draft_id':draft['draft_id'],'title':'Austin weekend','kind':'trip','location':'Austin','start':'2027-05-14','end':'2027-05-16'})
    assert created.status_code==200
    labels=[task['label'] for task in created.json()['tasks']]
    assert labels==['Confirm attendees']


def test_new_plans_do_not_repeat_default_budget_and_place_decisions_as_tasks():
    repo,c,a=setup()
    plan=c.post('/v1/plans',headers=a,json={'title':'New trip','kind':'trip','start':'2027-05-14','end':'2027-05-16'}).json()
    snapshot=c.get('/v1/plans/'+plan['id']+'/decisions',headers=a).json()
    categories={decision['category'] for decision in snapshot['decisions']}
    assert {'budget','destination'}<=categories
    assert not any('budget' in task['label'].casefold() or 'meeting place' in task['label'].casefold() for task in plan['tasks'])


def test_legacy_duplicate_decision_tasks_are_hidden_and_do_not_block_progress():
    repo,c,a=setup()
    plan=c.post('/v1/plans',headers=a,json={'title':'Older plan','kind':'trip','start':'2027-05-14','end':'2027-05-16'}).json()
    repo.state['plans'][plan['id']]['tasks']=[{'label':'Agree a budget','done':False},{'label':'Finalize budget','done':False},{'label':'Confirm attendees','done':False}]
    visible=c.get('/v1/plans/'+plan['id'],headers=a).json()
    assert [task['label'] for task in visible['tasks']]==['Confirm attendees']
    status=c.get('/v1/plans/'+plan['id']+'/coordination',headers=a).json()
    assert 'Complete 1 remaining task(s)' in status['blockers']


def test_coordination_is_stored_private_and_not_free_form():
    repo,c,a=setup()
    p=c.post('/v1/plans',headers=a,json={'title':'Weekend','kind':'trip','start':'2027-05-14','end':'2027-05-16'}).json()
    url='/v1/plans/'+p['id']+'/coordination'
    assert c.get(url,headers={'Authorization':'Bearer bob'}).status_code==404
    c.get(url,headers=a)
    result=c.get(url,headers=a).json()
    assert result['status']=='WAITING_FOR_VOTES'
    assert isinstance(result['health'],int)
    assert result['summary']=='The group is planning a weekend.'
    assert result['decisions_made']==[]
    assert repo.state['coordination'][p['id']]['summary']==result['summary']


def test_health_stalled_activity_and_explicit_insights():
    from tagalong.coordination import health
    repo,c,a=setup()
    p=c.post('/v1/plans',headers=a,json={'title':'Weekend','kind':'trip','start':'2027-05-14','end':'2027-05-16'}).json()
    pid=p['id'];old=(datetime.now(timezone.utc)-timedelta(days=10)).isoformat()
    repo.state['plan_activity'][pid]=old
    state=health(repo.state,pid)
    assert state['status']=='STALLED' and state['inactive_days']>=10
    assert 'Resume' in state['next_step']
    repo.state['plans'][pid]['preferences']=[{'label':'Vegetarian meals','confirmed':True},{'label':'Luxury hotels','confirmed':False}]
    overview=c.get('/v1/coordination/overview',headers=a).json()
    assert overview['group_insights']==[{'label':'Vegetarian meals','plan_count':1}]
    assert all('Luxury' not in item['label'] for item in overview['group_insights'])


def test_invalid_ai_output_does_not_create_a_plan():
    class Bad(AI):
        def generate_plan(self,*args):return {'title':'incomplete'}
    repo,c,a=setup(Bad())
    assert c.post('/v1/plans/generate',headers=a,json={'prompt':'Birthday dinner for ten','local_date':datetime.now(timezone.utc).date().isoformat()}).status_code==502
    assert repo.state['plans']=={}


def test_large_poll_context_has_hard_limit_and_marks_truncation():
    import json
    from tagalong.coordination import context
    repo,c,a=setup();p=c.post('/v1/plans',headers=a,json={'title':'Large plan','kind':'outing','start':'2027-05-14','end':'2027-05-14'}).json()
    repo.state['plans'][p['id']]['polls']=[{'id':str(i),'question':'Question '+('x'*480),'options':['A','B'],'votes':{}} for i in range(100)]
    result=context(repo.state,p['id'])
    assert len(json.dumps(result))<=40000
    assert result['context_truncated'] is True


def test_stale_ai_response_is_not_saved_after_a_plan_change():
    repo,c,a=setup()
    p=c.post('/v1/plans',headers=a,json={'title':'Original','kind':'outing','start':'2027-05-14','end':'2027-05-14'}).json()
    class Racing(AI):
        def coordinate(self,facts):
            repo.transact(lambda s:s['plans'][p['id']].update(title='Changed',revision=2))
            return super().coordinate(facts)
    from tagalong.coordination_routes import refresh,reserve
    actor=Actor('alice','alice@test.com','alice')
    token=repo.transact(lambda s:reserve(s,actor,p['id']))
    refresh(repo,actor,p['id'],Racing(),token)
    assert p['id'] not in repo.state.get('coordination',{})


def test_response_schema_keeps_title_fields_and_requires_all_properties():
    from tagalong.coordination_ai import response_schema
    from tagalong.coordination_models import PlanDraft,RecommendationOutput
    schema=response_schema(PlanDraft)
    assert 'title' in schema['properties']
    assert set(schema['required'])==set(schema['properties'])
    assert 'activity_ideas' in response_schema(RecommendationOutput)['required']


def test_health_states_and_provider_failure_are_factual():
    from tagalong.coordination import health
    repo,c,a=setup(object())
    p=c.post('/v1/plans',headers=a,json={'title':'Status check','kind':'trip','start':'2027-05-14','end':'2027-05-16'}).json();pid=p['id']
    p=repo.state['plans'][pid]
    p['start']='';assert health(repo.state,pid)['status']=='WAITING_FOR_DATE';p['start']='2027-05-14'
    p['polls'][0]['votes']={'alice':0};assert health(repo.state,pid)['status']=='WAITING_FOR_LOCATION'
    p.update(location='Austin',budget=350);assert health(repo.state,pid)['status']=='ACTIVE'
    p['itinerary']=[{'id':'draft','title':'Draft walk','time':'Afternoon','category':'Draft','location':'Austin'}]
    for task in p['tasks']:task['done']=True
    assert health(repo.state,pid)['status']=='READY_TO_FINALIZE'
    assert health(repo.state,pid,datetime(2027,6,1,tzinfo=timezone.utc))['status']=='COMPLETED'
    c.get('/v1/plans/'+pid+'/coordination',headers=a)
    data=c.get('/v1/plans/'+pid+'/coordination',headers=a).json()
    assert data['provider_status']=='unavailable'
    assert 'Status check' in data['summary']
    assert data['decisions_made']==[]


def test_ai_cannot_publish_unconfirmed_decisions_or_ungrounded_activity_insights():
    class Overclaim(AI):
        def coordinate(self,facts):
            return {'summary':'Working plan details.','decisions_made':['Everyone agreed to luxury hotels'],'open_questions':[],'next_step':facts['health']['next_step'],'reason':facts['health']['reason'],'activity_ideas':[{'title':'Luxury spa','reason':'Assumed preference','preference_labels':['Luxury hotels']}]}
    repo,c,a=setup(Overclaim());p=c.post('/v1/plans',headers=a,json={'title':'Grounded only','kind':'outing','start':'2027-05-14','end':'2027-05-14'}).json()
    c.get('/v1/plans/'+p['id']+'/coordination',headers=a)
    data=c.get('/v1/plans/'+p['id']+'/coordination',headers=a).json()
    assert data['decisions_made']==[] and data['activity_ideas']==[]


def test_inactivity_invalidates_old_recommendation_without_a_plan_edit():
    import time
    repo,c,a=setup();p=c.post('/v1/plans',headers=a,json={'title':'Aging plan','kind':'trip','start':'2027-05-14','end':'2027-05-16'}).json();pid=p['id']
    c.get('/v1/plans/'+pid+'/coordination',headers=a)
    assert repo.state['coordination'][pid]['status']=='WAITING_FOR_VOTES'
    repo.state['plan_activity'][pid]=(datetime.now(timezone.utc)-timedelta(days=8)).isoformat()
    repo.state['coordination_attempts'][pid]=time.time()-20
    response=c.get('/v1/plans/'+pid+'/coordination',headers=a).json()
    assert response['status']=='STALLED' and response['stale'] is True
    assert repo.state['coordination'][pid]['status']=='STALLED'
