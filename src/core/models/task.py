"""Data models for Motion tasks."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from src.utils.exceptions import ValidationError


class TaskStatus(str, Enum):
    """Possible statuses for a Motion task."""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    ARCHIVED = "archived"


class TaskPriority(str, Enum):
    """Possible priorities for a Motion task."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Task(BaseModel):
    """
    Data model for a Motion task.
    
    This model includes validation and transformation logic to ensure data consistency
    and proper handling of task data from the Motion API.
    """
    # Required fields
    id: str = Field(..., description="Unique identifier for the task")
    name: str = Field(..., description="Task name", min_length=1)
    status: TaskStatus = Field(..., description="Current status of the task")
    
    # Optional fields
    description: Optional[str] = Field(None, description="Task description")
    priority: Optional[TaskPriority] = Field(None, description="Task priority")
    due_date: Optional[datetime] = Field(None, description="Task due date")
    scheduled_start: Optional[datetime] = Field(None, description="When the task is scheduled to start")
    scheduled_end: Optional[datetime] = Field(None, description="When the task is scheduled to end")
    project_id: Optional[str] = Field(None, description="ID of the project this task belongs to")
    assignee_id: Optional[str] = Field(None, description="ID of the user assigned to this task")
    created_at: Optional[datetime] = Field(None, description="When the task was created")
    updated_at: Optional[datetime] = Field(None, description="When the task was last updated")
    completed_at: Optional[datetime] = Field(None, description="When the task was completed")
    tags: List[str] = Field(default_factory=list, description="List of tags associated with the task")
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional task metadata")
    
    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> "Task":
        """
        Create a Task instance from Motion API data.
        
        Args:
            data: Raw task data from Motion API
            
        Returns:
            Task: Validated and transformed task instance
            
        Raises:
            ValidationError: If the data is invalid
        """
        try:
            # Validate required fields
            if "name" not in data:
                raise ValidationError(
                    message="Task name is required",
                    details={"raw_data": data},
                )

            # Transform API data to match our model
            status_value = data.get("status")
            if isinstance(status_value, dict):
                status_value = status_value.get("name", "todo")
            if isinstance(status_value, str):
                status_value = status_value.lower()

            def parse_datetime_aware(dt_str):
                if isinstance(dt_str, str):
                    if dt_str.endswith('Z'):
                        return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
                    return datetime.fromisoformat(dt_str)
                return None

            task_data = {
                "id": data["id"],
                "name": data["name"],
                "status": TaskStatus(status_value),
                "description": data.get("description"),
                "priority": TaskPriority(data["priority"].lower()) if "priority" in data else None,
                "due_date": parse_datetime_aware(data["due_date"]) if "due_date" in data else None,
                "scheduled_start": parse_datetime_aware(data["scheduledStart"]) if "scheduledStart" in data else None,
                "scheduled_end": parse_datetime_aware(data["scheduledEnd"]) if "scheduledEnd" in data else None,
                "project_id": data.get("project_id"),
                "assignee_id": data.get("assignee_id"),
                "created_at": parse_datetime_aware(data["created_at"]) if "created_at" in data else None,
                "updated_at": parse_datetime_aware(data["updated_at"]) if "updated_at" in data else None,
                "completed_at": parse_datetime_aware(data["completed_at"]) if "completed_at" in data else None,
                "tags": data.get("tags", []),
                "metadata": {k: v for k, v in data.items() if k not in {
                    "id", "name", "status", "description", "priority",
                    "due_date", "scheduledStart", "scheduledEnd", "project_id", "assignee_id",
                    "created_at", "updated_at", "completed_at", "tags",
                }},
            }
            
            return cls(**task_data)
            
        except (KeyError, ValueError) as e:
            raise ValidationError(
                message=f"Invalid task data: {str(e)}",
                details={"raw_data": data},
                cause=e,
            )


class TaskCollection(BaseModel):
    """Collection of Motion tasks."""
    
    tasks: List[Task] = Field(default_factory=list, description="List of tasks")
    
    def __iter__(self):
        """Iterate over tasks."""
        return iter(self.tasks)
    
    def __len__(self) -> int:
        """Get number of tasks."""
        return len(self.tasks)
    
    def __getitem__(self, index: int) -> Task:
        """Get task by index."""
        return self.tasks[index]
    
    def append(self, task: Task) -> None:
        """Add a task to the collection."""
        self.tasks.append(task)
    
    def extend(self, tasks: List[Task]) -> None:
        """Add multiple tasks to the collection."""
        self.tasks.extend(tasks)
    
    def filter_by_status(self, status: TaskStatus) -> "TaskCollection":
        """Filter tasks by status."""
        return TaskCollection(tasks=[t for t in self.tasks if t.status == status])
    
    def filter_by_priority(self, priority: TaskPriority) -> "TaskCollection":
        """Filter tasks by priority."""
        return TaskCollection(tasks=[t for t in self.tasks if t.priority == priority])
    
    def filter_by_project(self, project_id: str) -> "TaskCollection":
        """Filter tasks by project ID."""
        return TaskCollection(tasks=[t for t in self.tasks if t.project_id == project_id])
    
    def filter_by_assignee(self, assignee_id: str) -> "TaskCollection":
        """Filter tasks by assignee ID."""
        return TaskCollection(tasks=[t for t in self.tasks if t.assignee_id == assignee_id])
    
    def sort_by_due_date(self, ascending: bool = True) -> "TaskCollection":
        """Sort tasks by due date."""
        sorted_tasks = sorted(
            self.tasks,
            key=lambda t: (t.due_date or datetime.max),
            reverse=not ascending,
        )
        return TaskCollection(tasks=sorted_tasks)
    
    def sort_by_priority(self, ascending: bool = True) -> "TaskCollection":
        """Sort tasks by priority."""
        priority_order = {
            TaskPriority.URGENT: 0,
            TaskPriority.HIGH: 1,
            TaskPriority.MEDIUM: 2,
            TaskPriority.LOW: 3,
        }
        sorted_tasks = sorted(
            self.tasks,
            key=lambda t: (priority_order.get(t.priority, 4) if t.priority else 4),
            reverse=not ascending,
        )
        return TaskCollection(tasks=sorted_tasks)
    
    def filter_by_scheduled_date(self, date: datetime) -> "TaskCollection":
        """
        Filter tasks scheduled for a specific date.
        
        Args:
            date: The date to filter tasks for
            
        Returns:
            TaskCollection: Tasks scheduled for the specified date
        """
        target_date = date.date()
        filtered_tasks = [
            task for task in self.tasks
            if task.scheduled_start and task.scheduled_start.date() == target_date
        ]
        return TaskCollection(tasks=filtered_tasks) 