"""Throttle processor: drops repeated identical messages within a time window."""

import time
from typing import Optional

from nestlog.processors import BaseProcessor


class ThrottleProcessor(BaseProcessor):
    """Suppress duplicate log messages that occur within *window* seconds.

    Two records are considered duplicates when they share the same logger name,
    level, and message template (the ``message`` field on the record).

    Parameters
    ----------
    window:
        Minimum number of seconds that must elapse before the same message is
        emitted again.  Defaults to 60 seconds.
    max_cache:
        Maximum number of distinct keys to track.  When the cache grows beyond
        this limit the oldest entry is evicted (LRU-style).  Defaults to 1024.
    """

    def __init__(self, window: float = 60.0, max_cache: int = 1024) -> None:
        if window < 0:
            raise ValueError("window must be >= 0")
        if max_cache < 1:
            raise ValueError("max_cache must be >= 1")
        self._window = window
        self._max_cache = max_cache
        # {key: last_emitted_timestamp}
        self._cache: dict = {}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _make_key(self, record) -> tuple:
        """Build a deduplication key from the record."""
        name = getattr(record, "name", "")
        level = str(getattr(record, "level", ""))
        message = getattr(record, "message", "")
        return (name, level, message)

    def _evict_oldest(self) -> None:
        """Remove the entry with the smallest timestamp."""
        if not self._cache:
            return
        oldest_key = min(self._cache, key=lambda k: self._cache[k])
        del self._cache[oldest_key]

    # ------------------------------------------------------------------
    # BaseProcessor interface
    # ------------------------------------------------------------------

    def process(self, record) -> Optional[object]:
        """Return *record* if it should be emitted, ``None`` to suppress it."""
        key = self._make_key(record)
        now = time.monotonic()
        last = self._cache.get(key)

        if last is not None and (now - last) < self._window:
            # Still within the throttle window — suppress.
            return None

        # Admit the record and update the cache.
        if len(self._cache) >= self._max_cache and key not in self._cache:
            self._evict_oldest()

        self._cache[key] = now
        return record

    def reset(self) -> None:
        """Clear all throttle state (useful in tests)."""
        self._cache.clear()
