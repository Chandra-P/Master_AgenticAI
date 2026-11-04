import os, copy, time
from fastapi import FastAPI, Depends, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Literal
from .core import *

class Create(BaseModel):
    kind:Literal['outing','trip']; title:str=Field(min_length=1,max_length=200); start:str; end:str; participants:str=''
class Update(BaseModel):
    plan:dict; expected_revision:int
class Chat(BaseModel):
    message:str=Field(min_length=1,max_length=10000)
class Share(BaseModel):
    email:str=Field(min_length=3,max_length=320)
class Document(BaseModel):
    title:str=Field(min_length=1,max_length=200); text:str=Field(min_length=1,max_length=100000); content_type:Literal['text/plain']='text/plain'

def create_app(repo=None,authenticate=None,ai=None):
    app=FastAPI(title='Tagalong API')
    app.add_middleware(CORSMiddleware,allow_origins=[x for x in os.getenv('CORS_ORIGINS','http://localhost:3000').split(',') if x],allow_methods=['GET','POST','PUT','DELETE'],allow_headers=['Authorization','Content-Type'])
    if repo is None and os.getenv('DATABASE_URL'):
        from .repository import PostgresRepository
        repo=PostgresRepository(os.environ['DATABASE_URL'])
    if authenticate is None and os.getenv('SUPABASE_URL') and os.getenv('SUPABASE_SERVICE_ROLE_KEY'):
        from .providers import SupabaseAuth
        authenticate=SupabaseAuth(os.environ['SUPABASE_URL'],os.environ['SUPABASE_SERVICE_ROLE_KEY'])
    if ai is None and all(os.getenv(k) for k in ('OPENAI_API_KEY','PINECONE_API_KEY','PINECONE_INDEX_HOST')):
        from .providers import ConnectedAI
        ai=ConnectedAI()
    def actor(authorization:str|None=Header(default=None)):
        if not authorization or not authorization.startswith('Bearer '): fail(401,'Bearer session required')
        if not authenticate or not repo: fail(503,'Connected service is not configured')
        a=authenticate(authorization[7:])
        repo.transact(lambda s:register(s,a))
        return a
    @app.get('/health')
    def health(): return {'status':'ok' if repo and authenticate else 'unconfigured','mode':'connected','capabilities':{'plans':bool(repo and authenticate),'assistant':bool(ai),'documents':bool(repo),'places':False,'calendar':False}}
    @app.get('/v1/me')
    def me(a=Depends(actor)): return vars(a)
    @app.get('/v1/plans')
    def plans(a=Depends(actor)): return repo.transact(lambda s:[view(s,p,a) for pid,p in s['plans'].items() if a.id in s['members'].get(pid,[])])
    @app.post('/v1/plans')
    def make(b:Create,a=Depends(actor)): return repo.transact(lambda s:create(s,a,b))
    @app.get('/v1/plans/{pid}')
    def get(pid:str,a=Depends(actor)): return repo.transact(lambda s:view(s,access(s,pid,a),a))
    @app.put('/v1/plans/{pid}')
    def put(pid:str,b:Update,a=Depends(actor)): return repo.transact(lambda s:update(s,a,pid,b.plan,b.expected_revision))
    @app.post('/v1/plans/{pid}/members')
    def share(pid:str,b:Share,a=Depends(actor)):
        def check(s):
            if access(s,pid,a)['owner_id']!=a.id: fail(403,'Only owner can share')
        repo.transact(check)
        target=authenticate.find(b.email) if hasattr(authenticate,'find') else repo.transact(lambda s:next((Actor(**v) for v in s['actors'].values() if v['email'].casefold()==b.email.casefold()),None))
        if not target: fail(404,'Existing account not found')
        def add(s):
            check(s); p=access(s,pid,a); register(s,target)
            if target.id not in s['members'][pid]:
                s['members'][pid].append(target.id); p['members'].append({'name':target.name,'user_id':target.id,'color':'#14b8a6'}); p['revision']+=1
            return {'status':'added'}
        return repo.transact(add)
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
                    return [copy.deepcopy(src) for hit in matches if (src:=s['sources'].get(pid+':'+hit['id'])) and not src['deleted'] and src['version']==hit.get('version') and src['plan_id']==pid]
                return repo.transact(evidence)
            output,sources=ai.answer(plan,b.message,resolve_sources)
            if not isinstance(output.get('text'),str) or not isinstance(output.get('preferences'),list) or any(not isinstance(x,str) or len(x)>200 for x in output['preferences']): raise ValueError()
            cited=[src for src in sources if src['id'] in output.get('source_ids',[])]
        except HTTPException: raise
        except Exception: fail(502,'AI provider unavailable or returned invalid output')
        def save(s):
            p=access(s,pid,a)
            if p['revision']!=plan['revision']: fail(409,'Plan changed during assistant response; retry')
            for src in cited:
                current=s['sources'].get(pid+':'+src['id'])
                if not current or current['deleted'] or current['version']!=src['version']: fail(409,'Evidence changed; retry')
            ids=[]
            for label in output['preferences'][:10]:
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
            access(s,pid,a); sid=uid(); source(s,pid,sid,b.title,b.text); return {'id':sid,'title':b.title,'status':'queued'}
        return repo.transact(add)
    @app.get('/v1/plans/{pid}/documents')
    def documents(pid:str,a=Depends(actor)):
        def read(s):
            access(s,pid,a); return [x for x in s['sources'].values() if x['plan_id']==pid and not x['deleted']]
        return repo.transact(read)
    @app.delete('/v1/plans/{pid}/documents/{sid}')
    def delete_document(pid:str,sid:str,a=Depends(actor)):
        def delete(s):
            access(s,pid,a); item=s['sources'].get(pid+':'+sid)
            if not item or item['deleted']: fail(404,'Document not found')
            source(s,pid,sid,item['title'],'',True); return {'status':'queued'}
        return repo.transact(delete)
    return app

app=create_app()



