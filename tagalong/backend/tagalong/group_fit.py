"""Read-only group-fit assessment over authoritative facts and verified RAG evidence."""
import copy
import json
import threading
import time
from typing import Literal
from urllib.parse import urlsplit

from fastapi import Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr, field_validator
from .core import access, fail
from .notes_context import notes_context
from .retrieval_status import indexing_status


class Option(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    name: StrictStr = Field(min_length=1, max_length=160, pattern=r'\S')
    details: StrictStr = Field(default='', max_length=6000)
    url: StrictStr | None = Field(default=None, max_length=2048)
    estimated_cost_per_person: float | None = Field(default=None, ge=0)

    @field_validator('estimated_cost_per_person',mode='before')
    @classmethod
    def numeric_cost(cls,value):
        if value is not None and (type(value) not in (int,float)):
            raise ValueError('Use a numeric per-person estimate')
        return value

    @field_validator('url')
    @classmethod
    def public_link(cls, value):
        if value is None: return value
        parsed=urlsplit(value)
        if parsed.scheme not in ('http','https') or not parsed.hostname or parsed.username or parsed.password or any(ord(c)<33 for c in value):
            raise ValueError('Use an HTTP or HTTPS source link')
        return value


class FitRequest(BaseModel):
    model_config=ConfigDict(extra='forbid')
    expected_revision: StrictInt = Field(ge=1)
    option: Option


class Finding(BaseModel):
    model_config=ConfigDict(extra='forbid')
    text: StrictStr = Field(min_length=1,max_length=700)
    source_ids: list[StrictStr] = Field(min_length=1,max_length=8)


class FitOutput(BaseModel):
    model_config=ConfigDict(extra='forbid')
    verdict: Literal['fits','conflicts','needs_info']
    summary: StrictStr = Field(min_length=1,max_length=1200)
    matches: list[Finding] = Field(max_length=8)
    conflicts: list[Finding] = Field(max_length=8)
    unknowns: list[StrictStr] = Field(max_length=8)


def fit_evidence(s,pid,query,hits,option):
    p=s['plans'][pid]
    facts={key:p[key] for key in ('title','start','end','location','budget')}
    from .decisions import context as decision_context
    facts['decision_context']=decision_context(s,pid)
    facts['budget_basis']='per person; 0 means not set'
    preferences=[x['label'] for x in p['preferences'] if x['confirmed']]
    facts['confirmed_preferences']=preferences[:30]
    facts['polls']=[{'question':x['question'],'options':x['options'],'votes':x['votes'],'status':'Votes are proposals, not automatically confirmed decisions'} for x in p['polls'][:12]]
    facts_truncated=len(preferences)>30 or len(p['polls'])>12
    while len(json.dumps(facts,ensure_ascii=False))>12000 and (facts['polls'] or facts['confirmed_preferences']):
        (facts['polls'] if facts['polls'] else facts['confirmed_preferences']).pop()
        facts_truncated=True
    option_text=('Name: '+option['name']+'\nEstimated cost per person (user-provided): '+str(option.get('estimated_cost_per_person','not supplied'))+'\nWebsite (user-provided, not fetched): '+option.get('url','not supplied')+'\nDetails (user-provided, unverified): '+option['details'])
    evidence=[{'id':'plan-facts','title':'Current plan facts','text':json.dumps(facts,ensure_ascii=False),'retrieval_origin':'postgres'},
              {'id':'option-details','title':'Proposed option — user-provided, unverified','text':option_text,'retrieval_origin':'user_input'}]
    docs=[x for x in s['sources'].values() if x['plan_id']==pid and not x['deleted'] and x.get('kind')=='document']
    notes,status=notes_context(docs,query)
    for item in notes:item['retrieval_origin']='saved_note'
    history=[]
    for hit in hits[:12]:
        if not isinstance(hit,dict) or not isinstance(hit.get('id'),str): continue
        src=s['sources'].get(pid+':'+hit['id'])
        if not src or src['plan_id']!=pid or src['deleted'] or src['version']!=hit.get('version'):continue
        if any(x['id']==src['id'] for x in history):continue
        chunk=hit.get('chunk',0)
        if type(chunk) is not int or chunk<0:continue
        item=copy.deepcopy(src);item['text']=src['text'][chunk*6000:(chunk+1)*6000];item['retrieval_origin']='pinecone'
        if not item['text']:continue
        item['excerpt_truncated']=len(item['text'])<len(src['text'])
        history.append(item)
    recent=[]
    for message in p['messages'][-20:]:
        if message.get('assistant'):continue
        src=s['sources'].get(pid+':'+message['id'])
        if src and not src['deleted'] and src['plan_id']==pid:
            item=copy.deepcopy(src);item['text']=item['text'][:1500]
            item['retrieval_origin']='recent_message'
            item['excerpt_truncated']=len(item['text'])<len(src['text'])
            recent.append(item)
    decision_sources=[copy.deepcopy(src) for src in s['sources'].values() if src['plan_id']==pid and not src['deleted'] and src.get('kind') in ('decision','decision_comment')]
    for item in decision_sources[-2:]:
        item['text']=item['text'][:3000];item['retrieval_origin']='current_decision';item['excerpt_truncated']=len(item['text'])<len(s['sources'][pid+':'+item['id']]['text']);recent.append(item)
    selected=[]
    # Preserve semantic history while also including fresh, not-yet-indexed chat.
    for item in history[:2]+recent[-2:]+notes+history[2:]:
        if len(selected)>=6:break
        if not any(x['id']==item['id'] for x in selected):selected.append(item)
    evidence.extend({**item,'_source_id':item['id'],'id':'saved:'+item['id']} for item in selected)
    included={x['id'] for x in selected}
    truncated=facts_truncated or status['context_truncated'] or any(x.get('excerpt_truncated') for x in selected) or any(x['id'] not in included for x in notes+history+recent)
    return evidence,bool(truncated),bool(selected),facts


def install_group_fit(app,repo,actor,ai):
    slots=threading.BoundedSemaphore(2); lock=threading.Lock();limits={}
    def reserve(a):
        bucket=int(time.monotonic()//60)
        with lock:
            for key in list(limits):
                if limits[key][0]!=bucket:del limits[key]
            count=limits.get(a.id,(bucket,0))[1]
            if count>=10 or (a.id not in limits and len(limits)>=10000):fail(429,'Group-fit limit reached; retry in a minute')
            if not slots.acquire(blocking=False):fail(429,'Group-fit checks busy; retry shortly')
            limits[a.id]=(bucket,count+1)

    @app.post('/v1/plans/{pid}/group-fit',summary='Check a proposed option against current plan facts and retrieved sources')
    def assess(pid:str,body:FitRequest,a=Depends(actor)):
        def guard(s):
            p=access(s,pid,a)
            if p['revision']!=body.expected_revision:fail(409,'Plan changed; refresh and check this option again')
            return copy.deepcopy(p)
        plan=repo.transact(guard)
        if ai is None or not hasattr(ai,'assess_group_fit'):fail(503,'Group-fit provider is not configured')
        option=body.option.model_dump(exclude_none=True)
        query=('Group fit dietary allergy accessibility quiet budget transport preferences constraints '+option['name']+' '+option['details'][:1500]+' '+' '.join(x['label'] for x in plan['preferences'] if x['confirmed']))[:3000]
        reserve(a)
        try:
            retrieval='available'
            try:hits=(ai.retrieve_group_fit if hasattr(ai,'retrieve_group_fit') else ai.retrieve)(pid,query)
            except Exception:hits=[];retrieval='unavailable'
            def snapshot(s):
                guard(s)
                document_versions={x['id']:x['version'] for x in s['sources'].values() if x['plan_id']==pid and not x['deleted'] and x.get('kind')=='document'}
                return (*fit_evidence(s,pid,query,hits,option),document_versions,indexing_status(s,pid))
            evidence,truncated,has_evidence,facts,document_versions,index_freshness=repo.transact(snapshot)
            try:
                output=FitOutput.model_validate(ai.assess_group_fit(option,evidence)).model_dump()
                ids={x['id'] for x in evidence}
                if any(not set(x['source_ids']).issubset(ids) for x in output['matches']+output['conflicts']):raise ValueError('Unknown citation')
                if any(len(x)>700 for x in output['unknowns']):raise ValueError('Oversized unknown')
            except HTTPException:raise
            except Exception:fail(502,'The group-fit answer could not be validated. Please try again.')
            def verify(s):
                guard(s)
                current_documents={x['id']:x['version'] for x in s['sources'].values() if x['plan_id']==pid and not x['deleted'] and x.get('kind')=='document'}
                if current_documents!=document_versions:fail(409,'Saved Notes changed; check the option again')
                for item in evidence:
                    if '_source_id' not in item:continue
                    current=s['sources'].get(pid+':'+item['_source_id'])
                    if not current or current['plan_id']!=pid or current['deleted'] or current['version']!=item['version']:fail(409,'Supporting sources changed; check the option again')
            repo.transact(verify)
            unknowns=output['unknowns']
            def unknown(text):
                if text not in unknowns:unknowns.insert(0,text)
            if not option['details'].strip():unknown('Add option details or a menu before judging suitability.')
            if not has_evidence:unknown('No saved group evidence was available; add preferences or Notes to assess this option.')
            if not facts['confirmed_preferences'] and not any(x.get('kind')=='message' for x in evidence) and not any(x.get('kind')=='document' and 'menu' not in x['title'].casefold() for x in evidence):
                unknown('Confirm the group’s preferences and constraints; a menu alone does not establish what everyone needs.')
            if facts['budget']<=0:unknown('The group has not set a working budget.')
            if retrieval=='unavailable':unknown('Historical search was unavailable; only current plan facts and saved evidence were reviewed.')
            if truncated:unknown('Only selected excerpts were reviewed; some plan evidence was omitted.')
            cost=option.get('estimated_cost_per_person')
            if cost is not None and facts['budget']>0 and cost>facts['budget']:
                output['conflicts'].insert(0,{'text':f'The proposed estimate of {cost:g} per person exceeds the working budget of {facts["budget"]:g}.','source_ids':['plan-facts','option-details']})
            if output['conflicts']:output['verdict']='conflicts';output['summary']='This option has conflicts with the group’s recorded constraints. Review the findings and sources below.'
            elif unknowns or not output['matches'] or output['verdict']=='conflicts':
                if output['verdict']=='conflicts' and not unknowns:unknown('Clarify the concern before deciding; no supported conflict was provided.')
                output['verdict']='needs_info';output['summary']='More information is needed before confirming this option fits the group. Review the findings and open questions below.'
            output['sources']=[{key:x[key] for key in ('id','title','text','retrieval_origin') if key in x} for x in evidence]
            output['matches']=output['matches'][:8];output['conflicts']=output['conflicts'][:8];output['unknowns']=unknowns[:8]
            output['retrieval_status']=retrieval;output['context_truncated']=truncated;output['index_freshness']=index_freshness
            return output
        finally:slots.release()
