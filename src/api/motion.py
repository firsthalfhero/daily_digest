"""Motion API client for retrieving task data."""

import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.core.models.task import Task, TaskCollection
from src.core.models.calendar import CalendarEvent, CalendarEventCollection
from src.utils.config import MotionAPIConfig
from src.utils.exceptions import MotionAPIError, retry_on_error
from src.utils.logging import get_logger
from src.utils.rate_limiter import global_rate_limiter

logger = get_logger(__name__)


class MotionClient:
    """Client for interacting with the Motion API."""

    def __init__(self, config: MotionAPIConfig):
        """
        Initialize the Motion API client.
        
        Args:
            config: Motion API configuration containing credentials and base URL.
        """
        self.config = config
        self.session = self._create_session()
        print(f"[DEBUG] Using API Key: {self.config.motion_api_key[:8]}...")

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
            "X-API-Key": self.config.motion_api_key,
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
        self._enforce_rate_limit()

        # Set headers per request type
        headers = {
            "X-API-Key": self.config.motion_api_key,
            "Accept": "application/json",
        }
        if method.upper() in ("POST", "PUT", "PATCH"):
            headers["Content-Type"] = "application/json"
            headers["Authorization"] = f"Bearer {self.config.motion_api_key}"

        try:
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
                headers=headers,  # override session headers
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
            
            error_message = f"Motion API request failed: {str(e)}"
            if error_details and isinstance(error_details, dict):
                if 'error' in error_details:
                    error_message += f" ({error_details['error']})"
                elif 'message' in error_details:
                    error_message += f" ({error_details['message']})"
            raise MotionAPIError(
                message=error_message,
                status_code=status_code,
                details=error_details,
                cause=e,
            )

    def get_tasks(
        self,
        project_id: Optional[str] = None,
        status: Optional[str] = None,
        assignee_id: Optional[str] = None,
        due_date: Optional[datetime] = None,
    ) -> TaskCollection:
        """
        Get tasks from Motion API.
        
        Args:
            project_id: Optional project ID to filter tasks
            status: Optional status to filter tasks
            assignee_id: Optional assignee ID to filter tasks
            due_date: Optional due date to filter tasks
            
        Returns:
            TaskCollection: Collection of tasks
            
        Raises:
            MotionAPIError: If the API request fails
        """
        params = {}
        if project_id:
            params["project_id"] = project_id
        if status:
            params["status"] = status
        if assignee_id:
            params["assignee_id"] = assignee_id
        if due_date:
            params["due_date"] = due_date.isoformat()
        
        print(f"[DEBUG] Calling get_tasks with params: {params}")
        try:
            response = self._make_request(
                method="GET",
                endpoint="/tasks",
                params=params,
            )
            import json
            print("[DEBUG] Raw /tasks API response:")
            print(json.dumps(response, indent=2))
            # Write the full response to a markdown file for inspection
            with open("motion_api_tasks_response.md", "w", encoding="utf-8") as f:
                f.write("```json\n")
                f.write(json.dumps(response, indent=2))
                f.write("\n```")
            # Convert API response to Task objects
            tasks = [
                Task.from_api_data(task_data)
                for task_data in response.get("tasks", [])
            ]
            print(f"[DEBUG] Parsed {len(tasks)} tasks from API response.")
            for t in tasks:
                print(f"  - Task: id={t.id}, title={t.title}, status={getattr(t, 'status', None)}, scheduled_start={getattr(t, 'scheduled_start', None)}")
            return TaskCollection(tasks=tasks)
            
        except MotionAPIError as e:
            logger.error(
                "failed_to_get_tasks",
                project_id=project_id,
                status=status,
                assignee_id=assignee_id,
                due_date=due_date.isoformat() if due_date else None,
                error=str(e),
            )
            raise

    def get_task(self, task_id: str) -> Task:
        """
        Get a single task by ID.
        
        Args:
            task_id: ID of the task to retrieve
            
        Returns:
            Task: The requested task
            
        Raises:
            MotionAPIError: If the API request fails
        """
        try:
            response = self._make_request(
                method="GET",
                endpoint=f"/tasks/{task_id}",
            )
            
            return Task.from_api_data(response)
            
        except MotionAPIError as e:
            logger.error(
                "failed_to_get_task",
                task_id=task_id,
                error=str(e),
            )
            raise

    def create_task(self, task_data: Dict[str, Any]) -> Task:
        """
        Create a new task.
        
        Args:
            task_data: Task data to create
            
        Returns:
            Task: The created task
            
        Raises:
            MotionAPIError: If the API request fails
        """
        try:
            response = self._make_request(
                method="POST",
                endpoint="/tasks",
                json=task_data,
            )
            
            return Task.from_api_data(response)
            
        except MotionAPIError as e:
            logger.error(
                "failed_to_create_task",
                task_data=task_data,
                error=str(e),
            )
            raise

    def update_task(self, task_id: str, task_data: Dict[str, Any]) -> Task:
        """
        Update an existing task.
        
        Args:
            task_id: ID of the task to update
            task_data: Updated task data
            
        Returns:
            Task: The updated task
            
        Raises:
            MotionAPIError: If the API request fails
        """
        try:
            response = self._make_request(
                method="PUT",
                endpoint=f"/tasks/{task_id}",
                json=task_data,
            )
            
            return Task.from_api_data(response)
            
        except MotionAPIError as e:
            logger.error(
                "failed_to_update_task",
                task_id=task_id,
                task_data=task_data,
                error=str(e),
            )
            raise

    def delete_task(self, task_id: str) -> None:
        """
        Delete a task.
        
        Args:
            task_id: ID of the task to delete
            
        Raises:
            MotionAPIError: If the API request fails
        """
        try:
            self._make_request(
                method="DELETE",
                endpoint=f"/tasks/{task_id}",
            )
            
        except MotionAPIError as e:
            logger.error(
                "failed_to_delete_task",
                task_id=task_id,
                error=str(e),
            )
            raise

    def get_tasks_scheduled_for_today(self, params: dict = None) -> TaskCollection:
        """
        Get tasks scheduled for today from Motion API, or for a custom date if params['due_date'] is provided.
        If params is provided, pass it to the API request.
        """
        print(f"[DEBUG] Calling get_tasks_scheduled_for_today with params: {params}")
        try:
            if params is not None:
                response = self._make_request(
                    method="GET",
                    endpoint="/tasks",
                    params=params,
                )
                import json
                print("[DEBUG] Raw /tasks API response (scheduled for today):")
                print(json.dumps(response, indent=2))
                # Write the full response to a markdown file for inspection
                with open("motion_api_tasks_response.md", "w", encoding="utf-8") as f:
                    f.write("```json\n")
                    f.write(json.dumps(response, indent=2))
                    f.write("\n```")
                tasks = [
                    Task.from_api_data(task_data)
                    for task_data in response.get("tasks", [])
                ]
                print(f"[DEBUG] Parsed {len(tasks)} tasks from API response (scheduled for today).")
                for t in tasks:
                    print(f"  - Task: id={t.id}, title={t.title}, status={getattr(t, 'status', None)}, scheduled_start={getattr(t, 'scheduled_start', None)}")
                return TaskCollection(tasks=tasks)
            else:
                # Get all tasks (we'll filter client-side)
                print("[DEBUG] No params provided, fetching all tasks for client-side filtering.")
                response = self._make_request(
                    method="GET",
                    endpoint="/tasks",
                )
                import json
                print("[DEBUG] Raw /tasks API response (all tasks):")
                print(json.dumps(response, indent=2))
                # Write the full response to a markdown file for inspection
                with open("motion_api_tasks_response.md", "w", encoding="utf-8") as f:
                    f.write("```json\n")
                    f.write(json.dumps(response, indent=2))
                    f.write("\n```")
                tasks = [
                    Task.from_api_data(task_data)
                    for task_data in response.get("tasks", [])
                ]
                print(f"[DEBUG] Parsed {len(tasks)} tasks from API response (all tasks). Filtering by scheduled date.")
                all_tasks = TaskCollection(tasks=tasks)
                today = datetime.now(timezone.utc)
                filtered = all_tasks.filter_by_scheduled_date(today)
                print(f"[DEBUG] {len(filtered)} tasks remain after filtering by scheduled date (today={today.date()}).")
                for t in filtered:
                    print(f"  - Task: id={t.id}, title={t.title}, status={getattr(t, 'status', None)}, scheduled_start={getattr(t, 'scheduled_start', None)}")
                return filtered
        except MotionAPIError as e:
            logger.error(
                "failed_to_get_today_tasks",
                error=str(e),
            )
            raise

    def get_calendar_events(self, start_date: datetime, end_date: datetime = None) -> 'CalendarEventCollection':
        """
        Get calendar events from the Motion API for a given date range.
        Args:
            start_date: The start date for events (required)
            end_date: The end date for events (optional, defaults to start_date + 1 day)
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
        try:
            response = self._make_request(
                method="GET",
                endpoint="/events",
                params=params,
            )
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
                error=str(e),
            )
            raise 