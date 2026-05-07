"""Async and batching log handlers for nestlog."""

import queue
import threading
from typing import Optional

from nestlog.sinks import BaseSink
from nestlog.core import LogRecord


class AsyncHandler:
    """Wraps a sink and emits records asynchronously in a background thread."""

    def __init__(self, sink: BaseSink, maxsize: int = 1000) -> None:
        self._sink = sink
        self._queue: queue.Queue[Optional[LogRecord]] = queue.Queue(maxsize=maxsize)
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def emit(self, record: LogRecord) -> None:
        """Enqueue a record for async emission. Drops record if queue is full."""
        try:
            self._queue.put_nowait(record)
        except queue.Full:
            pass

    def _worker(self) -> None:
        while True:
            record = self._queue.get()
            if record is None:
                break
            try:
                self._sink.emit(record)
            except Exception:  # noqa: BLE001
                pass
            finally:
                self._queue.task_done()

    def flush(self) -> None:
        """Block until all queued records have been processed."""
        self._queue.join()

    def close(self) -> None:
        """Signal the worker thread to stop and wait for it to finish."""
        self._queue.put(None)
        self._thread.join()


class BatchHandler:
    """Accumulates records and flushes them to a sink in configurable batches."""

    def __init__(self, sink: BaseSink, batch_size: int = 50) -> None:
        if batch_size < 1:
            raise ValueError("batch_size must be >= 1")
        self._sink = sink
        self._batch_size = batch_size
        self._buffer: list[LogRecord] = []
        self._lock = threading.Lock()

    def emit(self, record: LogRecord) -> None:
        """Buffer the record and auto-flush when the batch size is reached."""
        with self._lock:
            self._buffer.append(record)
            if len(self._buffer) >= self._batch_size:
                self._flush_locked()

    def flush(self) -> None:
        """Flush any remaining buffered records immediately."""
        with self._lock:
            self._flush_locked()

    def _flush_locked(self) -> None:
        for record in self._buffer:
            try:
                self._sink.emit(record)
            except Exception:  # noqa: BLE001
                pass
        self._buffer.clear()

    def close(self) -> None:
        """Flush remaining records and release resources."""
        self.flush()
