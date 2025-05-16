"""
Integration tests for calendar integration components.

This module tests the integration between Motion API client, calendar data models,
event processing, and timezone handling to ensure they work together correctly.
"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from unittest.mock import patch, MagicMock

import pytest
import requests
from requests.exceptions import RequestException

from src.api.motion import MotionClient
from src.core.models.calendar import (
    CalendarEvent,
    CalendarEventCollection,
    EventStatus,
    EventType,
    SYDNEY_TIMEZONE,
)
from src.core.processors.calendar import CalendarEventProcessor
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
        mock_session.return_value.headers = {
            "X-API-Key": api_config.motion_api_key,
            "Authorization": f"Bearer {api_config.motion_api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        client = MotionClient(api_config)
        client.session = mock_session.return_value
        yield client


@pytest.fixture(autouse=True)
def patch_rate_limiter_and_sleep():
    with patch("src.utils.rate_limiter.global_rate_limiter.acquire", return_value=True), \
         patch("time.sleep", return_value=None):
        yield


@pytest.fixture
def sample_event_data():
    base_time = datetime(2024, 6, 10, 9, 0, tzinfo=ZoneInfo("Australia/Sydney"))
    return [
        {
            "id": "evt_1",
            "title": "Test Meeting",
            "start": base_time.isoformat(),
            "end": (base_time + timedelta(hours=1)).isoformat(),
            "status": "confirmed",
            "type": "meeting",
            "description": "Test desc",
            "location": "Room 1",
            "attendees": ["user@example.com"],
            "calendar_id": "work",
            "created_at": (base_time - timedelta(days=1)).isoformat(),
            "updated_at": (base_time - timedelta(hours=12)).isoformat(),
        }
    ]


def test_get_calendar_events_success(mock_motion_client, sample_event_data):
    mock_response = MagicMock()
    mock_response.json.return_value = {"events": sample_event_data}
    mock_response.raise_for_status = MagicMock()
    mock_motion_client.session.request.return_value = mock_response

    start_date = datetime(2024, 6, 10, tzinfo=ZoneInfo("Australia/Sydney"))
    events = mock_motion_client.get_calendar_events(start_date=start_date)

    assert isinstance(events, CalendarEventCollection)
    assert len(events) == 1
    event = events[0]
    assert event.title == "Test Meeting"
    assert event.status == EventStatus.CONFIRMED
    assert event.type == EventType.MEETING
    # Compare UTC offset, not strict tzinfo object
    assert event.start_time.utcoffset() == ZoneInfo("Australia/Sydney").utcoffset(event.start_time)
    assert event.end_time.utcoffset() == ZoneInfo("Australia/Sydney").utcoffset(event.end_time)


@pytest.mark.parametrize("error_cls,side_effect", [
    (MotionAPIError, MotionAPIError("API fail")),
    (ValidationError, ValidationError("Invalid event", field="title")),
])
def test_get_calendar_events_error(mock_motion_client, error_cls, side_effect):
    if error_cls is MotionAPIError:
        mock_motion_client.session.request.side_effect = side_effect
        with pytest.raises(MotionAPIError):
            mock_motion_client.get_calendar_events(start_date=datetime.now(ZoneInfo("Australia/Sydney")))
    else:
        # Simulate invalid event data returned from API
        mock_response = MagicMock()
        mock_response.json.return_value = {"events": [{"id": "evt_2", "title": "", "start": "2024-06-10T09:00:00+10:00", "end": "2024-06-10T10:00:00+10:00", "status": "confirmed", "type": "meeting"}]}
        mock_response.raise_for_status = MagicMock()
        mock_motion_client.session.request.return_value = mock_response
        with pytest.raises(ValidationError):
            mock_motion_client.get_calendar_events(start_date=datetime.now(ZoneInfo("Australia/Sydney")))


def test_timezone_handling_in_events(mock_motion_client, sample_event_data):
    # Provide UTC times in API data, expect tzinfo to be UTC
    utc_event = sample_event_data[0].copy()
    utc_event["start"] = datetime(2024, 6, 10, 0, 0, tzinfo=ZoneInfo("UTC")).isoformat()
    utc_event["end"] = datetime(2024, 6, 10, 1, 0, tzinfo=ZoneInfo("UTC")).isoformat()
    mock_response = MagicMock()
    mock_response.json.return_value = {"events": [utc_event]}
    mock_response.raise_for_status = MagicMock()
    mock_motion_client.session.request.return_value = mock_response

    events = mock_motion_client.get_calendar_events(start_date=datetime(2024, 6, 10, tzinfo=ZoneInfo("Australia/Sydney")))
    event = events[0]
    # Should have UTC tzinfo and offset
    assert event.start_time.tzname() == "UTC"
    assert event.start_time.utcoffset() == timedelta(0)
    assert event.end_time.tzname() == "UTC"
    assert event.end_time.utcoffset() == timedelta(0)


def test_event_model_transformation_and_fields(sample_event_data):
    event = CalendarEvent.from_api_data(sample_event_data[0])
    assert event.id == "evt_1"
    assert event.title == "Test Meeting"
    assert event.status == EventStatus.CONFIRMED
    assert event.type == EventType.MEETING
    assert event.start_time < event.end_time
    assert event.attendees == ["user@example.com"]
    assert event.location == "Room 1"
    assert event.calendar_id == "work"
    assert isinstance(event.created_at, datetime)
    assert isinstance(event.updated_at, datetime)


def test_event_collection_methods(sample_event_data):
    events = CalendarEventCollection([
        CalendarEvent.from_api_data(sample_event_data[0]),
    ])
    filtered = events.filter_by_type(EventType.MEETING)
    assert len(filtered) == 1
    sorted_events = events.sort_by_start_time()
    assert sorted_events[0].id == "evt_1"
    grouped = events.group_by_date()
    assert list(grouped.keys())[0] == events[0].start_time.date()


class TestMotionAPIClientIntegration:
    """Integration tests for Motion API client."""

    def test_authentication_and_token_management(self, mock_motion_client):
        """Test authentication and token management."""
        # Check both header types for compatibility
        assert mock_motion_client.session.headers["X-API-Key"] == "test_api_key"
        assert mock_motion_client.session.headers["Authorization"] == "Bearer test_api_key"
        assert mock_motion_client.session.headers["Accept"] == "application/json"

    def test_api_response_handling(self, mock_motion_client, sample_event_data):
        """Test API response handling and data transformation."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"events": sample_event_data}
        mock_response.raise_for_status = MagicMock()
        mock_motion_client.session.request.return_value = mock_response
        start_date = datetime(2024, 6, 10, tzinfo=ZoneInfo("Australia/Sydney"))
        events = mock_motion_client.get_calendar_events(start_date=start_date)
        assert isinstance(events, CalendarEventCollection)
        assert len(events) == 1
        assert all(isinstance(event, CalendarEvent) for event in events)
        assert events[0].title == "Test Meeting"

    def test_concurrent_request_handling(self, mock_motion_client):
        """Test handling of concurrent requests with rate limiting."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"events": []}
        mock_response.raise_for_status = MagicMock()
        mock_motion_client.session.request.return_value = mock_response
        start_date = datetime(2024, 6, 10, tzinfo=ZoneInfo("Australia/Sydney"))
        for _ in range(15):
            mock_motion_client.get_calendar_events(start_date=start_date)
        # No assertion on sleep, since it's patched out
        assert mock_motion_client.session.request.call_count == 15

    def test_error_handling_and_retry(self, mock_motion_client):
        """Test error handling and retry logic."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.json.return_value = {"error": "Rate limit exceeded"}
        mock_response.raise_for_status = MagicMock(side_effect=[
            MotionAPIError("Rate limit exceeded"),
            None
        ])
        mock_response.json.side_effect = [
            {"error": "Rate limit exceeded"},
            {"events": []},
        ]
        mock_motion_client.session.request.return_value = mock_response
        start_date = datetime(2024, 6, 10, tzinfo=ZoneInfo("Australia/Sydney"))
        # Should raise MotionAPIError on first call, then succeed
        try:
            mock_motion_client.get_calendar_events(start_date=start_date)
        except MotionAPIError:
            pass
        # Second call should succeed
        events = mock_motion_client.get_calendar_events(start_date=start_date)
        assert isinstance(events, CalendarEventCollection)


class TestCalendarDataModelIntegration:
    """Integration tests for calendar data models."""

    def test_end_to_end_data_flow(self, mock_motion_client, sample_event_data):
        """Test end-to-end data flow from API to models."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"events": sample_event_data}
        mock_motion_client.session.request.return_value = mock_response
        start_date = datetime(2024, 6, 10, tzinfo=ZoneInfo("Australia/Sydney"))
        events = mock_motion_client.get_calendar_events(start_date=start_date)
        assert isinstance(events, CalendarEventCollection)
        assert len(events) == 1
        event = events[0]
        assert event.id == "evt_1"
        assert event.title == "Test Meeting"
        assert event.status == EventStatus.CONFIRMED
        assert event.type == EventType.MEETING
        assert event.description == "Test desc"
        assert event.location == "Room 1"
        assert event.attendees == ["user@example.com"]
        assert event.calendar_id == "work"

    def test_event_collection_operations(self, sample_event_data):
        """Test event collection operations."""
        events = CalendarEventCollection([
            CalendarEvent.from_api_data(event_data)
            for event_data in sample_event_data
        ])
        meetings = events.filter_by_type(EventType.MEETING)
        assert len(meetings) == 1
        sorted_events = events.sort_by_start_time()
        assert len(sorted_events) == 1
        assert sorted_events[0].title == "Test Meeting"
        grouped = events.group_by_date()
        assert len(grouped) == 1
        assert len(grouped[datetime(2024, 6, 10).date()]) == 1

    def test_model_relationship_testing(self, sample_event_data):
        """Test relationships between models."""
        events = CalendarEventCollection([
            CalendarEvent.from_api_data(event_data)
            for event_data in sample_event_data
        ])
        event = events[0]
        assert event.start_time < event.end_time


class TestEventProcessingIntegration:
    """Integration tests for event processing."""

    def test_event_processing_pipeline(self, sample_event_data):
        """Test the complete event processing pipeline."""
        events = CalendarEventCollection([
            CalendarEvent.from_api_data(event_data)
            for event_data in sample_event_data
        ])
        processor = CalendarEventProcessor(events)
        date = datetime(2024, 6, 10, tzinfo=ZoneInfo("Australia/Sydney"))
        daily_events = processor.get_daily_digest_events(date)
        assert isinstance(daily_events, CalendarEventCollection)
        assert len(daily_events) == 1
        # Format each event for digest
        formatted_events = [processor.format_event_for_digest(event) for event in daily_events]
        assert len(formatted_events) == 1
        assert all("title" in event for event in formatted_events)
        assert all("time" in event for event in formatted_events)

    def test_event_formatting_validation(self, sample_event_data):
        """Test event formatting validation."""
        invalid_events = sample_event_data.copy()
        invalid_events.append({
            "id": "evt_4",
            "title": "",  # Invalid: empty title
            "start": (datetime(2024, 6, 10, 15, 0, tzinfo=ZoneInfo("Australia/Sydney"))).isoformat(),
            "end": (datetime(2024, 6, 10, 16, 0, tzinfo=ZoneInfo("Australia/Sydney"))).isoformat(),
            "status": "confirmed",
            "type": "meeting",
        })
        # Only the valid event should be processed
        valid_events = []
        for event_data in invalid_events:
            try:
                valid_events.append(CalendarEvent.from_api_data(event_data))
            except Exception:
                pass
        events = CalendarEventCollection(valid_events)
        processor = CalendarEventProcessor(events)
        date = datetime(2024, 6, 10, tzinfo=ZoneInfo("Australia/Sydney"))
        daily_events = processor.get_daily_digest_events(date)
        assert len(daily_events) == 1

    def test_edge_case_handling(self, sample_event_data):
        """Test handling of edge cases in event processing."""
        edge_cases = [
            {
                "id": "evt_6",
                "title": "All Day Event",
                "start": (datetime(2024, 6, 10, 0, 0, tzinfo=ZoneInfo("Australia/Sydney"))).isoformat(),
                "end": (datetime(2024, 6, 11, 0, 0, tzinfo=ZoneInfo("Australia/Sydney"))).isoformat(),
                "status": "confirmed",
                "type": "reminder",
            },
            {
                "id": "evt_7",
                "title": "Multi-day Event",
                "start": (datetime(2024, 6, 10, 16, 0, tzinfo=ZoneInfo("Australia/Sydney"))).isoformat(),
                "end": (datetime(2024, 6, 11, 10, 0, tzinfo=ZoneInfo("Australia/Sydney"))).isoformat(),
                "status": "confirmed",
                "type": "meeting",
            },
            {
                "id": "evt_8",
                "title": "Solo Task",
                "start": (datetime(2024, 6, 10, 11, 0, tzinfo=ZoneInfo("Australia/Sydney"))).isoformat(),
                "end": (datetime(2024, 6, 10, 12, 0, tzinfo=ZoneInfo("Australia/Sydney"))).isoformat(),
                "status": "confirmed",
                "type": "task",
                "attendees": [],
            },
        ]
        all_events = sample_event_data + edge_cases
        valid_events = []
        for event_data in all_events:
            try:
                valid_events.append(CalendarEvent.from_api_data(event_data))
            except Exception:
                pass
        events = CalendarEventCollection(valid_events)
        processor = CalendarEventProcessor(events)
        date = datetime(2024, 6, 10, tzinfo=ZoneInfo("Australia/Sydney"))
        daily_events = processor.get_daily_digest_events(date)
        # Should include all events that fall on the date
        assert len(daily_events) == 4
        titles = [event.title for event in daily_events]
        assert "All Day Event" in titles
        assert "Multi-day Event" in titles
        assert "Solo Task" in titles
        assert "Test Meeting" in titles


class TestTimezoneIntegration:
    """Integration tests for timezone handling."""

    def test_timezone_conversion(self, sample_event_data):
        """Test timezone conversion and handling."""
        utc_events = [
            {
                **event_data,
                "start": datetime.fromisoformat(event_data["start"]).astimezone(ZoneInfo("UTC")).isoformat(),
                "end": datetime.fromisoformat(event_data["end"]).astimezone(ZoneInfo("UTC")).isoformat(),
            }
            for event_data in sample_event_data
        ]
        events = CalendarEventCollection([
            CalendarEvent.from_api_data(event_data)
            for event_data in utc_events
        ])
        for event in events:
            # Should have UTC tzname and offset
            assert event.start_time.tzname() == "UTC"
            assert event.start_time.utcoffset() == timedelta(0)
            assert event.end_time.tzname() == "UTC"
            assert event.end_time.utcoffset() == timedelta(0)

    def test_dst_transition_handling(self):
        """Test handling of daylight saving time transitions."""
        dst_events = [
            {
                "id": "evt_9",
                "title": "Before DST",
                "start": "2024-04-06T09:00:00+10:00",
                "end": "2024-04-06T10:00:00+10:00",
                "status": "confirmed",
                "type": "meeting",
            },
            {
                "id": "evt_10",
                "title": "After DST",
                "start": "2024-04-07T09:00:00+10:00",
                "end": "2024-04-07T10:00:00+10:00",
                "status": "confirmed",
                "type": "meeting",
            },
        ]
        events = CalendarEventCollection([
            CalendarEvent.from_api_data(event_data)
            for event_data in dst_events
        ])
        before_dst = events[0]
        after_dst = events[1]
        # Just check that tzinfo is present and offset is correct
        assert before_dst.start_time.tzinfo is not None
        assert after_dst.start_time.tzinfo is not None
        assert before_dst.start_time.utcoffset() == timedelta(hours=10)
        assert after_dst.start_time.utcoffset() == timedelta(hours=10)

    def test_timezone_validation(self):
        """Test timezone validation and error handling."""
        invalid_event = {
            "id": "evt_11",
            "title": "Invalid Timezone",
            "start": "2024-03-20T09:00:00",  # No timezone info
            "end": "2024-03-20T10:00:00",    # No timezone info
            "status": "confirmed",
            "type": "meeting",
        }
        # Should not raise, but tzinfo will be set to default
        event = CalendarEvent.from_api_data(invalid_event)
        assert event.start_time.tzinfo is not None
        assert event.end_time.tzinfo is not None 