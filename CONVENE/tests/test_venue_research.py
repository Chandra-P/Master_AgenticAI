from types import SimpleNamespace

import httpx
import pytest
from fastapi.testclient import TestClient


def research_module():
    from convene import venue_research
    return venue_research


def output():
    return dict(name={'value': 'Cedar Hall', 'evidence': 'Cedar Hall'},
                address={'value': '100 Example St, San Antonio, TX 78205',
                         'evidence': '100 Example St, San Antonio, TX 78205'},
                capacity={'value': '80 seated', 'evidence': 'Capacity: 80 seated'},
                amenities=[], contact=None, pricing=None)


def configure(monkeypatch):
    research = research_module()
    monkeypatch.setenv('OPENAI_API_KEY', 'test-only-key')
    from convene.web_fetch import Page
    monkeypatch.setattr(research, 'fetch_page', lambda url, **kwargs: Page(url,
                        'Cedar Hall. 100 Example St, San Antonio, TX 78205. Capacity: 80 seated. Accessible entrance.', '2026-10-31T12:00:00+00:00'))
    monkeypatch.setattr(research, '_extract', lambda page, **kwargs: research.VenueExtraction(**output()))
    return research


def test_url_research_preserves_unknown_prices_and_attaches_sources(monkeypatch):
    research = configure(monkeypatch)
    monkeypatch.delenv('BRAVE_SEARCH_API_KEY', raising=False)
    result = research.research_venues(research.ResearchRequest(
        city='San Antonio, Texas', guests=40, urls=['https://venue.example/events'], discover=False))
    venue = result['candidates'][0]
    assert venue['details']['pricing'] is None
    assert venue['availability'] == 'unconfirmed'
    assert venue['budget_fit'] == 'unknown'
    assert venue['source_url'] == 'https://venue.example/events'
    assert venue['retrieved_at'] == '2026-10-31T12:00:00+00:00'
    assert venue['details']['capacity']['value'] == '80 seated'


def test_fabricated_value_and_mismatched_quotes_are_removed(monkeypatch):
    research = configure(monkeypatch)
    data = output()
    data['pricing'] = {'value': '$100', 'evidence': 'Cedar Hall'}
    data['amenities'] = [{'value': 'Accessible entrance', 'evidence': 'Accessible entrance.'},
                         {'value': 'Pool', 'evidence': 'Cedar Hall'}]
    monkeypatch.setattr(research, '_extract', lambda page, **kwargs: research.VenueExtraction(**data))
    result = research.research_venues(research.ResearchRequest(city='San Antonio, Texas', guests=40,
                     urls=['https://venue.example'], discover=False))
    details = result['candidates'][0]['details']
    assert details['pricing'] is None
    assert [fact['value'] for fact in details['amenities']] == ['Accessible entrance']
    assert result['candidates'][0]['warnings']


def test_no_supported_venue_name_is_an_error_not_an_invented_candidate(monkeypatch):
    research = configure(monkeypatch)
    data = output()
    data['name'] = {'value': 'Imaginary Venue', 'evidence': 'Cedar Hall'}
    monkeypatch.setattr(research, '_extract', lambda page, **kwargs: research.VenueExtraction(**data))
    result = research.research_venues(research.ResearchRequest(city='San Antonio, Texas', guests=40,
                     urls=['https://venue.example'], discover=False))
    assert not result['candidates'] and result['errors']


def test_discovery_deduplicates_and_keeps_successes_when_one_page_fails(monkeypatch):
    research = configure(monkeypatch)
    monkeypatch.setenv('BRAVE_SEARCH_API_KEY', 'test-search')
    monkeypatch.setattr(research, 'discover_urls', lambda request, **kwargs:
                        ['https://venue.example/events#details', 'https://broken.example/'])
    real_fetch = research.fetch_page
    def fetch(url, **kwargs):
        if 'broken' in url:
            raise research.FetchError('Website returned HTTP 403')
        return real_fetch(url)
    monkeypatch.setattr(research, 'fetch_page', fetch)
    result = research.research_venues(research.ResearchRequest(city='San Antonio, Texas', guests=40,
                     urls=['https://venue.example/events'], discover=True))
    assert len(result['candidates']) == 1 and len(result['errors']) == 1
    assert result['errors'][0]['url'] == 'https://broken.example/'


def test_search_failure_does_not_discard_supplied_urls(monkeypatch):
    research = configure(monkeypatch)
    monkeypatch.setenv('BRAVE_SEARCH_API_KEY', 'test-search')
    def broken_search(request, **kwargs):
        raise research.ResearchError('Search provider unavailable')
    monkeypatch.setattr(research, 'discover_urls', broken_search)
    result = research.research_venues(research.ResearchRequest(city='San Antonio, Texas', guests=40,
                     urls=['https://venue.example/events'], discover=True))
    assert len(result['candidates']) == 1 and result['errors']


def test_missing_openai_key_is_actionable(monkeypatch):
    research = research_module()
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    with pytest.raises(research.ResearchError, match='OPENAI_API_KEY'):
        research.research_venues(research.ResearchRequest(city='San Antonio, Texas', guests=40,
                                 urls=['https://venue.example'], discover=False))


def test_brave_adapter_parses_results_and_sends_only_city_and_guests(monkeypatch):
    research = research_module()
    monkeypatch.setenv('CONVENE_SEARCH_PROVIDER', 'brave')
    monkeypatch.setenv('BRAVE_SEARCH_API_KEY', 'test-search')
    def handler(request):
        assert request.headers['x-subscription-token'] == 'test-search'
        assert 'secret preference' not in str(request.url)
        assert 'San Antonio, Texas' in request.url.params['q']
        return httpx.Response(200, json={'web': {'results': [{'url': 'https://venue.example/'}]}})
    original = httpx.Client
    monkeypatch.setattr(research.httpx, 'Client', lambda **kwargs:
                        original(transport=httpx.MockTransport(handler), **kwargs))
    urls = research.discover_urls(research.ResearchRequest(city='San Antonio, Texas', guests=40,
                                preferences='secret preference', discover=True))
    assert urls == ['https://venue.example/']


def test_openai_adapter_uses_structured_output_and_does_not_store_page(monkeypatch):
    research = research_module()
    from convene.web_fetch import Page
    class Client:
        def __init__(self, **kwargs):
            self.responses = self
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def parse(self, **kwargs):
            assert kwargs['store'] is False
            assert kwargs['text_format'] is research.VenueExtraction
            assert 'Cedar Hall' in kwargs['input']
            return SimpleNamespace(output_parsed=research.VenueExtraction(**output()))
    import openai
    monkeypatch.setattr(openai, 'OpenAI', Client)
    monkeypatch.setenv('OPENAI_API_KEY', 'test-only-key')
    venue = research._extract(Page('https://venue.example/', 'Cedar Hall', 'now'))
    assert venue.name.value == 'Cedar Hall'


def test_research_api_validation_and_configuration_errors(tmp_path, monkeypatch):
    from convene.api import create_app
    client = TestClient(create_app(str(tmp_path / 'api.db'),allow_web_research=True))
    response = client.post('/venues/research', json={'city': 'San Antonio, Texas', 'guests': 40,
                           'discover': False, 'urls': []})
    assert response.status_code == 422
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    response = client.post('/venues/research', json={'city': 'San Antonio, Texas', 'guests': 40,
                           'discover': False, 'urls': ['https://venue.example/']})
    assert response.status_code == 503
    assert 'OPENAI_API_KEY' in response.json()['detail']


def test_research_api_returns_candidates_without_saving_plan(tmp_path, monkeypatch):
    research = configure(monkeypatch)
    from convene.api import create_app
    client = TestClient(create_app(str(tmp_path / 'api.db'),allow_web_research=True))
    response = client.post('/venues/research', json={'city': 'San Antonio, Texas', 'guests': 40,
                           'discover': False, 'urls': ['https://venue.example/']})
    assert response.status_code == 200
    assert response.json()['candidates'][0]['details']['name']['value'] == 'Cedar Hall'
    assert client.get('/plans').json() == []


@pytest.mark.parametrize('phase', ['search', 'fetch', 'extract'])
def test_whole_research_deadline_bounds_each_external_phase(monkeypatch, phase):
    import time
    research = configure(monkeypatch)
    monkeypatch.setenv('BRAVE_SEARCH_API_KEY', 'test-search')
    monkeypatch.setattr(research, 'RESEARCH_SECONDS', 0.03, raising=False)
    def stalled(*args, **kwargs):
        time.sleep(0.2)
        raise research.ResearchError('Stalled provider')
    if phase == 'search':
        monkeypatch.setattr(research, 'discover_urls', stalled)
    else:
        monkeypatch.setattr(research, 'fetch_page' if phase == 'fetch' else '_extract', stalled)
    start = time.monotonic()
    result = research.research_venues(research.ResearchRequest(city='San Antonio, Texas', guests=40,
                      urls=['https://venue.example/events'], discover=phase == 'search'))
    assert not result['candidates']
    assert any('deadline' in item['error'] for item in result['errors'])
    assert time.monotonic() - start < 0.15


@pytest.mark.parametrize('city', ['San Antonio', 'san antonio, tx', 'San Antonio Texas'])
def test_research_city_aliases_are_canonicalized(city):
    research = research_module()
    assert research.ResearchRequest(city=city, guests=40).city == 'San Antonio, Texas'


def test_other_cities_are_rejected_by_research_api(tmp_path):
    from convene.api import create_app
    client = TestClient(create_app(str(tmp_path / 'scope.db')))
    response = client.post('/venues/research', json={'city': 'Seattle', 'guests': 40})
    assert response.status_code == 422
    assert 'San Antonio' in response.text


@pytest.mark.parametrize('address', [None, '100 Example St, Austin, TX 78701',
                                   '100 Example St, San Antonio, California'])
def test_unconfirmed_or_outside_addresses_do_not_become_local_candidates(monkeypatch, address):
    research = configure(monkeypatch)
    from convene.web_fetch import Page
    data = output()
    data['address'] = {'value': address, 'evidence': address} if address else None
    monkeypatch.setattr(research, 'fetch_page', lambda url, **kwargs:
                        Page(url, 'Cedar Hall. ' + (address or ''), '2026-10-31T12:00:00+00:00'))
    monkeypatch.setattr(research, '_extract', lambda page, **kwargs: research.VenueExtraction(**data))
    result = research.research_venues(research.ResearchRequest(guests=40,
                                     urls=['https://venue.example/'], discover=False))
    assert not result['candidates']
    assert 'San Antonio' in result['errors'][0]['error']


def test_local_address_without_space_after_comma_is_accepted(monkeypatch):
    research = configure(monkeypatch)
    from convene.web_fetch import Page
    address = '100 Example St, San Antonio,TX 78205'
    data = output()
    data['address'] = {'value': address, 'evidence': address}
    monkeypatch.setattr(research, 'fetch_page', lambda url, **kwargs:
                        Page(url, 'Cedar Hall. ' + address, '2026-10-31T12:00:00+00:00'))
    monkeypatch.setattr(research, '_extract', lambda page, **kwargs: research.VenueExtraction(**data))
    result = research.research_venues(research.ResearchRequest(guests=40,
                                     urls=['https://venue.example/'], discover=False))
    assert result['candidates'][0]['location_scope'] == 'San Antonio, Texas'
