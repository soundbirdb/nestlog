"""Deduplication processor: suppress repeated log records within a time window."""

import time
import hashlib
from nestlog.processors import BaseProcessor


class DeduplicatorProcessor(BaseProcessor):
    """Suppress duplicate log records that occur within *window* seconds.

    Two records are considered duplicates when they share the same level and
    message.  Extra *fields* keys can be included in the identity hash to make
    the comparison more (or less) strict.

    Parameters
    ----------
    window:
        Seconds during which a repeated record is suppressed.  Default: 60.
    fields:
        Additional record field names to fold into the identity key.
    max_entries:
        Maximum number of keys kept in memory.  Oldest entries are evicted
        when the limit is reached.  Default: 1 000.
    """

    def __init__(
        self,
        window: float = 60.0,
        fields: tuple = (),
        max_entries: int = 1_000,
    ) -> None:
        self._window = window
        self._fields = tuple(fields)
        self._max_entries = max_entries
        # key -> first-seen timestamp
        self._seen: dict[str, float] = {}

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    def _make_key(self, record) -> str:
        parts = [str(record.level), str(record.message)]
        for name in self._fields:
            parts.append(str(record.fields.get(name, "")))
        raw = "\x00".join(parts).encode()
        return hashlib.md5(raw, usedforsecurity=False).hexdigest()

    def _evict_expired(self, now: float) -> None:
        expired = [k for k, ts in self._seen.items() if now - ts >= self._window]
        for k in expired:
            del self._seen[k]

    def _evict_oldest(self) -> None:
        if not self._seen:
            return
        oldest_key = min(self._seen, key=lambda k: self._seen[k])
        del self._seen[oldest_key]

    # ------------------------------------------------------------------
    # BaseProcessor interface
    # ------------------------------------------------------------------

    def process(self, record):
        """Return *record* if it is not a duplicate; return ``None`` to suppress."""
        now = time.monotonic()
        self._evict_expired(now)

        key = self._make_key(record)
        if key in self._seen:
            return None  # suppress duplicate

        if len(self._seen) >= self._max_entries:
            self._evict_oldest()

        self._seen[key] = now
        return record
