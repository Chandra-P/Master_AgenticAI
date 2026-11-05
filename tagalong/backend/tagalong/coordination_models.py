from typing import Literal
from pydantic import BaseModel,ConfigDict,Field,field_validator,model_validator
from .models import DateFields,iso_date


class Structured(BaseModel):
    model_config=ConfigDict(extra='forbid')


class DraftActivity(Structured):
    title:str=Field(min_length=1,max_length=200)
    time:str=Field(max_length=100)
    category:str=Field(max_length=100)
    location:str=Field(max_length=500)


class SuggestedBudget(Structured):
    amount:float|None=Field(ge=0,le=1000000,allow_inf_nan=False)
    basis:Literal['per_person','total','unknown']
    currency:str=Field(max_length=10)
    notes:str=Field(max_length=500)


class PlanDraft(Structured):
    title:str=Field(min_length=1,max_length=200)
    type:Literal['outing','trip']
    location:str=Field(max_length=150)
    start:str|None
    end:str|None
    participant_count:int|None=Field(ge=1,le=100)
    suggested_tasks:list[str]=Field(max_length=12)
    suggested_itinerary:list[DraftActivity]=Field(max_length=12)
    suggested_budget:SuggestedBudget
    open_questions:list[str]=Field(max_length=10)

    @field_validator('start','end')
    @classmethod
    def valid_dates(cls,value):return iso_date(value) if value is not None else None
    @field_validator('suggested_tasks','open_questions')
    @classmethod
    def bounded_strings(cls,values):
        if any(not x.strip() or len(x)>300 for x in values):raise ValueError('Invalid item')
        return list(dict.fromkeys(x.strip() for x in values))
    @model_validator(mode='after')
    def ordered_dates(self):
        if self.start and self.end and self.end<self.start:raise ValueError('End before start')
        return self


class SummaryOutput(Structured):
    summary:str=Field(min_length=1,max_length=3000)
    decisions_made:list[str]=Field(max_length=30)
    open_questions:list[str]=Field(max_length=12)
    @field_validator('decisions_made','open_questions')
    @classmethod
    def bounded(cls,values):
        if any(not x.strip() or len(x)>500 for x in values):raise ValueError('Invalid summary item')
        return list(dict.fromkeys(x.strip() for x in values))


class ActivityIdea(Structured):
    title:str=Field(min_length=1,max_length=150)
    reason:str=Field(min_length=1,max_length=300)
    preference_labels:list[str]=Field(min_length=1,max_length=6)


class RecommendationOutput(Structured):
    next_step:str=Field(min_length=1,max_length=300)
    reason:str=Field(min_length=1,max_length=700)
    activity_ideas:list[ActivityIdea]=Field(default_factory=list,max_length=4)


class Generate(Structured):
    prompt:str=Field(min_length=5,max_length=2000)
    local_date:str
    @field_validator('prompt',mode='before')
    @classmethod
    def trim(cls,value):return value.strip() if isinstance(value,str) else value
    @field_validator('local_date')
    @classmethod
    def valid(cls,value):return iso_date(value)


class AcceptDraft(DateFields):
    draft_id:str=Field(min_length=1,max_length=100)
    title:str=Field(min_length=1,max_length=200)
    kind:Literal['outing','trip']
    location:str=Field(min_length=1,max_length=150)
    budget_per_person:float|None=Field(default=None,ge=0,le=1000000,allow_inf_nan=False)
    @field_validator('title','location',mode='before')
    @classmethod
    def trim(cls,value):return value.strip() if isinstance(value,str) else value
