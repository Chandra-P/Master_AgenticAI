from datetime import date
from pydantic import BaseModel, Field, ConfigDict

class EventBrief(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, allow_inf_nan=False)
    title: str = Field(min_length=1, max_length=200)
    city: str = Field(min_length=1, max_length=100)
    guests: int = Field(gt=0, le=10000)
    budget: float = Field(gt=0, le=100000000)
    event_date: date
    duration_hours: int = Field(ge=1, le=12, default=4)
    preferences: str = Field(default='', max_length=2000)
