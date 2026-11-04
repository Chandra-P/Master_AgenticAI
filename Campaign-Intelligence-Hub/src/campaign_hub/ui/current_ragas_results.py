"""Only current, calibrated question-answer assessments; no report-era fallback."""
from campaign_hub.rag.grounding import generation_prompt_identity
import hashlib
import json
import math
from campaign_hub.models import RetrievalOptions

# The optional stack is pinned and verified in requirements-ragas.txt.
TESTED_RAGAS_VERSION="0.3.9"


def _current_judge_contract(identity):
    from campaign_hub.evaluation.precision_prompt import PRECISION_PROMPT_VERSION,PRECISION_PROMPT_SHA256,CALIBRATION_VERSION
    return (identity.get('version')==TESTED_RAGAS_VERSION
        and identity.get('precision_prompt_version')==PRECISION_PROMPT_VERSION
        and identity.get('precision_prompt_sha256')==PRECISION_PROMPT_SHA256
        and identity.get('judge_calibration',{}).get('version')==CALIBRATION_VERSION
        and identity.get('judge_provider') in ('ollama','groq','openai')
        and isinstance(identity.get('judge_model'),str) and bool(identity['judge_model']))


def load_current_calibrations(service):
    from campaign_hub.embeddings.providers import create_embedder
    from campaign_hub.vectordb.chroma_store import default_chunking_config
    try:
        service.ensure_current()
        cases=json.loads((service.settings.data/'evaluation/questions.json').read_text(encoding='utf-8'))
        embedding=create_embedder(service.settings).identity
        accepted=[]
        for name in ('ragas','quality'):
            path=service.settings.data/'runs'/name/'latest/calibration-status.json'
            if not path.is_file():continue
            for status in json.loads(path.read_text(encoding='utf-8')):
                identity=status['identity'];options=RetrievalOptions(**identity['options'])
                expected=[c for c in cases if c['split']=='held_out' and
                    (c['kind']=='question' or identity['quality_assessment'] and c['kind']=='unsupported')]
                required={'framework':'ragas','assessment_version':3,'context_format':'source-json-v1','corpus':service.corpus_hash,
                    'embedding_config':embedding,'chunking_config':default_chunking_config(options.chunking),
                    'generation_provider':service.settings.generation_provider,'generation_model':service.settings.generation_model,
                    'generation_prompt_sha256':generation_prompt_identity(),
                    'case_set_hash':hashlib.sha256(json.dumps(expected,sort_keys=True).encode()).hexdigest()}
                if (_current_judge_contract(identity) and all(identity.get(k)==v for k,v in required.items())
                    and status.get('calibration')==identity.get('judge_calibration')):
                    accepted.append(status)
        return accepted
    except (OSError,ValueError,TypeError,KeyError):return []


def load_current_ragas(service):
    from campaign_hub.embeddings.providers import create_embedder
    from campaign_hub.vectordb.chroma_store import default_chunking_config
    paths=[service.settings.data/'runs'/name/'latest/results.json' for name in ('ragas','quality')]
    try:
        service.ensure_current()
        cases=json.loads((service.settings.data/'evaluation/questions.json').read_text(encoding='utf-8'))
        embedding=create_embedder(service.settings).identity
        accepted=[]
        for path in paths:
            if not path.is_file():continue
            rows=json.loads(path.read_text(encoding='utf-8'))
            if not isinstance(rows,list):continue
            current=[]
            for row in rows:
                identity=row['identity']
                if not _current_judge_contract(identity):break
                quality=identity['quality_assessment']
                expected=[c for c in cases if c['split']=='held_out' and
                          (c['kind']=='question' or quality and c['kind']=='unsupported')]
                case=next(c for c in expected if c['id']==row['case_id'])
                options=RetrievalOptions(**identity['options'])
                required={'framework':'ragas','assessment_version':3,'context_format':'source-json-v1','corpus':service.corpus_hash,
                    'embedding_config':embedding,'chunking_config':default_chunking_config(options.chunking),
                    'generation_provider':service.settings.generation_provider,'generation_model':service.settings.generation_model,
                    'generation_prompt_sha256':generation_prompt_identity(),
                    'case_id':case['id'],'reference_hash':hashlib.sha256(case['expected_answer'].encode()).hexdigest(),
                    'case_set_hash':hashlib.sha256(json.dumps(expected,sort_keys=True).encode()).hexdigest()}
                if any(identity.get(k)!=v for k,v in required.items()):break
                if any(row.get(k)!=v for k,v in options.model_dump().items()):break
                if row.get('judge_calibration_passed') is not True or identity.get('judge_calibration',{}).get('passed') is not True:break
                sample=row.get('sample',{})
                if sample.get('user_input')!=case['question'] or sample.get('reference')!=case['expected_answer']:break
                if not isinstance(sample.get('response'),str) or not isinstance(sample.get('retrieved_contexts'),list):break
                current.append(row)
            else:
                accepted.extend(current)
        return accepted
    except (OSError,ValueError,TypeError,KeyError,StopIteration):
        return []


def show_current_ragas(service):
    import pandas as pd
    import streamlit as st
    st.subheader('Generated-answer RAGAS assessment')
    statuses=load_current_calibrations(service)
    for status in statuses:
        identity=status['identity'];calibration=status['calibration']
        if calibration.get('passed') is not True:
            controls=calibration.get('controls',[])
            failed=sum(c.get('passed') is not True for c in controls)
            st.warning(f"Current judge calibration failed: {identity['judge_provider']} / {identity['judge_model']}; {failed} of {len(controls)} controls failed. Metrics from this judge remain unavailable.")
    rows=load_current_ragas(service)
    if not rows:
        st.info('No calibrated current-corpus RAGAS assessment is saved. Run the opt-in CLI assessment; historical report scores are excluded.')
        return
    metrics=['ragas_factual_correctness','ragas_faithfulness','ragas_context_precision','ragas_context_recall','passage_relevance_precision']
    from campaign_hub.evaluation.quality import reference_f1_summary
    cases=json.loads((service.settings.data/'evaluation/questions.json').read_text(encoding='utf-8'))
    supported=[c['id'] for c in cases if c['split']=='held_out' and c['kind']=='question']
    groups={}
    for row in rows:
        identity=row['identity']
        key=json.dumps({'options':identity['options'],'judge_provider':identity['judge_provider'],'judge_model':identity['judge_model']},sort_keys=True)
        groups.setdefault(key,[]).append(row)
    for group in groups.values():
        summary=reference_f1_summary(group,supported)
        if summary['complete']:
            options=group[0]['identity']['options']
            st.caption(f"Reference F1: {summary['score']:.1%} across all {summary['expected']} supported questions; {summary['answered']} answered, genuine refusals count as zero. Profile: {options['chunking']} / {options['retrieval']} / k={options['final_k']}. Development benchmark, not independent certification.")
    display=[]
    for row in rows:
        item={k:row.get(k) for k in ('case_id','chunking','retrieval','reranking','error')}
        item.update(judge_provider=row['identity'].get('judge_provider'),judge_model=row['identity'].get('judge_model'))
        for metric in metrics:
            value=row.get(metric)
            item[metric]=value if not row.get('error') and isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value) and 0<=value<=1 else None
        display.append(item)
    st.dataframe(pd.DataFrame(display),alt='Calibrated current generated-answer RAGAS measurements')
    st.caption('Faithfulness judges the actual generated answer against exact retrieved passages. RAGAS context precision is rank weighted; passage relevance precision is the useful-passage fraction. Missing or failed judgments remain unavailable. Partial runs are not full benchmark claims.')
