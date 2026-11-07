"""Read-only evidence retrieval and bounded public search; no suitability generation."""
import copy
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Literal
from fastapi import Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr
from .core import access, fail, now
from .group_fit import fit_evidence
from .places import safe_source_url
from .retrieval_status import indexing_status


class AssessmentFinding(BaseModel):
    model_config=ConfigDict(extra='forbid')
    text:StrictStr=Field(min_length=1,max_length=700)
    source_ids:list[StrictStr]=Field(min_length=1,max_length=4)


class OptionAssessment(BaseModel):
    model_config=ConfigDict(extra='forbid')
    option_id:StrictStr=Field(min_length=1,max_length=200)
    verdict:Literal['fits','conflicts','needs_info']
    summary:StrictStr=Field(min_length=1,max_length=1000)
    matches:list[AssessmentFinding]=Field(max_length=5)
    conflicts:list[AssessmentFinding]=Field(max_length=5)
    unknowns:list[StrictStr]=Field(max_length=6)


class AssessmentBatch(BaseModel):
    model_config=ConfigDict(extra='forbid')
    assessments:list[OptionAssessment]=Field(max_length=8)


def retrieval_query(request,plan):
    confirmed=[item['label'] for item in plan.get('preferences',[]) if item.get('confirmed') and isinstance(item.get('label'),str)]
    return ' '.join([request.query,request.category,request.location or plan.get('location',''),plan.get('start',''),plan.get('end',''),'Confirmed group preferences: '+', '.join(confirmed[:20])])[:3000]


def apply_option_assessments(options,raw_assessments,evidence,facts):
    parsed=AssessmentBatch(assessments=raw_assessments).assessments
    expected={option['id'] for option in options}
    if len(parsed)!=len(options) or {item.option_id for item in parsed}!=expected:
        raise ValueError('Assessment must cover the identified options exactly once')
    evidence_ids={item['id'] for item in evidence}
    saved_ids={item['id'] for item in evidence if item['id'].startswith('saved:')}
    basis='saved_group_context' if saved_ids else 'confirmed_plan_facts' if facts.get('confirmed_preferences') else 'insufficient_context'
    by_id={item.option_id:item for item in parsed}
    ranked=[]
    for option in options:
        item=by_id[option['id']]
        own_source=set(option.get('source_ids',[]))
        for finding in item.matches+item.conflicts:
            citations=set(finding.source_ids)
            if not citations.issubset(evidence_ids):raise ValueError('Unknown evidence citation')
            if not citations.intersection(own_source):raise ValueError('Venue finding lacks its public source')
            if basis=='saved_group_context' and not citations.intersection(saved_ids):raise ValueError('Group finding lacks saved group evidence')
            if basis=='confirmed_plan_facts' and 'plan-facts' not in citations:raise ValueError('Plan-fact finding lacks its source')
        if item.verdict=='fits' and (not item.matches or item.conflicts):raise ValueError('Unsupported positive assessment')
        if item.verdict=='conflicts' and not item.conflicts:raise ValueError('Conflict assessment lacks a conflict finding')
        result=item.model_dump()
        result['basis']=basis
        if basis=='insufficient_context':
            result['verdict']='needs_info';result['matches']=[];result['conflicts']=[]
            result['summary']='There is not enough saved group context to personalize this option comparison.'
            note='Add a group preference or relevant Note to compare this option with what the group needs.'
            if note not in result['unknowns']:result['unknowns'].insert(0,note)
        estimate=option.get('estimated_cost_per_person')
        budget=facts.get('budget',0)
        if type(estimate) in (int,float) and type(budget) in (int,float) and budget>0 and estimate>budget:
            result['conflicts'].insert(0,{'text':f'The estimated cost of {estimate:g} per person exceeds the working budget of {budget:g}.','source_ids':['plan-facts','option-details']})
            result['verdict']='conflicts';result['summary']='This option exceeds the group’s recorded working budget.'
        option={**option,'assessment':result}
        ranked.append(option)
    order={'fits':0,'needs_info':1,'conflicts':2}
    return sorted(ranked,key=lambda option:order[option['assessment']['verdict']])


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
        sources.append({'id':sid,'title':title[:200],'text':'Unverified public search snippet. Retrieved: '+retrieved_at+'. Source: '+url+'\n'+details,'retrieval_origin':'public_search'})
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
            semantic_query=retrieval_query(b,plan)
            with ThreadPoolExecutor(max_workers=2) as pool:
                retrieval=pool.submit(retrieve_group_evidence,ai,pid,semantic_query)
                public_search=pool.submit(search_public_places,places,b.query,location,b.category)
                retrieval_status,hits=retrieval.result()
                search_status,rows=public_search.result()
            steps.append({'id':'retrieval','label':'Search saved group evidence','status':retrieval_status,'detail':'Authorized current source excerpts only.' if retrieval_status=='completed' else 'Historical retrieval is not available; current facts and Notes remain visible.'})
            def snapshot(s):
                guard(s)
                if versions(s)!=source_versions:fail(409,'Supporting sources changed; refresh research')
                return (*fit_evidence(s,pid,semantic_query,hits,{'name':b.query,'details':''}),indexing_status(s,pid))
            evidence,truncated,_,facts,index_freshness=repo.transact(snapshot)
            sources=[{**{k:x[k] for k in ('id','title','text')},'retrieval_origin':x.get('retrieval_origin','saved_group_context')} for x in evidence if x['id']!='option-details']
            steps.append({'id':'notes','label':'Read current plan and saved Notes','status':'completed','detail':'These are recorded group facts and selected excerpts, not a suitability assessment.'})
            steps.append({'id':'search','label':'Search public sources','status':search_status,'detail':'Public snippets are unverified; confirm price, suitability and availability with the provider.' if search_status=='completed' else 'Public search was unavailable or no location was supplied.'})
            identified=hasattr(places,'venues')
            steps.append({'id':'venues','label':'Identify individual venues','status':search_status if identified else 'skipped','detail':'Only identified individual venue rows can become options; linked descriptions still need verification.' if identified else 'This search provider did not perform venue identification.'})
            public_sources,options=normalize_public_options(rows,sum(x['id'].startswith('external:') for x in sources))
            sources.extend(public_sources)
            assessment_evidence=evidence+public_sources
            assessment_status='skipped' if not options else 'unavailable'
            if options and ai is not None and hasattr(ai,'assess_research_options'):
                try:
                    raw=ai.assess_research_options(options,assessment_evidence,facts)
                    options=apply_option_assessments(options,raw,assessment_evidence,facts)
                    assessment_status='available'
                except Exception:
                    options=[{**option,'assessment':None} for option in options]
            else:
                options=[{**option,'assessment':None} for option in options]
            steps.append({'id':'indexing','label':'Check saved-source indexing','status':'completed' if index_freshness['status']=='current' else index_freshness['status'],'detail':(str(index_freshness['indexed_sources'])+' of '+str(index_freshness['current_sources'])+' current plan sources are indexed; saved Notes and current facts are still checked.')})
            steps.append({'id':'assessment','label':'Compare options with group context','status':'completed' if assessment_status=='available' else assessment_status,'detail':'The model compared public options with verified plan evidence. Review cited sources and open questions.' if assessment_status=='available' else 'Public results remain available, but the evidence-based comparison could not be completed.' if assessment_status=='unavailable' else 'No identified venue options were available to compare.'})
            def verify(s):
                guard(s)
                if versions(s)!=source_versions:fail(409,'Supporting sources changed; refresh research')
            repo.transact(verify)
            return JSONResponse({'plan_id':pid,'plan_revision':b.expected_revision,'query':b.query,'sources':sources,'options':options,'steps':steps,'assessment_status':assessment_status,'context_truncated':truncated,'index_freshness':index_freshness},headers={'Cache-Control':'no-store'})
        finally:slots.release()
