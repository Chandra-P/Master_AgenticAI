from campaign_hub.models import Chunk


def evidence():
    return Chunk(chunk_id='multi',text='## First\nMail reaches households.\n\n## Second\nMail uses addresses.',
        metadata={'document_id':'brief','source_path':'brief.md','section_anchor':'document',
                  'section_anchors':'first|second','section_name':'Document'})


def test_claim_section_uses_exact_source_span_not_all_overlapping_sections():
    from campaign_hub.reporting.citations import claim_section, source_references
    chunk=evidence()
    assert claim_section('Mail uses addresses.',chunk)=='second'
    assert claim_section('Mail reaches households.',chunk)=='first'
    assert claim_section('Mail supports acquisition.',chunk) is None
    assert source_references(chunk)==['brief.md#first','brief.md#second']


def test_claim_crossing_sections_or_ambiguous_occurrences_has_no_section_score():
    from campaign_hub.reporting.citations import claim_section
    chunk=evidence()
    assert claim_section(chunk.text,chunk) is None
    chunk=chunk.model_copy(update={'text':'## First\nSame statement.\n\n## Second\nSame statement.'})
    assert claim_section('Same statement.',chunk) is None


def test_leading_partial_section_does_not_inherit_next_heading():
    from campaign_hub.reporting.citations import claim_section
    chunk=evidence().model_copy(update={'text':'Last sentence.\n\n## Second\nSecond text.',
        'metadata':{**evidence().metadata,'section_anchors':'second'}})
    assert claim_section('Last sentence.',chunk) is None
    assert claim_section('Second text.',chunk)=='second'


def test_markdown_export_lists_real_sections_for_multisection_evidence():
    from campaign_hub.models import ReportResult,ReportSection
    from campaign_hub.reporting.render import render_report
    report=ReportResult(campaign_id='campaign',period='2026',status='partial',confidence=0,
        sections=[ReportSection(title='Source Citations')],evidence={'multi':evidence()})
    rendered=render_report(report)
    assert 'brief.md#first, brief.md#second' in rendered
    assert '#document' not in rendered
