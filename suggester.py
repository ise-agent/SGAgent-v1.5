import asyncio
import json
from pathlib import Path
from agents.suggester import SuggesterAgent
from agents.context import Context, Locations
from settings import settings
from utils.dock import (
    find_image,
    prepare_local_dir,
    create_container,
    copy_testbed,
    cleanup_container,
    cleanup_local_dir,
)

class AgentOrchestrator:
    def __init__(self):
        self.suggester = SuggesterAgent()
        self.context = Context()
        self.context.issue = settings.PROBLEM_STATEMENT
        loc_file = Path(f"results/locations/{settings.INSTANCE_ID}.json")
        if loc_file.exists():
            data = json.loads(loc_file.read_text(encoding="utf-8"))
            self.context.locations = Locations(**data)

    async def run(self) -> None:
        print("=" * 60)
        print("\nRunning Suggester Agent...")
        print(f"Using the docker image :{settings.DOCKER_IMAGE}")
        suggester_instruction = """Propose structured fix suggestions based on the issue description."""

        result = await self.suggester.run(suggester_instruction, context=self.context)
        print(f"Suggester result: {result}")

        output_file = Path(f"results/suggestions/{settings.INSTANCE_ID}.json")
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result.model_json_schema() and result.model_dump(), f, indent=4)
        print(f"Suggestions saved to {output_file}")

async def main():
    image = find_image(settings.INSTANCE_ID)
    local_dir = prepare_local_dir(settings.INSTANCE_ID)
    container_name = create_container(image, settings.INSTANCE_ID)
    copy_testbed(container_name, local_dir)
    try:
        orchestrator = AgentOrchestrator()
        await orchestrator.run()
    except Exception as e:
        print(f"Detailed error in suggester main loop: {e}")
        import traceback
        traceback.print_exc()
        raise e
    finally:
        cleanup_container(container_name)
        cleanup_local_dir(local_dir)

if __name__ == "__main__":
    asyncio.run(main())
