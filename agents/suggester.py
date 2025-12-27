from agents.base import BaseAgent
from agents.context import Suggestions
from tools import tool_registry
from tools.registry import AgentType
from prompts.suggester import suggester
from settings import settings
from pathlib import Path
from typing import TypeAlias

Suggester_output: TypeAlias = Suggestions

class SuggesterAgent(BaseAgent[Suggester_output]):
    def __init__(self):
        tools = tool_registry.get_tools(AgentType.SUGGESTER)
        super().__init__(tools=tools, output_type=Suggester_output)

    def get_system_prompt(self) -> str:
        base_dir = Path(settings.TEST_BED) / settings.PROJECT_NAME
        combined_prompt = suggester.format(base_dir=str(base_dir))
        return combined_prompt
