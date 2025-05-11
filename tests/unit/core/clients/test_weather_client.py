"""
Tests for the Weather API client implementation.
"""
import pytest
import responses
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from src.core.clients.weather_client import WeatherAPIClient
from src.core.utils.exceptions import WeatherAPIError, RateLimitError, ValidationError

@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    with patch('src.core.clients.weather_client.get_config') as mock:
        mock.return_value = {
            'WEATHER_API_KEY': 'test-key',
            'WEATHER_API_BASE_URL': 'https://api.weather.test',
            'WEATHER_API_RATE_LIMIT': 1000,
            'WEATHER_API_TIMEOUT': 10
        }
        yield mock

@pytest.fixture
def client(mock_config):
    """Create a test client instance."""
    return WeatherAPIClient()

@pytest.fixture
def mock_responses():
    """Mock responses for API calls."""
    with responses.RequestsMock() as rsps:
        yield rsps

def test_client_initialization(mock_config):
    """Test client initialization with config."""
    client = WeatherAPIClient()
    assert client.api_key == 'test-key'
    assert client.base_url == 'https://api.weather.test'
    assert client.rate_limit == 1000
    assert client.request_timeout == 10

def test_client_initialization_with_params():
    """Test client initialization with explicit parameters."""
    client = WeatherAPIClient(
        api_key='custom-key',
        base_url='https://custom.api.test'
    )
    assert client.api_key == 'custom-key'
    assert client.base_url == 'https://custom.api.test'

def test_client_initialization_missing_config(mock_config):
    """Test client initialization with missing config."""
    mock_config.return_value = {}
    with pytest.raises(ValidationError) as exc:
        WeatherAPIClient()
    assert "Weather API key is required" in str(exc.value)

@responses.activate
def test_get_current_weather_success(client):
    """Test successful current weather retrieval."""
    responses.add(
        responses.GET,
        'https://api.weather.test/current',
        json={'temperature': 25, 'humidity': 60},
        status=200
    )
    
    data = client.get_current_weather(-33.8688, 151.2093)
    assert data == {'temperature': 25, 'humidity': 60}
    assert len(responses.calls) == 1
    assert 'lat=-33.8688' in responses.calls[0].request.url
    assert 'lon=151.2093' in responses.calls[0].request.url

@responses.activate
def test_get_current_weather_invalid_coordinates(client):
    """Test current weather retrieval with invalid coordinates."""
    with pytest.raises(ValidationError) as exc:
        client.get_current_weather(200, 151.2093)
    assert "Latitude must be between -90 and 90" in str(exc.value)
    
    with pytest.raises(ValidationError) as exc:
        client.get_current_weather(-33.8688, 400)
    assert "Longitude must be between -180 and 180" in str(exc.value)

@responses.activate
def test_get_current_weather_api_error(client):
    """Test current weather retrieval with API error."""
    responses.add(
        responses.GET,
        'https://api.weather.test/current',
        json={'error': 'Internal server error'},
        status=500
    )
    
    with pytest.raises(WeatherAPIError) as exc:
        client.get_current_weather(-33.8688, 151.2093)
    assert "API request failed" in str(exc.value)

@responses.activate
def test_get_current_weather_rate_limit(client):
    """Test current weather retrieval with rate limit."""
    responses.add(
        responses.GET,
        'https://api.weather.test/current',
        json={'error': 'Rate limit exceeded'},
        status=429
    )
    
    with pytest.raises(RateLimitError) as exc:
        client.get_current_weather(-33.8688, 151.2093)
    assert "Rate limit exceeded" in str(exc.value)

@responses.activate
def test_get_forecast_success(client):
    """Test successful forecast retrieval."""
    responses.add(
        responses.GET,
        'https://api.weather.test/forecast',
        json={'forecast': [{'day': 1, 'temp': 25}]},
        status=200
    )
    
    data = client.get_forecast(-33.8688, 151.2093, days=7)
    assert data == {'forecast': [{'day': 1, 'temp': 25}]}
    assert len(responses.calls) == 1
    assert 'days=7' in responses.calls[0].request.url

@responses.activate
def test_get_forecast_invalid_days(client):
    """Test forecast retrieval with invalid days parameter."""
    with pytest.raises(ValidationError) as exc:
        client.get_forecast(-33.8688, 151.2093, days=20)
    assert "Forecast days must be between 1 and 14" in str(exc.value)

@responses.activate
def test_get_weather_alerts_success(client):
    """Test successful weather alerts retrieval."""
    responses.add(
        responses.GET,
        'https://api.weather.test/alerts',
        json={'alerts': [{'type': 'storm', 'level': 'warning'}]},
        status=200
    )
    
    data = client.get_weather_alerts(-33.8688, 151.2093)
    assert data == {'alerts': [{'type': 'storm', 'level': 'warning'}]}
    assert len(responses.calls) == 1

def test_rate_limiting(client):
    """Test rate limiting functionality."""
    # Set up client with low rate limit
    client.rate_limit = 2
    client._request_count = 0
    client._window_start = datetime.now()
    
    # First two requests should succeed
    with patch.object(client, '_make_request') as mock_request:
        mock_request.return_value = {'data': 'test'}
        client.get_current_weather(-33.8688, 151.2093)
        client.get_current_weather(-33.8688, 151.2093)
        assert mock_request.call_count == 2
    
    # Third request should fail
    with pytest.raises(RateLimitError) as exc:
        client.get_current_weather(-33.8688, 151.2093)
    assert "Rate limit" in str(exc.value)
    
    # Moving window should reset counter
    client._window_start = datetime.now() - timedelta(days=1)
    with patch.object(client, '_make_request') as mock_request:
        mock_request.return_value = {'data': 'test'}
        client.get_current_weather(-33.8688, 151.2093)
        assert mock_request.call_count == 1

@responses.activate
def test_retry_logic(client):
    """Test retry logic for failed requests."""
    # First two attempts fail, third succeeds
    responses.add(
        responses.GET,
        'https://api.weather.test/current',
        json={'error': 'Internal server error'},
        status=500
    )
    responses.add(
        responses.GET,
        'https://api.weather.test/current',
        json={'error': 'Internal server error'},
        status=500
    )
    responses.add(
        responses.GET,
        'https://api.weather.test/current',
        json={'temperature': 25},
        status=200
    )
    
    data = client.get_current_weather(-33.8688, 151.2093)
    assert data == {'temperature': 25}
    assert len(responses.calls) == 3

@responses.activate
def test_cache_integration(client):
    """Test caching integration."""
    # First request should hit API
    responses.add(
        responses.GET,
        'https://api.weather.test/current',
        json={'temperature': 25},
        status=200
    )
    
    data1 = client.get_current_weather(-33.8688, 151.2093)
    assert data1 == {'temperature': 25}
    assert len(responses.calls) == 1
    
    # Second request should use cache
    data2 = client.get_current_weather(-33.8688, 151.2093)
    assert data2 == {'temperature': 25}
    assert len(responses.calls) == 1  # No new API call
    
    # Invalidate cache
    client.invalidate_cache('get_current_weather', lat=-33.8688, lon=151.2093)
    
    # Third request should hit API again
    responses.add(
        responses.GET,
        'https://api.weather.test/current',
        json={'temperature': 26},  # Different temperature
        status=200
    )
    
    data3 = client.get_current_weather(-33.8688, 151.2093)
    assert data3 == {'temperature': 26}
    assert len(responses.calls) == 2  # New API call 