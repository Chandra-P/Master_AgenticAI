"""An explicitly fictional walkthrough saved under ordinary plan authorization."""
from fastapi import Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal
from .core import access, create, fail, register, source, view
from .models import Create


class DemoPlanRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    template: Literal['austin-four-friends']
    idempotency_key: str = Field(min_length=1, max_length=128, pattern=r'^[A-Za-z0-9_-]+$')


def story_data(pid):
    sources = [
        {'id':'demo-constraints','title':'Fictional demo · four friends’ constraints','text':'Alex proposes Austin, April 16–18, 2027. Maya prefers vegetarian food. Sam wants a fictional USD 650 per-person ceiling. Jordan prefers a relaxed pace and asks the group to verify step-free access. These are synthetic adult aliases and fictional needs.'},
        {'id':'demo-discussion','title':'Fictional demo · conflict and compromise','text':'Alex: “Austin, April 9–11, with a busy central hotel and late music?” Sam: “I cannot do April 9 and the fictional hotel estimate exceeds my ceiling.” Maya: “A barbecue-only dinner leaves me out; please compare a vegetarian candidate.” Jordan: “I prefer a relaxed schedule; can we verify step-free access?” Alex: “April 16–18 works instead.” Scripted assistant: “demo-constraints records the cost ceiling, vegetarian preference and pace needs. demo-discussion records the date conflict. Compare April 16–18, a lower modeled lodging allowance, Bouldin Creek Cafe as a meal candidate and an optional boardwalk walk. Verify actual provider details.” Sam: “That revised fictional budget works.” Maya: “I support the shared meal candidate, pending menu and seating checks.” Jordan: “I support the optional walk, pending route checks.” Alex: “I can live with a quieter evening.” The scripted compromise uses Lone Star Court as a lodging candidate. No actual prices or access guarantees are implied.'},
        {'id':'demo-official-links','title':'Fictional demo · official reference links','text':'Reference pages checked November 6, 2026: Lone Star Court https://www.lonestarcourt.com/ ; Bouldin Creek Cafe https://bouldincreekcafe.com/ ; Austin trail and boardwalk https://www.austintexas.gov/parks/locations/ann-and-roy-butler-hike-and-bike-trail-and-boardwalk-lady-bird-lake . These links do not establish future availability, prices, accessibility, reservations or an endorsement.'},
    ]
    cast = [{'name':name,'color':color} for name,color in [('Alex','#ec8677'),('Maya','#7b9270'),('Sam','#8583b3'),('Jordan','#6b98b4')]]
    choices = [
        {'category':'Destination','label':'Austin, Texas','url':'https://www.austintexas.gov/','estimate':None,'image':'/images/coast.jpg'},
        {'category':'Dates','label':'April 16–18, 2027','estimate':None},
        {'category':'Lodging','label':'Lone Star Court · proposed stay','url':'https://www.lonestarcourt.com/','estimate':300,'image':'/images/forest.jpg'},
        {'category':'Restaurant','label':'Bouldin Creek Cafe · proposed shared meal','url':'https://bouldincreekcafe.com/','estimate':35,'image':'/images/restaurant.jpg'},
        {'category':'Activity','label':'Lady Bird Lake trail and boardwalk · flexible walk','url':'https://www.austintexas.gov/parks/locations/ann-and-roy-butler-hike-and-bike-trail-and-boardwalk-lady-bird-lake','estimate':0,'image':'/images/forest.jpg'},
    ]
    comparisons = [
        (['Austin','San Antonio','Postpone the trip'],'Austin is the fictional cast’s shared preference after comparing travel effort. Travel costs and availability remain unverified.',{'Alex':'support','Maya':'support','Sam':'can_live_with','Jordan':'support'}),
        (['April 9–11, 2027','April 16–18, 2027','May 7–9, 2027'],'Sam cannot join April 9. In the scripted discussion all four report April 16–18 works; no actual calendars were checked.',{'Alex':'support','Maya':'support','Sam':'support','Jordan':'support'}),
        (['Busy central hotel · fictional USD 430 allowance','Lone Star Court candidate · fictional USD 300 allowance','Separate stays · fictional USD 280 allowance'],'A USD 300 modeled lodging allowance fits the story budget and keeps the group together. This is not a venue rate or a claim about transport or accessibility.',{'Alex':'can_live_with','Maya':'support','Sam':'support','Jordan':'support'}),
        (['Barbecue-only meal concept','Bouldin Creek Cafe candidate','Separate meals'],'The cast prefers one shared meal after Maya raises a vegetarian need. Verify the actual current menu, dietary requirements, hours and seating directly.',{'Alex':'can_live_with','Maya':'support','Sam':'support','Jordan':'support'}),
        (['Packed all-day activity schedule','Optional Lady Bird Lake walk and rest','Skip the group activity'],'Jordan’s pace objection leads to an optional walk with rest time. The route and step-free access still need provider checks; the fictional zero allowance is not a researched price.',{'Alex':'can_live_with','Maya':'support','Sam':'support','Jordan':'support'}),
    ]
    for choice, (alternatives, reason, votes) in zip(choices, comparisons):
        choice.update(alternatives=alternatives,reason=reason,votes=votes,sourceIds=['demo-constraints','demo-discussion'])
    milestones = [
        {'id':'idea','title':'1. Four friends initiate a weekend','text':'Alex opens a plan: “Could we meet in Austin for April 16–18?” Maya, Sam and Jordan join this fictional conversation. The real saved plan grants access only to your account.','sourceIds':['demo-constraints']},
        {'id':'preferences','title':'2. Needs become shared evidence','text':'Maya: “A vegetarian dinner matters to me.” Sam: “Let’s model a USD 650 ceiling.” Jordan: “Please keep the pace relaxed and verify step-free access.” The constraints note captures the discussion for retrieval.','sourceIds':['demo-constraints']},
        {'id':'conflict','title':'3. A disagreement surfaces','text':'Alex favors a packed central-city schedule. Sam objects to cost and Jordan to the pace. The group pauses selection instead of treating silence as consent.','sourceIds':['demo-discussion']},
        {'id':'options','title':'4. Scripted AI uses the saved notes','text':'Scripted assistant: “The constraints note asks for vegetarian food, a cost ceiling and a relaxed pace. The discussion note records objections to cost and rushing. Compare a lodging candidate, one vegetarian meal and an optional walk; verify transport and accessibility.” This is a transparent retrieval illustration, not a live model execution.','sourceIds':['demo-constraints','demo-discussion','demo-official-links'],'ai':True},
        {'id':'votes','title':'5. Four fictional responses','text':'First round: Alex supports the busy central option; Sam objects on cost, Jordan objects on pace, Maya can live with it. After discussion the revised relaxed option receives four supportive fictional responses. These votes belong only to this story.','sourceIds':['demo-discussion'],'votes':{'Alex':'Support relaxed option','Maya':'Support relaxed option','Sam':'Support revised budget','Jordan':'Support flexible pace'}},
        {'id':'consensus','title':'6. The friends select a shared outline','text':'The cast selects Austin, April 16–18, Lone Star Court as the lodging candidate, Bouldin Creek Cafe as the restaurant candidate, and a flexible boardwalk walk. Fictional estimates: lodging USD 300, meals USD 120, transport USD 100 and contingency USD 130 per person; total USD 650. These are demonstration arithmetic, not researched prices.','sourceIds':['demo-constraints','demo-discussion']},
        {'id':'itinerary','title':'7. A final story itinerary, ready for human checks','text':'The fictional story ends with the three-day outline below. The actual plan’s decisions remain unconfirmed until real members respond and the owner reviews them. Nobody has booked, paid, sent invitations or changed a calendar.','sourceIds':['demo-discussion','demo-official-links']},
    ]
    days = [
        {'date':'2027-04-16','title':'Friday · arrive and reconnect','items':[{'time':'3:00 PM','title':'Arrive and verify lodging arrangements','location':'Lone Star Court · candidate only','image':'/images/forest.jpg'},{'time':'6:30 PM','title':'Shared vegetarian dinner candidate','location':'Bouldin Creek Cafe · confirm hours and seating','image':'/images/restaurant.jpg'}]},
        {'date':'2027-04-17','title':'Saturday · a little exploring, plenty of room','items':[{'time':'10:00 AM','title':'Flexible trail and boardwalk walk','location':'Lady Bird Lake · verify route and step-free access','image':'/images/coast.jpg'},{'time':'1:00 PM','title':'Unscheduled lunch and rest','location':'Choose together on the day','image':'/images/restaurant.jpg'},{'time':'5:00 PM','title':'Optional music or a quiet evening','location':'Group chooses after checking energy and budget','image':'/images/forest.jpg'}]},
        {'date':'2027-04-18','title':'Sunday · an easy goodbye','items':[{'time':'9:00 AM','title':'Breakfast and shared expense review','location':'Choose together · fictional estimates only','image':'/images/restaurant.jpg'},{'time':'11:00 AM','title':'Verify checkout and head home','location':'Confirm actual provider checkout terms','image':'/images/coast.jpg'}]},
    ]
    return {'planId':pid,'template':'austin-four-friends','scripted':True,'title':'Four friends, one Austin weekend','disclosure':'Fictional walkthrough · scripted AI and votes · no bookings','cast':cast,'sources':sources,'choices':choices,'milestones':milestones,'days':days,'referenceDate':'2026-11-06'}


def create_demo_plan(state, actor, body):
    register(state, actor)
    keys = state.setdefault('demo_plan_keys', {})
    key = actor.id+':'+body.idempotency_key
    if key in keys:
        plan = access(state, keys[key], actor)
        return view(state, plan, actor)
    # Repeated clicks with a new browser key still reuse this owner's saved template.
    for pid, story in state.get('demo_plan_stories', {}).items():
        plan = state['plans'].get(pid)
        if plan and plan.get('owner_id') == actor.id and story['template'] == body.template and pid not in state.get('deleted_plans', {}):
            return view(state, access(state, pid, actor), actor)
    created = create(state, actor, Create(title='DEMO · Four friends, one Austin weekend', kind='trip', start='2027-04-16', end='2027-04-18'))
    pid = created['id']; plan = state['plans'][pid]
    story = story_data(pid)
    plan.update(location='Austin, Texas', budget=650)
    plan['messages'] = [{'id':'demo-story-introduction','author':'Fictional demo narrator','text':'Fictional demo: Alex, Maya, Sam and Jordan plan an Austin weekend. Open View demo story to replay the scripted conversation, source evidence, illustrative votes and itinerary. No real participant responses or bookings are represented here.','time':'Demo story','assistant':False}]
    plan['tasks'] = [{'label':label,'done':False} for label in ['Verify real prices, availability and cancellation terms','Confirm step-free access and travel times with providers','Replace fictional estimates with reviewed costs','Invite real participants and collect their own responses']]
    plan['itinerary'] = [{'id':'demo-story-'+str(index),'title':'DEMO · '+item['title'],'time':item['time'],'day':day['date'],'category':'Fictional walkthrough · illustrative photo','location':item['location'],'image':item['image']} for index,(day,item) in enumerate((day,item) for day in story['days'] for item in day['items'])]
    photos = [
        ('Lone Star Court','https://www.lonestarcourt.com/','https://valenciacollection.b-cdn.net/wp-content/uploads/sites/6/2026/09/ls-hero.jpg'),
        ('Bouldin Creek Cafe','https://bouldincreekcafe.com/','https://static.spotapps.co/spots/70/ea739e1c294c98808954e4a9162ef1/:original'),
        ('Lady Bird Lake','https://www.austintexas.gov/parks/locations/ann-and-roy-butler-hike-and-bike-trail-and-boardwalk-lady-bird-lake','https://austin.widen.net/content/73fc83a3-6ed9-4e07-9b7c-a6a7ab0d48ac/web/Boardwalk_GO_pier.jpg'),
    ]
    for item in plan['itinerary']:
        for marker, website, image in photos:
            if marker in item['location'] or marker in item['title']:
                item.update(image=image,source_url=website,image_source_url=website,category='Fictional walkthrough · source photo')
                break
    for item in story['sources']:
        source(state,pid,item['id'],item['title'],item['text'],kind='document')
    state.setdefault('demo_plan_stories', {})[pid] = story
    keys[key] = pid
    return view(state,plan,actor)


def install_demo_plans(app, repo, actor):
    @app.post('/v1/demo-plans')
    def make_demo(body: DemoPlanRequest, current=Depends(actor)):
        return JSONResponse(repo.transact(lambda state:create_demo_plan(state,current,body)),headers={'Cache-Control':'no-store'})

    @app.get('/v1/plans/{pid}/demo-story')
    def get_demo(pid: str, current=Depends(actor)):
        def read(state):
            access(state,pid,current)
            story = state.get('demo_plan_stories', {}).get(pid)
            if not story: fail(404,'Demo story not found')
            return story
        return JSONResponse(repo.transact(read),headers={'Cache-Control':'no-store'})
