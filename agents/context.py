from pydantic import BaseModel, Field
from typing import List, Optional, Literal


class Location(BaseModel):
    path: str
    start_line: int
    end_line: int

class Locations(BaseModel):
    locations: List[Location] = Field(default_factory=list)
    reasons: List[str] = Field(default_factory=list)

class Action(BaseModel):
    path: str
    operation: Literal["replace", "insert"]
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    symbol: Optional[str] = None
    patch_preview: Optional[str] = None

class Suggestion(BaseModel):
    title: str
    rationale: List[str] = Field(default_factory=list)
    confidence: float = 0.5
    impact_area: Optional[str] = None
    actions: List[Action] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    tests: List[str] = Field(default_factory=list)
    references: List[str] = Field(default_factory=list)

class Suggestions(BaseModel):
    suggestions: List[Suggestion] = Field(default_factory=list)

class Patch(Location):
    operation: Literal["replace", "insert"]
    content: Optional[str] = None


class Riew(BaseModel):
    passed: bool
    reason: Optional[str]
    
class Patches(BaseModel):
    patches: List[Patch]


class Context(BaseModel):
    issue: str = ""
    locations: Locations = Field(default_factory=lambda: Locations(locations=[], reasons=[]))
    suggestions: Suggestions = Field(default_factory=lambda: Suggestions(suggestions=[]))
    states: Patches = Field(default_factory=lambda: Patches(patches=[]))

    def update_patches(self, patches: Patches):
        self.states.patches = patches.patches


    def clear_patches(self):
        self.states.patches = []
        


