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


DIALOGUE_VERSION=2


def demo_dialogue(story):
    """Replay fictional adults and cited scripted assistance, never real account actions."""
    scenes=[
        ('1 · Start the weekend plan',[
            ('Alex','Could the four of us take a weekend trip? I vote Austin: food, a little music, and time together.'),
            ('Maya','I am interested. Let us compare a couple of places before we lock anything in.'),
            ('Sam','Yes, but I need a ceiling on the whole weekend, not just the hotel.'),
            ('Jordan','Count me in if we leave room to rest. I do not want a race between attractions.'),
            ('Tagalong','This is a fictional planning conversation. I will lay out choices and record objections; the real account owner still controls all actual decisions.'),
        ]),
        ('2 · Destination and dates',[
            ('Alex','Destination choices: Austin, San Antonio, or postpone. My first date choice is April 9–11, 2027; April 16–18 and May 7–9 are alternatives.'),
            ('Sam','I object to April 9–11: I cannot join that weekend. April 16–18 works. I can live with Austin if the numbers work.'),
            ('Maya','Austin and April 16–18 both work for this fictional plan. I prefer that to postponing.'),
            ('Jordan','April 16–18 works for me too. I support Austin, with a calmer schedule.'),
            ('Alex','I can move the trip a week. Austin, April 16–18 is my revised proposal.'),
            ('Tagalong','The saved discussion records Sam’s date objection. All four have now named April 16–18 as workable in the script; no real calendars were checked.'),
        ]),
        ('3 · Needs and budget conflict',[
            ('Alex','What about a central hotel, a big Saturday tour, and late music? I modeled USD 430 each for lodging and USD 780 overall.'),
            ('Sam','I object to that budget. USD 650 per person is my fictional ceiling, including meals, travel, and a cushion.'),
            ('Maya','I need vegetarian meal choices. A barbecue-only dinner would leave me out, even if everyone else likes it.'),
            ('Jordan','I object to the packed tour and late-night default. Please also verify step-free access; we cannot assume a route or hotel will work.'),
            ('Tagalong','The constraints note records USD 650, vegetarian food, a relaxed pace, and an access check. I suggest comparing lower lodging allowances, one shared meal, and optional activities. Those are proposed compromises, not verified venue suitability.'),
            ('Alex','Fair. I can trade the central hotel and mandatory late night for a weekend we can all join.'),
        ]),
        ('4 · Compare three lodging options',[
            ('Tagalong','Three scripted lodging alternatives: busy central hotel with a USD 430 allowance; Lone Star Court candidate with USD 300; or separate stays with USD 280. These are fictional budget allowances, not researched room prices.'),
            ('Alex','I initially support the busy central hotel, but I can live with the Lone Star Court candidate if we check transport.'),
            ('Sam','I object to the USD 430 allowance. I support the USD 300 candidate: lodging 300, meals 120, transport 100, contingency 130 totals 650.'),
            ('Maya','I support staying together rather than splitting up. The USD 300 lodging allowance works for the story.'),
            ('Jordan','I support the shared candidate, pending actual step-free access and travel-time checks. The name alone proves neither.'),
            ('Tagalong','Recorded compromise: Lone Star Court is the lodging candidate; Alex can live with it and the others support it. Its linked website is a reference, not proof of price, availability, or access.'),
        ]),
        ('5 · Compare three meal options',[
            ('Alex','For dinner: barbecue-only, Bouldin Creek Cafe as a shared candidate, or separate meals. My first choice was barbecue.'),
            ('Maya','I object to barbecue-only. I support comparing Bouldin Creek Cafe so the shared meal includes my vegetarian preference.'),
            ('Sam','I support the shared cafe candidate with a fictional USD 35 meal allowance inside the USD 120 meals budget.'),
            ('Jordan','I support that candidate if we check seating, access, and hours. I would rather eat together than split up.'),
            ('Tagalong','The saved constraints support the need for vegetarian choices, and the discussion records the objection. The cafe is a candidate to verify directly; this script does not certify dietary safety, current menu, or seating.'),
            ('Alex','I can live with the shared cafe. Let us verify the actual menu instead of assuming the restaurant label settles it.'),
        ]),
        ('6 · Activity pace and alternatives',[
            ('Alex','Activity choices: a packed all-day schedule, an optional Lady Bird Lake walk with rest, or skip a group activity. I initially preferred the full day.'),
            ('Jordan','I object to the full day. I support the flexible walk only if we verify a suitable route and can opt out without pressure.'),
            ('Maya','I support the optional walk and rest. That leaves time for our shared meal.'),
            ('Sam','I support the flexible plan with a fictional zero activity allowance. We still need to check any real transport or activity costs.'),
            ('Tagalong','The pace objection is recorded in the discussion note. The revised option is a flexible walk and rest; Alex can live with it. The official trail link does not establish step-free access or a researched zero price.'),
        ]),
        ('7 · Final responses and selection recap',[
            ('Alex','My final story responses: support Austin and April 16–18; can live with Lone Star Court, the shared cafe, and the flexible walk. I withdraw my earlier hotel and pace proposals.'),
            ('Maya','I support all five revised choices, pending direct menu and provider checks. Keeping the meal shared resolves my objection.'),
            ('Sam','I can live with Austin and support the revised dates, lodging, meal, and activity. The modeled USD 650 total resolves my cost objection; it is not a quote.'),
            ('Jordan','I support the revised five choices, with rest and an access-check task. My support is for this fictional outline, not a guarantee about any venue.'),
            ('Tagalong','Scripted selections: Austin, April 16–18, Lone Star Court lodging candidate, Bouldin Creek Cafe meal candidate, and an optional Lady Bird Lake walk. Friday arrival and dinner; Saturday flexible exploring and rest; Sunday breakfast and departure.'),
            ('Tagalong','These are fictional responses, not real ballots or finalization. The actual owner must review real costs, availability, dietary needs, transport and access, collect actual member responses, and arrange any booking personally. Nothing was booked, paid, invited, or sent.'),
        ]),
    ]
    citations=[{k:item[k] if k!='text' else item[k][:6000] for k in ('id','title','text')} for item in story['sources']]
    messages=[]
    for scene,turns in scenes:
        for author,text in turns:
            message={'id':'demo-scene-'+str(len(messages)).zfill(3),'author':author,'text':text,'time':'Scene '+scene,'assistant':author=='Tagalong','simulation':True}
            if author=='Tagalong':message['sources']=citations
            messages.append(message)
    return messages


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
    initial_votes=[
        {'Alex':'support','Maya':'support','Sam':'can_live_with','Jordan':'can_live_with'},
        {'Alex':'support','Maya':'can_live_with','Sam':'object','Jordan':'can_live_with'},
        {'Alex':'support','Maya':'can_live_with','Sam':'object','Jordan':'object'},
        {'Alex':'support','Maya':'object','Sam':'can_live_with','Jordan':'can_live_with'},
        {'Alex':'support','Maya':'can_live_with','Sam':'object','Jordan':'object'},
    ]
    for index,(choice, (alternatives, reason, votes)) in enumerate(zip(choices, comparisons)):
        choice.update(alternatives=alternatives,reason=reason,votes=votes,sourceIds=['demo-constraints','demo-discussion'])
        choice['rounds']=[
            {'title':'Initial proposal','option':alternatives[0],'votes':initial_votes[index],'resolution':'Compare objections before selecting a shared outline.','sourceIds':['demo-constraints','demo-discussion']},
            {'title':'Revised fictional responses','option':choice['label'],'votes':votes,'resolution':reason,'sourceIds':['demo-constraints','demo-discussion']},
        ]
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
    story={'planId':pid,'template':'austin-four-friends','scripted':True,'dialogueVersion':DIALOGUE_VERSION,'title':'Four friends, one Austin weekend','disclosure':'Fictional walkthrough · scripted AI and votes · no bookings','cast':cast,'sources':sources,'choices':choices,'milestones':milestones,'days':days,'referenceDate':'2026-11-06'}
    sources[1]['text']='Fictional scripted conversation; no actual participant responses or provider execution.\n'+'\n'.join(m['time']+' — '+m['author']+': '+m['text'] for m in demo_dialogue(story))
    return story


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
    plan['messages'] = demo_dialogue(story)
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


def upgrade_demo_plan(state,actor,pid):
    """Explicit owner-operated transcript upgrade; preserve real replies and decisions."""
    plan=access(state,pid,actor)
    if plan['owner_id']!=actor.id:fail(403,'Only the owner can upgrade the demo story')
    previous=state.get('demo_plan_stories',{}).get(pid)
    if not previous or previous.get('template')!='austin-four-friends':fail(404,'Demo story not found')
    if previous.get('dialogueVersion',0)>=DIALOGUE_VERSION:return view(state,plan,actor)
    story=story_data(pid)
    history=list(previous.get('previousLiveChecks',[]))
    if previous.get('liveCheck') is not None:history.append(previous['liveCheck'])
    if history:story['previousLiveChecks']=history
    def old_script(message):
        if message.get('user_id'):return False
        if message.get('id')=='demo-story-introduction' and message.get('author')=='Fictional demo narrator':return True
        return message.get('simulation') is True and message.get('id','').startswith('demo-scene-') and message.get('author') in {'Alex','Maya','Sam','Jordan','Tagalong'}
    real_messages=[m for m in plan['messages'] if not old_script(m)]
    from .models import MAX_MESSAGES
    transcript=demo_dialogue(story)
    if len(transcript)+len(real_messages)>MAX_MESSAGES:fail(409,'The upgraded demo would exceed the message limit')
    plan['messages']=transcript+real_messages
    for item in story['sources']:source(state,pid,item['id'],item['title'],item['text'],kind='document')
    state['demo_plan_stories'][pid]=story
    plan['revision']+=1
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
