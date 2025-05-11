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
from src.utils.config import APIConfig
from src.utils.exceptions import MotionAPIError, ValidationError
from src.utils.rate_limiter import global_rate_limiter


@pytest.fixture
def api_config():
    """Create a test API configuration."""
    return APIConfig(
        motion_api_key="test_api_key",
        motion_api_url="https://api.motion.dev/v1",
        weather_api_key="test_weather_key",
        weather_api_url="https://api.weatherapi.com/v1",
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
def sample_events():
    """Create a collection of sample events for testing."""
    base_time = datetime(2024, 3, 20, 9, 0, tzinfo=SYDNEY_TIMEZONE)
    
    return [
        {
            "id": "evt_1",
            "title": "Morning Meeting",
            "start": (base_time).isoformat(),
            "end": (base_time + timedelta(hours=1)).isoformat(),
            "status": "confirmed",
            "type": "meeting",
            "description": "Daily standup",
            "location": "Conference Room A",
            "attendees": ["user@example.com"],
            "calendar_id": "work",
            "created_at": (base_time - timedelta(days=1)).isoformat(),
            "updated_at": (base_time - timedelta(hours=12)).isoformat(),
        },
        {
            "id": "evt_2",
            "title": "Lunch Break",
            "start": (base_time + timedelta(hours=4)).isoformat(),
            "end": (base_time + timedelta(hours=5)).isoformat(),
            "status": "confirmed",
            "type": "break",
            "description": "Lunch break",
            "location": "Cafeteria",
            "attendees": [],
            "calendar_id": "work",
            "created_at": (base_time - timedelta(days=1)).isoformat(),
            "updated_at": (base_time - timedelta(hours=12)).isoformat(),
        },
        {
            "id": "evt_3",
            "title": "Project Review",
            "start": (base_time + timedelta(hours=6)).isoformat(),
            "end": (base_time + timedelta(hours=7)).isoformat(),
            "status": "confirmed",
            "type": "meeting",
            "description": "Project status review",
            "location": "Conference Room B",
            "attendees": ["user@example.com", "manager@example.com"],
            "calendar_id": "work",
            "created_at": (base_time - timedelta(days=1)).isoformat(),
            "updated_at": (base_time - timedelta(hours=12)).isoformat(),
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

    def test_api_response_handling(self, mock_motion_client, sample_events):
        """Test API response handling and data transformation."""
        # Mock successful response with all necessary methods
        mock_response = MagicMock()
        mock_response.json.return_value = {"events": sample_events}
        mock_response.raise_for_status = MagicMock()
        mock_motion_client.session.request.return_value = mock_response

        # Get events
        start_date = datetime(2024, 3, 20, tzinfo=SYDNEY_TIMEZONE)
        events = mock_motion_client.get_calendar_events(start_date=start_date)

        # Verify request
        mock_motion_client.session.request.assert_called_once()
        call_args = mock_motion_client.session.request.call_args[1]
        assert call_args["method"] == "GET"
        assert call_args["url"] == "https://api.motion.dev/v1/events"
        assert "start" in call_args["params"]
        assert "end" in call_args["params"]

        # Verify response transformation
        assert isinstance(events, CalendarEventCollection)
        assert len(events) == 3
        assert all(isinstance(event, CalendarEvent) for event in events)
        assert events[0].title == "Morning Meeting"
        assert events[1].title == "Lunch Break"
        assert events[2].title == "Project Review"

    def test_concurrent_request_handling(self, mock_motion_client):
        """Test handling of concurrent requests with rate limiting."""
        # Mock successful responses with all necessary methods
        mock_response = MagicMock()
        mock_response.json.return_value = {"events": []}
        mock_response.raise_for_status = MagicMock()
        mock_motion_client.session.request.return_value = mock_response

        # Reset rate limiter to ensure clean state
        global_rate_limiter.reset()

        # Make multiple concurrent requests
        start_date = datetime(2024, 3, 20, tzinfo=SYDNEY_TIMEZONE)
        
        with patch("time.sleep") as mock_sleep:
            # Make 15 requests (should trigger rate limiting)
            for _ in range(15):
                mock_motion_client.get_calendar_events(start_date=start_date)

            # Verify rate limiting was enforced
            assert mock_sleep.call_count > 0
            assert mock_motion_client.session.request.call_count == 15

    def test_error_handling_and_retry(self, mock_motion_client):
        """Test error handling and retry logic."""
        # Mock failed request followed by success with all necessary methods
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.json.return_value = {"error": "Rate limit exceeded"}
        mock_response.raise_for_status = MagicMock(side_effect=[
            requests.exceptions.HTTPError("Rate limit exceeded", response=mock_response),
            None
        ])
        mock_response.json.side_effect = [
            {"error": "Rate limit exceeded"},
            {"events": []},
        ]
        mock_motion_client.session.request.return_value = mock_response

        # Reset rate limiter to ensure clean state
        global_rate_limiter.reset()

        # Attempt to get events
        start_date = datetime(2024, 3, 20, tzinfo=SYDNEY_TIMEZONE)
        with patch("time.sleep") as mock_sleep:
            events = mock_motion_client.get_calendar_events(start_date=start_date)
            
            # Verify retry behavior
            assert mock_sleep.call_count > 0
            assert mock_motion_client.session.request.call_count == 2
            assert isinstance(events, CalendarEventCollection)
            assert len(events) == 0


class TestCalendarDataModelIntegration:
    """Integration tests for calendar data models."""

    def test_end_to_end_data_flow(self, mock_motion_client, sample_events):
        """Test end-to-end data flow from API to models."""
        # Mock API response
        mock_response = MagicMock()
        mock_response.json.return_value = {"events": sample_events}
        mock_motion_client.session.request.return_value = mock_response

        # Get events from API
        start_date = datetime(2024, 3, 20, tzinfo=SYDNEY_TIMEZONE)
        events = mock_motion_client.get_calendar_events(start_date=start_date)

        # Verify data flow
        assert isinstance(events, CalendarEventCollection)
        assert len(events) == 3
        
        # Verify event data
        morning_meeting = events[0]
        assert morning_meeting.id == "evt_1"
        assert morning_meeting.title == "Morning Meeting"
        assert morning_meeting.status == EventStatus.CONFIRMED
        assert morning_meeting.type == EventType.MEETING
        assert morning_meeting.description == "Daily standup"
        assert morning_meeting.location == "Conference Room A"
        assert morning_meeting.attendees == ["user@example.com"]
        assert morning_meeting.calendar_id == "work"

    def test_event_collection_operations(self, sample_events):
        """Test event collection operations."""
        # Create event collection
        events = CalendarEventCollection([
            CalendarEvent.from_api_data(event_data)
            for event_data in sample_events
        ])

        # Test filtering
        meetings = events.filter_by_type(EventType.MEETING)
        assert len(meetings) == 2
        assert all(event.type == EventType.MEETING for event in meetings)

        # Test sorting
        sorted_events = events.sort_by_start_time()
        assert len(sorted_events) == 3
        assert sorted_events[0].title == "Morning Meeting"
        assert sorted_events[1].title == "Lunch Break"
        assert sorted_events[2].title == "Project Review"

        # Test grouping
        grouped = events.group_by_date()
        assert len(grouped) == 1  # All events on same day
        assert len(grouped[datetime(2024, 3, 20).date()]) == 3

    def test_model_relationship_testing(self, sample_events):
        """Test relationships between models."""
        # Create events with relationships
        events = CalendarEventCollection([
            CalendarEvent.from_api_data(event_data)
            for event_data in sample_events
        ])

        # Test event overlap detection
        processor = CalendarEventProcessor(events)
        is_valid, messages = processor.validate_digest_events(events)
        assert is_valid
        assert not messages

        # Test event dependencies
        morning_meeting = events[0]
        lunch_break = events[1]
        project_review = events[2]

        # Verify time relationships
        assert morning_meeting.end_time < lunch_break.start_time
        assert lunch_break.end_time < project_review.start_time
        assert morning_meeting.end_time < project_review.start_time


class TestEventProcessingIntegration:
    """Integration tests for event processing."""

    def test_event_processing_pipeline(self, sample_events):
        """Test the complete event processing pipeline."""
        # Create event collection
        events = CalendarEventCollection([
            CalendarEvent.from_api_data(event_data)
            for event_data in sample_events
        ])

        # Process events
        processor = CalendarEventProcessor(events)
        date = datetime(2024, 3, 20, tzinfo=SYDNEY_TIMEZONE)
        daily_events = processor.get_daily_digest_events(date)

        # Verify processing
        assert isinstance(daily_events, CalendarEventCollection)
        assert len(daily_events) == 3

        # Verify event formatting
        formatted_events = processor.format_events_for_digest(daily_events)
        assert len(formatted_events) == 3
        assert all(isinstance(event, dict) for event in formatted_events)
        assert all("title" in event for event in formatted_events)
        assert all("time" in event for event in formatted_events)

    def test_event_formatting_validation(self, sample_events):
        """Test event formatting validation."""
        # Create event collection with some invalid events
        invalid_events = sample_events.copy()
        invalid_events.append({
            "id": "evt_4",
            "title": "",  # Invalid: empty title
            "start": (datetime(2024, 3, 20, 15, 0, tzinfo=SYDNEY_TIMEZONE)).isoformat(),
            "end": (datetime(2024, 3, 20, 16, 0, tzinfo=SYDNEY_TIMEZONE)).isoformat(),
            "status": "confirmed",
            "type": "meeting",
        })
        invalid_events.append({
            "id": "evt_5",
            "title": "Overlapping Meeting",
            "start": (datetime(2024, 3, 20, 9, 30, tzinfo=SYDNEY_TIMEZONE)).isoformat(),  # Overlaps with morning meeting
            "end": (datetime(2024, 3, 20, 10, 30, tzinfo=SYDNEY_TIMEZONE)).isoformat(),
            "status": "confirmed",
            "type": "meeting",
        })

        events = CalendarEventCollection([
            CalendarEvent.from_api_data(event_data)
            for event_data in invalid_events
        ])

        # Process events
        processor = CalendarEventProcessor(events)
        date = datetime(2024, 3, 20, tzinfo=SYDNEY_TIMEZONE)
        daily_events = processor.get_daily_digest_events(date)

        # Verify validation
        is_valid, messages = processor.validate_digest_events(daily_events)
        assert not is_valid
        assert len(messages) > 0
        assert any("has no title" in msg for msg in messages)
        assert any("Events overlap" in msg for msg in messages)

    def test_edge_case_handling(self, sample_events):
        """Test handling of edge cases in event processing."""
        # Create events with edge cases
        edge_cases = [
            # All-day event
            {
                "id": "evt_6",
                "title": "All Day Event",
                "start": (datetime(2024, 3, 20, 0, 0, tzinfo=SYDNEY_TIMEZONE)).isoformat(),
                "end": (datetime(2024, 3, 21, 0, 0, tzinfo=SYDNEY_TIMEZONE)).isoformat(),
                "status": "confirmed",
                "type": "reminder",
            },
            # Event spanning multiple days
            {
                "id": "evt_7",
                "title": "Multi-day Event",
                "start": (datetime(2024, 3, 20, 16, 0, tzinfo=SYDNEY_TIMEZONE)).isoformat(),
                "end": (datetime(2024, 3, 21, 10, 0, tzinfo=SYDNEY_TIMEZONE)).isoformat(),
                "status": "confirmed",
                "type": "meeting",
            },
            # Event with no attendees
            {
                "id": "evt_8",
                "title": "Solo Task",
                "start": (datetime(2024, 3, 20, 11, 0, tzinfo=SYDNEY_TIMEZONE)).isoformat(),
                "end": (datetime(2024, 3, 20, 12, 0, tzinfo=SYDNEY_TIMEZONE)).isoformat(),
                "status": "confirmed",
                "type": "task",
                "attendees": [],
            },
        ]

        events = CalendarEventCollection([
            CalendarEvent.from_api_data(event_data)
            for event_data in sample_events + edge_cases
        ])

        # Process events
        processor = CalendarEventProcessor(events)
        date = datetime(2024, 3, 20, tzinfo=SYDNEY_TIMEZONE)
        daily_events = processor.get_daily_digest_events(date)

        # Verify edge case handling
        assert len(daily_events) == 6  # 3 original + 3 edge cases
        assert any(event.title == "All Day Event" for event in daily_events)
        assert any(event.title == "Multi-day Event" for event in daily_events)
        assert any(event.title == "Solo Task" for event in daily_events)

        # Verify formatting
        formatted_events = processor.format_events_for_digest(daily_events)
        assert len(formatted_events) == 6
        assert all("title" in event for event in formatted_events)
        assert all("time" in event for event in formatted_events)


class TestTimezoneIntegration:
    """Integration tests for timezone handling."""

    def test_timezone_conversion(self, sample_events):
        """Test timezone conversion and handling."""
        # Create events in different timezones
        utc_events = [
            {
                **event_data,
                "start": datetime.fromisoformat(event_data["start"]).astimezone(ZoneInfo("UTC")).isoformat(),
                "end": datetime.fromisoformat(event_data["end"]).astimezone(ZoneInfo("UTC")).isoformat(),
            }
            for event_data in sample_events
        ]

        # Create event collection
        events = CalendarEventCollection([
            CalendarEvent.from_api_data(event_data)
            for event_data in utc_events
        ])

        # Verify timezone conversion
        for event in events:
            assert event.start_time.tzinfo == SYDNEY_TIMEZONE
            assert event.end_time.tzinfo == SYDNEY_TIMEZONE
            # Verify times are correct in Sydney timezone
            assert event.start_time.hour == 9  # 9 AM Sydney time
            assert event.end_time.hour == 10  # 10 AM Sydney time

    def test_dst_transition_handling(self):
        """Test handling of daylight saving time transitions."""
        # Create events around DST transition
        dst_events = [
            {
                "id": "evt_9",
                "title": "Before DST",
                "start": "2024-04-06T09:00:00+10:00",  # Before DST ends
                "end": "2024-04-06T10:00:00+10:00",
                "status": "confirmed",
                "type": "meeting",
            },
            {
                "id": "evt_10",
                "title": "After DST",
                "start": "2024-04-07T09:00:00+10:00",  # After DST ends
                "end": "2024-04-07T10:00:00+10:00",
                "status": "confirmed",
                "type": "meeting",
            },
        ]

        # Create event collection
        events = CalendarEventCollection([
            CalendarEvent.from_api_data(event_data)
            for event_data in dst_events
        ])

        # Verify DST handling
        before_dst = events[0]
        after_dst = events[1]

        # Verify times are correct in Sydney timezone
        assert before_dst.start_time.tzinfo == SYDNEY_TIMEZONE
        assert after_dst.start_time.tzinfo == SYDNEY_TIMEZONE
        assert before_dst.start_time.hour == 9
        assert after_dst.start_time.hour == 9

        # Verify UTC offsets are different
        assert before_dst.start_time.utcoffset() != after_dst.start_time.utcoffset()

    def test_timezone_validation(self):
        """Test timezone validation and error handling."""
        # Create event with invalid timezone
        invalid_event = {
            "id": "evt_11",
            "title": "Invalid Timezone",
            "start": "2024-03-20T09:00:00",  # No timezone info
            "end": "2024-03-20T10:00:00",    # No timezone info
            "status": "confirmed",
            "type": "meeting",
        }

        # Verify validation
        with pytest.raises(ValidationError) as exc_info:
            CalendarEvent.from_api_data(invalid_event)
        assert "Invalid event data" in str(exc_info.value)

        # Create event with mismatched timezones
        mismatched_event = {
            "id": "evt_12",
            "title": "Mismatched Timezones",
            "start": "2024-03-20T09:00:00+10:00",  # Sydney time
            "end": "2024-03-20T10:00:00+00:00",    # UTC
            "status": "confirmed",
            "type": "meeting",
        }

        # Verify validation
        with pytest.raises(ValidationError) as exc_info:
            CalendarEvent.from_api_data(mismatched_event)
        assert "Invalid event data" in str(exc_info.value) 