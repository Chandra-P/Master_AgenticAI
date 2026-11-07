"""Explicit test-only ASGI factory for browser tests. Never import from production code."""
from tagalong.app import create_app
from tagalong.core import MemoryRepository, Actor
from tests.test_workflows import FakeAI

def app_factory():
    repo=MemoryRepository()
    repo.state['app_admins']={'alice':{'granted_by':'explicit_test_fixture'}}
    accounts={'test-alice':Actor('alice','alice@example.test','alice'),'test-bob':Actor('bob','bob@example.test','bob'),'test-carol':Actor('carol','carol@example.test','carol')}
    def authenticate(token):
        from tagalong.core import fail
        if token not in accounts: fail(401,'Invalid test session')
        return accounts[token]
    class BrowserAI(FakeAI):
        def retrieve(self,pid,query):
            # Emulate vector retrieval only for sources whose current version
            # has actually completed the test fixture's indexing job.
            def hits(s):
                indexed={(job.get('source_key'),job.get('version')) for job in s['jobs'].values() if job.get('status')=='done'}
                return [{'id':x['id'],'version':x['version']} for x in s['sources'].values() if x['plan_id']==pid and not x['deleted'] and (pid+':'+x['id'],x['version']) in indexed]
            return repo.transact(hits)
        def assess_group_fit(self,option,evidence):
            note=next((x for x in evidence if '_source_id' in x),None)
            return {'verdict':'needs_info','summary':'Review the saved group constraints and verify the proposed venue details.','matches':[{'text':'The option can be compared with the saved group notes.','source_ids':[note['id']]}] if note else [],'conflicts':[],'unknowns':['Confirm current menu details directly with the venue.']}
        def assess_research_options(self,options,evidence,facts):
            notes=[item for item in evidence if item['id'].startswith('saved:')]
            if not notes:
                return [{'option_id':option['id'],'verdict':'needs_info','summary':'Add a group preference to personalize this comparison.','matches':[],'conflicts':[],'unknowns':['No saved group preference was retrieved.']} for option in options]
            return [{'option_id':option['id'],'verdict':'fits','summary':'This option matches a saved group preference for vegetarian food.','matches':[{'text':'The group note records vegetarian food as a preference.','source_ids':[notes[0]['id'],option['source_ids'][0]]}],'conflicts':[],'unknowns':['Confirm current menu and allergen details directly with the restaurant.']} for option in options]
        def generate_plan(self,prompt,today):
            return {'title':'Austin weekend draft','type':'trip','location':'Austin','start':None,'end':None,'participant_count':4,'suggested_tasks':['Confirm attendees','Choose lodging'],'suggested_itinerary':[{'title':'Draft neighborhood walk','time':'Afternoon','category':'Draft idea','location':'Austin — route to decide'}],'suggested_budget':{'amount':350,'basis':'per_person','currency':'USD','notes':'From the test request, not a price quote'},'open_questions':['Confirm travel dates']}
        def coordinate(self,context):
            return {'summary':'The group is planning '+context['plan']['title']+'. Working details and unresolved choices are tracked below.','decisions_made':context['approved_decisions'],'open_questions':context['health']['blockers'][:5],'next_step':context['health']['next_step'],'reason':context['health']['reason'],'activity_ideas':[]}
        def answer(self,plan,message,resolve_sources):
            self.matches=repo.transact(lambda state:[{'id':src['id'],'version':src['version']} for src in state['sources'].values() if src['plan_id']==plan['id'] and src.get('kind')=='document' and not src['deleted']])
            return super().answer(plan,message,resolve_sources)
    class BrowserPlaces:
        def search(self,query,location,category):
            if category=='events':return [{'title':'Synthetic Music Night','url':'https://events.example.test/music-night','snippet':'Synthetic Music Night May 15, 2027'}]
            return [{'id':'synthetic-restaurant','kind':'place','title':'Synthetic vegetarian restaurant','url':'https://places.example.test/restaurant','snippet':'Synthetic public source snippet for browser verification.','address':'10 Test Street','location':location,'category':'Food & drink','image':'https://places.example.test/restaurant.jpg','image_source_url':'https://places.example.test/restaurant','map_url':'https://www.google.com/maps/search/?api=1&query=Synthetic+restaurant'}]
        def fetch_page(self,row):return {**row,'content':'Synthetic Music Night May 15, 2027. This is a synthetic official organizer fixture.'}
    app=create_app(repo,authenticate,BrowserAI(),places=BrowserPlaces())
    app.state.city_event_extractor=lambda *args:[{'source_id':'event-source:1','kind':'event','official':True,'name':'Synthetic Music Night','raw_date':'May 15, 2027','date':'2027-05-15'}]
    class BrowserTyping:
        def complete(self,draft,context):
            return ' together.'
    app.state.typing_provider=BrowserTyping()
    return app
