"""Read-only evidence retrieval and bounded public search; no suitability generation."""
import copy
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from fastapi import Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr
from .core import access, fail, now
from .group_fit import fit_evidence
from .places import safe_source_url


class ResearchRequest(BaseModel):
    model_config=ConfigDict(extra='forbid')
    expected_revision:StrictInt=Field(ge=1)
    query:StrictStr=Field(min_length=2,max_length=250,pattern=r'\S')
    category:StrictStr=Field(min_length=1,max_length=60,pattern=r'\S')
    location:StrictStr|None=Field(default=None,min_length=2,max_length=150,pattern=r'\S')


def bounded_lookup(provider,args,limit):
    """Bound provider output and report failures without exposing provider errors."""
    if provider is None:return 'skipped',[]
    try:
        raw=provider(*args)
        if not isinstance(raw,list):raise ValueError('Invalid provider results')
        return 'completed',raw[:limit]
    except Exception:return 'unavailable',[]


def retrieve_group_evidence(ai,pid,query):
    """Retrieve candidate history hits; repository authorization resolves them later."""
    provider=getattr(ai,'retrieve_group_fit',getattr(ai,'retrieve',None))
    return bounded_lookup(provider,(pid,query),12)


def search_public_places(places,query,location,category):
    """Search bounded public venue results using the provider's own timeouts."""
    provider=(places.venues if hasattr(places,'venues') else getattr(places,'search',None)) if location else None
    return bounded_lookup(provider,(query,location,category),8)


def normalize_public_options(rows,source_offset=0):
    """Keep safe source excerpts and identified venues with unverified provenance."""
    sources=[];options=[]
    for row in rows:
        if not isinstance(row,dict):continue
        url=safe_source_url(row.get('url'));title=row.get('title');snippet=row.get('snippet','')
        if not url or not isinstance(title,str) or not title.strip():continue
        sid='external:'+str(source_offset+len(sources)+1)
        details=snippet[:1500] if isinstance(snippet,str) else ''
        retrieved_at=now()
        sources.append({'id':sid,'title':title[:200],'text':'Unverified public search snippet. Retrieved: '+retrieved_at+'. Source: '+url+'\n'+details})
        if row.get('kind')!='place':continue
        option={'id':sid,'name':title[:160],'details':details,'url':url,'estimated_cost_per_person':None,'source_ids':[sid],
                'provenance':{'url':url,'retrievedAt':retrieved_at,'excerpt':details}}
        image=safe_source_url(row.get('image'))
        if image and image.startswith('https://') and safe_source_url(row.get('image_source_url'))==url:option['image']=image
        options.append(option)
    return sources,options


def install_research(app,repo,actor,ai,places):
    """Install the authorized research pipeline and shared request limits."""
    slots=threading.BoundedSemaphore(2);lock=threading.Lock();limits={}
    def reserve(a):
        bucket=int(time.monotonic()//60)
        with lock:
            for key in list(limits):
                if limits[key][0]!=bucket:del limits[key]
            count=limits.get(a.id,(bucket,0))[1]
            if count>=10 or (a.id not in limits and len(limits)>=10000):fail(429,'Research limit reached; retry next minute')
            if not slots.acquire(blocking=False):fail(429,'Research busy; retry shortly')
            limits[a.id]=(bucket,count+1)

    @app.post('/v1/plans/{pid}/research')
    def research(pid:str,b:ResearchRequest,a=Depends(actor)):
        def versions(s):
            return {x['id']:x['version'] for x in s['sources'].values() if x['plan_id']==pid and not x['deleted']}
        def guard(s):
            p=access(s,pid,a)
            if p['revision']!=b.expected_revision:fail(409,'Plan changed; refresh research')
            return p
        def initial(s):return copy.deepcopy(guard(s)),versions(s)
        plan,source_versions=repo.transact(initial)
        reserve(a)
        try:
            steps=[]
            location=b.location or plan.get('location','')
            with ThreadPoolExecutor(max_workers=2) as pool:
                retrieval=pool.submit(retrieve_group_evidence,ai,pid,b.query)
                public_search=pool.submit(search_public_places,places,b.query,location,b.category)
                retrieval_status,hits=retrieval.result()
                search_status,rows=public_search.result()
            steps.append({'id':'retrieval','label':'Search saved group evidence','status':retrieval_status,'detail':'Authorized current source excerpts only.' if retrieval_status=='completed' else 'Historical retrieval is not available; current facts and Notes remain visible.'})
            def snapshot(s):
                guard(s)
                if versions(s)!=source_versions:fail(409,'Supporting sources changed; refresh research')
                return fit_evidence(s,pid,b.query,hits,{'name':b.query,'details':''})
            evidence,truncated,_,_=repo.transact(snapshot)
            sources=[{k:x[k] for k in ('id','title','text')} for x in evidence if x['id']!='option-details']
            steps.append({'id':'notes','label':'Read current plan and saved Notes','status':'completed','detail':'These are recorded group facts and selected excerpts, not a suitability assessment.'})
            steps.append({'id':'search','label':'Search public sources','status':search_status,'detail':'Public snippets are unverified; confirm price, suitability and availability with the provider.' if search_status=='completed' else 'Public search was unavailable or no location was supplied.'})
            identified=hasattr(places,'venues')
            steps.append({'id':'venues','label':'Identify individual venues','status':search_status if identified else 'skipped','detail':'Only identified individual venue rows can become options; linked descriptions still need verification.' if identified else 'This search provider did not perform venue identification.'})
            public_sources,options=normalize_public_options(rows,sum(x['id'].startswith('external:') for x in sources))
            sources.extend(public_sources)
            def verify(s):
                guard(s)
                if versions(s)!=source_versions:fail(409,'Supporting sources changed; refresh research')
            repo.transact(verify)
            return JSONResponse({'plan_id':pid,'plan_revision':b.expected_revision,'query':b.query,'sources':sources,'options':options,'steps':steps,'context_truncated':truncated},headers={'Cache-Control':'no-store'})
        finally:slots.release()
