from fastapi.testclient import TestClient

from convene.api import create_app


def test_party_website_and_official_catalog(tmp_path):
    client = TestClient(create_app(str(tmp_path / 'site.db')))
    page = client.get('/')
    assert page.status_code == 200
    assert 'text/html' in page.headers['content-type']
    data = client.get('/party/catalog').json()
    assert data['party']['guests'] == 120
    assert data['party']['budget'] == 2000
    assert data['party']['date'] == '2026-12-06'
    assert len(data['venues']) >= 3
    assert len(data['decorators']) >= 2
    for venue in data['venues']:
        assert venue['capacity'] >= 120
        assert venue['source_url'].startswith('https://www.bexar.org/')
        assert venue['availability'] == 'unconfirmed'
        assert venue['exclusions']
        assert client.get(venue['image']).status_code == 200
    for decorator in data['decorators']:
        assert decorator['stitch_confirmed'] is False
        assert decorator['price_type'] in ('starting_at', 'quote_required')
        assert decorator['source_url'].startswith('https://')


def test_website_does_not_expose_dotenv(tmp_path):
    client = TestClient(create_app(str(tmp_path / 'safe.db')))
    for path in ['/.env', '/assets/../.env', '/web/.env']:
        assert client.get(path).status_code == 404


def test_keenable_keyless_search_adapter(monkeypatch):
    import httpx
    from convene import venue_research as research
    monkeypatch.setenv('CONVENE_SEARCH_PROVIDER', 'keenable')
    monkeypatch.delenv('KEENABLE_API_KEY', raising=False)
    def handler(request):
        assert str(request.url) == 'https://api.keenable.ai/v1/search/public'
        assert request.headers['X-Keenable-Title'] == 'CONVENE'
        return httpx.Response(200, json={'query': 'test', 'results': [
            {'title': 'A venue', 'url': 'https://venue.example/', 'snippet': 'public text'}]})
    original = httpx.Client
    monkeypatch.setattr(research.httpx, 'Client', lambda **kwargs:
                        original(transport=httpx.MockTransport(handler), **kwargs))
    assert research.discover_urls(research.ResearchRequest(guests=120)) == ['https://venue.example/']
