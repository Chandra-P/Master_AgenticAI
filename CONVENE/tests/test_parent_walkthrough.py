from datetime import date
from uuid import uuid4

from convene.domain import EventBriefVersion, Principal
from convene.intake import ExtractedAnswer, IntakeService


def ready_brief(**changes):
    values = dict(occasion='birthday', age=8, services=['venue', 'decoration'],
                  children=20, family=20, event_date=date(2026, 12, 6),
                  theme='dinosaur', priorities='Keep everyone invited', time_window='Afternoon')
    values.update(changes)
    return EventBriefVersion(**values)


def test_budget_uncertainty_with_help_question_advances_without_guessing(repository):
    actor = Principal()
    event = repository.create_event(actor, ready_brief(priorities=None))
    class Model:
        def respond_with_context(self, *args):
            return ExtractedAnswer(intent='help', unknown_fields=['budget'],
                field_evidence=[{'field': 'budget', 'quote': "I'm not sure about budget"}])
    response = IntakeService(repository, Model()).reply(actor, event.id,
        "I'm not sure about budget. What would venue and decorations normally cost?",
        expected_version=1, request_id=uuid4())
    assert response['event']['brief']['budget'] is None
    assert 'budget' in response['event']['brief']['explicit_unknown']
    assert response['question']['key'] == 'priorities'
    assert 'undecided' in response['assistant_message'].lower()
    assert 'quote' in response['assistant_message'].lower()


def test_supported_facts_survive_mixed_help_intent_without_reasking(repository):
    actor = Principal()
    event = repository.create_event(actor, ready_brief(budget=800, priorities=None, time_window=None))
    message = 'Keep everyone invited. Afternoon is best. Can you help?'
    class Model:
        def respond_with_context(self, *args):
            return ExtractedAnswer(intent='help', answers={
                'priorities': 'Keep everyone invited', 'time_window': 'Afternoon'},
                field_evidence=[{'field': 'priorities', 'quote': 'Keep everyone invited'},
                                {'field': 'time_window', 'quote': 'Afternoon is best'}])
    response = IntakeService(repository, Model()).reply(actor, event.id, message,
        expected_version=1, request_id=uuid4())
    assert response['question'] is None
    assert response['event']['brief']['priorities'] == 'Keep everyone invited'
    assert response['event']['brief']['time_window'] == 'Afternoon'


def test_simple_event_answer_does_not_quote_procedural_guidance(repository):
    actor = Principal()
    event = repository.create_event(actor, ready_brief(budget=800, time_window=None))
    class Model:
        def respond_with_context(self, message, brief, history, context):
            source = next(c for c in context if c['kind'] == 'planning')
            quote = next(s.strip() + '.' for s in source['content'].split('.') if s.strip() and '?' not in s)
            return ExtractedAnswer(answers={'time_window':'Afternoon'},
                field_evidence=[{'field':'time_window','quote':'Afternoon'}],
                grounded_quotes=[{'source_id':source['id'],'quote':quote}])
    response = IntakeService(repository, Model()).reply(actor, event.id, 'Afternoon for our birthday venue and decorations',
        expected_version=1, request_id=uuid4())
    assert response['question'] is None
    assert not response.get('sources')
    assert 'planning guide' not in response['assistant_message']


def test_tentative_preferences_are_preserved_in_inquiry_preview(repository, monkeypatch):
    from convene.catalog_planner import CatalogPlanner
    actor = Principal()
    event = repository.create_event(actor, ready_brief(budget=800,
        date_flexibility='The following weekend also works',
        tentative_fields={'event_date', 'date_flexibility', 'time_window', 'family'}))
    repository.confirm_event(actor, event.id, expected_version=1)
    planner = CatalogPlanner(repository)
    monkeypatch.setattr(planner, 'shortlist', lambda *a, **kw: {'selected':[
        {'id':'room', 'name':'Test room', 'directory_version':1}], 'stale':[]})
    draft = planner.drafts(actor, event.id, expected_version=1)['drafts'][0]
    assert '2026-12-06 (tentative)' in draft['body']
    assert 'The following weekend also works (tentative)' in draft['body']
    assert 'Afternoon (tentative)' in draft['body']
    assert '40 guests (tentative)' in draft['body']
    assert '20 children' in draft['body'] and '20 accompanying adults' in draft['body']
    assert '8' in draft['body'] and 'Keep everyone invited' in draft['body']
    assert not draft['sendable']


def test_booking_status_question_receives_direct_answer_and_keeps_brief(repository):
    actor = Principal()
    event = repository.create_event(actor, ready_brief(budget=800))
    service = IntakeService(repository, lambda *args: ExtractedAnswer(intent='unclear'))
    response = service.reply(actor, event.id,
        'Have you booked any venue or sent an email for me yet?',
        expected_version=1, request_id=uuid4())
    text = response['assistant_message'].lower()
    assert 'not booked' in text and 'not sent' in text
    assert 'draft' in text
    assert response['event'] == event.model_dump(mode='json')


def test_new_total_discards_old_breakdown_without_inventing_adult_count():
    from convene.intake import apply_extraction, next_question
    changed = apply_extraction(ready_brief(budget=800, tentative_fields={'family'}),
        ExtractedAnswer(answers={'guest_estimate':220},
                        field_evidence=[{'field':'guest_estimate','quote':'220 guests in total'}]),
        'Plan for 220 guests in total')
    assert changed.total_guests == 220
    assert changed.children is None and changed.family is None
    assert not {'children','family'} & changed.tentative_fields
    assert next_question(changed) is None


def test_correcting_one_breakdown_count_recomputes_previously_saved_total():
    from convene.intake import apply_extraction
    changed = apply_extraction(ready_brief(budget=800, guest_estimate=40),
        ExtractedAnswer(answers={'family':30},
                        field_evidence=[{'field':'family','quote':'30 adults'}]),
        'Actually 30 adults')
    assert changed.total_guests == 50
