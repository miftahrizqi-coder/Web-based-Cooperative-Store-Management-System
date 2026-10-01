"""Rate limit sederhana (in-memory) untuk endpoint login (PRD §35 Security).

Catatan: in-memory berarti per-proses. Untuk deployment multi-worker,
ganti dengan penyimpanan terpusat (mis. Redis) dengan antarmuka yang sama.
"""

import time
from collections import defaultdict, deque
from threading import Lock

from app.core.config import settings


class LoginRateLimiter:
    def __init__(self, max_attempts: int, window_seconds: int):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._failures: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def _prune(self, key: str, now: float) -> deque[float]:
        bucket = self._failures[key]
        while bucket and now - bucket[0] > self.window_seconds:
            bucket.popleft()
        return bucket

    def retry_after(self, key: str) -> int:
        """0 jika boleh mencoba, selain itu detik yang harus ditunggu."""
        now = time.monotonic()
        with self._lock:
            bucket = self._prune(key, now)
            if len(bucket) < self.max_attempts:
                return 0
            return max(1, int(self.window_seconds - (now - bucket[0])))

    def register_failure(self, key: str) -> None:
        with self._lock:
            self._failures[key].append(time.monotonic())

    def reset(self, key: str) -> None:
        with self._lock:
            self._failures.pop(key, None)


login_rate_limiter = LoginRateLimiter(
    settings.login_max_attempts,
    settings.login_window_seconds,
)
