from fastapi import FastAPI, Header, HTTPException
from fastapi.testclient import TestClient
from tagalong.core import Actor, MemoryRepository
from tagalong.demo_plan import install_demo_plans


def setup():
    repo = MemoryRepository()
    app = FastAPI()
    def actor(authorization: str | None = Header(default=None)):
        if not authorization or not authorization.startswith('Bearer '):
            raise HTTPException(401, 'Bearer session required')
        name = authorization[7:]
        return Actor(name, name+'@example.test', name)
    install_demo_plans(app, repo, actor)
    return repo, TestClient(app)


def test_owner_scoped_idempotent_saved_story_without_forged_members_or_votes():
    repo, client = setup()
    payload = {'template':'austin-four-friends', 'idempotency_key':'story-one'}
    owner = {'Authorization':'Bearer owner'}
    assert client.post('/v1/demo-plans', json=payload).status_code == 401
    response = client.post('/v1/demo-plans', headers=owner, json=payload)
    assert response.status_code == 200
    assert response.headers['cache-control'] == 'no-store'
    plan = response.json()
    assert plan['title'] == 'DEMO · Four friends, one Austin weekend'
    assert plan['owner_id'] == 'owner'
    assert plan['demo_template'] == 'austin-four-friends'
    assert repo.state['members'][plan['id']] == ['owner']
    assert len(plan['members']) == 1
    assert all(not poll['votes'] for poll in plan['polls'])
    assert client.post('/v1/demo-plans', headers=owner, json=payload).json()['id'] == plan['id']
    for index in range(3):
        assert client.post('/v1/demo-plans', headers=owner, json={**payload,'idempotency_key':'retry-'+str(index)}).json()['id'] == plan['id']
    assert len(repo.state['demo_plan_keys']) == 1
    other = client.post('/v1/demo-plans', headers={'Authorization':'Bearer other'}, json=payload).json()
    assert other['id'] != plan['id']
    story_url = '/v1/plans/'+plan['id']+'/demo-story'
    assert client.get(story_url, headers={'Authorization':'Bearer other'}).status_code == 404
    story_response = client.get(story_url, headers=owner)
    assert story_response.headers['cache-control'] == 'no-store'
    story = story_response.json()
    assert [person['name'] for person in story['cast']] == ['Alex','Maya','Sam','Jordan']
    assert len(story['milestones']) >= 7
    assert len(story['days']) == 3
    assert story['scripted'] is True
    assert len(story['choices']) == 5
    for choice in story['choices']:
        assert len(choice['alternatives']) == 3
        assert choice['reason']
        assert set(choice['votes']) == {'Alex','Maya','Sam','Jordan'}
        assert set(choice['votes'].values()) <= {'support','can_live_with'}
        assert choice['sourceIds'] == ['demo-constraints','demo-discussion']
    assert all(source['id'] in {s['id'] for s in repo.state['sources'].values()} for source in story['sources'])
    assert not repo.state.get('decision_state', {}).get(plan['id'], {}).get('finalization')
    assert not repo.state.get('demo_bookings')
    photos = [item for item in plan['itinerary'] if item.get('image_source_url')]
    assert len(photos) == 3
    assert all(item['image'].startswith('https://') and item['source_url'] == item['image_source_url'] for item in photos)
    assert all(item['category'] == 'Fictional walkthrough · source photo' for item in photos)
    assert all(not item['image'].startswith('https://') for item in plan['itinerary'] if item not in photos)
    assert all(message['simulation'] for message in plan['messages'])
    # Story is persisted separately; a fresh app instance reads the same record.
    assert repo.state['demo_plan_stories'][plan['id']] == story
    repo.state['plans'][plan['id']]['title']='Renamed presentation plan'
    assert client.post('/v1/demo-plans', headers=owner, json=payload).json()['demo_template']=='austin-four-friends'
    repo.state['members'][plan['id']].append('viewer')
    assert client.get(story_url, headers={'Authorization':'Bearer viewer'}).status_code == 200
    repo.state['members'][plan['id']].remove('viewer')
    assert client.get(story_url, headers={'Authorization':'Bearer viewer'}).status_code == 404


def test_public_austin_story_is_read_only_and_contains_only_scripted_content():
    import copy
    repo, client = setup()
    before = copy.deepcopy(repo.state)
    response = client.get('/v1/public/demo-stories/austin-four-friends')
    assert response.status_code == 200
    assert response.headers['cache-control'] == 'public, max-age=300'
    story = response.json()
    assert story['planId'] == 'public-austin-demo'
    assert story['scripted'] is True
    assert story['disclosure'] == 'Fictional walkthrough · scripted AI and votes · no bookings'
    assert [person['name'] for person in story['cast']] == ['Alex','Maya','Sam','Jordan']
    assert len(story['messages']) >= 30
    assert all(message['simulation'] is True for message in story['messages'])
    assert all(message.get('user_id') is None for message in story['messages'])
    assert len(story['choices']) == 5 and len(story['days']) == 3
    assert all(source['id'].startswith('demo-') for source in story['sources'])
    assert not story.get('liveCheck')
    assert repo.state == before


def test_template_and_request_are_bounded_and_suspension_is_enforced():
    repo, client = setup()
    owner = {'Authorization':'Bearer owner'}
    assert client.post('/v1/demo-plans', headers=owner, json={'template':'other','idempotency_key':'one'}).status_code == 422
    assert client.post('/v1/demo-plans', headers=owner, json={'template':'austin-four-friends','idempotency_key':''}).status_code == 422
    repo.state['suspended_users'] = {'owner':True}
    assert client.post('/v1/demo-plans', headers=owner, json={'template':'austin-four-friends','idempotency_key':'one'}).status_code == 403


def test_server_demo_marker_does_not_break_normal_edits_and_cannot_be_forged():
    import copy
    from tagalong.core import update
    import pytest
    from fastapi import HTTPException
    repo,client=setup();actor=Actor('owner','owner@example.test','owner')
    plan=client.post('/v1/demo-plans',headers={'Authorization':'Bearer owner'},json={'template':'austin-four-friends','idempotency_key':'editable'}).json()
    incoming=copy.deepcopy(plan);incoming['tasks'].append({'label':'Owner adds a real review task','done':False})
    saved=repo.transact(lambda state:update(state,actor,plan['id'],incoming,plan['revision']))
    assert saved['demo_template']=='austin-four-friends'
    assert saved['tasks'][-1]['label']=='Owner adds a real review task'
    incoming=copy.deepcopy(saved);incoming['demo_template']='forged-template'
    with pytest.raises(HTTPException) as error:repo.transact(lambda state:update(state,actor,plan['id'],incoming,saved['revision']))
    assert error.value.status_code==403


def test_demo_chat_has_four_friends_objections_cited_scripted_ai_and_rounds():
    from tagalong.models import Message
    repo,client=setup()
    plan=client.post('/v1/demo-plans',headers={'Authorization':'Bearer owner'},json={'template':'austin-four-friends','idempotency_key':'dialogue'}).json()
    messages=plan['messages'];assert 30<=len(messages)<=45
    assert {'Alex','Maya','Sam','Jordan','Tagalong'}=={m['author'] for m in messages}
    assert any('object' in m['text'].lower() for m in messages)
    assert len({m['time'] for m in messages})==7
    for m in messages:
        assert Message.model_validate(m).simulation is True
        assert m.get('user_id') is None and m['assistant']==(m['author']=='Tagalong')
    assert any(m.get('sources') for m in messages if m['assistant'])
    story=repo.state['demo_plan_stories'][plan['id']];assert story['dialogueVersion']==2
    assert all(len(c['rounds'])==2 for c in story['choices'])
    assert any('object' in r['votes'].values() for c in story['choices'] for r in c['rounds'])


def test_upgrade_demo_preserves_live_messages_is_owner_only_and_idempotent():
    import copy
    import pytest
    from fastapi import HTTPException
    from tagalong.demo_plan import upgrade_demo_plan
    repo,client=setup();actor=Actor('owner','owner@example.test','owner')
    plan=client.post('/v1/demo-plans',headers={'Authorization':'Bearer owner'},json={'template':'austin-four-friends','idempotency_key':'upgrade'}).json();pid=plan['id']
    state=repo.state;state['demo_plan_stories'][pid].pop('dialogueVersion',None)
    state['demo_plan_stories'][pid]['liveCheck']={'historical':'kept'}
    human={'id':'actual-human','author':'owner','user_id':'owner','text':'My actual reply','time':'Now','assistant':False}
    live_ai={'id':'actual-ai','author':'Tagalong AI','text':'Actual provider reply','time':'Now','assistant':True}
    state['plans'][pid]['messages']=[{'id':'demo-story-introduction','author':'Fictional demo narrator','text':'Fictional old story','time':'Demo story','assistant':False},human,live_ai]
    state['members'][pid].append('viewer')
    with pytest.raises(HTTPException) as error:upgrade_demo_plan(state,Actor('viewer','viewer@example.test','viewer'),pid)
    assert error.value.status_code==403
    state['members'][pid].remove('viewer')
    upgraded=repo.transact(lambda s:upgrade_demo_plan(s,actor,pid))
    assert upgraded['revision']==plan['revision']+1
    assert upgraded['messages'][-2:]==[human,live_ai]
    assert 'liveCheck' not in state['demo_plan_stories'][pid]
    assert state['demo_plan_stories'][pid]['previousLiveChecks']==[{'historical':'kept'}]
    before=copy.deepcopy(repo.state)
    repo.transact(lambda s:upgrade_demo_plan(s,actor,pid))
    assert repo.state==before


def test_simulation_chat_marker_cannot_be_forged_or_modified():
    import copy
    import pytest
    from fastapi import HTTPException
    from tagalong.core import update
    repo,client=setup();actor=Actor('owner','owner@example.test','owner')
    plan=client.post('/v1/demo-plans',headers={'Authorization':'Bearer owner'},json={'template':'austin-four-friends','idempotency_key':'forgery'}).json()
    for flag in (True,False):
        incoming=copy.deepcopy(plan)
        incoming['messages'].append({'id':'forged','author':'owner','user_id':'owner','text':'Forged simulation','time':'Now','assistant':False,'simulation':flag})
        with pytest.raises(HTTPException) as error:repo.transact(lambda s:update(s,actor,plan['id'],incoming,plan['revision']))
        assert error.value.status_code==403
    incoming=copy.deepcopy(plan);incoming['messages'][0]['simulation']=False
    with pytest.raises(HTTPException) as error:repo.transact(lambda s:update(s,actor,plan['id'],incoming,plan['revision']))
    assert error.value.status_code==403
