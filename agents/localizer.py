from agents.base import BaseAgent
from agents.context import Patches
from tools import tool_registry
from tools.registry import AgentType
from prompts.localizer import localizer
from settings import settings
from pathlib import Path
from typing import TypeAlias
from agents.context import Locations


Localize_output: TypeAlias = Locations


class LocalizerAgent(BaseAgent[Localize_output]):
    def __init__(self):
        tools = tool_registry.get_tools(AgentType.LOCALIZER)
        print(tools)
        super().__init__(tools=tools, output_type=Localize_output)

    def get_system_prompt(self) -> str:
        base_dir = Path(settings.TEST_BED) / settings.PROJECT_NAME
        combined_prompt = localizer.format(base_dir=str(base_dir))
        return combined_prompt
