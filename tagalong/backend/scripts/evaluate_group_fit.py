"""Reproducible synthetic rule checks + four live, read-only provider evaluations.

Run from tagalong/backend with uv run --env-file PATH python scripts/evaluate_group_fit.py.
No production database, auth account, plan, index upsert, or ingestion worker is used.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
import xml.etree.ElementTree as ET

# Remove production persistence/auth before importing app.py (it builds a default app).
for key in ('DATABASE_URL', 'SUPABASE_URL', 'SUPABASE_SERVICE_ROLE_KEY'):
    os.environ.pop(key, None)
os.environ['TAGALONG_EMBEDDED_WORKER'] = 'false'
BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from fastapi.testclient import TestClient
from tagalong.app import create_app
from tagalong.core import Actor, MemoryRepository, source
from tagalong.providers import ConnectedAI
from tagalong.group_fit import FitOutput


CASES = [
    {'id':'over_budget','expected':'conflicts','budget':50,
     'constraints':'All members agreed a vegetarian dinner and a maximum budget of USD 50 per person.',
     'option':{'name':'Synthetic garden dinner','details':'User-provided vegetarian set menu, quoted at USD 75 per person. Venue details remain unverified.','estimated_cost_per_person':75}},
    {'id':'missing_evidence','expected':'needs_info','budget':50,'constraints':None,
     'option':{'name':'Undocumented dinner idea','details':''}},
    {'id':'dietary_conflict','expected':'conflicts','budget':60,
     'constraints':'Every member explicitly agreed to vegetarian-only food: no meat, poultry or seafood. All members confirmed this applies to dinner.',
     'option':{'name':'Synthetic steak tasting','details':'User-provided menu: every course contains beef, including beef stock, with no vegetarian alternatives. Estimated USD 30 per person.','estimated_cost_per_person':30}},
    {'id':'supported_home_option','expected':'fits','budget':50,
     'constraints':'For this fictional scenario, every member explicitly confirmed vegetarian mild food, a dinner at a member home on May 14, 2027 in San Francisco, no reported food allergies or access requirements, and a USD 50 per-person limit. No restaurant booking is wanted. Everyone has confirmed transport and the date.',
     'option':{'name':'Synthetic vegetarian home dinner','details':'A member-hosted dinner at the agreed San Francisco home on May 14, 2027. Mild vegetarian tomato pasta, bread and water, with ingredient lists supplied to all members. Each attendee has confirmed this exact proposal and transport. Ingredients are donated: USD 0 per person. No venue, booking or paid provider is involved. These are fictional supplied facts, not live inventory.','estimated_cost_per_person':0}},
]


def rule_checks():
    env=os.environ.copy()
    for key in ('OPENAI_API_KEY','PINECONE_API_KEY','PINECONE_INDEX_HOST'):
        env.pop(key,None)
    started=time.perf_counter()
    with tempfile.TemporaryDirectory() as temporary:
        report=Path(temporary)/'rules.xml'
        run=subprocess.run([sys.executable,'-m','pytest','tests/test_group_fit.py','-q','-p','no:cacheprovider','--junitxml='+str(report)],cwd=BACKEND,env=env,capture_output=True,text=True)
        cases=[]
        if report.exists():
            for item in ET.parse(report).iter('testcase'):
                status='failed' if item.find('failure') is not None or item.find('error') is not None else 'skipped' if item.find('skipped') is not None else 'passed'
                cases.append({'name':item.attrib['name'],'status':status,'seconds':float(item.attrib.get('time',0))})
        groups={
            'citation_validation':['fabricated_citations','saved_ids_cannot_collide'],
            'budget_conflict_rule':['budget_conflict_is_deterministic'],
            'missing_evidence_rule':['no_saved_evidence'],
            'cross_plan_access':['requires_authorized_current_revision','foreign_deleted_and_stale'],
            'freshness':['rechecks_access_and_evidence','new_notes_during_assessment','saved_ids_cannot_collide'],
        }
        metrics={}
        for category,patterns in groups.items():
            selected=[x for x in cases if any(pattern in x['name'] for pattern in patterns)]
            metrics[category]={'passed':sum(x['status']=='passed' for x in selected),'total':len(selected),'tests':[x['name'] for x in selected]}
        return {'command':'python -m pytest tests/test_group_fit.py -q -p no:cacheprovider --junitxml=TEMP/rules.xml','exit_code':run.returncode,'seconds':round(time.perf_counter()-started,3),'passed':sum(x['status']=='passed' for x in cases),'total':len(cases),'metrics':metrics,'cases':cases}


class MeasuredAI:
    def __init__(self,provider):self.provider=provider;self.measurements={}
    def retrieve_group_fit(self,pid,query):
        started=time.perf_counter()
        try:
            hits=self.provider.retrieve_group_fit(pid,query)
            self.measurements['retrieved_hit_count']=len(hits)
            return hits
        except Exception as error:
            self.measurements['retrieval_error_type']=type(error).__name__
            raise
        finally:self.measurements['retrieval_seconds']=round(time.perf_counter()-started,3)
    def assess_group_fit(self,option,evidence):
        started=time.perf_counter()
        try:
            result=self.provider.assess_group_fit(option,evidence)
            self.measurements['raw_model_verdict']=result.get('verdict')
            return result
        finally:self.measurements['generation_seconds']=round(time.perf_counter()-started,3)


def live_checks():
    provider=ConnectedAI()
    measured=MeasuredAI(provider);repo=MemoryRepository()
    app=create_app(repo,lambda token:Actor('synthetic-evaluator','evaluator@example.test','Synthetic evaluator'),measured)
    client=TestClient(app);headers={'Authorization':'Bearer synthetic-evaluation'}
    results=[]
    for case in CASES:
        measured.measurements={}
        created=client.post('/v1/plans',headers=headers,json={'title':'Synthetic RAG evaluation: '+case['id'],'kind':'outing','start':'2027-05-14','end':'2027-05-14'})
        created.raise_for_status();plan=created.json();pid=plan['id']
        repo.state['plans'][pid]['budget']=case['budget'];repo.state['plans'][pid]['location']='San Francisco'
        if case['constraints']:
            repo.transact(lambda state:source(state,pid,'constraints','Synthetic group constraints',case['constraints'],kind='document'))
        before=copy.deepcopy(repo.state)
        started=time.perf_counter()
        response=client.post('/v1/plans/'+pid+'/group-fit',headers=headers,json={'expected_revision':plan['revision'],'option':case['option']})
        elapsed=round(time.perf_counter()-started,3)
        body=response.json()
        ids={item['id'] for item in body.get('sources',[])}
        findings=body.get('matches',[])+body.get('conflicts',[])
        valid_citations=(all(item.get('source_ids') and set(item['source_ids']).issubset(ids) for item in findings) if findings else None) if response.status_code==200 else False
        try:
            FitOutput.model_validate({key:body[key] for key in ('verdict','summary','matches','conflicts','unknowns')})
            schema_valid=response.status_code==200 and isinstance(body['context_truncated'],bool) and body['retrieval_status'] in ('available','unavailable') and all(all(isinstance(x[key],str) for key in ('id','title','text')) for x in body['sources'])
        except (KeyError,TypeError,ValueError):schema_valid=False
        results.append({'case':case['id'],'expected_verdict':case['expected'],'http_status':response.status_code,'observed_verdict':body.get('verdict'),'verdict_matches_expectation':body.get('verdict')==case['expected'],'validated_response':schema_valid,'citation_ids_valid':valid_citations,'finding_count':len(findings),'citation_entailment_human_reviewed':False,'plan_state_unchanged':repo.state==before,'latency_seconds':elapsed,**measured.measurements,'synthetic_input':case,'response':body})
    return provider.model,results


def main():
    started=datetime.now(timezone.utc).isoformat()
    rules=rule_checks()
    model,live=live_checks()
    latencies=[item['latency_seconds'] for item in live]
    artifact={'title':'Tagalong group-fit synthetic demonstration evaluation','started_at_utc':started,'completed_at_utc':datetime.now(timezone.utc).isoformat(),'model':model,'scope':'Synthetic MemoryRepository plans only; real OpenAI generation and real Pinecone queries in fresh random namespaces. No index writes, production plans, production database, or real auth accounts.','source_sha256':{str(path.relative_to(BACKEND)):hashlib.sha256(path.read_bytes()).hexdigest() for path in [BACKEND/'tagalong/group_fit.py',BACKEND/'tagalong/providers.py',BACKEND/'tests/test_group_fit.py']},'rule_evaluation':rules,'live_evaluation':{'case_count':len(live),'validated_responses':sum(x['validated_response'] for x in live),'citation_bearing_cases':sum(x['finding_count']>0 for x in live),'valid_citation_id_cases':sum(x['citation_ids_valid'] is True for x in live),'cited_findings':sum(x['finding_count'] for x in live),'findings_with_valid_source_ids':sum(x['finding_count'] for x in live if x['citation_ids_valid'] is True),'expected_verdict_matches':sum(x['verdict_matches_expectation'] for x in live),'unchanged_state_cases':sum(x['plan_state_unchanged'] for x in live),'median_latency_seconds':round(statistics.median(latencies),3),'max_latency_seconds':max(latencies),'cases':live},'limitations':['Four synthetic cases are a demonstration, not a statistically representative benchmark.','Citation-ID validity establishes supplied-source references, not semantic entailment, truth, or safety. Human citation entailment was not scored. Cases with no findings are N/A for citation validity.','Fresh namespaces intentionally have no indexed records. Live Pinecone checks validate routing/availability, not retrieval relevance or ranking quality. Saved synthetic Notes provide immediate evidence.','Budget and missing-evidence outcomes include deterministic server rules; they do not measure model-only reasoning accuracy.','Latency includes authentication adapter, repository, real embedding/query and model generation. One sequential run, no load test or percentile claims.','No real menu, allergy safety, prices, availability, booking or calendar action was verified.']}
    destination=BACKEND.parent/'docs/evaluations'
    destination.mkdir(parents=True,exist_ok=True)
    stem=destination/'2026-11-06-group-fit-demo'
    stem.with_suffix('.json').write_text(json.dumps(artifact,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# Group-fit synthetic demonstration evaluation','',f"Run started (UTC): {started}",f"Model: `{model}`",'',artifact['scope'],'','## Reproduce','','From `tagalong/backend`:','','```sh','uv run --env-file /secure/path/backend.env python scripts/evaluate_group_fit.py','```','','The script removes database/auth environment values, disables indexing, runs fake-provider rule tests without provider keys, then runs four live synthetic requests. It uses existing OpenAI/Pinecone credentials only for provider calls. It never upserts vectors. Re-running overwrites these dated demo artifacts.','','## Deterministic rule and security scenarios','',f"{rules['passed']}/{rules['total']} tests passed; exit code {rules['exit_code']}; {rules['seconds']} seconds.",'','| Check | Passing scenarios |','|---|---|']
    lines.extend(f"| {key.replace('_',' ')} | {value['passed']}/{value['total']} |" for key,value in rules['metrics'].items())
    lines+=['','## Live provider outcomes','','| Synthetic case | Expected | Observed | Valid citation IDs | End-to-end seconds |','|---|---|---|---|---|']
    lines.extend(f"| {x['case']} | {x['expected_verdict']} | {x['observed_verdict'] or 'HTTP '+str(x['http_status'])} | {'yes' if x['citation_ids_valid'] is True else 'N/A (no findings)' if x['citation_ids_valid'] is None else 'no'} | {x['latency_seconds']} |" for x in live)
    metrics=artifact['live_evaluation']
    lines+=['',f"Validated responses: {metrics['validated_responses']}/4. Expected-verdict agreement: {metrics['expected_verdict_matches']}/4. Unchanged in-memory state: {metrics['unchanged_state_cases']}/4.",f"Median latency: {metrics['median_latency_seconds']} seconds; maximum observed: {metrics['max_latency_seconds']} seconds.",'','## Limits and honest interpretation','']
    lines.insert(-3,f"Citation references: {metrics['findings_with_valid_source_ids']}/{metrics['cited_findings']} findings cite supplied source IDs across {metrics['citation_bearing_cases']} cases with findings. This is reference validity, not semantic accuracy.")
    lines.extend('- '+item for item in artifact['limitations'])
    lines+=['','See the adjacent JSON for exact synthetic inputs, returned evidence/findings, per-stage timings and source-file hashes.']
    stem.with_suffix('.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'artifacts':str(stem),'rules_passed':rules['passed'],'rules_total':rules['total'],'live_validated':metrics['validated_responses'],'verdict_matches':metrics['expected_verdict_matches'],'cases':4,'median_seconds':metrics['median_latency_seconds']}))
    return 0 if rules['exit_code']==0 and metrics['validated_responses']==4 else 1


if __name__=='__main__':raise SystemExit(main())
