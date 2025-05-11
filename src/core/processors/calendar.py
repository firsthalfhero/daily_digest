"""
Calendar event processor for digest email preparation.

This module provides specialized processing of calendar events for the daily digest email,
including filtering, sorting, formatting, and grouping operations specific to the digest needs.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from src.core.models.calendar import (
    CalendarEvent,
    CalendarEventCollection,
    EventStatus,
    EventType,
    SYDNEY_TIMEZONE,
)
from src.utils.exceptions import ValidationError
from src.utils.logging import get_logger

logger = get_logger(__name__)


class CalendarEventProcessor:
    """
    Processes calendar events for digest email preparation.
    
    This class provides specialized methods for processing calendar events
    specifically for the daily digest email, including digest-specific
    filtering, sorting, formatting, and grouping operations.
    """
    
    def __init__(self, events: CalendarEventCollection):
        """
        Initialize the processor with a collection of events.
        
        Args:
            events: Collection of calendar events to process
        """
        self.events = events.to_sydney_time()  # Ensure all events are in Sydney time
    
    def get_daily_digest_events(self, date: datetime) -> CalendarEventCollection:
        """
        Get events for the daily digest, filtered and processed appropriately.
        
        Args:
            date: The date to get events for
            
        Returns:
            CalendarEventCollection: Processed events for the digest
        """
        # Filter to only confirmed events for the specified date
        filtered = (
            self.events
            .filter_by_date(date)
            .filter_by_status(EventStatus.CONFIRMED)
        )
        
        # Sort chronologically
        return filtered.sort_by_start_time()
    
    def group_events_by_time_of_day(
        self,
        events: Optional[CalendarEventCollection] = None,
    ) -> Dict[str, List[CalendarEvent]]:
        """
        Group events by time of day (morning, afternoon, evening).
        
        Args:
            events: Optional events to group (defaults to all events)
            
        Returns:
            Dict[str, List[CalendarEvent]]: Events grouped by time of day
        """
        events = events or self.events
        
        # Define time boundaries (Sydney time)
        morning_start = datetime.now(SYDNEY_TIMEZONE).replace(hour=5, minute=0, second=0, microsecond=0)
        afternoon_start = datetime.now(SYDNEY_TIMEZONE).replace(hour=12, minute=0, second=0, microsecond=0)
        evening_start = datetime.now(SYDNEY_TIMEZONE).replace(hour=17, minute=0, second=0, microsecond=0)
        
        groups = {
            "morning": [],
            "afternoon": [],
            "evening": [],
        }
        
        for event in events:
            start_time = event.start_time
            
            if start_time < morning_start:
                # Events before 5 AM are considered part of the morning
                groups["morning"].append(event)
            elif start_time < afternoon_start:
                groups["morning"].append(event)
            elif start_time < evening_start:
                groups["afternoon"].append(event)
            else:
                groups["evening"].append(event)
        
        return groups
    
    def format_event_for_digest(self, event: CalendarEvent) -> Dict[str, str]:
        """
        Format an event for display in the digest email.
        
        Args:
            event: The event to format
            
        Returns:
            Dict[str, str]: Formatted event details
        """
        # Format time range
        if event.is_all_day():
            time_str = "All day"
        else:
            start_time = event.start_time.strftime("%I:%M %p").lstrip("0")
            end_time = event.end_time.strftime("%I:%M %p").lstrip("0")
            time_str = f"{start_time} - {end_time}"
        
        # Format location if present
        location_str = f" at {event.location}" if event.location else ""
        
        # Format attendees if present
        attendees_str = ""
        if event.attendees:
            attendee_count = len(event.attendees)
            if attendee_count == 1:
                attendees_str = f" with {event.attendees[0]}"
            else:
                attendees_str = f" with {attendee_count} attendees"
        
        return {
            "title": event.title,
            "time": time_str,
            "location": location_str,
            "attendees": attendees_str,
            "description": event.description or "",
            "type": event.type.value.title(),
        }
    
    def get_digest_summary(self, date: datetime) -> Dict[str, Any]:
        """
        Generate a complete digest summary for the specified date.
        
        Args:
            date: The date to generate the summary for
            
        Returns:
            Dict[str, Any]: Complete digest summary including:
                - Total events
                - Events by time of day
                - Formatted events
                - Event types distribution
        """
        # Get processed events for the day
        daily_events = self.get_daily_digest_events(date)
        
        # Group events by time of day
        time_groups = self.group_events_by_time_of_day(daily_events)
        
        # Format all events
        formatted_events = {
            period: [self.format_event_for_digest(event) for event in events]
            for period, events in time_groups.items()
        }
        
        # Count events by type
        type_counts = {
            event_type: len(daily_events.filter_by_type(event_type))
            for event_type in EventType
        }
        
        return {
            "date": date.strftime("%A, %B %d, %Y"),
            "total_events": len(daily_events),
            "events_by_period": {
                period: len(events)
                for period, events in time_groups.items()
            },
            "events_by_type": type_counts,
            "formatted_events": formatted_events,
        }
    
    def validate_digest_events(self, events: CalendarEventCollection) -> Tuple[bool, List[str]]:
        """
        Validate events for digest inclusion.
        
        Args:
            events: Events to validate
            
        Returns:
            Tuple[bool, List[str]]: (is_valid, list of validation messages)
        """
        messages = []
        
        # Check for events with missing required fields
        for event in events:
            if not event.title:
                messages.append(f"Event {event.id} has no title")
            if not event.start_time or not event.end_time:
                messages.append(f"Event {event.id} has invalid times")
            if event.status != EventStatus.CONFIRMED:
                messages.append(f"Event {event.id} is not confirmed")
        
        # Check for overlapping events
        sorted_events = events.sort_by_start_time()
        for i in range(len(sorted_events) - 1):
            current = sorted_events[i]
            next_event = sorted_events[i + 1]
            if current.end_time > next_event.start_time:
                messages.append(
                    f"Events overlap: '{current.title}' and '{next_event.title}'"
                )
        
        return len(messages) == 0, messages 