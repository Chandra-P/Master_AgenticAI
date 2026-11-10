from __future__ import annotations
import copy, uuid, threading, hashlib
from dataclasses import dataclass
from datetime import datetime, timezone, date
from fastapi import HTTPException

def uid(): return str(uuid.uuid4())
def now(): return datetime.now(timezone.utc).isoformat()
def fail(code, text): raise HTTPException(code, text)
@dataclass
class Actor:
    id: str
    email: str
    name: str
    display_name: str | None = None
    workspace_mode: str = 'member'
    email_verified: bool = False

def identity(data):
    email = data.get('email') or ''
    preferred=(data.get('user_metadata') or {}).get('display_name')
    preferred=' '.join(preferred.split())[:50] if isinstance(preferred,str) else None
    return Actor(data['id'], email, email.split('@')[0][:30]+'-'+hashlib.sha256(data['id'].encode()).hexdigest()[:10], preferred or None,
                 email_verified=bool(email and data.get('email_confirmed_at')))

class MemoryRepository:
    def __init__(self):
        self.state = {'plans':{}, 'members':{}, 'actors':{}, 'proposals':{}, 'sources':{}, 'jobs':{}}
        self.lock = threading.RLock()
    def health(self): return True
    def transact(self, fn):
        with self.lock:
            snapshot = copy.deepcopy(self.state)
            try:
                result=fn(self.state)
                from .decisions import reconcile
                reconcile(snapshot,self.state)
                from .coordination import track_activity
                track_activity(snapshot,self.state)
                return copy.deepcopy(result)
            except Exception:
                self.state = snapshot
                raise

def register(s,a):
    if s.get('suspended_users',{}).get(a.id): fail(403,'Account suspended. Contact the app administrator.')
    s['actors'][a.id] = {key:value for key,value in vars(a).items() if key!='workspace_mode'}

def visible(s,pid,a):
    if pid in s.get('deleted_plans',{}): return False
    qa=any(pid in run['plan_ids'] for run in s.get('qa_runs',{}).values())
    return a.id in s['members'].get(pid,[]) and (not qa or (a.workspace_mode=='admin' and a.id in s.get('app_admins',{})))
def access(s,pid,a):
    if s.get('suspended_users',{}).get(a.id): fail(403,'Account suspended. Contact the app administrator.')
    if pid not in s['plans'] or not visible(s,pid,a): fail(404,'Plan not found')
    return s['plans'][pid]
def view(s,p,a):
    p = copy.deepcopy(p)
    from .task_rules import distinct_task_records
    p['tasks']=distinct_task_records(p.get('tasks',[]))
    # This is server-derived identity, independent of editable display titles.
    p.pop('demo_template',None)
    story=s.get('demo_plan_stories',{}).get(p['id'])
    if story:p['demo_template']=story['template']
    for member in p['members']:
        preferred=s['actors'].get(member.get('user_id'),{}).get('display_name')
        if preferred: member['name']=preferred
    p['role'] = 'owner' if p['owner_id']==a.id else 'member'
    labels={x['label'] for x in p['preferences']}
    for proposal in s['proposals'].values():
        if proposal['plan_id']==p['id'] and proposal['status']=='pending' and proposal['label'] not in labels:
            p['preferences'].append({'label':proposal['label'],'confirmed':False}); labels.add(proposal['label'])
    return p

def source(s,pid,sid,title,text,deleted=False,kind='message'):
    key=pid+':'+sid
    old=s['sources'].get(key,{})
    item={'id':sid,'plan_id':pid,'title':title,'text':text,'version':old.get('version',0)+1,'deleted':deleted,'kind':old.get('kind','message') if deleted else kind,'chunks':max(old.get('chunks',1),(len(text)+5999)//6000,1)}
    s['sources'][key]=item
    job=uid(); s['jobs'][job]={'id':job,'source_key':key,'version':item['version'],'status':'pending','attempts':0,'lease_until':0}

def create(s,a,b):
    register(s,a); pid=uid()
    from .groups import plan_group
    group=plan_group(s,a,b.group_id,b.expected_group_revision)
    start=date.fromisoformat(b.start); end=date.fromisoformat(b.end)
    display=lambda d:f'{d:%b} {d.day}'+(f', {d.year}' if start.year!=end.year else '')
    date_label=display(start) if start==end else display(start)+' - '+display(end)
    options=[date_label,'Suggest another date range' if start!=end else 'Suggest another date']
    p={'id':pid,'title':b.title,'kind':b.kind,'location':'Location to decide','date':date_label,'start':b.start,'end':b.end,'budget':0,'image':'/images/coast.jpg' if b.kind=='trip' else '/images/restaurant.jpg','members':[{'name':a.name,'color':'#6366f1','user_id':a.id}], 'messages':[],'preferences':[],'polls':[{'id':uid(),'question':'Which date range works best?' if start!=end else 'Which date works best?','options':options,'votes':{},'datePoll':True}],'itinerary':[],'tasks':[],'revision':1,'owner_id':a.id}
    if group is not None:p['group']=group
    s['plans'][pid]=p; s['members'][pid]=[a.id]
    if b.share_with_group:
        from .plan_group_sharing import approve
        approve(s,a,p,b.group_id,b.expected_group_revision)
    return view(s,p,a)

def update(s,a,pid,incoming,revision):
    p=access(s,pid,a)
    if p['revision']!=revision: fail(409,'Plan changed; reload before retrying')
    if any(key in incoming for key in ('decisions','decision_state','finalization','finalized','score','comments')): fail(403,'Decision state is server-controlled')
    projected=view(s,p,a)
    if 'demo_template' in incoming and incoming['demo_template']!=projected.get('demo_template'):
        fail(403,'Demo identity is server-controlled')
    incoming={key:value for key,value in incoming.items() if key!='demo_template'}
    if incoming.get('role')!=projected['role']: fail(403,'Invalid role')
    if incoming.get('group')!=projected.get('group'):fail(403,'Server-controlled group snapshot')
    for key in ('id','owner_id','members','preferences'):
        if incoming.get(key)!=projected[key]: fail(403,'Server-controlled field: '+key)
    from .models import validate_snapshot, ValidationError
    try: validate_snapshot(incoming)
    except ValidationError: fail(422,'Invalid plan snapshot')
    reservation_ids={b['itinerary_entry_id'] for b in s.get('demo_bookings',{}).values() if b['plan_id']==pid}
    if [x for x in incoming.get('itinerary',[]) if x.get('id') in reservation_ids]!=[x for x in p['itinerary'] if x.get('id') in reservation_ids]:
        fail(403,'Reservation itinerary entries are server-controlled')
    old={m['id']:m for m in p['messages']}; proposed=incoming.get('messages',[])
    if len({m.get('id') for m in proposed})!=len(proposed): fail(422,'Duplicate message IDs')
    for mid,m in old.items():
        if m not in proposed: fail(403,'Existing messages cannot be changed')
    for m in proposed:
        if m.get('id') not in old:
            if 'simulation' in m: fail(403,'Simulation messages are server-controlled')
            if m.get('author')!=a.name or m.get('user_id')!=a.id or m.get('assistant') or m.get('sources'): fail(403,'Invalid message identity')
            if not isinstance(m.get('text'),str) or not m['text'].strip() or len(m['text'])>20000: fail(422,'Invalid message')
            source(s,pid,m['id'],'Chat: '+a.name,m['text'])
    oldpoll={x['id']:x for x in p['polls']}
    polls=incoming.get('polls',[])
    if len({x['id'] for x in polls})!=len(polls): fail(422,'Duplicate poll IDs')
    for poll in polls:
        prev=oldpoll.get(poll.get('id'),{'votes':{}})
        votes=poll.get('votes',{})
        if prev['votes'] and poll.get('options')!=prev.get('options'): fail(409,'Cannot change options after votes have been cast')
        if any(k!=a.name and votes.get(k)!=v for k,v in prev['votes'].items()) or any(k!=a.name and k not in prev['votes'] for k in votes): fail(403,'Cannot change another member vote')
        if any(type(v)!=int or v<0 or v>=len(poll.get('options',[])) for v in votes.values()): fail(422,'Invalid vote')
    for poll in p['polls']:
        if poll['id'] not in {x.get('id') for x in polls} and any(k!=a.name for k in poll['votes']): fail(403,'Cannot remove other votes')
    for key in ('title','location','date','start','end','budget','image','messages','polls','itinerary','tasks'):
        if key in incoming: p[key]=copy.deepcopy(incoming[key])
    if not isinstance(p['budget'],(int,float)) or p['budget']<0: fail(422,'Invalid budget')
    p['revision']+=1
    return view(s,p,a)









MUTABLE_PLAN_FIELDS = frozenset(('title','location','date','start','end','budget','image','messages','polls','itinerary','tasks'))


def patch_plan(s, actor, plan_id, patches, expected_revision):
    """Apply bounded data-only patches, then run the same invariants as PUT."""
    plan = access(s, plan_id, actor)
    if plan['revision'] != expected_revision:
        fail(409, 'Plan changed; reload before retrying')
    if not isinstance(patches, list) or not 1 <= len(patches) <= 200:
        fail(422, 'Provide between 1 and 200 patches')
    draft = view(s, plan, actor)
    for patch in patches:
        if not isinstance(patch, dict) or set(patch) - {'op','path','value'}:
            fail(422, 'Invalid patch object')
        op = patch.get('op')
        path = patch.get('path')
        if op not in ('add','replace','remove') or not isinstance(path,list) or not 1 <= len(path) <= 12:
            fail(422, 'Invalid patch operation or path')
        if any(type(part) not in (str,int) for part in path) or type(path[0]) is not str:
            fail(422, 'Patch paths require string keys and integer array indices')
        if path[0] not in MUTABLE_PLAN_FIELDS:
            fail(403, 'Server-controlled plan field')
        if op in ('add','replace') and 'value' not in patch:
            fail(422, 'Patch value is required')
        parent = draft
        for part in path[:-1]:
            if isinstance(parent, dict):
                if type(part) is not str or part not in parent:
                    fail(422, 'Patch object path does not exist')
                parent = parent[part]
            elif isinstance(parent, list):
                if type(part) is not int or not 0 <= part < len(parent):
                    fail(422, 'Invalid patch array index')
                parent = parent[part]
            else:
                fail(422, 'Patch path cannot traverse a scalar')
        key = path[-1]
        if isinstance(parent, dict):
            if type(key) is not str:
                fail(422, 'Object paths require string keys')
            if op == 'add':
                if key in parent: fail(422, 'Added object key already exists')
                parent[key] = copy.deepcopy(patch['value'])
            else:
                if key not in parent: fail(422, 'Patch object key does not exist')
                if op == 'replace': parent[key] = copy.deepcopy(patch['value'])
                else: del parent[key]
        elif isinstance(parent, list):
            if type(key) is not int or key < 0:
                fail(422, 'Array paths require nonnegative integer indices')
            if op == 'add':
                if key != len(parent): fail(422, 'Array additions must append at its length')
                parent.append(copy.deepcopy(patch['value']))
            else:
                if key >= len(parent): fail(422, 'Patch array index does not exist')
                if op == 'replace': parent[key] = copy.deepcopy(patch['value'])
                else: del parent[key]
        else:
            fail(422, 'Patch target parent must be an object or array')
    return update(s, actor, plan_id, draft, expected_revision)
