from pydantic import BaseModel
from typing import Optional

class Observation(BaseModel):
    ticket_text: str
    user_history: Optional[str]
    current_step: int

class Action(BaseModel):
    category: str
    priority: str
    team: str
    response: str

class Reward(BaseModel):
    score: float
