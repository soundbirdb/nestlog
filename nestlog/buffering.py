"""Buffering processor: accumulates records and flushes them in batches."""

from __future__ import annotations

from typing import Callable, List, Optional

from .processors import BaseProcessor


class BufferingProcessor(BaseProcessor):
    """Accumulates log records up to *capacity* then flushes them all at once
    through *flush_fn*.

    Parameters
    ----------
    capacity:
        Maximum number of records to hold before an automatic flush.
    flush_fn:
        Callable that receives the list of flushed records.  Defaults to a
        no-op so the processor can be used purely for manual flushing.
    auto_flush:
        When *True* (default) a flush is triggered automatically once
        *capacity* is reached.
    """

    def __init__(
        self,
        capacity: int = 100,
        flush_fn: Optional[Callable[[List], None]] = None,
        *,
        auto_flush: bool = True,
    ) -> None:
        if capacity < 1:
            raise ValueError("capacity must be >= 1")
        self._capacity = capacity
        self._flush_fn: Callable[[List], None] = flush_fn or (lambda records: None)
        self._auto_flush = auto_flush
        self._buffer: List = []

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    @property
    def buffered(self) -> List:
        """Read-only view of currently buffered records."""
        return list(self._buffer)

    @property
    def capacity(self) -> int:
        return self._capacity

    def flush(self) -> None:
        """Emit all buffered records through *flush_fn* and clear the buffer."""
        if self._buffer:
            self._flush_fn(list(self._buffer))
            self._buffer.clear()

    # ------------------------------------------------------------------
    # BaseProcessor interface
    # ------------------------------------------------------------------

    def process(self, record):
        """Buffer *record* and optionally auto-flush when capacity is reached."""
        self._buffer.append(record)
        if self._auto_flush and len(self._buffer) >= self._capacity:
            self.flush()
        return record
