from fastapi.testclient import TestClient
from tagalong.app import create_app
from tagalong.core import Actor, MemoryRepository
import asyncio
import pytest


class FakeGateway:
    def __init__(self):
        self.hook=None
        self.calls=[]

    async def call(self,tool,arguments):
        self.calls.append(tool)
        if self.hook:
            self.hook(tool)
        results={'check_availability':{'available':True,'restaurant_name':'Fictional Lantern','estimated_total':70,'currency':'USD'},'create_demo_booking':{'reference':'DEMO-SYNTHETIC'},'cancel_demo_booking':{'status':'cancelled'},'search_restaurants':{'restaurants':[]}}
        return {'result':{'simulation':True,**results[tool]},'trace':[{'tool':tool,'status':'ok','protocol':'MCP','transport':'stdio'}]}


def setup():
    repo=MemoryRepository();app=create_app(repo,lambda t:Actor(t,t+'@test.com',t));app.state.demo_booking_gateway=FakeGateway()
    c=TestClient(app);h={'Authorization':'Bearer alice'}
    p=c.post('/v1/plans',headers=h,json={'title':'Dinner','kind':'outing','start':'2026-12-12','end':'2026-12-12'}).json()
    base='/v1/plans/'+p['id']+'/demo-bookings'
    return repo,app,c,h,p,base


def quote(c,h,base):
    response=c.post(base+'/quote',headers=h,json={'restaurant_id':'demo-lantern','city':'Austin','date':'2026-12-12','time':'18:00','party_size':2})
    assert response.status_code==200,response.text
    return response.json()['quote']['id']


def confirm(c,h,base,qid):
    return c.post(base+'/confirm',headers=h,json={'quote_id':qid,'confirmed':True})


def test_demo_booking_requires_explicit_confirmation_and_is_shared_idempotent():
    repo,app,c,h,p,base=setup()
    assert c.get(base,headers=h).status_code==200
    q=c.post(base+'/quote',headers=h,json={'restaurant_id':'demo-lantern','city':'Austin','date':'2026-12-12','time':'18:00','party_size':2})
    assert q.status_code==200, q.text
    qid=q.json()['quote']['id']
    assert c.post(base+'/confirm',headers=h,json={'quote_id':qid,'confirmed':'true'}).status_code==422
    b=c.post(base+'/confirm',headers=h,json={'quote_id':qid,'confirmed':True}); assert b.status_code==200,b.text
    assert b.json()['booking']['reference'].startswith('DEMO-')
    assert c.post(base+'/confirm',headers=h,json={'quote_id':qid,'confirmed':True}).json()['booking']==b.json()['booking']
    assert len(repo.state['plans'][p['id']]['itinerary'])==1
    assert repo.state['plans'][p['id']]['revision']==2
    bid=b.json()['booking']['id']
    assert c.post(base+'/'+bid+'/cancel',headers=h,json={'confirmed':True}).json()['booking']['status']=='cancelled'
    assert c.post(base+'/'+bid+'/cancel',headers=h,json={'confirmed':True}).status_code==200
    assert repo.state['plans'][p['id']]['itinerary']==[]
    assert confirm(c,h,base,qid).json()['booking']['status']=='cancelled'


@pytest.mark.parametrize('change',['expired','revision','foreign','cross_plan','suspended'])
def test_invalid_quote_cannot_create_booking(change):
    repo,app,c,h,p,base=setup();qid=quote(c,h,base)
    if change=='expired':repo.state['demo_booking_quotes'][qid]['expires_epoch']=0
    if change=='revision':repo.state['plans'][p['id']]['revision']+=1
    if change=='foreign':repo.state['demo_booking_quotes'][qid]['created_by']='bob'
    if change=='cross_plan':repo.state['demo_booking_quotes'][qid]['plan_id']='other'
    if change=='suspended':repo.state['suspended_users']={'alice':True}
    assert confirm(c,h,base,qid).status_code in (403,404,409)
    assert 'create_demo_booking' not in app.state.demo_booking_gateway.calls
    assert repo.state.get('demo_bookings',{})=={}


@pytest.mark.parametrize('change',['suspended','membership','revision','expired'])
def test_confirm_rechecks_after_tool_call(change):
    repo,app,c,h,p,base=setup();qid=quote(c,h,base)
    def hook(tool):
        if tool!='create_demo_booking':return
        if change=='suspended':repo.state['suspended_users']={'alice':True}
        if change=='membership':repo.state['members'][p['id']]=[]
        if change=='revision':repo.state['plans'][p['id']]['revision']+=1
        if change=='expired':repo.state['demo_booking_quotes'][qid]['expires_epoch']=0
    app.state.demo_booking_gateway.hook=hook
    assert confirm(c,h,base,qid).status_code in (403,404,409)
    assert repo.state.get('demo_bookings',{})=={}
    assert repo.state['plans'][p['id']]['itinerary']==[]


def test_members_can_view_but_only_creator_or_owner_can_cancel_and_only_generated_entry_removed():
    repo,app,c,h,p,base=setup();qid=quote(c,h,base);booking=confirm(c,h,base,qid).json()['booking']
    bob={'Authorization':'Bearer bob'};c.get('/v1/me',headers=bob)
    c.post('/v1/plans/'+p['id']+'/members',headers=h,json={'email':'bob@test.com'})
    assert len(c.get(base,headers=bob).json()['bookings'])==1
    assert c.post(base+'/'+booking['id']+'/cancel',headers=bob,json={'confirmed':True}).status_code==403
    extra={'id':'manual','title':'Manual','time':'19:00','category':'Food','location':'Austin'}
    repo.state['plans'][p['id']]['itinerary'].append(extra)
    assert c.post(base+'/'+booking['id']+'/cancel',headers=h,json={'confirmed':False}).status_code==422
    assert c.post(base+'/'+booking['id']+'/cancel',headers=h,json={'confirmed':True}).status_code==200
    assert repo.state['plans'][p['id']]['itinerary']==[extra]
    assert confirm(c,h,base,qid).json()['booking']['status']=='cancelled'


def test_actual_sdk_stdio_initialize_list_and_four_tools(monkeypatch):
    from tagalong.demo_booking_gateway import DemoBookingGateway
    monkeypatch.setenv('OPENAI_API_KEY','synthetic-secret-must-not-be-inherited')
    async def run():
        gateway=DemoBookingGateway()
        calls=[('search_restaurants',{'city':'Synthetic City','date':'2026-12-12','party_size':2}),('check_availability',{'restaurant_id':'demo-lantern','city':'Synthetic City','date':'2026-12-12','time':'18:00','party_size':2}),('create_demo_booking',{'quote_id':'synthetic-quote'}),('cancel_demo_booking',{'reference':'DEMO-SYNTHETIC'})]
        for tool,args in calls:
            result=await gateway.call(tool,args)
            assert result['result']['simulation'] is True
            assert [x['event'] for x in result['trace']]==['initialize','tools/list','tools/call']
            assert result['trace'][-1]['tool']==tool
            if tool=='search_restaurants':assert '19:00' in result['result']['restaurants'][0]['times']
        unavailable=await gateway.call('check_availability',{'restaurant_id':'demo-lantern','city':'Synthetic City','date':'2026-12-12','time':'23:00','party_size':2})
        assert unavailable['result']['available'] is False
    asyncio.run(run())


def test_quote_and_search_recheck_membership_and_dates():
    repo,app,c,h,p,base=setup()
    data={'restaurant_id':'demo-lantern','city':'Austin','date':'2026-12-13','time':'18:00','party_size':2}
    assert c.post(base+'/quote',headers=h,json=data).status_code==422
    assert app.state.demo_booking_gateway.calls==[]
    data['date']='2026-12-12'
    app.state.demo_booking_gateway.hook=lambda tool:repo.state['members'].__setitem__(p['id'],[])
    assert c.post(base+'/quote',headers=h,json=data).status_code==404
    assert repo.state.get('demo_booking_quotes',{})=={}


def test_duplicate_concurrent_confirmations_create_exactly_one_record_and_activity():
    from concurrent.futures import ThreadPoolExecutor
    import threading
    repo,app,c,h,p,base=setup();qid=quote(c,h,base)
    barrier=threading.Barrier(2)
    app.state.demo_booking_gateway.hook=lambda tool:barrier.wait(timeout=10) if tool=='create_demo_booking' else None
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses=list(pool.map(lambda _:confirm(c,h,base,qid),range(2)))
    assert [r.status_code for r in responses]==[200,200]
    assert responses[0].json()['booking']['id']==responses[1].json()['booking']['id']
    assert len(repo.state['demo_bookings'])==1
    assert len(repo.state['plans'][p['id']]['itinerary'])==1
    assert repo.state['plans'][p['id']]['revision']==2


def test_sdk_subprocess_parameters_exclude_provider_secrets_and_use_fixed_program(monkeypatch):
    from tagalong.demo_booking_gateway import DemoBookingGateway
    from contextlib import asynccontextmanager
    import sys
    monkeypatch.setenv('DATABASE_URL','synthetic-db-secret')
    monkeypatch.setenv('SUPABASE_SERVICE_ROLE_KEY','synthetic-provider-secret')
    @asynccontextmanager
    async def inspect(params):
        assert params.command==sys.executable
        assert params.args[0].endswith('demo_restaurant_server.py')
        assert params.env=={'PYTHONUNBUFFERED':'1'}
        raise RuntimeError('inspection complete')
        yield
    monkeypatch.setattr('tagalong.demo_booking_gateway.stdio_client',inspect)
    with pytest.raises(RuntimeError,match='inspection complete'):
        asyncio.run(DemoBookingGateway().call('create_demo_booking',{'quote_id':'synthetic'}))
