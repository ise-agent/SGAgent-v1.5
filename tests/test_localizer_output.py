import asyncio
import json
from agents.localizer import LocalizerAgent
from agents.context import Context, Location

async def test_localizer():
    # Create a localizer agent
    localizer = LocalizerAgent()

    # Test with a query that should return a location
    print("\nTesting location output...")
    try:
        # We'll simulate a case where the AI should return a location
        result = await localizer.run("hi")
        print(f"Result: {result}")
        print(f"Type: {type(result)}")
       
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_localizer())