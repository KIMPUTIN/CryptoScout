
# backend/core/api_usage.py

import time
from collections import deque


class APIUsageTracker:

    def __init__(self, window_seconds: int = 3600):
        self.window_seconds = window_seconds
        self.calls = deque()
        self.failures = deque()
        self.rate_limits = deque()

    def _cleanup(self):
        cutoff = time.time() - self.window_seconds

        while self.calls and self.calls[0] < cutoff:
            self.calls.popleft()

        while self.failures and self.failures[0] < cutoff:
            self.failures.popleft()

        while self.rate_limits and self.rate_limits[0] < cutoff:
            self.rate_limits.popleft()

    def record_call(self):
        self.calls.append(time.time())
        self._cleanup()

    def record_failure(self):
        self.failures.append(time.time())
        self._cleanup()

    def record_rate_limit(self):
        self.rate_limits.append(time.time())
        self._cleanup()

    def snapshot(self):
        self._cleanup()
        return {
            "calls_last_hour": len(self.calls),
            "failures_last_hour": len(self.failures),
            "rate_limits_last_hour": len(self.rate_limits)
        }
