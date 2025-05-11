"""
Unit tests for calendar data models.

This module tests the validation, transformation, and timezone handling
of calendar event models.
"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from pydantic import ValidationError as PydanticValidationError

from src.core.models.calendar import (
    CalendarEvent,
    CalendarEventCollection,
    EventStatus,
    EventType,
    SYDNEY_TIMEZONE,
)
from src.utils.exceptions import ValidationError


# Test data
VALID_EVENT_DATA = {
    "id": "event_123",
    "title": "Test Meeting",
    "start": "2024-03-20T10:00:00+10:00",
    "end": "2024-03-20T11:00:00+10:00",
    "status": "confirmed",
    "type": "meeting",
    "description": "Test meeting description",
    "location": "Conference Room A",
    "attendees": ["test@example.com"],
    "calendar_id": "cal_123",
    "created_at": "2024-03-19T15:00:00+10:00",
    "updated_at": "2024-03-19T15:30:00+10:00",
}

UTC_TIMEZONE = ZoneInfo("UTC")


def test_create_valid_event():
    """Test creating a valid calendar event."""
    event = CalendarEvent.from_api_data(VALID_EVENT_DATA)
    
    assert event.id == "event_123"
    assert event.title == "Test Meeting"
    assert event.start_time == datetime.fromisoformat("2024-03-20T10:00:00+10:00")
    assert event.end_time == datetime.fromisoformat("2024-03-20T11:00:00+10:00")
    assert event.status == EventStatus.CONFIRMED
    assert event.type == EventType.MEETING
    assert event.description == "Test meeting description"
    assert event.location == "Conference Room A"
    assert event.attendees == ["test@example.com"]
    assert event.calendar_id == "cal_123"
    assert event.created_at == datetime.fromisoformat("2024-03-19T15:00:00+10:00")
    assert event.updated_at == datetime.fromisoformat("2024-03-19T15:30:00+10:00")


def test_create_event_with_missing_required_fields():
    """Test creating an event with missing required fields."""
    invalid_data = VALID_EVENT_DATA.copy()
    del invalid_data["id"]
    
    with pytest.raises(ValidationError) as exc_info:
        CalendarEvent.from_api_data(invalid_data)
    
    assert "Invalid event data" in str(exc_info.value)


def test_create_event_with_invalid_times():
    """Test creating an event with invalid time values."""
    invalid_data = VALID_EVENT_DATA.copy()
    invalid_data["end"] = "2024-03-20T09:00:00+10:00"  # End before start
    
    with pytest.raises(ValidationError) as exc_info:
        CalendarEvent.from_api_data(invalid_data)
    
    assert "Event end time must be after start time" in str(exc_info.value)


def test_create_event_with_invalid_status():
    """Test creating an event with an invalid status."""
    invalid_data = VALID_EVENT_DATA.copy()
    invalid_data["status"] = "invalid_status"
    
    with pytest.raises(ValidationError) as exc_info:
        CalendarEvent.from_api_data(invalid_data)
    
    assert "Invalid event data" in str(exc_info.value)


def test_create_event_with_invalid_type():
    """Test creating an event with an invalid type."""
    invalid_data = VALID_EVENT_DATA.copy()
    invalid_data["type"] = "invalid_type"
    
    with pytest.raises(ValidationError) as exc_info:
        CalendarEvent.from_api_data(invalid_data)
    
    assert "Invalid event data" in str(exc_info.value)


def test_event_timezone_handling():
    """Test timezone handling for event times."""
    # Create event with UTC times
    utc_data = VALID_EVENT_DATA.copy()
    utc_data["start"] = "2024-03-20T00:00:00+00:00"
    utc_data["end"] = "2024-03-20T01:00:00+00:00"
    
    event = CalendarEvent.from_api_data(utc_data)
    
    # Convert to Sydney time
    sydney_event = event.to_sydney_time()
    
    # Check times are in Sydney timezone
    assert sydney_event.start_time.tzinfo == SYDNEY_TIMEZONE
    assert sydney_event.end_time.tzinfo == SYDNEY_TIMEZONE
    assert sydney_event.start_time.hour == 10  # UTC+10
    assert sydney_event.end_time.hour == 11


def test_event_duration():
    """Test event duration calculation."""
    event = CalendarEvent.from_api_data(VALID_EVENT_DATA)
    assert event.duration() == timedelta(hours=1)


def test_event_is_all_day():
    """Test all-day event detection."""
    # Create an all-day event
    all_day_data = VALID_EVENT_DATA.copy()
    all_day_data["start"] = "2024-03-20T00:00:00+10:00"
    all_day_data["end"] = "2024-03-21T00:00:00+10:00"
    
    event = CalendarEvent.from_api_data(all_day_data)
    assert event.is_all_day()
    
    # Regular event should not be all-day
    regular_event = CalendarEvent.from_api_data(VALID_EVENT_DATA)
    assert not regular_event.is_all_day()


def test_event_collection_filtering():
    """Test filtering events in a collection."""
    # Create test events
    events = [
        CalendarEvent.from_api_data({
            **VALID_EVENT_DATA,
            "id": "event_1",
            "start": "2024-03-20T10:00:00+10:00",
            "end": "2024-03-20T11:00:00+10:00",
            "status": "confirmed",
            "type": "meeting",
        }),
        CalendarEvent.from_api_data({
            **VALID_EVENT_DATA,
            "id": "event_2",
            "start": "2024-03-20T14:00:00+10:00",
            "end": "2024-03-20T15:00:00+10:00",
            "status": "tentative",
            "type": "task",
        }),
        CalendarEvent.from_api_data({
            **VALID_EVENT_DATA,
            "id": "event_3",
            "start": "2024-03-21T10:00:00+10:00",
            "end": "2024-03-21T11:00:00+10:00",
            "status": "confirmed",
            "type": "meeting",
        }),
    ]
    
    collection = CalendarEventCollection(events)
    
    # Test filtering by date
    date = datetime(2024, 3, 20, tzinfo=SYDNEY_TIMEZONE)
    filtered = collection.filter_by_date(date)
    assert len(filtered) == 2
    assert all(e.start_time.date() == date.date() for e in filtered)
    
    # Test filtering by status
    confirmed = collection.filter_by_status(EventStatus.CONFIRMED)
    assert len(confirmed) == 2
    assert all(e.status == EventStatus.CONFIRMED for e in confirmed)
    
    # Test filtering by type
    meetings = collection.filter_by_type(EventType.MEETING)
    assert len(meetings) == 2
    assert all(e.type == EventType.MEETING for e in meetings)


def test_event_collection_sorting():
    """Test sorting events in a collection."""
    # Create test events in random order
    events = [
        CalendarEvent.from_api_data({
            **VALID_EVENT_DATA,
            "id": "event_2",
            "start": "2024-03-20T14:00:00+10:00",
            "end": "2024-03-20T15:00:00+10:00",
        }),
        CalendarEvent.from_api_data({
            **VALID_EVENT_DATA,
            "id": "event_1",
            "start": "2024-03-20T10:00:00+10:00",
            "end": "2024-03-20T11:00:00+10:00",
        }),
        CalendarEvent.from_api_data({
            **VALID_EVENT_DATA,
            "id": "event_3",
            "start": "2024-03-20T16:00:00+10:00",
            "end": "2024-03-20T17:00:00+10:00",
        }),
    ]
    
    collection = CalendarEventCollection(events)
    
    # Test ascending sort
    sorted_asc = collection.sort_by_start_time()
    assert [e.id for e in sorted_asc] == ["event_1", "event_2", "event_3"]
    
    # Test descending sort
    sorted_desc = collection.sort_by_start_time(reverse=True)
    assert [e.id for e in sorted_desc] == ["event_3", "event_2", "event_1"]


def test_event_collection_grouping():
    """Test grouping events by date."""
    # Create test events on different dates
    events = [
        CalendarEvent.from_api_data({
            **VALID_EVENT_DATA,
            "id": "event_1",
            "start": "2024-03-20T10:00:00+10:00",
            "end": "2024-03-20T11:00:00+10:00",
        }),
        CalendarEvent.from_api_data({
            **VALID_EVENT_DATA,
            "id": "event_2",
            "start": "2024-03-20T14:00:00+10:00",
            "end": "2024-03-20T15:00:00+10:00",
        }),
        CalendarEvent.from_api_data({
            **VALID_EVENT_DATA,
            "id": "event_3",
            "start": "2024-03-21T10:00:00+10:00",
            "end": "2024-03-21T11:00:00+10:00",
        }),
    ]
    
    collection = CalendarEventCollection(events)
    grouped = collection.group_by_date()
    
    # Check grouping
    assert len(grouped) == 2
    assert len(grouped[datetime(2024, 3, 20).date()]) == 2
    assert len(grouped[datetime(2024, 3, 21).date()]) == 1


def test_event_collection_timezone_conversion():
    """Test converting all events in a collection to Sydney time."""
    # Create events in UTC
    events = [
        CalendarEvent.from_api_data({
            **VALID_EVENT_DATA,
            "id": "event_1",
            "start": "2024-03-20T00:00:00+00:00",
            "end": "2024-03-20T01:00:00+00:00",
        }),
        CalendarEvent.from_api_data({
            **VALID_EVENT_DATA,
            "id": "event_2",
            "start": "2024-03-20T04:00:00+00:00",
            "end": "2024-03-20T05:00:00+00:00",
        }),
    ]
    
    collection = CalendarEventCollection(events)
    sydney_collection = collection.to_sydney_time()
    
    # Check all events are in Sydney timezone
    for event in sydney_collection:
        assert event.start_time.tzinfo == SYDNEY_TIMEZONE
        assert event.end_time.tzinfo == SYDNEY_TIMEZONE
        assert event.start_time.hour in (10, 14)  # UTC+10
        assert event.end_time.hour in (11, 15) 