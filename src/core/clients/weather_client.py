"""
Weather API Client implementation with rate limiting, retry logic, and proper error handling.
"""
import logging
import time
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from ..utils.exceptions import WeatherAPIError, RateLimitError, ValidationError
from ..utils.config import get_config

logger = logging.getLogger(__name__)

class WeatherAPIClient:
    """Client for interacting with the Weather API with built-in rate limiting and retry logic."""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """Initialize the Weather API client.
        
        Args:
            api_key: Optional API key. If not provided, will be loaded from config.
            base_url: Optional base URL. If not provided, will be loaded from config.
        """
        self.config = get_config()
        self.api_key = api_key or self.config.get('WEATHER_API_KEY')
        self.base_url = base_url or self.config.get('WEATHER_API_BASE_URL')
        self.rate_limit = self.config.get('WEATHER_API_RATE_LIMIT', 1000)  # calls per day
        self.rate_limit_window = timedelta(days=1)
        self.request_timeout = self.config.get('WEATHER_API_TIMEOUT', 10)  # seconds
        
        # Initialize rate limiting tracking
        self._request_count = 0
        self._window_start = datetime.now()
        
        # Configure session with retry logic
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,  # max retries
            backoff_factor=5,  # initial delay of 5s
            status_forcelist=[429, 500, 502, 503, 504]  # retry on these status codes
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        

        # Validate configuration
        if not self.api_key:
            raise ValidationError("Weather API key is required")
        if not self.base_url:
            raise ValidationError("Weather API base URL is required")

    def _check_rate_limit(self) -> None:
        """Check if we've hit the rate limit and reset counter if window has passed."""
        now = datetime.now()
        if now - self._window_start >= self.rate_limit_window:
            self._request_count = 0
            self._window_start = now
        elif self._request_count >= self.rate_limit:
            raise RateLimitError(
                f"Rate limit of {self.rate_limit} requests per day exceeded. "
                f"Window resets at {self._window_start + self.rate_limit_window}"
            )

    def _make_request(
        self, 
        endpoint: str, 
        method: str = "GET", 
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an API request with proper error handling and rate limiting.
        
        Args:
            endpoint: API endpoint to call
            method: HTTP method (default: GET)
            params: Query parameters
            data: Request body data
            
        Returns:
            Dict containing the API response
            
        Raises:
            WeatherAPIError: For API-specific errors
            RateLimitError: When rate limit is exceeded
            ValidationError: For invalid requests
        """
        self._check_rate_limit()
        
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }
        
        try:
            logger.debug(f"Making {method} request to {url}")
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=data,
                headers=headers,
                timeout=self.request_timeout
            )
            
            self._request_count += 1
            
            # Log response for debugging
            logger.debug(
                f"Response from {url}: status={response.status_code}, "
                f"size={len(response.content)} bytes"
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            raise WeatherAPIError("Request timed out")
        except requests.exceptions.ConnectionError:
            raise WeatherAPIError("Failed to connect to Weather API")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                raise RateLimitError("Rate limit exceeded")
            raise WeatherAPIError(f"API request failed: {str(e)}")
        except requests.exceptions.RequestException as e:
            raise WeatherAPIError(f"Request failed: {str(e)}")


    def get_current_weather(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get current weather conditions for a location.
        
        Args:
            lat: Latitude (-33.8688 for Sydney)
            lon: Longitude (151.2093 for Sydney)
            
        Returns:
            Dict containing current weather data
        """
        if not -90 <= lat <= 90:
            raise ValidationError("Latitude must be between -90 and 90")
        if not -180 <= lon <= 180:
            raise ValidationError("Longitude must be between -180 and 180")
            
        return self._make_request(
            "current",
            params={"lat": lat, "lon": lon}
        )


    def get_forecast(self, lat: float, lon: float, days: int = 7) -> Dict[str, Any]:
        """Get weather forecast for a location.
        
        Args:
            lat: Latitude (-33.8688 for Sydney)
            lon: Longitude (151.2093 for Sydney)
            days: Number of days to forecast (1-14)
            
        Returns:
            Dict containing forecast data
        """
        if not 1 <= days <= 14:
            raise ValidationError("Forecast days must be between 1 and 14")
            
        return self._make_request(
            "forecast",
            params={"lat": lat, "lon": lon, "days": days}
        )


    def get_weather_alerts(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get weather alerts for a location.
        
        Args:
            lat: Latitude (-33.8688 for Sydney)
            lon: Longitude (151.2093 for Sydney)
            
        Returns:
            Dict containing weather alerts
        """
        return self._make_request(
            "alerts",
            params={"lat": lat, "lon": lon}
        )

