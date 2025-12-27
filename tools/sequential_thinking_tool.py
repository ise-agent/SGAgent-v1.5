from typing import Dict, Any, Optional
from tools.registry import tool_registry, AgentType
import json


# Global variables for storing thought history (in practice, this may need more sophisticated persistence)
thought_history = []
branches = {}


def reset_sequential_thinking():
    """Reset thought history and branches, for starting a new thinking session"""
    global thought_history, branches
    thought_history = []
    branches = {}




def _validate_thought_data(
    thought: str,
    thought_number: int,
    total_thoughts: int,
    next_thought_needed: bool,
    is_revision: Optional[bool] = None,
    revises_thought: Optional[int] = None,
    branch_from_thought: Optional[int] = None,
    branch_id: Optional[str] = None,
    needs_more_thoughts: Optional[bool] = None
) -> Dict[str, Any]:
    if thought is None:
        raise ValueError("thought parameter is required")
    if not isinstance(thought, str):
        raise ValueError("thought must be a string")

    if thought_number is None:
        raise ValueError("thought_number parameter is required")
    if not isinstance(thought_number, int) or thought_number < 1:
        raise ValueError("thought_number must be an integer greater than or equal to 1")

    if total_thoughts is None:
        raise ValueError("total_thoughts parameter is required")
    if not isinstance(total_thoughts, int) or total_thoughts < 1:
        raise ValueError("total_thoughts must be an integer greater than or equal to 1")

    if next_thought_needed is None:
        raise ValueError("next_thought_needed parameter is required")
    if not isinstance(next_thought_needed, bool):
        raise ValueError("next_thought_needed must be a boolean")

    if is_revision is not None and not isinstance(is_revision, bool):
        raise ValueError("is_revision must be a boolean")

    if revises_thought is not None:
        if not isinstance(revises_thought, int) or revises_thought < 1:
            raise ValueError("revises_thought must be an integer greater than or equal to 1")

    if branch_from_thought is not None:
        if not isinstance(branch_from_thought, int) or branch_from_thought < 1:
            raise ValueError("branch_from_thought must be an integer greater than or equal to 1")

    if branch_id is not None and not isinstance(branch_id, str):
        raise ValueError("branch_id must be a string")

    if needs_more_thoughts is not None and not isinstance(needs_more_thoughts, bool):
        raise ValueError("needs_more_thoughts must be a boolean")

    return {
        "thought": thought,
        "thought_number": thought_number,
        "total_thoughts": total_thoughts,
        "next_thought_needed": next_thought_needed,
        "is_revision": is_revision,
        "revises_thought": revises_thought,
        "branch_from_thought": branch_from_thought,
        "branch_id": branch_id,
        "needs_more_thoughts": needs_more_thoughts
    }


@tool_registry.register(agents=[AgentType.FIXER,AgentType.LOCALIZER,AgentType.SUGGESTER])
def sequential_thinking(
    thought: str,
    thought_number: int,
    total_thoughts: int,
    next_thought_needed: bool,
    is_revision: Optional[bool] = None,
    revises_thought: Optional[int] = None,
    branch_from_thought: Optional[int] = None,
    branch_id: Optional[str] = None,
    needs_more_thoughts: Optional[bool] = None
) -> str:
    """
    Sequential thinking tool, used to break down complex problems into multiple thinking steps.
    This tool allows agents to perform long thinking processes, including revising previous thoughts and creating thought branches.
    Suitable for scenarios that require multi-step reasoning, analysis, or solving complex problems.

    Args:
        thought: Content of the current thinking step
        thought_number: Current thinking step number (starting from), minimum value is 1
        total_thoughts: Estimated total number of thinking steps, minimum value is 1
        next_thought_needed: Whether next step of thinking is needed
        is_revision: Whether this is a revision of previous thinking
        revises_thought: If it's a revision, indicates which thought number is being revised
        branch_from_thought: If it's a branch, indicates which thought number to branch from
        branch_id: Unique identifier for the branch
        needs_more_thoughts: Whether more thoughts are needed

    Returns:
        JSON string containing thought status information
    """
    global thought_history, branches

    try:
        # Validate input
        validated_input = _validate_thought_data(
            thought=thought,
            thought_number=thought_number,
            total_thoughts=total_thoughts,
            next_thought_needed=next_thought_needed,
            is_revision=is_revision,
            revises_thought=revises_thought,
            branch_from_thought=branch_from_thought,
            branch_id=branch_id,
            needs_more_thoughts=needs_more_thoughts
        )

        # If current thought_number exceeds total_thoughts, update total_thoughts
        if validated_input["thought_number"] > validated_input["total_thoughts"]:
            validated_input["total_thoughts"] = validated_input["thought_number"]

        # Add validated thought to history
        thought_history.append(validated_input)

        # Handle branching
        if validated_input["branch_from_thought"] and validated_input["branch_id"]:
            if validated_input["branch_id"] not in branches:
                branches[validated_input["branch_id"]] = []
            branches[validated_input["branch_id"]].append(validated_input)

        # Prepare response data
        response_data = {
            "thought_number": validated_input["thought_number"],
            "total_thoughts": validated_input["total_thoughts"],
            "next_thought_needed": validated_input["next_thought_needed"],
            "branches": list(branches.keys()),
            "thought_history_length": len(thought_history),
            "message": f"Thought {validated_input['thought_number']} recorded. "
                      f"Total thoughts: {len(thought_history)}. "
                      f"Branches: {len(branches)}."
        }

        if validated_input["is_revision"] and validated_input["revises_thought"]:
            response_data["message"] += f" Revision of thought {validated_input['revises_thought']}."

        if validated_input["branch_from_thought"] and validated_input["branch_id"]:
            response_data["message"] += f" Branch '{validated_input['branch_id']}' from thought {validated_input['branch_from_thought']}."

        return json.dumps(response_data, ensure_ascii=False, indent=2)

    except Exception as e:
        return f"Error executing sequential thinking tool: {str(e)}"