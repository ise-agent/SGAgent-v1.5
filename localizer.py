import asyncio
import json
from pathlib import Path
from agents.localizer import LocalizerAgent
from agents.context import Context
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
    """Orchestrates the single localizer agent system to locate the bug."""

    def __init__(self):
        self.localizer = LocalizerAgent()
        self.context = Context()
        self.context.issue = settings.PROBLEM_STATEMENT

    async def run(self) -> None:
        """
        Run the single localizer agent system.
        """
        print("=" * 60)
        print("\nRunning Localizer Agent...")
        print(f"Using the docker image :{settings.DOCKER_IMAGE}")
        localizer_instruction = "Identify the locations of the bug based on the issue description."

        result = await self.localizer.run(localizer_instruction, context=self.context)
        print(f"Localizer result: {result}")
        
        # Save the locations to a file
        output_file = Path(f"results/locations/{settings.INSTANCE_ID}.json")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result.model_dump(), f, indent=4)
        print(f"Locations saved to {output_file}")


async def main():
    image = find_image(settings.INSTANCE_ID)

    local_dir = prepare_local_dir(settings.INSTANCE_ID)

    container_name = create_container(image, settings.INSTANCE_ID)

    copy_testbed(container_name, local_dir)

    try:
        orchestrator = AgentOrchestrator()
        await orchestrator.run()
    except Exception as e:
        print(f"Detailed error in localizer main loop: {e}")
        import traceback
        traceback.print_exc()
        # Depending on requirements, we might want to exit with error code or 0
        # If we want batch runner to continue to next task even if this fails hard (after retries),
        # we might just log it. But usually non-zero exit code is better for batch runners to know failure.
        raise e
    finally:
        cleanup_container(container_name)
        cleanup_local_dir(local_dir)


if __name__ == "__main__":
    asyncio.run(main())
