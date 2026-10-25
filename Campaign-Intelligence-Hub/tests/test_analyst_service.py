from types import SimpleNamespace
from campaign_hub.config import Settings
from campaign_hub.models import RetrievalOptions, Chunk, SearchHit
from campaign_hub.reporting.service import CampaignService


def fixture_service(monkeypatch, inferred):
    service = CampaignService.__new__(CampaignService)
    service.settings = Settings()
    service.manifest = {'documents': [
        {'campaign_id': 'A', 'region': 'TX', 'year': 2026, 'document_type': 'brief'},
        {'campaign_id': 'B', 'region': 'CA', 'year': 2025, 'document_type': 'performance_report'}]}
    service.store = lambda strategy: object()
    import campaign_hub.retrieval.classification as classification
    monkeypatch.setattr(classification, 'classify_filters', lambda *a, **kw: inferred)
    calls = []
    import campaign_hub.retrieval.pipeline as pipeline
    def retrieve(store, query, filters, options):
        calls.append(filters)
        return [SearchHit(chunk=Chunk(chunk_id='a', text='Evidence.', metadata={'campaign_id': 'A'}), score=1)]
    monkeypatch.setattr(pipeline, 'retrieve', retrieve)
    return service, calls


def test_analysis_exposes_manual_inferred_and_effective_filters(monkeypatch):
    service, calls = fixture_service(monkeypatch, {'year': [2026]})
    result = service.analyze_query('Texas results in 2026', RetrievalOptions(), {'region': ['TX']}, automatic=True)
    assert result['manual_filters'] == {'region': ['TX']}
    assert result['inferred_filters'] == {'year': [2026]}
    assert result['effective_filters'] == {'region': ['TX'], 'year': [2026]}
    assert calls == [result['effective_filters']]
    assert result['hits'][0]['chunk']['chunk_id'] == 'a'


def test_conflicting_campaign_never_queries_any_store(monkeypatch):
    service, calls = fixture_service(monkeypatch, {'campaign_id': ['B']})
    result = service.analyze_query('Campaign B', RetrievalOptions(), campaign_id='A', automatic=True)
    assert result['status'] == 'filter_conflict'
    assert result['hits'] == [] and calls == []
    assert result['effective_filters'] is None


def test_manual_only_never_calls_classifier(monkeypatch):
    service, calls = fixture_service(monkeypatch, {})
    import campaign_hub.retrieval.classification as classification
    def forbidden(*a, **kw): raise AssertionError('Manual mode invoked model')
    monkeypatch.setattr(classification, 'classify_filters', forbidden)
    result = service.analyze_query('results', RetrievalOptions(), {'year': [2026]}, automatic=False)
    assert result['classification_provider'] is None and calls == [{'year': [2026]}]


def test_question_conflict_does_not_generate_answer_or_drop_selected_campaign(monkeypatch):
    service, calls = fixture_service(monkeypatch, {'campaign_id': ['B']})
    result = service.answer_question('Campaign B', 'A', RetrievalOptions(), automatic=True)
    assert result['status'] == 'filter_conflict'
    assert result['hits'] == [] and calls == []


def test_filtered_question_preserves_goal_routing_and_focus(monkeypatch):
    service, calls = fixture_service(monkeypatch, {})
    import campaign_hub.reporting.service as module
    monkeypatch.setattr(module, 'grounded_answer', lambda settings, question, hits: {'answer': 'ok'})
    result = service.answer_question('What were the objectives?', 'A', RetrievalOptions(), filters={})
    assert result['effective_filters']['document_type'] == ['brief']
    import campaign_hub.retrieval.focus as focus
    seen = []
    monkeypatch.setattr(focus, 'focus_context', lambda question, hits: seen.append(question) or hits)
    service.answer_question('What were the objectives?', 'A', RetrievalOptions(focus_context=True), filters={})
    assert seen == ['What were the objectives?']


def test_explicit_document_filter_is_never_replaced_by_goal_routing(monkeypatch):
    service, calls = fixture_service(monkeypatch, {})
    import campaign_hub.reporting.service as module
    monkeypatch.setattr(module, 'grounded_answer', lambda *args: {'answer': 'ok'})
    result = service.answer_question('What were the objectives?', 'A', RetrievalOptions(),
                                     filters={'document_type': ['performance_report']})
    assert result['effective_filters']['document_type'] == ['performance_report']
