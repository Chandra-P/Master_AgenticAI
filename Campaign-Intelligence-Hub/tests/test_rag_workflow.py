from campaign_hub.models import RetrievalOptions, FALLBACK
from campaign_hub.rag.service import RAGService
from campaign_hub.config import Settings


def test_graph_refusal_skips_generator_and_measures_end_to_end(monkeypatch):
    service = RAGService.__new__(RAGService)
    service.settings = Settings()
    service.analyze_query = lambda *a, **k: {'hits': [], 'status': 'no_results', 'effective_filters': {}}
    result = service.answer_question('Unknown evidence?', None, RetrievalOptions())
    assert result['answer'] == FALLBACK
    assert result['workflow_steps'] == ['retrieve', 'refuse', 'finalize']
    assert result['latency_seconds'] >= result['retrieval_seconds'] >= 0


def test_graph_records_answer_path_and_preserves_filter_conflict():
    service = RAGService.__new__(RAGService)
    service.settings = Settings()
    service.analyze_query = lambda *a, **k: {'hits': [], 'status': 'filter_conflict',
                                            'effective_filters': None, 'message': 'Conflicting filters'}
    result = service.answer_question('Conflicting question?', None, RetrievalOptions())
    assert result['status'] == 'filter_conflict'
    assert result['message'] == 'Conflicting filters'
    assert result['workflow_steps'] == ['retrieve', 'refuse', 'finalize']
