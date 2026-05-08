"""Tests for nestlog.throttle.ThrottleProcessor."""

import time
import pytest

from nestlog.throttle import ThrottleProcessor


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _Level:
    def __init__(self, name: str):
        self._name = name

    def __str__(self) -> str:
        return self._name


class _Record:
    def __init__(self, name: str, level: str, message: str):
        self.name = name
        self.level = _Level(level)
        self.message = message


def _rec(message="hello", name="app", level="INFO"):
    return _Record(name=name, level=level, message=message)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_default_construction():
    tp = ThrottleProcessor()
    assert tp._window == 60.0
    assert tp._max_cache == 1024


def test_invalid_window_raises():
    with pytest.raises(ValueError, match="window"):
        ThrottleProcessor(window=-1)


def test_invalid_max_cache_raises():
    with pytest.raises(ValueError, match="max_cache"):
        ThrottleProcessor(max_cache=0)


# ---------------------------------------------------------------------------
# Basic allow / suppress behaviour
# ---------------------------------------------------------------------------

def test_first_occurrence_is_allowed():
    tp = ThrottleProcessor(window=5.0)
    record = _rec()
    assert tp.process(record) is record


def test_immediate_duplicate_is_suppressed():
    tp = ThrottleProcessor(window=5.0)
    record = _rec()
    tp.process(record)
    assert tp.process(_rec()) is None


def test_different_message_is_allowed():
    tp = ThrottleProcessor(window=5.0)
    tp.process(_rec("hello"))
    result = tp.process(_rec("world"))
    assert result is not None


def test_different_level_is_allowed():
    tp = ThrottleProcessor(window=5.0)
    tp.process(_rec(level="INFO"))
    result = tp.process(_rec(level="ERROR"))
    assert result is not None


def test_different_logger_name_is_allowed():
    tp = ThrottleProcessor(window=5.0)
    tp.process(_rec(name="app.a"))
    result = tp.process(_rec(name="app.b"))
    assert result is not None


# ---------------------------------------------------------------------------
# Window expiry
# ---------------------------------------------------------------------------

def test_record_allowed_after_window_expires(monkeypatch):
    tp = ThrottleProcessor(window=1.0)
    fake_time = [0.0]

    monkeypatch.setattr(time, "monotonic", lambda: fake_time[0])

    tp.process(_rec())          # admitted at t=0
    fake_time[0] = 0.5
    assert tp.process(_rec()) is None   # within window
    fake_time[0] = 1.0
    result = tp.process(_rec())         # exactly at boundary — allowed
    assert result is not None


# ---------------------------------------------------------------------------
# Cache eviction
# ---------------------------------------------------------------------------

def test_cache_evicts_oldest_when_full():
    tp = ThrottleProcessor(window=60.0, max_cache=3)
    tp.process(_rec(message="a"))
    tp.process(_rec(message="b"))
    tp.process(_rec(message="c"))
    # Cache is full; adding a new key must evict one entry.
    tp.process(_rec(message="d"))
    assert len(tp._cache) == 3


# ---------------------------------------------------------------------------
# Reset
# ---------------------------------------------------------------------------

def test_reset_clears_state():
    tp = ThrottleProcessor(window=60.0)
    tp.process(_rec())
    tp.reset()
    assert len(tp._cache) == 0
    # After reset the same message should be admitted again.
    assert tp.process(_rec()) is not None
