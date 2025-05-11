"""Example usage of the error handling system."""

import time
from typing import Dict, Any

from src.utils.config import load_config
from src.utils.exceptions import (
    APIError,
    ConfigurationError,
    DailyDigestError,
    EmailError,
    MotionAPIError,
    ValidationError,
    WeatherAPIError,
    handle_error,
    retry_on_error,
)
from src.utils.logging import get_logger, setup_logging


logger = get_logger(__name__)


def validate_email(email: str) -> None:
    """Validate email format."""
    if "@" not in email:
        raise ValidationError(
            message="Invalid email format",
            field="email",
            details={"value": email},
        )


@retry_on_error(max_attempts=3, delay=1.0)
def fetch_motion_data(user_id: str) -> Dict[str, Any]:
    """Fetch data from Motion API with retry logic."""
    # Simulate API call
    if user_id == "invalid":
        raise MotionAPIError(
            message="Invalid user ID",
            status_code=400,
            details={"user_id": user_id},
        )
    elif user_id == "rate_limited":
        raise MotionAPIError(
            message="Rate limit exceeded",
            status_code=429,
            details={"retry_after": 60},
        )
    return {"events": ["Meeting at 10:00", "Lunch at 12:30"]}


@retry_on_error(max_attempts=2, delay=0.5)
def fetch_weather_data(location: str) -> Dict[str, Any]:
    """Fetch weather data with retry logic."""
    # Simulate API call
    if location == "unknown":
        raise WeatherAPIError(
            message="Location not found",
            status_code=404,
            details={"location": location},
        )
    return {"temperature": 22, "condition": "Sunny"}


def send_email(to: str, subject: str, content: str) -> None:
    """Send email with error handling."""
    try:
        # Simulate email sending
        if to == "invalid":
            raise EmailError(
                message="Invalid recipient",
                details={"email": to},
            )
        logger.info("email_sent", to=to, subject=subject)
    except Exception as e:
        raise handle_error(e, context={"recipient": to})


def process_digest(user_id: str, email: str, location: str) -> None:
    """Process daily digest with comprehensive error handling."""
    try:
        # Validate input
        validate_email(email)
        
        # Fetch data with retry logic
        calendar_data = fetch_motion_data(user_id)
        weather_data = fetch_weather_data(location)
        
        # Generate and send email
        content = f"""
        Your Daily Digest:
        
        Calendar:
        {chr(10).join(f"- {event}" for event in calendar_data['events'])}
        
        Weather:
        Temperature: {weather_data['temperature']}°C
        Condition: {weather_data['condition']}
        """
        
        send_email(email, "Your Daily Digest", content)
        
    except DailyDigestError as e:
        # Log and re-raise application errors
        logger.error(
            "digest_processing_failed",
            error_code=e.error_code,
            details=e.details,
        )
        raise
    except Exception as e:
        # Convert unknown errors to application errors
        raise handle_error(e, context={
            "user_id": user_id,
            "email": email,
            "location": location,
        })


def main():
    """Demonstrate error handling features."""
    # Set up logging
    config = load_config()
    setup_logging(config)
    
    # Test cases
    test_cases = [
        # Valid case
        {
            "user_id": "valid_user",
            "email": "user@example.com",
            "location": "Sydney",
        },
        # Invalid email
        {
            "user_id": "valid_user",
            "email": "invalid-email",
            "location": "Sydney",
        },
        # Invalid user ID
        {
            "user_id": "invalid",
            "email": "user@example.com",
            "location": "Sydney",
        },
        # Rate limited
        {
            "user_id": "rate_limited",
            "email": "user@example.com",
            "location": "Sydney",
        },
        # Unknown location
        {
            "user_id": "valid_user",
            "email": "user@example.com",
            "location": "unknown",
        },
        # Invalid recipient
        {
            "user_id": "valid_user",
            "email": "invalid",
            "location": "Sydney",
        },
    ]
    
    # Run test cases
    for case in test_cases:
        logger.info("processing_test_case", **case)
        try:
            process_digest(**case)
            logger.info("test_case_succeeded", **case)
        except DailyDigestError as e:
            logger.error(
                "test_case_failed",
                error_code=e.error_code,
                message=str(e),
                details=e.details,
                **case,
            )


if __name__ == "__main__":
    main() 