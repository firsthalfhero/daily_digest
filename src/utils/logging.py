"""
Logging configuration for the Daily Digest Assistant.

This module provides a structured logging setup with both file and console output,
log rotation, and context-aware logging capabilities.
"""

import json
import logging
import logging.handlers
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import structlog
from structlog.stdlib import BoundLogger

from src.utils.config import Config, load_config


def setup_logging(config: Optional[Config] = None) -> BoundLogger:
    """
    Set up logging configuration with both file and console handlers.
    
    Args:
        config: Optional configuration object. If not provided, will be loaded.
        
    Returns:
        BoundLogger: Configured structured logger instance.
    """
    if config is None:
        config = load_config()
    
    # Ensure log directory exists
    log_dir = config.log_file.parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=config.log_level,
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Set up file handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        filename=config.log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(logging.Formatter("%(message)s"))
    
    # Add file handler to root logger
    logging.getLogger().addHandler(file_handler)
    
    # Create and return a bound logger
    logger = structlog.get_logger("daily_digest")
    
    # Log initial configuration
    logger.info(
        "logging_initialized",
        log_level=config.log_level,
        log_file=str(config.log_file),
        environment=config.env,
    )
    return logger

def get_logger(name: str) -> BoundLogger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name, typically __name__ of the calling module.
        
    Returns:
        BoundLogger: Configured logger instance.
    """
    return structlog.get_logger(name)


class LoggerContext:
    """Context manager for adding temporary context to loggers."""
    
    def __init__(self, logger: BoundLogger, **context: Any):
        """
        Initialize logger context.
        
        Args:
            logger: Logger instance to add context to.
            **context: Key-value pairs to add to logging context.
        """
        self.logger = logger
        self.context = context
        self.old_context: Dict[str, Any] = {}
    
    def __enter__(self) -> BoundLogger:
        """Add context to logger."""
        # Store old context
        self.old_context = self.logger._context.copy()
        # Add new context
        self.logger = self.logger.bind(**self.context)
        return self.logger
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Restore old context."""
        # Restore old context
        self.logger = self.logger.bind(**self.old_context)


# Create default logger instance
logger = get_logger(__name__) 