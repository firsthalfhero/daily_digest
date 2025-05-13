"""Integration tests for Motion API task endpoints."""

from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

import pytest
import requests
from requests.exceptions import RequestException

from src.api.motion import MotionClient
from src.core.models.task import Task, TaskCollection, TaskStatus, TaskPriority
from src.utils.config import MotionAPIConfig
from src.utils.exceptions import MotionAPIError, ValidationError
from src.utils.rate_limiter import global_rate_limiter


@pytest.fixture
def api_config():
    """Create a test API configuration."""
    return MotionAPIConfig(
        motion_api_key="test_api_key",
        motion_api_url="https://api.motion.dev/v1",
    )


@pytest.fixture
def mock_motion_client(api_config):
    """Create a Motion client with mocked session."""
    with patch("requests.Session") as mock_session:
        mock_session.return_value.headers = {}
        client = MotionClient(api_config)
        client.session = mock_session.return_value
        # Reset rate limiter before each test
        global_rate_limiter.reset()
        yield client
        # Reset rate limiter after each test
        global_rate_limiter.reset()


@pytest.fixture
def sample_tasks():
    """Create sample task data for testing."""
    return [
        {
            "id": "task_1",
            "name": "High Priority Task",
            "status": "todo",
            "priority": "high",
            "due_date": "2024-03-20T10:00:00Z",
            "description": "Urgent task description",
            "project_id": "proj_1",
            "assignee_id": "user_1",
            "created_at": "2024-03-19T10:00:00Z",
            "updated_at": "2024-03-19T10:00:00Z",
            "tags": ["urgent", "api"],
        },
        {
            "id": "task_2",
            "name": "Medium Priority Task",
            "status": "in_progress",
            "priority": "medium",
            "due_date": "2024-03-21T10:00:00Z",
            "description": "Medium priority task",
            "project_id": "proj_1",
            "assignee_id": "user_2",
            "created_at": "2024-03-19T10:00:00Z",
            "updated_at": "2024-03-19T10:00:00Z",
            "tags": ["ongoing", "api"],
        },
        {
            "id": "task_3",
            "name": "Low Priority Task",
            "status": "done",
            "priority": "low",
            "due_date": "2024-03-22T10:00:00Z",
            "description": "Low priority task",
            "project_id": "proj_2",
            "assignee_id": "user_1",
            "created_at": "2024-03-19T10:00:00Z",
            "updated_at": "2024-03-19T10:00:00Z",
            "completed_at": "2024-03-19T11:00:00Z",
            "tags": ["completed", "api"],
        },
    ]


class TestMotionAPIClientIntegration:
    """Integration tests for Motion API client."""

    def test_authentication_and_token_management(self, mock_motion_client):
        """Test authentication and token management."""
        # Verify headers are set correctly
        assert mock_motion_client.session.headers["Authorization"] == "Bearer test_api_key"
        assert mock_motion_client.session.headers["Content-Type"] == "application/json"
        assert mock_motion_client.session.headers["Accept"] == "application/json"

    def test_api_response_handling(self, mock_motion_client, sample_tasks):
        """Test API response handling and data transformation."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.json.return_value = {"tasks": sample_tasks}
        mock_response.raise_for_status = MagicMock()
        mock_motion_client.session.request.return_value = mock_response

        # Get tasks
        tasks = mock_motion_client.get_tasks()

        # Verify request
        mock_motion_client.session.request.assert_called_once()
        call_args = mock_motion_client.session.request.call_args[1]
        assert call_args["method"] == "GET"
        assert call_args["url"] == "https://api.motion.dev/v1/tasks"

        # Verify response transformation
        assert isinstance(tasks, TaskCollection)
        assert len(tasks) == 3
        assert all(isinstance(task, Task) for task in tasks)
        assert tasks[0].name == "High Priority Task"
        assert tasks[1].name == "Medium Priority Task"
        assert tasks[2].name == "Low Priority Task"

    def test_task_filtering_and_sorting(self, mock_motion_client, sample_tasks):
        """Test task filtering and sorting functionality."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.json.return_value = {"tasks": sample_tasks}
        mock_motion_client.session.request.return_value = mock_response

        # Get tasks
        tasks = mock_motion_client.get_tasks()

        # Test filtering
        high_priority_tasks = tasks.filter_by_priority(TaskPriority.HIGH)
        assert len(high_priority_tasks) == 1
        assert high_priority_tasks[0].name == "High Priority Task"

        in_progress_tasks = tasks.filter_by_status(TaskStatus.IN_PROGRESS)
        assert len(in_progress_tasks) == 1
        assert in_progress_tasks[0].name == "Medium Priority Task"

        proj_1_tasks = tasks.filter_by_project("proj_1")
        assert len(proj_1_tasks) == 2
        assert all(task.project_id == "proj_1" for task in proj_1_tasks)

        user_1_tasks = tasks.filter_by_assignee("user_1")
        assert len(user_1_tasks) == 2
        assert all(task.assignee_id == "user_1" for task in user_1_tasks)

        # Test sorting
        sorted_by_priority = tasks.sort_by_priority()
        assert sorted_by_priority[0].priority == TaskPriority.HIGH
        assert sorted_by_priority[1].priority == TaskPriority.MEDIUM
        assert sorted_by_priority[2].priority == TaskPriority.LOW

        sorted_by_due_date = tasks.sort_by_due_date()
        assert sorted_by_due_date[0].due_date == datetime.fromisoformat("2024-03-20T10:00:00Z")
        assert sorted_by_due_date[1].due_date == datetime.fromisoformat("2024-03-21T10:00:00Z")
        assert sorted_by_due_date[2].due_date == datetime.fromisoformat("2024-03-22T10:00:00Z")

    def test_task_crud_operations(self, mock_motion_client):
        """Test create, read, update, and delete operations."""
        # Test data
        task_data = {
            "name": "New Task",
            "priority": "high",
            "due_date": "2024-03-20T10:00:00Z",
            "description": "New task description",
            "project_id": "proj_1",
            "assignee_id": "user_1",
            "tags": ["new", "api"],
        }

        # Mock create response
        create_response = MagicMock()
        create_response.json.return_value = {
            "id": "task_1",
            **task_data,
            "status": "todo",
            "created_at": "2024-03-19T10:00:00Z",
            "updated_at": "2024-03-19T10:00:00Z",
        }
        mock_motion_client.session.request.return_value = create_response

        # Create task
        created_task = mock_motion_client.create_task(task_data)
        assert isinstance(created_task, Task)
        assert created_task.id == "task_1"
        assert created_task.name == "New Task"

        # Mock get response
        get_response = MagicMock()
        get_response.json.return_value = create_response.json.return_value
        mock_motion_client.session.request.return_value = get_response

        # Get task
        retrieved_task = mock_motion_client.get_task("task_1")
        assert isinstance(retrieved_task, Task)
        assert retrieved_task.id == "task_1"
        assert retrieved_task.name == "New Task"

        # Mock update response
        update_data = {
            "name": "Updated Task",
            "status": "in_progress",
            "priority": "medium",
        }
        update_response = MagicMock()
        update_response.json.return_value = {
            **create_response.json.return_value,
            **update_data,
            "updated_at": "2024-03-19T11:00:00Z",
        }
        mock_motion_client.session.request.return_value = update_response

        # Update task
        updated_task = mock_motion_client.update_task("task_1", update_data)
        assert isinstance(updated_task, Task)
        assert updated_task.id == "task_1"
        assert updated_task.name == "Updated Task"
        assert updated_task.status == TaskStatus.IN_PROGRESS
        assert updated_task.priority == TaskPriority.MEDIUM

        # Mock delete response
        delete_response = MagicMock()
        delete_response.json.return_value = {}
        mock_motion_client.session.request.return_value = delete_response

        # Delete task
        mock_motion_client.delete_task("task_1")
        mock_motion_client.session.request.assert_called_with(
            method="DELETE",
            url="https://api.motion.dev/v1/tasks/task_1",
            params=None,
            json=None,
            timeout=10.0,
        )

    def test_error_handling(self, mock_motion_client):
        """Test error handling in various scenarios."""
        # Test rate limit error
        rate_limit_response = MagicMock()
        rate_limit_response.status_code = 429
        rate_limit_response.json.return_value = {"error": "Rate limit exceeded"}
        http_error = requests.exceptions.HTTPError()
        http_error.response = rate_limit_response
        rate_limit_response.raise_for_status.side_effect = http_error
        mock_motion_client.session.request.return_value = rate_limit_response

        with pytest.raises(MotionAPIError) as exc_info:
            mock_motion_client.get_tasks()
        error = exc_info.value
        assert error.status_code == 429
        assert "Rate limit exceeded" in str(error)

        # Test network error
        mock_motion_client.session.request.side_effect = RequestException("Connection failed")
        with pytest.raises(MotionAPIError) as exc_info:
            mock_motion_client.get_tasks()
        error = exc_info.value
        assert "Connection failed" in str(error)
        assert error.status_code is None

        # Test invalid data error
        invalid_data_response = MagicMock()
        invalid_data_response.json.return_value = {
            "tasks": [
                {
                    "id": "task_1",
                    # Missing required 'name' field
                    "status": "invalid_status",
                }
            ]
        }
        mock_motion_client.session.request.return_value = invalid_data_response
        mock_motion_client.session.request.side_effect = None  # Reset side effect

        with pytest.raises(ValidationError) as exc_info:
            mock_motion_client.get_tasks()
        error = exc_info.value
        assert "Task name is required" in str(error)
        assert "raw_data" in error.details 