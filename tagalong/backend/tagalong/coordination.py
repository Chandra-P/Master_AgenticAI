"""Demo-focused derived health and activity; no event-sourcing or new service."""
import copy,hashlib,json
from collections import Counter
from datetime import datetime,timezone,date
from .core import now,visible


def track_activity(before,state):
    if not state['plans']:return
    changed={pid for pid,p in state['plans'].items() if before['plans'].get(pid)!=p}
    changed.update(src['plan_id'] for key,src in state['sources'].items() if before['sources'].get(key)!=src)
    activity=state.setdefault('plan_activity',{})
    for pid in state['plans']:
        if pid in changed or pid not in activity:activity[pid]=now()


def documents(s,pid):
    return [x for x in s['sources'].values() if x['plan_id']==pid and not x['deleted'] and x.get('kind')=='document']


def fingerprint(s,pid):
    facts={'plan':s['plans'][pid],'documents':[(x['id'],x['version']) for x in documents(s,pid)],'reference_date':datetime.now(timezone.utc).date().isoformat()}
    return hashlib.sha256(json.dumps(facts,sort_keys=True).encode()).hexdigest()


def health(s,pid,clock=None):
    p=s['plans'][pid];current=clock or datetime.now(timezone.utc);today=current.date().isoformat()
    try:inactive=max(0,(current-datetime.fromisoformat(s.get('plan_activity',{}).get(pid,now()))).days)
    except (ValueError,TypeError):inactive=0
    names={s['actors'].get(m.get('user_id'),{}).get('name',m['name']) for m in p['members']}
    open_polls=[]
    for poll in p['polls']:
        votes=[v for name,v in poll['votes'].items() if name in names]
        counts=Counter(votes)
        tied=bool(counts) and len([v for v in counts.values() if v==max(counts.values())])>1
        if len(votes)<len(names) or not votes or tied:open_polls.append({'id':poll['id'],'question':poll['question'],'remaining':max(0,len(names)-len(votes)),'tied':tied})
    has_dates=bool(p.get('start') and p.get('end'))
    has_location=bool(p.get('location','').strip()) and not any(x in p.get('location','').lower() for x in ('to decide','somewhere together'))
    undone=[t['label'] for t in p['tasks'] if not t['done']]
    questions=[]
    if not has_dates:questions.append('Choose dates')
    if open_polls:questions.append('Resolve '+str(len(open_polls))+' open poll(s); leading votes are not confirmed decisions')
    if not has_location:questions.append('Choose a destination or meeting place')
    if p['budget']<=0:questions.append('Agree a working budget')
    if not p['itinerary']:questions.append('Build a draft itinerary')
    if undone:questions.append('Complete '+str(len(undone))+' remaining task(s)')
    completed=bool(has_dates and p['end']<today and not questions)
    if completed:status='COMPLETED'
    elif inactive>=7 and questions:status='STALLED'
    elif not has_dates:status='WAITING_FOR_DATE'
    elif open_polls:status='WAITING_FOR_VOTES'
    elif not has_location:status='WAITING_FOR_LOCATION'
    elif not questions:status='READY_TO_FINALIZE'
    else:status='ACTIVE'
    if completed:step,reason,tab='Review your experience','The dates have passed and recorded polls/tasks are resolved.','Planning board'
    elif not has_dates:step,reason,tab='Choose dates','Dates are needed before comparing options.','Polls'
    elif open_polls:step,reason,tab='Resolve the open polls',f"{sum(x['remaining'] for x in open_polls)} vote(s) remain, or a poll is tied.",'Polls'
    elif not has_location:step,reason,tab='Choose a destination','A destination is still missing.','Planning board'
    elif p['budget']<=0:step,reason,tab='Set a working budget','A spending limit will help narrow the options.','Planning board'
    elif not p['itinerary']:step,reason,tab='Build a draft itinerary','Turn your ideas into an outline for the group to review.','Itinerary'
    elif undone:step,reason,tab=undone[0],'There are unfinished planning tasks.','Planning board'
    else:step,reason,tab='Review and finalize the outline','Working details are filled in; confirm them together.','Planning board'
    if status=='STALLED':step='Resume planning: '+step;reason=f'This plan has had no recorded activity for {inactive} days. '+reason
    score=round(100*sum((has_dates,not open_polls,has_location,p['budget']>0,bool(p['itinerary']),not undone))/6)
    if status=='STALLED':score=max(0,score-20)
    return {'status':status,'health':score,'inactive_days':inactive,'next_step':step[:300],'reason':reason,'target_tab':tab,'open_polls':open_polls,'blockers':questions}


def context(s,pid):
    p=copy.deepcopy(s['plans'][pid]);trimmed=len(p['messages'])>35 or len(documents(s,pid))>4;p['messages']=p['messages'][-35:]
    for m in p['messages']:m['text']=m['text'][:1200];m.pop('sources',None)
    docs=[{'id':d['id'],'title':d['title'],'text':d['text'][:3000]} for d in documents(s,pid)[:4]]
    approved=[x['label'] for x in p['preferences'] if x['confirmed']]
    h=health(s,pid)
    p['preferences']=p['preferences'][:50]
    result={'plan':p,'documents':docs,'reference_date':datetime.now(timezone.utc).date().isoformat(),'approved_decisions':approved[:30],'health':h,'allowed_next_steps':[h['next_step']]+[x['label'][:300] for x in p['tasks'] if not x['done']][:12],'context_truncated':trimmed}
    for field in ('messages','polls','itinerary','tasks'):
        while len(json.dumps(result))>40000 and p[field]:p[field].pop(0);result['context_truncated']=True
    while len(json.dumps(result))>40000 and docs:docs.pop();result['context_truncated']=True
    while len(json.dumps(result))>40000:
        for container,key in ((h,'open_polls'),(p,'preferences'),(p,'members'),(result,'allowed_next_steps'),(result,'approved_decisions')):
            if len(container[key])>1:container[key].pop();result['context_truncated']=True;break
        else:raise ValueError('Coordination context exceeds its hard limit')
    return result


def snapshot(s,pid):
    h=health(s,pid);p=s['plans'][pid];cached=s.get('coordination',{}).get(pid,{})
    fresh=cached.get('source_fingerprint')==fingerprint(s,pid) and cached.get('status')==h['status']
    approved=[x['label'] for x in p['preferences'] if x['confirmed']]
    fallback=f"{p['title']}: {p['kind']} with {len(p['members'])} member(s). {len(p['messages'])} message(s), {len(documents(s,pid))} document(s) and {len(p['itinerary'])} draft itinerary item(s)."
    return {**h,'plan_id':pid,'plan_revision':p['revision'],'title':p['title'],'summary':cached.get('summary',fallback) if fresh else fallback,'decisions_made':[x for x in cached.get('decisions_made',approved) if x in approved] if fresh else approved,'open_questions':list(dict.fromkeys(h['blockers']+(cached.get('open_questions',[]) if fresh else [])))[:15],'activity_ideas':cached.get('activity_ideas',[]) if fresh else [],'ai_next_step':cached.get('next_step') if fresh else None,'ai_reason':cached.get('reason') if fresh else None,'provider_status':cached.get('provider_status','pending') if fresh else 'pending','stale':not fresh,'generated_at':cached.get('generated_at') if fresh else None,'last_activity_at':s.get('plan_activity',{}).get(pid)}
