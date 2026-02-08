"""
Logging Configuration
====================

Centralized logging configuration with structured JSON logging.
Enhanced for production with request IDs, error tracking, and performance metrics.
"""

import logging
import logging.handlers
import sys
import uuid
from pathlib import Path
from typing import Optional
import structlog
from datetime import datetime
from contextvars import ContextVar

from config.settings import LoggingConfig

# Context variables for request tracking
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar('user_id', default=None)


def setup_logging(config: LoggingConfig):
    """Setup application logging."""
    
    # Create logs directory
    log_file = Path(config.file_path)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Add context processors for request/user tracking
    def add_request_context(logger, method_name, event_dict):
        """Add request context to log entries."""
        request_id = request_id_var.get()
        user_id = user_id_var.get()
        if request_id:
            event_dict["request_id"] = request_id
        if user_id:
            event_dict["user_id"] = user_id
        return event_dict
    
    # Configure structlog
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="ISO"),
        add_request_context,  # Add request/user context
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    
    # Add renderer based on format
    if config.format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard logging
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.level.upper()))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, config.level.upper()))
    
    if config.format == "json":
        console_formatter = logging.Formatter('%(message)s')
    else:
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        filename=config.file_path,
        maxBytes=config.max_file_size,
        backupCount=config.backup_count
    )
    file_handler.setLevel(getattr(logging, config.level.upper()))
    file_handler.setFormatter(console_formatter)
    root_logger.addHandler(file_handler)


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


def set_request_id(request_id: Optional[str] = None) -> str:
    """Set request ID for current context. Returns the request ID."""
    if request_id is None:
        request_id = str(uuid.uuid4())
    request_id_var.set(request_id)
    return request_id


def get_request_id() -> Optional[str]:
    """Get current request ID."""
    return request_id_var.get()


def set_user_id(user_id: Optional[str]):
    """Set user ID for current context."""
    user_id_var.set(user_id)


def get_user_id() -> Optional[str]:
    """Get current user ID."""
    return user_id_var.get()
