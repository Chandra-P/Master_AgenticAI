import io
import zipfile
import pytest
from test_presentation_workspace import service_fixture


def test_comparisons_and_insights_use_the_same_facts(tmp_path):
    from campaign_hub.reporting.client_packet import build_client_packet
    from campaign_hub.reporting.visuals import comparison_panels
    packet=build_client_packet(service_fixture(tmp_path),'TX-CHK-001')
    panels=comparison_panels(packet)
    assert len(panels)==10
    goals=panels[0]
    assert goals['values']==[180,230]
    assert '127.8%' in goals['insight']
    assert all(p['citations'] and p['insight'] for p in panels)
    geography=next(p for p in panels if p['key']=='geographic_accounts')
    assert sum(geography['values'])==230
    for panel in (p for p in panels if p['family']=='Same-client historical standing'):
        channel=panel['key'].split(':')[0]
        metric=panel['key'].split(':')[1]
        source=next(r for r in packet['facts']['history'] if r['channel']==channel)['metrics'][metric]
        assert panel['values'][-1]==source['current']
        assert len(panel['values'])==source['peer_count']+1


def test_visual_pdf_and_editable_chart_workbooks(tmp_path):
    from campaign_hub.reporting.client_packet import build_client_packet
    from campaign_hub.reporting.exports import export_pdf,export_pptx
    from pypdf import PdfReader
    packet=build_client_packet(service_fixture(tmp_path),'TX-CHK-001')
    text='\n'.join(p.extract_text() for p in PdfReader(io.BytesIO(export_pdf(packet))).pages)
    assert 'What the data shows' in text
    assert 'Same-client historical standing' in text
    with zipfile.ZipFile(io.BytesIO(export_pptx(packet))) as deck:
        charts=[n for n in deck.namelist() if n.startswith('ppt/charts/chart') and n.endswith('.xml')]
        workbooks=[n for n in deck.namelist() if n.startswith('ppt/embeddings/')]
        assert len(charts)==len(workbooks)==10
        assert all(b'externalData' in deck.read(n) for n in charts)


@pytest.mark.parametrize('chunking',['section','fixed','semantic'])
def test_final_packet_requires_attributable_retrieved_sources(tmp_path,monkeypatch,chunking):
    from campaign_hub.reporting.client_retrieval import retrieve_client_packet
    from campaign_hub.reporting.client_packet import validate_packet
    from campaign_hub.ingestion.markdown import load_documents
    from campaign_hub.chunking.pipeline import chunk_documents
    from campaign_hub.models import RetrievalOptions,SearchHit
    service=service_fixture(tmp_path)
    class Embedder:
        identity={'provider':'test','model':'constant'}
        def embed_documents(self,texts):return [[1.,0.] for text in texts]
    chunks=chunk_documents(load_documents(service.settings.data,service.manifest),chunking,embedder=Embedder())
    calls=[]
    def search(query,cid,options,kind):
        calls.append((cid,kind))
        return [SearchHit(chunk=c,score=1) for c in chunks if c.metadata['campaign_id']==cid and c.metadata['document_type']==kind][:5]
    monkeypatch.setattr(service,'search',search)
    packet=retrieve_client_packet(service,'TX-CHK-001',RetrievalOptions(chunking=chunking))
    assert packet['evidence_mode']=='rag'
    assert len(calls)==9
    assert len(packet['sources'])==9
    assert not validate_packet(packet)
    packet['retrieval']['hits'][0]['chunk_text']='Unsupported text'
    assert validate_packet(packet)
    monkeypatch.setattr(service,'search',lambda *args:[])
    with pytest.raises(ValueError,match='Retrieval found no validated'):
        retrieve_client_packet(service,'TX-CHK-001',RetrievalOptions())
