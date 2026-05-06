"""Tests for nestlog.formatters."""

import json
import time

import pytest

from nestlog.formatters import JSONFormatter, TextFormatter


class FakeLevel:
    def __init__(self, name: str):
        self._name = name

    def __str__(self) -> str:
        return self._name


class FakeRecord:
    def __init__(self, level="INFO", name="myapp", message="hello", **extra):
        self.level = FakeLevel(level)
        self.name = name
        self.message = message
        self.created = time.time()
        for k, v in extra.items():
            setattr(self, k, v)


# ---------------------------------------------------------------------------
# TextFormatter
# ---------------------------------------------------------------------------

class TestTextFormatter:
    def test_default_pattern_contains_level(self):
        fmt = TextFormatter()
        result = fmt.format(FakeRecord(level="WARNING"))
        assert "WARNING" in result

    def test_default_pattern_contains_name(self):
        fmt = TextFormatter()
        result = fmt.format(FakeRecord(name="svc.auth"))
        assert "svc.auth" in result

    def test_default_pattern_contains_message(self):
        fmt = TextFormatter()
        result = fmt.format(FakeRecord(message="something happened"))
        assert "something happened" in result

    def test_custom_pattern(self):
        fmt = TextFormatter(pattern="{level}|{message}")
        result = fmt.format(FakeRecord(level="DEBUG", message="test"))
        assert result == "DEBUG|test"

    def test_timestamp_format(self):
        fmt = TextFormatter(time_fmt="%Y")
        result = fmt.format(FakeRecord())
        import datetime
        assert str(datetime.datetime.now().year) in result


# ---------------------------------------------------------------------------
# JSONFormatter
# ---------------------------------------------------------------------------

class TestJSONFormatter:
    def test_output_is_valid_json(self):
        fmt = JSONFormatter()
        result = fmt.format(FakeRecord())
        parsed = json.loads(result)
        assert isinstance(parsed, dict)

    def test_required_keys_present(self):
        fmt = JSONFormatter()
        parsed = json.loads(fmt.format(FakeRecord()))
        for key in ("timestamp", "level", "name", "message"):
            assert key in parsed

    def test_level_value(self):
        fmt = JSONFormatter()
        parsed = json.loads(fmt.format(FakeRecord(level="ERROR")))
        assert parsed["level"] == "ERROR"

    def test_extra_fields_included(self):
        fmt = JSONFormatter(extra_fields=["request_id"])
        record = FakeRecord(request_id="abc-123")
        parsed = json.loads(fmt.format(record))
        assert parsed["request_id"] == "abc-123"

    def test_missing_extra_field_omitted(self):
        fmt = JSONFormatter(extra_fields=["trace_id"])
        parsed = json.loads(fmt.format(FakeRecord()))
        assert "trace_id" not in parsed
