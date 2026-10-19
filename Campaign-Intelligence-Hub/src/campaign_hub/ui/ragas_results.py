"""Display saved assessments without importing RAGAS or invoking models in the UI."""
import json
import pandas as pd
import streamlit as st

LABELS={'ragas_faithfulness':'RAGAS faithfulness','ragas_context_precision':'RAGAS context precision',
        'ragas_context_recall':'RAGAS context recall'}


def show_ragas(service):
    st.subheader('RAGAS answer and passage assessment')
    local=service.settings.data/'runs/ragas/latest/results.json'
    bundled=service.settings.root/'docs/evaluation/ragas-smoke-results.json'
    path=local if local.exists() else bundled
    if not path.exists():
        st.info('No RAGAS assessment is saved. The owner can run evaluate --ragas with the optional evaluation dependencies; no scores have been substituted.')
        return
    try:
        rows=json.loads(path.read_text(encoding='utf-8'))
        if not rows:
            st.info('The saved RAGAS run contains no assessed cases.')
            return
        if any(r['identity'].get('corpus')!=service.corpus_hash or r['identity'].get('framework')!='ragas'
               or r['identity'].get('assessment_version')!=1 for r in rows):
            st.warning('Saved RAGAS results belong to a different corpus or assessment version. Run a fresh assessment.')
            return
        records=[]
        for r in rows:
            identity=r['identity']
            records.append({**{k:v for k,v in r.items() if k not in ('identity','sample','chunk_ids','document_ids')},
                'judge_profile':identity['judge_provider']+' / '+identity['judge_model']
                    +' / precision prompt v'+str(identity.get('precision_prompt_version',1))
                    +' / JSON '+str(identity.get('judge_json_mode','unrecorded')),
                'generation_profile':identity['generation_provider']+' / '+identity['generation_model']})
        df=pd.DataFrame(records)
    except (OSError,ValueError,KeyError,TypeError):
        st.warning('Saved RAGAS results could not be read; the owner should rerun the assessment.')
        return
    st.caption('Saved model-judged measurements. The recorded generator/judge profiles can differ from this live app. A smoke sample is not a full benchmark; using the same model as generator and judge is not independent validation.')
    for note in dict.fromkeys(r.get('verification_note','') for r in rows):
        if note:st.caption('Run note: '+note)
    st.dataframe(df,alt='Saved RAGAS scores, judge profiles, failures and measurement coverage')
    for metric,label in LABELS.items():
        measured=df[df[metric].notna()] if metric in df else pd.DataFrame()
        st.caption(f'{label}: {len(measured)} of {len(df)} cases have measured scores.')
        if len(measured):
            st.subheader(label)
            chart=measured.groupby(['chunking','retrieval','reranking','generation_profile','judge_profile'])[metric].mean().reset_index()
            chart['configuration']=chart['chunking']+' / '+chart['retrieval']+' / rerank '+chart['reranking'].astype(str)+' / generator '+chart['generation_profile']+' / judge '+chart['judge_profile']
            st.bar_chart(chart,x='configuration',y=metric,alt=label+' by recorded retrieval, generator and judge configuration')
    st.info('Failed, empty and abstention faithfulness judgments remain unavailable. These RAGAS scores are separate from document-ID precision/recall and do not guarantee factual correctness.')
    with st.expander('Inspect assessed answers, ranked passages and reference answers'):
        st.json(rows)
