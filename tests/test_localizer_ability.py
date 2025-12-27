import asyncio
import json
from agents.localizer import LocalizerAgent
from agents.context import Context, Locations
from settings import settings


async def test_localizer():
    # Create a localizer agent
    localizer = LocalizerAgent()

    ctx = Context(issue=settings.PROBLEM_STATEMENT)
    # Test with a query that should return a location
    try:
        resp = await localizer.run(
            f"what's problem statement",
            context=ctx,
        )
        print("Response type:", type(resp))
        print("Response:", resp)
        if hasattr(resp, "locations"):
            print("Locations:", resp.locations)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        
        
   

if __name__ == "__main__":
    asyncio.run(test_localizer())
