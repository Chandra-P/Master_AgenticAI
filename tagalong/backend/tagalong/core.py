from __future__ import annotations
import copy, uuid, threading, hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from fastapi import HTTPException

def uid(): return str(uuid.uuid4())
def now(): return datetime.now(timezone.utc).isoformat()
def fail(code, text): raise HTTPException(code, text)
@dataclass
class Actor:
    id: str
    email: str
    name: str

def identity(data):
    email = data.get('email') or ''
    return Actor(data['id'], email, email.split('@')[0][:30]+'-'+hashlib.sha256(data['id'].encode()).hexdigest()[:10])

class MemoryRepository:
    def __init__(self):
        self.state = {'plans':{}, 'members':{}, 'actors':{}, 'proposals':{}, 'sources':{}, 'jobs':{}}
        self.lock = threading.RLock()
    def transact(self, fn):
        with self.lock:
            snapshot = copy.deepcopy(self.state)
            try: return copy.deepcopy(fn(self.state))
            except Exception:
                self.state = snapshot
                raise

def register(s,a): s['actors'][a.id] = vars(a)
def access(s,pid,a):
    if pid not in s['plans'] or a.id not in s['members'].get(pid,[]): fail(404,'Plan not found')
    return s['plans'][pid]
def view(s,p,a):
    p = copy.deepcopy(p)
    p['role'] = 'owner' if p['owner_id']==a.id else 'member'
    labels={x['label'] for x in p['preferences']}
    for proposal in s['proposals'].values():
        if proposal['plan_id']==p['id'] and proposal['status']=='pending' and proposal['label'] not in labels:
            p['preferences'].append({'label':proposal['label'],'confirmed':False}); labels.add(proposal['label'])
    return p

def source(s,pid,sid,title,text,deleted=False):
    key=pid+':'+sid
    old=s['sources'].get(key,{})
    item={'id':sid,'plan_id':pid,'title':title,'text':text,'version':old.get('version',0)+1,'deleted':deleted,'chunks':max(old.get('chunks',1),(len(text)+5999)//6000,1)}
    s['sources'][key]=item
    job=uid(); s['jobs'][job]={'id':job,'source_key':key,'version':item['version'],'status':'pending','attempts':0,'lease_until':0}

def create(s,a,b):
    register(s,a); pid=uid()
    p={'id':pid,'title':b.title,'kind':b.kind,'location':'','date':b.start,'start':b.start,'end':b.end,'budget':0,'image':'','members':[{'name':a.name,'color':'#6366f1','user_id':a.id}], 'messages':[],'preferences':[],'polls':[],'itinerary':[],'tasks':[],'revision':1,'owner_id':a.id}
    s['plans'][pid]=p; s['members'][pid]=[a.id]
    return view(s,p,a)

def update(s,a,pid,incoming,revision):
    p=access(s,pid,a)
    from .models import validate_snapshot, ValidationError
    try: validate_snapshot(incoming)
    except ValidationError: fail(422,'Invalid plan snapshot')
    if p['revision']!=revision: fail(409,'Plan changed; reload before retrying')
    projected=view(s,p,a)
    if incoming.get('role')!=projected['role']: fail(403,'Invalid role')
    for key in ('id','owner_id','members','preferences'):
        if incoming.get(key)!=projected[key]: fail(403,'Server-controlled field: '+key)
    old={m['id']:m for m in p['messages']}; proposed=incoming.get('messages',[])
    if len({m.get('id') for m in proposed})!=len(proposed): fail(422,'Duplicate message IDs')
    for mid,m in old.items():
        if m not in proposed: fail(403,'Existing messages cannot be changed')
    for m in proposed:
        if m.get('id') not in old:
            if m.get('author')!=a.name or m.get('user_id')!=a.id or m.get('assistant') or m.get('sources'): fail(403,'Invalid message identity')
            if not isinstance(m.get('text'),str) or not m['text'].strip() or len(m['text'])>20000: fail(422,'Invalid message')
            source(s,pid,m['id'],'Chat: '+a.name,m['text'])
    oldpoll={x['id']:x for x in p['polls']}
    polls=incoming.get('polls',[])
    for poll in polls:
        prev=oldpoll.get(poll.get('id'),{'votes':{}})
        votes=poll.get('votes',{})
        if any(k!=a.name and votes.get(k)!=v for k,v in prev['votes'].items()) or any(k!=a.name and k not in prev['votes'] for k in votes): fail(403,'Cannot change another member vote')
        if any(type(v)!=int or v<0 or v>=len(poll.get('options',[])) for v in votes.values()): fail(422,'Invalid vote')
    for poll in p['polls']:
        if poll['id'] not in {x.get('id') for x in polls} and any(k!=a.name for k in poll['votes']): fail(403,'Cannot remove other votes')
    for key in ('title','location','date','start','end','budget','image','messages','polls','itinerary','tasks'):
        if key in incoming: p[key]=copy.deepcopy(incoming[key])
    if not isinstance(p['budget'],(int,float)) or p['budget']<0: fail(422,'Invalid budget')
    p['revision']+=1
    return view(s,p,a)



