"""Tests for the error handling system."""

import time
from unittest.mock import patch

import pytest

from src.utils.exceptions import (
    APIError,
    ConfigurationError,
    DailyDigestError,
    EmailError,
    MotionAPIError,
    ValidationError,
    WeatherAPIError,
    handle_error,
    retry_on_error,
)


def test_daily_digest_error_creation():
    """Test creation of base error with all attributes."""
    error = DailyDigestError(
        message="Test error",
        error_code="TEST_ERROR",
        details={"key": "value"},
        cause=ValueError("Original error"),
    )
    
    assert str(error) == "Test error"
    assert error.message == "Test error"
    assert error.error_code == "TEST_ERROR"
    assert error.details == {"key": "value"}
    assert isinstance(error.cause, ValueError)
    assert str(error.cause) == "Original error"


def test_configuration_error():
    """Test creation of configuration error."""
    error = ConfigurationError(
        message="Invalid config",
        details={"missing_key": "api_key"},
    )
    
    assert str(error) == "Invalid config"
    assert error.error_code == "CONFIG_ERROR"
    assert error.details == {"missing_key": "api_key"}


def test_api_error():
    """Test creation of API error."""
    error = APIError(
        message="API failed",
        api_name="test",
        status_code=500,
        details={"endpoint": "/test"},
    )
    
    assert str(error) == "API failed"
    assert error.error_code == "TEST_API_ERROR"
    assert error.details == {
        "api_name": "test",
        "status_code": 500,
        "endpoint": "/test",
    }


def test_motion_api_error():
    """Test creation of Motion API error."""
    error = MotionAPIError(
        message="Motion API failed",
        status_code=429,
        details={"rate_limit": "exceeded"},
    )
    
    assert str(error) == "Motion API failed"
    assert error.error_code == "MOTION_API_ERROR"
    assert error.details == {
        "api_name": "motion",
        "status_code": 429,
        "rate_limit": "exceeded",
    }


def test_weather_api_error():
    """Test creation of Weather API error."""
    error = WeatherAPIError(
        message="Weather API failed",
        status_code=404,
        details={"location": "unknown"},
    )
    
    assert str(error) == "Weather API failed"
    assert error.error_code == "WEATHER_API_ERROR"
    assert error.details == {
        "api_name": "weather",
        "status_code": 404,
        "location": "unknown",
    }


def test_email_error():
    """Test creation of email error."""
    error = EmailError(
        message="Failed to send email",
        details={"recipient": "test@example.com"},
    )
    
    assert str(error) == "Failed to send email"
    assert error.error_code == "EMAIL_ERROR"
    assert error.details == {"recipient": "test@example.com"}


def test_validation_error():
    """Test creation of validation error."""
    error = ValidationError(
        message="Invalid input",
        field="email",
        details={"value": "invalid-email"},
    )
    
    assert str(error) == "Invalid input"
    assert error.error_code == "VALIDATION_ERROR"
    assert error.details == {
        "field": "email",
        "value": "invalid-email",
    }


def test_handle_error_with_daily_digest_error():
    """Test handling of DailyDigestError."""
    original_error = DailyDigestError(
        message="Original error",
        error_code="ORIGINAL_ERROR",
    )
    
    handled_error = handle_error(
        original_error,
        context={"additional": "context"},
    )
    
    assert handled_error is original_error
    assert handled_error.details == {"additional": "context"}


def test_handle_error_with_standard_exceptions():
    """Test handling of standard exceptions."""
    # Test ValueError -> ValidationError
    error = handle_error(ValueError("Invalid value"))
    assert isinstance(error, ValidationError)
    assert str(error) == "Invalid value"
    
    # Test KeyError -> ConfigurationError
    error = handle_error(KeyError("missing_key"))
    assert isinstance(error, ConfigurationError)
    assert str(error) == "'missing_key'"
    
    # Test unknown exception -> DailyDigestError
    error = handle_error(Exception("Unknown error"))
    assert isinstance(error, DailyDigestError)
    assert str(error) == "Unknown error"


def test_retry_on_error_success():
    """Test retry decorator with successful retry."""
    attempts = 0
    
    @retry_on_error(max_attempts=3, delay=0.1)
    def failing_function():
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            raise ValueError("Temporary error")
        return "success"
    
    result = failing_function()
    assert result == "success"
    assert attempts == 2


def test_retry_on_error_max_attempts():
    """Test retry decorator with max attempts exceeded."""
    attempts = 0
    
    @retry_on_error(max_attempts=3, delay=0.1)
    def always_failing_function():
        nonlocal attempts
        attempts += 1
        raise ValueError("Persistent error")
    
    with pytest.raises(ValidationError) as exc_info:
        always_failing_function()
    
    assert str(exc_info.value) == "Persistent error"
    assert attempts == 3


def test_retry_on_error_specific_exceptions():
    """Test retry decorator with specific exceptions."""
    attempts = 0
    
    @retry_on_error(
        max_attempts=3,
        delay=0.1,
        exceptions=(ValueError,),
    )
    def function_with_different_errors():
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise ValueError("Retry this")
        raise TypeError("Don't retry this")
    
    with pytest.raises(TypeError) as exc_info:
        function_with_different_errors()
    
    assert str(exc_info.value) == "Don't retry this"
    assert attempts == 2


def test_retry_on_error_logging():
    """Test retry decorator logging."""
    with patch("src.utils.exceptions.logger") as mock_logger:
        attempts = 0
        
        @retry_on_error(max_attempts=3, delay=0.1)
        def failing_function():
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise ValueError("Temporary error")
            return "success"
        
        failing_function()
        
        # Verify warning logs for retries
        assert mock_logger.warning.call_count == 2
        for call in mock_logger.warning.call_args_list:
            assert call[1]["function"] == "failing_function"
            assert "attempt" in call[1]
            assert "max_attempts" in call[1]
            assert "delay" in call[1]
            assert "error" in call[1] 