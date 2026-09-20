"""One bucket per caller key, created on demand.

A single shared bucket rate-limits the whole service as one client, which is
never what anyone wants: one noisy caller starves everyone. The registry hands
each key its own bucket with the same policy.

Idle keys are dropped on `sweep()` rather than on every lookup, so the common
path stays a dict hit.
"""

import time
from dataclasses import dataclass

from .bucket import TokenBucket


@dataclass
class LimiterRegistry:
    capacity: int
    rate: float
    idle_ttl: float = 3600.0

    def __post_init__(self) -> None:
        self._buckets: dict[str, TokenBucket] = {}
        self._seen: dict[str, float] = {}

    def bucket(self, key: str) -> TokenBucket:
        b = self._buckets.get(key)
        if b is None:
            b = TokenBucket(capacity=self.capacity, rate=self.rate)
            self._buckets[key] = b
        self._seen[key] = time.monotonic()
        return b

    def take(self, key: str, n: int = 1) -> bool:
        return self.bucket(key).take(n)

    def retry_after(self, key: str, n: int = 1) -> float:
        """Seconds until this key can spend `n` tokens."""
        return self.bucket(key).retry_after(n)

    def sweep(self) -> int:
        """Drop keys untouched for `idle_ttl`. Returns how many were dropped."""
        now = time.monotonic()
        stale = [k for k, t in self._seen.items() if now - t >= self.idle_ttl]
        for k in stale:
            self._buckets.pop(k, None)
            self._seen.pop(k, None)
        return len(stale)

    def __len__(self) -> int:
        return len(self._buckets)
