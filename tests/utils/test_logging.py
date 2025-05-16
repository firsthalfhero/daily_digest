"""Tests for the logging module."""

import json
import logging
import os
from pathlib import Path
from unittest.mock import patch

import pytest
import structlog
from structlog.stdlib import BoundLogger

from src.utils.config import Config
from src.utils.logging import LoggerContext, get_logger, setup_logging


@pytest.fixture
def mock_config(tmp_path):
    """Create a mock configuration for testing."""
    return Config(
        env="test",
        debug=True,
        motion=Config.APIConfig(
            motion_api_key="test",
            motion_api_url="https://api.motion.dev/v1",
            weather_api_key="test",
            weather_api_url="https://api.weatherapi.com/v1",
        ),
        email=Config.EmailConfig(
            smtp_host="smtp.test.com",
            smtp_port=587,
            smtp_username="test",
            smtp_password="test",
            sender_email="test@example.com",
            recipient_email="user@example.com",
        ),
        aws_region="ap-southeast-2",
        log_level="DEBUG",
        log_file=tmp_path / "test.log",
    )


def test_setup_logging_creates_log_directory(mock_config, tmp_path):
    """Test that setup_logging creates the log directory."""
    log_dir = tmp_path / "logs"
    mock_config.log_file = log_dir / "test.log"
    
    setup_logging(mock_config)
    
    assert log_dir.exists()
    assert log_dir.is_dir()


def test_setup_logging_creates_log_file(mock_config, tmp_path):
    """Test that setup_logging creates the log file."""
    logger = setup_logging(mock_config)
    logger.info("test_message")
    
    assert mock_config.log_file.exists()
    assert mock_config.log_file.is_file()
    
    # Verify log content
    log_content = mock_config.log_file.read_text()
    assert "test_message" in log_content
    assert "logging_initialized" in log_content


def test_log_rotation(mock_config, tmp_path):
    """Test that log rotation works."""
    # Create a small maxBytes to trigger rotation
    with patch("logging.handlers.RotatingFileHandler") as mock_handler:
        mock_handler.return_value.maxBytes = 100
        
        logger = setup_logging(mock_config)
        
        # Write enough logs to trigger rotation
        for i in range(10):
            logger.info("test_message", number=i, data="x" * 50)
        
        # Verify that rotation was called
        assert mock_handler.called


def test_get_logger_returns_bound_logger():
    """Test that get_logger returns a BoundLogger instance."""
    logger = get_logger("test_logger")
    assert isinstance(logger, BoundLogger)


def test_logger_context():
    """Test the LoggerContext context manager."""
    logger = get_logger("test_context")
    
    # Log without context
    logger.info("no_context")
    
    # Log with context
    with LoggerContext(logger, user_id="123", action="test"):
        logger.info("with_context")
    
    # Log without context again
    logger.info("no_context_again")


def test_structured_logging(mock_config, tmp_path):
    """Test that logs are properly structured in JSON format."""
    logger = setup_logging(mock_config)
    
    # Log with structured data
    logger.info(
        "test_event",
        user_id="123",
        action="test",
        data={"key": "value"},
    )
    
    # Read and parse log file
    log_content = mock_config.log_file.read_text()
    log_lines = log_content.strip().split("\n")
    
    # Find our test event
    test_event = None
    for line in log_lines:
        try:
            event = json.loads(line)
            if event.get("event") == "test_event":
                test_event = event
                break
        except json.JSONDecodeError:
            continue
    
    assert test_event is not None
    assert test_event["user_id"] == "123"
    assert test_event["action"] == "test"
    assert test_event["data"] == {"key": "value"}
    assert "timestamp" in test_event
    assert "logger" in test_event
    assert "level" in test_event


def test_log_levels(mock_config, tmp_path):
    """Test that different log levels work correctly."""
    logger = setup_logging(mock_config)
    
    # Test all log levels
    logger.debug("debug_message")
    logger.info("info_message")
    logger.warning("warning_message")
    logger.error("error_message")
    logger.critical("critical_message")
    
    # Read log file
    log_content = mock_config.log_file.read_text()
    
    # Verify all messages are present
    assert "debug_message" in log_content
    assert "info_message" in log_content
    assert "warning_message" in log_content
    assert "error_message" in log_content
    assert "critical_message" in log_content


def test_exception_logging(mock_config, tmp_path):
    """Test that exceptions are properly logged with traceback."""
    logger = setup_logging(mock_config)
    
    try:
        raise ValueError("test exception")
    except ValueError:
        logger.exception("exception_occurred")
    
    # Read log file
    log_content = mock_config.log_file.read_text()
    
    # Verify exception details
    assert "exception_occurred" in log_content
    assert "ValueError: test exception" in log_content
    assert "Traceback" in log_content 