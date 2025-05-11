"""
Timezone utilities for the Daily Digest Assistant.

This module provides comprehensive timezone handling utilities, including
conversion, validation, and DST transition handling.
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from src.utils.exceptions import ValidationError
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Constants
SYDNEY_TIMEZONE = ZoneInfo("Australia/Sydney")
DEFAULT_TIMEZONE = SYDNEY_TIMEZONE

def validate_timezone(timezone_str: str) -> ZoneInfo:
    """
    Validate a timezone string and return a ZoneInfo object.
    
    Args:
        timezone_str: IANA timezone string (e.g., 'Australia/Sydney')
        
    Returns:
        ZoneInfo: Validated timezone object
        
    Raises:
        ValidationError: If the timezone is invalid
    """
    try:
        return ZoneInfo(timezone_str)
    except ZoneInfoNotFoundError as e:
        raise ValidationError(
            message=f"Invalid timezone: {timezone_str}",
            field="timezone",
            cause=e,
        )

def convert_to_timezone(
    dt: datetime,
    target_timezone: ZoneInfo,
    source_timezone: Optional[ZoneInfo] = None,
) -> datetime:
    """
    Convert a datetime to a target timezone.
    
    Args:
        dt: Datetime to convert
        target_timezone: Target timezone
        source_timezone: Optional source timezone (if dt is naive)
        
    Returns:
        datetime: Converted datetime in target timezone
        
    Raises:
        ValidationError: If the datetime is naive and no source timezone provided
    """
    if dt.tzinfo is None:
        if source_timezone is None:
            raise ValidationError(
                message="Cannot convert naive datetime without source timezone",
                field="datetime",
            )
        dt = dt.replace(tzinfo=source_timezone)
    
    return dt.astimezone(target_timezone)

def is_dst_transition(dt: datetime, timezone: ZoneInfo) -> bool:
    """
    Check if a datetime is during a DST transition period.
    
    Args:
        dt: Datetime to check
        timezone: Timezone to check against
        
    Returns:
        bool: True if the datetime is during a DST transition
    """
    # Get the UTC offset for the given datetime
    current_offset = dt.utcoffset()
    if current_offset is None:
        return False
    
    # Check offset 1 hour before and after
    one_hour_before = dt - timedelta(hours=1)
    one_hour_after = dt + timedelta(hours=1)
    
    before_offset = one_hour_before.utcoffset()
    after_offset = one_hour_after.utcoffset()
    
    if before_offset is None or after_offset is None:
        return False
    
    # If any of the offsets are different, we're in a transition period
    return current_offset != before_offset or current_offset != after_offset

def get_dst_transition_info(
    dt: datetime,
    timezone: ZoneInfo,
) -> Tuple[bool, Optional[timedelta]]:
    """
    Get detailed information about DST transitions.
    
    Args:
        dt: Datetime to check
        timezone: Timezone to check against
        
    Returns:
        Tuple[bool, Optional[timedelta]]: 
            - Whether the datetime is during a DST transition
            - The DST offset if applicable (None if not in DST)
    """
    is_transition = is_dst_transition(dt, timezone)
    dst_offset = dt.dst()
    
    return is_transition, dst_offset

def format_timezone_info(dt: datetime) -> str:
    """
    Format timezone information for display.
    
    Args:
        dt: Datetime to format
        
    Returns:
        str: Formatted timezone information
    """
    if dt.tzinfo is None:
        return "No timezone"
    
    tz_name = dt.tzinfo.key if hasattr(dt.tzinfo, 'key') else str(dt.tzinfo)
    offset = dt.strftime('%z')
    dst = "DST" if dt.dst() else "STD"
    
    return f"{tz_name} ({offset}, {dst})" 