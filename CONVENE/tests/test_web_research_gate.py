from fastapi.testclient import TestClient


def test_legacy_live_web_routes_are_disabled_by_default(tmp_path,monkeypatch):
    from convene.api import create_app
    monkeypatch.delenv('CONVENE_ALLOW_WEB_RESEARCH',raising=False)
    client=TestClient(create_app(str(tmp_path/'legacy.db')))
    assert client.post('/party/agent',json={'mode':'live'}).status_code==403
    r=client.post('/venues/research',json={'guests':40,'urls':['https://example.org'],'discover':False})
    assert r.status_code==403 and 'approved' in r.json()['detail'].lower()
