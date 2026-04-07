from pydantic import BaseModel
from typing import Optional

class Observation(BaseModel):
    ticket_text: str
    user_history: Optional[str]
    current_step: int

class Action(BaseModel):
    category: Optional[str]
    priority: Optional[str]
    team: Optional[str]
    response: Optional[str]

class Reward(BaseModel):
    score: float
