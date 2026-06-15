"""Logging configuration and utilities."""

import logging
import json
from datetime import datetime
from typing import Any, Dict
from pathlib import Path
from src.config import AgentConfig


class JsonFormatter(logging.Formatter):
    """JSON log formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'logger': record.name,
        }

        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        if hasattr(record, 'extra_data'):
            log_data.update(record.extra_data)

        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """Colored log formatter for console output."""

    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[41m',   # Red background
    }
    RESET = '\033[0m'

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        message = super().format(record)
        return f"{color}{timestamp} | {record.levelname:8} | {message}{self.RESET}"


def setup_logging(config: AgentConfig) -> logging.Logger:
    """Setup logging for the application.

    Args:
        config: Agent configuration

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger('jira-servicenow-agent')
    logger.setLevel(getattr(logging, config.log_level))

    # Remove existing handlers
    logger.handlers.clear()

    # Console handler with colors
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(ColoredFormatter('%(name)s | %(message)s'))
    logger.addHandler(console_handler)

    # File handler with JSON
    Path(config.log_file_path).parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(config.log_file_path)
    file_handler.setFormatter(JsonFormatter())
    logger.addHandler(file_handler)

    return logger


class LoggerMixin:
    """Mixin to provide logging capabilities to classes."""

    _logger: logging.Logger = None

    @property
    def logger(self) -> logging.Logger:
        if self._logger is None:
            self._logger = logging.getLogger(self.__class__.__name__)
        return self._logger

    def log_info(self, message: str, **kwargs):
        """Log info message with extra data."""
        extra = logging.LogRecord(
            name=self.logger.name,
            level=logging.INFO,
            pathname='',
            lineno=0,
            msg=message,
            args=(),
            exc_info=None
        )
        extra.extra_data = kwargs
        self.logger.info(message, extra=extra)

    def log_error(self, message: str, exception: Exception = None, **kwargs):
        """Log error message with extra data."""
        if exception:
            self.logger.exception(message)
        else:
            self.logger.error(message)
