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

from src.utils.config import WeatherAPIConfig
from src.utils.exceptions import WeatherAPIError

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

    def __str__(self):
        return self.message or super().__str__()

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
        config: WeatherAPIConfig,
        timeout: int = 10,
        max_retries: int = 3,
        initial_retry_delay: int = 5,
        max_requests_per_day: int = 1000
    ):
        """Initialize the Weather API client.
        
        Args:
            config: Weather API configuration containing credentials and base URL
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            initial_retry_delay: Initial delay between retries in seconds
            max_requests_per_day: Maximum number of requests allowed per day
        """
        self.config = config
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
        
        # Set default headers
        self.session.headers.update({
            "Authorization": f"Bearer {self.config.weather_api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        })
        
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
        
        url = urljoin(self.config.base_url, endpoint)
        params = params or {}
        params["key"] = self.config.weather_api_key
        
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
        except (requests.exceptions.RetryError, requests.packages.urllib3.exceptions.MaxRetryError) as e:
            # Handle retry errors, which may wrap a 429 or other status
            import re
            msg = str(e)
            status_code = None
            if hasattr(e, 'reason') and hasattr(e.reason, 'response') and e.reason.response is not None:
                status_code = getattr(e.reason.response, 'status_code', None)
            if status_code is None:
                match = re.search(r'(\d{3})', msg)
                if match:
                    status_code = int(match.group(1))
            # If 429 is in the error message, treat as rate limit error
            if status_code == 429 or '429' in msg:
                raise RateLimitError(
                    message="Rate limit exceeded",
                    status_code=429
                )
            raise WeatherAPIError(
                message=msg,
                status_code=status_code
            )
        except requests.exceptions.RequestException as e:
            # Try to extract status code and response from the exception, even if using mocks
            status_code = None
            response_json = None
            message = str(e)
            if hasattr(e, 'response') and e.response is not None:
                status_code = getattr(e.response, 'status_code', None)
                try:
                    if hasattr(e.response, 'json') and e.response.content:
                        response_json = e.response.json()
                        # If the API returned an error message, use it
                        if response_json and 'error' in response_json and 'message' in response_json['error']:
                            message = response_json['error']['message']
                except Exception:
                    response_json = None
            # Fallback: try to extract status code from the error string (for responses mock)
            if status_code is None and e.args and isinstance(e.args[0], str):
                import re
                match = re.search(r'(\d{3}) Client Error', e.args[0])
                if match:
                    status_code = int(match.group(1))
            # Rate limit error
            if status_code == 429:
                raise RateLimitError(
                    message=message or "Rate limit exceeded",
                    status_code=429,
                    response=response_json
                )
            raise WeatherAPIError(
                message=message,
                status_code=status_code,
                response=response_json
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