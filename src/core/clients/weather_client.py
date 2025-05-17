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
from src.api.weather import WeatherAPI

logger = logging.getLogger(__name__)

class WeatherAPIClient:
    """Thin wrapper for the Weather API, delegating to src.api.weather. Use this for backward compatibility."""
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        config = get_config()
        self.api = WeatherAPI(
            config.weather,
        )

    def get_current_weather(self, lat: float = None, lon: float = None) -> Dict[str, Any]:
        # Google WeatherAPI always uses Sydney if no lat/lon provided
        return self.api.get_current_weather()

    def get_forecast(self, lat: float = None, lon: float = None, days: int = 7) -> Dict[str, Any]:
        return self.api.get_forecast(days=days)

    def get_weather_alerts(self, lat: float = None, lon: float = None) -> Dict[str, Any]:
        return self.api.get_weather_alerts()

