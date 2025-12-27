from typing import Dict, Any, Optional
from pydantic_ai.usage import RequestUsage
from settings import settings
import os

from .logger import Logger

# Global logger for API calls
_api_logger: Optional[Logger] = None


def get_api_logger() -> Logger:
    """Get or create the API logger"""
    global _api_logger
    if _api_logger is None:
        log_dir = settings.LOG_DIR
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f"{settings.DATASET}_{settings.INSTANCE_ID}.log")
        _api_logger = Logger("api_logger", log_file)
    return _api_logger


def record_api_call(
    model: str,
    usage: RequestUsage,
    prompt: str = "",
    response: str = "",
    additional_data: Optional[Dict[str, Any]] = None
):
    """
    Record API call details for token tracking and monitoring
    """
    logger = get_api_logger()

    api_call_data = {
        "model": model,
        "usage": {
            "input_tokens": usage.input_tokens if usage else 0,
            "output_tokens": usage.output_tokens if usage else 0,
            "total_tokens": usage.total_tokens if usage else 0,
        },
        "prompt_length": len(prompt),
        "response_length": len(response),
    }

    if additional_data:
        api_call_data["additional_data"] = additional_data

    # Record to structured log
    logger.log_event("API_CALL", api_call_data)


def log_event_stream(event_type: str, data: Dict[str, Any]):
    """
    Log event stream data
    """
    logger = get_api_logger()
    logger.log_event(event_type, data)