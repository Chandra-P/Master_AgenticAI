"""Private, owner-approved recipient snapshots. No email, directory lookup or AI calls."""
from fastapi import Depends
from fastapi.responses import JSONResponse
from pydantic import Field, StrictInt
from .core import access, fail, now, uid
from .groups import access_group
from .models import GroupSelection, Item, MAX_MEMBERS


class SharePlan(GroupSelection):
    expected_revision: StrictInt = Field(ge=1)


class RevokeGrant(Item):
    expected_revision: StrictInt = Field(ge=1)


def approve(state, actor, plan, group_id, group_revision):
    group=access_group(state,actor,group_id,group_revision)
    if group['archived']:fail(409,'Choose an active group')
    if plan['owner_id']!=actor.id:fail(403,'Only the plan owner can share')
    if any(plan['id'] in run['plan_ids'] for run in state.get('qa_runs',{}).values()):
        fail(409,'QA demonstration plans cannot be shared with a group')
    recipients=[m for m in group['members'] if m['id']!=group['ownerId'] and m.get('email')]
    if not recipients:fail(422,'Add at least one adult account email before sharing')
    grants=state.setdefault('plan_group_grants',{}).setdefault(plan['id'],{})
    emails={m['email'].strip().casefold() for m in recipients}
    if len(set(grants)|emails)>MAX_MEMBERS:fail(409,'Plan sharing recipient limit reached')
    pending={email for email,g in grants.items() if g['status']=='pending'}
    if len(state['members'][plan['id']])+len(pending|emails)>MAX_MEMBERS:fail(409,'Plan member capacity reached')
    if sum(len(items) for items in state['plan_group_grants'].values())+len(emails-set(grants))>100000:
        fail(503,'Plan sharing capacity reached')
    sequence=state.setdefault('plan_group_approvals',{}).get(plan['id'],0)+1
    state['plan_group_approvals'][plan['id']]=sequence
    for member in recipients:
        email=member['email'].strip().casefold()
        previous=grants.get(email)
        if previous and previous['status']=='claimed' and previous.get('user_id') in state['members'][plan['id']]:continue
        grants[email]={'id':previous['id'] if previous else uid(),'alias':member['preferredName'],
                       'color':member['color'],'status':'pending','approval':sequence,'approved_by':actor.id,'at':now()}
    from .plan_management import event
    event(state,actor,plan['id'],'share_group',group_id)


def redeem(state, actor):
    """Use only the current provider-verified identity, never cached actor emails."""
    if not actor.email_verified or not actor.email or actor.workspace_mode!='member':return
    email=actor.email.strip().casefold()
    for pid,grants in state.get('plan_group_grants',{}).items():
        grant=grants.get(email)
        if not grant or grant['status']!='pending' or pid in state.get('deleted_plans',{}):continue
        plan=state['plans'].get(pid)
        if not plan or any(pid in run['plan_ids'] for run in state.get('qa_runs',{}).values()):continue
        if state.get('suspended_users',{}).get(grant['approved_by']):continue
        if grant['approval']<=state.get('plan_group_blocks',{}).get(pid,{}).get(actor.id,0):continue
        members=state['members'][pid]
        if actor.id not in members:
            if len(members)>=MAX_MEMBERS:continue
            members.append(actor.id)
            plan['members'].append({'user_id':actor.id,'name':actor.name,'color':grant['color']})
            plan['revision']+=1
            from .notifications import notify
            notify(state,actor.id,pid)
        grant.update(status='claimed',user_id=actor.id)


def revoke_member_grants(state,pid,user_id):
    state.setdefault('plan_group_blocks',{}).setdefault(pid,{})[user_id]=state.get('plan_group_approvals',{}).get(pid,0)
    for grant in state.get('plan_group_grants',{}).get(pid,{}).values():
        if grant.get('user_id')==user_id:grant['status']='revoked'


def owner_grants(state,pid,actor):
    plan=access(state,pid,actor)
    if plan['owner_id']!=actor.id:fail(403,'Only the owner can manage group recipients')
    return plan,[{'id':g['id'],'alias':g['alias'],'status':g['status']} for g in state.get('plan_group_grants',{}).get(pid,{}).values()]


def install_plan_group_sharing(app,repo,actor):
    @app.get('/v1/plans/{pid}/group-sharing')
    def listing(pid:str,a=Depends(actor)):
        def read(state):
            plan,grants=owner_grants(state,pid,a)
            return {'plan_revision':plan['revision'],'recipients':grants}
        return JSONResponse(repo.transact(read),headers={'Cache-Control':'no-store'})

    @app.post('/v1/plans/{pid}/group-sharing')
    def share(pid:str,b:SharePlan,a=Depends(actor)):
        def change(state):
            plan,_=owner_grants(state,pid,a)
            if plan['revision']!=b.expected_revision:fail(409,'Plan changed; review recipients again')
            if not b.share_with_group or not b.group_id:fail(422,'Explicit group sharing approval is required')
            approve(state,a,plan,b.group_id,b.expected_group_revision)
            plan['revision']+=1
            return {'status':'shared','plan_revision':plan['revision']}
        return repo.transact(change)

    @app.delete('/v1/plans/{pid}/group-sharing/{grant_id}')
    def revoke(pid:str,grant_id:str,b:RevokeGrant,a=Depends(actor)):
        def change(state):
            plan,_=owner_grants(state,pid,a)
            if plan['revision']!=b.expected_revision:fail(409,'Plan changed; refresh recipients')
            grant=next((g for g in state.get('plan_group_grants',{}).get(pid,{}).values() if g['id']==grant_id),None)
            if not grant:fail(404,'Recipient not found')
            if grant['status']=='claimed':fail(409,'Use Remove access for an existing plan member')
            grant['status']='revoked';plan['revision']+=1
            from .plan_management import event
            event(state,a,pid,'revoke_group_recipient',grant_id)
            return {'status':'revoked','plan_revision':plan['revision']}
        return repo.transact(change)
