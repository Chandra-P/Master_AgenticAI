def test_client_report_has_identity_citations_without_internal_diagnostics():
    from campaign_hub.models import Chunk,EvidenceClaim,ReportResult,ReportSection
    from campaign_hub.reporting.render import render_report
    chunk=Chunk(chunk_id='source',text='230 activations.',metadata={'source_path':'corpus/results/private-internal.md',
        'campaign_name':'Checking campaign','document_type':'performance_report','section_name':'KPI Results'})
    report=ReportResult(campaign_id='TX-CHK-001',period='2026-Q2',client_name='Example Credit Union',campaign_name='Checking campaign',
        sections=[ReportSection(title='Executive Summary',claims=[EvidenceClaim(text='230 activations.',citations=['source'])]),
                  ReportSection(title='Source Citations')],evidence={'source':chunk},status='complete',confidence=1,
        provenance={'corpus_hash':'INTERNAL_HASH','options':{'reranking':True}})
    text=render_report(report,client_facing=True)
    assert 'Example Credit Union' in text and 'Checking campaign' in text
    assert '230 activations.' in text and '[1]' in text
    assert 'KPI Results' in text
    assert 'INTERNAL_HASH' not in text and 'reranking' not in text
    assert 'corpus/results/private-internal.md' not in text
    assert 'SYNTHETIC' in text
    assert 'INTERNAL_HASH' in render_report(report)


def test_client_selection_limits_campaigns(tmp_path,monkeypatch):
    from streamlit.testing.v1 import AppTest
    from campaign_hub.config import ROOT,Settings
    from campaign_hub.synthetic_data.generator import generate_corpus
    from campaign_hub.reporting.service import CampaignService
    import campaign_hub.ui.resources as resources
    generate_corpus(tmp_path/'data')
    service=CampaignService(Settings(root=tmp_path))
    monkeypatch.setattr(resources,'service_for',lambda model,provider=None:service)
    app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
    client=service.campaigns['TX-CHK-001']['client_name']
    app.selectbox(key='report-client').set_value(client).run()
    assert not app.exception
    picker=app.selectbox(key='report-campaign')
    assert len(picker.options)==sum(c['client_name']==client for c in service.campaigns.values())
    assert 'TX-CHK-001' in picker.options[0]
    assert any(b.label=='Generate client-facing report' for b in app.button)


def test_previously_generated_report_gets_client_identity():
    from campaign_hub.reporting.render import enrich_report_identity
    legacy={'campaign_id':'A','period':'2026-Q2','sections':[],'evidence':{},'status':'partial','confidence':0}
    updated=enrich_report_identity(legacy,{'client_name':'Example CU','campaign_name':'Acquisition'})
    assert updated.client_name=='Example CU'
    assert updated.campaign_name=='Acquisition'
