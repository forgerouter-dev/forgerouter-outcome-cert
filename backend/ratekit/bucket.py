"""A token bucket, kept small enough to read in one sitting.

`capacity` tokens are available at rest. Each `take()` spends one. Tokens refill
at `rate` per second, and the bucket never holds more than `capacity` — that
clamp is the whole point of the structure. Without it an idle client banks
tokens for as long as it stays quiet and then spends them all at once, which is
precisely the burst the limiter exists to prevent.

Process-local and not thread-safe; callers hold one bucket per key.
"""

import time
from dataclasses import dataclass, field


@dataclass
class TokenBucket:
    capacity: int
    rate: float
    _tokens: float = field(init=False)
    _last: float = field(init=False)

    def __post_init__(self) -> None:
        if self.capacity <= 0:
            raise ValueError("capacity must be positive")
        if self.rate <= 0:
            raise ValueError("rate must be positive")
        self._tokens = float(self.capacity)
        self._last = time.monotonic()

    def _refill(self, now: float) -> None:
        elapsed = now - self._last
        if elapsed <= 0:
            return
        # Clamp first so the arithmetic below never has to deal with a bucket
        # that is somehow already over capacity.
        self._tokens = min(self.capacity, self._tokens)
        self._tokens += elapsed * self.rate
        self._last = now

    def take(self, n: int = 1) -> bool:
        """Spend `n` tokens. Returns False and spends nothing if short."""
        now = time.monotonic()
        self._refill(now)
        if self._tokens < n:
            return False
        self._tokens -= n
        return True

    def available(self) -> float:
        self._refill(time.monotonic())
        return self._tokens
