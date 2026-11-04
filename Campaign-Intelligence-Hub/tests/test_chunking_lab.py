from campaign_hub.chunking.lab import canonical_text, describe_chunks
from campaign_hub.models import Chunk, SourceDocument
from campaign_hub.chunking.pipeline import chunk_documents


def test_real_chunks_resolve_to_canonical_source():
    doc = SourceDocument(metadata={'document_id':'test'}, text='# Title\n\n## First\n' + 'alpha beta. ' * 700 + '\n\n## Second\nsame ending.')
    source = canonical_text(doc.text)
    for strategy in ('fixed', 'section'):
        rows = describe_chunks(doc.text, chunk_documents([doc], strategy))
        assert rows
        for row in rows:
            assert row['char_start'] is not None
            assert source[row['char_start']:row['char_end']] == row['text']
            assert row['token_count'] <= 500
        assert any(r['overlap_chars'] > 0 for r in rows)


def test_ambiguous_and_invalid_spans_stay_unknown():
    text='## A\nsame\n\n## B\nsame'
    chunk=Chunk(chunk_id='external', text='same', metadata={})
    assert describe_chunks(text,[chunk])[0]['char_start'] is None
    invalid=Chunk(chunk_id='external2', text='absent', metadata={'char_start':0,'char_end':6})
    assert describe_chunks(text,[invalid])[0]['char_start'] is None


def test_section_duplicate_text_resolves_using_heading_and_chunk_id():
    doc=SourceDocument(metadata={'document_id':'x'},text='## A\nsame\n\n## B\nsame')
    rows=describe_chunks(doc.text,chunk_documents([doc],'section'))
    assert [(r['char_start'],r['char_end']) for r in rows] == [(5,9),(16,20)]


def test_semantic_offsets_and_unknown_overlap_are_disclosed():
    text='alpha beta gamma'
    chunks=[Chunk(chunk_id='semantic1',text='alpha beta',metadata={'char_start':0,'char_end':10}),
            Chunk(chunk_id='semantic2',text='beta gamma',metadata={'char_start':6,'char_end':16}),
            Chunk(chunk_id='unknown',text='missing',metadata={})]
    rows=describe_chunks(text,chunks)
    assert rows[1]['overlap_chars']==4
    assert rows[2]['overlap_chars'] is None


def test_inspection_reads_only_actual_indexes_and_reports_missing(tmp_path):
    from types import SimpleNamespace
    from campaign_hub.chunking.lab import inspect_source
    (tmp_path/'source.md').write_text('alpha beta',encoding='utf-8')
    chunk=Chunk(chunk_id='fixed',text='alpha beta',metadata={'char_start':0,'char_end':10})
    class Store:
        def assert_compatible(self, corpus):
            assert corpus=='hash'
        def chunks(self,filters):
            assert filters=={'document_id':'doc'}
            return [chunk]
    class Service:
        settings=SimpleNamespace(data=tmp_path)
        manifest={'documents':[{'document_id':'doc','source_path':'source.md'}]}
        corpus_hash='hash'
        def store(self,strategy):
            if strategy=='semantic':
                raise ValueError('Index missing')
            return Store()
    result=inspect_source(Service(),'doc')
    assert result['strategies']['fixed']['chunks'][0]['text']=='alpha beta'
    assert 'Rebuild the semantic index' in result['strategies']['semantic']['error']


def test_overlapping_repeated_text_is_ambiguous():
    chunk=Chunk(chunk_id='external',text='aaa',metadata={})
    assert describe_chunks('aaaa',[chunk])[0]['char_start'] is None
