"""
Calendar data models for the Daily Digest Assistant.

This module defines the data structures and validation logic for calendar events
retrieved from the Motion API. It includes timezone handling and data transformation
utilities.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field, field_validator, model_validator

from src.utils.exceptions import ValidationError
from src.utils.logging import get_logger
from src.utils.timezone import (
    SYDNEY_TIMEZONE,
    DEFAULT_TIMEZONE,
    validate_timezone,
    convert_to_timezone,
    is_dst_transition,
    get_dst_transition_info,
    format_timezone_info,
)

logger = get_logger(__name__)

# Constants
SYDNEY_TIMEZONE = ZoneInfo("Australia/Sydney")
DEFAULT_TIMEZONE = SYDNEY_TIMEZONE


class EventStatus(str, Enum):
    """Possible status values for calendar events."""
    CONFIRMED = "confirmed"
    TENTATIVE = "tentative"
    CANCELLED = "cancelled"


class EventType(str, Enum):
    """Types of calendar events."""
    MEETING = "meeting"
    TASK = "task"
    REMINDER = "reminder"
    BREAK = "break"
    OTHER = "other"


class CalendarEvent(BaseModel):
    """
    Data model for a calendar event from Motion API.
    
    This model includes validation and transformation logic to ensure data consistency
    and proper timezone handling.
    """
    # Required fields
    id: str = Field(..., description="Unique identifier for the event")
    title: str = Field(..., description="Event title", min_length=1)
    start_time: datetime = Field(..., description="Event start time")
    end_time: datetime = Field(..., description="Event end time")
    status: EventStatus = Field(..., description="Event status")
    type: EventType = Field(..., description="Event type")
    
    # Optional fields
    description: Optional[str] = Field(None, description="Event description")
    location: Optional[str] = Field(None, description="Event location")
    attendees: List[str] = Field(default_factory=list, description="List of attendee emails")
    calendar_id: Optional[str] = Field(None, description="ID of the calendar containing this event")
    created_at: Optional[datetime] = Field(None, description="When the event was created")
    updated_at: Optional[datetime] = Field(None, description="When the event was last updated")
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional event metadata")
    
    @field_validator("start_time", "end_time", "created_at", "updated_at")
    @classmethod
    def ensure_timezone(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Ensure datetime fields have timezone information."""
        if v is None:
            return v
        if v.tzinfo is None:
            return v.replace(tzinfo=DEFAULT_TIMEZONE)
        return v
    
    @model_validator(mode="after")
    def validate_times(self) -> "CalendarEvent":
        """Validate event times and ensure end time is after start time."""
        # Check for DST transitions
        start_transition, start_dst = get_dst_transition_info(self.start_time, self.start_time.tzinfo)
        end_transition, end_dst = get_dst_transition_info(self.end_time, self.end_time.tzinfo)
        
        if start_transition or end_transition:
            logger.warning(
                "event_spans_dst_transition",
                event_id=self.id,
                start_time=self.start_time.isoformat(),
                end_time=self.end_time.isoformat(),
                start_transition=start_transition,
                end_transition=end_transition,
            )
        
        # Convert both times to UTC for comparison
        start_utc = self.start_time.astimezone(ZoneInfo("UTC"))
        end_utc = self.end_time.astimezone(ZoneInfo("UTC"))
        
        if end_utc <= start_utc:
            raise ValidationError(
                message="Event end time must be after start time",
                field="end_time",
                details={
                    "start_time": self.start_time.isoformat(),
                    "end_time": self.end_time.isoformat(),
                    "start_timezone": format_timezone_info(self.start_time),
                    "end_timezone": format_timezone_info(self.end_time),
                },
            )
        return self
    
    def to_sydney_time(self) -> "CalendarEvent":
        """Convert event times to Sydney timezone."""
        return CalendarEvent(
            **{
                **self.model_dump(),
                "start_time": convert_to_timezone(self.start_time, SYDNEY_TIMEZONE),
                "end_time": convert_to_timezone(self.end_time, SYDNEY_TIMEZONE),
                "created_at": convert_to_timezone(self.created_at, SYDNEY_TIMEZONE) if self.created_at else None,
                "updated_at": convert_to_timezone(self.updated_at, SYDNEY_TIMEZONE) if self.updated_at else None,
            }
        )
    
    def get_timezone_info(self) -> Dict[str, Any]:
        """Get detailed timezone information for the event."""
        return {
            "start_time": {
                "timezone": format_timezone_info(self.start_time),
                "is_dst_transition": is_dst_transition(self.start_time, self.start_time.tzinfo),
            },
            "end_time": {
                "timezone": format_timezone_info(self.end_time),
                "is_dst_transition": is_dst_transition(self.end_time, self.end_time.tzinfo),
            },
        }
    
    def is_all_day(self) -> bool:
        """Check if the event is an all-day event."""
        return (
            self.start_time.hour == 0
            and self.start_time.minute == 0
            and self.end_time.hour == 0
            and self.end_time.minute == 0
            and (self.end_time - self.start_time).days >= 1
        )
    
    def duration(self) -> timedelta:
        """Calculate the event duration."""
        return self.end_time - self.start_time
    
    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> "CalendarEvent":
        """
        Create a CalendarEvent instance from Motion API data.
        
        Args:
            data: Raw event data from Motion API
            
        Returns:
            CalendarEvent: Validated and transformed event instance
            
        Raises:
            ValidationError: If the data is invalid
        """
        try:
            # Transform API data to match our model
            event_data = {
                "id": data["id"],
                "title": data["title"],
                "start_time": datetime.fromisoformat(data["start"]),
                "end_time": datetime.fromisoformat(data["end"]),
                "status": EventStatus(data.get("status", "confirmed")),
                "type": EventType(data.get("type", "meeting")),
                "description": data.get("description"),
                "location": data.get("location"),
                "attendees": data.get("attendees", []),
                "calendar_id": data.get("calendar_id"),
                "created_at": datetime.fromisoformat(data["created_at"]) if "created_at" in data else None,
                "updated_at": datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else None,
                "metadata": {k: v for k, v in data.items() if k not in {
                    "id", "title", "start", "end", "status", "type",
                    "description", "location", "attendees", "calendar_id",
                    "created_at", "updated_at",
                }},
            }
            
            return cls(**event_data)
            
        except (KeyError, ValueError) as e:
            raise ValidationError(
                message=f"Invalid event data: {str(e)}",
                details={"raw_data": data},
                cause=e,
            )


class CalendarEventCollection:
    """
    Collection of calendar events with filtering and sorting capabilities.
    
    This class provides methods for working with multiple calendar events,
    including filtering, sorting, and grouping operations.
    """
    
    def __init__(self, events: List[CalendarEvent]):
        """Initialize with a list of calendar events."""
        self.events = events
    
    def filter_by_date(self, date: datetime) -> "CalendarEventCollection":
        """Filter events to only those occurring on the specified date."""
        date_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        date_end = date_start + timedelta(days=1)
        
        filtered_events = [
            event for event in self.events
            if (date_start <= event.start_time < date_end)
            or (date_start <= event.end_time < date_end)
            or (event.start_time <= date_start and event.end_time >= date_end)
        ]
        
        return CalendarEventCollection(filtered_events)
    
    def filter_by_status(self, status: EventStatus) -> "CalendarEventCollection":
        """Filter events by status."""
        return CalendarEventCollection([
            event for event in self.events
            if event.status == status
        ])
    
    def filter_by_type(self, event_type: EventType) -> "CalendarEventCollection":
        """Filter events by type."""
        return CalendarEventCollection([
            event for event in self.events
            if event.type == event_type
        ])
    
    def sort_by_start_time(self, reverse: bool = False) -> "CalendarEventCollection":
        """Sort events by start time."""
        sorted_events = sorted(
            self.events,
            key=lambda e: e.start_time,
            reverse=reverse,
        )
        return CalendarEventCollection(sorted_events)
    
    def group_by_date(self) -> Dict[datetime, List[CalendarEvent]]:
        """Group events by date."""
        grouped: Dict[datetime, List[CalendarEvent]] = {}
        
        for event in self.events:
            date = event.start_time.date()
            if date not in grouped:
                grouped[date] = []
            grouped[date].append(event)
        
        return grouped
    
    def to_sydney_time(self) -> "CalendarEventCollection":
        """Convert all events to Sydney timezone."""
        return CalendarEventCollection([
            event.to_sydney_time()
            for event in self.events
        ])
    
    def __len__(self) -> int:
        return len(self.events)
    
    def __iter__(self):
        return iter(self.events)
    
    def __getitem__(self, index: int) -> CalendarEvent:
        return self.events[index] 