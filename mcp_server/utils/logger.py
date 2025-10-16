"""
Logging Configuration

Provides centralized logging configuration for the application.
"""

import logging
import sys
from typing import Optional

from ..config import settings

# Global logger registry
_loggers: dict[str, logging.Logger] = {}


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger with the specified name.

    Args:
        name: Logger name (typically __name__ of the module)

    Returns:
        Configured logger instance
    """
    if name in _loggers:
        return _loggers[name]

    # Create new logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.log_level.upper()))

    # Avoid adding multiple handlers if logger already exists
    if not logger.handlers:
        # Create console handler with formatting
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(getattr(logging, settings.log_level.upper()))

        # Create formatter
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)

        logger.addHandler(handler)

    # Cache logger
    _loggers[name] = logger

    return logger


def set_log_level(level: str) -> None:
    """
    Update log level for all registered loggers.

    Args:
        level: New log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    log_level = getattr(logging, level.upper())

    for logger in _loggers.values():
        logger.setLevel(log_level)
        for handler in logger.handlers:
            handler.setLevel(log_level)


def configure_structured_logging() -> None:
    """
    Configure structured JSON logging for Cloud Run environments.

    This is useful when deploying to Cloud Run as it allows logs to be
    properly parsed and indexed by Cloud Logging.
    """
    # TODO: Implement structured JSON logging
    # import json
    # class JsonFormatter(logging.Formatter):
    #     def format(self, record):
    #         log_obj = {
    #             "timestamp": self.formatTime(record, self.datefmt),
    #             "severity": record.levelname,
    #             "message": record.getMessage(),
    #             "logger": record.name,
    #             "module": record.module,
    #             "function": record.funcName,
    #             "line": record.lineno
    #         }
    #         return json.dumps(log_obj)

    pass
