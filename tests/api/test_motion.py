"""Tests for the Motion API client."""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest
import requests
from requests.exceptions import RequestException

from src.api.motion import MotionClient
from src.core.models.task import Task, TaskCollection, TaskStatus, TaskPriority
from src.utils.config import MotionAPIConfig
from src.utils.exceptions import MotionAPIError, ValidationError


@pytest.fixture
def api_config():
    """Create a test API configuration."""
    return MotionAPIConfig(
        motion_api_key="test_api_key",
        motion_api_url="https://api.motion.dev/v1",
    )


@pytest.fixture
def client(api_config):
    """Create a Motion API client with mocked session."""
    with patch("requests.Session") as mock_session:
        mock_session.return_value.headers = {}
        client = MotionClient(api_config)
        client.session = mock_session.return_value
        yield client


def test_init_sets_headers(api_config):
    """Test that client initialization sets correct headers."""
    with patch("requests.Session") as mock_session:
        mock_session.return_value.headers = {}
        client = MotionClient(api_config)
        
        assert client.session.headers["Authorization"] == f"Bearer {api_config.motion_api_key}"
        assert client.session.headers["Content-Type"] == "application/json"
        assert client.session.headers["Accept"] == "application/json"


def test_get_tasks_success(client):
    """Test successful task retrieval."""
    # Mock response
    mock_response = Mock()
    mock_response.json.return_value = {
        "tasks": [
            {
                "id": "task_1",
                "name": "Test Task",
                "status": "todo",
                "priority": "high",
                "due_date": "2024-03-20T10:00:00Z",
                "description": "Test description",
                "project_id": "proj_1",
                "assignee_id": "user_1",
                "created_at": "2024-03-19T10:00:00Z",
                "updated_at": "2024-03-19T10:00:00Z",
                "tags": ["test", "api"],
            }
        ]
    }
    client.session.request.return_value = mock_response
    
    # Test parameters
    due_date = datetime(2024, 3, 20)
    project_id = "proj_1"
    status = "todo"
    assignee_id = "user_1"
    
    # Call the method
    tasks = client.get_tasks(
        due_date=due_date,
        project_id=project_id,
        status=status,
        assignee_id=assignee_id,
    )
    
    # Verify request
    client.session.request.assert_called_once_with(
        method="GET",
        url="https://api.motion.dev/v1/tasks",
        params={
            "due_date": due_date.isoformat(),
            "project_id": project_id,
            "status": status,
            "assignee_id": assignee_id,
        },
        json=None,
        timeout=10.0,
    )
    
    # Verify response
    assert isinstance(tasks, TaskCollection)
    assert len(tasks) == 1
    task = tasks[0]
    assert task.id == "task_1"
    assert task.name == "Test Task"
    assert task.status == TaskStatus.TODO
    assert task.priority == TaskPriority.HIGH
    assert task.description == "Test description"
    assert task.project_id == "proj_1"
    assert task.assignee_id == "user_1"
    assert task.tags == ["test", "api"]


def test_get_task_success(client):
    """Test successful single task retrieval."""
    # Mock response
    mock_response = Mock()
    mock_response.json.return_value = {
        "id": "task_1",
        "name": "Test Task",
        "status": "todo",
        "priority": "high",
        "due_date": "2024-03-20T10:00:00Z",
        "description": "Test description",
        "project_id": "proj_1",
        "assignee_id": "user_1",
        "created_at": "2024-03-19T10:00:00Z",
        "updated_at": "2024-03-19T10:00:00Z",
        "tags": ["test", "api"],
    }
    client.session.request.return_value = mock_response
    
    # Call the method
    task = client.get_task("task_1")
    
    # Verify request
    client.session.request.assert_called_once_with(
        method="GET",
        url="https://api.motion.dev/v1/tasks/task_1",
        params=None,
        json=None,
        timeout=10.0,
    )
    
    # Verify response
    assert isinstance(task, Task)
    assert task.id == "task_1"
    assert task.name == "Test Task"
    assert task.status == TaskStatus.TODO
    assert task.priority == TaskPriority.HIGH


def test_create_task_success(client):
    """Test successful task creation."""
    # Mock response
    mock_response = Mock()
    mock_response.json.return_value = {
        "id": "task_1",
        "name": "New Task",
        "status": "todo",
        "priority": "high",
        "due_date": "2024-03-20T10:00:00Z",
        "description": "New task description",
        "project_id": "proj_1",
        "assignee_id": "user_1",
        "created_at": "2024-03-19T10:00:00Z",
        "updated_at": "2024-03-19T10:00:00Z",
        "tags": ["new", "api"],
    }
    client.session.request.return_value = mock_response
    
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
    
    # Call the method
    task = client.create_task(task_data)
    
    # Verify request
    client.session.request.assert_called_once_with(
        method="POST",
        url="https://api.motion.dev/v1/tasks",
        params=None,
        json=task_data,
        timeout=10.0,
    )
    
    # Verify response
    assert isinstance(task, Task)
    assert task.id == "task_1"
    assert task.name == "New Task"
    assert task.status == TaskStatus.TODO
    assert task.priority == TaskPriority.HIGH


def test_update_task_success(client):
    """Test successful task update."""
    # Mock response
    mock_response = Mock()
    mock_response.json.return_value = {
        "id": "task_1",
        "name": "Updated Task",
        "status": "in_progress",
        "priority": "medium",
        "due_date": "2024-03-21T10:00:00Z",
        "description": "Updated description",
        "project_id": "proj_1",
        "assignee_id": "user_2",
        "created_at": "2024-03-19T10:00:00Z",
        "updated_at": "2024-03-19T11:00:00Z",
        "tags": ["updated", "api"],
    }
    client.session.request.return_value = mock_response
    
    # Test data
    task_data = {
        "name": "Updated Task",
        "status": "in_progress",
        "priority": "medium",
        "due_date": "2024-03-21T10:00:00Z",
        "description": "Updated description",
        "assignee_id": "user_2",
        "tags": ["updated", "api"],
    }
    
    # Call the method
    task = client.update_task("task_1", task_data)
    
    # Verify request
    client.session.request.assert_called_once_with(
        method="PUT",
        url="https://api.motion.dev/v1/tasks/task_1",
        params=None,
        json=task_data,
        timeout=10.0,
    )
    
    # Verify response
    assert isinstance(task, Task)
    assert task.id == "task_1"
    assert task.name == "Updated Task"
    assert task.status == TaskStatus.IN_PROGRESS
    assert task.priority == TaskPriority.MEDIUM


def test_delete_task_success(client):
    """Test successful task deletion."""
    # Mock response
    mock_response = Mock()
    mock_response.json.return_value = {}
    client.session.request.return_value = mock_response
    
    # Call the method
    client.delete_task("task_1")
    
    # Verify request
    client.session.request.assert_called_once_with(
        method="DELETE",
        url="https://api.motion.dev/v1/tasks/task_1",
        params=None,
        json=None,
        timeout=10.0,
    )


def test_api_error_handling(client):
    """Test API error handling."""
    # Mock failed request
    mock_response = Mock()
    mock_response.status_code = 429
    mock_response.json.return_value = {"error": "Rate limit exceeded"}
    http_error = requests.exceptions.HTTPError()
    http_error.response = mock_response
    mock_response.raise_for_status.side_effect = http_error
    
    client.session.request.return_value = mock_response
    
    # Test that the error is converted to MotionAPIError
    with pytest.raises(MotionAPIError) as exc_info:
        client.get_tasks()
    
    error = exc_info.value
    assert error.status_code == 429
    assert "Rate limit exceeded" in str(error)
    assert error.details["error"] == "Rate limit exceeded"


def test_network_error_handling(client):
    """Test network error handling."""
    # Mock network error
    client.session.request.side_effect = RequestException("Connection failed")
    
    # Test that the error is converted to MotionAPIError
    with pytest.raises(MotionAPIError) as exc_info:
        client.get_tasks()
    
    error = exc_info.value
    assert "Connection failed" in str(error)
    assert error.status_code is None


def test_invalid_task_data_handling(client):
    """Test handling of invalid task data."""
    # Mock response with invalid data
    mock_response = Mock()
    mock_response.json.return_value = {
        "tasks": [
            {
                "id": "task_1",
                # Missing required 'name' field
                "status": "invalid_status",  # Invalid status
                "priority": "invalid_priority",  # Invalid priority
            }
        ]
    }
    client.session.request.return_value = mock_response
    
    # Test that invalid data raises ValidationError
    with pytest.raises(ValidationError) as exc_info:
        client.get_tasks()
    
    error = exc_info.value
    assert "Task name is required" in str(error)
    assert "raw_data" in error.details 