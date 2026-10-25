"""Analyst retrieval and shared scoped-question controls."""
import json
import streamlit as st
from campaign_hub.retrieval.filters import available_values

LABELS = {'campaign_id': 'Campaign ID', 'client_name': 'Client', 'campaign_type': 'Campaign type',
          'region': 'Region', 'year': 'Year', 'period': 'Reporting period', 'document_type': 'Document type'}


def show(service, options, campaign_id=None, answer=False):
    prefix = 'questions' if answer else 'analyst'
    if not answer:
        st.header('Analyst view')
        st.caption('Inspect how metadata constraints scope dense and hybrid retrieval. Ranking scores are not confidence scores.')
    automatic = st.checkbox('Automatically classify metadata', value=True, key=prefix+'-automatic')
    providers = ['ollama', 'openai']
    default = service.settings.classification_provider
    provider = st.selectbox('Classification provider', providers,
        index=providers.index(default) if default in providers else 0, key=prefix+'-provider', disabled=not automatic)
    default_model = (service.settings.classification_model if provider == default else
                     'gpt-4.1-mini' if provider == 'openai' else 'llama3.2:3b')
    model = st.text_input('Classification model', value=default_model,
                         key=prefix+'-model-'+provider, disabled=not automatic)
    if automatic and provider == 'openai':
        st.info('OpenAI classification sends your question and available metadata values to OpenAI using the server key.')
    catalog = available_values(service.manifest)
    # Inputs rerun cheaply to hide stale evidence immediately; only the button
    # below starts classification/retrieval, so edits never trigger model calls.
    question = st.text_area('Your question', value='What were the objectives?' if answer else
                           'Find performance reports for Texas campaigns in 2026.', key=prefix+'-query')
    filters = {}
    st.caption('Values within a field use OR. Different fields use AND. Manual choices remain binding.')
    with st.expander('Combined metadata filters'):
        for field, values in catalog.items():
            if campaign_id and field == 'campaign_id': continue
            selected = st.multiselect(LABELS[field], values, key=prefix+'-filter-'+field)
            if selected: filters[field] = selected
    submitted = st.button('Find evidence', type='primary', key=prefix+'-submit')
    fingerprint = json.dumps({'query': question, 'filters': filters, 'campaign': campaign_id,
        'automatic': automatic, 'provider': provider, 'model': model, 'options': options.model_dump(),
        'corpus': service.corpus_hash, 'answer_provider': service.settings.generation_provider,
        'answer_model': service.settings.generation_model}, sort_keys=True)
    cache_key = prefix+'-analysis'
    if submitted:
        st.session_state.pop(cache_key, None)
        try:
            with st.spinner('Classifying and retrieving evidence…'):
                kwargs = dict(filters=filters, automatic=automatic,
                              classification_provider=provider, classification_model=model)
                result = (service.answer_question(question, campaign_id, options, **kwargs) if answer else
                          service.analyze_query(question, options, campaign_id=campaign_id, **kwargs))
                st.session_state[cache_key] = (fingerprint, result)
        except (ValueError, RuntimeError) as error:
            st.error(str(error))
        except Exception:
            st.error('Retrieval failed. Check the embedding provider, selected index and reranker configuration.')
    cached = st.session_state.get(cache_key)
    if not cached or cached[0] != fingerprint: return
    result = cached[1]
    st.subheader('Applied filters')
    st.json({name: result.get(name) for name in
             ('manual_filters', 'scope_filters', 'inferred_filters', 'routing_filters', 'effective_filters')})
    if result.get('classification_provider'):
        st.caption(f"Classifier: {result['classification_provider']} · {result.get('classification_model', model)}")
    if result['status'] == 'filter_conflict':
        st.warning(result['message']+'. No search was run. Adjust the question or manual filters.')
        return
    if not result['hits']:
        st.info('No evidence matches these filters. Filters were not relaxed.')
        return
    if answer:
        st.markdown(result['answer'])
        st.caption('Answers retain source validation. Retrieval scores do not measure answer faithfulness.')
    st.subheader('Retrieved evidence')
    for rank, hit in enumerate(result['hits'], 1):
        chunk = hit['chunk']
        with st.expander(f"{rank}. {chunk['metadata'].get('document_id', chunk['chunk_id'])}"):
            st.json({'chunk_id': chunk['chunk_id'], **chunk['metadata']})
            st.code(chunk['text'], language='markdown')
            st.json({'ranking_method': options.retrieval, 'ranking_score': hit['score'],
                **{key: hit[key] for key in ('dense_score', 'bm25_score', 'rerank_score') if hit.get(key) is not None}})
