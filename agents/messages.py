"""消息历史，只保留输入和输出消息"""

from typing import List, Union
from datetime import datetime
from pydantic_ai import ModelRequest, ModelResponse
from pydantic_ai.messages import UserPromptPart, TextPart, ToolReturnPart
import json


class Message:
    def __init__(self, message_type: str, content: str, timestamp: datetime = None):
        self.type = message_type  # "user_input" 或 "agent_output"
        self.content = content
        self.timestamp = timestamp or datetime.now()

    def __str__(self):
        return f"Message(type={self.type}, content={self.content[:50]}...)"


class MessageHistory:
    def __init__(self):
        self._history: List[Message] = []
        self._raw_history: List[Union[ModelRequest, ModelResponse]] = []

    def _should_include_message(self, msg: Union[ModelRequest, ModelResponse]) -> bool:
        # Include all messages to maintain proper tool call/response sequences
        return True

    def _filter_messages(
        self, messages: List[Union[ModelRequest, ModelResponse]]
    ) -> List[Union[ModelRequest, ModelResponse]]:
        return [msg for msg in messages if self._should_include_message(msg)]

    def add_model_messages(
        self, messages: List[Union[ModelRequest, ModelResponse]]
    ) -> None:
        filtered_messages = self._filter_messages(messages)
        self._raw_history.extend(filtered_messages)

        for msg in filtered_messages:
            if isinstance(msg, ModelRequest):
                user_content = ""
                for part in msg.parts:
                    if isinstance(part, UserPromptPart):
                        user_content += part.content + " "
                if user_content:
                    simple_msg = Message("user_input", user_content.strip())
                    self._history.append(simple_msg)
            else:
                output_content = ""
                tool_calls = []

                for part in msg.parts:
                    if isinstance(part, TextPart):
                        output_content += part.content + " "
                    elif hasattr(part, "tool_name"):
                        tool_calls.append(part)
                    elif hasattr(part, "content") and part.content:
                        output_content += str(part.content) + " "

                if tool_calls:
                    final_results = [
                        part for part in tool_calls if part.tool_name == "final_result"
                    ]
                    if final_results:
                        last_result = final_results[-1]
                        if hasattr(last_result, "args") and last_result.args:
                            try:
                                args_dict = json.loads(last_result.args)
                                if (
                                    isinstance(args_dict, dict)
                                    and "response" in args_dict
                                ):
                                    output_content = (
                                        f"Final result: {args_dict['response']}"
                                    )
                                else:
                                    output_content = f"Final result: {last_result.args}"
                            except json.JSONDecodeError:
                                output_content = f"Final result: {last_result.args}"
                    else:
                        tool_info = "Tool calls: " + ", ".join(
                            [f"{part.tool_name}" for part in tool_calls]
                        )
                        output_content = tool_info

                if output_content:
                    simple_msg = Message("agent_output", output_content.strip())
                    self._history.append(simple_msg)

    def get_history(self) -> List[Message]:
        return self._history.copy()

    def get_raw_history(self) -> List[Union[ModelRequest, ModelResponse]]:
        filtered_messages = self._filter_messages(self._raw_history)
        result = []
        for msg in filtered_messages:
            if isinstance(msg, ModelRequest):
                filtered_parts = [
                    part
                    for part in msg.parts
                    if not (
                        hasattr(part, "__class__")
                        and "SystemPromptPart" in part.__class__.__name__
                    )
                ]
                if filtered_parts:
                    new_msg = ModelRequest(parts=filtered_parts, run_id=msg.run_id)
                    result.append(new_msg)
            else:
                result.append(msg)
        return result

    def get_recent_raw_history(
        self, count: int = 10
    ) -> List[Union[ModelRequest, ModelResponse]]:
        filtered_history = self.get_raw_history()
        return (
            filtered_history[-count:]
            if len(filtered_history) > count
            else filtered_history
        )

    def get_recent_messages(self, count: int = 10) -> List[Message]:
        return (
            self._history[-count:]
            if len(self._history) > count
            else self._history.copy()
        )

    def clear(self) -> None:
        self._history.clear()
        self._raw_history.clear()

    def get_message_count(self) -> int:
        return len(self._history)


global_message_history = MessageHistory()
