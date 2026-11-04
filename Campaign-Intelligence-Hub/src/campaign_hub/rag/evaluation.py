"""Versioned question-only evaluation; historical report scores are never loaded."""
import hashlib,itertools,json,time
from pathlib import Path
from campaign_hub.models import RetrievalOptions,FALLBACK
from campaign_hub.evaluation.metrics import retrieval_metrics

VERSION='pure-rag-v2'


def evaluation_cases(data,split='held_out'):
    if split not in ('held_out','development'):raise ValueError('Choose held_out or development')
    cases=json.loads((Path(data)/'evaluation/questions.json').read_text(encoding='utf-8'))
    return [c for c in cases if c['split']==split and c['kind'] in ('question','unsupported')]


def configurations(include_reranking=False):
    from campaign_hub.chunking.pipeline import STRATEGIES
    return [RetrievalOptions(chunking=c,retrieval=r,reranking=k)
            for c,r,k in itertools.product(STRATEGIES,('dense','hybrid'),(False,True) if include_reranking else (False,))]


def run_identity(service,options,cases,generated,embedding_config=None):
    from campaign_hub.rag.grounding import generation_prompt_identity
    from campaign_hub.embeddings.providers import create_embedder
    from campaign_hub.vectordb.chroma_store import default_chunking_config
    return {'runner_version':VERSION,'corpus':service.corpus_hash,
        'embedding_config':embedding_config if embedding_config is not None else create_embedder(service.settings).identity,
        'chunking_config':default_chunking_config(options.chunking),'options':options.model_dump(),
        'generation_provider':service.settings.generation_provider if generated else None,
        'generation_model':service.settings.generation_model if generated else None,
        **({'generation_prompt_sha256':generation_prompt_identity()} if generated else {}),
        'generated':generated,'case_set_hash':hashlib.sha256(json.dumps(cases,sort_keys=True).encode()).hexdigest()}


def run_evaluation(service,output=None,*,split='held_out',smoke=False,generated=False,include_reranking=False):
    output=Path(output or service.settings.data/'runs/rag/latest');output.mkdir(parents=True,exist_ok=True)
    all_cases=evaluation_cases(service.settings.data,split)
    cases=all_cases[:1] if smoke else all_cases
    rows=[]
    (output/'results.json').write_text('[]',encoding='utf-8')
    for options in configurations(include_reranking):
        identity=run_identity(service,options,all_cases,generated)
        for case in cases:
            start=time.perf_counter()
            row={**options.model_dump(),'identity':identity,'case_id':case['id'],'case_kind':case['kind'],
                'split':split,'expected_cases_per_configuration':len(all_cases),'smoke':smoke,
                'faithfulness':None,'faithfulness_note':'Not measured; retrieval and source checks are not entailment judgments.',
                'generation_skipped':not generated,'answer':None,'error':None}
            row.update(retrieval_seconds=None,answer_seconds=None)
            try:
                if generated:
                    result=service.answer_question(case['question'],case.get('campaign_id'),options)
                    docs=[h['chunk']['metadata']['document_id'] for h in result['hits']]
                    row['answer']=result['answer']
                    row['retrieval_seconds']=result.get('retrieval_seconds')
                    row['answer_seconds']=result.get('latency_seconds')
                    row['abstention_accuracy']=float(result['answer']==FALLBACK) if case['kind']=='unsupported' else None
                else:
                    hits=service.search(case['question'],case.get('campaign_id'),options)
                    row['retrieval_seconds']=time.perf_counter()-start
                    docs=[h.chunk.metadata['document_id'] for h in hits]
                row.update(retrieval_metrics(docs,case['expected_sources']))
                if not case['expected_sources']:
                    row['context_precision']=None;row['context_recall']=None
                    row['mrr']=None;row['ndcg']=None
                row['retrieved_documents']=docs
            except Exception as error:row['error']=str(error)
            row['latency_seconds']=time.perf_counter()-start
            rows.append(row)
            (output/'results.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
    return rows


def load_current_results(service):
    path=service.settings.data/'runs/rag/latest/results.json'
    if not path.exists():return []
    try:
        service.ensure_current()
        rows=json.loads(path.read_text(encoding='utf-8'))
        from campaign_hub.embeddings.providers import create_embedder
        embedding_config=create_embedder(service.settings).identity
        expected={};sets={}
        for row in rows:
            options=RetrievalOptions(**{k:row[k] for k in RetrievalOptions.model_fields if k in row})
            split=row['split']
            if split not in sets:sets[split]=evaluation_cases(service.settings.data,split)
            generated=row['identity']['generated']
            key=(split,options.model_dump_json(),generated)
            if key not in expected:expected[key]=run_identity(service,options,sets[split],generated,embedding_config)
            if row['identity']!=expected[key]:return []
        return rows
    except (OSError,ValueError,TypeError,KeyError):return []


def evaluation_coverage(rows):
    """Keep failed configurations in denominators instead of dropping them."""
    groups={}
    for row in rows:
        key=tuple(row[k] for k in ('split','chunking','retrieval','reranking'))
        item=groups.setdefault(key,{'split':key[0],'chunking':key[1],'retrieval':key[2],
            'reranking':key[3],'expected':0,'completed_ids':set(),'precision_ids':set(),'recall_ids':set()})
        item['expected']=max(item['expected'],row['expected_cases_per_configuration'])
        if not row.get('error'):
            item['completed_ids'].add(row['case_id'])
            if row.get('context_precision') is not None:item['precision_ids'].add(row['case_id'])
            if row.get('context_recall') is not None:item['recall_ids'].add(row['case_id'])
    return [{k:v for k,v in item.items() if not k.endswith('_ids')}|
            {'completed':len(item['completed_ids']),'precision_measured':len(item['precision_ids']),
             'recall_measured':len(item['recall_ids'])} for item in groups.values()]
