from datetime import date
from uuid import uuid4

import pytest


def test_model_echo_of_existing_brief_does_not_reject_new_services_answer():
    from convene.intake import apply_extraction,ExtractedAnswer,BriefAnswers
    from convene.domain import EventBriefVersion
    brief=EventBriefVersion(occasion='birthday',age=10,children=30,family=90)
    proposal=ExtractedAnswer(answers=BriefAnswers(occasion='birthday',age=10,children=30,family=90,
        guest_estimate=120,services=['venue','decoration']),
        field_evidence=[{'field':'services','quote':'venue and decorations'}])
    changed=apply_extraction(brief,proposal,'venue and decorations')
    assert changed.services==['venue','decoration']
    assert changed.total_guests==120 and changed.guest_estimate is None


def test_changed_family_count_still_checks_an_inconsistent_total():
    from convene.intake import apply_extraction,ExtractedAnswer,BriefAnswers
    from convene.domain import EventBriefVersion
    with pytest.raises(ValueError):
        apply_extraction(EventBriefVersion(children=30,family=90),ExtractedAnswer(
            answers=BriefAnswers(children=20,family=50,guest_estimate=120),
            evidence='20 kids, 50 parents, 120 total'),'20 kids, 50 parents, 120 total')


def test_reaffirming_same_budget_can_clear_tentative_status():
    from convene.intake import apply_extraction,ExtractedAnswer,BriefAnswers
    from convene.domain import EventBriefVersion
    result=apply_extraction(EventBriefVersion(budget=2000,tentative_fields={'budget'}),
        ExtractedAnswer(answers=BriefAnswers(budget=2000),
            field_evidence=[{'field':'budget','quote':'2000 is firm'}]),'Yes, 2000 is firm')
    assert result.budget==2000 and 'budget' not in result.tentative_fields


def test_small_talk_is_conversation_not_an_unknown_event_answer(repository):
    from convene.intake import IntakeService,ExtractedAnswer
    from convene.domain import Principal
    service=IntakeService(repository,extractor=lambda *args:ExtractedAnswer(intent='small_talk',
        unknown_fields=['occasion'],evidence=''))
    parent=Principal();opened=service.start(parent);request_id=uuid4()
    response=service.reply(parent,opened['event']['id'],'how ar you',expected_version=1,request_id=request_id)
    assert response['event']==opened['event']
    assert 'ready to help' in response['question']['text']
    assert response['question']['text'].count('?')==1
    assert response['question']['key']=='occasion'
    assert service.reply(parent,opened['event']['id'],'how ar you',expected_version=1,request_id=request_id)==response


def test_unsupported_model_answer_prompts_clarification_without_mutating_brief(repository):
    from convene.intake import IntakeService,ExtractedAnswer,BriefAnswers
    from convene.domain import Principal
    service=IntakeService(repository,extractor=lambda *args:ExtractedAnswer(
        answers=BriefAnswers(budget=5000),evidence='spend 5000'))
    parent=Principal();opened=service.start(parent)
    response=service.reply(parent,opened['event']['id'],'something fun',expected_version=1,request_id=uuid4())
    assert response['event']==opened['event']
    assert 'misunderstood' in response['question']['text']
    assert len(repository.intake_history(parent,opened['event']['id']))==3


def test_empty_extraction_keeps_confirmed_version(repository):
    from convene.intake import IntakeService,ExtractedAnswer
    from convene.domain import Principal,EventBriefVersion
    parent=Principal()
    event=repository.create_event(parent,EventBriefVersion(occasion='graduation',services=['venue'],
        guest_estimate=40,event_date=date(2026,12,6),budget=2000,time_window='afternoon',priorities='Guests'))
    event=repository.confirm_event(parent,event.id,expected_version=1)
    service=IntakeService(repository,extractor=lambda *args:ExtractedAnswer())
    response=service.reply(parent,event.id,'thank you',expected_version=1,request_id=uuid4())
    assert response['event']==event.model_dump(mode='json')


@pytest.mark.parametrize('message',['hi','Hello!',' hey there '])
def test_simple_greeting_is_warm_and_needs_no_model(repository,message):
    from convene.intake import IntakeService
    from convene.domain import Principal
    parent=Principal()
    service=IntakeService(repository,extractor=lambda *args:pytest.fail('Greeting must not call model'))
    opened=service.start(parent)
    response=service.reply(parent,opened['event']['id'],message,expected_version=1,request_id=uuid4())
    assert response['event']['brief']['occasion'] is None
    assert response['event']['brief']['version']==1
    assert response['event']['brief']['explicit_unknown']==[]
    assert response['question']['key']=='occasion'
    assert response['question']['text'].startswith('Hi!')
    assert response['question']['text'].count('?')==1
    assert len(repository.intake_history(parent,opened['event']['id']))==3


def test_greeting_with_event_facts_still_extracts_them(repository):
    from convene.intake import IntakeService,ExtractedAnswer,BriefAnswers
    from convene.domain import Principal
    calls=[]
    def extract(message,*args):
        calls.append(message)
        return ExtractedAnswer(answers=BriefAnswers(occasion='birthday'),evidence='birthday')
    service=IntakeService(repository,extractor=extract);parent=Principal()
    opened=service.start(parent)
    response=service.reply(parent,opened['event']['id'],"Hi, I'm planning a birthday",expected_version=1,request_id=uuid4())
    assert calls and response['event']['brief']['occasion']=='birthday'


def test_greeting_starts_with_occasion_without_research():
    from convene.intake import next_question
    from convene.domain import EventBriefVersion
    question=next_question(EventBriefVersion())
    assert question.key=='occasion'
    assert question.text.count('?')==1
    assert 'Welcome' in question.text


def test_questions_adapt_to_chosen_services_and_missing_family():
    from convene.intake import next_question
    from convene.domain import EventBriefVersion
    brief=EventBriefVersion(occasion='birthday',services=['venue'],age=10,children=30)
    assert next_question(brief).key=='family'
    complete=EventBriefVersion(occasion='graduation',services=['venue'],guest_estimate=40,
        event_date=date(2026,12,6),budget=2000,priorities='Keep everyone invited',time_window='afternoon')
    assert next_question(complete) is None


def test_unsure_answer_does_not_invent_a_budget_and_can_continue():
    from convene.intake import apply_extraction,ExtractedAnswer,next_question
    from convene.domain import EventBriefVersion
    brief=EventBriefVersion(occasion='graduation',services=['venue'],guest_estimate=40,event_date=date(2026,12,6))
    result=apply_extraction(brief,ExtractedAnswer(unknown_fields=['budget'],evidence='not sure'),'not sure')
    assert result.budget is None
    assert 'budget' in result.explicit_unknown
    assert next_question(result).key=='priorities'


def test_extraction_without_user_evidence_is_not_applied():
    from convene.intake import apply_extraction,ExtractedAnswer,BriefAnswers
    from convene.domain import EventBriefVersion
    with pytest.raises(ValueError,match='evidence'):
        apply_extraction(EventBriefVersion(),ExtractedAnswer(answers=BriefAnswers(budget='5000'),
                         evidence='I want to spend 5000'),'not sure')


def test_model_cannot_lower_guest_count_by_ignoring_family():
    from convene.intake import apply_extraction,ExtractedAnswer,BriefAnswers
    from convene.domain import EventBriefVersion
    with pytest.raises(ValueError):
        apply_extraction(EventBriefVersion(),ExtractedAnswer(answers=BriefAnswers(children=30,family=90,
                         guest_estimate=30),evidence='30 children and 90 family'),'30 children and 90 family')


def test_one_turn_is_persisted_and_retry_returns_same_response(repository):
    from convene.intake import IntakeService,ExtractedAnswer,BriefAnswers
    from convene.domain import Principal
    service=IntakeService(repository,extractor=lambda *args:ExtractedAnswer(
        answers=BriefAnswers(occasion='birthday'),evidence='birthday'))
    parent=Principal();opened=service.start(parent)
    event_id=opened['event']['id'];request_id=uuid4()
    first=service.reply(parent,event_id,'birthday',expected_version=1,request_id=request_id)
    second=service.reply(parent,event_id,'birthday',expected_version=1,request_id=request_id)
    assert first==second
    assert first['question']['key']=='services'
    assert len(repository.intake_history(parent,event_id))==3


def test_intake_confirmation_does_not_authorize_anonymous_research(repository):
    from convene.intake import IntakeService
    from convene.domain import Principal,EventBriefVersion
    from convene.policy import authorize_action,PolicyDenied
    parent=Principal()
    brief=EventBriefVersion(occasion='baby shower',services=['food'],guest_estimate=50,
        event_date=date(2026,12,6),budget=2000,priorities='Vegetarian trays',
        dietary_needs='Vegetarian',food_fulfilment='pickup',time_window='afternoon')
    event=repository.create_event(parent,brief)
    response=IntakeService(repository).confirm(parent,event.id,expected_version=1)
    assert response['next_action']=='compare_catalog' and response['save_requires_sign_in']
    with pytest.raises(PolicyDenied):
        authorize_action(parent,repository.get_event(parent,event.id),'research')
