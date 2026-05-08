"""Tests for nestlog.deduplicator.DeduplicatorProcessor."""

import time
import pytest
from nestlog.deduplicator import DeduplicatorProcessor


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

class _Level:
    def __init__(self, name: str) -> None:
        self._name = name

    def __str__(self) -> str:
        return self._name


class _Record:
    def __init__(self, level_name: str, message: str, **fields):
        self.level = _Level(level_name)
        self.message = message
        self.fields = fields


def _make_record(message: str = "hello", level: str = "INFO", **fields):
    return _Record(level, message, **fields)


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------

class TestDeduplicatorProcessor:
    def test_first_occurrence_passes_through(self):
        proc = DeduplicatorProcessor(window=60)
        rec = _make_record("msg")
        assert proc.process(rec) is rec

    def test_immediate_duplicate_is_suppressed(self):
        proc = DeduplicatorProcessor(window=60)
        rec1 = _make_record("msg")
        rec2 = _make_record("msg")
        proc.process(rec1)
        assert proc.process(rec2) is None

    def test_different_messages_both_pass(self):
        proc = DeduplicatorProcessor(window=60)
        assert proc.process(_make_record("msg A")) is not None
        assert proc.process(_make_record("msg B")) is not None

    def test_different_levels_both_pass(self):
        proc = DeduplicatorProcessor(window=60)
        assert proc.process(_make_record("msg", level="INFO")) is not None
        assert proc.process(_make_record("msg", level="ERROR")) is not None

    def test_record_passes_after_window_expires(self, monkeypatch):
        proc = DeduplicatorProcessor(window=5)
        start = time.monotonic()
        monkeypatch.setattr(time, "monotonic", lambda: start)
        proc.process(_make_record("msg"))

        # advance time beyond window
        monkeypatch.setattr(time, "monotonic", lambda: start + 6)
        assert proc.process(_make_record("msg")) is not None

    def test_extra_fields_included_in_key(self):
        proc = DeduplicatorProcessor(window=60, fields=("request_id",))
        r1 = _make_record("msg", request_id="aaa")
        r2 = _make_record("msg", request_id="bbb")
        assert proc.process(r1) is not None
        assert proc.process(r2) is not None  # different field value -> not dup

    def test_extra_fields_same_value_is_suppressed(self):
        proc = DeduplicatorProcessor(window=60, fields=("request_id",))
        r1 = _make_record("msg", request_id="aaa")
        r2 = _make_record("msg", request_id="aaa")
        proc.process(r1)
        assert proc.process(r2) is None

    def test_max_entries_evicts_oldest(self, monkeypatch):
        start = time.monotonic()
        monkeypatch.setattr(time, "monotonic", lambda: start)

        proc = DeduplicatorProcessor(window=9999, max_entries=3)
        proc.process(_make_record("a"))
        proc.process(_make_record("b"))
        proc.process(_make_record("c"))
        # adding "d" should evict the oldest ("a")
        proc.process(_make_record("d"))
        # "a" should now be allowed through again
        assert proc.process(_make_record("a")) is not None

    def test_returns_same_record_object(self):
        proc = DeduplicatorProcessor()
        rec = _make_record("unique-message-xyz")
        result = proc.process(rec)
        assert result is rec
