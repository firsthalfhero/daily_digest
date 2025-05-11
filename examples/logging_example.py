"""Example usage of the logging system."""

import time
from pathlib import Path

from src.utils.config import load_config
from src.utils.logging import LoggerContext, get_logger, setup_logging


def main():
    """Demonstrate logging features."""
    # Load configuration
    config = load_config()
    
    # Set up logging
    logger = setup_logging(config)
    
    # Basic logging
    logger.info("application_started")
    
    # Logging with context
    logger.info(
        "user_action",
        user_id="123",
        action="login",
        ip_address="192.168.1.1",
    )
    
    # Using LoggerContext for temporary context
    with LoggerContext(logger, request_id="req-123", user_id="456"):
        logger.info("processing_request")
        logger.debug("request_details", data={"key": "value"})
        
        # Simulate some work
        time.sleep(0.1)
        
        logger.info("request_completed", duration_ms=100)
    
    # Logging exceptions
    try:
        # Simulate an error
        raise ValueError("Invalid input")
    except ValueError as e:
        logger.exception(
            "error_occurred",
            error_type="validation_error",
            details=str(e),
        )
    
    # Logging with different levels
    logger.debug("debug_message", data={"debug": True})
    logger.info("info_message", data={"info": True})
    logger.warning("warning_message", data={"warning": True})
    logger.error("error_message", data={"error": True})
    logger.critical("critical_message", data={"critical": True})
    
    # Logging with structured data
    logger.info(
        "complex_event",
        event_type="user_interaction",
        user={
            "id": "789",
            "name": "John Doe",
            "preferences": {
                "theme": "dark",
                "notifications": True,
            },
        },
        action={
            "type": "click",
            "target": "button",
            "timestamp": time.time(),
        },
    )
    
    logger.info("application_shutdown")


if __name__ == "__main__":
    main() 