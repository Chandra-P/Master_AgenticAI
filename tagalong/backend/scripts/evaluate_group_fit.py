"""Reproducible rule checks and synthetic live RAG evaluations.

Run from tagalong/backend with uv run --env-file PATH python scripts/evaluate_group_fit.py.
Uses MemoryRepository plans and short-lived, unique Pinecone namespaces. Never uses the
production database, real plans, or ingestion worker; synthetic vectors are deleted.
"""
import copy
import argparse
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
import uuid

# Remove production persistence/auth before importing app.py (it builds a default app).
for key in ('DATABASE_URL', 'SUPABASE_URL', 'SUPABASE_SERVICE_ROLE_KEY'):
    os.environ.pop(key, None)
os.environ['TAGALONG_EMBEDDED_WORKER'] = 'false'
BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from fastapi.testclient import TestClient
from tagalong.app import create_app
from tagalong.core import Actor, MemoryRepository
from tagalong.providers import ConnectedAI
from tagalong.group_fit import FitOutput
from tagalong.rag_evaluation import (cleanup_synthetic_sources, create_synthetic_source,
                                     compare_ablation_responses, mark_synthetic_source_indexed, remove_synthetic_source,
                                     wait_for_pinecone_sources)
from tagalong.ragas_eval import build_ragas_sample, score_with_ragas_sync


CASES = [
    {'id':'over_budget','expected':'conflicts','budget':50,
     'constraints':'All members agreed a vegetarian dinner and a maximum budget of USD 50 per person.',
     'option':{'name':'Synthetic garden dinner','details':'User-provided vegetarian set menu, quoted at USD 75 per person. Venue details remain unverified.','estimated_cost_per_person':75}},
    {'id':'missing_evidence','expected':'needs_info','budget':50,'constraints':None,
     'option':{'name':'Undocumented dinner idea','details':''}},
    {'id':'dietary_conflict','expected':'conflicts','budget':60,
     'constraints':'Every member explicitly agreed to vegetarian-only food: no meat, poultry or seafood. All members confirmed this applies to dinner.',
     'option':{'name':'Synthetic steak tasting','details':'User-provided menu: every course contains beef, including beef stock, with no vegetarian alternatives. Estimated USD 30 per person.','estimated_cost_per_person':30}},
    {'id':'supported_home_option_safety_unknown','expected':'needs_info','budget':50,
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
            self.measurements['retrieved_source_ids']=[hit['id'] for hit in hits]
            self.measurements['retrieved_hit_details']=[{
                'id':hit['id'],'version':hit.get('version'),'version_type':type(hit.get('version')).__name__,
                'chunk':hit.get('chunk'),'chunk_type':type(hit.get('chunk')).__name__
            } for hit in hits]
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


def group_fit_query(option):
    # Keep this byte-for-byte aligned with the authenticated Group Fit endpoint.
    return ('Group fit dietary allergy accessibility quiet budget transport preferences constraints '
            +option['name']+' '+option.get('details','')[:1500])[:3000]


def response_checks(response, body, expected_source_id=None):
    ids={item['id'] for item in body.get('sources',[]) if isinstance(item,dict) and 'id' in item}
    findings=body.get('matches',[])+body.get('conflicts',[])
    valid_citations=(all(item.get('source_ids') and set(item['source_ids']).issubset(ids) for item in findings) if findings else None) if response.status_code==200 else False
    try:
        FitOutput.model_validate({key:body[key] for key in ('verdict','summary','matches','conflicts','unknowns')})
        schema_valid=response.status_code==200 and isinstance(body['context_truncated'],bool) and body['retrieval_status'] in ('available','unavailable') and all(all(isinstance(x[key],str) for key in ('id','title','text')) for x in body['sources'])
    except (KeyError,TypeError,ValueError):schema_valid=False
    pinecone_sources=[item for item in body.get('sources',[]) if item.get('retrieval_origin')=='pinecone']
    expected_source_in_prompt=bool(expected_source_id and any(item['id']=='saved:'+expected_source_id for item in pinecone_sources))
    expected_source_cited=bool(expected_source_id and any('saved:'+expected_source_id in finding.get('source_ids',[]) for finding in findings))
    return {'validated_response':schema_valid,'citation_ids_valid':valid_citations,'finding_count':len(findings),
            'pinecone_source_ids_in_prompt':[item['id'].removeprefix('saved:') for item in pinecone_sources],
            'expected_pinecone_source_in_prompt':expected_source_in_prompt,
            'expected_pinecone_source_cited':expected_source_cited}


def live_checks(provider):
    measured=MeasuredAI(provider);repo=MemoryRepository()
    app=create_app(repo,lambda token:Actor('synthetic-evaluator','evaluator@example.test','Synthetic evaluator'),measured)
    client=TestClient(app);headers={'Authorization':'Bearer synthetic-evaluation'}
    results=[];cleanup_failures=[];measured.ragas_rows=[]
    for case in CASES:
        measured.measurements={};seeded=[];preflight=None;preflight_error=None
        created=client.post('/v1/plans',headers=headers,json={'title':'Synthetic RAG evaluation: '+case['id'],'kind':'outing','start':'2027-05-14','end':'2027-05-14'})
        created.raise_for_status();plan=created.json();pid=plan['id']
        repo.state['plans'][pid]['budget']=case['budget'];repo.state['plans'][pid]['location']='San Francisco'
        expected_source_id=None
        if case['constraints']:
            expected_source_id='eval-'+case['id']+'-constraints'
            source_record=create_synthetic_source(repo,pid,expected_source_id,'Synthetic group preference',case['constraints'])
            seeded.append(source_record)
            try:
                provider.upsert(source_record)
                mark_synthetic_source_indexed(repo,source_record)
                preflight=wait_for_pinecone_sources(provider,pid,group_fit_query(case['option']),[expected_source_id])
            except Exception as error:
                preflight_error=type(error).__name__
        before=copy.deepcopy(repo.state)
        started=time.perf_counter()
        response=client.post('/v1/plans/'+pid+'/group-fit',headers=headers,json={'expected_revision':plan['revision'],'option':case['option']})
        elapsed=round(time.perf_counter()-started,3)
        body=response.json()
        if response.status_code == 200:
            measured.ragas_rows.append(build_ragas_sample(case, body.get('sources', []), body))
        checks=response_checks(response,body,expected_source_id)
        result={'case':case['id'],'expected_verdict':case['expected'],'http_status':response.status_code,
                'expected_pinecone_source_id':expected_source_id,
                'observed_verdict':body.get('verdict'),'verdict_matches_expectation':body.get('verdict')==case['expected'],
                **checks,'citation_entailment_human_reviewed':False,'plan_state_unchanged':repo.state==before,
                'latency_seconds':elapsed,'preflight_query':preflight,'preflight_error_type':preflight_error,
                **measured.measurements,'synthetic_input':case,'response':body}
        results.append(result)
        failures=cleanup_synthetic_sources(provider,seeded)
        for source_record in seeded:remove_synthetic_source(repo,source_record)
        result['cleanup_failed_source_ids']=failures
        cleanup_failures.extend({'plan_id':pid,'source_id':sid} for sid in failures)
    return repo,client,headers,measured,results,cleanup_failures


def live_pinecone_ablation(provider):
    """Run the same real model assessment with and without a Pinecone-only source."""
    measured=MeasuredAI(provider);repo=MemoryRepository()
    app=create_app(repo,lambda token:Actor('synthetic-ablation-user','ablation@example.test','Synthetic evaluator'),measured)
    client=TestClient(app);headers={'Authorization':'Bearer synthetic-ablation'}
    created=client.post('/v1/plans',headers=headers,json={'title':'Synthetic Pinecone ablation','kind':'outing','start':'2027-05-14','end':'2027-05-16'})
    created.raise_for_status();plan=created.json();pid=plan['id']
    repo.state['plans'][pid]['budget']=50;repo.state['plans'][pid]['location']='Austin'
    option={'name':'Synthetic quiet vegetarian patio dinner','details':'A quiet vegetarian dinner on an outdoor patio in Austin for $35 per person, with ingredients listed and no known access or allergy concerns.','estimated_cost_per_person':35}
    source_id='eval-pinecone-ablation-preference'
    preference=('For this synthetic trip, all four friends explicitly agreed they prefer a quiet outdoor dinner, '
                'vegetarian food, a maximum of $50 per person, and an Austin location. Everyone confirmed this preference.')
    source_record=create_synthetic_source(repo,pid,source_id,'Synthetic group agreement',preference)
    measured.measurements={};seeded=[source_record];cleanup_failures=[]
    try:
        provider.upsert(source_record);mark_synthetic_source_indexed(repo,source_record)
        preflight=wait_for_pinecone_sources(provider,pid,group_fit_query(option),[source_id])
        before=copy.deepcopy(repo.state);started=time.perf_counter()
        with_response=client.post('/v1/plans/'+pid+'/group-fit',headers=headers,json={'expected_revision':plan['revision'],'option':option})
        with_body=with_response.json();with_elapsed=round(time.perf_counter()-started,3)
        with_checks=response_checks(with_response,with_body,source_id)
        with_result={'expected_verdict':'needs_info','observed_verdict':with_body.get('verdict'),
                     'verdict_matches_expectation':with_body.get('verdict')=='needs_info',**with_checks,
                     'plan_state_unchanged':repo.state==before,'latency_seconds':with_elapsed,
                     'retrieval':dict(measured.measurements),'response':with_body}

        deletion_failures=cleanup_synthetic_sources(provider,seeded)
        cleanup_failures.extend(deletion_failures)
        remove_synthetic_source(repo,source_record)
        absent=wait_for_pinecone_sources(provider,pid,group_fit_query(option),[source_id],present=False)
        measured.measurements={};before=copy.deepcopy(repo.state);started=time.perf_counter()
        without_response=client.post('/v1/plans/'+pid+'/group-fit',headers=headers,json={'expected_revision':plan['revision'],'option':option})
        without_body=without_response.json();without_elapsed=round(time.perf_counter()-started,3)
        without_checks=response_checks(without_response,without_body)
        without_result={'expected_verdict':'needs_info','observed_verdict':without_body.get('verdict'),
                        'verdict_matches_expectation':without_body.get('verdict')=='needs_info',**without_checks,
                        'plan_state_unchanged':repo.state==before,'latency_seconds':without_elapsed,
                        'retrieval':dict(measured.measurements),'response':without_body}
        comparison=compare_ablation_responses(with_body,without_body,source_id)
        result={'source_id':source_id,'pinecone_preflight':preflight,'pinecone_absence_check':absent,
                'with_retrieved_evidence':with_result,'after_removal':without_result,
                **comparison,
                'pinecone_evidence_cited':with_checks['expected_pinecone_source_cited'],
                'synthetic_input':{'preference':preference,'option':option}}
        return result,cleanup_failures
    finally:
        # Cleanup is idempotent and restricted to a random in-memory plan namespace.
        more_failures=cleanup_synthetic_sources(provider,seeded)
        for record in seeded:remove_synthetic_source(repo,record)
        cleanup_failures.extend(sid for sid in more_failures if sid not in cleanup_failures)


def main(argv=None):
    parser=argparse.ArgumentParser(description='Run synthetic Group Fit retrieval evaluation.')
    parser.add_argument('--ragas',action='store_true',help='Opt in to additional live Ragas scoring (extra OpenAI model and embedding calls).')
    parser.add_argument('--ragas-judge-model',default=os.getenv('RAGAS_JUDGE_MODEL','gpt-4o-mini'))
    parser.add_argument('--ragas-embedding-model',default=os.getenv('RAGAS_EMBEDDING_MODEL','text-embedding-3-small'))
    args=parser.parse_args(argv)
    if args.ragas and not os.getenv('OPENAI_API_KEY'):
        parser.error('--ragas requires OPENAI_API_KEY')
    run_started=datetime.now(timezone.utc)
    started=run_started.isoformat()
    rules=rule_checks()
    provider=ConnectedAI()
    _,_,_,measured,live,case_cleanup_failures=live_checks(provider)
    try:
        ablation,ablation_cleanup_failures=live_pinecone_ablation(provider)
        ablation_error=None
    except Exception as error:
        ablation=None;ablation_cleanup_failures=[];ablation_error=type(error).__name__

    seeded_cases=sum(bool(x.get('expected_pinecone_source_id')) for x in live)
    retrieved_top_k=sum(bool((x.get('preflight_query') or {}).get('matched_source_ids')) for x in live)
    retrieved_in_prompt=sum(x.get('expected_pinecone_source_in_prompt',False) for x in live)
    latencies=[x['latency_seconds'] for x in live if isinstance(x.get('latency_seconds'),(int,float))]
    cleanup_failures=case_cleanup_failures+ablation_cleanup_failures
    ragas_evaluation=None;ragas_error_type=None
    if args.ragas:
        try:
            ragas_evaluation=score_with_ragas_sync(
                measured.ragas_rows,os.getenv('OPENAI_API_KEY'),
                args.ragas_judge_model,args.ragas_embedding_model)
        except Exception as error:
            ragas_error_type=type(error).__name__
    artifact={
        'title':'Tagalong Group Fit synthetic Pinecone retrieval evaluation',
        'started_at_utc':started,'completed_at_utc':datetime.now(timezone.utc).isoformat(),
        'model':provider.model,
        'scope':'Synthetic MemoryRepository plans only. Positive cases upsert synthetic message evidence into random plan namespaces, verify it appears in Pinecone semantic top-k, then call the real Group Fit endpoint and OpenAI model. Synthetic vectors are deleted after each case. No production database, real plan, account, or index namespace is used.',
        'source_sha256':{str(path.relative_to(BACKEND)):hashlib.sha256(path.read_bytes()).hexdigest() for path in [BACKEND/'tagalong/group_fit.py',BACKEND/'tagalong/providers.py',BACKEND/'tagalong/rag_evaluation.py',BACKEND/'tagalong/ragas_eval.py',BACKEND/'scripts/evaluate_group_fit.py',BACKEND/'tests/test_group_fit.py']},
        'rule_evaluation':rules,
        'live_evaluation':{'case_count':len(live),
            'validated_responses':sum(x.get('validated_response',False) for x in live),
            'expected_verdict_matches':sum(x.get('verdict_matches_expectation',False) for x in live),
            'seeded_retrieval_cases':seeded_cases,'expected_sources_in_pinecone_top_k':retrieved_top_k,
            'expected_sources_in_model_prompt':retrieved_in_prompt,
            'unchanged_state_cases':sum(x.get('plan_state_unchanged',False) for x in live),'cases':live},
        'live_ablation':ablation,'live_ablation_error_type':ablation_error,
        'ragas_evaluation':{'enabled':args.ragas,'judge_model':args.ragas_judge_model if args.ragas else None,
            'embedding_model':args.ragas_embedding_model if args.ragas else None,
            'result':ragas_evaluation,'error_type':ragas_error_type},
        'cleanup_failed_source_ids':cleanup_failures,
        'limitations':['This is a small synthetic demonstration, not a representative quality benchmark.',
            'The live ablation tests whether a uniquely indexed synthetic group message is retrieved, cited, and changes the assessment findings when removed. Safety uncertainty can correctly keep the verdict at needs_info in both runs; one pair does not establish broad retrieval precision or recall.',
            'Citation ID validity and model citations do not prove semantic entailment, truth, or safety; human citation entailment remains unscored.',
            'Budget and missing-evidence rules are deterministic, so those outcomes are not model-only reasoning tests.',
            'The sequential run is not a load test or latency percentile study.',
            'No real menu, allergy safety, current prices, availability, booking or calendar action is verified.']}

    destination=BACKEND.parent/'docs/evaluations';destination.mkdir(parents=True,exist_ok=True)
    stem=destination/(run_started.strftime('%Y-%m-%dT%H%M%SZ')+'-group-fit-rag-evaluation')
    stem.with_suffix('.json').write_text(json.dumps(artifact,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# Group Fit live synthetic Pinecone retrieval evaluation','',f'Run started (UTC): {started}',f"Model: `{provider.model}`",'',artifact['scope'],'',
        '## Reproduce','','From `tagalong/backend`:','','```powershell',"$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'",'.\\.venv\\Scripts\\python.exe scripts\\evaluate_group_fit.py','```','',
        'The runner uses existing OpenAI and Pinecone credentials only for synthetic provider calls. It creates random in-memory plans and `eval-` source IDs, checks actual Pinecone top-k retrieval, and deletes only vectors it created. It does not write to the production database or production plan namespaces. Each run creates new timestamped artifacts.','',
        '## Deterministic rule and security scenarios','',f"{rules['passed']}/{rules['total']} tests passed; exit code {rules['exit_code']}; {rules['seconds']} seconds.",'','| Check | Passing scenarios |','|---|---|']
    lines.extend(f"| {key.replace('_',' ')} | {value['passed']}/{value['total']} |" for key,value in rules['metrics'].items())
    lines+=['','## Live cases','','| Case | Expected | Observed | Pinecone evidence in prompt | Valid citation IDs | Seconds |','|---|---|---|---|---|---|']
    lines.extend(f"| {x.get('case','unknown')} | {x.get('expected_verdict','?')} | {x.get('observed_verdict') or 'HTTP '+str(x.get('http_status','?'))} | {'yes' if x.get('expected_pinecone_source_in_prompt') else 'no / N/A'} | {'yes' if x.get('citation_ids_valid') is True else 'N/A (no findings)' if x.get('citation_ids_valid') is None else 'no'} | {x.get('latency_seconds','—')} |" for x in live)
    lines+=['',f'Indexed source checks: {retrieved_top_k}/{seeded_cases} found in Pinecone top-k; {retrieved_in_prompt}/{seeded_cases} reached the model prompt.','',
        '## Same-option live ablation','',
        f"Pinecone evidence cited: {ablation.get('pinecone_evidence_cited') if ablation else 'not completed'}.",
        f"Verdict changed after source removal: {ablation.get('verdict_changed') if ablation else 'not completed'}; substantive response content changed: {ablation.get('response_content_changed') if ablation else 'not completed'}.",
        f"Evidence materially changed the response: {ablation.get('evidence_materially_changed_response') if ablation else 'not completed'} (the Pinecone-sourced group match is cited only when evidence is present).",
        f"With evidence: `{ablation.get('with_retrieved_evidence',{}).get('observed_verdict','not completed') if ablation else 'not completed'}`; after removal: `{ablation.get('after_removal',{}).get('observed_verdict','not completed') if ablation else 'not completed'}`.",
        f"Ablation error type: `{ablation_error or 'none'}`. Cleanup failures: `{cleanup_failures or 'none'}`.",'','## Limits','']
    lines+=['','## Ragas scoring','',
        ('Not run. Enable with `--ragas`; this adds OpenAI judge and embedding calls.' if not args.ragas else
         f"Status: `{(ragas_evaluation or {}).get('status', 'failed')}`. Judge: `{args.ragas_judge_model}`; embeddings: `{args.ragas_embedding_model}`; error type: `{ragas_error_type or 'none'}`."),
        'Ragas Faithfulness uses the complete evidence passed to generation. Context Precision and Context Recall use only Pinecone-retrieved context, with the synthetic scenario preference as reference. The missing-evidence case has no reference and is skipped for those retrieval metrics. Scores are diagnostic on a tiny synthetic set, not a production-quality benchmark.','']
    if ragas_evaluation:
        lines+=['| Metric | Mean | Scored cases | Errors |','|---|---:|---:|---:|']
        lines.extend(f"| {name} | {stats['mean'] if stats['mean'] is not None else '—'} | {stats['scored_cases']} | {stats['errors']} |" for name,stats in ragas_evaluation['aggregate'].items())
    lines.extend('- '+item for item in artifact['limitations'])
    lines+=['','See the adjacent JSON for per-case query hits, evidence origins, source IDs, responses, timings, and code hashes.']
    stem.with_suffix('.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

    ablation_pass=bool(ablation and ablation['evidence_materially_changed_response']
        and ablation['with_retrieved_evidence']['verdict_matches_expectation']
        and ablation['after_removal']['verdict_matches_expectation'])
    pass_run=(rules['exit_code']==0 and artifact['live_evaluation']['validated_responses']==len(live)
        and artifact['live_evaluation']['expected_verdict_matches']==len(live)
        and retrieved_top_k==seeded_cases and retrieved_in_prompt==seeded_cases
        and ablation_pass and not cleanup_failures
        and (not args.ragas or bool(ragas_evaluation and ragas_evaluation.get('status')=='completed')))
    print(json.dumps({'artifacts':str(stem),'rules_passed':rules['passed'],'rules_total':rules['total'],
        'live_validated':artifact['live_evaluation']['validated_responses'],'live_cases':len(live),
        'retrieval_sources_found':retrieved_top_k,'retrieval_cases':seeded_cases,
        'ablation_passed':ablation_pass,'cleanup_failures':cleanup_failures,
        'ragas_enabled':args.ragas,'ragas_status':(ragas_evaluation or {}).get('status','failed' if args.ragas else 'disabled'),
        'median_seconds':round(statistics.median(latencies),3) if latencies else None}))
    return 0 if pass_run else 1


if __name__=='__main__':raise SystemExit(main())
