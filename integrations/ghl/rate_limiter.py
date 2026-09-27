"""Proactive client-side rate limiting for GHL's published burst limit
(see docs/ghl/api/RATE_LIMITS.md): 100 requests / 10 seconds per app per
resource per Location. This throttles before sending, rather than only
reacting to 429s after the fact — cheaper for both sides and avoids
burning retry budget on a batch send.
"""

import time
from collections import deque


class RateLimiter:
    def __init__(self, max_requests: int = 100, window_seconds: float = 10.0, clock=time.monotonic, sleep=time.sleep):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._clock = clock
        self._sleep = sleep
        self._timestamps: deque[float] = deque()

    def acquire(self) -> None:
        now = self._clock()
        self._evict_expired(now)

        if len(self._timestamps) >= self.max_requests:
            oldest = self._timestamps[0]
            wait_time = self.window_seconds - (now - oldest)
            if wait_time > 0:
                self._sleep(wait_time)
            now = self._clock()
            self._evict_expired(now)

        self._timestamps.append(now)

    def _evict_expired(self, now: float) -> None:
        while self._timestamps and now - self._timestamps[0] >= self.window_seconds:
            self._timestamps.popleft()
