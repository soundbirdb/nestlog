"""Tests for nestlog.handlers (AsyncHandler and BatchHandler)."""

import time
import threading
from unittest.mock import MagicMock

import pytest

from nestlog.handlers import AsyncHandler, BatchHandler


def _make_record(msg: str = "test") -> MagicMock:
    record = MagicMock()
    record.__str__ = lambda self: msg
    return record


# ---------------------------------------------------------------------------
# AsyncHandler
# ---------------------------------------------------------------------------

class TestAsyncHandler:
    def test_emit_reaches_sink(self):
        sink = MagicMock()
        handler = AsyncHandler(sink)
        record = _make_record()
        handler.emit(record)
        handler.flush()
        sink.emit.assert_called_once_with(record)

    def test_multiple_records_all_reach_sink(self):
        sink = MagicMock()
        handler = AsyncHandler(sink)
        records = [_make_record(str(i)) for i in range(10)]
        for r in records:
            handler.emit(r)
        handler.flush()
        assert sink.emit.call_count == 10

    def test_close_stops_worker(self):
        sink = MagicMock()
        handler = AsyncHandler(sink)
        handler.close()
        assert not handler._thread.is_alive()

    def test_drops_record_when_queue_full(self):
        sink = MagicMock()
        # Make sink slow so queue fills up
        barrier = threading.Event()

        def slow_emit(record):
            barrier.wait(timeout=5)

        sink.emit.side_effect = slow_emit
        handler = AsyncHandler(sink, maxsize=1)
        # Fill the queue
        for _ in range(20):
            handler.emit(_make_record())
        # Unblock the worker
        barrier.set()
        handler.flush()
        handler.close()
        # Should not raise; just verifies no exception on overflow

    def test_sink_exception_does_not_kill_worker(self):
        sink = MagicMock()
        sink.emit.side_effect = RuntimeError("boom")
        handler = AsyncHandler(sink)
        handler.emit(_make_record())
        handler.flush()
        # Worker should still be alive
        assert handler._thread.is_alive()
        handler.close()


# ---------------------------------------------------------------------------
# BatchHandler
# ---------------------------------------------------------------------------

class TestBatchHandler:
    def test_records_buffered_until_batch_size(self):
        sink = MagicMock()
        handler = BatchHandler(sink, batch_size=3)
        handler.emit(_make_record("a"))
        handler.emit(_make_record("b"))
        sink.emit.assert_not_called()
        handler.emit(_make_record("c"))
        assert sink.emit.call_count == 3

    def test_flush_sends_partial_batch(self):
        sink = MagicMock()
        handler = BatchHandler(sink, batch_size=10)
        handler.emit(_make_record())
        handler.emit(_make_record())
        handler.flush()
        assert sink.emit.call_count == 2

    def test_flush_clears_buffer(self):
        sink = MagicMock()
        handler = BatchHandler(sink, batch_size=10)
        handler.emit(_make_record())
        handler.flush()
        handler.flush()  # second flush should emit nothing new
        assert sink.emit.call_count == 1

    def test_close_flushes_remaining(self):
        sink = MagicMock()
        handler = BatchHandler(sink, batch_size=100)
        for _ in range(5):
            handler.emit(_make_record())
        handler.close()
        assert sink.emit.call_count == 5

    def test_invalid_batch_size_raises(self):
        with pytest.raises(ValueError):
            BatchHandler(MagicMock(), batch_size=0)

    def test_thread_safety(self):
        sink = MagicMock()
        handler = BatchHandler(sink, batch_size=5)
        threads = [
            threading.Thread(target=lambda: handler.emit(_make_record()))
            for _ in range(20)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        handler.flush()
        assert sink.emit.call_count == 20
