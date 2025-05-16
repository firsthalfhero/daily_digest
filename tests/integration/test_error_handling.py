"""Integration tests for error handling in real scenarios."""

import pytest
from unittest.mock import patch, MagicMock

from src.utils.exceptions import (
    MotionAPIError,
    WeatherAPIError,
    EmailError,
    handle_error,
    retry_on_error,
)
from src.api.motion import MotionClient
from src.api.weather import WeatherClient
from src.digest_email.sender import EmailSender


@pytest.fixture
def mock_motion_client():
    """Create a mock Motion client for testing."""
    client = MagicMock(spec=MotionClient)
    return client


@pytest.fixture
def mock_weather_client():
    """Create a mock Weather client for testing."""
    client = MagicMock(spec=WeatherClient)
    return client


@pytest.fixture
def mock_email_sender():
    """Create a mock email sender for testing."""
    sender = MagicMock(spec=EmailSender)
    return sender


def test_motion_api_error_handling(mock_motion_client):
    """Test error handling when Motion API fails."""
    # Simulate API failure
    mock_motion_client.get_calendar_events.side_effect = MotionAPIError(
        message="Rate limit exceeded",
        status_code=429,
        details={"rate_limit": "exceeded"},
    )
    
    # Attempt to get calendar events
    with pytest.raises(MotionAPIError) as exc_info:
        mock_motion_client.get_calendar_events()
    
    # Verify error details
    error = exc_info.value
    assert error.error_code == "MOTION_API_ERROR"
    assert error.status_code == 429
    assert error.details["rate_limit"] == "exceeded"


def test_weather_api_error_handling(mock_weather_client):
    """Test error handling when Weather API fails."""
    # Simulate API failure
    mock_weather_client.get_weather.side_effect = WeatherAPIError(
        message="Location not found",
        status_code=404,
        details={"location": "unknown"},
    )
    
    # Attempt to get weather data
    with pytest.raises(WeatherAPIError) as exc_info:
        mock_weather_client.get_weather("Sydney")
    
    # Verify error details
    error = exc_info.value
    assert error.error_code == "WEATHER_API_ERROR"
    assert error.status_code == 404
    assert error.details["location"] == "unknown"


def test_email_error_handling(mock_email_sender):
    """Test error handling when email delivery fails."""
    # Simulate email failure
    mock_email_sender.send_email.side_effect = EmailError(
        message="Failed to send email",
        details={"recipient": "test@example.com"},
    )
    
    # Attempt to send email
    with pytest.raises(EmailError) as exc_info:
        mock_email_sender.send_email(
            subject="Test",
            body="Test email",
            recipient="test@example.com",
        )
    
    # Verify error details
    error = exc_info.value
    assert error.error_code == "EMAIL_ERROR"
    assert error.details["recipient"] == "test@example.com"


def test_retry_on_error_integration(mock_motion_client):
    """Test retry mechanism in a real API scenario."""
    attempts = 0
    
    def mock_api_call():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise MotionAPIError(
                message="Temporary API error",
                status_code=503,
                details={"attempt": attempts},
            )
        return {"events": []}
    
    mock_motion_client.get_calendar_events.side_effect = mock_api_call
    
    # Call with retry decorator
    @retry_on_error(max_attempts=3, delay=0.1)
    def get_events():
        return mock_motion_client.get_calendar_events()
    
    result = get_events()
    assert result == {"events": []}
    assert attempts == 3


def test_error_handling_with_context(mock_motion_client):
    """Test error handling with additional context."""
    # Simulate API failure with context
    mock_motion_client.get_calendar_events.side_effect = MotionAPIError(
        message="API error",
        status_code=500,
        details={"endpoint": "/events"},
    )
    
    try:
        mock_motion_client.get_calendar_events()
    except Exception as e:
        # Add context to the error
        error = handle_error(e, context={"user_id": "123", "action": "get_events"})
        assert error.details["user_id"] == "123"
        assert error.details["action"] == "get_events"
        assert error.details["endpoint"] == "/events"


def test_error_propagation(mock_motion_client, mock_weather_client):
    """Test error propagation through multiple service calls."""
    # Simulate Motion API failure
    mock_motion_client.get_calendar_events.side_effect = MotionAPIError(
        message="Motion API unavailable",
        status_code=503,
    )
    
    # Simulate Weather API failure
    mock_weather_client.get_weather.side_effect = WeatherAPIError(
        message="Weather API unavailable",
        status_code=503,
    )
    
    def generate_digest():
        try:
            events = mock_motion_client.get_calendar_events()
            weather = mock_weather_client.get_weather("Sydney")
            return {"events": events, "weather": weather}
        except Exception as e:
            # Handle and propagate the first error
            raise handle_error(e, context={"stage": "digest_generation"})
    
    # Verify that the first error (Motion API) is propagated
    with pytest.raises(MotionAPIError) as exc_info:
        generate_digest()
    
    error = exc_info.value
    assert error.error_code == "MOTION_API_ERROR"
    assert error.details["stage"] == "digest_generation" 