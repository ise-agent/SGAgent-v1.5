import logging
from typing import Optional
from pydantic_ai.usage import RequestUsage


class Logger:
    def __init__(self, name: str, log_file: Optional[str] = None):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        # Avoid duplicate handlers
        if not self.logger.handlers:
            # Formatter without logger name and level for file logs
            file_formatter = logging.Formatter('%(message)s')

            # Console handler with standard format
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(
                '%(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)

            # File handler without logger name and level
            if log_file:
                file_handler = logging.FileHandler(log_file, mode='w')
                file_handler.setFormatter(file_formatter)
                self.logger.addHandler(file_handler)

    def info(self, message: str):
        self.logger.info(message)

    def error(self, message: str):
        self.logger.error(message)

    def debug(self, message: str):
        self.logger.debug(message)

    def warning(self, message: str):
        self.logger.warning(message)

    def log_event(self, event_type: str, data: dict):
        """Log a structured event"""
        message = f"[{event_type}] {data}"
        self.logger.info(message)

    def log_usage(self, usage: RequestUsage):
        """Log API usage/tokens"""
        if usage:
            usage_data = {
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "total_tokens": usage.total_tokens,
            }

            self.logger.info(f"API Usage: {usage_data}")


def create_logger(name: str, log_file: Optional[str] = None) -> Logger:
    """Create and return a logger instance"""
    return Logger(name, log_file)
