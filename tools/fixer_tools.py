from tools.registry import tool_registry, AgentType
from settings import settings
from pathlib import Path
import subprocess
import re
from utils.apply_check import ruff_check_file
from settings import settings

@tool_registry.register(agents=[AgentType.FIXER])
def create_file(file_path: str, code: str, timeout: int = 60) -> str:
    """
    Create a new file with the given code at the specified path.  
    The file_path must be a relative path. An absolute path is not allowed.  
    After creation, the file will be executed inside the SWE-bench Docker container  
    (using the same interactive bash environment as normal evaluation).

    Args:
        file_path: The path where the file should be created. 
        code: The Python code to write to the file and execute.
        timeout: Timeout for the execution in seconds (default 60).

    Returns:
        The output from the executed code.
    """
    try:
        path_obj = Path(file_path)
        if not path_obj.is_absolute():
            full_path = Path(settings.TEST_BED) / settings.PROJECT_NAME / file_path
        else:
            full_path = path_obj

        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(code)

        script_rel_path = f"./{full_path.relative_to(Path(settings.TEST_BED) / settings.PROJECT_NAME)}"

        docker_cmd = [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{Path(settings.TEST_BED) / settings.PROJECT_NAME}:/testbed",
            "-w",
            "/testbed",
            settings.DOCKER_IMAGE,
            "bash",
            "--login",
            "-i",
            "-c",
            f"python {script_rel_path}",
        ]

        result = subprocess.run(
            docker_cmd, capture_output=True, text=True, timeout=timeout
        )

        if result.returncode == 0:
            return result.stdout
        else:
            return f"Error executing code:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"

    except subprocess.TimeoutExpired:
        return f"Execution timed out after {timeout} seconds"
    except Exception as e:
        return f"Error: {str(e)}"


@tool_registry.register(agents=[AgentType.FIXER])
def edit_file_by_lineno(
    file_path: str, content: str, start_line: int, end_line: int
) -> str:
    """
    Edit a file by replacing content between start_line and end_line (inclusive).
    If content is empty, it performs a delete operation.

    Args:
        file_path: Path to the file to edit. If relative, TEST_BED/PROJECT_NAME will be prepended.
        content: New content to insert. If empty, it deletes the specified lines.
        start_line: Starting line number (1-based).
        end_line: Ending line number (1-based, inclusive).

    Returns:
        Success or error message.
    """
    try:
        path_obj = Path(file_path)
        if not path_obj.is_absolute():
            full_path = Path(settings.TEST_BED) / settings.PROJECT_NAME / file_path
        else:
            base_path = Path(settings.TEST_BED) / settings.PROJECT_NAME
            try:
                path_obj.relative_to(base_path)
            except ValueError:
                return f"Error: Absolute path does not start with {base_path}"
            full_path = path_obj

        if not full_path.exists():
            return f"Error: File does not exist: {full_path}"

        # Read the file
        with open(full_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Adjust for 0-based indexing
        start_idx = start_line - 1
        end_idx = end_line  # end_line is inclusive

        # Validate line numbers
        if start_idx < 0 or end_idx > len(lines) or start_idx > end_idx:
            return f"Error: Invalid line range. File has {len(lines)} lines."

        # Ensure content ends with a newline if not empty
        if content and not content.endswith("\n"):
            content += "\n"

        # Replace or delete the specified lines
        if content == "" or content == "\n":  # Delete operation
            updated_lines = lines[:start_idx] + lines[end_idx:]
        else:  # Replace operation
            content_lines = content.splitlines(keepends=True)
            updated_lines = lines[:start_idx] + content_lines + lines[end_idx:]

        # Write the updated content back to the file
        with open(full_path, "w", encoding="utf-8") as f:
            f.write("".join(updated_lines))

        # Perform ruff check on the modified file
        ruff_result = ruff_check_file(str(full_path))

        if content == "" or content == "\n":
            result = (
                f"Successfully deleted lines {start_line} to {end_line} in {file_path}"
            )
        else:
            result = (
                f"Successfully replaced lines {start_line} to {end_line} in {file_path}"
            )

        # Return both the operation result and ruff check result
        return f"{result}\n\nRuff check result:\n{ruff_result}"

    except Exception as e:
        return f"Error editing file: {str(e)}"


@tool_registry.register(agents=[AgentType.FIXER])
def insert(file_path: str, content: str, insert_line: int) -> str:
    """
    Insert content at the specified line in a file.

    Args:
        file_path: Path to the file to edit. If relative, TEST_BED/PROJECT_NAME will be prepended.
        content: Content to insert.
        insert_line: Line number to insert before (1-based).

    Returns:
        Success or error message.
    """
    try:
        path_obj = Path(file_path)
        if not path_obj.is_absolute():
            full_path = Path(settings.TEST_BED) / settings.PROJECT_NAME / file_path
        else:
            base_path = Path(settings.TEST_BED) / settings.PROJECT_NAME
            try:
                path_obj.relative_to(base_path)
            except ValueError:
                return f"Error: Absolute path does not start with {base_path}"
            full_path = path_obj

        if not full_path.exists():
            return f"Error: File does not exist: {full_path}"

        # Read the file
        with open(full_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Adjust for 0-based indexing
        insert_idx = insert_line - 1

        # Validate insert position
        if insert_idx < 0 or insert_idx > len(lines):
            return f"Error: Invalid insert line. File has {len(lines)} lines, insert_line={insert_line}."

        # Ensure content ends with a newline if not empty
        if content and not content.endswith("\n"):
            content += "\n"

        # Insert the content at the specified line
        content_lines = content.splitlines(keepends=True)
        updated_lines = lines[:insert_idx] + content_lines + lines[insert_idx:]

        # Write the updated content back to the file
        with open(full_path, "w", encoding="utf-8") as f:
            f.write("".join(updated_lines))

        # Perform ruff check on the modified file
        ruff_result = ruff_check_file(str(full_path))

        result = f"Successfully inserted content at line {insert_line} in {file_path}"

        # Return both the operation result and ruff check result
        return f"{result}\n\nRuff check result:\n{ruff_result}"

    except Exception as e:
        return f"Error inserting content: {str(e)}"


@tool_registry.register(agents=[AgentType.FIXER])
def edit_file_by_content(file_path: str, old_content: str, new_content: str) -> str:
    """
    Edit a file by replacing content using regex matching instead of line numbers.
    If multiple matches are found, returns a warning to user.

    Args:
        file_path: Path to the file to edit. If relative, TEST_BED/PROJECT_NAME will be prepended.
        old_content: The content pattern (regex) to match and replace.
        new_content: The new content to insert.

    Returns:
        Success or error message.
    """
    try:
        path_obj = Path(file_path)
        if not path_obj.is_absolute():
            full_path = Path(settings.TEST_BED) / settings.PROJECT_NAME / file_path
        else:
            base_path = Path(settings.TEST_BED) / settings.PROJECT_NAME
            try:
                path_obj.relative_to(base_path)
            except ValueError:
                return f"Error: Absolute path does not start with {base_path}"
            full_path = path_obj

        if not full_path.exists():
            return f"Error: File does not exist: {full_path}"

        # Read the file
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Find all matches
        matches = list(re.finditer(old_content, content, re.MULTILINE | re.DOTALL))

        if not matches:
            return f"Error: Pattern '{old_content}' not found in {file_path}"

        if len(matches) > 1:
            return f"Warning: Pattern '{old_content}' matches {len(matches)} times in {file_path}. Please use a more specific pattern to avoid unintended replacements."

        # Replace the matched content
        new_file_content = re.sub(
            old_content, new_content, content, count=1, flags=re.MULTILINE | re.DOTALL
        )

        # Write the updated content back to the file
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(new_file_content)

        # Perform ruff check on the modified file
        ruff_result = ruff_check_file(str(full_path))

        result = f"Successfully replaced pattern '{old_content}' with '{new_content}' in {file_path}"

        # Return both the operation result and ruff check result
        return f"{result}\n\nRuff check result:\n{ruff_result}"

    except re.error as e:
        return f"Error with regex pattern: {str(e)}"
    except Exception as e:
        return f"Error editing file: {str(e)}"
