"""Tests for nestlog.serializers."""

import json
import datetime
import pytest

from nestlog.serializers import JSONSerializer, LineSerializer, _default_encoder


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _FakeLevel:
    def __init__(self, name: str) -> None:
        self._name = name

    def __str__(self) -> str:
        return self._name


class _FakeRecord:
    def __init__(self, message: str, level: str = "INFO", fields=None, timestamp=None):
        self.level = _FakeLevel(level)
        self._message = message
        self.fields = fields or {}
        self.timestamp = timestamp

    def __str__(self) -> str:
        return self._message


def _make_record(**kwargs):
    return _FakeRecord(**kwargs)


# ---------------------------------------------------------------------------
# _default_encoder
# ---------------------------------------------------------------------------

def test_default_encoder_datetime():
    dt = datetime.datetime(2024, 1, 15, 12, 0, 0)
    assert _default_encoder(dt) == "2024-01-15T12:00:00"


def test_default_encoder_date():
    d = datetime.date(2024, 6, 1)
    assert _default_encoder(d) == "2024-06-01"


def test_default_encoder_set():
    result = _default_encoder({1, 2, 3})
    assert sorted(result) == [1, 2, 3]


def test_default_encoder_fallback():
    assert _default_encoder(object()) is not None


# ---------------------------------------------------------------------------
# JSONSerializer
# ---------------------------------------------------------------------------

class TestJSONSerializer:
    def test_basic_fields_present(self):
        s = JSONSerializer()
        record = _make_record(message="hello", level="DEBUG")
        data = json.loads(s.serialize(record))
        assert data["level"] == "DEBUG"
        assert data["message"] == "hello"

    def test_extra_fields_included(self):
        s = JSONSerializer()
        record = _make_record(message="hi", fields={"user": "alice", "req_id": "abc"})
        data = json.loads(s.serialize(record))
        assert data["user"] == "alice"
        assert data["req_id"] == "abc"

    def test_timestamp_serialized(self):
        s = JSONSerializer()
        ts = datetime.datetime(2024, 3, 10, 8, 30, 0)
        record = _make_record(message="ts test", timestamp=ts)
        data = json.loads(s.serialize(record))
        assert data["timestamp"] == "2024-03-10T08:30:00"

    def test_no_timestamp_key_when_none(self):
        s = JSONSerializer()
        record = _make_record(message="no ts")
        data = json.loads(s.serialize(record))
        assert "timestamp" not in data

    def test_sort_keys(self):
        s = JSONSerializer(sort_keys=True)
        record = _make_record(message="sorted", fields={"z": 1, "a": 2})
        raw = s.serialize(record)
        keys = list(json.loads(raw).keys())
        assert keys == sorted(keys)


# ---------------------------------------------------------------------------
# LineSerializer
# ---------------------------------------------------------------------------

class TestLineSerializer:
    def test_basic_output(self):
        s = LineSerializer()
        record = _make_record(message="hello", level="INFO")
        line = s.serialize(record)
        assert "level=INFO" in line
        assert "msg=hello" in line

    def test_values_with_spaces_are_quoted(self):
        s = LineSerializer()
        record = _make_record(message="hello world", level="INFO")
        line = s.serialize(record)
        assert 'msg="hello world"' in line

    def test_extra_fields_appended(self):
        s = LineSerializer()
        record = _make_record(message="ok", fields={"env": "prod"})
        line = s.serialize(record)
        assert "env=prod" in line

    def test_timestamp_included(self):
        s = LineSerializer()
        ts = datetime.datetime(2024, 1, 1, 0, 0, 0)
        record = _make_record(message="ts", timestamp=ts)
        line = s.serialize(record)
        assert "ts=2024-01-01T00:00:00" in line
