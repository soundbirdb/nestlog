"""Tests for nestlog.buffering.BufferingProcessor."""

import pytest

from nestlog.buffering import BufferingProcessor


# ---------------------------------------------------------------------------
# Minimal fake record
# ---------------------------------------------------------------------------

class _Record:
    def __init__(self, msg: str) -> None:
        self.message = msg
        self.fields: dict = {}

    def __repr__(self) -> str:  # pragma: no cover
        return f"_Record({self.message!r})"


def _rec(msg: str = "hello") -> _Record:
    return _Record(msg)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

class TestConstruction:
    def test_default_capacity(self):
        bp = BufferingProcessor()
        assert bp.capacity == 100

    def test_custom_capacity(self):
        bp = BufferingProcessor(capacity=5)
        assert bp.capacity == 5

    def test_invalid_capacity_raises(self):
        with pytest.raises(ValueError):
            BufferingProcessor(capacity=0)


# ---------------------------------------------------------------------------
# Buffering behaviour
# ---------------------------------------------------------------------------

class TestBuffering:
    def test_records_are_buffered(self):
        bp = BufferingProcessor(capacity=10)
        bp.process(_rec("a"))
        bp.process(_rec("b"))
        assert len(bp.buffered) == 2

    def test_process_returns_record(self):
        bp = BufferingProcessor(capacity=10)
        r = _rec()
        assert bp.process(r) is r

    def test_buffered_is_a_copy(self):
        bp = BufferingProcessor(capacity=10)
        bp.process(_rec())
        snapshot = bp.buffered
        bp.process(_rec())
        assert len(snapshot) == 1  # original snapshot unchanged


# ---------------------------------------------------------------------------
# Auto-flush
# ---------------------------------------------------------------------------

class TestAutoFlush:
    def test_auto_flush_triggers_at_capacity(self):
        flushed = []
        bp = BufferingProcessor(capacity=3, flush_fn=flushed.extend)
        for i in range(3):
            bp.process(_rec(str(i)))
        assert len(flushed) == 3
        assert len(bp.buffered) == 0

    def test_auto_flush_disabled(self):
        flushed = []
        bp = BufferingProcessor(capacity=2, flush_fn=flushed.extend, auto_flush=False)
        bp.process(_rec("x"))
        bp.process(_rec("y"))
        assert flushed == []
        assert len(bp.buffered) == 2

    def test_manual_flush_clears_buffer(self):
        flushed = []
        bp = BufferingProcessor(capacity=10, flush_fn=flushed.extend)
        bp.process(_rec("a"))
        bp.process(_rec("b"))
        bp.flush()
        assert len(flushed) == 2
        assert bp.buffered == []

    def test_flush_empty_buffer_is_noop(self):
        called = []
        bp = BufferingProcessor(capacity=5, flush_fn=lambda rs: called.extend(rs))
        bp.flush()  # should not raise
        assert called == []

    def test_default_flush_fn_is_noop(self):
        bp = BufferingProcessor(capacity=2)
        bp.process(_rec())
        bp.process(_rec())  # triggers auto-flush with default no-op
        assert bp.buffered == []  # buffer cleared even with no-op
