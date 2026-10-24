import pytest
from campaign_hub.models import SourceDocument
from campaign_hub.chunking.pipeline import chunk_documents,tokens


class TopicEmbeddings:
    identity={'provider':'test','model':'topic-vectors'}
    def __init__(self):self.calls=[]
    def embed_documents(self,texts):
        self.calls.extend(texts)
        return [[0.,1.] if 'Display' in text else [1.,0.] for text in texts]


def document(text):
    return SourceDocument(text=text,metadata={'document_id':'campaign-brief','campaign_id':'campaign'})


def test_semantic_finds_a_topic_change_without_headings():
    text='Mail reaches households. Mail uses addresses. Display reaches browsers. Display uses impressions.'
    embedder=TopicEmbeddings()
    chunks=chunk_documents([document(text)],'semantic',embedder=embedder)
    assert len(chunks)==2 and len(embedder.calls)==4
    assert 'Mail uses addresses.' in chunks[0].text
    assert 'Display reaches browsers.' in chunks[1].text
    assert all(c.text in text for c in chunks)
    assert all(c.metadata['chunking']=='semantic' for c in chunks)
    assert chunks[0].metadata['semantic_percentile']==65
    assert chunks[0].metadata['boundary_reason']=='semantic'


def test_section_boundaries_are_not_semantic_boundaries():
    text='## First\nMail reaches households.\n\n## Second\nMail uses addresses.'
    structural=chunk_documents([document(text)],'section')
    semantic=chunk_documents([document(text)],'semantic',embedder=TopicEmbeddings())
    assert len(structural)==2 and len(semantic)==1
    assert semantic[0].metadata['section_name']=='Document'
    assert semantic[0].metadata['section_anchors']=='first|second'


def test_semantic_preserves_table_and_exact_source_spans():
    text='## Results\nMail results.\n\n| Channel | Actual |\n|---|---:|\n| Mail | 180 |\n| Display | 50 |\n\nDisplay results.'
    chunks=chunk_documents([document(text)],'semantic',embedder=TopicEmbeddings())
    table='| Channel | Actual |\n|---|---:|\n| Mail | 180 |\n| Display | 50 |'
    assert any(table in c.text for c in chunks)
    for c in chunks:
        assert text[c.metadata['char_start']:c.metadata['char_end']]==c.text


def test_semantic_bounds_long_unicode_text_without_losing_tail():
    text='## Details\n'+('顧客💡 balance ' * 800)+'END_OF_SOURCE'
    chunks=chunk_documents([document(text)],'semantic',embedder=TopicEmbeddings())
    assert len(chunks)>1
    assert all(len(tokens(c.text))<=500 and c.text in text and '\ufffd' not in c.text for c in chunks)
    assert chunks[-1].text.endswith('END_OF_SOURCE')


def test_semantic_requires_real_embedding_provider():
    with pytest.raises(ValueError,match='embedder'):
        chunk_documents([document('Mail. Display.')],'semantic')


def test_semantic_batches_segmentation_embeddings_across_documents():
    class Batched(TopicEmbeddings):
        def __init__(self):super().__init__();self.batches=0
        def embed_documents(self,texts):
            self.batches+=1
            return super().embed_documents(texts)
    e=Batched()
    chunk_documents([document('Mail reaches homes. Display reaches browsers.'),
        document('Mail uses addresses. Display uses impressions.')],'semantic',embedder=e)
    assert e.batches==1


@pytest.mark.parametrize('vectors',[[[0.,0.],[1.,0.]],[[float('nan'),1.],[0.,1.]],[[1.,0.]],[[1.],[1.,0.]],[[1e308,1e308],[1.,0.]]])
def test_semantic_rejects_invalid_embeddings(vectors):
    class Invalid:
        identity={}
        def embed_documents(self,texts):return vectors
    with pytest.raises(ValueError,match='embedding'):
        chunk_documents([document('Mail reaches homes. Display reaches browsers.')],'semantic',embedder=Invalid())


def test_index_identity_separates_algorithms_and_parameters(tmp_path):
    from campaign_hub.vectordb.chroma_store import ChromaStore,default_chunking_config
    e=TopicEmbeddings()
    fixed=ChromaStore(tmp_path,'fixed',e)
    section=ChromaStore(tmp_path,'section',e)
    semantic=ChromaStore(tmp_path,'semantic',e)
    changed=ChromaStore(tmp_path,'semantic',e,chunking_config={**default_chunking_config('semantic'),'semantic_percentile':95})
    assert len({s.name for s in (fixed,section,semantic,changed)})==4
    assert default_chunking_config('section')!=default_chunking_config('semantic')


def test_index_rejects_semantic_chunks_from_different_parameters(tmp_path):
    from campaign_hub.vectordb.chroma_store import ChromaStore,default_chunking_config
    e=TopicEmbeddings()
    chunks=chunk_documents([document('Mail reaches homes. Display reaches browsers.')],'semantic',embedder=e)
    store=ChromaStore(tmp_path,'semantic',e,chunking_config={**default_chunking_config('semantic'),'semantic_percentile':95})
    with pytest.raises(ValueError,match='chunking configuration'):
        store.build(chunks,'source-version')
