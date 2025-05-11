"""
Unit tests for timezone utilities.

This module tests the timezone handling functions, including conversion,
validation, and DST transition detection.
"""

from datetime import datetime, timedelta
import pytest
from zoneinfo import ZoneInfo

from src.utils.exceptions import ValidationError
from src.utils.timezone import (
    SYDNEY_TIMEZONE,
    DEFAULT_TIMEZONE,
    validate_timezone,
    convert_to_timezone,
    is_dst_transition,
    get_dst_transition_info,
    format_timezone_info,
)

# Test data
SYDNEY_DST_START_2024 = datetime(2024, 10, 6, 2, 0, tzinfo=SYDNEY_TIMEZONE)  # DST starts at 2am
SYDNEY_DST_END_2024 = datetime(2024, 4, 7, 3, 0, tzinfo=SYDNEY_TIMEZONE)  # DST ends at 3am

def test_validate_timezone():
    """Test timezone validation."""
    # Valid timezone
    tz = validate_timezone("Australia/Sydney")
    assert isinstance(tz, ZoneInfo)
    assert str(tz) == "Australia/Sydney"
    
    # Invalid timezone
    with pytest.raises(ValidationError) as exc_info:
        validate_timezone("Invalid/Timezone")
    assert "Invalid timezone" in str(exc_info.value)

def test_convert_to_timezone():
    """Test timezone conversion."""
    # Test with naive datetime
    naive_dt = datetime(2024, 3, 20, 10, 0)
    with pytest.raises(ValidationError) as exc_info:
        convert_to_timezone(naive_dt, SYDNEY_TIMEZONE)
    assert "naive datetime" in str(exc_info.value)
    
    # Test with source timezone
    converted = convert_to_timezone(naive_dt, SYDNEY_TIMEZONE, ZoneInfo("UTC"))
    assert converted.tzinfo == SYDNEY_TIMEZONE
    assert converted.hour == 20  # UTC+10
    
    # Test with aware datetime
    utc_dt = datetime(2024, 3, 20, 10, 0, tzinfo=ZoneInfo("UTC"))
    converted = convert_to_timezone(utc_dt, SYDNEY_TIMEZONE)
    assert converted.tzinfo == SYDNEY_TIMEZONE
    assert converted.hour == 20  # UTC+10

def test_dst_transition_detection():
    """Test DST transition detection."""
    # Test during DST
    during_dst = datetime(2024, 1, 15, 12, 0, tzinfo=SYDNEY_TIMEZONE)
    assert not is_dst_transition(during_dst, SYDNEY_TIMEZONE)
    
    # Test during DST transition (start)
    transition_start = SYDNEY_DST_START_2024
    assert is_dst_transition(transition_start, SYDNEY_TIMEZONE)
    
    # Test during DST transition (end)
    transition_end = SYDNEY_DST_END_2024
    assert is_dst_transition(transition_end, SYDNEY_TIMEZONE)
    
    # Test just before transition
    before_transition = transition_start - timedelta(minutes=30)
    assert not is_dst_transition(before_transition, SYDNEY_TIMEZONE)
    
    # Test just after transition
    after_transition = transition_end + timedelta(minutes=30)
    assert not is_dst_transition(after_transition, SYDNEY_TIMEZONE)

def test_get_dst_transition_info():
    """Test getting detailed DST transition information."""
    # Test during DST
    during_dst = datetime(2024, 1, 15, 12, 0, tzinfo=SYDNEY_TIMEZONE)
    is_transition, dst_offset = get_dst_transition_info(during_dst, SYDNEY_TIMEZONE)
    assert not is_transition
    assert dst_offset == timedelta(hours=1)  # Sydney DST offset
    
    # Test during DST transition
    transition_start = SYDNEY_DST_START_2024
    is_transition, dst_offset = get_dst_transition_info(transition_start, SYDNEY_TIMEZONE)
    assert is_transition
    assert dst_offset == timedelta(hours=1)  # Sydney DST offset
    
    # Test outside DST
    outside_dst = datetime(2024, 6, 15, 12, 0, tzinfo=SYDNEY_TIMEZONE)
    is_transition, dst_offset = get_dst_transition_info(outside_dst, SYDNEY_TIMEZONE)
    assert not is_transition
    assert dst_offset == timedelta(0)  # No DST offset

def test_format_timezone_info():
    """Test timezone information formatting."""
    # Test with timezone
    dt = datetime(2024, 3, 20, 10, 0, tzinfo=SYDNEY_TIMEZONE)
    info = format_timezone_info(dt)
    assert "Australia/Sydney" in info
    assert "+1000" in info  # Sydney offset
    assert "STD" in info  # Not in DST
    
    # Test with DST
    dt_dst = datetime(2024, 1, 15, 10, 0, tzinfo=SYDNEY_TIMEZONE)
    info = format_timezone_info(dt_dst)
    assert "Australia/Sydney" in info
    assert "+1100" in info  # Sydney DST offset
    assert "DST" in info
    
    # Test with naive datetime
    naive_dt = datetime(2024, 3, 20, 10, 0)
    assert format_timezone_info(naive_dt) == "No timezone"

def test_timezone_edge_cases():
    """Test timezone handling edge cases."""
    # Test with UTC midnight
    utc_midnight = datetime(2024, 3, 20, 0, 0, tzinfo=ZoneInfo("UTC"))
    sydney_time = convert_to_timezone(utc_midnight, SYDNEY_TIMEZONE)
    assert sydney_time.hour == 10  # UTC+10
    assert sydney_time.day == 20
    
    # Test with date change
    utc_late = datetime(2024, 3, 20, 23, 0, tzinfo=ZoneInfo("UTC"))
    sydney_time = convert_to_timezone(utc_late, SYDNEY_TIMEZONE)
    assert sydney_time.hour == 9  # Next day UTC+10
    assert sydney_time.day == 21
    
    # Test with DST transition
    transition_time = SYDNEY_DST_START_2024
    info = format_timezone_info(transition_time)
    assert "Australia/Sydney" in info
    assert "+1100" in info  # DST offset
    assert "DST" in info 