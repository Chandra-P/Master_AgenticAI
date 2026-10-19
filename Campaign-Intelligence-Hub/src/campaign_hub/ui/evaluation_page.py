import json
import pandas as pd
import streamlit as st


def show(service,options):
    st.header('Evaluation dashboard')
    st.caption('Only measured local runs appear here. Errors and unavailable judgments remain visible.')
    path=service.settings.data/'runs/latest/results.json'
    if st.button('Run eight-configuration retrieval smoke experiment',type='primary'):
        try:
            from campaign_hub.evaluation.runner import run_experiments
            with st.spinner('Running actual retrieval experiments, including cross-encoder reranking…'):
                run_experiments(service,path.parent,smoke=True,use_llm=False)
        except Exception as error:
            st.error(str(error))
    if not path.exists():
        st.info('No evaluations have been run. Build both indexes, then run a smoke experiment or use the evaluation CLI.')
        return
    rows=json.loads(path.read_text(encoding='utf-8'))
    if any(r.get('identity',{}).get('corpus')!=service.corpus_hash for r in rows):
        st.warning('These evaluation results belong to an earlier corpus. Run a fresh evaluation before comparing current performance.')
        return
    if any(r.get('identity',{}).get('embedding_provider','ollama')!=service.settings.embedding_provider
        or r.get('identity',{}).get('embedding')!=service.settings.embedding_model for r in rows):
        st.warning('These measurements use a different embedding provider/model. Run a fresh evaluation for this deployment profile.')
        return
    from campaign_hub.embeddings.providers import create_embedder
    from campaign_hub.vectordb.chroma_store import default_chunking_config
    embedding_config=create_embedder(service.settings).identity
    if any(r.get('identity',{}).get('embedding_config',embedding_config if service.settings.embedding_provider=='ollama' else None)!=embedding_config for r in rows):
        st.warning('These measurements use a different embedding configuration. Run a fresh evaluation for this deployment profile.')
        return
    if any(r.get('identity',{}).get('chunking_config')!=default_chunking_config() for r in rows):
        st.warning('These measurements lack the current chunking configuration. Run a fresh evaluation before comparing performance.')
        return
    generated=[r.get('identity',{}) for r in rows if r.get('identity',{}).get('use_llm') or r.get('identity',{}).get('judge')]
    if any(i.get('generation_provider','ollama')!=service.settings.generation_provider
        or i.get('generation')!=service.settings.generation_model for i in generated):
        st.warning('These measurements use a different generation provider/model. Run a fresh evaluation for this deployment profile.')
        return
    df=pd.DataFrame(rows)
    st.dataframe(df.drop(columns=['answer','identity','judgments'],errors='ignore'),alt='Actual evaluation results by configuration')
    good=df[df['error'].isna()] if 'error' in df else df
    for metric,label in [('mrr','Retrieval relevance (MRR@5)'),('context_precision','Context precision'),('context_recall','Context recall'),('latency_seconds','Latency in seconds'),('answer_completeness','Expected-fact completeness proxy'),('faithfulness','Model-judged faithfulness'),('citation_accuracy','Gold source/section citation overlap')]:
        if metric in good and good[metric].notna().any():
            st.subheader(label)
            chart=good.groupby(['chunking','retrieval','reranking'])[metric].mean().reset_index()
            chart['configuration']=chart['chunking']+' / '+chart['retrieval']+' / rerank '+chart['reranking'].astype(str)
            st.bar_chart(chart,x='configuration',y=metric,alt=label+' across measured configurations')
    st.info('Faithfulness requires a separate entailment judgment. Missing values are unavailable, not zero or perfect scores.')
    if 'error' in df and df['error'].notna().any():
        st.warning(f"{df['error'].notna().sum()} configurations/questions failed. Inspect error rows before drawing conclusions.")
