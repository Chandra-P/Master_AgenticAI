from pydantic import BaseModel, ConfigDict, Field, ValidationError
from typing import Literal

class Item(BaseModel):
    model_config=ConfigDict(extra='allow',strict=True)
class Member(Item):
    name:str; color:str; user_id:str|None=None
class Message(Item):
    id:str; author:str; text:str; time:str; assistant:bool=False; user_id:str|None=None
class Preference(Item):
    label:str; confirmed:bool
class Poll(Item):
    id:str; question:str; options:list[str]; votes:dict[str,int]; datePoll:bool=False
class Activity(Item):
    id:str; title:str; time:str; category:str; location:str
class Task(Item):
    label:str; done:bool
class Snapshot(Item):
    id:str; title:str=Field(min_length=1,max_length=200); kind:Literal['outing','trip']; location:str; date:str; start:str; end:str; budget:float=Field(ge=0,allow_inf_nan=False); image:str
    members:list[Member]; messages:list[Message]; preferences:list[Preference]; polls:list[Poll]; itinerary:list[Activity]; tasks:list[Task]
    revision:int; owner_id:str; role:Literal['owner','member']

def validate_snapshot(value):
    Snapshot.model_validate(value)
