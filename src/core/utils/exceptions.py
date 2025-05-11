"""
Custom exceptions for the application.
"""

class BaseError(Exception):
    """Base exception class for the application."""
    pass

class ValidationError(BaseError):
    """Raised when input validation fails."""
    pass

class WeatherAPIError(BaseError):
    """Raised when there's an error with the Weather API."""
    pass

class RateLimitError(WeatherAPIError):
    """Raised when the Weather API rate limit is exceeded."""
    pass 