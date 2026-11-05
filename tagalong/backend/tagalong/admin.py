"""Server-owned app administration, independent of plan membership."""
from collections import Counter
from fastapi import Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, StrictBool, field_validator
from .core import fail, now, uid, view


def is_admin(state, actor):
    return actor.id in state.get('app_admins', {})


def require_admin(state, actor):
    if state.get('suspended_users', {}).get(actor.id): fail(403, 'Account suspended. Contact the app administrator.')
    if not is_admin(state, actor): fail(403, 'App administrator access required')


def audit(state, actor, action, target, reason):
    events=state.setdefault('admin_audit', [])
    if len(events)>=100000: fail(503, 'Audit capacity reached. Contact the operator.')
    event={'id':uid(),'at':now(),'actor_id':actor.id,'action':action,'target':target,'reason':reason}
    events.append(event)
    return event


class Reason(BaseModel):
    model_config=ConfigDict(extra='forbid')
    reason:str=Field(min_length=3,max_length=500)

    @field_validator('reason',mode='before')
    @classmethod
    def strip_reason(cls, value):
        return value.strip() if isinstance(value,str) else value


class Suspension(Reason):
    suspended:StrictBool


def install_admin(app, repo, actor):
    @app.get('/v1/admin/overview')
    def overview(offset:int=Query(0,ge=0),limit:int=Query(50,ge=1,le=100),a=Depends(actor)):
        def read(s):
            require_admin(s,a)
            plans=list(s['plans'].values())
            accounts=list(s['actors'].values())
            qa_ids={pid for run in s.get('qa_runs',{}).values() for pid in run['plan_ids']}
            return {
                'counts':{'plans':len(plans),'accounts':len(accounts),'qa_plans':len(qa_ids)},
                'plans':[{'id':p['id'],'title':p['title'],'owner_id':p['owner_id'],'members':len(s['members'].get(p['id'],[])),'revision':p['revision'],'qa':p['id'] in qa_ids} for p in plans[offset:offset+limit]],
                'accounts':[{'id':u['id'],'email':u['email'],'display_name':u.get('display_name') or u['name'],'app_admin':u['id'] in s.get('app_admins',{}),'suspended':bool(s.get('suspended_users',{}).get(u['id']))} for u in accounts[offset:offset+limit]],
                'jobs':dict(Counter(job['status'] for job in s['jobs'].values())),
                'audit':list(reversed(s.get('admin_audit',[])[-50:])),
                'offset':offset,'limit':limit,
            }
        return JSONResponse(repo.transact(read),headers={'Cache-Control':'no-store'})

    @app.post('/v1/admin/plans/{pid}/inspect')
    def inspect(pid:str,b:Reason,a=Depends(actor)):
        def read(s):
            require_admin(s,a)
            if pid not in s['plans']: fail(404,'Plan not found')
            event=audit(s,a,'inspect_plan',pid,b.reason)
            plan=view(s,s['plans'][pid],a)
            # Inspection is not a membership grant and has no editable plan role.
            plan['role']='admin_review'
            documents=[{'id':x['id'],'title':x['title'],'text':x['text']} for x in s['sources'].values() if x['plan_id']==pid and x.get('kind')=='document' and not x['deleted']]
            return {'plan':plan,'documents':documents,'audit_id':event['id']}
        return JSONResponse(repo.transact(read),headers={'Cache-Control':'no-store'})

    @app.post('/v1/admin/accounts/{user_id}/suspension')
    def suspend(user_id:str,b:Suspension,a=Depends(actor)):
        def change(s):
            require_admin(s,a)
            if user_id not in s['actors']: fail(404,'Account not found')
            if b.suspended and user_id in s.get('app_admins',{}): fail(409,'Administrators cannot be suspended here')
            audit(s,a,'suspend_account' if b.suspended else 'restore_account',user_id,b.reason)
            users=s.setdefault('suspended_users',{})
            if b.suspended: users[user_id]={'at':now(),'by':a.id}
            else: users.pop(user_id,None)
            return {'status':'suspended' if b.suspended else 'active'}
        return repo.transact(change)

    @app.post('/v1/admin/qa-plans')
    def qa(a=Depends(actor)):
        from .qa import seed_review_plans
        def seed(s):
            require_admin(s,a)
            return seed_review_plans(s,a)
        return repo.transact(seed)
