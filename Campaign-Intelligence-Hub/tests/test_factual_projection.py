from campaign_hub.models import Chunk,SearchHit


def hit(text,kind='performance_report',identifier='one',period='2026-Q3',campaign='TEST-777'):
    return SearchHit(chunk=Chunk(chunk_id=identifier,text=text,metadata={'campaign_id':campaign,'period':period,'document_type':kind,'section_name':'Document'}),score=1)

TOTAL='## KPI Results\n| Metric | Target | Actual | Unit |\n|---|---:|---:|---|\n| Verified activations | 40 | 37 | count |'
CHANNELS='## Channel Results\n| Channel | Activations | Exposures |\n|---|---:|---:|\n| direct_mail | 13 | 90 |\n| display | 24 | 200 |'


def test_counts_are_projected_from_actual_columns_with_source_proof():
    from campaign_hub.rag.factual import factual_answer
    result=factual_answer('What were the results and channel findings?',[hit(TOTAL),hit(CHANNELS,identifier='two')])
    assert result['answer']=='37 activations. [one]\n\nDirect mail: 13 activations. [two]\n\nDisplay: 24 activations. [two]'
    assert result['evidence_method']=='retrieved_table_projection'
    assert result['source_proof'] and result['accepted_claims']==3
    assert all(p['source_id'] in ('one','two') and p['row'] for p in result['source_proof'])


def test_incomplete_conflicting_or_wrong_scope_counts_fall_back():
    from campaign_hub.rag.factual import factual_answer
    q='What were the results and channel findings?'
    for rows in ([hit(TOTAL)], [hit(TOTAL),hit(CHANNELS.replace('24','23'),identifier='two')],
                 [hit(TOTAL),hit(CHANNELS,identifier='two',period='2025-Q1')],
                 [hit(TOTAL),hit(CHANNELS,identifier='two',campaign='OTHER')],
                 [hit(TOTAL),hit(CHANNELS,identifier='two'),hit(TOTAL.replace('37','38'),identifier='conflict')],
                 [hit(TOTAL.replace('count','USD')),hit(CHANNELS,identifier='two')]):
        assert factual_answer(q,rows) is None
    for extra in ('and budget','and audience','and causal lift','and ROI','and opening balance'):
        assert factual_answer(q+extra,[hit(TOTAL),hit(CHANNELS,identifier='two')]) is None


def test_objective_extracts_only_complete_section_and_preserves_compound_questions(tmp_path):
    from campaign_hub.rag.factual import factual_answer
    row=hit('## Objectives\nEnroll 46 verified accounts in the autumn pilot.\n\n## Budget\nUSD 9000.',kind='brief')
    import hashlib
    from types import SimpleNamespace
    source=tmp_path/'corpus/brief.md';source.parent.mkdir();source.write_text(row.chunk.text)
    row.chunk.metadata.update(source_path='corpus/brief.md',content_hash=hashlib.sha256(row.chunk.text.encode()).hexdigest())
    settings=SimpleNamespace(data=tmp_path)
    result=factual_answer('What were the objectives?',[row],settings)
    assert result['answer']=='Enroll 46 verified accounts in the autumn pilot. [one]'
    for question in ('What were the objectives and budget?','Were the goals met?','What was the balance goal?'):
        assert factual_answer(question,[row],settings) is None
    other=hit('## Objectives\nEnroll 47 verified accounts in the autumn pilot.',kind='brief',identifier='other')
    assert factual_answer('What were the objectives?',[row,other]) is None


def test_projection_path_never_calls_generator_and_retains_raw_evidence(monkeypatch):
    from campaign_hub.rag.grounding import grounded_answer
    def forbidden(*args):raise AssertionError('Count extraction must not generate unverified facts')
    monkeypatch.setattr('campaign_hub.generation.providers.create_generator',forbidden)
    rows=[hit(TOTAL),hit(CHANNELS,identifier='two')]
    result=grounded_answer(object(),'What were the results and channel findings?',rows)
    assert result['accepted_claims']==3
    assert result['hits']==[h.model_dump() for h in rows]
    assert result['source_proof'][0]['value']==37


def test_unrecognized_requested_facets_and_scope_do_not_project():
    from campaign_hub.rag.factual import factual_answer
    rows=[hit(TOTAL),hit(CHANNELS,identifier='two')]
    for question in ('results and channel findings and recommendations?',
                     'results and channel findings for email only?',
                     'results and channel findings in 2024?',
                     'What were the results and channel findings for OTHER-123?'):
        assert factual_answer(question,rows) is None


def test_objective_fragment_needs_verified_full_section(tmp_path):
    import hashlib
    from types import SimpleNamespace
    from campaign_hub.rag.factual import factual_answer
    full='## Objectives\nEnroll forty accounts. Retain the audited eligibility restriction.'
    source=tmp_path/'corpus/brief.md';source.parent.mkdir();source.write_text(full)
    row=hit('## Objectives\nEnroll forty accounts.',kind='brief')
    row.chunk.metadata.update(source_path='corpus/brief.md',content_hash=hashlib.sha256(full.encode()).hexdigest())
    assert factual_answer('What were the objectives?',[row],SimpleNamespace(data=tmp_path)) is None
