from datetime import date,datetime,timezone

import pytest

from convene.domain import Principal,EventBriefVersion,EvidenceFact
from convene.repository import NotFound


def test_planning_guidance_is_retrieved_from_postgres(repository):
    from convene.evidence_retrieval import EvidenceIndex
    parent=Principal();event=repository.create_event(parent)
    hits=EvidenceIndex(repository).retrieve(parent,event.id,'budget cost prices fees')
    assert hits and any('budget' in h['content'].lower() for h in hits)
    assert all(h['kind']=='planning' and h['source_id'] for h in hits)


def test_private_evidence_is_bound_to_parent_event_and_current_version(repository):
    from convene.evidence_retrieval import EvidenceIndex
    from convene.policy import PolicyDenied
    actor=Principal(authenticated=True)
    brief=EventBriefVersion(occasion='graduation',services=['venue'],guest_estimate=40,
        event_date=date(2026,12,6),budget=2000)
    event=repository.create_event(actor,brief)
    repository.confirm_event(actor,event.id,expected_version=1)
    index=EvidenceIndex(repository)
    fact=EvidenceFact(event_id=event.id,provider_id='fixture',brief_version=1,field='capacity',
        value='160',excerpt='The Cypress test room seats 160 guests.',source_kind='public_page',
        source_id='https://example.org/test-room',retrieved_at=datetime.now(timezone.utc))
    index.add(actor,fact)
    hits=index.retrieve(actor,event.id,'Cypress capacity seats')
    assert any(h['id']==str(fact.id) for h in hits)
    with pytest.raises(NotFound):index.retrieve(Principal(),event.id,'Cypress')
    other=repository.create_event(actor,brief)
    assert not any(h['id']==str(fact.id) for h in index.retrieve(actor,other.id,'Cypress'))
    anonymous=Principal(id=actor.id)
    assert not any(h['id']==str(fact.id) for h in index.retrieve(anonymous,event.id,'Cypress'))
    repository.revise_event(actor,event.id,{'guest_estimate':60},expected_version=1)
    assert not any(h['id']==str(fact.id) for h in index.retrieve(actor,event.id,'Cypress'))
    with pytest.raises(PolicyDenied):index.add(actor,fact)


def test_grounded_conversation_receives_retrieved_context_and_returns_sources(repository):
    from convene.intake import IntakeService,ExtractedAnswer
    actor=Principal();seen=[]
    class Model:
        def respond_with_context(self,message,brief,history,context):
            seen.extend(context)
            return ExtractedAnswer(intent='help',source_ids=[context[0]['id']],
                grounded_quotes=[{'source_id':context[0]['id'],'quote':'Published base prices and minimums are not all-in quotes.'}])
    service=IntakeService(repository,extractor=Model());opened=service.start(actor)
    from uuid import uuid4
    response=service.reply(actor,opened['event']['id'],'How do you help with my budget?',expected_version=1,request_id=uuid4())
    assert seen and response['sources']
    assert 'not all-in quotes' in response['assistant_message']
    assert response['assistant_message'].count('?')==1
    assert response['event']==opened['event']
    assert repository.intake_history(actor,opened['event']['id'])[-1]['sources']==response['sources']


def test_model_cannot_cite_a_source_it_did_not_retrieve(repository):
    from convene.intake import IntakeService,ExtractedAnswer
    from uuid import uuid4
    actor=Principal()
    class Model:
        def respond_with_context(self,*args):
            return ExtractedAnswer(intent='help',reply='Invented venue price is $50.',source_ids=['not-retrieved'])
    service=IntakeService(repository,extractor=Model());opened=service.start(actor)
    response=service.reply(actor,opened['event']['id'],'venue prices?',expected_version=1,request_id=uuid4())
    assert 'Invented' not in response['assistant_message'] and not response.get('sources')


def test_retrieved_document_reference_also_resolves_to_its_chunk(repository):
    from convene.intake import IntakeService,ExtractedAnswer
    from uuid import uuid4
    class Model:
        def respond_with_context(self,*args):
            return ExtractedAnswer(intent='help',source_ids=['convene:approved-planner-design#budget'],
                grounded_quotes=[{'source_id':'convene:approved-planner-design#budget',
                    'quote':'Published base prices and minimums are not all-in quotes.'}])
    actor=Principal();service=IntakeService(repository,extractor=Model());event=service.start(actor)['event']
    response=service.reply(actor,event['id'],'budget fees?',expected_version=1,request_id=uuid4())
    assert response['sources'][0]['id']=='planning-budget'
    assert 'not all-in quotes' in response['assistant_message']


@pytest.mark.parametrize('intent',['help','small_talk'])
def test_existing_source_does_not_support_invented_provider_claim(repository,intent):
    from convene.intake import IntakeService,ExtractedAnswer
    from uuid import uuid4
    class Model:
        def respond_with_context(self,*args):
            return ExtractedAnswer(intent=intent,reply='Cypress costs $50 and is booked.',source_ids=['planning-budget'])
    actor=Principal();service=IntakeService(repository,extractor=Model());event=service.start(actor)['event']
    response=service.reply(actor,event['id'],'venue budget costs?',expected_version=1,request_id=uuid4())
    assert 'Cypress' not in response['assistant_message'] and '$50' not in response['assistant_message']


def test_model_history_drops_stale_private_assistant_answers(repository):
    from convene.intake import IntakeService,ExtractedAnswer
    from uuid import uuid4
    actor=Principal(authenticated=True);event=repository.create_event(actor)
    repository.record_intake_greeting(actor,event.id,'Welcome')
    repository.commit_intake(actor,event.id,'test',None,{'question':None,'assistant_message':'Old private venue costs $999.',
        'sources':[{'id':'old','kind':'event_evidence','brief_version':1}]},expected_version=1,request_id=uuid4())
    repository.revise_event(actor,event.id,{'occasion':'birthday'},expected_version=1)
    seen=[]
    class Model:
        def respond_with_context(self,message,brief,history,context):
            seen.extend(history);return ExtractedAnswer(intent='help')
    IntakeService(repository,extractor=Model()).reply(actor,event.id,'help',expected_version=2,request_id=uuid4())
    assert not any('$999' in row['body'] for row in seen)


def test_correction_does_not_publish_evidence_from_previous_confirmed_brief(repository):
    from convene.evidence_retrieval import EvidenceIndex
    from convene.intake import IntakeService,ExtractedAnswer,BriefAnswers
    from uuid import uuid4
    actor=Principal(authenticated=True)
    event=repository.create_event(actor,EventBriefVersion(occasion='graduation',services=['venue'],guest_estimate=40,
        event_date=date(2026,12,6),budget=2000))
    repository.confirm_event(actor,event.id,expected_version=1)
    fact=EvidenceFact(event_id=event.id,provider_id='cypress',brief_version=1,field='capacity',value='160',
        excerpt='Cypress seats 160 guests.',source_kind='public_page',source_id='https://example.org/cypress',
        retrieved_at=datetime.now(timezone.utc))
    EvidenceIndex(repository).add(actor,fact)
    class Model:
        def respond_with_context(self,*args):
            return ExtractedAnswer(answers=BriefAnswers(budget=2500),source_ids=[str(fact.id)],
                field_evidence=[{'field':'budget','quote':'2500'}],
                grounded_quotes=[{'source_id':str(fact.id),'quote':'Cypress seats 160 guests.'}])
    response=IntakeService(repository,extractor=Model()).reply(actor,event.id,'Cypress budget now 2500',
        expected_version=1,request_id=uuid4())
    assert response['event']['brief']['budget']=='2500'
    assert not response.get('sources') and 'Cypress seats' not in response['assistant_message']


def test_facts_must_be_supported_in_the_current_message(repository):
    from convene.intake import IntakeService,ExtractedAnswer,BriefAnswers
    from uuid import uuid4
    actor=Principal()
    class Model:
        def respond_with_context(self,*args):
            return ExtractedAnswer(answers=BriefAnswers(occasion='birthday'),
                field_evidence=[{'field':'occasion','quote':'birthday'}])
    service=IntakeService(repository,extractor=Model());event=service.start(actor)['event']
    response=service.reply(actor,event['id'],'What about the budget?',expected_version=1,request_id=uuid4())
    assert response['event']==event and 'misunderstood' in response['assistant_message']
