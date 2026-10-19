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


async def score_sample(sample,metrics,sample_factory,timeout=180):
    result={name:None for name in metrics};result['metric_errors']={}
    record=sample_factory(**sample)
    for name,metric in metrics.items():
        if not sample['retrieved_contexts']:
            result['metric_errors'][name]='No retrieved passages; metric unavailable.'
            continue
        if name=='ragas_faithfulness' and (not sample['response'].strip() or sample['response']==FALLBACK):
            result['metric_errors'][name]='Abstention or empty response; faithfulness unavailable.'
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
    def __init__(self,settings):
        os.environ['RAGAS_DO_NOT_TRACK']='true'
        try:
            from ragas import SingleTurnSample
            from ragas.llms import LangchainLLMWrapper
            from ragas.metrics import Faithfulness,LLMContextPrecisionWithReference,LLMContextRecall
            from ragas.run_config import RunConfig
        except ImportError as error:
            raise RuntimeError('Install optional evaluation dependencies: pip install -r requirements-ragas.txt') from error
        from campaign_hub.generation.providers import create_generator
        model=create_generator(settings).model
        if settings.generation_provider=='ollama':
            model=model.model_copy(update={'num_predict':2048,'num_ctx':8192,'format':'json'})
        else:
            model=model.model_copy(update={'max_tokens':2048,
                'model_kwargs':{**model.model_kwargs,'response_format':{'type':'json_object'}}})
        wrapper=LangchainLLMWrapper(model,run_config=RunConfig(timeout=180,max_retries=1,max_workers=1))
        from campaign_hub.evaluation.precision_prompt import create_precision_prompt
        precision_prompt=create_precision_prompt(model,settings.generation_provider)
        self.metrics=dict(zip(METRICS,[Faithfulness(llm=wrapper),
            LLMContextPrecisionWithReference(llm=wrapper,context_precision_prompt=precision_prompt),LLMContextRecall(llm=wrapper)]))
        self.sample_factory=SingleTurnSample
        self._runner=asyncio.Runner()
        self.identity={'framework':'ragas','version':version('ragas'),'assessment_version':1,
            'judge_provider':settings.generation_provider,'judge_model':settings.generation_model,
            'judge_context_tokens':8192 if settings.generation_provider=='ollama' else None,
            'judge_output_tokens':2048,'judge_json_mode':True,'metric_timeout_seconds':180,'metrics':list(METRICS)}
        self.identity.update(precision_prompt_version=2,precision_output_tokens=256,
            precision_prompt_sha256=hashlib.sha256(precision_prompt.to_string().encode()).hexdigest())

    def assess(self,sample):
        return self._runner.run(score_sample(sample,self.metrics,self.sample_factory))

    def __enter__(self):
        return self

    def __exit__(self,*args):
        self._runner.close()


def run_assessment(service,output,options,assessor,limit=1):
    """Evaluate held-out question answers, never retrieved text substituted as answers."""
    if limit<1:raise ValueError('Assessment case limit must be positive')
    from campaign_hub.embeddings.providers import create_embedder
    from campaign_hub.vectordb.chroma_store import default_chunking_config
    cases=json.loads((service.settings.data/'evaluation/questions.json').read_text(encoding='utf-8'))
    cases=[c for c in cases if c['split']=='held_out' and c['kind']=='question'][:limit]
    output=Path(output);output.mkdir(parents=True,exist_ok=True);rows=[]
    for config in options:
        for case in cases:
            identity={**assessor.identity,'corpus':service.corpus_hash,'options':config.model_dump(),
                'embedding_config':create_embedder(service.settings).identity,
                'chunking_config':default_chunking_config(config.chunking),
                'generation_provider':service.settings.generation_provider,'generation_model':service.settings.generation_model,
                'case_id':case['id'],'reference_hash':hashlib.sha256(case['expected_answer'].encode()).hexdigest()}
            row={**config.model_dump(),'case_id':case['id'],'identity':identity,
                **{m:None for m in METRICS},'metric_errors':{},'error':None,
                'created_at':datetime.now(timezone.utc).isoformat(),
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
                row['generation_seconds']=time.perf_counter()-started
                row.update(assessor.assess(row['sample']))
            except Exception as error:
                row['error']=f'{type(error).__name__}: generation or assessment failed; inspect owner configuration.'
            row['latency_seconds']=time.perf_counter()-started
            # Preserve every actual execution; never reuse an answer from a changed generator.
            key=hashlib.sha256(json.dumps(row,sort_keys=True).encode()).hexdigest()
            (output/(key+'.json')).write_text(json.dumps(row,indent=2,allow_nan=False),encoding='utf-8')
            rows.append(row)
    (output/'results.json').write_text(json.dumps(rows,indent=2,allow_nan=False),encoding='utf-8')
    import pandas as pd
    pd.DataFrame([{k:v for k,v in r.items() if not isinstance(v,(dict,list))} for r in rows]).to_csv(output/'results.csv',index=False)
    return rows
