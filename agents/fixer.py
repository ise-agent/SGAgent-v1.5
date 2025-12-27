from agents.base import BaseAgent
from agents.context import Patches
from tools import tool_registry
from tools.registry import AgentType
from prompts.fixer import fixer
from settings import settings
from prompts.common import common
from pathlib import Path
from typing import TypeAlias
from pydantic import BaseModel, Field

Fix_output: TypeAlias = Patches


class END(BaseModel):
    end: bool = Field(default=False)


class FixerAgent(BaseAgent[END]):
    def __init__(self):
        tools = tool_registry.get_tools(AgentType.FIXER)
        print(tools)
        super().__init__(tools=tools, output_type=END)

    def get_system_prompt(self) -> str:
        base_dir = Path(settings.TEST_BED) / settings.PROJECT_NAME
        combined_prompt = fixer.format(base_dir=str(base_dir))
        return combined_prompt
