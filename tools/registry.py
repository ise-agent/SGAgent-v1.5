from typing import Dict, List, Callable, Optional
from enum import Enum

#TODO @hanyu transfer to models dir
class AgentType(Enum):
    LOCALIZER = "localizer"
    SUGGESTER = "suggester"
    FIXER = "fixer"
    REVIEWER = "reviewer"
    PUBLISHER = "publisher"
    COORDINATOR = "coordinator"
    TESTER ="tester"


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._tool_agents: Dict[str, List[AgentType]] = {}

    def register(self, name: str = None, agents: List[AgentType] | None = None):
        def decorator(func):
            tool_name = name or func.__name__
            self._tools[tool_name] = func
            self._tool_agents[tool_name] = agents or [
                AgentType.LOCALIZER,
                AgentType.SUGGESTER,
                AgentType.FIXER,
                AgentType.REVIEWER,
            ]
            return func

        return decorator

    def get_tools(self, agent_type: Optional[AgentType] = None) -> List[Callable]:
        if agent_type is None:
            return list(self._tools.values())

        tools = []
        for tool_name, tool_func in self._tools.items():
            allowed_agents = self._tool_agents.get(tool_name, [])
            if not allowed_agents or agent_type in allowed_agents:
                tools.append(tool_func)
        return tools

    def get_tool(self, name: str) -> Callable:
        return self._tools.get(name)

    def list_tools(self, agent_type: Optional[AgentType] = None) -> List[str]:
        if agent_type is None:
            return list(self._tools.keys())

        tool_names = []
        for tool_name, allowed_agents in self._tool_agents.items():
            if not allowed_agents or agent_type in allowed_agents:
                tool_names.append(tool_name)
        return tool_names


tool_registry = ToolRegistry()
