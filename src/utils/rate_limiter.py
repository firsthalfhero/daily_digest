"""Rate limiter implementation using a sliding window approach."""

import time
from collections import deque
from threading import Lock
from typing import Optional, Deque

from src.utils.logging import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """
    A thread-safe rate limiter using a sliding window approach.
    
    This implementation uses a deque to store timestamps of requests within the window.
    It automatically removes timestamps that are outside the window when checking limits.
    """

    def __init__(self, requests_per_minute: int = 12):
        """
        Initialize the rate limiter.
        
        Args:
            requests_per_minute: Maximum number of requests allowed per minute.
        """
        self.requests_per_minute = requests_per_minute
        self.window_size = 60  # 1 minute in seconds
        self.timestamps: Deque[float] = deque()
        self.lock = Lock()

    def _clean_old_timestamps(self, current_time: float) -> None:
        """Remove timestamps that are outside the current window."""
        cutoff_time = current_time - self.window_size
        while self.timestamps and self.timestamps[0] < cutoff_time:
            self.timestamps.popleft()

    def acquire(self, wait: bool = True) -> bool:
        """
        Try to acquire a rate limit token.
        
        Args:
            wait: If True, wait until a token is available. If False, return immediately
                 if no token is available.
        
        Returns:
            bool: True if a token was acquired, False if not (and wait=False).
        """
        with self.lock:
            current_time = time.time()
            self._clean_old_timestamps(current_time)
            
            if len(self.timestamps) < self.requests_per_minute:
                self.timestamps.append(current_time)
                return True
            
            if not wait:
                return False
            
            # Calculate wait time until next available token
            oldest_timestamp = self.timestamps[0]
            wait_time = oldest_timestamp + self.window_size - current_time
            
            if wait_time > 0:
                logger.warning(
                    "rate_limit_wait",
                    wait_time=wait_time,
                    current_requests=len(self.timestamps),
                    max_requests=self.requests_per_minute,
                )
                time.sleep(wait_time)
                return self.acquire(wait=True)
            
            return False

    def get_current_usage(self) -> tuple[int, float]:
        """
        Get the current rate limit usage.
        
        Returns:
            tuple[int, float]: (current number of requests, time until next available token)
        """
        with self.lock:
            current_time = time.time()
            self._clean_old_timestamps(current_time)
            
            if not self.timestamps:
                return 0, 0.0
            
            oldest_timestamp = self.timestamps[0]
            time_until_next = max(0.0, oldest_timestamp + self.window_size - current_time)
            
            return len(self.timestamps), time_until_next


# Global rate limiter instance
global_rate_limiter = RateLimiter(requests_per_minute=12) 