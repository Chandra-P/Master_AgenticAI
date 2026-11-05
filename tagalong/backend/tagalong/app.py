import os, copy, time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, StrictInt
from typing import Literal
from dataclasses import replace
from .core import *

from .models import Create, AssistantOutput, MAX_MESSAGES, MAX_PREFERENCES, MAX_MEMBERS
class Update(BaseModel):
    plan:dict; expected_revision:int
class PatchRequest(BaseModel):
    expected_revision:StrictInt
    patches:list[dict]=Field(min_length=1,max_length=200)
class Chat(BaseModel):
    message:str=Field(min_length=1,max_length=10000)
class Share(BaseModel):
    email:str=Field(min_length=3,max_length=320)
class AcceptInvitation(BaseModel):
    token:str=Field(pattern=r'^[A-Za-z0-9_-]{43}$')
class Document(BaseModel):
    title:str=Field(min_length=1,max_length=200); text:str=Field(min_length=1,max_length=100000); content_type:Literal['text/plain']='text/plain'

def create_app(repo=None,authenticate=None,ai=None,places=None):
    from .places import KeenableSearch
    if places is None: places=KeenableSearch()
    embedded_enabled=os.getenv('TAGALONG_EMBEDDED_WORKER','false').strip().lower()=='true'
    @asynccontextmanager
    async def lifespan(application):
        runner=None
        if embedded_enabled and repo is not None and authenticate is not None and ai is not None:
            from .worker import EmbeddedWorker
            runner=EmbeddedWorker(repo,ai)
            application.state.ingestion_worker=runner
            runner.start()
        try:
            yield
        finally:
            if runner is not None:
                runner.stop()
    app=FastAPI(title='Tagalong API',lifespan=lifespan)
    app.state.ingestion_worker=None
    app.add_middleware(CORSMiddleware,allow_origins=[x for x in os.getenv('CORS_ORIGINS','http://localhost:3000').split(',') if x],allow_methods=['GET','POST','PUT','PATCH','DELETE'],allow_headers=['Authorization','Content-Type','X-Workspace-Mode'])
    if repo is None and os.getenv('DATABASE_URL'):
        from .repository import PostgresRepository
        repo=PostgresRepository(os.environ['DATABASE_URL'])
    if authenticate is None and os.getenv('SUPABASE_URL') and os.getenv('SUPABASE_SERVICE_ROLE_KEY'):
        from .providers import SupabaseAuth
        authenticate=SupabaseAuth(os.environ['SUPABASE_URL'],os.environ['SUPABASE_SERVICE_ROLE_KEY'])
    if ai is None and all(os.getenv(k) for k in ('OPENAI_API_KEY','PINECONE_API_KEY','PINECONE_INDEX_HOST')):
        from .providers import ConnectedAI
        ai=ConnectedAI()
    def actor(authorization:str|None=Header(default=None),workspace_mode:Literal['member','admin']=Header(default='member',alias='X-Workspace-Mode')):
        if not authorization or not authorization.startswith('Bearer '): fail(401,'Bearer session required')
        if not authenticate or not repo: fail(503,'Connected service is not configured')
        a=replace(authenticate(authorization[7:]),workspace_mode=workspace_mode)
        def authorize(s):
            register(s,a)
            if workspace_mode=='admin' and a.id not in s.get('app_admins',{}): fail(403,'App administrator access required')
        repo.transact(authorize)
        return a
    @app.get('/health')
    def health():
        ready=bool(repo and authenticate and repo.health())
        status='ok' if ready else ('unavailable' if repo and authenticate else 'unconfigured')
        runner=app.state.ingestion_worker
        return JSONResponse(status_code=200 if ready else 503,content={'assistant_citation_policy':'evidence-only','assistant_diagnostics':1,'status':status,'mode':'connected','indexing_mode':'embedded' if embedded_enabled else 'external','indexing_worker_running':bool(runner and runner.is_alive()),'capabilities':{'plans':ready,'assistant':bool(ai and ready),'documents':ready,'places':bool(places and ready),'calendar':False}})
    @app.get('/v1/me')
    def me(a=Depends(actor)):
        from .admin import is_admin
        return {**vars(a),'app_admin':repo.transact(lambda s:is_admin(s,a))}
    @app.get('/v1/plans')
    def plans(a=Depends(actor)): return repo.transact(lambda s:[view(s,p,a) for pid,p in s['plans'].items() if visible(s,pid,a)])
    @app.post('/v1/plans')
    def make(b:Create,a=Depends(actor)): return repo.transact(lambda s:create(s,a,b))
    @app.get('/v1/plans/{pid}')
    def get(pid:str,a=Depends(actor)): return repo.transact(lambda s:view(s,access(s,pid,a),a))
    @app.put('/v1/plans/{pid}')
    def put(pid:str,b:Update,a=Depends(actor)): return repo.transact(lambda s:update(s,a,pid,b.plan,b.expected_revision))
    @app.patch('/v1/plans/{pid}')
    def patch(pid:str,b:PatchRequest,a=Depends(actor)):
        return repo.transact(lambda s:patch_plan(s,a,pid,b.patches,b.expected_revision))
    @app.post('/v1/plans/{pid}/members')
    def share(pid:str,b:Share,a=Depends(actor)):
        def check(s):
            if access(s,pid,a)['owner_id']!=a.id: fail(403,'Only owner can share')
        repo.transact(check)
        target=authenticate.find(b.email) if hasattr(authenticate,'find') else repo.transact(lambda s:next((Actor(**v) for v in s['actors'].values() if v['email'].casefold()==b.email.casefold()),None))
        if not target: fail(404,'Account not found. Ask them to register, confirm their email, and sign in once, or share a private join link.')
        def add(s):
            check(s); p=access(s,pid,a); register(s,target)
            if target.id not in s['members'][pid]:
                if len(s['members'][pid])>=MAX_MEMBERS: fail(409,'Plan member limit reached')
                s['members'][pid].append(target.id); p['members'].append({'name':target.name,'user_id':target.id,'color':'#14b8a6'}); p['revision']+=1
            return {'status':'added'}
        return repo.transact(add)
    @app.post('/v1/plans/{pid}/invitation')
    def invitation(pid:str,a=Depends(actor)):
        from .invitations import issue
        return JSONResponse(repo.transact(lambda s:issue(s,pid,a)),headers={'Cache-Control':'no-store'})
    @app.delete('/v1/plans/{pid}/invitation')
    def disable_invitation(pid:str,a=Depends(actor)):
        from .invitations import revoke
        return repo.transact(lambda s:revoke(s,pid,a))
    @app.post('/v1/invitations/accept')
    def accept_invitation(b:AcceptInvitation,a=Depends(actor)):
        from .invitations import accept
        def throttle(s):
            bucket=int(time.time()//60)
            limits=s.setdefault('invitation_limits',{})
            for key in list(limits):
                if limits[key]['bucket']!=bucket: del limits[key]
            record=limits.get(a.id,{'bucket':bucket,'count':0})
            if record['count']>=20: fail(429,'Too many join attempts. Retry next minute.')
            record['count']+=1; limits[a.id]=record
        repo.transact(throttle)
        return repo.transact(lambda s:accept(s,b.token,a))
    @app.delete('/v1/plans/{pid}/members/{user_id}')
    def remove_member(pid:str,user_id:str,a=Depends(actor)):
        def remove(s):
            p=access(s,pid,a)
            if p['owner_id']!=a.id: fail(403,'Only owner can remove members')
            if user_id==p['owner_id']: fail(409,'The owner cannot be removed')
            if user_id not in s['members'][pid]: fail(404,'Member not found')
            s['members'][pid].remove(user_id)
            p['members']=[m for m in p['members'] if m.get('user_id')!=user_id]
            p['revision']+=1
            return {'status':'removed'}
        return repo.transact(remove)
    @app.get('/v1/plans/{pid}/proposals')
    def proposals(pid:str,a=Depends(actor)):
        def read(s):
            access(s,pid,a); return [p for p in s['proposals'].values() if p['plan_id']==pid]
        return repo.transact(read)
    @app.post('/v1/plans/{pid}/proposals/{proposal_id}/confirm')
    def confirm(pid:str,proposal_id:str,a=Depends(actor)):
        def apply(s):
            p=access(s,pid,a); proposal=s['proposals'].get(proposal_id)
            if not proposal or proposal['plan_id']!=pid: fail(404,'Proposal not found')
            if proposal['status']=='pending':
                if not any(x['label']==proposal['label'] for x in p['preferences']): p['preferences'].append({'label':proposal['label'],'confirmed':True})
                proposal['status']='confirmed'; proposal['confirmed_by']=a.id; p['revision']+=1
            return view(s,p,a)
        return repo.transact(apply)
    @app.post('/v1/plans/{pid}/assistant')
    def assistant(pid:str,b:Chat,a=Depends(actor)):
        plan=repo.transact(lambda s:copy.deepcopy(access(s,pid,a)))
        if not ai: fail(503,'AI providers are not configured')
        def charge(s):
            access(s,pid,a)
            limits=s.setdefault('assistant_limits',{})
            bucket=int(time.time()//60); record=limits.get(a.id,{'bucket':bucket,'count':0})
            if record['bucket']!=bucket: record={'bucket':bucket,'count':0}
            if record['count']>=10: fail(429,'Assistant request limit reached; retry next minute')
            record['count']+=1; limits[a.id]=record
        repo.transact(charge)
        try:
            def resolve_sources(matches):
                def evidence(s):
                    access(s,pid,a)
                    verified=[]
                    for hit in matches[:6]:
                        src=s['sources'].get(pid+':'+hit['id'])
                        if src and not src['deleted'] and src['version']==hit.get('version') and src['plan_id']==pid:
                            item=copy.deepcopy(src); chunk=max(0,int(hit.get('chunk',0)))
                            item['text']=item['text'][chunk*6000:(chunk+1)*6000]; verified.append(item)
                    return verified
                return repo.transact(evidence)
            answer=ai.dispatch_assistant if hasattr(ai,'dispatch_assistant') else ai.answer
            output,sources=answer(plan,b.message,resolve_sources)
            output=AssistantOutput.model_validate(output).model_dump()
            if not set(output['source_ids']).issubset({src['id'] for src in sources}): raise ValueError('Unverified citation')
            cited=[src for src in sources if src['id'] in output.get('source_ids',[])]
        except HTTPException: raise
        except Exception as error:
            from .ai_failures import assistant_failure
            fail(502,assistant_failure(error))
        def save(s):
            p=access(s,pid,a)
            if p['revision']!=plan['revision']: fail(409,'Plan changed during assistant response; retry')
            for src in cited:
                current=s['sources'].get(pid+':'+src['id'])
                if not current or current['deleted'] or current['version']!=src['version']: fail(409,'Evidence changed; retry')
            if len(p['messages'])>MAX_MESSAGES-2: fail(409,'Plan message limit reached')
            labels={x['label'] for x in view(s,p,a)['preferences']}
            if len(labels | set(output['preferences']))>MAX_PREFERENCES: fail(409,'Plan preference limit reached')
            ids=[]
            for label in output['preferences'][:10]:
                if label in labels: continue
                labels.add(label)
                proposal_id=uid(); ids.append(proposal_id); s['proposals'][proposal_id]={'id':proposal_id,'plan_id':pid,'label':label,'status':'pending','created_by':a.id}
            public=[{'id':x['id'],'title':x['title'],'text':x['text']} for x in cited]
            last=p['messages'][-1] if p['messages'] else {}
            if last.get('user_id')!=a.id or last.get('text')!=b.message or last.get('assistant'):
                message_id=uid(); source(s,pid,message_id,'Chat: '+a.name,b.message)
                p['messages'].append({'id':message_id,'author':a.name,'user_id':a.id,'text':b.message,'time':now()})
            p['messages'].append({'id':uid(),'author':'Tagalong','text':output['text'],'time':now(),'assistant':True,'sources':public}); p['revision']+=1
            return {'text':output['text'],'preferences':[{'label':x,'confirmed':False} for x in output['preferences'][:10]],'sources':public,'mode':'live','proposal_ids':ids}
        return repo.transact(save)
    @app.post('/v1/plans/{pid}/documents')
    def document(pid:str,b:Document,a=Depends(actor)):
        def add(s):
            access(s,pid,a); sid=uid(); source(s,pid,sid,b.title,b.text,kind='document'); return {'id':sid,'title':b.title,'status':'queued'}
        return repo.transact(add)
    @app.get('/v1/plans/{pid}/documents')
    def documents(pid:str,a=Depends(actor)):
        def read(s):
            access(s,pid,a); return [x for x in s['sources'].values() if x['plan_id']==pid and not x['deleted'] and x.get('kind','message')=='document']
        return repo.transact(read)
    @app.delete('/v1/plans/{pid}/documents/{sid}')
    def delete_document(pid:str,sid:str,a=Depends(actor)):
        def delete(s):
            access(s,pid,a); item=s['sources'].get(pid+':'+sid)
            if not item or item['deleted'] or item.get('kind','message')!='document': fail(404,'Document not found')
            source(s,pid,sid,item['title'],'',True); return {'status':'queued'}
        return repo.transact(delete)
    from .admin import install_admin
    install_admin(app,repo,actor)
    from .places import install_places
    install_places(app,repo,actor,places)
    from .plan_management import install_plan_management
    install_plan_management(app,repo,actor)
    from .coordination_routes import install_coordination
    install_coordination(app,repo,actor,ai)
    return app

app=create_app()
