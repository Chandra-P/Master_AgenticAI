import pytest


def test_fixed_and_section_chunking(tmp_path):
    from campaign_hub.synthetic_data.generator import generate_corpus
    from campaign_hub.ingestion.markdown import load_documents
    from campaign_hub.chunking.pipeline import chunk_documents, tokens
    manifest = generate_corpus(tmp_path)
    docs = load_documents(tmp_path, manifest)
    fixed = chunk_documents(docs, 'fixed')
    semantic = chunk_documents(docs, 'section')
    assert fixed and semantic
    assert all(len(tokens(c.text)) <= 500 for c in fixed)
    assert any(c.metadata['section_name'] == 'KPI Results' for c in semantic)
    assert all(c.metadata['campaign_id'] for c in semantic)
    assert len({c.chunk_id for c in semantic}) == len(semantic)


def test_kpi_direction_zero_and_period():
    from campaign_hub.reporting.kpis import compare
    assert compare(100, 120, 'higher')['status'] == 'met'
    assert compare(100, 120, 'lower')['status'] == 'not met'
    assert compare(0, 1, 'higher')['percentage_variance'] is None
    assert compare(100, None, 'higher')['status'] == 'unavailable'
    assert compare(100, 120, 'higher', compatible=False)['status'] == 'incompatible'


def test_claims_cannot_invent_sources_or_numbers():
    from campaign_hub.reporting.evidence import valid_claim
    from campaign_hub.models import Chunk, EvidenceClaim
    evidence = {'x': Chunk(chunk_id='x', text='Actual activations: 120.', metadata={'campaign_id':'A'})}
    assert valid_claim(EvidenceClaim(text='Actual activations: 120.', citations=['x']), evidence)
    assert not valid_claim(EvidenceClaim(text='Actual activations: 999.', citations=['x']), evidence)
    assert not valid_claim(EvidenceClaim(text='Actual activations: 120.', citations=['fake']), evidence)
    assert not valid_claim(EvidenceClaim(text='Actual activations: 120.', citations=[]), evidence)


def test_fusion_deduplicates():
    from campaign_hub.retrieval.pipeline import fuse
    from campaign_hub.models import Chunk, SearchHit
    a = SearchHit(chunk=Chunk(chunk_id='a', text='a', metadata={}), score=0.8)
    b = SearchHit(chunk=Chunk(chunk_id='b', text='b', metadata={}), score=0.7)
    result = fuse([a,b], [b,a])
    assert len(result) == 2
    assert {h.chunk.chunk_id for h in result} == {'a','b'}


def test_metrics_hand_computed():
    from campaign_hub.evaluation.metrics import retrieval_metrics
    result = retrieval_metrics(['wrong','right','right'], ['right'])
    assert result['mrr'] == 0.5
    assert result['context_precision'] == 0.5
    assert result['context_recall'] == 1.0


def test_report_keeps_all_headings():
    from campaign_hub.reporting.render import render_report
    from campaign_hub.models import ReportResult, ReportSection, SECTIONS, FALLBACK
    r = ReportResult(campaign_id='X', period='2026-Q2', sections=[ReportSection(title=s, gap=FALLBACK) for s in SECTIONS], evidence={}, status='partial', confidence=0)
    text = render_report(r)
    assert all('## ' + s in text for s in SECTIONS)
    assert FALLBACK in text


def test_index_identity_and_persistence(tmp_path):
    from campaign_hub.vectordb.chroma_store import ChromaStore
    from campaign_hub.models import Chunk
    class Embedder:
        identity = {'model': 'test', 'dimensions': 3}
        def embed_documents(self, texts):
            return [[1.0, 0.0, 0.0] for _ in texts]
        def embed_query(self, text):
            return [1.0, 0.0, 0.0]
    e = Embedder()
    chunk = Chunk(chunk_id='one', text='hello', metadata={'campaign_id':'A', 'document_id':'A-brief'})
    store = ChromaStore(tmp_path, 'semantic', e)
    store.build([chunk], 'corpus-hash')
    assert store.search('hello', {'campaign_id':'A'})[0].chunk.text == 'hello'
    assert store.search('hello', {'campaign_id':'B'}) == []
    other = ChromaStore(tmp_path, 'semantic', e)
    other.assert_compatible('corpus-hash')
    with pytest.raises(ValueError, match='rebuild'):
        other.assert_compatible('changed-corpus')
