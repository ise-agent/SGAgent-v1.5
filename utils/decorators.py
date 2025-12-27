"""Utility decorators"""
from typing import Any, Callable, Dict


def singleton(cls: type) -> Callable:
    """Singleton pattern decorator"""
    instances: Dict[type, Any] = {}

    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance