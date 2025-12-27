#!/usr/bin/env python3
"""
Test script for message history
"""

import asyncio
from agents.coordinator import CoordinatorAgent
from agents.context import Context, Issue
from agents.messages import global_message_history


async def test_message_history():
    print("Testing message history...")

    # Clear any existing history
    global_message_history.clear()

    # Create coordinator agent
    coordinator = CoordinatorAgent()

    # First run - should use empty history
    print("\n=== First run ===")
    context1 = Context()
    result1 = await coordinator.run("Find bugs in this code", context1)
    print(f"Result 1: {result1}")

    # Check message history after first run
    message_history1 = global_message_history.get_history()
    print(f"Message history after first run: {len(message_history1)} messages")
    for i, msg in enumerate(message_history1):
        print(f"  Message {i}: {msg}")

    # Second run - should use history from first run
    print("\n=== Second run ===")
    context2 = Context(
        issues=[
            Issue(
                path="/path/to/file.py",
                start_line=10,
                end_line=15
            )
        ]
    )
    result2 = await coordinator.run("Suggest fixes for this issue", context2)
    print(f"Result 2: {result2}")

    # Check message history after second run
    message_history2 = global_message_history.get_history()
    print(f"Message history after second run: {len(message_history2)} messages")
    for i, msg in enumerate(message_history2):
        print(f"  Message {i}: {msg}")


if __name__ == "__main__":
    asyncio.run(test_message_history())