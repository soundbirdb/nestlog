"""Tests for nestlog.filters."""

from __future__ import annotations

import pytest

from nestlog.core import Level, LogRecord
from nestlog.filters import (
    CallableFilter,
    CompositeFilter,
    LevelFilter,
    NameFilter,
)


def _make_record(level: Level = Level.INFO, name: str = "app") -> LogRecord:
    return LogRecord(level=level, name=name, message="test")


class TestLevelFilter:
    def test_allows_exact_level(self):
        f = LevelFilter(min_level=Level.INFO, max_level=Level.INFO)
        assert f.allow(_make_record(Level.INFO))

    def test_rejects_below_min(self):
        f = LevelFilter(min_level=Level.WARNING)
        assert not f.allow(_make_record(Level.DEBUG))

    def test_rejects_above_max(self):
        f = LevelFilter(max_level=Level.WARNING)
        assert not f.allow(_make_record(Level.ERROR))

    def test_allows_range(self):
        f = LevelFilter(min_level=Level.DEBUG, max_level=Level.CRITICAL)
        for lvl in (Level.DEBUG, Level.INFO, Level.WARNING, Level.ERROR, Level.CRITICAL):
            assert f.allow(_make_record(lvl))


class TestNameFilter:
    def test_allows_matching_prefix(self):
        f = NameFilter("app")
        assert f.allow(_make_record(name="app.module"))

    def test_rejects_non_matching(self):
        f = NameFilter("app")
        assert not f.allow(_make_record(name="other"))

    def test_exact_match(self):
        f = NameFilter("app")
        assert f.allow(_make_record(name="app"))


class TestCallableFilter:
    def test_passes_through_true(self):
        f = CallableFilter(lambda r: True)
        assert f.allow(_make_record())

    def test_passes_through_false(self):
        f = CallableFilter(lambda r: False)
        assert not f.allow(_make_record())

    def test_uses_record_attributes(self):
        f = CallableFilter(lambda r: r.level >= Level.WARNING)
        assert f.allow(_make_record(Level.WARNING))
        assert not f.allow(_make_record(Level.DEBUG))


class TestCompositeFilter:
    def test_and_both_true(self):
        f = LevelFilter(min_level=Level.INFO) & NameFilter("app")
        assert f.allow(_make_record(Level.INFO, "app"))

    def test_and_one_false(self):
        f = LevelFilter(min_level=Level.ERROR) & NameFilter("app")
        assert not f.allow(_make_record(Level.INFO, "app"))

    def test_or_one_true(self):
        f = LevelFilter(min_level=Level.ERROR) | NameFilter("app")
        assert f.allow(_make_record(Level.INFO, "app"))

    def test_or_both_false(self):
        f = LevelFilter(min_level=Level.ERROR) | NameFilter("special")
        assert not f.allow(_make_record(Level.DEBUG, "app"))

    def test_invalid_mode_raises(self):
        with pytest.raises(ValueError, match="mode"):
            CompositeFilter([], mode="xor")
