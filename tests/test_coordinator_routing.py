"""
Test file for coordinator agent routing capabilities
"""
import pytest
from agents.coordinator import CoordinatorAgent
from agents.context import Context, States
from models.agent_types import SubAgentType


@pytest.mark.asyncio
async def test_coordinator_route_to_localizer_when_no_location():
    """Test that coordinator routes to localizer when issue location is unknown"""
    coordinator = CoordinatorAgent()
    context = Context()
    context.issue = "The application crashes when clicking the submit button"

    result: SubAgentType = await coordinator.run(
        "Analyze this issue and decide next step",
        context=context
    )

    assert result.target_agent == "localizer"
    assert "reason" in result.model_dump()
    assert "instruction" in result.model_dump()


@pytest.mark.asyncio
async def test_coordinator_route_to_fixer_when_location_known():
    """Test that coordinator routes to fixer when location is already known"""
    coordinator = CoordinatorAgent()
    context = Context()
    context.issue = "Button click handler has a typo causing crash"
    # Add location information to context
    if not context.states:
        context.states = States()
    context.states.locations = [{"file": "src/components/Button.tsx", "line": 42, "reason": "submit handler has typo"}]

    result: SubAgentType = await coordinator.run(
        "We have identified the location, what's next?",
        context=context
    )

    assert result.target_agent == "fixer"


@pytest.mark.asyncio
async def test_coordinator_route_to_reviewer_when_patch_available():
    """Test that coordinator routes to reviewer when a patch is available"""
    coordinator = CoordinatorAgent()
    context = Context()
    context.issue = "Button click handler has a typo"
    if not context.states:
        context.states = States()
    context.states.locations = [{"file": "src/components/Button.tsx", "line": 42, "reason": "submit handler has typo"}]
    context.states.patches = [{"file": "src/components/Button.tsx", "patch": "Fixed typo in handler function"}]

    result: SubAgentType = await coordinator.run(
        "We have a patch for the issue, what's next?",
        context=context
    )

    assert result.target_agent == "reviewer"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__])