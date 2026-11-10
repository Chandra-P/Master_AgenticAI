"""Owner-only transfer and reversible access deletion (retained admin records)."""
from fastapi import Depends
from pydantic import BaseModel, ConfigDict, Field, StrictInt
from .core import access, fail, now, source, uid, view


class Revision(BaseModel):
    model_config=ConfigDict(extra='forbid')
    expected_revision:StrictInt=Field(ge=1)


class Transfer(Revision):
    user_id:str=Field(min_length=1,max_length=128)


class Delete(Revision):
    confirmation:str=Field(min_length=1,max_length=200)


def owner(s,pid,a,revision):
    p=access(s,pid,a)
    if p['owner_id']!=a.id:fail(403,'Only the owner can manage this plan')
    if p['revision']!=revision:fail(409,'Plan changed; reload before retrying')
    return p


def event(s,a,pid,action,target=''):
    events=s.setdefault('plan_events',[])
    if len(events)>=100000:fail(503,'Plan event capacity reached. Contact the administrator.')
    events.append({'id':uid(),'at':now(),'actor_id':a.id,'plan_id':pid,'action':action,'target':target})


def install_plan_management(app,repo,actor):
    @app.post('/v1/plans/{pid}/owner')
    def transfer(pid:str,b:Transfer,a=Depends(actor)):
        def change(s):
            p=owner(s,pid,a,b.expected_revision)
            if b.user_id==a.id or b.user_id not in s['members'][pid]:fail(422,'Choose another existing plan member')
            if s.get('suspended_users',{}).get(b.user_id):fail(409,'Cannot transfer to a suspended account')
            if any(pid in run['plan_ids'] for run in s.get('qa_runs',{}).values()) and b.user_id not in s.get('app_admins',{}):fail(422,'QA review plans require an administrator as owner')
            p['owner_id']=b.user_id;p['revision']+=1
            for grant in s.get('plan_group_grants',{}).get(pid,{}).values():
                if grant['status']=='pending':grant['status']='revoked'
            s.setdefault('invitations',{}).pop(pid,None)
            event(s,a,pid,'transfer_owner',b.user_id)
            return view(s,p,a)
        return repo.transact(change)

    @app.delete('/v1/plans/{pid}')
    def delete(pid:str,b:Delete,a=Depends(actor)):
        def remove(s):
            if pid in s.get('deleted_plans',{}):
                if s['plans'][pid]['owner_id']!=a.id:fail(404,'Plan not found')
                return {'status':'deleted'}
            p=owner(s,pid,a,b.expected_revision)
            if b.confirmation!=p['title']:fail(422,'Type the exact plan name to confirm deletion')
            event(s,a,pid,'delete_plan')
            s.setdefault('deleted_plans',{})[pid]={'at':now(),'by':a.id}
            s.setdefault('invitations',{}).pop(pid,None)
            for item in list(s['sources'].values()):
                if item['plan_id']==pid and not item['deleted']:source(s,pid,item['id'],item['title'],'',True)
            p['revision']+=1
            return {'status':'deleted'}
        return repo.transact(remove)
