import asyncio
from agents.localizer import LocalizerAgent
from agents.fixer import FixerAgent
from agents.reviewer import ReviewerAgent
from agents.context import Context
from settings import settings


async def test_localizer():
    # Create a localizer agent
    localizer = LocalizerAgent()
    fixer = FixerAgent()
    reviewer = ReviewerAgent()

    ctx = Context(issue=settings.PROBLEM_STATEMENT)

    # Test with a query that should return a location
    try:
        resp = await localizer.run(
            "find the bug location",
            context=ctx,
        )
        print("Response type:", type(resp))
        print("Response:", resp)
        print(f"Context now has {len(ctx.states.locations)} locations")
    except Exception as e:
        print(f"Error: {e}")

    try:
        resp = await fixer.run(
            "propose the patches",
            context=ctx,
        )
        print("Response type:", type(resp))
        print("Response:", resp)
        print(f"Context now has {len(ctx.states.patches)} patches")
    except Exception as e:
        print(f"Error: {e}")

    try:
        resp = await reviewer.run(
            "review the patch",
            context=ctx,
        )
        print("Response type:", type(resp))
        print("Response:", resp)
        print(f"Context now has {len(ctx.states.patches)} patches")
    except Exception as e:
        print(f"Error: {e}")


    # print("\nFinal context state:")
    # print(f"Locations: {len(ctx.states.locations)}")
    # print(f"Patches: {len(ctx.states.patches)}")
    # print(ctx.model_dump_json())


if __name__ == "__main__":
    asyncio.run(test_localizer())
