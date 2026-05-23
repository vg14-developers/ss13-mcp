import time
from threading import Lock


class TokenBucket:
    """Simple per-key token bucket. In-process; resets on restart (acceptable for our scale)."""

    def __init__(self, capacity: int, refill_per_second: float) -> None:
        self.capacity = capacity
        self.refill = refill_per_second
        self._buckets: dict[str, tuple[float, float]] = {}
        self._lock = Lock()

    def take(self, key: str, cost: int = 1) -> bool:
        now = time.monotonic()
        with self._lock:
            tokens, last = self._buckets.get(key, (float(self.capacity), now))
            tokens = min(self.capacity, tokens + (now - last) * self.refill)
            if tokens >= cost:
                tokens -= cost
                self._buckets[key] = (tokens, now)
                return True
            self._buckets[key] = (tokens, now)
            return False
