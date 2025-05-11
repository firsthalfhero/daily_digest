"""Tests for the rate limiter implementation."""

import time
import threading
from unittest.mock import patch

import pytest

from src.utils.rate_limiter import RateLimiter


def test_rate_limiter_initialization():
    """Test rate limiter initialization."""
    limiter = RateLimiter(requests_per_minute=12)
    assert limiter.requests_per_minute == 12
    assert limiter.window_size == 60
    assert len(limiter.timestamps) == 0


def test_rate_limiter_basic_usage():
    """Test basic rate limiter usage."""
    limiter = RateLimiter(requests_per_minute=2)
    
    # Should allow first two requests
    assert limiter.acquire(wait=False) is True
    assert limiter.acquire(wait=False) is True
    
    # Third request should be blocked (wait=False)
    assert limiter.acquire(wait=False) is False
    
    # Should allow request after window expires
    with patch('time.time') as mock_time:
        mock_time.return_value = time.time() + 61  # Move time forward 61 seconds
        assert limiter.acquire(wait=False) is True


def test_rate_limiter_waiting():
    """Test rate limiter with waiting enabled."""
    limiter = RateLimiter(requests_per_minute=1)
    
    # First request should succeed
    assert limiter.acquire(wait=True) is True
    
    # Second request should wait and then succeed
    start_time = time.time()
    assert limiter.acquire(wait=True) is True
    elapsed = time.time() - start_time
    
    # Should have waited approximately 60 seconds
    assert 58 <= elapsed <= 62  # Allow 2 second margin for test execution


def test_rate_limiter_concurrent_access():
    """Test rate limiter with concurrent access."""
    limiter = RateLimiter(requests_per_minute=10)
    success_count = 0
    failure_count = 0
    
    def make_request():
        nonlocal success_count, failure_count
        if limiter.acquire(wait=False):
            success_count += 1
        else:
            failure_count += 1
    
    # Create 20 threads making requests simultaneously
    threads = [threading.Thread(target=make_request) for _ in range(20)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    
    # Should have exactly 10 successes and 10 failures
    assert success_count == 10
    assert failure_count == 10


def test_get_current_usage():
    """Test getting current rate limit usage."""
    limiter = RateLimiter(requests_per_minute=2)
    
    # Initially no usage
    count, wait_time = limiter.get_current_usage()
    assert count == 0
    assert wait_time == 0.0
    
    # After one request
    limiter.acquire(wait=False)
    count, wait_time = limiter.get_current_usage()
    assert count == 1
    assert wait_time == 0.0
    
    # After two requests
    limiter.acquire(wait=False)
    count, wait_time = limiter.get_current_usage()
    assert count == 2
    assert wait_time > 0.0  # Should have some wait time remaining
    
    # After window expires
    with patch('time.time') as mock_time:
        mock_time.return_value = time.time() + 61
        count, wait_time = limiter.get_current_usage()
        assert count == 0
        assert wait_time == 0.0 