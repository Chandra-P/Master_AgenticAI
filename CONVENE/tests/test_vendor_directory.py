from fastapi.testclient import TestClient


def test_existing_venues_have_sourced_shared_reservations_contact():
    from convene.party_catalog import get_catalog
    venues=get_catalog()['venues']
    assert len(venues)==3
    for venue in venues:
        contact=venue['contact']
        assert contact['organization_id']=='bexar-county-parks'
        assert contact['phone_e164']=='+12103357275'
        assert contact['email'] is None and contact['email_status']=='not_verified'
        assert contact['source_url']==venue['source_url']
        assert contact['verified_on']=='2026-11-01'
        assert 'shared' in contact['role'].lower()


def test_private_app_serves_only_existing_approved_directory_without_network(repository):
    from convene.planner_api import create_planner_app
    client=TestClient(create_planner_app(repository,secure_cookies=False))
    assert client.get('/api/vendors').status_code==401
    client.post('/api/session')
    data=client.get('/api/vendors').json()
    assert {v['id'] for v in data['vendors']}=={'south-san','navajo','harlandale','belle-arch','bewitchin'}
    assert data['food']==[]
    assert all(v['approval']['status']=='approved' for v in data['vendors'])
    assert all(v['availability']=='unconfirmed' for v in data['vendors'])
