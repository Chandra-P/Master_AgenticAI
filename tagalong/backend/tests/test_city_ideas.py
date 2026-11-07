from fastapi import FastAPI
from fastapi.testclient import TestClient
from tagalong.core import Actor,MemoryRepository
from tagalong.city_ideas import install_city_ideas,normalize_events


def setup(provider):
    repo=MemoryRepository();app=FastAPI()
    install_city_ideas(app,repo,lambda:Actor('a','a@example.com','a'),provider,None)
    return repo,TestClient(app)


def test_missing_interests_asks_without_provider():
    class Provider:
        def search(self,*args):raise AssertionError('No call expected')
    repo,c=setup(Provider())
    result=c.post('/v1/city-ideas',json={'city':'Austin','start':'2027-05-01','end':'2027-05-03','interests':[]})
    assert result.status_code==200 and result.json()['question']
    assert result.json()['places']==[]


def test_filters_articles_and_unsafe_images_and_bounds_dates():
    class Provider:
        def search(self,*args):return [{'kind':'article','title':'Top places','url':'https://example.com/top'},{'kind':'place','title':'Garden','url':'https://example.com/garden','image':'https://example.com/photo.jpg'}]
    _,c=setup(Provider())
    data={'city':'Austin','start':'2027-05-01','end':'2027-05-03','interests':['gardens']}
    result=c.post('/v1/city-ideas',json=data).json()
    assert [p['name'] for p in result['places']]==['Garden']
    assert 'image' not in result['places'][0]
    assert result['places'][0]['provenance']['url']=='https://example.com/garden'
    assert result['places'][0]['provenance']['retrievedAt']
    assert result['events']==[]
    assert c.post('/v1/city-ideas',json={**data,'end':'2027-07-01'}).status_code==422


def test_events_require_verbatim_name_date_official_page_and_range():
    pages=[{'id':'p1','url':'https://example.com/event','title':'Organizer','content':'Garden Festival May 2, 2027. Official organizer ticket page.'}]
    valid={'source_id':'p1','kind':'event','name':'Garden Festival','raw_date':'May 2, 2027','date':'2027-05-02','official':True,'description':'','image_url':''}
    assert len(normalize_events([valid],pages,'2027-05-01','2027-05-03'))==1
    for change in [{'name':'Made up'},{'raw_date':'May 9, 2027'},{'date':'2028-05-02'},{'official':False}]:
        assert normalize_events([{**valid,**change}],pages,'2027-05-01','2027-05-03')==[]


def test_suspension_after_provider_prevents_disclosure():
    class Provider:
        def search(self,*args):
            repo.state['suspended_users']={'a':True}
            return []
    repo,c=setup(Provider())
    assert c.post('/v1/city-ideas',json={'city':'Austin','start':'2027-05-01','end':'2027-05-03','interests':['art']}).status_code==403


def test_live_event_pipeline_and_request_limit():
    class Provider:
        def search(self,*args):return [{'title':'Garden','url':'https://example.com/festival'}]
        def fetch_page(self,row):return {**row,'content':'Garden Festival May 2, 2027'}
    repo,c=setup(Provider())
    c.app.state.city_event_extractor=lambda *args:[{'source_id':'event-source:1','kind':'event','official':True,'name':'Garden Festival','raw_date':'May 2, 2027','date':'2027-05-02'}]
    body={'city':'Austin','start':'2027-05-01','end':'2027-05-03','interests':['gardens']}
    result=c.post('/v1/city-ideas',json=body).json()
    assert result['events'][0]['date']=='2027-05-02'
    from datetime import datetime,timezone
    provenance=result['events'][0]['provenance']
    assert provenance['url']=='https://example.com/festival'
    assert abs((datetime.now(timezone.utc)-datetime.fromisoformat(provenance['retrievedAt'])).total_seconds())<30
    assert 'Retrieved:' in result['sources'][0]['text']
    assert 'Garden Festival' in provenance['excerpt'] and 'May 2, 2027' in provenance['excerpt']
    for _ in range(5):assert c.post('/v1/city-ideas',json=body).status_code==200
    assert c.post('/v1/city-ideas',json=body).status_code==429


def test_reviewed_draft_suggestions_are_drafts_and_saved_note():
    import time
    from tagalong.coordination_routes import install_coordination
    repo,c=setup(None)
    install_coordination(c.app,repo,lambda:Actor('a','a@example.com','a'),None)
    draft={'title':'Weekend','type':'trip','location':'Austin','start':None,'end':None,'participant_count':2,'suggested_tasks':[],'suggested_itinerary':[{'title':'Talk together','time':'Later','category':'Draft','location':'Austin'}],'suggested_budget':{'amount':None,'basis':'unknown','currency':'','notes':''},'open_questions':[]}
    repo.state['plan_drafts']={'draft':{'owner_id':'a','expires_at':time.time()+100,'created_plan_id':None,'draft':draft}}
    body={'draft_id':'draft','title':'Weekend','kind':'trip','location':'Austin','start':'2027-05-01','end':'2027-05-03','reviewed_suggestions':[{'title':'Garden Festival','url':'https://example.com/event','day':'2027-05-02','category':'Event idea'}]}
    body['reviewed_suggestions'][0]['provenance']={'url':'https://example.com/event','retrievedAt':'2027-04-01T10:00:00Z','excerpt':'Garden Festival May 2, 2027'}
    response=c.post('/v1/plans/from-draft',json=body)
    assert response.status_code==200,response.text
    itinerary=response.json()['itinerary']
    assert len(itinerary)==2 and itinerary[-1]['source_url']=='https://example.com/event'
    assert itinerary[-1]['time'].startswith('Draft')
    notes=[s for s in repo.state['sources'].values() if s['kind']=='document']
    assert len(notes)==1 and 'unverified' in notes[0]['text'] and 'https://example.com/event' in notes[0]['text']
    assert '2027-04-01T10:00:00Z' in notes[0]['text'] and 'Garden Festival May 2, 2027' in notes[0]['text']
    for suggestion in [{'title':'X','url':'http://127.0.0.1','category':'Place idea'},{'title':'X','url':'https://example.com/','day':'2028-01-01','category':'Event idea'}]:
        assert c.post('/v1/plans/from-draft',json={**body,'reviewed_suggestions':[suggestion]}).status_code==422
