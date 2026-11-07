import copy
from fastapi.testclient import TestClient
from tagalong.app import create_app
from tagalong.core import Actor, MemoryRepository, source

class Retrieval:
    def retrieve_group_fit(self,pid,query):return []
class Places:
    def __init__(self):self.hook=None
    def search(self,*args):
        if self.hook:self.hook()
        return [{'kind':'place','title':'Lake lodge','url':'https://example.com/lodge','snippet':'Public listing; verify availability.'}]
def setup():
    repo=MemoryRepository();places=Places();ai=Retrieval()
    c=TestClient(create_app(repo,lambda t:Actor(t,t+'@test.com',t),ai,places));h={'Authorization':'Bearer owner'}
    p=c.post('/v1/plans',headers=h,json={'title':'Trip','kind':'trip','start':'2027-05-14','end':'2027-05-16'}).json()
    repo.transact(lambda s:source(s,p['id'],'needs','Group needs','Quiet lodging requested.',kind='document'))
    return repo,c,h,p,places,ai
def research(c,h,p,**changes):
    return c.post('/v1/plans/'+p['id']+'/research',headers=h,json={'expected_revision':p['revision'],'query':'quiet lodge','category':'lodging','location':'Chicago',**changes})
def test_research_read_only_sources_and_external_receipts():
    repo,c,h,p,places,ai=setup();before=copy.deepcopy(repo.state)
    r=research(c,h,p);assert r.status_code==200,r.text
    data=r.json();assert repo.state==before
    assert {'plan-facts','saved:needs','external:1'}<={s['id'] for s in data['sources']}
    assert data['options'][0]['source_ids']==['external:1']
    provenance=data['options'][0]['provenance']
    assert provenance['url']==data['options'][0]['url'] and provenance['excerpt']==data['options'][0]['details']
    from tagalong.decisions import OptionProvenance
    assert OptionProvenance.model_validate(provenance).retrievedAt==provenance['retrievedAt']
    assert all(s['status']=='completed' for s in data['steps'][:3])
def test_research_partial_outage_and_stale_access():
    repo,c,h,p,places,ai=setup()
    def unavailable(*args):raise RuntimeError('private failure')
    ai.retrieve_group_fit=unavailable
    assert research(c,h,p).json()['steps'][0]['status']=='unavailable'
    places.hook=lambda:repo.state['sources'][p['id']+':needs'].update(version=2)
    assert research(c,h,p).status_code==409
    assert research(c,{'Authorization':'Bearer stranger'},p).status_code==404
def test_option_metadata_and_legacy_validation():
    repo,c,h,p,places,ai=setup();url='/v1/plans/'+p['id']+'/decisions'
    body={'expected_revision':p['revision'],'title':'Stay','category':'lodging','options':['Lodge'],'option_details':[{'label':'Lodge','url':'https://example.com','estimatedCostPerPerson':90,'notes':'Verify','sourceIds':['saved:needs']}]}
    r=c.post(url,headers=h,json=body);assert r.status_code==200,r.text
    o=r.json()['decisions'][-1]['options'][0];assert o['notes']=='Verify' and o['estimatedCostPerPerson']==90
    body['expected_revision']=r.json()['plan_revision'];body['option_details'][0]['url']='javascript:bad'
    assert c.post(url,headers=h,json=body).status_code==422
    body['option_details'][0]['url']='https://example.com';body['option_details'][0]['label']='Different'
    assert c.post(url,headers=h,json=body).status_code==422

def test_research_sanitizes_provider_rows_and_limits_requests():
    repo,c,h,p,places,ai=setup()
    places.search=lambda *args:[{'title':'Unsafe','url':'http://127.0.0.1','snippet':'bad'}, {'kind':'place','title':'Safe','url':'https://example.com','snippet':'x'*5000}]
    r=research(c,h,p);assert r.status_code==200
    assert len(r.json()['options'])==1 and len(r.json()['options'][0]['details'])==1500
    for _ in range(9):assert research(c,h,p).status_code==200
    assert research(c,h,p).status_code==429

def test_research_rejects_changes_during_retrieval_and_revocation_during_search():
    repo,c,h,p,places,ai=setup()
    def retrieve(*args):
        repo.state['sources'][p['id']+':needs']['version']+=1
        return []
    ai.retrieve_group_fit=retrieve
    assert research(c,h,p).status_code==409
    ai.retrieve_group_fit=lambda *args:[]
    places.hook=lambda:repo.state['members'][p['id']].clear()
    assert research(c,h,p).status_code==404

def test_option_legacy_edits_preserve_metadata_and_reject_cross_plan_source():
    repo,c,h,p,places,ai=setup();url='/v1/plans/'+p['id']+'/decisions'
    b={'expected_revision':p['revision'],'title':'Stay','category':'lodging','options':['Lodge'],'option_details':[{'label':'Lodge','notes':'Keep me','url':'https://example.com','sourceIds':['saved:missing']}]}
    assert c.post(url,headers=h,json=b).status_code==422
    b['option_details'][0]['sourceIds']=['saved:needs']
    r=c.post(url,headers=h,json=b);assert r.status_code==200
    d=r.json()['decisions'][-1]
    edit={'expected_revision':r.json()['plan_revision'],'expected_version':d['version'],'options':['Lodge','Other']}
    r=c.patch(url+'/'+d['id'],headers=h,json=edit);assert r.status_code==200
    updated=r.json()['decisions'][-1]
    assert updated['version']==2 and updated['options'][0]['notes']=='Keep me'
    assert updated['options'][1]['sourceIds']==[]

import pytest
@pytest.mark.parametrize('field,value',[('estimatedCostPerPerson',True),('estimatedCostPerPerson',-1),('estimatedCostPerPerson',1000001),('image','data:image/png,bad'),('url','https://example.com@localhost/')])
def test_option_metadata_bounds(field,value):
    repo,c,h,p,places,ai=setup()
    body={'expected_revision':p['revision'],'title':'Stay','category':'lodging','options':['Lodge'],'option_details':[{'label':'Lodge',field:value}]}
    assert c.post('/v1/plans/'+p['id']+'/decisions',headers=h,json=body).status_code==422


def test_venue_identification_preferred_articles_not_options_and_photos_grounded():
    repo,c,h,p,places,ai=setup()
    def venues(*args):
        return [{'kind':'article','title':'Best stays','url':'https://example.com/guide','snippet':'Guide'},
                {'kind':'place','title':'Lake lodge','url':'https://example.com/lodge','snippet':'Official description','image':'https://example.com/photo.jpg','image_source_url':'https://example.com/lodge'},
                {'kind':'place','title':'Other lodge','url':'https://example.com/other','snippet':'Official description','image':'https://example.com/unrelated.jpg','image_source_url':'https://foreign.example.com/'}]
    places.venues=venues
    places.search=lambda *args:(_ for _ in ()).throw(AssertionError('Raw search must not be used'))
    r=research(c,h,p);assert r.status_code==200
    data=r.json();assert len(data['options'])==2
    assert len([s for s in data['sources'] if s['id'].startswith('external:')])==3
    assert data['options'][0]['image']=='https://example.com/photo.jpg'
    assert 'image' not in data['options'][1]
    assert data['steps'][-1]['status']=='completed'

def test_research_global_concurrency_is_bounded_and_slots_released():
    repo,c,h,p,places,ai=setup();responses=[];depth=[0]
    def nested():
        if depth[0]>=2:return
        depth[0]+=1
        responses.append(research(c,h,p).status_code)
        depth[0]-=1
    places.hook=nested
    assert research(c,h,p).status_code==200
    assert sorted(responses)==[200,429]
    places.hook=None
    assert research(c,h,p).status_code==200

def test_option_provenance_survives_legacy_edit_and_external_ids_are_not_persisted():
    repo,c,h,p,places,ai=setup();url='/v1/plans/'+p['id']+'/decisions'
    provenance={'url':'https://example.com/lodge','retrievedAt':'2026-11-06T18:00:00Z','excerpt':'Unverified official listing excerpt'}
    detail={'label':'Lodge','url':provenance['url'],'sourceIds':['external:1'],'provenance':provenance}
    body={'expected_revision':p['revision'],'title':'Stay','category':'lodging','options':['Lodge'],'option_details':[detail]}
    r=c.post(url,headers=h,json=body);assert r.status_code==200,r.text
    d=r.json()['decisions'][-1];assert d['options'][0]['sourceIds']==[]
    assert d['options'][0]['provenance']==provenance
    r=c.patch(url+'/'+d['id'],headers=h,json={'expected_revision':r.json()['plan_revision'],'expected_version':d['version'],'options':['Lodge']})
    assert r.status_code==200 and r.json()['decisions'][-1]['options'][0]['provenance']==provenance

@pytest.mark.parametrize('provenance',[
    None,
    {'url':'https://other.example.com/','retrievedAt':'2026-11-06T18:00:00Z','excerpt':'Text'},
    {'url':'https://example.com/lodge','retrievedAt':'yesterday','excerpt':'Text'},
    {'url':'https://example.com/lodge','retrievedAt':'2026-11-06','excerpt':'Text'},
    {'url':'http://localhost/','retrievedAt':'2026-11-06T18:00:00Z','excerpt':'Text'},
])
def test_option_rejects_invalid_or_missing_external_provenance(provenance):
    repo,c,h,p,places,ai=setup()
    detail={'label':'Lodge','url':'https://example.com/lodge','sourceIds':['external:unknown']}
    if provenance is not None:detail['provenance']=provenance
    body={'expected_revision':p['revision'],'title':'Stay','category':'lodging','options':['Lodge'],'option_details':[detail]}
    assert c.post('/v1/plans/'+p['id']+'/decisions',headers=h,json=body).status_code==422

def test_retrieval_and_public_search_start_concurrently():
    import threading
    repo,c,h,p,places,ai=setup();retrieval_started=threading.Event();search_started=threading.Event();overlap=[]
    def retrieve(*args):
        retrieval_started.set()
        if not search_started.wait(timeout=3):raise AssertionError('Public search did not start concurrently')
        overlap.append('retrieve')
        return []
    def search(*args):
        search_started.set()
        if not retrieval_started.wait(timeout=3):raise AssertionError('Retrieval did not start concurrently')
        overlap.append('search')
        return []
    ai.retrieve_group_fit=retrieve;places.search=search
    r=research(c,h,p);assert r.status_code==200,r.text
    assert sorted(overlap)==['retrieve','search']
    statuses={s['id']:s['status'] for s in r.json()['steps']}
    assert statuses['retrieval']==statuses['search']=='completed'
