import asyncio
import subprocess
import json
from pathlib import Path

from agents.fixer import FixerAgent
from agents.context import Context, Locations, Suggestions
from utils.logging import log_event_stream
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
    """Orchestrates the single fixer agent system to resolve GitHub issues."""

    def __init__(self):
        self.fixer = FixerAgent()

        self.context = Context()
        self.context.issue = settings.PROBLEM_STATEMENT

        # Load locations
        locations_path = Path("results/locations") / f"{settings.INSTANCE_ID}.json"
        if locations_path.exists():
            try:
                with open(locations_path, "r") as f:
                    data = json.load(f)
                    self.context.locations = Locations(**data)
            except Exception as e:
                print(f"Error loading locations from {locations_path}: {e}")

        # Load suggestions
        suggestions_path = Path("results/suggestions") / f"{settings.INSTANCE_ID}.json"
        if suggestions_path.exists():
            try:
                with open(suggestions_path, "r") as f:
                    data = json.load(f)
                    self.context.suggestions = Suggestions(**data)
            except Exception as e:
                print(f"Error loading suggestions from {suggestions_path}: {e}")

    def _get_project_path(self):
        project_path = Path(settings.TEST_BED) / settings.PROJECT_NAME
        return project_path

    def _save_git_diff_and_restore(
        self, output_file: str = None, save_diff: bool = True
    ):
        project_path = self._get_project_path()

        try:
            # Determine patch file path
            if output_file is None:
                output_file = (
                    f"results/patch_diff/{settings.DATASET}_{settings.INSTANCE_ID}.patch"
                )

            if save_diff:
                Path("results/patch_diff").mkdir(exist_ok=True)

            if not project_path.exists():
                print(f"Project path does not exist: {project_path}")
                return False

            git_dir = project_path / ".git"
            if not git_dir.exists() or not git_dir.is_dir():
                print(f"Directory is not a git repository: {project_path}")
                return True  # Nothing to do

            # Check git status
            status_result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=project_path,
            )

            if status_result.returncode != 0:
                print(f"Error checking git status: {status_result.stderr}")
                return False

            has_changes = bool(status_result.stdout.strip())

            if has_changes and save_diff:
                # Add all changes first to include new files
                add_result = subprocess.run(
                    ["git", "add", "."],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=project_path,
                )

                if add_result.returncode != 0:
                    print(f"Error adding files: {add_result.stderr}")
                    return False

                # Get the diff of staged changes (includes new files)
                diff_result = subprocess.run(
                    ["git", "diff", "--cached"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=project_path,
                )
                # diff_result = subprocess.run(
                #     ["git", "diff"],
                #     capture_output=True,
                #     text=True,
                #     timeout=30,
                #     cwd=project_path,
                # )

                # Commit the changes
                commit_result = subprocess.run(
                    ["git", "commit", "-m", "Fixed"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=project_path,
                )

                if commit_result.returncode != 0:
                    print(f"Error committing changes: {commit_result.stderr}")
                    # If commit fails, continue anyway as the diff was already captured
                    print("Continuing despite commit failure...")

                if diff_result.returncode == 0 and diff_result.stdout.strip():
                    with open(output_file, "w", encoding="utf-8") as f:
                        f.write(diff_result.stdout)
                    print(f"Git diff saved to {output_file}")
                else:
                    print(f"Error getting git diff: {diff_result.stderr}")
                    return False
            elif not has_changes:
                print("No changes to save in diff")

            return True

        except Exception as e:
            print(f"Error during git operations: {e}")
            return False

        finally:
            try:
                print("Cleaning untracked files...")
                subprocess.run(
                    ["git", "clean", "-fd"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=project_path,
                )

                print("Restoring tracked files...")
                subprocess.run(
                    ["git", "checkout", "."],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=project_path,
                )

                print("Project fully restored to original state")

            except Exception as e2:
                print(f"Error in final restore phase: {e2}")

    async def run(self, max_iterations: int = 1) -> None:
        """
        Run the single fixer agent system with patch application and export git diff.

        Args:
            max_iterations: Number of iterations (set to 1 for single run)

        Returns:
            Dict containing final state and results
        """
        print("=" * 60)
        print("\nRunning Fixer Agent...")
        print(f"Using the docke image :{settings.DOCKER_IMAGE}")
        fixer_instruction = "Identify the issues and use the modification tool to fix them. "

        result = await self.fixer.run(fixer_instruction, context=self.context)
        self._save_git_diff_and_restore()
        print(f"Fixer result: {result}")



async def main():
    image = find_image(settings.INSTANCE_ID)

    local_dir = prepare_local_dir(settings.INSTANCE_ID)

    container_name = create_container(image, settings.INSTANCE_ID)

    copy_testbed(container_name, local_dir)

    try:
        orchestrator = AgentOrchestrator()
        result = await orchestrator.run(max_iterations=1)
        return result
    finally:
        cleanup_container(container_name)
        cleanup_local_dir(local_dir)


if __name__ == "__main__":
    asyncio.run(main())
