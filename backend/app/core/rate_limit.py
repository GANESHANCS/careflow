import time
from collections import defaultdict
from threading import Lock

class InMemoryRateLimiter:
    """
    Thread-safe in-memory sliding window rate limiter for abuse protection.
    Does not require external infrastructure (Redis, etc.).
    """
    def __init__(self, default_max_requests: int = 5, default_window_seconds: int = 60):
        self.max_requests = default_max_requests
        self.window_seconds = default_window_seconds
        self._history = defaultdict(list)
        self._lock = Lock()

    def is_allowed(self, key: str, max_requests: int = None, window_seconds: int = None) -> bool:
        limit = max_requests if max_requests is not None else self.max_requests
        window = window_seconds if window_seconds is not None else self.window_seconds
        now = time.time()

        with self._lock:
            # Filter out timestamps outside window
            timestamps = [t for t in self._history[key] if now - t < window]
            if len(timestamps) >= limit:
                self._history[key] = timestamps
                return False
            timestamps.append(now)
            self._history[key] = timestamps
            return True

    def clear(self):
        with self._lock:
            self._history.clear()


# Global login rate limiter instance (5 attempts per minute per key)
login_rate_limiter = InMemoryRateLimiter(default_max_requests=5, default_window_seconds=60)
