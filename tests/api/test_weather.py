"""Tests for the Weather API client."""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest
import requests
from requests.exceptions import RequestException

from src.api.weather import WeatherAPI
from src.utils.config import WeatherAPIConfig
from src.utils.exceptions import WeatherAPIError


@pytest.fixture
def api_config():
    """Create a test API configuration."""
    return WeatherAPIConfig(
        weather_api_key="test_api_key",
        weather_api_url="https://api.weatherapi.com/v1",
    )


@pytest.fixture
def client(api_config):
    """Create a Weather API client with mocked session."""
    with patch("requests.Session") as mock_session:
        mock_session.return_value.headers = {}
        client = WeatherAPI(api_config)
        client.session = mock_session.return_value
        yield client


def test_init_with_valid_config(api_config):
    """Test initializing with valid configuration."""
    client = WeatherAPI(api_config)
    assert client.config == api_config
    assert client.timeout == 10
    assert client.max_requests_per_day == 1000


def test_init_with_custom_settings(api_config):
    """Test initializing with custom settings."""
    client = WeatherAPI(
        api_config,
        timeout=20,
        max_retries=5,
        initial_retry_delay=10,
        max_requests_per_day=500
    )
    assert client.timeout == 20
    assert client.max_requests_per_day == 500


def test_get_current_weather(client):
    """Test getting current weather."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "location": {
            "name": "Sydney",
            "region": "New South Wales",
            "country": "Australia",
            "lat": -33.87,
            "lon": 151.21,
            "localtime": "2024-03-20 10:00"
        },
        "current": {
            "temp_c": 22.0,
            "condition": {
                "text": "Sunny",
                "icon": "113"
            },
            "wind_kph": 15.0,
            "humidity": 65,
            "feelslike_c": 23.0
        }
    }
    mock_response.status_code = 200
    client.session.get.return_value = mock_response

    result = client.get_current_weather()
    assert result == mock_response.json.return_value
    client.session.get.assert_called_once()
    call_args = client.session.get.call_args
    assert "current.json" in call_args[0][0]
    assert call_args[1]["params"]["q"] == f"{client.SYDNEY_LAT},{client.SYDNEY_LON}"


def test_get_forecast(client):
    """Test getting weather forecast."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "forecast": {
            "forecastday": [
                {
                    "date": "2024-03-20",
                    "day": {
                        "maxtemp_c": 25.0,
                        "mintemp_c": 18.0,
                        "condition": {
                            "text": "Sunny",
                            "icon": "113"
                        }
                    }
                }
            ]
        }
    }
    mock_response.status_code = 200
    client.session.get.return_value = mock_response

    result = client.get_forecast(days=1)
    assert result == mock_response.json.return_value
    client.session.get.assert_called_once()
    call_args = client.session.get.call_args
    assert "forecast.json" in call_args[0][0]
    assert call_args[1]["params"]["days"] == 1


def test_get_forecast_invalid_days(client):
    """Test getting forecast with invalid days."""
    with pytest.raises(ValueError, match="Forecast days must be between 1 and 3"):
        client.get_forecast(days=4)


def test_get_weather_alerts(client):
    """Test getting weather alerts."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "alerts": {
            "alert": [
                {
                    "headline": "Severe Weather Warning",
                    "msgtype": "Alert",
                    "severity": "Moderate",
                    "urgency": "Expected",
                    "areas": "Sydney Metropolitan",
                    "category": "Met",
                    "certainty": "Likely",
                    "event": "Severe Thunderstorm Warning",
                    "note": "The Bureau of Meteorology warns of severe thunderstorms.",
                    "effective": "2024-03-20T10:00:00+10:00",
                    "expires": "2024-03-20T16:00:00+10:00",
                    "desc": "Severe thunderstorms are likely to produce damaging winds and heavy rainfall.",
                    "instruction": "People in affected areas should take shelter."
                }
            ]
        }
    }
    mock_response.status_code = 200
    client.session.get.return_value = mock_response

    result = client.get_weather_alerts()
    assert result == mock_response.json.return_value
    client.session.get.assert_called_once()
    call_args = client.session.get.call_args
    assert "alerts.json" in call_args[0][0]


def test_api_error_handling(client):
    """Test handling of API errors."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "error": {
            "code": 1006,
            "message": "No location found"
        }
    }
    mock_response.status_code = 400
    client.session.get.return_value = mock_response

    with pytest.raises(WeatherAPIError) as exc_info:
        client.get_current_weather()
    assert exc_info.value.status_code == 400
    assert "No location found" in str(exc_info.value)


def test_rate_limit_handling(client):
    """Test handling of rate limits."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "error": {
            "code": 429,
            "message": "API rate limit exceeded"
        }
    }
    mock_response.status_code = 429
    client.session.get.return_value = mock_response

    with pytest.raises(WeatherAPIError) as exc_info:
        client.get_current_weather()
    assert exc_info.value.status_code == 429
    assert "API rate limit exceeded" in str(exc_info.value)


def test_request_exception_handling(client):
    """Test handling of request exceptions."""
    client.session.get.side_effect = RequestException("Connection error")

    with pytest.raises(WeatherAPIError) as exc_info:
        client.get_current_weather()
    assert "Connection error" in str(exc_info.value)
    assert exc_info.value.status_code is None 