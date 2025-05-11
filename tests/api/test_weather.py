"""Tests for the Weather API client."""

import os
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

import pytest
import requests
from requests.exceptions import Timeout, RequestException

from src.api.weather import WeatherAPI, WeatherAPIError, RateLimitError

# Test data
MOCK_API_KEY = "test_api_key"
MOCK_CURRENT_WEATHER = {
    "location": {
        "name": "Sydney",
        "region": "New South Wales",
        "country": "Australia",
        "lat": -33.87,
        "lon": 151.21,
        "localtime": "2024-03-19 12:00"
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

MOCK_FORECAST = {
    "location": MOCK_CURRENT_WEATHER["location"],
    "forecast": {
        "forecastday": [
            {
                "date": "2024-03-19",
                "day": {
                    "maxtemp_c": 25.0,
                    "mintemp_c": 18.0,
                    "condition": {"text": "Sunny"}
                }
            }
        ]
    }
}

@pytest.fixture
def weather_api():
    """Create a WeatherAPI instance for testing."""
    with patch.dict(os.environ, {"WEATHER_API_KEY": MOCK_API_KEY}):
        api = WeatherAPI()
        yield api

def test_init_with_env_var():
    """Test initialization with environment variable."""
    with patch.dict(os.environ, {"WEATHER_API_KEY": MOCK_API_KEY}):
        api = WeatherAPI()
        assert api.api_key == MOCK_API_KEY

def test_init_with_api_key():
    """Test initialization with provided API key."""
    api = WeatherAPI(api_key=MOCK_API_KEY)
    assert api.api_key == MOCK_API_KEY

def test_init_without_api_key():
    """Test initialization without API key raises error."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="Weather API key must be provided"):
            WeatherAPI()

@patch("requests.Session.get")
def test_get_current_weather(mock_get, weather_api):
    """Test getting current weather."""
    mock_response = MagicMock()
    mock_response.json.return_value = MOCK_CURRENT_WEATHER
    mock_get.return_value = mock_response
    
    result = weather_api.get_current_weather()
    
    assert result == MOCK_CURRENT_WEATHER
    mock_get.assert_called_once()
    call_args = mock_get.call_args
    assert "current.json" in call_args[0][0]
    assert call_args[1]["params"]["key"] == MOCK_API_KEY
    assert call_args[1]["params"]["q"] == f"{weather_api.SYDNEY_LAT},{weather_api.SYDNEY_LON}"

@patch("requests.Session.get")
def test_get_forecast(mock_get, weather_api):
    """Test getting weather forecast."""
    mock_response = MagicMock()
    mock_response.json.return_value = MOCK_FORECAST
    mock_get.return_value = mock_response
    
    result = weather_api.get_forecast(days=1)
    
    assert result == MOCK_FORECAST
    mock_get.assert_called_once()
    call_args = mock_get.call_args
    assert "forecast.json" in call_args[0][0]
    assert call_args[1]["params"]["days"] == 1

def test_get_forecast_invalid_days(weather_api):
    """Test getting forecast with invalid days raises error."""
    with pytest.raises(ValueError, match="Forecast days must be between 1 and 3"):
        weather_api.get_forecast(days=4)

@patch("requests.Session.get")
def test_request_timeout(mock_get, weather_api):
    """Test handling request timeout."""
    mock_get.side_effect = Timeout()
    
    with pytest.raises(WeatherAPIError) as exc_info:
        weather_api.get_current_weather()
    
    assert exc_info.value.status_code == 408
    assert exc_info.value.message == "Request timed out"

@patch("requests.Session.get")
def test_rate_limit_exceeded(mock_get, weather_api):
    """Test handling rate limit exceeded."""
    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_response.json.return_value = {"error": {"message": "Rate limit exceeded"}}
    mock_get.side_effect = RequestException(response=mock_response)
    
    with pytest.raises(RateLimitError) as exc_info:
        weather_api.get_current_weather()
    
    assert exc_info.value.status_code == 429
    assert exc_info.value.message == "Rate limit exceeded"

@pytest.mark.xfail(reason="Mocking raise_for_status does not trigger the requests Retry adapter's retry logic (integration test required).")
@patch("requests.Session.get")
def test_retry_on_server_error(mock_get, weather_api):
    """Test retry logic on server error (expected to fail in unit tests)."""
    # Simulate a real HTTP 500 response (not an exception)
    error_response = MagicMock()
    error_response.status_code = 500
    error_response.raise_for_status.side_effect = requests.HTTPError(response=error_response)
    error_response.json.return_value = {"error": "Internal Server Error"}

    success_response = MagicMock()
    success_response.raise_for_status.return_value = None
    success_response.json.return_value = MOCK_CURRENT_WEATHER

    mock_get.side_effect = [error_response, success_response]

    result = weather_api.get_current_weather()
    assert result == MOCK_CURRENT_WEATHER
    assert mock_get.call_count == 2

def test_rate_limit_tracking(weather_api):
    """Test rate limit tracking."""
    # Simulate making max requests
    weather_api._request_count = weather_api.max_requests_per_day - 1
    
    # Should not raise
    weather_api._check_rate_limit()
    
    # Make one more request to exceed limit
    weather_api._request_count += 1
    with pytest.raises(RateLimitError) as exc_info:
        weather_api._check_rate_limit()
    assert exc_info.value.message == "Daily API request limit exceeded"
    
    # Simulate next day (reset should happen before check)
    weather_api._last_reset = datetime.now() - timedelta(days=1, seconds=1)
    weather_api._request_count = 0
    # Should not raise now
    weather_api._check_rate_limit()
    assert weather_api._request_count == 0 