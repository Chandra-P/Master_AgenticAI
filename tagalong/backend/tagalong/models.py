"""Strict bounded HTTP snapshots; mutable plan data is validated before transactions."""
from datetime import date
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

MAX_MESSAGES = 1000
MAX_PREFERENCES = 200
MAX_MEMBERS = 100


def iso_date(value: str) -> str:
    parsed = date.fromisoformat(value)
    if parsed.isoformat() != value:
        raise ValueError('Use ISO YYYY-MM-DD dates')
    return value


class Item(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)


class DateFields(Item):
    start: str
    end: str

    @field_validator('start', 'end')
    @classmethod
    def valid_date(cls, value):
        return iso_date(value)

    @model_validator(mode='after')
    def date_order(self):
        if self.end < self.start:
            raise ValueError('End date must not precede start date')
        return self


class Create(DateFields):
    kind: Literal['outing', 'trip']
    title: str = Field(min_length=1, max_length=200)
    participants: str = Field(default='', max_length=2000)

    @field_validator('title', mode='before')
    @classmethod
    def trimmed_title(cls, value):
        return value.strip() if isinstance(value, str) else value


class Member(Item):
    name: str = Field(min_length=1, max_length=100)
    color: str = Field(max_length=30)
    user_id: str | None = None


class Citation(Item):
    id: str = Field(min_length=1, max_length=100)
    title: str = Field(max_length=200)
    text: str = Field(max_length=6000)


class Message(Item):
    id: str = Field(min_length=1, max_length=100)
    author: str = Field(min_length=1, max_length=100)
    text: str = Field(min_length=1, max_length=20000)
    time: str = Field(max_length=100)
    sources: list[Citation] = Field(default_factory=list, max_length=6)
    assistant: bool = False
    user_id: str | None = None


class Preference(Item):
    label: str = Field(min_length=1, max_length=200)
    confirmed: bool


class Poll(Item):
    id: str = Field(min_length=1, max_length=100)
    question: str = Field(min_length=1, max_length=500)
    options: list[str] = Field(min_length=2, max_length=20)
    votes: dict[str, int] = Field(max_length=MAX_MEMBERS)
    datePoll: bool = False

    @field_validator('options')
    @classmethod
    def valid_options(cls, values):
        normalized = [v.strip().casefold() for v in values]
        if any(not v or len(v) > 200 for v in normalized) or len(set(normalized)) != len(values):
            raise ValueError('Options must be distinct nonempty strings')
        return values


class Activity(Item):
    id: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=200)
    time: str = Field(max_length=100)
    category: str = Field(max_length=100)
    location: str = Field(max_length=500)


    image: str | None = Field(default=None, max_length=2048)


class Task(Item):
    label: str = Field(min_length=1, max_length=500)
    done: bool


class Snapshot(DateFields):
    id: str
    title: str = Field(min_length=1, max_length=200)
    kind: Literal['outing', 'trip']
    location: str = Field(max_length=500)
    date: str = Field(max_length=100)
    budget: float = Field(ge=0, le=1000000000, allow_inf_nan=False)
    image: str = Field(min_length=1, max_length=2048)
    members: list[Member] = Field(min_length=1, max_length=MAX_MEMBERS)
    messages: list[Message] = Field(max_length=MAX_MESSAGES)
    preferences: list[Preference] = Field(max_length=MAX_PREFERENCES)
    polls: list[Poll] = Field(max_length=100)
    itinerary: list[Activity] = Field(max_length=200)
    tasks: list[Task] = Field(max_length=200)
    revision: int
    owner_id: str
    role: Literal['owner', 'member']

    @field_validator('title', mode='before')
    @classmethod
    def trimmed_title(cls, value):
        return value.strip() if isinstance(value, str) else value


class AssistantOutput(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    text: str = Field(min_length=1, max_length=12000)
    preferences: list[str] = Field(max_length=10)
    source_ids: list[str] = Field(max_length=6)

    @field_validator('text')
    @classmethod
    def nonempty_text(cls, value):
        if not value.strip():
            raise ValueError('Empty assistant response')
        return value

    @field_validator('preferences')
    @classmethod
    def bounded_preferences(cls, values):
        if any(not v.strip() or len(v) > 200 for v in values):
            raise ValueError('Invalid preference label')
        return list(dict.fromkeys(v.strip() for v in values))


def validate_snapshot(value):
    parsed = Snapshot.model_validate(value)
    value['title'] = parsed.title

