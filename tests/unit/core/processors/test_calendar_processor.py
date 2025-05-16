"""
Unit tests for calendar event processor.

This module tests the processing of calendar events for the daily digest email,
including filtering, sorting, formatting, and grouping operations.
"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from src.core.models.calendar import (
    CalendarEvent,
    CalendarEventCollection,
    EventStatus,
    EventType,
    SYDNEY_TIMEZONE,
)
from src.core.processors.calendar import CalendarEventProcessor
from src.utils.exceptions import ValidationError

# Rename module to avoid conflict
__name__ = "test_calendar_processor"


# Test data
def create_test_event(
    event_id: str,
    title: str,
    start_time: datetime,
    end_time: datetime,
    status: EventStatus = EventStatus.CONFIRMED,
    event_type: EventType = EventType.MEETING,
    **kwargs,
) -> CalendarEvent:
    """Helper function to create test events."""
    return CalendarEvent(
        id=event_id,
        title=title,
        start_time=start_time,
        end_time=end_time,
        status=status,
        type=event_type,
        **kwargs,
    )


@pytest.fixture
def test_events():
    """Create a collection of test events."""
    base_time = datetime(2024, 3, 20, tzinfo=SYDNEY_TIMEZONE)
    
    events = [
        # Morning events
        create_test_event(
            "event_1",
            "Morning Meeting",
            base_time.replace(hour=9),
            base_time.replace(hour=10),
            location="Room A",
            attendees=["alice@example.com"],
        ),
        create_test_event(
            "event_2",
            "Early Call",
            base_time.replace(hour=8),
            base_time.replace(hour=8, minute=30),
            event_type=EventType.TASK,
        ),
        # Afternoon events
        create_test_event(
            "event_3",
            "Team Lunch",
            base_time.replace(hour=12, minute=30),
            base_time.replace(hour=13, minute=30),
            location="Café",
            attendees=["alice@example.com", "bob@example.com"],
        ),
        create_test_event(
            "event_4",
            "Project Review",
            base_time.replace(hour=14),
            base_time.replace(hour=15, minute=30),
            event_type=EventType.MEETING,
        ),
        # Evening events
        create_test_event(
            "event_5",
            "Dinner",
            base_time.replace(hour=18),
            base_time.replace(hour=19, minute=30),
            location="Restaurant",
        ),
        # Events for next day
        create_test_event(
            "event_6",
            "Next Day Meeting",
            base_time + timedelta(days=1),
            base_time + timedelta(days=1, hours=1),
        ),
        # Cancelled event
        create_test_event(
            "event_7",
            "Cancelled Meeting",
            base_time.replace(hour=11),
            base_time.replace(hour=12),
            status=EventStatus.CANCELLED,
        ),
        # All-day event
        create_test_event(
            "event_8",
            "All Day Event",
            base_time.replace(hour=0),
            base_time.replace(hour=0) + timedelta(days=1),
            event_type=EventType.REMINDER,
        ),
    ]
    
    return CalendarEventCollection(events)


def test_get_daily_digest_events(test_events):
    """Test filtering events for daily digest."""
    processor = CalendarEventProcessor(test_events)
    date = datetime(2024, 3, 20, tzinfo=SYDNEY_TIMEZONE)
    
    digest_events = processor.get_daily_digest_events(date)
    
    # Should only include confirmed events for the specified date
    assert len(digest_events) == 6  # Excludes cancelled and next day events
    assert all(event.status == EventStatus.CONFIRMED for event in digest_events)
    assert all(event.start_time.date() == date.date() for event in digest_events)
    
    # Should be sorted chronologically
    event_times = [event.start_time for event in digest_events]
    assert event_times == sorted(event_times)


def test_group_events_by_time_of_day(test_events):
    """Test grouping events by time of day."""
    processor = CalendarEventProcessor(test_events)
    date = datetime(2024, 3, 20, tzinfo=SYDNEY_TIMEZONE)
    daily_events = processor.get_daily_digest_events(date)
    
    groups = processor.group_events_by_time_of_day(daily_events)
    
    # Check group counts
    assert len(groups["morning"]) == 3  # Early Call, Morning Meeting, All Day Event
    assert len(groups["afternoon"]) == 2  # Team Lunch, Project Review
    assert len(groups["evening"]) == 1  # Dinner
    
    # Verify event assignments
    morning_titles = {event.title for event in groups["morning"]}
    assert "Early Call" in morning_titles
    assert "Morning Meeting" in morning_titles
    assert "All Day Event" in morning_titles
    
    afternoon_titles = {event.title for event in groups["afternoon"]}
    assert "Team Lunch" in afternoon_titles
    assert "Project Review" in afternoon_titles
    
    evening_titles = {event.title for event in groups["evening"]}
    assert "Dinner" in evening_titles


def test_format_event_for_digest(test_events):
    """Test event formatting for digest display."""
    processor = CalendarEventProcessor(test_events)
    event = test_events[0]  # Morning Meeting
    
    formatted = processor.format_event_for_digest(event)
    
    assert formatted["title"] == "Morning Meeting"
    assert formatted["time"] == "9:00 AM - 10:00 AM"
    assert formatted["location"] == " at Room A"
    assert formatted["attendees"] == " with alice@example.com"
    assert formatted["type"] == "Meeting"
    
    # Test all-day event formatting
    all_day_event = test_events[7]  # All Day Event
    formatted_all_day = processor.format_event_for_digest(all_day_event)
    assert formatted_all_day["time"] == "All day"


def test_get_digest_summary(test_events):
    """Test generation of complete digest summary."""
    processor = CalendarEventProcessor(test_events)
    date = datetime(2024, 3, 20, tzinfo=SYDNEY_TIMEZONE)
    
    summary = processor.get_digest_summary(date)
    
    # Check summary structure
    assert summary["date"] == "Wednesday, March 20, 2024"
    assert summary["total_events"] == 6
    
    # Check event counts by period
    assert summary["events_by_period"]["morning"] == 3
    assert summary["events_by_period"]["afternoon"] == 2
    assert summary["events_by_period"]["evening"] == 1
    
    # Check event type distribution
    assert summary["events_by_type"][EventType.MEETING] == 2
    assert summary["events_by_type"][EventType.TASK] == 1
    assert summary["events_by_type"][EventType.REMINDER] == 1
    
    # Check formatted events
    assert "Morning Meeting" in [e["title"] for e in summary["formatted_events"]["morning"]]
    assert "Team Lunch" in [e["title"] for e in summary["formatted_events"]["afternoon"]]
    assert "Dinner" in [e["title"] for e in summary["formatted_events"]["evening"]]


def test_validate_digest_events(test_events):
    """Test validation of events for digest inclusion."""
    processor = CalendarEventProcessor(test_events)
    
    # Test valid events
    date = datetime(2024, 3, 20, tzinfo=SYDNEY_TIMEZONE)
    daily_events = processor.get_daily_digest_events(date)
    is_valid, messages = processor.validate_digest_events(daily_events)
    assert is_valid
    assert not messages
    
    # Test invalid events
    invalid_events = CalendarEventCollection([
        # Missing title
        create_test_event(
            "invalid_1",
            "",
            datetime(2024, 3, 20, 9, tzinfo=SYDNEY_TIMEZONE),
            datetime(2024, 3, 20, 10, tzinfo=SYDNEY_TIMEZONE),
        ),
        # Invalid times
        create_test_event(
            "invalid_2",
            "Invalid Times",
            None,  # type: ignore
            None,  # type: ignore
        ),
        # Not confirmed
        create_test_event(
            "invalid_3",
            "Tentative Meeting",
            datetime(2024, 3, 20, 11, tzinfo=SYDNEY_TIMEZONE),
            datetime(2024, 3, 20, 12, tzinfo=SYDNEY_TIMEZONE),
            status=EventStatus.TENTATIVE,
        ),
        # Overlapping events
        create_test_event(
            "invalid_4",
            "Overlapping 1",
            datetime(2024, 3, 20, 14, tzinfo=SYDNEY_TIMEZONE),
            datetime(2024, 3, 20, 16, tzinfo=SYDNEY_TIMEZONE),
        ),
        create_test_event(
            "invalid_5",
            "Overlapping 2",
            datetime(2024, 3, 20, 15, tzinfo=SYDNEY_TIMEZONE),
            datetime(2024, 3, 20, 17, tzinfo=SYDNEY_TIMEZONE),
        ),
    ])
    
    is_valid, messages = processor.validate_digest_events(invalid_events)
    assert not is_valid
    assert len(messages) == 4  # 4 validation errors
    assert any("has no title" in msg for msg in messages)
    assert any("has invalid times" in msg for msg in messages)
    assert any("is not confirmed" in msg for msg in messages)
    assert any("Events overlap" in msg for msg in messages) 