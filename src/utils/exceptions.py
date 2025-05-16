"""
Custom exceptions and error handling utilities for the Daily Digest Assistant.

This module provides domain-specific exceptions and utilities for consistent
error handling across the application.
"""

from typing import Any, Dict, Optional, Type
import time

# from src.utils.logging import get_logger
# logger = get_logger(__name__)

# Dummy logger for testing purposes
class DummyLogger:
    def warning(self, *args, **kwargs):
        pass
    def error(self, *args, **kwargs):
        pass

logger = DummyLogger()


class DailyDigestError(Exception):
    """Base exception class for all application errors."""
    
    def __init__(
        self,
        message: str,
        error_code: str,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        """
        Initialize the error.
        
        Args:
            message: Human-readable error message.
            error_code: Machine-readable error code.
            details: Optional dictionary with additional error details.
            cause: Optional exception that caused this error.
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.cause = cause
        # Removed logger.error to break circular import

    def __str__(self):
        return self.message


class ConfigurationError(DailyDigestError):
    """Raised when there are issues with configuration."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        super().__init__(
            message=message,
            error_code="CONFIG_ERROR",
            details=details,
            cause=cause,
        )


class APIError(DailyDigestError):
    """Base class for API-related errors."""
    
    def __init__(
        self,
        message: str,
        api_name: str,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        self.status_code = status_code
        super().__init__(
            message=message,
            error_code=f"{api_name.upper()}_API_ERROR",
            details={
                "api_name": api_name,
                "status_code": status_code,
                **(details or {}),
            },
            cause=cause,
        )


class MotionAPIError(APIError):
    """Raised when there are issues with the Motion API."""
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        super().__init__(
            message=message,
            api_name="motion",
            status_code=status_code,
            details=details,
            cause=cause,
        )


class WeatherAPIError(APIError):
    """Raised when there are issues with the Weather API."""
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        super().__init__(
            message=message,
            api_name="weather",
            status_code=status_code,
            details=details,
            cause=cause,
        )


class EmailError(DailyDigestError):
    """Raised when there are issues with email delivery."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        super().__init__(
            message=message,
            error_code="EMAIL_ERROR",
            details=details,
            cause=cause,
        )


class ValidationError(DailyDigestError):
    """Raised when input validation fails."""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details={
                "field": field,
                **(details or {}),
            },
            cause=cause,
        )


def handle_error(
    error: Exception,
    default_error: Type[DailyDigestError] = DailyDigestError,
    context: Optional[Dict[str, Any]] = None,
) -> DailyDigestError:
    """
    Convert any exception to an appropriate DailyDigestError.
    
    Args:
        error: The exception to handle.
        default_error: The error class to use if no specific handler exists.
        context: Optional context to add to the error details.
        
    Returns:
        DailyDigestError: An appropriate error instance.
    """
    # If it's already a DailyDigestError, just add context if provided
    if isinstance(error, DailyDigestError):
        if context:
            error.details.update(context)
        return error
    
    # Map common exceptions to our error types
    error_map = {
        ValueError: ValidationError,
        KeyError: ConfigurationError,
        FileNotFoundError: ConfigurationError,
        PermissionError: ConfigurationError,
    }
    
    # Get the appropriate error class
    error_class = error_map.get(type(error), default_error)
    
    # Create a new error instance
    if error_class is DailyDigestError:
        return error_class(
            message=str(error),
            error_code="UNKNOWN_ERROR",
            details=context,
            cause=error,
        )
    else:
        return error_class(
            message=str(error),
            details=context,
            cause=error,
        )


def retry_on_error(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[Type[Exception], ...] = (Exception,),
):
    """
    Decorator for retrying functions on specific exceptions.
    
    Args:
        max_attempts: Maximum number of retry attempts.
        delay: Initial delay between retries in seconds.
        backoff: Multiplier for delay after each retry.
        exceptions: Tuple of exceptions to catch and retry on.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            "retry_attempt",
                            function=func.__name__,
                            attempt=attempt + 1,
                            max_attempts=max_attempts,
                            delay=current_delay,
                            error=str(e),
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            "max_retries_exceeded",
                            function=func.__name__,
                            max_attempts=max_attempts,
                            error=str(e),
                        )
                        raise handle_error(e)
            
            # This should never be reached due to the raise in the loop
            raise last_exception  # type: ignore
        
        return wrapper
    
    return decorator 