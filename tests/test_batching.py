"""Tests for nestlog.batching.BatchingProcessor."""

import threading
import time

import pytest

from nestlog.batching import BatchingProcessor


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _Record:
    def __init__(self, msg: str):
        self.msg = msg

    def __repr__(self):
        return f"_Record({self.msg!r})"


def _rec(msg="hello"):
    return _Record(msg)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

class TestConstruction:
    def test_default_attributes(self):
        bp = BatchingProcessor(sink=lambda b: None)
        assert bp.buffered == 0

    def test_invalid_max_size_raises(self):
        with pytest.raises(ValueError):
            BatchingProcessor(sink=lambda b: None, max_size=0)


# ---------------------------------------------------------------------------
# Size-based flushing
# ---------------------------------------------------------------------------

class TestSizeFlush:
    def test_no_flush_below_threshold(self):
        received = []
        bp = BatchingProcessor(sink=received.append, max_size=3, max_age=None)
        bp.process(_rec("a"))
        bp.process(_rec("b"))
        assert received == []
        assert bp.buffered == 2

    def test_flush_at_threshold(self):
        batches = []
        bp = BatchingProcessor(sink=batches.append, max_size=2, max_age=None)
        bp.process(_rec("a"))
        bp.process(_rec("b"))
        assert len(batches) == 1
        assert len(batches[0]) == 2
        assert bp.buffered == 0

    def test_overflow_starts_new_buffer(self):
        batches = []
        bp = BatchingProcessor(sink=batches.append, max_size=2, max_age=None)
        for i in range(5):
            bp.process(_rec(str(i)))
        # 2 full batches flushed; 1 record still buffered
        assert len(batches) == 2
        assert bp.buffered == 1


# ---------------------------------------------------------------------------
# Manual flush
# ---------------------------------------------------------------------------

class TestManualFlush:
    def test_flush_empties_buffer(self):
        batches = []
        bp = BatchingProcessor(sink=batches.append, max_size=100, max_age=None)
        bp.process(_rec("x"))
        bp.process(_rec("y"))
        bp.flush()
        assert len(batches) == 1
        assert bp.buffered == 0

    def test_flush_empty_buffer_is_noop(self):
        batches = []
        bp = BatchingProcessor(sink=batches.append, max_size=10, max_age=None)
        bp.flush()  # should not raise
        assert batches == []


# ---------------------------------------------------------------------------
# Time-based flushing
# ---------------------------------------------------------------------------

class TestAgeFlush:
    def test_flush_after_max_age(self):
        batches = []
        bp = BatchingProcessor(sink=batches.append, max_size=100, max_age=0.05)
        bp.process(_rec("timed"))
        assert bp.buffered == 1
        time.sleep(0.15)
        assert len(batches) == 1
        assert batches[0][0].msg == "timed"

    def test_no_timer_without_max_age(self):
        batches = []
        bp = BatchingProcessor(sink=batches.append, max_size=100, max_age=None)
        bp.process(_rec("no-timer"))
        time.sleep(0.05)
        # Nothing flushed automatically
        assert batches == []
        bp.flush()


# ---------------------------------------------------------------------------
# Thread safety
# ---------------------------------------------------------------------------

class TestThreadSafety:
    def test_concurrent_process_calls(self):
        batches = []
        lock = threading.Lock()

        def sink(batch):
            with lock:
                batches.append(batch)

        bp = BatchingProcessor(sink=sink, max_size=10, max_age=None)
        threads = [threading.Thread(target=bp.process, args=(_rec(str(i)),)) for i in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        bp.flush()
        total = sum(len(b) for b in batches)
        assert total == 50
