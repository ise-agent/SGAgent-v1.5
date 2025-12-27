from agents.test import TesterAgent
from agents.context import Context
from settings import settings
from pathlib import Path
import json
from agents.context import Locations, Suggestions

t = TesterAgent()

context = Context()
context.issue = settings.PROBLEM_STATEMENT

# Load locations
locations_path = Path("results/locations") / f"{settings.INSTANCE_ID}.json"
if locations_path.exists():
    try:
        with open(locations_path, "r") as f:
            data = json.load(f)
            context.locations = Locations(**data)
    except Exception as e:
        print(f"Error loading locations from {locations_path}: {e}")

# Load suggestions
suggestions_path = Path("results/suggestions") / f"{settings.INSTANCE_ID}.json"
if suggestions_path.exists():
    try:
        with open(suggestions_path, "r") as f:
            data = json.load(f)
            context.suggestions = Suggestions(**data)
    except Exception as e:
        print(f"Error loading suggestions from {suggestions_path}: {e}")
        


async def test_suggestions():
    result = await t.run("what's suggestion?", context=context)
    print(result)

def main():
    import asyncio
    asyncio.run(test_suggestions())

if __name__ == "__main__":
    main()
