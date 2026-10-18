def test_missing_campaign_abstains(tmp_path):
    from campaign_hub.synthetic_data.generator import generate_corpus
    from campaign_hub.reporting.service import CampaignService
    from campaign_hub.config import Settings
    from campaign_hub.models import RetrievalOptions, FALLBACK
    generate_corpus(tmp_path/'data')
    service = CampaignService(Settings(root=tmp_path))
    result = service.generate_report('UNKNOWN','2026-Q2',RetrievalOptions())
    assert result.status == 'partial'
    assert result.confidence == 0
    assert all(s.gap == FALLBACK for s in result.sections)


def test_no_numeric_evidence_invented_in_table():
    from campaign_hub.reporting.service import kpi_review
    from campaign_hub.models import Chunk
    c=Chunk(chunk_id='x',metadata={},text='| Metric | Target | Actual | Unit | Direction | Period |\n|---|---:|---:|---|---|---|\n| Verified activations | 100 | 120 | count | higher | 2026-Q2 |')
    claim=kpi_review(c, '2026-Q2')
    assert '20.00%' in claim.text
    assert 'met' in claim.text
    assert claim.citations == ['x']
