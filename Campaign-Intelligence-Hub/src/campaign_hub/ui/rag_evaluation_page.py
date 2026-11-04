"""Current RAG results only; no historical report metrics or bundled fallbacks."""
import pandas as pd
import streamlit as st
from campaign_hub.rag.evaluation import evaluation_cases,load_current_results,run_evaluation,evaluation_coverage


def show(service,options):
    st.header('RAG evaluation')
    st.caption('Question-only measurements for the current corpus, embedding model and chunkers.')
    from campaign_hub.ui.current_ragas_results import show_current_ragas
    show_current_ragas(service)
    split=st.selectbox('Question set',['held_out','development'],key='rag-evaluation-split')
    cases=evaluation_cases(service.settings.data,split)
    st.caption(f'{len(cases)} eligible cases. Development examples demonstrate behavior; they are not held-out validation.')
    if st.button('Run retrieval smoke evaluation',key='rag-evaluation-run'):
        try:
            with st.spinner('Running six measured retrieval configurations; no answer generation…'):
                run_evaluation(service,split=split,smoke=True)
        except Exception:
            st.error('Evaluation failed. Check that all three compatible indexes are built.')
    rows=[row for row in load_current_results(service) if row['split']==split]
    if not rows:
        st.info('No compatible current RAG evaluation is saved. Historical report and earlier-corpus scores are excluded.')
        return
    df=pd.DataFrame(rows)
    st.dataframe(df.drop(columns=['identity','answer'],errors='ignore'),alt='Current question-only RAG evaluation rows')
    successful=df[df.error.isna()]
    for metric,label in [('context_precision','Document precision'),('context_recall','Document recall'),
                         ('mrr','MRR at 5'),('retrieval_seconds','Retrieval latency (seconds)'),
                         ('answer_seconds','End-to-end answer latency (seconds)'),
                         ('latency_seconds','Total evaluation execution time (seconds)')]:
        if metric in successful and successful[metric].notna().any():
            st.subheader(label)
            chart=successful.groupby(['split','chunking','retrieval','reranking'])[metric].mean().reset_index()
            chart['configuration']=chart['split']+' / '+chart['chunking']+' / '+chart['retrieval']+' / rerank '+chart['reranking'].astype(str)
            st.bar_chart(chart,x='configuration',y=metric,alt=label+' by actual measured configuration')
    coverage=pd.DataFrame(evaluation_coverage(rows))
    st.dataframe(coverage,alt='Completed cases versus expected cases for every measured configuration')
    if rows[0].get('smoke'):st.warning('Smoke evaluation only: one case per configuration, not a complete benchmark.')
    st.info('Faithfulness is unavailable here. Document precision/recall and validated citations do not establish generated-answer faithfulness.')
    if df.error.notna().any():st.warning('Failed cases remain visible and do not count as measured successes.')
