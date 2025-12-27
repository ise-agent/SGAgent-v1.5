#!/usr/bin/env python3
"""
Test script for coordinator agent
"""

import asyncio
from agents.coordinator import CoordinatorAgent
from agents.context import Context, Issue


async def test_coordinator():
    coordinator = CoordinatorAgent()
    context = Context(
        issues=[
            Issue(
                path="/path/to/file.py",
                start_line=10,
                end_line=15
            )
        ]
    )
    result = await coordinator.run("go on", context)
    print(f"Result: {result}")



if __name__ == "__main__":
    asyncio.run(test_coordinator())