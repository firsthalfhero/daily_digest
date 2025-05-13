"""Unit tests for get_tasks script."""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock
import requests
from pydantic import ValidationError

import pytest

from src.api.motion import MotionClient
from src.core.models.task import Task, TaskStatus, TaskPriority
from src.utils.config import MotionAPIConfig
from src.utils.exceptions import MotionAPIError, ConfigurationError
from scripts.get_tasks import main


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
        yield client


@pytest.fixture
def sample_tasks():
    """Create sample task data for testing."""
    today_iso = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
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
            "scheduledStart": today_iso,
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
            "scheduledStart": today_iso,
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
            "scheduledStart": today_iso,
        },
    ]


class TestGetTasksScript:
    """Test get_tasks script functionality."""

    def test_main_success(self, mock_motion_client, sample_tasks, capsys):
        """Test successful script execution."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.json.return_value = {"tasks": sample_tasks}
        mock_motion_client.session.request.return_value = mock_response

        # Mock environment variables
        env_vars = {
            "MOTION_API_KEY": "test_api_key",
            "MOTION_API_URL": "https://api.motion.dev/v1",
            "WEATHER_API_KEY": "test_weather_key",
            "WEATHER_API_URL": "https://api.weatherapi.com/v1",
        }

        with patch.dict("os.environ", env_vars, clear=True):
            with patch("scripts.get_tasks.MotionClient", return_value=mock_motion_client):
                main()

        # Verify output
        captured = capsys.readouterr()
        output = captured.out

        # Check task information in output
        assert "High Priority Task" in output
        assert "Medium Priority Task" in output
        assert "Low Priority Task" in output
        assert "Urgent task description" in output
        assert "Medium priority task" in output
        assert "Low priority task" in output
        assert "proj_1" in output
        assert "proj_2" in output
        assert "user_1" in output
        assert "user_2" in output
        assert "urgent" in output
        assert "ongoing" in output
        assert "completed" in output

    def test_main_with_missing_env_vars(self):
        """Test script execution with missing environment variables."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ConfigurationError) as exc_info:
                main()
            error = exc_info.value
            assert "Missing required environment variables" in str(error)
            assert "MOTION_API_KEY" in error.details["missing_vars"]
            assert "MOTION_API_URL" in error.details["missing_vars"]

    def test_main_with_api_error(self, mock_motion_client):
        """Test script execution with API error."""
        # Mock API error response
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": "Unauthorized"}
        http_error = requests.exceptions.HTTPError()
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        mock_motion_client.session.request.return_value = mock_response

        # Mock environment variables
        env_vars = {
            "MOTION_API_KEY": "test_api_key",
            "MOTION_API_URL": "https://api.motion.dev/v1",
            "WEATHER_API_KEY": "test_weather_key",
            "WEATHER_API_URL": "https://api.weatherapi.com/v1",
        }

        with patch.dict("os.environ", env_vars, clear=True):
            with patch("scripts.get_tasks.MotionClient", return_value=mock_motion_client):
                with pytest.raises(MotionAPIError) as exc_info:
                    main()
                error = exc_info.value
                assert error.status_code == 401
                assert "Unauthorized" in str(error)

    def test_main_with_network_error(self, mock_motion_client):
        """Test script execution with network error."""
        # Mock network error
        mock_motion_client.session.request.side_effect = requests.exceptions.RequestException(
            "Connection failed"
        )

        # Mock environment variables
        env_vars = {
            "MOTION_API_KEY": "test_api_key",
            "MOTION_API_URL": "https://api.motion.dev/v1",
            "WEATHER_API_KEY": "test_weather_key",
            "WEATHER_API_URL": "https://api.weatherapi.com/v1",
        }

        with patch.dict("os.environ", env_vars, clear=True):
            with patch("scripts.get_tasks.MotionClient", return_value=mock_motion_client):
                with pytest.raises(MotionAPIError) as exc_info:
                    main()
                error = exc_info.value
                assert "Connection failed" in str(error)
                assert error.status_code is None

    def test_main_with_no_tasks(self, mock_motion_client, capsys):
        """Test script execution with no tasks."""
        # Mock empty response
        mock_response = MagicMock()
        mock_response.json.return_value = {"tasks": []}
        mock_motion_client.session.request.return_value = mock_response

        # Mock environment variables
        env_vars = {
            "MOTION_API_KEY": "test_api_key",
            "MOTION_API_URL": "https://api.motion.dev/v1",
            "WEATHER_API_KEY": "test_weather_key",
            "WEATHER_API_URL": "https://api.weatherapi.com/v1",
        }

        with patch.dict("os.environ", env_vars, clear=True):
            with patch("scripts.get_tasks.MotionClient", return_value=mock_motion_client):
                main()

        # Verify output
        captured = capsys.readouterr()
        output = captured.out
        assert "No tasks scheduled for today." in output

    def test_main_with_invalid_task_data(self, mock_motion_client):
        """Test script execution with invalid task data."""
        # Mock response with invalid task data
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "tasks": [
                {
                    "id": "task_1",
                    # Missing required 'name' field
                    "status": "invalid_status",
                }
            ]
        }
        mock_motion_client.session.request.return_value = mock_response

        # Mock environment variables
        env_vars = {
            "MOTION_API_KEY": "test_api_key",
            "MOTION_API_URL": "https://api.motion.dev/v1",
            "WEATHER_API_KEY": "test_weather_key",
            "WEATHER_API_URL": "https://api.weatherapi.com/v1",
        }

        with patch.dict("os.environ", env_vars, clear=True):
            with patch("scripts.get_tasks.MotionClient", return_value=mock_motion_client):
                with pytest.raises(ValidationError) as exc_info:
                    main()
                error = exc_info.value
                assert "Invalid task data" in str(error)
                assert "name" in error.details

    def test_main_with_custom_date(self, mock_motion_client, sample_tasks, capsys):
        """Test script execution with custom date."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.json.return_value = {"tasks": sample_tasks}
        mock_motion_client.session.request.return_value = mock_response

        # Mock environment variables
        env_vars = {
            "MOTION_API_KEY": "test_api_key",
            "MOTION_API_URL": "https://api.motion.dev/v1",
            "WEATHER_API_KEY": "test_weather_key",
            "WEATHER_API_URL": "https://api.weatherapi.com/v1",
        }

        # Mock command line arguments
        test_date = "2024-03-25"
        with patch.dict("os.environ", env_vars, clear=True):
            with patch("sys.argv", ["get_tasks.py", "--date", test_date]):
                with patch("scripts.get_tasks.MotionClient", return_value=mock_motion_client):
                    main()

        # Verify request was made with correct date
        call_args = mock_motion_client.session.request.call_args[1]
        assert "params" in call_args
        assert "due_date" in call_args["params"]
        assert call_args["params"]["due_date"] == test_date

        # Verify output
        captured = capsys.readouterr()
        output = captured.out
        assert "High Priority Task" in output
        assert "Medium Priority Task" in output
        assert "Low Priority Task" in output 