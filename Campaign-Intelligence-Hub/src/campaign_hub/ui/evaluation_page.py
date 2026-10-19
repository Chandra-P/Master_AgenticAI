import json
import pandas as pd
import streamlit as st


def results_path(settings):
    latest=settings.data/'runs/latest/results.json'
    bundled=settings.root/'docs/evaluation/three-chunking-results.json'
    if latest.exists() and bundled.exists():
        try:
            rows=json.loads(latest.read_text(encoding='utf-8'))
            if any(r.get('identity',{}).get('runner_version')!=6 for r in rows):
                return bundled
        except (ValueError,TypeError,AttributeError):
            return bundled
    return latest if latest.exists() or not bundled.exists() else bundled


def show(service,options):
    st.header('Evaluation dashboard')
    st.caption('Only measured runs appear here. Errors and unavailable judgments remain visible.')
    path=results_path(service.settings)
    if st.button('Run twelve-configuration retrieval smoke experiment',type='primary'):
        try:
            from campaign_hub.evaluation.runner import run_experiments
            with st.spinner('Running actual retrieval experiments, including cross-encoder reranking…'):
                run_experiments(service,service.settings.data/'runs/latest',smoke=True,use_llm=False)
            path=results_path(service.settings)
        except Exception as error:
            st.error(str(error))
    if not path.exists():
        st.info('No evaluations have been run. Build all three indexes, then run a smoke experiment or use the evaluation CLI.')
        return
    rows=json.loads(path.read_text(encoding='utf-8'))
    if any(r.get('identity',{}).get('runner_version')!=6 for r in rows):
        st.warning('These measurements use an earlier citation-scoring version. Run a fresh evaluation before comparing performance.')
        return
    if path.parent.name=='evaluation':
        st.caption('Bundled development-machine CPU measurements; these are not hosted latency or generated-answer faithfulness benchmarks.')
        if (service.settings.data/'runs/latest/results.json').exists():
            st.caption('An older or unreadable saved run is preserved; the bundled comparison uses the current citation-scoring version.')
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
    if any(r.get('identity',{}).get('chunking_config')!=default_chunking_config(r.get('chunking','section')) for r in rows):
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
    for metric,label in [('mrr','Retrieval relevance (MRR@5)'),('context_precision','Context precision'),('context_recall','Context recall'),('latency_seconds','Latency in seconds'),('answer_completeness','Expected-fact completeness proxy'),('faithfulness','Model-judged faithfulness'),('document_citation_accuracy','Gold document citation overlap'),('citation_accuracy','Gold section citation overlap (fully resolved cases only)'),('section_citation_resolution','Resolved citation section fraction')]:
        if metric in good and good[metric].notna().any():
            st.subheader(label)
            chart=good.groupby(['chunking','retrieval','reranking'])[metric].mean().reset_index()
            chart['configuration']=chart['chunking']+' / '+chart['retrieval']+' / rerank '+chart['reranking'].astype(str)
            st.bar_chart(chart,x='configuration',y=metric,alt=label+' across measured configurations')
    st.info('Faithfulness requires a separate entailment judgment. Missing values are unavailable, not zero or perfect scores.')
    if 'error' in df and df['error'].notna().any():
        st.warning(f"{df['error'].notna().sum()} configurations/questions failed. Inspect error rows before drawing conclusions.")
