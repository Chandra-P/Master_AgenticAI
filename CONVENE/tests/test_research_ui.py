from pathlib import Path

import httpx
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / 'streamlit_app.py'


def test_supplied_urls_show_real_sources_unknown_price_and_download(monkeypatch):
    def post(url, *, json, **kwargs):
        assert url.endswith('/venues/research')
        assert json['urls'] == ['https://venue.example/events']
        assert json['discover'] is False
        assert json['city'] == 'San Antonio, Texas' and json['guests'] == 40
        return httpx.Response(200, request=httpx.Request('POST', url), json={
            'query': json, 'candidates': [{
                'details': {'name': {'value': 'Cedar Hall', 'evidence': 'Cedar Hall'},
                            'address': None, 'capacity': None, 'amenities': [], 'contact': None, 'pricing': None},
                'source_url': 'https://venue.example/events', 'retrieved_at': '2026-10-31T12:00:00+00:00',
                'availability': 'unconfirmed', 'warnings': []}],
            'errors': [{'url': 'https://blocked.example/', 'error': 'Disallowed by robots.txt'}],
            'disclaimer': 'Web-published details; confirm with venue.'})
    monkeypatch.setattr(httpx, 'post', post)
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    assert app.text_input(key='research_city').value == 'San Antonio, Texas'
    assert app.selectbox[0].value == 'San Antonio'
    app.text_area(key='research_urls').set_value('https://venue.example/events')
    app.checkbox(key='research_discover').uncheck()
    app.button(key='research_submit').click().run()
    assert not app.exception and not app.error
    assert 'Cedar Hall' in [item.value for item in app.subheader]
    assert any('Quote required' in item.value for item in app.text)
    assert any('unconfirmed' in item.value for item in app.caption)
    assert any('robots.txt' in item.value for item in app.warning)
    assert len(app.get('download_button')) == 1
    assert app.session_state['venue_research']['candidates'][0]['source_url'] == 'https://venue.example/events'


def test_discovery_configuration_error_is_actionable(monkeypatch):
    def post(url, *, json, **kwargs):
        assert json['discover'] is True
        return httpx.Response(503, request=httpx.Request('POST', url),
                              json={'detail': 'Automatic discovery requires BRAVE_SEARCH_API_KEY'})
    monkeypatch.setattr(httpx, 'post', post)
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    app.button(key='research_submit').click().run()
    assert not app.exception
    assert any('BRAVE_SEARCH_API_KEY' in item.value for item in app.error)
