import json
import pytest


def make_service(tmp_path):
    from campaign_hub.synthetic_data.generator import generate_corpus
    from campaign_hub.reporting.service import CampaignService
    from campaign_hub.config import Settings
    generate_corpus(tmp_path/'data')
    return CampaignService(Settings(root=tmp_path))


def test_arbitrary_retrieval_does_not_satisfy_section(tmp_path,monkeypatch):
    from campaign_hub.models import Chunk,SearchHit,RetrievalOptions
    service=make_service(tmp_path)
    unrelated=SearchHit(chunk=Chunk(chunk_id='wrong',text='Spend was tracked.',metadata={
        'campaign_id':'TX-CHK-001','period':'2024-Q2','section_name':'Measurement Limitations',
        'section_anchor':'measurement-limitations','document_id':'TX-CHK-001-performance_report','source_path':'fake.md'}),score=.9)
    monkeypatch.setattr(service,'search',lambda *a,**kw:[unrelated])
    report=service.report_sections('TX-CHK-001','2024-Q2',RetrievalOptions(),use_llm=False)
    audience=next(s for s in report.sections if s.title=='Audience Insights')
    assert not audience.claims
    assert audience.gap
    assert report.status=='partial'


def test_kpi_wrong_period_is_not_a_supported_review():
    from campaign_hub.reporting.service import kpi_review
    from campaign_hub.models import Chunk
    chunk=Chunk(chunk_id='x',metadata={},text='| Activations | 100 | 120 | count | higher | 2025-Q2 |')
    assert kpi_review(chunk,'2026-Q2') is None


def test_service_detects_corpus_change(tmp_path):
    service=make_service(tmp_path)
    path=service.settings.data/'manifest.json'
    manifest=json.loads(path.read_text())
    manifest['seed']=999
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError,match='changed|rebuild'):
        service.ensure_current()


def test_fixed_evidence_has_real_section_anchor():
    from campaign_hub.reporting.service import section_evidence
    from campaign_hub.models import Chunk
    chunk=Chunk(chunk_id='x',metadata={'section_name':'Document'},text='## Objectives\nAcquire members.\n\n## Audience Insights\nExisting members performed well.')
    evidence=section_evidence(chunk,'Audience Insights')
    assert evidence.metadata['section_anchor']=='audience-insights'
    assert 'Acquire members' not in evidence.text


def test_model_cannot_cite_other_report_sections():
    from campaign_hub.reporting.evidence import supported_claims
    from campaign_hub.models import Chunk,EvidenceClaim
    scope={'audience':Chunk(chunk_id='audience',text='Existing members converted.',metadata={})}
    claims=[EvidenceClaim(text='Spend was low.',citations=['budget']),
            EvidenceClaim(text='Existing members converted.',citations=['audience'])]
    assert [c.citations for c in supported_claims(claims,scope)]==[['audience']]


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


def test_goal_analysis_explicitly_marks_below_target(tmp_path,monkeypatch):
    from campaign_hub.models import Chunk,SearchHit,RetrievalOptions
    service=make_service(tmp_path)
    def search(query,campaign_id,options,document_type=None):
        heading='Success Criteria' if document_type=='success_plan' else 'KPI Results'
        text='Success requires 100 activations.' if heading=='Success Criteria' else '| Activations | 100 | 80 | count | higher | 2024-Q2 |'
        return [SearchHit(chunk=Chunk(chunk_id=heading,text=text,metadata={'campaign_id':'TX-CHK-001','period':'2024-Q2','section_name':heading}),score=.9)]
    monkeypatch.setattr(service,'search',search)
    report=service.report_sections('TX-CHK-001','2024-Q2',RetrievalOptions(),False)
    goal=next(s for s in report.sections if s.title=='Goal Achievement Analysis')
    assert any('not met' in c.text and '80' in c.text and '100' in c.text for c in goal.claims)
    assert all(c.citations for c in goal.claims)


def test_zero_target_retains_absolute_variance():
    from campaign_hub.reporting.service import kpi_review
    from campaign_hub.models import Chunk
    c=Chunk(chunk_id='x',text='| Activations | 0 | 5 | count | higher | 2024-Q2 |',metadata={})
    assert '| 5.0 | unavailable |' in kpi_review(c,'2024-Q2').text


def test_markdown_includes_provenance():
    from campaign_hub.models import ReportResult
    from campaign_hub.reporting.render import render_report
    r=ReportResult(campaign_id='A',period='P',sections=[],evidence={},status='partial',confidence=0,provenance={'inputs':{'brief':False},'generated_at':'2026-10-17','corpus_hash':'abc'})
    rendered=render_report(r)
    assert '2026-10-17' in rendered and 'abc' in rendered and 'brief' in rendered
