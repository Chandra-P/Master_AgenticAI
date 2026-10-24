from html.parser import HTMLParser
import pytest
from test_presentation_workspace import service_fixture


class ReportParser(HTMLParser):
    def __init__(self):
        super().__init__();self.ids=[];self.links=[];self.charts=0;self.external=[]
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if 'id' in attrs:self.ids.append(attrs['id'])
        if tag=='svg':self.charts+=1
        if tag=='a' and attrs.get('href','').startswith('#'):self.links.append(attrs['href'][1:])
        if tag in ('script','link','img','iframe') and ('src' in attrs or 'href' in attrs):self.external.append(attrs)


def test_html_is_portable_chart_led_and_cited(tmp_path):
    from campaign_hub.reporting.client_packet import build_client_packet
    from campaign_hub.reporting.html_report import export_html
    packet=build_client_packet(service_fixture(tmp_path),'TX-CHK-001')
    html=export_html(packet);parser=ReportParser();parser.feed(html)
    assert parser.charts==10
    assert not parser.external
    assert len(parser.ids)==len(set(parser.ids))
    assert set(parser.links)<=set(parser.ids)
    assert html.count('What the data shows')==10
    assert 'Fictional Meridian Credit Union' in html
    assert 'No verified industry benchmark' in html
    assert '230' in html and '127.8%' in html
    assert 'prefers-reduced-motion' in html
    packet['facts']['actual']+=1
    with pytest.raises(ValueError,match='validation'):
        export_html(packet)


def test_html_does_not_infer_missing_history(tmp_path):
    from campaign_hub.reporting.client_packet import build_client_packet
    from campaign_hub.reporting.html_report import export_html
    service=service_fixture(tmp_path)
    html=export_html(build_client_packet(service,'FL-CMP-004'))
    assert 'No compatible same-client history' in html


def test_interactive_dashboard_retains_evidence_and_missing_data(tmp_path):
    from campaign_hub.reporting.client_packet import build_client_packet
    from campaign_hub.reporting.html_report import export_html
    html=export_html(build_client_packet(service_fixture(tmp_path),'TX-CHK-001'))
    assert 'new Chart(' in html
    assert 'bootstrap' in html.lower()
    assert 'KPI callout' in html and 'Recommended action' in html
    assert 'Audience composition' in html and '138' in html
    assert 'Attribution timeline' in html and '2026-04-01' in html
    assert 'Funded account trend' in html and 'Unavailable' in html
    assert 'Presentation storyline' in html
    assert 'Variance' in html and 'Favorable' in html
    parser=ReportParser();parser.feed(html)
    assert not parser.external
    assert set(parser.links)<=set(parser.ids)


def test_chart_payload_cannot_close_script():
    from campaign_hub.reporting.dashboard import script_json
    assert '</script>' not in script_json({'label':'</script><img src=x>'})
    assert '\\u003c' in script_json({'label':'<script>'})
