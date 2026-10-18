import json
import pytest


def service_fixture(tmp_path):
    from campaign_hub.synthetic_data.generator import generate_corpus
    from campaign_hub.config import Settings
    from campaign_hub.reporting.service import CampaignService
    generate_corpus(tmp_path/'data')
    return CampaignService(Settings(root=tmp_path))


def test_geography_reconciles_and_filters_without_model(tmp_path):
    service=service_fixture(tmp_path)
    snap=service.campaign_snapshot('TX-CHK-001')
    assert sum(r['accounts'] for r in snap['geography'])==snap['actual']
    assert sum(r['balance_cents'] for r in snap['geography'])==snap['balance_cents']
    assert {r['client_name'] for r in snap['geography']}=={snap['client_name']}
    dm=service.campaign_snapshot('TX-CHK-001',channel='direct_mail')
    assert {r['channel'] for r in dm['geography']}=={'direct_mail'}
    assert dm['actual']==sum(r['accounts'] for r in dm['geography'])
    assert service.campaign_snapshot('TX-CHK-001',period='1900-Q1')['geography']==[]
    with pytest.raises(ValueError,match='client'):
        service.campaign_snapshot('TX-CHK-001',client_name='Other client')


def test_primary_history_is_same_client(tmp_path):
    service=service_fixture(tmp_path)
    current=service.campaigns['TX-CHK-001']
    peers=[c for c in service.campaigns.values() if c['client_name']==current['client_name']
           and c['campaign_type']==current['campaign_type'] and c['period']<current['period']]
    assert len(peers)>=2
    from campaign_hub.reporting.benchmark import compare_campaign
    other={**peers[0],'client_name':'Other client','campaign_id':'OTHER'}
    result=compare_campaign(current,peers+[other],'direct_mail',scope='client')
    assert 'OTHER' not in result['peer_ids']
    reference=compare_campaign(current,peers+[other],'direct_mail',scope='peer_reference')
    assert reference['peer_ids']==['OTHER']
    assert reference['benchmark_label']=='Synthetic peer reference — not an industry benchmark'


def test_fact_packet_is_deterministic_and_fail_closed(tmp_path):
    service=service_fixture(tmp_path)
    from campaign_hub.reporting.client_packet import build_client_packet,validate_packet
    packet=build_client_packet(service,'TX-CHK-001')
    assert packet['readiness']['ready']
    assert [s['title'] for s in packet['sections']]==[
        'Executive Summary','Goals','Progress Toward Goals','Learnings','Recommendations',
        'Suggested Next Steps','Measurement Notes and Limitations','Source Citations']
    assert packet['client_name']
    assert all(s['citations'] for s in packet['sections'] if s['title']!='Source Citations')
    assert validate_packet(packet)==[]
    packet['facts']['actual']+=99
    assert validate_packet(packet)
    packet=build_client_packet(service,'TX-CHK-001')
    packet['sections'][0]['text']='Invented results: 999999 accounts.'
    assert validate_packet(packet)
    packet=build_client_packet(service,'TX-CHK-001')
    packet['sources'].pop(next(iter(packet['sources'])))
    assert validate_packet(packet)


def test_pdf_and_deck_share_the_fact_packet(tmp_path):
    service=service_fixture(tmp_path)
    from campaign_hub.reporting.client_packet import build_client_packet
    from campaign_hub.reporting.exports import export_pdf,export_pptx
    from pypdf import PdfReader
    import zipfile,io
    packet=build_client_packet(service,'TX-CHK-001')
    pdf=export_pdf(packet)
    assert pdf.startswith(b'%PDF')
    reader=PdfReader(io.BytesIO(pdf))
    assert len(reader.pages)>=5
    text='\n'.join(p.extract_text() for p in reader.pages)
    assert packet['client_name'] in text and str(packet['facts']['actual']) in text
    pptx=export_pptx(packet)
    with zipfile.ZipFile(io.BytesIO(pptx)) as deck:
        slides=[n for n in deck.namelist() if n.startswith('ppt/slides/slide') and n.endswith('.xml')]
        assert len(slides)>=9
        assert any(packet['client_name'] in deck.read(n).decode() for n in slides)
    packet['readiness']['ready']=False
    with pytest.raises(ValueError,match='ready|validation'):
        export_pdf(packet)


@pytest.mark.parametrize('old,new',[
    ('| count | higher |','| USD | lower |'),
    ('spend ceiling: USD 24000;','spend ceiling: USD 240000;'),
    ('opening account balance target: USD 540000.00','opening account balance target: USD 540001.00')])
def test_conflicting_source_definitions_are_rejected(tmp_path,old,new):
    from campaign_hub.reporting.snapshot import source_bundle,snapshot_from_sources
    sources=source_bundle(service_fixture(tmp_path))
    for key in sources:
        sources[key]['text']=sources[key]['text'].replace(old,new)
    with pytest.raises(ValueError,match='mismatch|conflict'):
        snapshot_from_sources(sources,'TX-CHK-001')


def test_unrelated_invalid_campaign_does_not_block_packet(tmp_path):
    from campaign_hub.reporting.snapshot import source_bundle
    from campaign_hub.reporting.client_packet import _compose
    sources=source_bundle(service_fixture(tmp_path))
    sources['NY-CMP-005-performance_report']['text']=sources['NY-CMP-005-performance_report']['text'].replace('## Geographic Results','## Broken')
    facts,sections,readiness=_compose(sources,'TX-CHK-001')
    assert readiness['ready']


def test_zero_channel_cost_is_unavailable(tmp_path,monkeypatch):
    import campaign_hub.reporting.client_packet as module
    from campaign_hub.reporting.snapshot import source_bundle,snapshot_from_sources
    sources=source_bundle(service_fixture(tmp_path))
    original=snapshot_from_sources
    def snapshot(bundle,cid):
        result=original(bundle,cid)
        if cid=='TX-CHK-001':
            result['channel_results']['direct_mail']['activations']=0
        return result
    monkeypatch.setattr(module,'snapshot_from_sources',snapshot)
    _,sections,_=module._compose(sources,'TX-CHK-001')
    assert 'unavailable (zero activations) per activation' in sections[2]['text']
