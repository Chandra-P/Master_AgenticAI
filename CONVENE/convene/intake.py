"""One-question intake. Extraction proposes facts; confirmation grants no tool access."""
from datetime import date
from decimal import Decimal
import re
from typing import Literal

from pydantic import Field

from convene.domain import EventBriefVersion, Record


class Question(Record):
    key: str
    text: str


class BriefAnswers(Record):
    occasion: str | None = None
    services: list[Literal['venue', 'decoration', 'food']] | None = None
    event_date: date | None = None
    date_flexibility: str | None = None
    time_window: str | None = None
    children: int | None = None
    family: int | None = None
    guest_estimate: int | None = None
    budget: Decimal | None = None
    age: int | None = None
    interests: str | None = None
    theme: str | None = None
    priorities: str | None = None
    dietary_needs: str | None = None
    food_fulfilment: Literal['pickup', 'delivery', 'either'] | None = None


class FieldEvidence(Record):
    field:Literal['occasion','services','event_date','date_flexibility','time_window','children','family',
        'guest_estimate','budget','age','interests','theme','priorities','dietary_needs','food_fulfilment']
    quote:str=Field(min_length=1,max_length=1000)


class GroundedQuote(Record):
    source_id:str
    quote:str=Field(min_length=1,max_length=600)


class ExtractedAnswer(Record):
    intent: Literal['answer','small_talk','help','unclear'] = 'answer'
    reply: str = Field(default='',max_length=700)
    source_ids: list[str] = Field(default_factory=list,max_length=6)
    grounded_quotes:list[GroundedQuote]=Field(default_factory=list,max_length=2)
    field_evidence:list[FieldEvidence]=Field(default_factory=list,max_length=20)
    answers: BriefAnswers = Field(default_factory=BriefAnswers)
    tentative_fields: list[str] = Field(default_factory=list)
    unknown_fields: list[str] = Field(default_factory=list)
    evidence: str = ''


def next_question(brief: EventBriefVersion):
    def missing(key):
        return getattr(brief, key) is None and key not in brief.explicit_unknown

    questions = []
    if not brief.occasion:
        return Question(key='occasion', text="Welcome to CONVENE! I'd love to help you plan something special in San Antonio. What are you celebrating?")
    if not brief.services:
        return Question(key='services', text='Which parts would you like help with: venue, professional decorations, food, or all three?')
    if 'birthday' in brief.occasion.lower() and missing('age'):
        questions.append(('age', 'How old will the birthday person be?'))
    if brief.children is not None and missing('family'):
        questions.append(('family', 'How many parents and other family members will join the children?'))
    elif brief.total_guests is None:
        questions.append(('guest_estimate', 'How many guests should we plan for, including children and accompanying adults?'))
    if missing('event_date') and not brief.date_flexibility:
        questions.append(('event_date', 'When would you like to celebrate?'))
    if missing('budget'):
        questions.append(('budget', 'What total budget would you feel comfortable spending on the parts we are planning?'))
    if missing('priorities'):
        questions.append(('priorities', 'What matters most if we need to balance your guest count, budget, and preferences?'))
    if missing('time_window'):
        questions.append(('time_window', 'What time of day would you prefer?'))
    if 'decoration' in brief.services and missing('theme'):
        questions.append(('theme', 'Do you have a theme or decoration style in mind?'))
    if 'food' in brief.services:
        if missing('dietary_needs'):
            questions.append(('dietary_needs', 'What food preferences, allergies, or dietary needs should we keep in mind?'))
        if missing('food_fulfilment'):
            questions.append(('food_fulfilment', 'Would you prefer restaurant tray pickup, delivery, or either?'))
    return Question(key=questions[0][0], text=questions[0][1]) if questions else None


def apply_extraction(brief, extraction, message):
    patch = extraction.answers.model_dump(mode='json', exclude_none=True)
    current=brief.model_dump(mode='json')
    # Structured models may echo old facts. They are not new parent answers.
    supports={item.field:item.quote for item in extraction.field_evidence}
    def reaffirms(key):
        quote=supports.get(key) or (extraction.evidence if not supports else '')
        return (key in brief.tentative_fields and key not in extraction.tentative_fields
                and bool(quote) and quote in message)
    patch={key:value for key,value in patch.items() if value!=current[key] or reaffirms(key)}
    if (brief.children is not None and brief.family is not None
            and not {'children','family'} & patch.keys()
            and patch.get('guest_estimate')==brief.total_guests):
        patch.pop('guest_estimate')
    changed = bool(patch or extraction.unknown_fields or extraction.tentative_fields)
    if changed:
        if extraction.field_evidence:
            supports={item.field:item.quote for item in extraction.field_evidence}
            fields=set(patch)|set(extraction.unknown_fields)|set(extraction.tentative_fields)
            if any(not supports.get(key) or supports[key] not in message for key in fields):
                raise ValueError('Each extracted field requires evidence from the current parent message.')
        elif not extraction.evidence or extraction.evidence not in message:
            raise ValueError('Extracted facts require evidence from the current parent message.')
    allowed = set(BriefAnswers.model_fields)
    if not set(extraction.unknown_fields + extraction.tentative_fields) <= allowed:
        raise ValueError('Unknown extraction field.')
    if set(patch) & set(extraction.unknown_fields):
        raise ValueError('An answer cannot be known and unknown at the same time.')
    unknown = (brief.explicit_unknown - set(patch)) | set(extraction.unknown_fields)
    tentative = (brief.tentative_fields - set(patch)) | set(extraction.tentative_fields)
    for key in extraction.unknown_fields:
        if key == 'services':
            raise ValueError('Choose planning services before confirming.')
        patch[key] = None
    body = brief.model_dump(mode='json')
    body.update(patch, explicit_unknown=sorted(unknown), tentative_fields=sorted(tentative))
    return EventBriefVersion.model_validate(body)


def _response(event):
    question = next_question(event.brief)
    return {'event': event.model_dump(mode='json'),
            'question': question.model_dump() if question else None,
            'assistant_message':question.text if question else 'Here is your brief. Please review and confirm it before I research options.',
            'next_action': 'answer' if question else 'review_brief'}


class IntakeService:
    def __init__(self, repository, extractor=None):
        self.repository = repository
        self.extractor = extractor

    def start(self, actor):
        event = self.repository.create_event(actor)
        response = _response(event)
        self.repository.record_intake_greeting(actor, event.id, response['question']['text'])
        return response

    def reply(self, actor, event_id, message, *, expected_version, request_id):
        from convene.repository import Conflict
        if not isinstance(message, str) or not message.strip() or len(message) > 4000:
            raise ValueError('Please send a message between 1 and 4000 characters.')
        receipt = self.repository.get_intake_receipt(actor, event_id, request_id)
        if receipt is not None:
            return receipt
        event = self.repository.get_event(actor, event_id)
        if event.brief.version != expected_version:
            raise Conflict('Stale brief version; reload before replying.')
        history = self.repository.intake_history(actor, event_id)
        if len(history) >= 81:
            raise ValueError('Conversation limit reached; review or start a new brief.')
        def converse(prefix,sources=None):
            response=_response(event)
            question=response['question']
            text=prefix+' '+(question['text'] if question and question['key']!='occasion'
                            else 'What are you celebrating?' if question
                            else 'Which approved option would you like to explore?' if event.confirmed_version==event.brief.version
                            else 'Your brief is ready to review. You can confirm it or tell me what to change.')
            if question:response['question']={**question,'text':text}
            response['assistant_message']=text
            response['sources']=sources or []
            return self.repository.commit_intake(actor,event_id,message,None,response,
                expected_version=expected_version,request_id=request_id)
        if re.fullmatch(r'(?:hi|hello|hey)(?: there)?[\s!.]*',message.strip(),flags=re.IGNORECASE):
            return converse("Hi! I'm glad you're here.")
        if self.extractor is None:
            raise RuntimeError('An intake extraction provider must be configured.')
        context=[]
        from convene.catalog_planner import CatalogPlanner
        from convene.vendor_directory import DirectoryRepository
        directory_reader=DirectoryRepository(self.repository.dsn)
        published=directory_reader.list_approved()
        approved={v['id']:v for v in published['vendors']+published['food']}
        def provider_current(source,current):
            vendor=current.get(source.get('vendor_id'))
            return bool(vendor and vendor['directory_version']==source.get('vendor_version')
                        and vendor['approval']['approval_id']==source.get('approval_id'))
        vendor_context=CatalogPlanner(self.repository).context(actor,event_id,message)
        current_vendor_sources={item['id'] for item in vendor_context}
        safe_history=[]
        for turn in history[-12:]:
            catalog_sources=[source for source in turn.get('sources',[]) if source.get('kind')=='approved_vendor']
            if any(source.get('id') not in current_vendor_sources or source.get('brief_version')!=event.brief.version for source in catalog_sources):
                continue
            private=[source for source in turn.get('sources',[]) if source.get('kind')=='event_evidence']
            if private and (not actor.authenticated or event.confirmed_version!=event.brief.version
                            or any(source.get('brief_version')!=event.brief.version or not provider_current(source,approved) for source in private)):
                continue
            safe_history.append({'role':turn['role'],'body':turn['body']})
        if hasattr(self.extractor,'respond_with_context'):
            from convene.evidence_retrieval import EvidenceIndex
            recent_questions=' '.join(turn['body'] for turn in history[-4:] if turn['role']=='user')
            context=EvidenceIndex(self.repository).retrieve(actor,event_id,message+' '+recent_questions)
            context=[source for source in context if source['kind']=='planning' or provider_current(source,approved)]
            context=vendor_context+context
            extracted=ExtractedAnswer.model_validate(self.extractor.respond_with_context(
                message,event.brief,safe_history,context))
        else:
            extracted=ExtractedAnswer.model_validate(self.extractor(message,event.brief,safe_history))
        selected={item['id']:item for item in context}
        def known_source(key):
            return [item for item in context if item['id']==key or item['source_id']==key]
        quotes=[]
        for quote in extracted.grounded_quotes:
            matches=[item for item in known_source(quote.source_id) if quote.quote in item['content']]
            quotes.append(quote.model_copy(update={'source_id':matches[0]['id']}) if len(matches)==1 else quote)
        valid_reply=bool(quotes) and all(
            q.source_id in selected and q.quote in selected[q.source_id]['content'] and '?' not in q.quote for q in quotes)
        if any(not known_source(key) for key in extracted.source_ids):valid_reply=False
        citations=[selected[key] for key in dict.fromkeys(q.source_id for q in quotes)] if valid_reply else []
        fresh=directory_reader.list_approved()
        fresh_approved={v['id']:v for v in fresh['vendors']+fresh['food']}
        if any(s['kind'] in ('event_evidence','approved_vendor') and not provider_current(s,fresh_approved) for s in citations):
            valid_reply=False;citations=[]
        prefix=None
        if valid_reply:
            label='From the CONVENE planning guide' if all(s['kind']=='planning' for s in citations) else 'From recorded source evidence'
            prefix=label+': '+ ' '.join('“'+q.quote+'”' for q in quotes)
        if extracted.intent!='answer':
            prefixes={'small_talk':"I'm here and ready to help you plan something special!",
                      'help':'I can help you plan venues, professional decorations, and restaurant party trays in San Antonio.',
                      'unclear':"Let's take it one step at a time."}
            return converse(prefix or prefixes[extracted.intent],citations if valid_reply else [])
        discarded=False
        if hasattr(self.extractor,'respond_with_context'):
            supported={item.field for item in extracted.field_evidence if item.quote in message}
            values=extracted.answers.model_dump(mode='json',exclude_none=True)
            current=event.brief.model_dump(mode='json')
            discarded=any(key not in supported and value!=current[key] for key,value in values.items())
            discarded=discarded or bool(set(extracted.unknown_fields+extracted.tentative_fields)-supported)
            extracted=extracted.model_copy(update={
                'answers':BriefAnswers.model_validate({key:value for key,value in values.items() if key in supported}),
                'unknown_fields':[key for key in extracted.unknown_fields if key in supported],
                'tentative_fields':[key for key in extracted.tentative_fields if key in supported]})
        try:
            if hasattr(self.extractor,'respond_with_context'):
                changes=(extracted.answers.model_dump(exclude_none=True) or extracted.unknown_fields or extracted.tentative_fields)
                if changes and not extracted.field_evidence:
                    raise ValueError('Current-message evidence required for each field.')
            brief = apply_extraction(event.brief, extracted, message)
        except ValueError:
            # Reject unsupported facts, but keep a normal misunderstanding in the conversation.
            return converse('I may have misunderstood that. Your event details are unchanged.')
        if brief==event.brief:
            if discarded:return converse('I may have misunderstood part of that. Your event details are unchanged.')
            return converse(prefix or "Let's take it one step at a time.",citations if valid_reply else [])
        patch = brief.model_dump(mode='json', exclude={'version'})
        changed = event.revise(patch, expected_version)
        response = _response(changed)
        if discarded and not prefix:
            response['assistant_message']='I saved the details supported by your latest message. '+response['assistant_message']
            if response['question']:response['question']={**response['question'],'text':response['assistant_message']}
        if any(source['kind'] in ('event_evidence','approved_vendor') for source in citations):
            # A correction invalidates old provider evidence for outgoing responses too.
            prefix=None
            citations=[]
        if prefix:
            response['assistant_message']=prefix+' '+response['assistant_message']
            if response['question']:
                response['question']={**response['question'],'text':response['assistant_message']}
            response['sources']=citations
        return self.repository.commit_intake(actor, event_id, message, patch, response,
            expected_version=expected_version, request_id=request_id)

    def confirm(self, actor, event_id, *, expected_version):
        event = self.repository.get_event(actor, event_id)
        if next_question(event.brief) is not None:
            raise ValueError('Review the remaining planning questions before confirming.')
        event = self.repository.confirm_event(actor, event_id, expected_version=expected_version)
        return {'event': event.model_dump(mode='json'),
                'next_action':'compare_catalog','save_requires_sign_in':not actor.authenticated}
