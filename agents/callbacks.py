
from typing import Any
from agents.context import Context, Patches


def update_context(result: Any, context: Context) -> None:
    if isinstance(result, Patches):
        context.update_patches(result)
    elif isinstance(result, str):
        pass
    else:
        pass
