import asyncio
from abc import ABC, abstractmethod
from typing import (
    TypeVar,
    Generic,
    Type,
    Callable,
    TypeAlias,
    Sequence,
    Dict,
    Optional,
    Any,
)
from collections.abc import AsyncIterable
from pydantic_ai import Agent, UsageLimits, RunContext, FunctionToolset, AbstractToolset
from pydantic_ai.exceptions import ModelHTTPError
from pydantic_ai.messages import (
    AgentStreamEvent,
    PartStartEvent,
    PartDeltaEvent,
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    PartEndEvent,
)
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from agents.context import Context
from agents.messages import global_message_history
from settings import settings
from agents.callbacks import update_context
from utils.logging import log_event_stream, record_api_call
from utils.metrics import increment_tool_usage, increment_agent_run, print_tool_usage_stats
import textwrap

Callback: TypeAlias = Callable[..., Context]
T = TypeVar("T")


class BaseAgent(ABC, Generic[T]):
    def __init__(
        self,
        tools: list | None = None,
        output_type: Type[T] | None = None,
        enable_monitoring: bool = True,
    ):
        self.model = OpenAIChatModel(
            settings.model,
            provider=OpenAIProvider(
                base_url=settings.base_url, api_key=settings.api_key
            ),
        )
        self.agent_tools = tools
        self.enable_monitoring = enable_monitoring
        self.dynamic_toolset = FunctionToolset()

        self.event_stream_handler = (
            self._create_event_handler() if enable_monitoring else None
        )

        @self.dynamic_toolset.tool
        def create_tool(code: str) -> str:
            """
            Dynamically create and register a small Python helper tool.

            IMPORTANT LIMITATIONS:
            - The execution environment is NOT the target project environment.
            The target project (e.g. astropy) cannot be imported or executed here.
            - Tools created here MUST NOT import any third-party libraries, and MUST NOT
            import the target project. Only Python standard library and pure Python
            logic are allowed.
            - These tools are intended only for lightweight helper functions such as
            string processing, small math helpers, diff/patch manipulation, or other
            environment-independent utilities.
            - Tools MUST NOT contain project logic, test execution, file I/O,
            subprocess calls, or any system-level operations.

            The `code` parameter must contain exactly one full Python function
            definition. The function will be safely validated, executed inside a
            controlled namespace, and then registered as a callable tool.
            """

            try:
                forbidden_keywords = [
                    "import os", "system(", "subprocess",
                    "open(", "exec(", "eval("
                ]
                if any(kw in code for kw in forbidden_keywords):
                    return "Tool creation failed: Potential dangerous code detected"

                namespace = {"Any": Any}

                exec(code, namespace)

                new_func = None
                for v in namespace.values():
                    if callable(v) and v.__name__ in code:
                        new_func = v

                if not new_func:
                    return "Tool creation failed: No valid function definition detected"

                self.dynamic_toolset.add_function(new_func, name=new_func.__name__)

                return f"Successfully created tool '{new_func.__name__}'"

            except Exception as e:
                return f"Creation failed: {e}"
        
        self.agent = Agent(
            model=self.model,
            system_prompt=self.get_system_prompt(),
            tools=self.agent_tools,
            toolsets=[self.dynamic_toolset],
            output_type=output_type,
            deps_type=Context,
            output_retries=20,
            event_stream_handler=self.event_stream_handler,
        )

        @self.agent.instructions
        async def inject_context(ctx: RunContext[Context]) -> str:
            context_info = []
            if ctx.deps.issue:
                context_info.append(f"Issue: {ctx.deps.issue}")

            if ctx.deps.locations and ctx.deps.locations.locations:
                loc_strings = [
                    f"{loc.path}:{loc.start_line}-{loc.end_line}"
                    for loc in ctx.deps.locations.locations
                ]
                context_info.append(f"Locations: {', '.join(loc_strings)}")
                if ctx.deps.locations.reasons:
                    context_info.append(f"Location Reasons: {'; '.join(ctx.deps.locations.reasons)}")

            if ctx.deps.suggestions and ctx.deps.suggestions.suggestions:
                sugg_strings = [
                    f"{s.title}: {'; '.join(s.rationale)}"
                    for s in ctx.deps.suggestions.suggestions
                ]
                context_info.append(f"Suggestions: {'; '.join(sugg_strings)}")

            if ctx.deps.states and ctx.deps.states.patches:
                state_info = []
                if ctx.deps.states.patches:
                    state_info.append(f"Patches: {len(ctx.deps.states.patches)}")
                context_info.append(f"States: {', '.join(state_info)}")

            if context_info:
                return "Context:\n" + "\n".join(context_info) + "\n"
            return ""

    def _create_event_handler(self):
        async def handle_events(
            ctx: RunContext[Context], events: AsyncIterable[AgentStreamEvent]
        ):
            async for event in events:
                self._print_event(event)

        return handle_events

    def _print_event(self, event):
        if isinstance(event, PartStartEvent):
            self._current_content = ""
            print(f"Begin {event.index}: {type(event.part).__name__}")
            log_event_stream("PART_START", {"index": event.index, "part_type": type(event.part).__name__})

            if hasattr(event.part, "content") and event.part.content:
                self._current_content += event.part.content

        elif isinstance(event, PartDeltaEvent):
            if hasattr(event.delta, "content_delta"):
                self._current_content += event.delta.content_delta
                # Skip logging delta events to reduce log noise

        elif isinstance(event, PartEndEvent):
            if hasattr(self, "_current_content"):
                print(f"Content : {self._current_content}")
                log_event_stream("PART_END", {"content": self._current_content})

        elif isinstance(event, FunctionToolCallEvent):
            print(f"Tool Call: {event.part.tool_name}({event.part.args})")
            log_event_stream("TOOL_CALL", {"tool_name": event.part.tool_name, "args": event.part.args})
            # Increment tool usage counter
            increment_tool_usage(event.part.tool_name)

        elif isinstance(event, FunctionToolResultEvent):
            print(f"Tool Result: {event.result.content}")
            log_event_stream("TOOL_RESULT", {"content": event.result.content})

    @abstractmethod
    def get_system_prompt(self) -> str:
        pass

    def add_tool(self, func: Callable, name: str | None = None):
        self.dynamic_toolset.add_function(func, name=name)

    def create_toolset(self, tools: list[Callable]) -> FunctionToolset:
        return FunctionToolset(tools=tools)

    async def run(
        self,
        message: str,
        context: Context | None = None,
        use_shared_history: bool = True,
        callback: Callback = update_context,
        toolsets: Sequence[AbstractToolset[Context]] | None = None,
    ) -> T:
        # Increment agent run counter using class name
        agent_name = self.__class__.__name__
        increment_agent_run(agent_name)

        if context is None:
            context = Context()

        message_history = None
        if use_shared_history:
            message_history = global_message_history.get_raw_history()

        result = None
        max_retries = 1
        base_delay = 5

        for attempt in range(max_retries):
            try:
                result = await self.agent.run(
                    message,
                    deps=context,
                    message_history=message_history,
                    usage_limits=UsageLimits(request_limit=150),
                    toolsets=toolsets,
                )
                break
            except ModelHTTPError as e:
                if attempt == max_retries - 1:
                    print(f"Failed after {max_retries} attempts. Last error: {e}")
                    raise e
                
                delay = base_delay * (2 ** attempt)
                print(f"ModelHTTPError encountered: {e}. Retrying in {delay} seconds (Attempt {attempt + 1}/{max_retries})...")
                await asyncio.sleep(delay)
            except Exception as e:
                 # Catch other potential transient errors if needed, or let them bubble up
                 # For now, focusing on ModelHTTPError as requested
                 if "500" in str(e) or "502" in str(e) or "503" in str(e) or "504" in str(e):
                     if attempt == max_retries - 1:
                        print(f"Failed after {max_retries} attempts. Last error: {e}")
                        raise e
                     delay = base_delay * (2 ** attempt)
                     print(f"Server Error encountered: {e}. Retrying in {delay} seconds (Attempt {attempt + 1}/{max_retries})...")
                     await asyncio.sleep(delay)
                 else:
                     raise e

        # Log API call usage (tokens)
        usage = result.usage()
        if usage:
            record_api_call(
                model=settings.model,
                usage=usage,
                prompt=message,
                response=str(result.output) if result.output else ""
            )

        if use_shared_history:
            messages = result.all_messages()
            global_message_history.add_model_messages(messages)

        if callback:
            callback(result.output, context)

        # Print tool usage statistics after each run
        print_tool_usage_stats()

        return result.output
