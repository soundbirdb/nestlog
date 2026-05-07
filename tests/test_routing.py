"""Tests for nestlog.routing."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from nestlog.routing import Router, by_field, by_level_name, by_predicate


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _FakeLevel:
    def __init__(self, name: str) -> None:
        self._name = name

    def __str__(self) -> str:
        return self._name


class _FakeRecord:
    def __init__(self, level_name: str = "INFO", **fields):
        self.level = _FakeLevel(level_name)
        self.fields = dict(fields)
        self.message = "test"


def _sink() -> MagicMock:
    return MagicMock(spec=["emit"])


# ---------------------------------------------------------------------------
# Router — exclusive mode (default)
# ---------------------------------------------------------------------------

class TestRouterExclusive:
    def test_first_matching_rule_wins(self):
        r = Router(exclusive=True)
        s1, s2 = _sink(), _sink()
        r.add_route(by_level_name("ERROR"), s1)
        r.add_route(by_level_name("ERROR"), s2)
        r.emit(_FakeRecord("ERROR"))
        s1.emit.assert_called_once()
        s2.emit.assert_not_called()

    def test_default_sink_receives_unmatched(self):
        r = Router()
        s_default = _sink()
        r.add_route(by_level_name("ERROR"), _sink())
        r.set_default(s_default)
        r.emit(_FakeRecord("DEBUG"))
        s_default.emit.assert_called_once()

    def test_no_default_and_no_match_is_silent(self):
        r = Router()
        r.add_route(by_level_name("ERROR"), _sink())
        # Should not raise
        r.emit(_FakeRecord("DEBUG"))


# ---------------------------------------------------------------------------
# Router — non-exclusive mode
# ---------------------------------------------------------------------------

class TestRouterNonExclusive:
    def test_all_matching_sinks_receive_record(self):
        r = Router(exclusive=False)
        s1, s2 = _sink(), _sink()
        r.add_route(by_level_name("WARNING"), s1)
        r.add_route(by_level_name("WARNING"), s2)
        r.emit(_FakeRecord("WARNING"))
        s1.emit.assert_called_once()
        s2.emit.assert_called_once()

    def test_default_not_called_when_rule_matches(self):
        r = Router(exclusive=False)
        s_default = _sink()
        r.add_route(by_level_name("INFO"), _sink())
        r.set_default(s_default)
        r.emit(_FakeRecord("INFO"))
        s_default.emit.assert_not_called()


# ---------------------------------------------------------------------------
# Rule helpers
# ---------------------------------------------------------------------------

def test_by_level_name_case_insensitive():
    rule = by_level_name("error")
    assert rule(_FakeRecord("ERROR")) is True
    assert rule(_FakeRecord("DEBUG")) is False


def test_by_field_matches_value():
    rule = by_field("service", "auth")
    assert rule(_FakeRecord(service="auth")) is True
    assert rule(_FakeRecord(service="billing")) is False
    assert rule(_FakeRecord()) is False


def test_by_predicate_passthrough():
    fn = lambda rec: True
    assert by_predicate(fn) is fn
