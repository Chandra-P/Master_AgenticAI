"""Private event records. Constructed by services, never trusted as authorization."""
from datetime import date as Date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID, uuid4

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator, model_validator


class Record(BaseModel):
    model_config=ConfigDict(extra='forbid',frozen=True,str_strip_whitespace=True,allow_inf_nan=False)


class Principal(Record):
    id:UUID=Field(default_factory=uuid4)
    authenticated:bool=False


class EventBriefVersion(Record):
    version:int=Field(default=1,ge=1)
    occasion:str|None=Field(default=None,min_length=1,max_length=200)
    city:Literal['San Antonio, Texas']='San Antonio, Texas'
    services:list[Literal['venue','decoration','food']]=Field(default_factory=list,max_length=3)
    event_date:Date|None=None
    date_flexibility:str|None=Field(default=None,max_length=300)
    time_window:str|None=Field(default=None,max_length=200)
    children:int|None=Field(default=None,ge=0,le=10000)
    family:int|None=Field(default=None,ge=0,le=10000)
    guest_estimate:int|None=Field(default=None,ge=1,le=20000)
    budget:Decimal|None=Field(default=None,gt=0,le=1000000,max_digits=10,decimal_places=2)
    age:int|None=Field(default=None,ge=0,le=120)
    interests:str|None=Field(default=None,max_length=1000)
    theme:str|None=Field(default=None,max_length=300)
    priorities:str|None=Field(default=None,max_length=1000)
    dietary_needs:str|None=Field(default=None,max_length=1000)
    food_fulfilment:Literal['pickup','delivery','either']|None=None
    tentative_fields:set[str]=Field(default_factory=set)
    explicit_unknown:set[str]=Field(default_factory=set)

    @model_validator(mode='after')
    def consistent(self):
        if len(self.services)!=len(set(self.services)):
            raise ValueError('Services must be unique.')
        if self.children is not None and self.family is not None:
            total=self.children+self.family
            if total<1 or (self.guest_estimate is not None and self.guest_estimate!=total):
                raise ValueError('Guest estimate must include children and accompanying family.')
        allowed=set(type(self).model_fields)-{'version','tentative_fields','explicit_unknown'}
        if not (self.tentative_fields|self.explicit_unknown)<=allowed:
            raise ValueError('Unknown brief field status.')
        return self

    @property
    def total_guests(self):
        if self.children is not None and self.family is not None:
            return self.children+self.family
        return self.guest_estimate

    def confirmation_gaps(self):
        gaps=[]
        if not self.occasion:gaps.append('occasion')
        if not self.services:gaps.append('services')
        if self.total_guests is None:gaps.append('guests')
        if self.event_date is None and not self.date_flexibility and 'event_date' not in self.explicit_unknown:
            gaps.append('event_date')
        if self.budget is None and 'budget' not in self.explicit_unknown:gaps.append('budget')
        return gaps


class EventRecord(Record):
    id:UUID=Field(default_factory=uuid4)
    owner_id:UUID
    brief:EventBriefVersion=Field(default_factory=EventBriefVersion)
    confirmed_version:int|None=None
    status:Literal['planning','archived']='planning'

    def confirm(self,expected_version:int):
        if expected_version!=self.brief.version:raise ValueError('Stale brief version.')
        if self.brief.confirmation_gaps():raise ValueError('Incomplete brief: '+', '.join(self.brief.confirmation_gaps()))
        return self.model_copy(update={'confirmed_version':expected_version})

    def revise(self,patch:dict,expected_version:int):
        if expected_version!=self.brief.version:raise ValueError('Stale brief version.')
        if 'version' in patch:raise ValueError('Version is controlled by the server.')
        body=self.brief.model_dump(mode='json')
        body.update(patch)
        body['version']=expected_version+1
        brief=EventBriefVersion.model_validate(body)
        return self.model_copy(update={'brief':brief,'confirmed_version':None})


class EvidenceFact(Record):
    id:UUID=Field(default_factory=uuid4)
    event_id:UUID
    provider_id:str=Field(min_length=1,max_length=200)
    brief_version:int=Field(ge=1)
    field:str=Field(min_length=1,max_length=100)
    value:str=Field(min_length=1,max_length=4000)
    excerpt:str=Field(min_length=1,max_length=8000)
    source_kind:Literal['public_page','provider_email','upload','parent_statement']
    source_id:str=Field(min_length=1,max_length=2000)
    retrieved_at:AwareDatetime


class ProviderOption(Record):
    id:UUID=Field(default_factory=uuid4)
    event_id:UUID
    kind:Literal['venue','decoration','food']
    name:str=Field(min_length=1,max_length=300)
    price:Decimal|None=Field(default=None,ge=0)
    price_basis:Literal['unknown','published_base','published_minimum','provider_quote']='unknown'
    evidence_ids:list[UUID]=Field(default_factory=list)


class AttachmentRef(Record):
    id:UUID
    sha256:str=Field(pattern=r'^[a-f0-9]{64}$')


class InquiryPayload(Record):
    to:list[str]=Field(min_length=1,max_length=5)
    subject:str=Field(min_length=1,max_length=200)
    body:str=Field(min_length=1,max_length=20000)
    attachments:list[AttachmentRef]=Field(default_factory=list,max_length=10)

    @field_validator('to')
    @classmethod
    def safe_recipients(cls,recipients):
        import re
        if any(not re.fullmatch(r'[^\s<>@,;]+@[^\s<>@,;]+\.[^\s<>@,;]+',value) for value in recipients):
            raise ValueError('Use explicit email addresses without display names or control characters.')
        return recipients

    @field_validator('subject')
    @classmethod
    def no_header_injection(cls,subject):
        if '\n' in subject or '\r' in subject:raise ValueError('Subject must be one line.')
        return subject


Capability=Literal['send_inquiry','factual_reply','followup','reconfirmation']


class Approval(Record):
    id:UUID=Field(default_factory=uuid4)
    actor_id:UUID
    event_id:UUID
    inquiry_id:UUID
    provider_id:str=Field(min_length=1,max_length=200)
    mailbox_id:UUID
    brief_version:int=Field(ge=1)
    capability:Capability
    payload_digest:str|None=Field(default=None,pattern=r'^[a-f0-9]{64}$')
    expires_at:AwareDatetime
    revoked_at:AwareDatetime|None=None


class Inquiry(Record):
    id:UUID=Field(default_factory=uuid4)
    event_id:UUID
    provider_id:str
    mailbox_id:UUID
    brief_version:int=Field(ge=1)
    draft:InquiryPayload
    state:Literal['draft','approved','queued','sending','sent','uncertain','replied','cancelled']='draft'
    followups_sent:int=Field(default=0,ge=0,le=3)
    gmail_thread_id:str|None=None


class BookingRecord(Record):
    id:UUID=Field(default_factory=uuid4)
    event_id:UUID
    provider_id:str
    reservation:Literal['unconfirmed','held','confirmed','cancelled']='unconfirmed'
    payment:Literal['unknown','pending','paid','balance_due','not_required']='unknown'
    contract:Literal['unknown','pending','signed','not_required']='unknown'
    evidence_ids:list[UUID]=Field(default_factory=list)
    required_conditions_met:bool=False

    @model_validator(mode='after')
    def no_confirmation_without_evidence(self):
        if self.reservation=='confirmed' and (not self.evidence_ids or not self.required_conditions_met):
            raise ValueError('Confirmation requires provider evidence and satisfied securing conditions.')
        return self


class Job(Record):
    id:UUID=Field(default_factory=uuid4)
    owner_id:UUID
    event_id:UUID
    brief_version:int=Field(ge=1)
    kind:Literal['followup','reconfirmation','mail_sync','notification']
    due_at:AwareDatetime
    dedupe_key:str=Field(min_length=1,max_length=300)
    status:Literal['queued','running','done','failed','cancelled']='queued'
