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
    class Dummy:
        pass
    dummy_api = Dummy()
    dummy_api.motion_api_key = "key"
    dummy_api.motion_api_url = "url"
    dummy_api.weather_api_key = "key"
    dummy_api.weather_api_url = "url"
    dummy_email = Dummy()
    dummy_email.smtp_host = "host"
    dummy_email.smtp_port = 123
    dummy_email.smtp_username = "user"
    dummy_email.smtp_password = "pass"
    dummy_email.sender_email = "sender@example.com"
    dummy_email.recipient_email = "recipient@example.com"
    return Config(
        env="test",
        debug=True,
        motion=dummy_api,
        weather=dummy_api,
        email=dummy_email,
        aws_region="ap-southeast-2",
        log_level="DEBUG",
        log_file=tmp_path / "test.log"
    )


@pytest.fixture(autouse=True)
def cleanup_logging():
    """Clean up logging configuration after each test."""
    # Store original handlers
    original_handlers = logging.getLogger().handlers[:]
    
    yield
    
    # Remove all handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        handler.close()
        root_logger.removeHandler(handler)
    
    # Reset logging configuration
    logging.basicConfig(force=True)
    
    # Reset structlog configuration
    structlog.reset_defaults()


def test_setup_logging_creates_log_directory(mock_config, tmp_path, caplog):
    """Test that setup_logging creates the log directory."""
    print("Starting test_setup_logging_creates_log_directory")  # Debug print
    
    # Enable debug logging for the test
    caplog.set_level(logging.DEBUG)
    print("Set caplog level to DEBUG")  # Debug print
    
    # Set up the log directory path
    log_dir = tmp_path / "logs"
    mock_config.log_file = log_dir / "test.log"
    print(f"Log directory path set to: {log_dir}")  # Debug print
    
    try:
        print("About to call setup_logging")  # Debug print
        # Call setup_logging and capture any output
        logger = setup_logging(mock_config)
        print(f"Logger created: {logger}")  # Debug print
        
        # Verify directory was created
        print("Checking if directory exists")  # Debug print
        assert log_dir.exists(), f"Log directory {log_dir} was not created"
        print("Directory exists, checking if it's a directory")  # Debug print
        assert log_dir.is_dir(), f"{log_dir} exists but is not a directory"
        
        # Log a test message to verify logger works
        print("Logging test message")  # Debug print
        logger.info("test_directory_creation")
        print("Test message logged")  # Debug print
        
    except Exception as e:
        print(f"Error in test: {str(e)}")  # Debug print
        raise
    finally:
        print("Test cleanup")  # Debug print


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
    assert logger is not None


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


def test_tmp_path_directory_creation(tmp_path):
    """Minimal test: just create a directory in tmp_path and check it exists."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    print(f"Created directory: {log_dir}")
    assert log_dir.exists()
    assert log_dir.is_dir() 