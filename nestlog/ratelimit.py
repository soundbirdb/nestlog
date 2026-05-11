"""Token-bucket rate limiter processor for nestlog.

Drops log records that exceed a configured rate (messages per second)
per unique key (default: logger name + level).
"""

import time
from typing import Callable, Optional

from .processors import BaseProcessor


def _default_key(record) -> str:
    level = str(record.level)
    name = getattr(record, "name", "") or ""
    return f"{name}:{level}"


class TokenBucketProcessor(BaseProcessor):
    """Rate-limit log records using a per-key token-bucket algorithm.

    Each unique key gets its own bucket.  Tokens refill continuously at
    *rate* tokens/second up to *capacity*.  A record is passed through
    only when at least one token is available; otherwise it is dropped
    (``process`` returns ``None``).

    Args:
        rate:     Refill speed in tokens per second (e.g. ``10.0``).
        capacity: Maximum burst size (bucket ceiling).  Defaults to
                  ``rate`` (no burst beyond one second of accumulation).
        key_fn:   Callable that maps a record to a string bucket key.
                  Defaults to ``"<name>:<level>"``.
    """

    def __init__(
        self,
        rate: float,
        capacity: Optional[float] = None,
        key_fn: Optional[Callable] = None,
    ) -> None:
        if rate <= 0:
            raise ValueError("rate must be positive")
        self._rate = rate
        self._capacity = capacity if capacity is not None else rate
        self._key_fn = key_fn or _default_key
        # {key: (tokens, last_refill_timestamp)}
        self._buckets: dict = {}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _refill(self, tokens: float, last: float, now: float) -> float:
        elapsed = max(0.0, now - last)
        return min(self._capacity, tokens + elapsed * self._rate)

    def _consume(self, key: str, now: float) -> bool:
        """Return True if a token was consumed (record allowed)."""
        tokens, last = self._buckets.get(key, (self._capacity, now))
        tokens = self._refill(tokens, last, now)
        if tokens >= 1.0:
            self._buckets[key] = (tokens - 1.0, now)
            return True
        self._buckets[key] = (tokens, now)
        return False

    # ------------------------------------------------------------------
    # BaseProcessor interface
    # ------------------------------------------------------------------

    def process(self, record):
        """Return *record* if allowed, ``None`` if rate-limited."""
        key = self._key_fn(record)
        now = time.monotonic()
        if self._consume(key, now):
            return record
        return None
