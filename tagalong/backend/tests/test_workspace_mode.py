from fastapi.testclient import TestClient
from tagalong.app import create_app
from tagalong.core import Actor, MemoryRepository


def test_admin_requires_explicit_mode_and_qa_is_hidden_in_member_mode():
    repo=MemoryRepository();repo.state['app_admins']={'owner':{}}
    c=TestClient(create_app(repo,lambda t:Actor(t,t+'@test.com',t)))
    member={'Authorization':'Bearer owner'}
    admin={**member,'X-Workspace-Mode':'admin'}
    assert c.get('/v1/me',headers=member).json()['workspace_mode']=='member'
    assert c.get('/v1/admin/overview',headers=member).status_code==403
    assert c.get('/v1/admin/overview',headers=admin).status_code==200
    ids=c.post('/v1/admin/qa-plans',headers=admin,json={}).json()['plan_ids']
    assert c.get('/v1/plans',headers=member).json()==[]
    assert len(c.get('/v1/plans',headers=admin).json())==3
    for pid in ids:
        assert c.get('/v1/plans/'+pid,headers=member).status_code==404
        assert c.get('/v1/plans/'+pid+'/documents',headers=member).status_code==404
    normal=c.post('/v1/plans',headers=member,json={'title':'Real member plan','kind':'outing','start':'2026-11-21','end':'2026-11-21'}).json()
    assert [p['id'] for p in c.get('/v1/plans',headers=member).json()]==[normal['id']]
    assert c.get('/v1/admin/overview',headers={'Authorization':'Bearer stranger','X-Workspace-Mode':'admin'}).status_code==403
    assert c.get('/v1/me',headers={**member,'X-Workspace-Mode':'root'}).status_code==422


def test_demo_stories_are_admin_only_and_do_not_create_accounts_or_plans():
    repo=MemoryRepository();repo.state['app_admins']={'owner':{}}
    c=TestClient(create_app(repo,lambda t:Actor(t,t+'@test.com',t)))
    admin={'Authorization':'Bearer owner','X-Workspace-Mode':'admin'}
    assert c.get('/v1/admin/demo-stories',headers={'Authorization':'Bearer owner'}).status_code==403
    stories=c.get('/v1/admin/demo-stories',headers=admin).json()
    assert len(stories)==3
    for summary in stories:
        story=c.get('/v1/admin/demo-stories/'+summary['id'],headers=admin).json()
        assert len(story['events'])>=16
        assert story['simulated'] is True
        assert story['events'][-1]['stage']=='Final agreement'
        assert 'itinerary' in story['events'][-1]['snapshot']
    assert repo.state['plans']=={}
    assert set(repo.state['actors'])=={'owner'}
