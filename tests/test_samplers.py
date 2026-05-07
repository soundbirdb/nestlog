"""Tests for nestlog.samplers."""

import time
import threading
import pytest
from nestlog.samplers import SamplingFilter, RateLimitFilter


# ---------------------------------------------------------------------------
# Minimal fake record (no dependency on core)
# ---------------------------------------------------------------------------

class _FakeRecord:
    pass


RECORD = _FakeRecord()


# ---------------------------------------------------------------------------
# SamplingFilter
# ---------------------------------------------------------------------------

class TestSamplingFilter:
    def test_rate_one_always_allows(self):
        f = SamplingFilter(rate=1.0)
        assert all(f.allow(RECORD) for _ in range(100))

    def test_rate_zero_never_allows(self):
        f = SamplingFilter(rate=0.0)
        assert not any(f.allow(RECORD) for _ in range(100))

    def test_partial_rate_is_probabilistic(self):
        f = SamplingFilter(rate=0.5)
        results = [f.allow(RECORD) for _ in range(1000)]
        allowed = sum(results)
        # With rate=0.5 and 1000 trials, expect roughly 500 ± 100
        assert 300 < allowed < 700

    def test_invalid_rate_raises(self):
        with pytest.raises(ValueError):
            SamplingFilter(rate=1.5)
        with pytest.raises(ValueError):
            SamplingFilter(rate=-0.1)

    def test_rate_property(self):
        f = SamplingFilter(rate=0.3)
        assert f.rate == pytest.approx(0.3)

    def test_composable_with_and(self):
        """SamplingFilter inherits __and__ from BaseFilter."""
        always = SamplingFilter(rate=1.0)
        never = SamplingFilter(rate=0.0)
        combined = always & never
        assert not combined.allow(RECORD)


# ---------------------------------------------------------------------------
# RateLimitFilter
# ---------------------------------------------------------------------------

class TestRateLimitFilter:
    def test_allows_up_to_limit(self):
        f = RateLimitFilter(max_per_second=5)
        results = [f.allow(RECORD) for _ in range(10)]
        assert results[:5] == [True] * 5
        assert results[5:] == [False] * 5

    def test_resets_after_one_second(self):
        f = RateLimitFilter(max_per_second=3)
        # exhaust the window
        for _ in range(3):
            f.allow(RECORD)
        assert f.allow(RECORD) is False
        # force window reset
        f._window_start -= 1.1
        assert f.allow(RECORD) is True

    def test_invalid_max_raises(self):
        with pytest.raises(ValueError):
            RateLimitFilter(max_per_second=0)
        with pytest.raises(ValueError):
            RateLimitFilter(max_per_second=-1)

    def test_thread_safety(self):
        f = RateLimitFilter(max_per_second=50)
        allowed = []
        lock = threading.Lock()

        def worker():
            result = f.allow(RECORD)
            with lock:
                allowed.append(result)

        threads = [threading.Thread(target=worker) for _ in range(100)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert sum(allowed) == 50
