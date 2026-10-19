from html.parser import HTMLParser
from pathlib import Path
import pytest
from test_presentation_workspace import service_fixture


def test_solution_kit_uses_saved_measurements_and_exact_prompts(tmp_path):
    from campaign_hub.deliverables import technical_kit
    root=Path(__file__).resolve().parents[1]
    html=technical_kit(root)
    assert '0.9886' in html and '324' in html
    assert 'Document overlap' in html and 'RAGAS' in html
    assert 'Return concise claims grounded only in these sources.' in html
    assert 'Answer using only the supplied sources.' in html
    assert 'BAAI/bge-small-en-v1.5' in html
    assert 'FUTURE WORK' in html and 'retrieve_rerank_generate_sections' in html
    assert 'Missing judgment' in html
    assert 'new Chart(' in html


def test_all_campaign_dashboards_render_without_external_assets(tmp_path):
    from campaign_hub.reporting.client_packet import build_client_packet
    from campaign_hub.reporting.html_report import export_html
    service=service_fixture(tmp_path)
    for cid in service.campaigns:
        html=export_html(build_client_packet(service,cid))
        assert '<canvas' in html and 'Funded account trend' in html
        assert '<script src=' not in html and '<link href=' not in html
