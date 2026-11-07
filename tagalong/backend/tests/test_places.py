import httpx
from fastapi.testclient import TestClient
from tagalong.app import create_app
from tagalong.core import Actor, MemoryRepository


def test_keenable_maps_only_safe_source_links(monkeypatch):
    from tagalong.places import KeenableSearch
    monkeypatch.delenv('KEENABLE_API_KEY',raising=False)
    def handler(request):
        assert str(request.url)=='https://api.keenable.ai/v1/search/public'
        assert request.headers['X-Keenable-Title']=='Tagalong'
        return httpx.Response(200,json={'results':[
            {'title':'A restaurant','url':'https://restaurant.example/menu','snippet':'Vegetarian options'},
            {'title':'Duplicate','url':'https://restaurant.example/menu'},
            {'title':'Unsafe','url':'javascript:alert(1)'},
            {'title':'Local','url':'http://127.0.0.1/admin'},
            {'title':'Credential URL','url':'https://person:password@example.com/'},
            {'title':'Invalid browser URL','url':'https://bad%20host.example/'},
            {'title':'Legacy local address','url':'http://0x7f.1/'},
        ]})
    search=KeenableSearch(transport=httpx.MockTransport(handler))
    results=search.search('vegetarian restaurants','San Francisco','restaurants')
    assert len(results)==1
    assert results[0]['url']=='https://restaurant.example/menu'
    assert results[0]['snippet']=='Vegetarian options'


def test_search_requires_auth_bounds_inputs_and_limits_calls():
    class Search:
        def search(self,*args):return [{'title':'A place','url':'https://example.com/','snippet':'Public source'}]
    c=TestClient(create_app(MemoryRepository(),lambda t:Actor(t,t+'@test.com',t),places=Search()))
    payload={'query':'vegetarian dinner','location':'San Francisco','category':'restaurants'}
    assert c.post('/v1/places/search',json=payload).status_code==401
    headers={'Authorization':'Bearer account'}
    assert c.post('/v1/places/search',headers=headers,json={**payload,'query':'a'}).status_code==422
    for _ in range(10):
        r=c.post('/v1/places/search',headers=headers,json=payload)
        assert r.status_code==200
        assert r.json()['provider']=='Keenable'
    assert c.post('/v1/places/search',headers=headers,json=payload).status_code==429


def test_provider_error_is_actionable_and_does_not_expose_details():
    from tagalong.places import KeenableSearch
    transport=httpx.MockTransport(lambda r:httpx.Response(429,text='private provider detail'))
    search=KeenableSearch(transport=transport)
    c=TestClient(create_app(MemoryRepository(),lambda t:Actor(t,t+'@test.com',t),places=search))
    response=c.post('/v1/places/search',headers={'Authorization':'Bearer account'},json={'query':'restaurants','location':'San Francisco','category':'restaurants'})
    assert response.status_code==502
    assert 'private provider detail' not in response.text
