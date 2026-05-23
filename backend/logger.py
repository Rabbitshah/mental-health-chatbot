"""
Structured JSON logging configuration for the mental health chatbot backend.
Requirement 16.4, 16.5
"""
import logging
import json
import os
import traceback
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    """Custom JSON log formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include extra fields attached to the record
        for key, value in record.__dict__.items():
            if key not in (
                "name", "msg", "args", "levelname", "levelno", "pathname",
                "filename", "module", "exc_info", "exc_text", "stack_info",
                "lineno", "funcName", "created", "msecs", "relativeCreated",
                "thread", "threadName", "processName", "process", "message",
                "taskName",
            ):
                log_entry[key] = value

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        if record.stack_info:
            log_entry["stack_info"] = self.formatStack(record.stack_info)

        return json.dumps(log_entry, default=str)


def setup_logging() -> None:
    """Configure root logger with JSON formatter and level from environment."""
    log_level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_name, logging.INFO)

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicate output
    root_logger.handlers.clear()
    root_logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger. Call setup_logging() once at app startup."""
    return logging.getLogger(name)
