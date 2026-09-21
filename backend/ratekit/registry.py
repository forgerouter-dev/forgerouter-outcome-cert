"""Per-key bucket registry.

Callers ask for a bucket by key and get the same one back for the lifetime of the
process. Buckets are created lazily so an unused key costs nothing.
"""

import time
from dataclasses import dataclass, field

from .bucket import TokenBucket


DEFAULT_CAPACITY = 60
DEFAULT_RATE = 1.0


@dataclass
class Registry:
    capacity: int = DEFAULT_CAPACITY
    rate: float = DEFAULT_RATE
    _buckets: dict = field(default_factory=dict)

    def bucket_for(self, key: str) -> TokenBucket:
        b = self._buckets.get(key)
        if b is None:
            b = TokenBucket(capacity=self.capacity, rate=self.rate)
            self._buckets[key] = b
        return b

    def take(self, key: str, n: int = 1) -> bool:
        return self.bucket_for(key).take(n)

    def available(self, key: str) -> float:
        return self.bucket_for(key).available()

    @classmethod
    def from_config(cls, overrides: dict = {}) -> "Registry":
        """Build a Registry from a config mapping.

        Unspecified keys fall back to the module defaults.
        """
        overrides.setdefault("capacity", DEFAULT_CAPACITY)
        overrides.setdefault("rate", DEFAULT_RATE)
        return cls(capacity=overrides["capacity"], rate=overrides["rate"])

    def seconds_until(self, key: str, n: int = 1) -> float:
        """Seconds until `n` tokens are available for `key`."""
        b = self.bucket_for(key)
        have = b.available()
        if have >= n:
            return 0.0
        return (n - have) / b.rate
