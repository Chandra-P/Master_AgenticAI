"""Structured planning drafts and bounded proactive in-app coordination."""
import time
from collections import Counter
from datetime import datetime,timezone,date
from fastapi import BackgroundTasks,Depends
from fastapi.responses import JSONResponse
from .core import access,create,update,view,visible,uid,now,fail
from .models import Create
from .coordination_models import Generate,AcceptDraft,PlanDraft,SummaryOutput,RecommendationOutput
from .coordination import context,fingerprint,health,snapshot


def refresh(repo,a,pid,ai,token):
    try:
        def read(s):
            access(s,pid,a)
            return fingerprint(s,pid),context(s,pid)
        version,facts=repo.transact(read)
        if not ai or not hasattr(ai,'coordinate'):raise ValueError('Provider not configured')
        result=ai.coordinate(facts)
        summary=SummaryOutput.model_validate({key:result[key] for key in ('summary','decisions_made','open_questions')}).model_dump()
        recommendation=RecommendationOutput.model_validate({**{key:result[key] for key in ('next_step','reason')},'activity_ideas':result.get('activity_ideas',[])}).model_dump()
        recommendation['activity_ideas']=[x for x in recommendation['activity_ideas'] if all(label in facts['approved_decisions'] for label in x['preference_labels'])]
        summary['decisions_made']=[x for x in summary['decisions_made'] if x in facts['approved_decisions']]
        if recommendation['next_step'] not in facts['allowed_next_steps']:
            recommendation={**{key:facts['health'][key] for key in ('next_step','reason')},'activity_ideas':recommendation['activity_ideas']}
        record={**summary,**recommendation,'provider_status':'live','generated_at':now()}
    except Exception:
        version=None;record=None
    def save(s):
        lease=s.get('coordination_leases',{}).get(pid)
        if not lease or lease['token']!=token:return
        s['coordination_leases'].pop(pid,None)
        try:access(s,pid,a)
        except Exception:return
        current=fingerprint(s,pid)
        if version is not None and version!=current:return
        if record is None:
            fallback=snapshot(s,pid)
            record_to_save={key:fallback[key] for key in ('summary','decisions_made','open_questions','next_step','reason')}
            record_to_save.update(provider_status='unavailable',generated_at=now())
        else:record_to_save=record
        s.setdefault('coordination',{})[pid]={**record_to_save,'source_fingerprint':current,'plan_revision':s['plans'][pid]['revision'],**{key:health(s,pid)[key] for key in ('status','health')},'last_activity_at':s.get('plan_activity',{}).get(pid)}
    try:repo.transact(save)
    except Exception:pass


def reserve(s,a,pid):
    access(s,pid,a)
    cache=s.get('coordination',{}).get(pid,{})
    current=fingerprint(s,pid)
    if cache.get('source_fingerprint')==current and cache.get('status')==health(s,pid)['status'] and cache.get('provider_status')=='live':return None
    clock=time.time();lease=s.get('coordination_leases',{}).get(pid,{})
    if lease.get('until',0)>clock:return None
    attempts=s.setdefault('coordination_attempts',{})
    if clock-attempts.get(pid,0)<15:return None
    budget=s.setdefault('coordination_budget',{});bucket=int(clock//3600)
    record=budget.get(a.id,{'bucket':bucket,'count':0})
    if record['bucket']!=bucket:record={'bucket':bucket,'count':0}
    if record['count']>=60:return None
    record['count']+=1;budget[a.id]=record;attempts[pid]=clock
    token=uid();s.setdefault('coordination_leases',{})[pid]={'token':token,'until':clock+120}
    return token


def install_coordination(app,repo,actor,ai):
    @app.post('/v1/plans/generate')
    def generate(b:Generate,a=Depends(actor)):
        if abs((date.fromisoformat(b.local_date)-datetime.now(timezone.utc).date()).days)>1:fail(422,'Refresh the local reference date and retry')
        if not ai or not hasattr(ai,'generate_plan'):fail(503,'AI plan generation is unavailable. You can still create a plan manually.')
        def allowance(s):
            limits=s.setdefault('draft_limits',{});bucket=int(time.time()//3600);record=limits.get(a.id,{'bucket':bucket,'count':0})
            if record['bucket']!=bucket:record={'bucket':bucket,'count':0}
            if record['count']>=30:fail(429,'Plan generation limit reached. Please try later or create a plan manually.')
            record['count']+=1;limits[a.id]=record
        repo.transact(allowance)
        try:draft=PlanDraft.model_validate(ai.generate_plan(b.prompt,b.local_date)).model_dump()
        except Exception:fail(502,'AI could not produce a valid plan draft. Please retry or create a plan manually.')
        def save(s):
            from .core import register
            register(s,a)
            records=s.setdefault('plan_drafts',{})
            for key in list(records):
                if records[key]['expires_at']<time.time():del records[key]
            did=uid();records[did]={'owner_id':a.id,'draft':draft,'prompt':b.prompt,'expires_at':time.time()+1800,'created_plan_id':None}
            return {'draft_id':did,'draft':draft,'mode':'live','notice':'AI draft. Review dates, budget and activities before creating a shared plan.'}
        return JSONResponse(repo.transact(save),headers={'Cache-Control':'no-store'})

    @app.post('/v1/plans/from-draft')
    def accept(b:AcceptDraft,a=Depends(actor)):
        def save(s):
            item=s.get('plan_drafts',{}).get(b.draft_id)
            if not item or item['owner_id']!=a.id or item['expires_at']<time.time():fail(404,'Draft not found or expired; generate a new one')
            if item['created_plan_id']:return view(s,access(s,item['created_plan_id'],a),a)
            d=PlanDraft.model_validate(item['draft'])
            p=create(s,a,Create(title=b.title,kind=b.kind,start=b.start,end=b.end))
            p['location']=b.location;p['budget']=b.budget_per_person or 0
            p['messages']=[{'id':uid(),'author':a.name,'user_id':a.id,'text':'Planning idea: '+item.get('prompt',b.title),'time':now()}]
            p['tasks']=[{'label':x,'done':False} for x in d.suggested_tasks]
            p['itinerary']=[{'id':uid(),**activity.model_dump()} for activity in d.suggested_itinerary]
            saved=update(s,a,p['id'],p,p['revision']);item['created_plan_id']=p['id']
            return saved
        return repo.transact(save)

    @app.get('/v1/plans/{pid}/coordination')
    def coordination(pid:str,background:BackgroundTasks,a=Depends(actor)):
        def read(s):
            access(s,pid,a);token=reserve(s,a,pid)
            result=snapshot(s,pid)
            return result,token
        result,token=repo.transact(read)
        if token:background.add_task(refresh,repo,a,pid,ai,token)
        return JSONResponse(result,headers={'Cache-Control':'no-store'})

    @app.get('/v1/coordination/overview')
    def overview(background:BackgroundTasks,a=Depends(actor)):
        def read(s):
            ids=[pid for pid in s['plans'] if visible(s,pid,a)]
            ids.sort(key=lambda pid:s.get('plan_activity',{}).get(pid,''),reverse=True)
            cards=[snapshot(s,pid) for pid in ids[:30]]
            insights=Counter()
            for pid in ids:
                insights.update({x['label'] for x in s['plans'][pid]['preferences'] if x['confirmed']})
            jobs=[]
            for pid in ids[:30]:
                if len(jobs)>=3:break
                token=reserve(s,a,pid)
                if token:jobs.append((pid,token))
            return {'plans':cards,'group_insights':[{'label':label,'plan_count':count} for label,count in insights.most_common(8)],'notice':'Insights use explicitly confirmed preferences in your accessible plans. Health is rule-based, not AI confidence.'},jobs
        result,jobs=repo.transact(read)
        for pid,token in jobs:background.add_task(refresh,repo,a,pid,ai,token)
        return JSONResponse(result,headers={'Cache-Control':'no-store'})
