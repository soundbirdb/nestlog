"""Tests for nestlog.ratelimit.TokenBucketProcessor."""

import time
import pytest

from nestlog.ratelimit import TokenBucketProcessor, _default_key


# ---------------------------------------------------------------------------
# Minimal fake record
# ---------------------------------------------------------------------------

class _Level:
    def __init__(self, name: str):
        self._name = name

    def __str__(self) -> str:
        return self._name


class _Record:
    def __init__(self, name: str = "app", level: str = "INFO"):
        self.name = name
        self.level = _Level(level)
        self.message = "hello"
        self.fields: dict = {}


def _rec(name="app", level="INFO") -> _Record:
    return _Record(name=name, level=level)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

class TestConstruction:
    def test_positive_rate_ok(self):
        p = TokenBucketProcessor(rate=5.0)
        assert p._rate == 5.0

    def test_capacity_defaults_to_rate(self):
        p = TokenBucketProcessor(rate=3.0)
        assert p._capacity == 3.0

    def test_explicit_capacity(self):
        p = TokenBucketProcessor(rate=2.0, capacity=10.0)
        assert p._capacity == 10.0

    def test_zero_rate_raises(self):
        with pytest.raises(ValueError):
            TokenBucketProcessor(rate=0)

    def test_negative_rate_raises(self):
        with pytest.raises(ValueError):
            TokenBucketProcessor(rate=-1.0)


# ---------------------------------------------------------------------------
# Behaviour
# ---------------------------------------------------------------------------

class TestTokenBucket:
    def test_first_message_always_passes(self):
        p = TokenBucketProcessor(rate=1.0)
        assert p.process(_rec()) is not None

    def test_burst_up_to_capacity_passes(self):
        capacity = 5
        p = TokenBucketProcessor(rate=100.0, capacity=float(capacity))
        results = [p.process(_rec()) for _ in range(capacity)]
        assert all(r is not None for r in results)

    def test_exceeding_capacity_is_dropped(self):
        p = TokenBucketProcessor(rate=100.0, capacity=3.0)
        # drain the bucket
        for _ in range(3):
            p.process(_rec())
        # next one should be dropped
        assert p.process(_rec()) is None

    def test_tokens_refill_over_time(self):
        p = TokenBucketProcessor(rate=100.0, capacity=1.0)
        p.process(_rec())  # consume the only token
        assert p.process(_rec()) is None
        # Manually advance the bucket's last-seen timestamp into the past
        key = _default_key(_rec())
        tokens, last = p._buckets[key]
        p._buckets[key] = (tokens, last - 1.0)  # pretend 1 s has passed
        assert p.process(_rec()) is not None

    def test_different_keys_have_independent_buckets(self):
        p = TokenBucketProcessor(rate=100.0, capacity=1.0)
        r_info = _rec(level="INFO")
        r_warn = _rec(level="WARNING")
        p.process(r_info)  # drain INFO bucket
        # WARNING bucket should still be full
        assert p.process(r_warn) is not None

    def test_custom_key_fn(self):
        p = TokenBucketProcessor(rate=100.0, capacity=1.0, key_fn=lambda r: "fixed")
        p.process(_rec(name="a"))
        # second call uses same key -> dropped
        assert p.process(_rec(name="b")) is None

    def test_process_returns_same_record_object(self):
        p = TokenBucketProcessor(rate=10.0)
        r = _rec()
        assert p.process(r) is r
