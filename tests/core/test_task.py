"""Unit tests for Task model and TaskCollection."""

from datetime import datetime, timedelta
from typing import Dict, Any

import pytest

from src.core.models.task import Task, TaskCollection, TaskStatus, TaskPriority
from src.utils.exceptions import ValidationError


@pytest.fixture
def valid_task_data() -> Dict[str, Any]:
    """Create valid task data for testing."""
    return {
        "id": "task_1",
        "name": "Test Task",
        "status": "todo",
        "priority": "high",
        "due_date": "2024-03-20T10:00:00Z",
        "description": "Test task description",
        "project_id": "proj_1",
        "assignee_id": "user_1",
        "created_at": "2024-03-19T10:00:00Z",
        "updated_at": "2024-03-19T10:00:00Z",
        "tags": ["test", "api"],
    }


@pytest.fixture
def task_collection_data() -> list[Dict[str, Any]]:
    """Create a collection of task data for testing."""
    return [
        {
            "id": "task_1",
            "name": "High Priority Task",
            "status": "todo",
            "priority": "high",
            "due_date": "2024-03-20T10:00:00Z",
            "description": "Urgent task",
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


class TestTask:
    """Test Task model functionality."""

    def test_create_task_from_valid_data(self, valid_task_data):
        """Test creating a task from valid data."""
        task = Task.from_api_data(valid_task_data)
        assert task.id == "task_1"
        assert task.name == "Test Task"
        assert task.status == TaskStatus.TODO
        assert task.priority == TaskPriority.HIGH
        assert task.due_date == datetime.fromisoformat("2024-03-20T10:00:00Z")
        assert task.description == "Test task description"
        assert task.project_id == "proj_1"
        assert task.assignee_id == "user_1"
        assert task.created_at == datetime.fromisoformat("2024-03-19T10:00:00Z")
        assert task.updated_at == datetime.fromisoformat("2024-03-19T10:00:00Z")
        assert task.completed_at is None
        assert task.tags == ["test", "api"]

    def test_create_task_with_minimal_data(self):
        """Test creating a task with only required fields."""
        minimal_data = {
            "id": "task_1",
            "name": "Minimal Task",
            "status": "todo",
        }
        task = Task.from_api_data(minimal_data)
        assert task.id == "task_1"
        assert task.name == "Minimal Task"
        assert task.status == TaskStatus.TODO
        assert task.priority is None
        assert task.due_date is None
        assert task.description is None
        assert task.project_id is None
        assert task.assignee_id is None
        assert task.created_at is None
        assert task.updated_at is None
        assert task.completed_at is None
        assert task.tags == []

    def test_create_task_with_invalid_data(self):
        """Test creating a task with invalid data."""
        # Missing required field
        invalid_data = {
            "id": "task_1",
            "status": "todo",
        }
        with pytest.raises(ValidationError) as exc_info:
            Task.from_api_data(invalid_data)
        error = exc_info.value
        assert "Invalid task data" in str(error)
        assert "name" in error.details

        # Invalid status
        invalid_data = {
            "id": "task_1",
            "name": "Invalid Task",
            "status": "invalid_status",
        }
        with pytest.raises(ValidationError) as exc_info:
            Task.from_api_data(invalid_data)
        error = exc_info.value
        assert "Invalid task data" in str(error)
        assert "status" in error.details

        # Invalid priority
        invalid_data = {
            "id": "task_1",
            "name": "Invalid Task",
            "status": "todo",
            "priority": "invalid_priority",
        }
        with pytest.raises(ValidationError) as exc_info:
            Task.from_api_data(invalid_data)
        error = exc_info.value
        assert "Invalid task data" in str(error)
        assert "priority" in error.details

        # Invalid date format
        invalid_data = {
            "id": "task_1",
            "name": "Invalid Task",
            "status": "todo",
            "due_date": "invalid_date",
        }
        with pytest.raises(ValidationError) as exc_info:
            Task.from_api_data(invalid_data)
        error = exc_info.value
        assert "Invalid task data" in str(error)
        assert "due_date" in error.details

    def test_task_equality(self, valid_task_data):
        """Test task equality comparison."""
        task1 = Task.from_api_data(valid_task_data)
        task2 = Task.from_api_data(valid_task_data)
        task3 = Task.from_api_data({**valid_task_data, "id": "task_2"})

        assert task1 == task2
        assert task1 != task3
        assert task1 != "not a task"

    def test_task_string_representation(self, valid_task_data):
        """Test task string representation."""
        task = Task.from_api_data(valid_task_data)
        expected_str = (
            "Task(id='task_1', name='Test Task', status=TaskStatus.TODO, "
            "priority=TaskPriority.HIGH, due_date=2024-03-20 10:00:00+00:00)"
        )
        assert str(task) == expected_str


class TestTaskCollection:
    """Test TaskCollection functionality."""

    def test_create_collection_from_tasks(self, task_collection_data):
        """Test creating a collection from task data."""
        tasks = [Task.from_api_data(data) for data in task_collection_data]
        collection = TaskCollection(tasks=tasks)
        assert len(collection) == 3
        assert all(isinstance(task, Task) for task in collection)
        assert collection[0].name == "High Priority Task"
        assert collection[1].name == "Medium Priority Task"
        assert collection[2].name == "Low Priority Task"

    def test_collection_iteration(self, task_collection_data):
        """Test iterating over a collection."""
        tasks = [Task.from_api_data(data) for data in task_collection_data]
        collection = TaskCollection(tasks=tasks)
        task_names = [task.name for task in collection]
        assert task_names == [
            "High Priority Task",
            "Medium Priority Task",
            "Low Priority Task",
        ]

    def test_collection_filtering(self, task_collection_data):
        """Test filtering tasks in a collection."""
        tasks = [Task.from_api_data(data) for data in task_collection_data]
        collection = TaskCollection(tasks=tasks)

        # Filter by priority
        high_priority = collection.filter_by_priority(TaskPriority.HIGH)
        assert len(high_priority) == 1
        assert high_priority[0].name == "High Priority Task"

        # Filter by status
        in_progress = collection.filter_by_status(TaskStatus.IN_PROGRESS)
        assert len(in_progress) == 1
        assert in_progress[0].name == "Medium Priority Task"

        # Filter by project
        proj_1_tasks = collection.filter_by_project("proj_1")
        assert len(proj_1_tasks) == 2
        assert all(task.project_id == "proj_1" for task in proj_1_tasks)

        # Filter by assignee
        user_1_tasks = collection.filter_by_assignee("user_1")
        assert len(user_1_tasks) == 2
        assert all(task.assignee_id == "user_1" for task in user_1_tasks)

    def test_collection_sorting(self, task_collection_data):
        """Test sorting tasks in a collection."""
        tasks = [Task.from_api_data(data) for data in task_collection_data]
        collection = TaskCollection(tasks=tasks)

        # Sort by priority
        sorted_by_priority = collection.sort_by_priority()
        assert sorted_by_priority[0].priority == TaskPriority.HIGH
        assert sorted_by_priority[1].priority == TaskPriority.MEDIUM
        assert sorted_by_priority[2].priority == TaskPriority.LOW

        # Sort by due date
        sorted_by_due_date = collection.sort_by_due_date()
        assert sorted_by_due_date[0].due_date == datetime.fromisoformat("2024-03-20T10:00:00Z")
        assert sorted_by_due_date[1].due_date == datetime.fromisoformat("2024-03-21T10:00:00Z")
        assert sorted_by_due_date[2].due_date == datetime.fromisoformat("2024-03-22T10:00:00Z")

    def test_collection_modification(self, task_collection_data):
        """Test modifying a collection."""
        tasks = [Task.from_api_data(data) for data in task_collection_data]
        collection = TaskCollection(tasks=tasks)

        # Append task
        new_task = Task.from_api_data({
            "id": "task_4",
            "name": "New Task",
            "status": "todo",
        })
        collection.append(new_task)
        assert len(collection) == 4
        assert collection[3].name == "New Task"

        # Extend collection
        more_tasks = [
            Task.from_api_data({
                "id": "task_5",
                "name": "Extra Task 1",
                "status": "todo",
            }),
            Task.from_api_data({
                "id": "task_6",
                "name": "Extra Task 2",
                "status": "todo",
            }),
        ]
        collection.extend(more_tasks)
        assert len(collection) == 6
        assert collection[4].name == "Extra Task 1"
        assert collection[5].name == "Extra Task 2"

    def test_collection_string_representation(self, task_collection_data):
        """Test collection string representation."""
        tasks = [Task.from_api_data(data) for data in task_collection_data]
        collection = TaskCollection(tasks=tasks)
        expected_str = (
            "TaskCollection(tasks=[\n"
            "  Task(id='task_1', name='High Priority Task', status=TaskStatus.TODO, "
            "priority=TaskPriority.HIGH, due_date=2024-03-20 10:00:00+00:00),\n"
            "  Task(id='task_2', name='Medium Priority Task', status=TaskStatus.IN_PROGRESS, "
            "priority=TaskPriority.MEDIUM, due_date=2024-03-21 10:00:00+00:00),\n"
            "  Task(id='task_3', name='Low Priority Task', status=TaskStatus.DONE, "
            "priority=TaskPriority.LOW, due_date=2024-03-22 10:00:00+00:00)\n"
            "])"
        )
        assert str(collection) == expected_str 