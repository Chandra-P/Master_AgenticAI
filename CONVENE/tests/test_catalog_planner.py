from datetime import date

import pytest

from convene.domain import EventBriefVersion,Principal
from convene.policy import PolicyDenied
from convene.repository import Conflict,NotFound


def brief(**patch):
    return EventBriefVersion.model_validate(dict(occasion='birthday',age=10,children=30,family=90,
        services=['venue','decoration'],event_date=date(2026,12,6),budget=2000,theme='Stitch',
        priorities='Keep all guests',time_window='afternoon',**patch))


def test_real_approved_inventory_is_matched_without_inventing_options(repository):
    from convene.catalog_planner import match_catalog
    from convene.vendor_directory import DirectoryRepository
    result=match_catalog(brief(),DirectoryRepository(repository.dsn).list_approved())
    assert len(result['groups']['venue']['options'])==3
    assert len(result['groups']['decoration']['options'])==2
    assert result['guests']==120 and result['budget_status']=='needs_quotes'
    assert all(o['vendor']['approval']['status']=='approved' for o in result['options'])
    assert all(o['missing'] for o in result['options'])
    assert result['known_minimum_combination']==610
    assert 'not an all-in quote' in result['cost_note']


def test_capacity_and_lower_bound_conflict_never_change_guests_or_budget(repository):
    from convene.catalog_planner import match_catalog
    from convene.vendor_directory import DirectoryRepository
    b=EventBriefVersion(occasion='graduation',services=['venue'],children=30,family=200,
        event_date=date(2026,12,6),budget=100)
    result=match_catalog(b,DirectoryRepository(repository.dsn).list_approved())
    assert not result['groups']['venue']['options']
    assert len(result['groups']['venue']['excluded'])==3
    assert result['guests']==230 and result['budget_ceiling']==100
    assert result['budget_status']=='needs_changes'


def test_food_gap_and_unknown_prices_are_not_zero(repository):
    from convene.catalog_planner import match_catalog
    from convene.vendor_directory import DirectoryRepository
    b=EventBriefVersion(occasion='graduation',services=['venue','food'],guest_estimate=40,
        event_date=date(2026,12,6),budget=2000)
    result=match_catalog(b,DirectoryRepository(repository.dsn).list_approved())
    assert not result['groups']['food']['options']
    assert result['known_minimum_combination'] is None
    assert any('food' in gap.lower() for gap in result['gaps'])


def test_confirmed_owner_can_compare_public_catalog_but_not_research(repository):
    from convene.catalog_planner import CatalogPlanner
    from convene.planner_graph import setup_checkpoints
    from convene.policy import authorize_action
    setup_checkpoints(repository.dsn)
    actor=Principal();event=repository.create_event(actor,brief())
    planner=CatalogPlanner(repository)
    with pytest.raises(PolicyDenied):planner.compare(actor,event.id,expected_version=1)
    repository.confirm_event(actor,event.id,expected_version=1)
    first=planner.compare(actor,event.id,expected_version=1)
    assert first['completed_nodes']==['Requirements','Budget','Vendor','Schedule','Creative','Review']
    assert planner.compare(actor,event.id,expected_version=1)['run_id']==first['run_id']
    with pytest.raises(NotFound):planner.compare(Principal(),event.id,expected_version=1)
    with pytest.raises(PolicyDenied):authorize_action(actor,repository.get_event(actor,event.id),'research')
    repository.revise_event(actor,event.id,{'budget':2500},expected_version=1)
    with pytest.raises(Conflict):planner.compare(actor,event.id,expected_version=1)


def test_shortlist_and_shared_office_drafts_are_private_versioned_and_unsent(repository):
    from convene.catalog_planner import CatalogPlanner
    planner=CatalogPlanner(repository);actor=Principal();event=repository.create_event(actor,brief())
    repository.confirm_event(actor,event.id,expected_version=1)
    planner.select(actor,event.id,'south-san',vendor_version=1,expected_version=1,selected=True)
    planner.select(actor,event.id,'navajo',vendor_version=1,expected_version=1,selected=True)
    planner.select(actor,event.id,'navajo',vendor_version=1,expected_version=1,selected=True)
    assert len(planner.shortlist(actor,event.id,expected_version=1)['selected'])==2
    drafts=planner.drafts(actor,event.id,expected_version=1)
    assert len(drafts['drafts'])==1
    draft=drafts['drafts'][0]
    assert len(draft['vendor_ids'])==2 and draft['to']==[]
    assert draft['sendable'] is False and '120' in draft['body']
    assert '2026-12-06' in draft['body'] and 'not sent' in draft['status']
    with pytest.raises(NotFound):planner.shortlist(Principal(),event.id,expected_version=1)
    with pytest.raises(Conflict):planner.select(actor,event.id,'south-san',vendor_version=999,expected_version=1,selected=True)
    repository.revise_event(actor,event.id,{'budget':2500},expected_version=1)
    with pytest.raises(Conflict):planner.drafts(actor,event.id,expected_version=1)


def test_api_compares_and_shortlists_after_confirmation_without_web_or_account_spoof(repository):
    from fastapi.testclient import TestClient
    from convene.planner_api import create_planner_app
    from convene.intake import ExtractedAnswer,BriefAnswers
    def extract(*args):return ExtractedAnswer(answers=BriefAnswers(occasion='graduation',services=['venue'],
        guest_estimate=40,event_date=date(2026,12,6),budget=2000,priorities='Guests',time_window='afternoon'),evidence='graduation')
    c=TestClient(create_planner_app(repository,secure_cookies=False,extractor=extract))
    s=c.post('/api/session').json();headers={'X-CSRF-Token':s['csrf_token']}
    event=c.post('/api/events',headers=headers).json()['event']
    from uuid import uuid4
    answer=c.post(f'/api/events/{event["id"]}/messages',headers=headers,json={
        'message':'graduation','expected_version':1,'request_id':str(uuid4())}).json()
    version=answer['event']['brief']['version'];path=f'/api/events/{event["id"]}'
    assert c.post(path+'/recommendations',headers=headers,json={'expected_version':version}).status_code==403
    assert c.post(path+'/confirm',headers=headers,json={'expected_version':version}).json()['next_action']=='compare_catalog'
    result=c.post(path+'/recommendations',headers=headers,json={'expected_version':version})
    assert result.status_code==200 and result.json()['mode']=='approved_catalog'
    chosen=result.json()['groups']['venue']['options'][0]['vendor']
    payload={'expected_version':version,'vendor_id':chosen['id'],'vendor_version':chosen['directory_version'],'selected':True}
    assert c.post(path+'/shortlist',headers=headers,json=payload).status_code==200
    assert c.post(path+'/drafts',headers=headers,json={'expected_version':version}).json()['drafts']
    assert c.post(path+'/recommendations',json={'expected_version':version}).status_code==403


def test_approved_vendor_rag_context_requires_current_confirmed_brief(repository):
    from convene.catalog_planner import CatalogPlanner
    actor=Principal();event=repository.create_event(actor,brief());planner=CatalogPlanner(repository)
    assert planner.context(actor,event.id,'venue capacity')==[]
    repository.confirm_event(actor,event.id,expected_version=1)
    context=planner.context(actor,event.id,'South San capacity')
    assert any(c['vendor_id']=='south-san' and '160' in c['content'] for c in context)
    assert all(c['kind']=='approved_vendor' and c['brief_version']==1 for c in context)
    repository.revise_event(actor,event.id,{'budget':2500},expected_version=1)
    assert planner.context(actor,event.id,'venue capacity')==[]


def test_approval_changes_invalidate_cache_shortlist_and_rag_history(repository):
    import os
    from uuid import uuid4
    from dotenv import dotenv_values
    from convene.vendor_directory import DirectoryAdmin
    from convene.catalog_planner import CatalogPlanner
    from convene.intake import IntakeService,ExtractedAnswer
    from convene.planner_graph import setup_checkpoints
    setup_checkpoints(repository.dsn)
    admin=DirectoryAdmin(os.getenv('CONVENE_TEST_DIRECTORY_ADMIN_URL') or dotenv_values('.env')['CONVENE_TEST_DIRECTORY_ADMIN_URL'],operator='catalog test reviewer')
    vendor_id='test-'+uuid4().hex
    vendor={'id':vendor_id,'name':'Temporary test room','kind':'venue','price':10,'capacity':500,
        'source_url':'https://example.org/test','address':'100 Test Rd, San Antonio, TX 78221'}
    actor=Principal();event=repository.create_event(actor,brief())
    repository.confirm_event(actor,event.id,expected_version=1)
    planner=CatalogPlanner(repository)
    try:
        admin.propose(vendor,reason='Fixture',expected_version=0);admin.approve(vendor_id,1,reason='Fixture approved')
        first=planner.compare(actor,event.id,expected_version=1)
        planner.select(actor,event.id,vendor_id,vendor_version=1,expected_version=1,selected=True)
        chunk=next(x for x in planner.context(actor,event.id,'Temporary test room') if x['vendor_id']==vendor_id)
        repository.commit_intake(actor,event.id,'old question',None,{'question':None,
            'assistant_message':'Old temporary room details from version one','sources':[chunk]},expected_version=1,request_id=uuid4())
        admin.propose({**vendor,'price':15},reason='New rate',expected_version=1);admin.approve(vendor_id,2,reason='New rate reviewed')
        second=planner.compare(actor,event.id,expected_version=1)
        assert second['run_id']!=first['run_id']
        assert not planner.shortlist(actor,event.id,expected_version=1)['selected']
        assert planner.drafts(actor,event.id,expected_version=1)['stale']
        seen=[]
        class Model:
            def respond_with_context(self,message,brief,history,context):
                seen.extend(history);return ExtractedAnswer(intent='help')
        IntakeService(repository,extractor=Model()).reply(actor,event.id,'room rates?',expected_version=1,request_id=uuid4())
        assert not any('version one' in t['body'] for t in seen)
        admin.suspend(vendor_id,reason='Fixture suspended')
        third=planner.compare(actor,event.id,expected_version=1)
        assert third['run_id']!=second['run_id']
        assert not any(o['vendor']['id']==vendor_id for o in third['options'])
        assert not any(c['vendor_id']==vendor_id for c in planner.context(actor,event.id,'Temporary room'))
    finally:admin.suspend(vendor_id,reason='Test cleanup')


@pytest.mark.parametrize('during_model',[False,True])
def test_private_and_inflight_provider_quotes_cannot_bypass_suspension(repository,during_model):
    import os
    from uuid import uuid4
    from datetime import datetime,timezone
    from dotenv import dotenv_values
    from convene.vendor_directory import DirectoryAdmin
    from convene.domain import EvidenceFact
    from convene.evidence_retrieval import EvidenceIndex
    from convene.intake import IntakeService,ExtractedAnswer
    admin=DirectoryAdmin(os.getenv('CONVENE_TEST_DIRECTORY_ADMIN_URL') or dotenv_values('.env')['CONVENE_TEST_DIRECTORY_ADMIN_URL'],operator='freshness test')
    vendor_id='test-'+uuid4().hex
    body={'id':vendor_id,'name':'Temporary violet room','kind':'venue','price':10,'capacity':500,
        'source_url':'https://example.org/violet','address':'100 Test Rd, San Antonio, TX 78221'}
    actor=Principal(authenticated=True);event=repository.create_event(actor,brief())
    repository.confirm_event(actor,event.id,expected_version=1)
    try:
        admin.propose(body,reason='Fixture',expected_version=0);admin.approve(vendor_id,1,reason='Reviewed')
        fact=EvidenceFact(event_id=event.id,provider_id=vendor_id,brief_version=1,field='pricing',value='77',
            excerpt='Violet room private quote is 77 dollars.',source_kind='provider_email',source_id='thread:test',
            retrieved_at=datetime.now(timezone.utc))
        EvidenceIndex(repository).add(actor,fact)
        if not during_model:admin.suspend(vendor_id,reason='No longer approved')
        seen=[]
        class Model:
            def respond_with_context(self,message,brief,history,context):
                seen.extend(context)
                if during_model:
                    chosen=next(c for c in context if c['id']==str(fact.id))
                    admin.suspend(vendor_id,reason='Suspended during model call')
                    return ExtractedAnswer(intent='help',source_ids=[chosen['id']],
                        grounded_quotes=[{'source_id':chosen['id'],'quote':fact.excerpt}])
                return ExtractedAnswer(intent='help')
        response=IntakeService(repository,extractor=Model()).reply(actor,event.id,'Violet room private quote?',expected_version=1,request_id=uuid4())
        if not during_model:assert not any(c['id']==str(fact.id) for c in seen)
        assert not any(s['id']==str(fact.id) for s in response.get('sources',[]))
        assert '77 dollars' not in response['assistant_message']
    finally:admin.suspend(vendor_id,reason='Test cleanup')


def test_one_unsupported_field_does_not_discard_other_supported_parent_answers(repository):
    from uuid import uuid4
    from convene.intake import IntakeService,ExtractedAnswer,BriefAnswers
    actor=Principal()
    class Model:
        def respond_with_context(self,*args):
            return ExtractedAnswer(answers=BriefAnswers(occasion='birthday',theme='Stitch'),
                field_evidence=[{'field':'occasion','quote':'birthday'},{'field':'theme','quote':'Stitch'}])
    service=IntakeService(repository,extractor=Model());opened=service.start(actor)
    response=service.reply(actor,opened['event']['id'],'birthday',expected_version=1,request_id=uuid4())
    assert response['event']['brief']['occasion']=='birthday'
    assert response['event']['brief']['theme'] is None
    assert response['question']['key']=='services'


def test_shared_draft_never_promotes_an_unverified_email(repository,monkeypatch):
    from convene.catalog_planner import CatalogPlanner
    actor=Principal();event=repository.create_event(actor,brief());repository.confirm_event(actor,event.id,expected_version=1)
    planner=CatalogPlanner(repository)
    common={'organization_id':'office','email':'office@example.org'}
    vendors=[{'id':'one','name':'Room one','directory_version':1,'contact':{**common,'email_status':'verified'}},
             {'id':'two','name':'Room two','directory_version':1,'contact':{**common,'email_status':'not_verified'}}]
    monkeypatch.setattr(planner,'shortlist',lambda *a,**k:{'selected':vendors,'stale':[]})
    draft=planner.drafts(actor,event.id,expected_version=1)['drafts'][0]
    assert draft['to']==[] and not draft['sendable']
