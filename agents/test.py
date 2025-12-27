from agents.base import BaseAgent
from tools import tool_registry
from tools.registry import AgentType


class TesterAgent(BaseAgent[str]): 
    def __init__(self):
        tools = tool_registry.get_tools(AgentType.TESTER)
        super().__init__(tools=tools, output_type=str)  

    def get_system_prompt(self) -> str:
        return "assist user"
