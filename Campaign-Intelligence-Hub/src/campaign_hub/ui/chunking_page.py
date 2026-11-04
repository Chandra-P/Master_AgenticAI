"""Chunking lab: explicit indexed inspection and matched retrieval experiments."""
import json
import streamlit as st
from campaign_hub.chunking.lab import inspect_source, compare_evidence
from campaign_hub.chunking.pipeline import STRATEGIES, LABELS
from campaign_hub.retrieval.filters import available_values
from campaign_hub.ui.analyst_page import LABELS as FILTER_LABELS


def show(service, options, campaign_id=None):
    st.header('Chunking lab')
    st.caption('Inspect actual indexed chunks. Semantic boundaries come from the indexed embedding model; inspection never recomputes embeddings.')
    documents = service.manifest.get('documents', [])
    if not documents:
        st.info('No sources are available. Generate the corpus first.')
        return
    ids = [d['document_id'] for d in documents]
    preferred = next((i for i, d in enumerate(documents) if d.get('document_shape')), 0)
    source_id = st.selectbox('Source document', ids, index=preferred, key='lab-source')
    query = st.text_area('Comparison query', key='lab-query')
    filters = {}
    with st.expander('Comparison metadata filters'):
        st.caption('Manual choices apply identically across indexes. Values within fields use OR; fields use AND.')
        for field, values in available_values(service.manifest).items():
            if campaign_id and field == 'campaign_id':
                continue
            selected = st.multiselect(FILTER_LABELS.get(field, field), values, key='lab-filter-' + field)
            if selected:
                filters[field] = selected
    fingerprint = json.dumps({'source': source_id, 'query': query, 'filters': filters,
        'options': options.model_dump(), 'campaign': campaign_id, 'corpus': service.corpus_hash}, sort_keys=True)
    inspect = st.button('Inspect indexed chunks', key='lab-inspect')
    compare = st.button('Compare retrieved evidence', key='lab-compare', disabled=not query.strip())
    for clicked, key, compute in (
        (inspect, 'lab-inspection', lambda: inspect_source(service, source_id)),
        (compare, 'lab-comparison', lambda: compare_evidence(service, query, options, campaign_id, filters)),
    ):
        cached = st.session_state.get(key)
        if cached and cached[0] != fingerprint:
            st.session_state.pop(key, None)
        if clicked:
            st.session_state.pop(key, None)
            try:
                with st.spinner('Loading indexed evidence…'):
                    st.session_state[key] = (fingerprint, compute())
            except (ValueError, RuntimeError, OSError) as error:
                st.error(str(error))
    cached = st.session_state.get('lab-inspection')
    if cached:
        result = cached[1]
        st.subheader('Canonical source')
        st.caption('Offsets are zero-based character positions in this text; the end position is exclusive. Headings are normalized exactly as during indexing.')
        with st.expander('Inspect canonical source text'):
            st.code(result['source'], language='markdown')
        for column, strategy in zip(st.columns(3), STRATEGIES):
            with column:
                st.subheader(LABELS[strategy])
                data = result['strategies'][strategy]
                if 'error' in data:
                    st.error(data['error'])
                    continue
                rows = data['chunks']
                st.metric('Indexed chunks', len(rows))
                st.caption(f"Total tokens including overlap: {sum(r['token_count'] for r in rows)} · tokenizer: cl100k_base")
                for i, row in enumerate(rows, 1):
                    with st.expander(f"Chunk {i} · {row['token_count']} tokens"):
                        span = 'unknown' if row['char_start'] is None else f"[{row['char_start']}, {row['char_end']})"
                        st.caption(f"Source span: {span} · overlap with preceding covered source: {row['overlap_chars']} characters / {row['overlap_tokens']} tokens")
                        st.code(row['text'], language='markdown')
                        st.json({'chunk_id': row['chunk_id'], **row['metadata']})
    cached = st.session_state.get('lab-comparison')
    if cached:
        st.subheader('Retrieved evidence comparison')
        st.json({'manual_filters': filters, 'campaign_id': campaign_id, 'retrieval_options': options.model_dump(), 'corpus': service.corpus_hash})
        st.caption('Scores describe the labeled ranking method, not answer confidence. Retrieval uses the same query, scope and options in all three indexes.')
        for column, strategy in zip(st.columns(3), STRATEGIES):
            with column:
                st.subheader(LABELS[strategy])
                data = cached[1][strategy]
                if 'error' in data:
                    st.error(data['error'])
                    continue
                if not data['hits']:
                    st.info('No matching evidence. Filters were not relaxed.')
                for rank, hit in enumerate(data['hits'], 1):
                    with st.expander(f"{rank}. {hit['chunk']['chunk_id']}"):
                        st.code(hit['chunk']['text'], language='markdown')
                        st.json({'ranking_method': options.retrieval, **hit})
