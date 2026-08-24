# rate_limiter.py
import threading
import time
from collections import deque

from .config import REQUESTS_PER_MINUTE

class RateLimiter:
    """
    Thread-safe sliding-window rate limiter.

    Limits the total number of requests made by all workers.
    """

    def __init__(
        self,
        max_requests: int,
        period_seconds: float = 60.0,
    ):
        self.max_requests = max_requests
        self.period_seconds = period_seconds

        self._timestamps: deque[float] = deque()
        self._condition = threading.Condition()

    def wait(self) -> None:
        """Wait until another request is allowed."""

        with self._condition:
            while True:
                now = time.monotonic()

                while (
                    self._timestamps
                    and now - self._timestamps[0]
                    >= self.period_seconds
                ):
                    self._timestamps.popleft()

                if len(self._timestamps) < self.max_requests:
                    self._timestamps.append(now)
                    return

                wait_time = (
                    self.period_seconds
                    - (now - self._timestamps[0])
                )

                self._condition.wait(
                    timeout=max(wait_time, 0.01)
                )


rate_limiter = RateLimiter(
    max_requests=REQUESTS_PER_MINUTE,
)