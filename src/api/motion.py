"""Motion API client for retrieving calendar data."""

import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.core.models.calendar import CalendarEvent, CalendarEventCollection
from src.utils.config import APIConfig
from src.utils.exceptions import MotionAPIError, retry_on_error
from src.utils.logging import get_logger
from src.utils.rate_limiter import global_rate_limiter

logger = get_logger(__name__)


class MotionClient:
    """Client for interacting with the Motion API."""

    def __init__(self, config: APIConfig):
        """
        Initialize the Motion API client.
        
        Args:
            config: API configuration containing credentials and base URL.
        """
        self.config = config
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic."""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,  # number of retries
            backoff_factor=0.5,  # wait 0.5, 1, 2 seconds between retries
            status_forcelist=[429, 500, 502, 503, 504],  # retry on these status codes
        )
        
        # Mount the retry strategy to both http and https
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set default headers
        session.headers.update({
            "Authorization": f"Bearer {self.config.motion_api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        })
        
        return session

    def _enforce_rate_limit(self) -> None:
        """Enforce rate limiting for API requests."""
        if not global_rate_limiter.acquire(wait=True):
            raise MotionAPIError(
                message="Rate limit exceeded",
                status_code=429,
                details={"retry_after": global_rate_limiter.get_current_usage()[1]},
            )

    @retry_on_error(max_attempts=3, delay=1.0, backoff=2.0, exceptions=(requests.RequestException,))
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make a request to the Motion API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Optional query parameters
            json: Optional JSON request body
            
        Returns:
            Dict[str, Any]: API response data
            
        Raises:
            MotionAPIError: If the request fails
        """
        url = f"{self.config.motion_api_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        try:
            self._enforce_rate_limit()
            
            logger.debug(
                "making_api_request",
                method=method,
                url=url,
                params=params,
                has_json=json is not None,
            )
            
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json,
                timeout=10.0,  # 10 second timeout
            )
            
            # Log the response status
            logger.debug(
                "api_response_received",
                status_code=response.status_code,
                url=url,
            )
            
            # Raise for bad status codes
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            # Convert to our custom error type
            status_code = getattr(e.response, "status_code", None) if hasattr(e, "response") else None
            error_details = None
            
            if hasattr(e, "response") and e.response is not None:
                try:
                    error_details = e.response.json()
                except ValueError:
                    error_details = {"text": e.response.text}
            
            raise MotionAPIError(
                message=f"Motion API request failed: {str(e)}",
                status_code=status_code,
                details=error_details,
                cause=e,
            )

    def get_calendar_events(
        self,
        start_date: datetime,
        end_date: Optional[datetime] = None,
        calendar_id: Optional[str] = None,
    ) -> CalendarEventCollection:
        """
        Get calendar events for a date range.
        
        Args:
            start_date: Start date for event retrieval
            end_date: Optional end date (defaults to start_date + 1 day)
            calendar_id: Optional specific calendar ID
            
        Returns:
            CalendarEventCollection: Collection of calendar events
            
        Raises:
            MotionAPIError: If the API request fails
        """
        if end_date is None:
            end_date = start_date + timedelta(days=1)
        
        params = {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
        }
        
        if calendar_id:
            params["calendar_id"] = calendar_id
        
        try:
            response = self._make_request(
                method="GET",
                endpoint="/events",
                params=params,
            )
            
            # Convert API response to CalendarEvent objects
            events = [
                CalendarEvent.from_api_data(event_data)
                for event_data in response.get("events", [])
            ]
            
            return CalendarEventCollection(events)
            
        except MotionAPIError as e:
            logger.error(
                "failed_to_get_calendar_events",
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
                calendar_id=calendar_id,
                error=str(e),
            )
            raise

    def get_calendars(self) -> List[Dict[str, Any]]:
        """
        Get list of available calendars.
        
        Returns:
            List[Dict[str, Any]]: List of calendars
            
        Raises:
            MotionAPIError: If the API request fails
        """
        try:
            response = self._make_request(
                method="GET",
                endpoint="/calendars",
            )
            
            return response.get("calendars", [])
            
        except MotionAPIError as e:
            logger.error(
                "failed_to_get_calendars",
                error=str(e),
            )
            raise 