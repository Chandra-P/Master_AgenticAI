"""Versioned human decisions in the existing transactional JSON repository."""
import copy
import json
import math
from collections import Counter
from typing import Literal
from fastapi import Depends
from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictBool, field_validator
from .core import access, fail, now, source, uid


class Revision(BaseModel):
    model_config=ConfigDict(extra='forbid')
    expected_revision: StrictInt=Field(ge=1)

class Version(Revision):
    expected_version: StrictInt=Field(ge=1)

class Options(BaseModel):
    options:list[str]=Field(max_length=12)
    @field_validator('options')
    @classmethod
    def labels(cls,value):
        if any(not x.strip() or len(x)>300 for x in value) or len(set(x.strip().casefold() for x in value))!=len(value):
            raise ValueError('Options must be unique nonempty labels of at most 300 characters')
        return [x.strip() for x in value]

class Propose(Revision,Options):
    title:str=Field(min_length=1,max_length=120,pattern=r'\S')
    category:str=Field(min_length=1,max_length=60,pattern=r'\S')
    required:StrictBool=True

class Edit(Version):
    title:str|None=Field(default=None,min_length=1,max_length=120,pattern=r'\S')
    required:StrictBool|None=None
    options:list[str]|None=None
    @field_validator('options')
    @classmethod
    def labels(cls,value):
        if value is not None:return Options(options=value).options
        return value

class Respond(Version):
    option_id:str|None=Field(default=None,max_length=128)
    response:Literal['support','can_live_with','object','abstain']

class Comment(Version):
    text:str=Field(min_length=1,max_length=2000,pattern=r'\S')

class Confirm(Version):
    option_id:str=Field(min_length=1,max_length=128)

class Finalize(Revision):
    idempotency_key:str=Field(min_length=1,max_length=128)
    reviewed:StrictBool


def new_decision(pid,title,category,required,labels,members):
    return {'id':uid(),'planId':pid,'title':title,'category':category,'required':required,'status':'needs_options','version':1,
            'options':[{'id':uid(),'label':label,'sourceIds':[]} for label in labels], 'eligibleMemberIds':list(members),
            'ballots':[],'selectedOptionId':None,'confirmation':None}


def ensure(s,pid):
    records=s.setdefault('decision_state',{})
    if pid not in records:
        p=s['plans'][pid];trip=p['kind']=='trip'
        defaults=[('Destination' if trip else 'Place','destination' if trip else 'place',p.get('location')),
                  ('Dates' if trip else 'Date and time','dates',p.get('date')),('Budget','budget','USD '+str(p['budget'])+' per person' if p.get('budget',0)>0 else None)]
        if trip:defaults.append(('Lodging','lodging',None))
        defaults.append(('Activities' if trip else 'Activity or meal','activities',', '.join(x.get('title','') for x in p.get('itinerary',[]))[:300] or None))
        decisions=[]
        for title,category,label in defaults:
            labels=[label] if label and not any(x in label.lower() for x in ('to decide','somewhere together')) else []
            decisions.append(new_decision(pid,title,category,True,labels,s['members'][pid]))
        records[pid]={'decisions':decisions,'comments':[],'finalization':None,'last_activity_at':s.get('plan_activity',{}).get(pid),'engaged':False,'idempotency':{}}
    return records[pid]


def ballots(d):
    return [b for b in d['ballots'] if b['decisionVersion']==d['version'] and b['memberId'] in d['eligibleMemberIds']]


def consent(d,option):
    votes=ballots(d)
    return bool(d['eligibleMemberIds']) and len(votes)==len(d['eligibleMemberIds']) and any(b['response'] in ('support','can_live_with') for b in votes) and all(b['response']=='abstain' or (b['response'] in ('support','can_live_with') and b['optionId']==option) for b in votes)


def status(d):
    if d['confirmation']:return 'confirmed'
    if not d['options']:return 'needs_options'
    if any(consent(d,o['id']) for o in d['options']):return 'ready_to_confirm'
    votes=ballots(d)
    if any(b['response']=='object' for b in votes) or len(votes)==len(d['eligibleMemberIds']):return 'needs_discussion'
    return 'reopened' if d.get('reopened') and not votes else 'awaiting_responses'


def snapshot(s,pid,a):
    p=access(s,pid,a);record=ensure(s,pid)
    decisions=copy.deepcopy(record['decisions'])
    for d in decisions:d['status']=status(d)
    contributions=[]
    for d in decisions:
        if not d['required']:continue
        if d['confirmation']:contributions.append(1);continue
        votes=ballots(d);abstain=sum(b['response']=='abstain' for b in votes)
        counts=Counter(b['optionId'] for b in votes if b['response'] in ('support','can_live_with'))
        denominator=len(d['eligibleMemberIds'])-abstain
        contributions.append(max(counts.values(),default=0)/denominator if denominator and d['options'] else 0)
    finalized=bool(record['finalization'])
    score=100 if finalized else min(99,math.floor(100*sum(contributions)/len(contributions)+0.5)) if contributions else 0
    return {'plan_id':pid,'plan_revision':p['revision'],'decisions':decisions,'comments':copy.deepcopy(record['comments'][-200:]),'comment_counts':dict(Counter(c['decisionId'] for c in record['comments'])),'score':score,'finalized':finalized,'finalization':copy.deepcopy(record['finalization']),'last_activity_at':record['last_activity_at']}


def evidence(s,pid,d):
    source(s,pid,'decision-'+d['id'],'Decision: '+d['title'],json.dumps({**d,'status':status(d)},ensure_ascii=False),kind='decision')


def invalidate(record,d):
    d['version']+=1;d['ballots']=[];d['confirmation']=None;d['selectedOptionId']=None;d['reopened']=True
    record['finalization']=None


def reconcile(before,s):
    """Called inside every repository transaction, including invitations and admin changes."""
    fields=('title','kind','location','date','start','end','budget','owner_id')
    for pid,record in s.get('decision_state',{}).items():
        old=before.get('plans',{}).get(pid);p=s['plans'].get(pid)
        if not old or not p:continue
        def outline(state,plan):
            reservation_ids={b['itinerary_entry_id'] for b in state.get('demo_bookings',{}).values() if b['plan_id']==pid}
            return [entry for entry in plan.get('itinerary',[]) if entry.get('id') not in reservation_ids]
        changed=outline(before,old)!=outline(s,p) or before.get('members',{}).get(pid)!=s['members'].get(pid) or any(old.get(k)!=p.get(k) for k in fields)
        if changed:
            for d in record['decisions']:
                invalidate(record,d);d['eligibleMemberIds']=list(s['members'][pid]);evidence(s,pid,d)
            record['last_activity_at']=now()


def context(s,pid):
    record=s.get('decision_state',{}).get(pid)
    if not record:return {'decisions':[],'comments':[],'finalized':False,'context_truncated':False}
    result={'decisions':[{**{key:copy.deepcopy(d[key]) for key in ('id','title','version','required','options','eligibleMemberIds','ballots','selectedOptionId','confirmation')},'status':status(d),
                         'sourceId':'decision-'+d['id'] if pid+':decision-'+d['id'] in s['sources'] else None} for d in record['decisions'][:20]],
            'comments':[{**c,'text':c['text'][:500]} for c in record['comments'][-12:]],'finalized':bool(record['finalization']),'context_truncated':len(record['comments'])>12}
    while len(json.dumps(result))>10000 and result['comments']:
        result['comments'].pop(0);result['context_truncated']=True
    while len(json.dumps(result))>10000 and result['decisions']:
        result['decisions'].pop();result['context_truncated']=True
    return result


def install_decisions(app,repo,actor,ai=None):
    @app.get('/v1/plans/{pid}/decisions')
    def get(pid:str,a=Depends(actor)):return repo.transact(lambda s:snapshot(s,pid,a))

    def command(s,pid,a,b,did=None,owner=False):
        p=access(s,pid,a)
        if owner and p['owner_id']!=a.id:fail(403,'Only the owner can perform this decision action')
        if p['revision']!=b.expected_revision:fail(409,'Plan changed; reload before retrying')
        record=ensure(s,pid);d=None
        if did:
            d=next((d for d in record['decisions'] if d['id']==did),None)
            if not d:fail(404,'Decision not found')
            if d['version']!=b.expected_version:fail(409,'Decision changed; reload before retrying')
        return p,record,d

    def finish(s,pid,a,p,record,d=None):
        p['revision']+=1;record['last_activity_at']=now();record['engaged']=True
        if d:evidence(s,pid,d)
        return snapshot(s,pid,a)

    @app.post('/v1/plans/{pid}/decisions')
    def propose(pid:str,b:Propose,a=Depends(actor)):
        def change(s):
            p,r,_=command(s,pid,a,b,owner=True)
            if len(r['decisions'])>=20:fail(409,'Decision limit reached')
            d=new_decision(pid,b.title,b.category,b.required,b.options,s['members'][pid]);r['decisions'].append(d);r['finalization']=None
            return finish(s,pid,a,p,r,d)
        return repo.transact(change)

    @app.patch('/v1/plans/{pid}/decisions/{did}')
    def edit(pid:str,did:str,b:Edit,a=Depends(actor)):
        def change(s):
            p,r,d=command(s,pid,a,b,did,True)
            if not any(getattr(b,k) is not None for k in ('title','required','options')):fail(422,'Provide a decision change')
            invalidate(r,d)
            if b.title is not None:d['title']=b.title
            if b.required is not None:d['required']=b.required
            if b.options is not None:d['options']=[{'id':uid(),'label':x,'sourceIds':[]} for x in b.options]
            return finish(s,pid,a,p,r,d)
        return repo.transact(change)

    @app.put('/v1/plans/{pid}/decisions/{did}/response')
    def respond(pid:str,did:str,b:Respond,a=Depends(actor)):
        def change(s):
            p,r,d=command(s,pid,a,b,did)
            if a.id not in d['eligibleMemberIds']:fail(403,'Not an eligible member')
            if b.response=='abstain':
                if b.option_id is not None:fail(422,'Abstention has no option')
            elif b.option_id not in {o['id'] for o in d['options']}:fail(422,'Choose a current option')
            d['confirmation']=None;d['selectedOptionId']=None;r['finalization']=None
            d['ballots']=[x for x in d['ballots'] if x['memberId']!=a.id]+[{'memberId':a.id,'optionId':b.option_id,'response':b.response,'decisionVersion':d['version'],'updatedAt':now()}]
            return finish(s,pid,a,p,r,d)
        return repo.transact(change)

    @app.get('/v1/plans/{pid}/decisions/{did}/comments')
    def comments(pid:str,did:str,offset:int=0,limit:int=50,a=Depends(actor)):
        def read(s):
            access(s,pid,a);r=ensure(s,pid)
            if not any(d['id']==did for d in r['decisions']):fail(404,'Decision not found')
            if offset<0 or not 1<=limit<=100:fail(422,'Invalid comment page')
            return [c for c in r['comments'] if c['decisionId']==did][offset:offset+limit]
        return repo.transact(read)

    @app.post('/v1/plans/{pid}/decisions/{did}/comments')
    def comment(pid:str,did:str,b:Comment,a=Depends(actor)):
        def change(s):
            p,r,d=command(s,pid,a,b,did)
            if len(r['comments'])>=2000:fail(409,'Comment limit reached')
            c={'id':uid(),'planId':pid,'decisionId':did,'authorId':a.id,'decisionVersion':d['version'],'text':b.text.strip(),'createdAt':now()};r['comments'].append(c)
            source(s,pid,'comment-'+c['id'],'Comment: '+d['title'],json.dumps(c),kind='decision_comment')
            return finish(s,pid,a,p,r)
        return repo.transact(change)

    @app.post('/v1/plans/{pid}/decisions/{did}/confirm')
    def confirm(pid:str,did:str,b:Confirm,a=Depends(actor)):
        def change(s):
            p,r,d=command(s,pid,a,b,did,True)
            if b.option_id not in {o['id'] for o in d['options']} or not consent(d,b.option_id):fail(409,'Every eligible member must respond with compatible consent and no objections')
            d['selectedOptionId']=b.option_id;d['confirmation']={'by':a.id,'at':now(),'decisionVersion':d['version']};r['finalization']=None
            return finish(s,pid,a,p,r,d)
        return repo.transact(change)

    @app.post('/v1/plans/{pid}/decisions/{did}/reopen')
    def reopen_decision(pid:str,did:str,b:Version,a=Depends(actor)):
        def change(s):
            p,r,d=command(s,pid,a,b,did,True);invalidate(r,d)
            return finish(s,pid,a,p,r,d)
        return repo.transact(change)

    @app.post('/v1/plans/{pid}/finalize')
    def finalize(pid:str,b:Finalize,a=Depends(actor)):
        def change(s):
            p=access(s,pid,a)
            if p['owner_id']!=a.id:fail(403,'Only the owner can finalize')
            r=ensure(s,pid);saved=r['idempotency'].get(b.idempotency_key)
            if saved:
                if saved['request']!=b.model_dump():fail(409,'Idempotency key already used for another snapshot')
                if r['finalization']!=saved['result']['finalization'] or p['revision']!=saved['result']['plan_revision']:fail(409,'Finalized snapshot changed')
                return copy.deepcopy(saved['result'])
            command(s,pid,a,b,owner=True)
            required=[d for d in r['decisions'] if d['required']]
            if not b.reviewed or not required or any(not d['confirmation'] or not consent(d,d['selectedOptionId']) for d in required):fail(409,'Review the outline and confirm all required decisions first')
            if any(b['response']=='object' for d in r['decisions'] for b in ballots(d)):fail(409,'Resolve outstanding objections first')
            r['finalization']={'by':a.id,'at':now(),'planRevision':p['revision']+1,'decisionVersions':{d['id']:d['version'] for d in r['decisions']}}
            result=finish(s,pid,a,p,r)
            if len(r['idempotency'])>=100:fail(409,'Finalization retry limit reached')
            r['idempotency'][b.idempotency_key]={'request':b.model_dump(),'result':copy.deepcopy(result)}
            return result
        return repo.transact(change)

    @app.post('/v1/plans/{pid}/reopen')
    def reopen(pid:str,b:Revision,a=Depends(actor)):
        def change(s):
            p,r,_=command(s,pid,a,b,owner=True);r['finalization']=None
            return finish(s,pid,a,p,r)
        return repo.transact(change)

    from .decision_summaries import install_decision_summaries
    install_decision_summaries(app,repo,actor,ai)
