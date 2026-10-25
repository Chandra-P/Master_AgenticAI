import pytest
from types import SimpleNamespace
from campaign_hub.models import Chunk, RetrievalOptions


CATALOG = {'campaign_id': ['A', 'B'], 'region': ['TX', 'CA'],
           'year': [2025, 2026], 'document_type': ['brief', 'performance_report']}


def test_combined_filters_intersect_and_compile_without_broadening():
    from campaign_hub.retrieval.filters import normalize_filters, merge_filters, chroma_where, FilterConflict
    manual = normalize_filters({'campaign_id': ['A', 'B'], 'region': 'TX'}, CATALOG)
    effective = merge_filters(manual, {'campaign_id': ['B'], 'year': [2026]})
    assert effective == {'campaign_id': ['B'], 'region': ['TX'], 'year': [2026]}
    assert chroma_where(effective) == {'$and': [{'campaign_id': {'$in': ['B']}},
        {'region': {'$in': ['TX']}}, {'year': {'$in': [2026]}}]}
    with pytest.raises(FilterConflict): merge_filters(manual, {'region': ['CA']})


@pytest.mark.parametrize('filters', [{'$or': []}, {'region': ['ZZ']}, {'year': [True]},
    {'region': {'$ne': 'TX'}}, {'year': ['2026']}])
def test_unsupported_filters_are_rejected(filters):
    from campaign_hub.retrieval.filters import normalize_filters
    with pytest.raises(ValueError): normalize_filters(filters, CATALOG)


@pytest.mark.parametrize('retrieval', ['dense', 'hybrid'])
def test_real_chroma_and_lexical_search_obey_same_combined_filters(tmp_path, retrieval):
    from campaign_hub.vectordb.chroma_store import ChromaStore
    from campaign_hub.retrieval.pipeline import retrieve
    from langchain_core.embeddings import Embeddings
    class Embedder(Embeddings):
        identity = {'provider': 'test', 'model': 'test'}
        def embed_documents(self, texts): return [[1., 0.] for _ in texts]
        def embed_query(self, text): return [1., 0.]
    store = ChromaStore(tmp_path, 'fixed', Embedder())
    docs = [Chunk(chunk_id=str(i), text='activation results', metadata=meta) for i, meta in enumerate([
        {'region': 'TX', 'year': 2026, 'document_type': 'brief'},
        {'region': 'TX', 'year': 2026, 'document_type': 'performance_report'},
        {'region': 'TX', 'year': 2025, 'document_type': 'brief'},
        {'region': 'CA', 'year': 2026, 'document_type': 'brief'}])]
    store.build(docs, 'hash')
    filters = {'region': ['TX'], 'year': [2026], 'document_type': ['brief', 'performance_report']}
    assert {c.chunk_id for c in store.chunks(filters)} == {'0', '1'}
    hits = retrieve(store, 'activation', filters, RetrievalOptions(retrieval=retrieval))
    assert {h.chunk.chunk_id for h in hits} == {'0', '1'}
    assert retrieve(store, 'activation', {'year': [1900]}, RetrievalOptions(retrieval=retrieval)) == []
