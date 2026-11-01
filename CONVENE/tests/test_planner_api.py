from fastapi.testclient import TestClient

from convene.intake import ExtractedAnswer, BriefAnswers


def client_for(repository):
    from convene.planner_api import create_planner_app
    return TestClient(create_planner_app(repository,secure_cookies=False,
        extractor=lambda *args:ExtractedAnswer(answers=BriefAnswers(occasion='birthday'),evidence='birthday')))


def test_session_cookie_csrf_and_private_event_access(repository):
    alice=client_for(repository);bob=client_for(repository)
    assert alice.post('/api/events').status_code==401
    session=alice.post('/api/session').json()
    cookie=alice.cookies.get('convene_session')
    assert cookie and session.get('csrf_token')
    assert alice.post('/api/events').status_code==403
    created=alice.post('/api/events',headers={'X-CSRF-Token':session['csrf_token']})
    assert created.status_code==201
    event_id=created.json()['event']['id']
    loaded=alice.get(f'/api/events/{event_id}')
    assert loaded.status_code==200 and loaded.json()['next_action']=='answer'
    bob.post('/api/session')
    assert bob.get(f'/api/events/{event_id}').status_code==404
    assert alice.get('/plans').status_code==404
    assert alice.post('/party/agent',json={}).status_code==404


def test_reply_retry_logout_and_no_owner_spoofing(repository):
    from uuid import uuid4
    client=client_for(repository)
    session=client.post('/api/session').json();headers={'X-CSRF-Token':session['csrf_token']}
    opened=client.post('/api/events',headers=headers).json();event_id=opened['event']['id']
    payload={'message':'birthday','expected_version':1,'request_id':str(uuid4())}
    first=client.post(f'/api/events/{event_id}/messages',headers=headers,json=payload)
    assert first.status_code==200
    assert first.json()['question']['key']=='services'
    assert client.post(f'/api/events/{event_id}/messages',headers=headers,json=payload).json()==first.json()
    assert client.post(f'/api/events/{event_id}/messages',headers=headers,json={**payload,'owner_id':str(uuid4())}).status_code==422
    old_cookie=client.cookies.get('convene_session')
    assert client.post('/api/logout',headers=headers).status_code==204
    client.cookies.set('convene_session',old_cookie)
    assert client.get(f'/api/events/{event_id}').status_code==401
