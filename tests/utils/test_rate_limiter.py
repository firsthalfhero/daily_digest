"""Unit tests for rate limiter utility."""

import time
from unittest.mock import patch

import pytest

from src.utils.rate_limiter import RateLimiter, global_rate_limiter


class TestRateLimiter:
    """Test RateLimiter functionality."""

    def test_init_with_default_values(self):
        """Test initializing rate limiter with default values."""
        limiter = RateLimiter()
        assert limiter.max_requests == 60
        assert limiter.time_window == 60
        assert limiter.requests == []
        assert not limiter.is_rate_limited

    def test_init_with_custom_values(self):
        """Test initializing rate limiter with custom values."""
        limiter = RateLimiter(max_requests=10, time_window=5)
        assert limiter.max_requests == 10
        assert limiter.time_window == 5
        assert limiter.requests == []
        assert not limiter.is_rate_limited

    def test_reset(self):
        """Test resetting the rate limiter."""
        limiter = RateLimiter()
        limiter.requests = [time.time()] * 5
        limiter.is_rate_limited = True
        limiter.reset()
        assert limiter.requests == []
        assert not limiter.is_rate_limited

    def test_wait_time_calculation(self):
        """Test calculating wait time for rate limited requests."""
        limiter = RateLimiter(max_requests=2, time_window=5)
        current_time = time.time()

        # Add two requests at the start of the window
        limiter.requests = [current_time - 4, current_time - 3]
        assert limiter.wait_time(current_time) == 0

        # Add a third request, should be rate limited
        limiter.requests.append(current_time - 2)
        assert limiter.wait_time(current_time) == 3  # Wait until first request expires

        # Test with requests outside the window
        limiter.requests = [current_time - 6, current_time - 5.5]
        assert limiter.wait_time(current_time) == 0

    def test_rate_limiting(self):
        """Test rate limiting functionality."""
        limiter = RateLimiter(max_requests=2, time_window=5)
        current_time = time.time()

        # First two requests should succeed
        assert not limiter.is_rate_limited
        limiter.requests = [current_time - 1, current_time - 0.5]
        assert not limiter.is_rate_limited

        # Third request should be rate limited
        limiter.requests.append(current_time)
        assert limiter.is_rate_limited

        # After waiting, should be able to make requests again
        with patch("time.time") as mock_time:
            mock_time.return_value = current_time + 5
            assert not limiter.is_rate_limited

    def test_global_rate_limiter(self):
        """Test global rate limiter instance."""
        # Reset global limiter
        global_rate_limiter.reset()
        assert global_rate_limiter.max_requests == 60
        assert global_rate_limiter.time_window == 60
        assert global_rate_limiter.requests == []
        assert not global_rate_limiter.is_rate_limited

        # Test rate limiting with global instance
        current_time = time.time()
        global_rate_limiter.requests = [current_time] * 61
        assert global_rate_limiter.is_rate_limited

        # Reset and verify
        global_rate_limiter.reset()
        assert not global_rate_limiter.is_rate_limited
        assert global_rate_limiter.requests == []

    def test_concurrent_requests(self):
        """Test handling of concurrent requests."""
        limiter = RateLimiter(max_requests=3, time_window=1)
        current_time = time.time()

        # Simulate concurrent requests
        limiter.requests = [
            current_time - 0.1,
            current_time - 0.05,
            current_time,
        ]
        assert limiter.is_rate_limited

        # After window expires, should be able to make requests again
        with patch("time.time") as mock_time:
            mock_time.return_value = current_time + 1.1
            assert not limiter.is_rate_limited
            assert len(limiter.requests) == 0

    def test_edge_cases(self):
        """Test rate limiter edge cases."""
        limiter = RateLimiter(max_requests=1, time_window=1)

        # Test with empty requests list
        assert not limiter.is_rate_limited
        assert limiter.wait_time(time.time()) == 0

        # Test with max_requests = 0
        limiter = RateLimiter(max_requests=0, time_window=1)
        assert limiter.is_rate_limited

        # Test with time_window = 0
        limiter = RateLimiter(max_requests=1, time_window=0)
        assert not limiter.is_rate_limited
        limiter.requests.append(time.time())
        assert not limiter.is_rate_limited  # Should not be rate limited with 0 time window

    def test_request_tracking(self):
        """Test tracking of requests over time."""
        limiter = RateLimiter(max_requests=3, time_window=2)
        current_time = time.time()

        # Add requests at different times
        limiter.requests = [
            current_time - 1.5,  # Should be expired
            current_time - 0.5,  # Should be active
            current_time,        # Should be active
        ]

        # Verify only active requests are counted
        assert len(limiter.requests) == 3
        assert not limiter.is_rate_limited

        # Add one more request
        limiter.requests.append(current_time + 0.1)
        assert limiter.is_rate_limited

        # After window expires, old requests should be removed
        with patch("time.time") as mock_time:
            mock_time.return_value = current_time + 2.1
            assert not limiter.is_rate_limited
            assert len(limiter.requests) == 1  # Only the most recent request should remain 