"""Opt-in actual RAGAS metrics, kept separate from document-overlap proxies."""
import asyncio
import hashlib
import json
import math
import os
import time
from datetime import datetime,timezone
from importlib.metadata import version
from pathlib import Path
from campaign_hub.models import FALLBACK

METRICS=('ragas_faithfulness','ragas_context_precision','ragas_context_recall')


async def judge_controls(metric,sample_factory,timeout=75):
    """Known calibration examples; references must not be mistaken for passage evidence."""
    contexts=[('Acquire 180 verified product activations during 2026-Q2.',1),
        ('Campaign-specific eligibility incentive. Product suitability must be verified.',0),
        ('Approved budget: USD 24000.',0),('Digitally active local households; existing and prospective members.',0)]
    controls=[]
    for context,expected in contexts:
        sample={'user_input':'What was the campaign objective?','reference':'Acquire 180 verified product activations during 2026-Q2.',
            'response':'Acquire 180 verified product activations during 2026-Q2.','retrieved_contexts':[context]}
        result=await score_sample(sample,{'precision':metric},sample_factory,timeout)
        actual=result['precision']
        controls.append({'context':context,'expected':expected,'score':actual,
            'passed':actual is not None and abs(actual-expected)<.01})
    return {'version':1,'passed':all(c['passed'] for c in controls),'controls':controls}


async def score_sample(sample,metrics,sample_factory,timeout=180):
    result={name:None for name in metrics};result['metric_errors']={}
    record=sample_factory(**sample)
    for name,metric in metrics.items():
        if not sample['retrieved_contexts']:
            result['metric_errors'][name]='No retrieved passages; metric unavailable.'
            continue
        if name in ('ragas_faithfulness','ragas_factual_correctness') and (not sample['response'].strip() or sample['response']==FALLBACK):
            result['metric_errors'][name]='Abstention or empty response; claim assessment unavailable.'
            continue
        try:
            value=float(await asyncio.wait_for(metric.single_turn_ascore(record),timeout=timeout))
            if not math.isfinite(value) or not 0<=value<=1:
                raise ValueError('Invalid score')
            result[name]=value
        except Exception as error:
            # Provider exceptions can include request content or credentials.
            result['metric_errors'][name]=f'{type(error).__name__}: judgment failed or returned an invalid score.'
    return result


class RagasAssessor:
    def __init__(self,settings,quality=False,timeout=180):
        os.environ['RAGAS_DO_NOT_TRACK']='true'
        try:
            from ragas import SingleTurnSample
            from ragas.llms import LangchainLLMWrapper
            from ragas.metrics import Faithfulness,LLMContextPrecisionWithReference,LLMContextRecall
            from ragas.run_config import RunConfig
        except ImportError as error:
            raise RuntimeError('Install optional evaluation dependencies: pip install -r requirements-ragas.txt') from error
        from campaign_hub.generation.providers import create_generator
        provider_retries=5 if settings.generation_provider=='groq' else 1
        model=create_generator(settings,max_retries=provider_retries).model
        if settings.generation_provider=='ollama':
            model=model.model_copy(update={'num_predict':2048,'num_ctx':8192,'format':'json'})
        else:
            model=model.model_copy(update={'max_tokens':2048,
                'model_kwargs':{**model.model_kwargs,'response_format':{'type':'json_object'}}})
        wrapper=LangchainLLMWrapper(model,run_config=RunConfig(timeout=180,max_retries=1,max_workers=1))
        from campaign_hub.evaluation.precision_prompt import create_precision_prompt
        self.precision_verdicts=[]
        precision_prompt=create_precision_prompt(model,settings.generation_provider,verdict_sink=self.precision_verdicts)
        self.metrics=dict(zip(METRICS,[Faithfulness(llm=wrapper),
            LLMContextPrecisionWithReference(llm=wrapper,context_precision_prompt=precision_prompt),LLMContextRecall(llm=wrapper)]))
        if quality:
            from ragas.metrics import FactualCorrectness
            self.metrics['ragas_factual_correctness']=FactualCorrectness(llm=wrapper,mode='f1')
        self.timeout=timeout
        self.sample_factory=SingleTurnSample
        self._runner=asyncio.Runner()
        self.identity={'framework':'ragas','version':version('ragas'),'assessment_version':1,
            'judge_provider':settings.generation_provider,'judge_model':settings.generation_model,
            'judge_context_tokens':8192 if settings.generation_provider=='ollama' else None,
            'judge_output_tokens':2048,'judge_json_mode':True,'metric_timeout_seconds':timeout,'metrics':list(self.metrics),
            'judge_provider_max_retries':provider_retries,
            'quality_assessment':quality}
        self.identity.update(precision_prompt_version=2,precision_output_tokens=256,
            precision_prompt_sha256=hashlib.sha256(precision_prompt.to_string().encode()).hexdigest())

    def assess(self,sample):
        from campaign_hub.evaluation.quality import passage_precision
        verdicts=getattr(self,'precision_verdicts',None)
        if verdicts is not None:verdicts.clear()
        result=self._runner.run(score_sample(sample,self.metrics,self.sample_factory,getattr(self,'timeout',180)))
        if verdicts is not None:
            result['passage_verdicts']=list(verdicts)
            result['passage_relevance_precision']=passage_precision(verdicts,len(sample['retrieved_contexts'])) if result.get('ragas_context_precision') is not None else None
        return result

    def __enter__(self):
        if getattr(self,'identity',{}).get('quality_assessment'):
            self.judge_controls=self._runner.run(judge_controls(self.metrics['ragas_context_precision'],self.sample_factory,self.timeout))
            self.precision_verdicts.clear()
            self.identity['judge_calibration']=self.judge_controls
            print(f"Judge calibration passed: {self.judge_controls['passed']}",flush=True)
        return self

    def __exit__(self,*args):
        self._runner.close()


def run_assessment(service,output,options,assessor,limit=1,quality=False):
    """Evaluate held-out question answers, never retrieved text substituted as answers."""
    if limit<1:raise ValueError('Assessment case limit must be positive')
    from campaign_hub.embeddings.providers import create_embedder
    from campaign_hub.vectordb.chroma_store import default_chunking_config
    cases=json.loads((service.settings.data/'evaluation/questions.json').read_text(encoding='utf-8'))
    expected=[c for c in cases if c['split']=='held_out' and (c['kind']=='question' or quality and c['kind']=='unsupported')]
    cases=expected[:limit]
    output=Path(output);output.mkdir(parents=True,exist_ok=True);rows=[]
    if quality and assessor.identity.get('judge_calibration',{}).get('passed') is False:
        (output/'judge-controls.json').write_text(json.dumps(assessor.identity['judge_calibration'],indent=2),encoding='utf-8')
        print('Judge failed calibration; skipping answer assessments and leaving the quality target incomplete.',flush=True)
        cases=[]
    for config in options:
        for case in cases:
            identity={**assessor.identity,'corpus':service.corpus_hash,'options':config.model_dump(),
                'embedding_config':create_embedder(service.settings).identity,
                'chunking_config':default_chunking_config(config.chunking),
                'generation_provider':service.settings.generation_provider,'generation_model':service.settings.generation_model,
                'case_id':case['id'],'reference_hash':hashlib.sha256(case['expected_answer'].encode()).hexdigest()}
            row={**config.model_dump(),'case_id':case['id'],'case_kind':case['kind'],'identity':identity,
                **{m:None for m in METRICS},'metric_errors':{},'error':None,
                'created_at':datetime.now(timezone.utc).isoformat(),
                'judge_calibration_passed':assessor.identity.get('judge_calibration',{}).get('passed'),
                'same_generation_and_judge_model':(identity.get('judge_provider')==identity['generation_provider'] and identity.get('judge_model')==identity['generation_model'])}
            started=time.perf_counter()
            try:
                result=service.answer_question(case['question'],case['campaign_id'],config)
                row['sample']={'user_input':case['question'],'response':result['answer'],
                    'retrieved_contexts':[h['chunk']['text'] for h in result['hits']],
                    'reference':case['expected_answer']}
                row['chunk_ids']=[h['chunk']['chunk_id'] for h in result['hits']]
                row['document_ids']=[h['chunk']['metadata']['document_id'] for h in result['hits']]
                row['abstained']=result['answer']==FALLBACK
                row['answer_validation']={k:result.get(k) for k in ('accepted_claims','draft_claims')}
                row['generation_seconds']=time.perf_counter()-started
                if case['kind']=='unsupported':
                    row['assessment_note']='Unsupported-case abstention scored separately; no reference-answer judge required.'
                else:
                    row.update(assessor.assess(row['sample']))
            except Exception as error:
                row['error']=f'{type(error).__name__}: generation or assessment failed; inspect owner configuration.'
            row['latency_seconds']=time.perf_counter()-started
            # Preserve every actual execution; never reuse an answer from a changed generator.
            key=hashlib.sha256(json.dumps(row,sort_keys=True).encode()).hexdigest()
            (output/(key+'.json')).write_text(json.dumps(row,indent=2,allow_nan=False),encoding='utf-8')
            rows.append(row)
            print(f"Assessment {case['id']} complete; {row['latency_seconds']:.1f}s; error={bool(row['error'])}",flush=True)
    (output/'results.json').write_text(json.dumps(rows,indent=2,allow_nan=False),encoding='utf-8')
    import pandas as pd
    pd.DataFrame([{k:v for k,v in r.items() if not isinstance(v,(dict,list))} for r in rows]).to_csv(output/'results.csv',index=False)
    if quality:
        from campaign_hub.evaluation.quality import quality_summary
        summaries=[]
        for config in options:
            group=[r for r in rows if all(r[k]==v for k,v in config.model_dump().items())]
            summaries.append({'options':config.model_dump(),**quality_summary(group,
                [c['id'] for c in expected if c['kind']=='question'],[c['id'] for c in expected if c['kind']=='unsupported'])})
        (output/'quality-summary.json').write_text(json.dumps(summaries,indent=2,allow_nan=False),encoding='utf-8')
    return rows
