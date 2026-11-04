import json
import pytest


def make_service(tmp_path):
    from campaign_hub.synthetic_data.generator import generate_corpus
    from campaign_hub.rag.service import RAGService
    from campaign_hub.config import Settings
    generate_corpus(tmp_path/'data')
    return RAGService(Settings(root=tmp_path))


def test_service_detects_corpus_change(tmp_path):
    service=make_service(tmp_path)
    path=service.settings.data/'manifest.json'
    manifest=json.loads(path.read_text())
    manifest['seed']=999
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError,match='changed|rebuild'):
        service.ensure_current()


def test_fixed_evidence_has_real_section_anchor():
    from campaign_hub.rag.grounding import section_evidence
    from campaign_hub.models import Chunk
    chunk=Chunk(chunk_id='x',metadata={'section_name':'Document'},text='## Objectives\nAcquire members.\n\n## Audience Insights\nExisting members performed well.')
    evidence=section_evidence(chunk,'Audience Insights')
    assert evidence.metadata['section_anchor']=='audience-insights'
    assert 'Acquire members' not in evidence.text


def test_model_cannot_cite_sources_outside_retrieved_scope():
    from campaign_hub.rag.grounding import supported_claim
    from campaign_hub.models import Chunk,EvidenceClaim
    scope={'audience':Chunk(chunk_id='audience',text='Existing members converted.',metadata={})}
    claims=[EvidenceClaim(text='Spend was low.',citations=['budget']),
            EvidenceClaim(text='Existing members converted.',citations=['audience'])]
    assert [c.citations for c in claims if supported_claim(c,scope)]==[['audience']]


def test_index_rejects_changed_chunker(tmp_path):
    from campaign_hub.vectordb.chroma_store import ChromaStore
    from campaign_hub.models import Chunk
    class E:
        identity={'model':'test','dimensions':3}
        def embed_documents(self,texts):return [[1.0,0.0,0.0] for _ in texts]
    store=ChromaStore(tmp_path,'fixed',E())
    store.build([Chunk(chunk_id='x',text='text',metadata={'campaign_id':'A'})],'hash')
    changed=ChromaStore(tmp_path,'fixed',E(),chunking_config={'tokenizer':'changed','window':400,'overlap':20})
    with pytest.raises(ValueError,match='rebuild'):
        changed.assert_compatible('hash')
