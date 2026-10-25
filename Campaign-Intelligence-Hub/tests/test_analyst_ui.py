from types import SimpleNamespace
from campaign_hub.config import Settings
from campaign_hub.models import RetrievalOptions
from streamlit.testing.v1 import AppTest


def analyst_app():
    from campaign_hub.config import Settings
    from campaign_hub.models import RetrievalOptions
    from campaign_hub.ui.analyst_page import show
    import streamlit as st
    if 'stub' not in st.session_state:
        class Service:
            settings = Settings()
            corpus_hash = 'test-corpus'
            manifest = {'documents': [{'region': 'TX', 'year': 2026, 'document_type': 'brief'}]}
            def analyze_query(self, question, options, **kwargs):
                return {'manual_filters': kwargs['filters'], 'scope_filters': {}, 'inferred_filters': {},
                    'effective_filters': kwargs['filters'], 'classification_provider': None,
                    'status': 'retrieved', 'hits': [{'chunk': {'chunk_id': 'evidence-1', 'text': 'Supported evidence.',
                    'metadata': {'document_id': 'brief-1'}}, 'score': .5, 'dense_score': .7,
                    'bm25_score': 2., 'rerank_score': None}]}
        st.session_state.stub = Service()
    show(st.session_state.stub, RetrievalOptions())


def test_analyst_submission_discloses_filters_evidence_and_invalidates_stale_results():
    at = AppTest.from_function(analyst_app).run()
    assert not at.exception
    at.checkbox[0].uncheck().run()
    at.text_area[0].set_value('Texas objectives')
    region = next(x for x in at.multiselect if x.label == 'Region')
    region.select('TX')
    at.button[0].click().run()
    assert not at.exception
    assert any('Applied filters' in x.value for x in at.subheader)
    assert any(x.value == 'Supported evidence.' for x in at.code)
    assert any('TX' in x.value for x in at.json)
    at.text_area[0].set_value('Different question').run()
    assert not any(x.value == 'Supported evidence.' for x in at.code)
