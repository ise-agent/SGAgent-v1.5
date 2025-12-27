from pydantic import BaseModel
from typing import Literal


class SubAgentType(BaseModel):
    target_agent: Literal["localizer", "fixer", "publisher"]
    reason: str
    instruction: str
    

