"""Weather API client for retrieving weather data for Sydney."""

import os
import time
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class WeatherAPIError(Exception):
    """Base exception for Weather API errors."""
    message: str
    status_code: Optional[int] = None
    response: Optional[Dict[str, Any]] = None

class RateLimitError(WeatherAPIError):
    """Exception raised when rate limit is exceeded."""
    pass

class WeatherAPI:
    """Client for interacting with the Weather API."""
    
    # Sydney coordinates
    SYDNEY_LAT = -33.8688
    SYDNEY_LON = 151.2093
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.weatherapi.com/v1/",
        timeout: int = 10,
        max_retries: int = 3,
        initial_retry_delay: int = 5,
        max_requests_per_day: int = 1000
    ):
        """Initialize the Weather API client.
        
        Args:
            api_key: Weather API key. If not provided, will try to get from WEATHER_API_KEY env var
            base_url: Base URL for the Weather API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            initial_retry_delay: Initial delay between retries in seconds
            max_requests_per_day: Maximum number of requests allowed per day
        """
        self.api_key = api_key or os.getenv("WEATHER_API_KEY")
        if not self.api_key:
            raise ValueError("Weather API key must be provided or set in WEATHER_API_KEY environment variable")
            
        self.base_url = base_url
        self.timeout = timeout
        self.max_requests_per_day = max_requests_per_day
        
        # Initialize request tracking
        self._request_count = 0
        self._last_reset = datetime.now()
        
        # Configure session with retry logic
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=initial_retry_delay,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
    def _check_rate_limit(self) -> None:
        """Check if we've exceeded the rate limit."""
        now = datetime.now()
        if (now - self._last_reset) > timedelta(days=1):
            self._request_count = 0
            self._last_reset = now
            
        if self._request_count >= self.max_requests_per_day:
            raise RateLimitError(
                message="Daily API request limit exceeded",
                status_code=429
            )
            
    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a request to the Weather API.
        
        Args:
            endpoint: API endpoint to call
            params: Query parameters for the request
            
        Returns:
            API response as dictionary
            
        Raises:
            WeatherAPIError: If the API request fails
            RateLimitError: If rate limit is exceeded
        """
        self._check_rate_limit()
        
        url = urljoin(self.base_url, endpoint)
        params = params or {}
        params["key"] = self.api_key
        
        try:
            logger.debug(f"Making request to {endpoint} with params {params}")
            response = self.session.get(
                url,
                params=params,
                timeout=self.timeout
            )
            self._request_count += 1
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            raise WeatherAPIError(
                message="Request timed out",
                status_code=408
            )
        except requests.exceptions.RequestException as e:
            if e.response is not None and e.response.status_code == 429:
                raise RateLimitError(
                    message="Rate limit exceeded",
                    status_code=429,
                    response=e.response.json() if e.response.content else None
                )
            raise WeatherAPIError(
                message=str(e),
                status_code=e.response.status_code if e.response else None,
                response=e.response.json() if e.response and e.response.content else None
            )
            
    def get_current_weather(self) -> Dict[str, Any]:
        """Get current weather conditions for Sydney.
        
        Returns:
            Current weather data
            
        Raises:
            WeatherAPIError: If the API request fails
            RateLimitError: If rate limit is exceeded
        """
        params = {
            "q": f"{self.SYDNEY_LAT},{self.SYDNEY_LON}",
            "aqi": "no"  # Don't include air quality data
        }
        return self._make_request("current.json", params)
        
    def get_forecast(self, days: int = 3) -> Dict[str, Any]:
        """Get weather forecast for Sydney.
        
        Args:
            days: Number of days to forecast (1-3)
            
        Returns:
            Forecast weather data
            
        Raises:
            WeatherAPIError: If the API request fails
            RateLimitError: If rate limit is exceeded
            ValueError: If days is not between 1 and 3
        """
        if not 1 <= days <= 3:
            raise ValueError("Forecast days must be between 1 and 3")
            
        params = {
            "q": f"{self.SYDNEY_LAT},{self.SYDNEY_LON}",
            "days": days,
            "aqi": "no",
            "alerts": "yes"
        }
        return self._make_request("forecast.json", params)
        
    def get_weather_alerts(self) -> Dict[str, Any]:
        """Get any active weather alerts for Sydney.
        
        Returns:
            Weather alerts data
            
        Raises:
            WeatherAPIError: If the API request fails
            RateLimitError: If rate limit is exceeded
        """
        params = {
            "q": f"{self.SYDNEY_LAT},{self.SYDNEY_LON}",
            "alerts": "yes"
        }
        return self._make_request("forecast.json", params) 