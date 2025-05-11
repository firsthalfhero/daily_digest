"""Tests for the Motion API client."""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest
import requests
from requests.exceptions import RequestException

from src.api.motion import MotionClient
from src.utils.config import APIConfig
from src.utils.exceptions import MotionAPIError


@pytest.fixture
def api_config():
    """Create a test API configuration."""
    return APIConfig(
        motion_api_key="test_api_key",
        motion_api_url="https://api.motion.dev/v1",
        weather_api_key="test_weather_key",
        weather_api_url="https://api.weatherapi.com/v1",
    )


@pytest.fixture
def client(api_config):
    """Create a Motion API client with mocked session."""
    with patch("requests.Session") as mock_session:
        mock_session.return_value.headers = {}
        client = MotionClient(api_config)
        client.session = mock_session.return_value
        yield client


def test_init_sets_headers(api_config):
    """Test that client initialization sets correct headers."""
    with patch("requests.Session") as mock_session:
        mock_session.return_value.headers = {}
        client = MotionClient(api_config)
        
        assert client.session.headers["Authorization"] == f"Bearer {api_config.motion_api_key}"
        assert client.session.headers["Content-Type"] == "application/json"
        assert client.session.headers["Accept"] == "application/json"


def test_get_calendars_success(client):
    """Test successful calendar retrieval."""
    # Mock response
    mock_response = Mock()
    mock_response.json.return_value = {
        "calendars": [
            {"id": "1", "name": "Work"},
            {"id": "2", "name": "Personal"},
        ]
    }
    client.session.request.return_value = mock_response
    
    # Call the method
    calendars = client.get_calendars()
    
    # Verify request
    client.session.request.assert_called_once_with(
        method="GET",
        url="https://api.motion.dev/v1/calendars",
        params=None,
        json=None,
        timeout=10.0,
    )
    
    # Verify response
    assert len(calendars) == 2
    assert calendars[0]["id"] == "1"
    assert calendars[0]["name"] == "Work"
    assert calendars[1]["id"] == "2"
    assert calendars[1]["name"] == "Personal"


def test_get_calendar_events_success(client):
    """Test successful event retrieval."""
    # Mock response
    mock_response = Mock()
    mock_response.json.return_value = {
        "events": [
            {
                "id": "1",
                "title": "Meeting",
                "start": "2024-03-20T10:00:00Z",
                "end": "2024-03-20T11:00:00Z",
            }
        ]
    }
    client.session.request.return_value = mock_response
    
    # Test parameters
    start_date = datetime(2024, 3, 20)
    end_date = start_date + timedelta(days=1)
    calendar_id = "work"
    
    # Call the method
    events = client.get_calendar_events(
        start_date=start_date,
        end_date=end_date,
        calendar_id=calendar_id,
    )
    
    # Verify request
    client.session.request.assert_called_once_with(
        method="GET",
        url="https://api.motion.dev/v1/events",
        params={
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "calendar_id": calendar_id,
        },
        json=None,
        timeout=10.0,
    )
    
    # Verify response
    assert len(events) == 1
    assert events[0]["id"] == "1"
    assert events[0]["title"] == "Meeting"


def test_get_calendar_events_default_end_date(client):
    """Test event retrieval with default end date."""
    # Mock response
    mock_response = Mock()
    mock_response.json.return_value = {"events": []}
    client.session.request.return_value = mock_response
    
    # Test parameters
    start_date = datetime(2024, 3, 20)
    
    # Call the method
    client.get_calendar_events(start_date=start_date)
    
    # Verify request
    expected_end_date = start_date + timedelta(days=1)
    client.session.request.assert_called_once_with(
        method="GET",
        url="https://api.motion.dev/v1/events",
        params={
            "start": start_date.isoformat(),
            "end": expected_end_date.isoformat(),
        },
        json=None,
        timeout=10.0,
    )


def test_api_error_handling(client):
    """Test API error handling."""
    # Mock failed request
    mock_response = Mock()
    mock_response.status_code = 429
    mock_response.json.return_value = {"error": "Rate limit exceeded"}
    http_error = requests.exceptions.HTTPError()
    http_error.response = mock_response  # Attach the mock response
    mock_response.raise_for_status.side_effect = http_error
    
    client.session.request.return_value = mock_response
    
    # Test that the error is converted to MotionAPIError
    with pytest.raises(MotionAPIError) as exc_info:
        client.get_calendars()
    
    error = exc_info.value
    assert error.status_code == 429
    assert "Rate limit exceeded" in str(error)
    # Check that error.details contains the expected keys and values
    assert error.details["error"] == "Rate limit exceeded"
    assert error.details["api_name"] == "motion"
    assert error.details["status_code"] == 429


def test_network_error_handling(client):
    """Test network error handling."""
    # Mock network error
    client.session.request.side_effect = RequestException("Connection failed")
    
    # Test that the error is converted to MotionAPIError
    with pytest.raises(MotionAPIError) as exc_info:
        client.get_calendars()
    
    error = exc_info.value
    assert "Connection failed" in str(error)
    assert error.status_code is None


def test_rate_limiting(client):
    """Test that rate limiting is enforced."""
    # Mock response
    mock_response = Mock()
    mock_response.json.return_value = {"calendars": []}
    client.session.request.return_value = mock_response
    
    # Make multiple requests
    with patch("time.sleep") as mock_sleep:
        client.get_calendars()
        client.get_calendars()
        client.get_calendars()
        
        # Verify that sleep was called to enforce rate limiting
        assert mock_sleep.call_count == 2  # Should sleep between requests 