"""
nestlog.batching
~~~~~~~~~~~~~~~~
BatchingProcessor accumulates log records and flushes them to a sink
as a batch once a size threshold or time interval is reached.
"""

import threading
import time
from typing import Callable, List, Optional

from .processors import BaseProcessor


class BatchingProcessor(BaseProcessor):
    """Accumulate records and flush in batches.

    Parameters
    ----------
    sink:
        Callable that accepts a list of records and processes them.
    max_size:
        Flush when the buffer reaches this many records. Default 100.
    max_age:
        Flush when the oldest buffered record is this many seconds old.
        Set to ``None`` to disable time-based flushing. Default 5.0.
    """

    def __init__(
        self,
        sink: Callable[[List], None],
        *,
        max_size: int = 100,
        max_age: Optional[float] = 5.0,
    ) -> None:
        if max_size < 1:
            raise ValueError("max_size must be >= 1")
        self._sink = sink
        self._max_size = max_size
        self._max_age = max_age
        self._buffer: List = []
        self._oldest_ts: Optional[float] = None
        self._lock = threading.Lock()
        self._timer: Optional[threading.Timer] = None

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def process(self, record):
        """Buffer *record*, flushing if a threshold is met."""
        with self._lock:
            self._buffer.append(record)
            if self._oldest_ts is None:
                self._oldest_ts = time.monotonic()
                self._schedule_timer()
            if len(self._buffer) >= self._max_size:
                self._flush_locked()
        return record

    def flush(self) -> None:
        """Immediately flush all buffered records to the sink."""
        with self._lock:
            self._flush_locked()

    @property
    def buffered(self) -> int:
        """Number of records currently waiting in the buffer."""
        with self._lock:
            return len(self._buffer)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _flush_locked(self) -> None:
        """Must be called with *self._lock* held."""
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None
        if not self._buffer:
            return
        batch, self._buffer = self._buffer, []
        self._oldest_ts = None
        # Release lock while calling sink to avoid deadlocks.
        self._lock.release()
        try:
            self._sink(batch)
        finally:
            self._lock.acquire()

    def _schedule_timer(self) -> None:
        """Start a background timer to enforce *max_age* flushing."""
        if self._max_age is None:
            return
        self._timer = threading.Timer(self._max_age, self._on_timer)
        self._timer.daemon = True
        self._timer.start()

    def _on_timer(self) -> None:
        with self._lock:
            self._timer = None
            self._flush_locked()
