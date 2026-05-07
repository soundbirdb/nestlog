"""Integration tests: Router wired to real StreamSink instances."""

from __future__ import annotations

import io

from nestlog.routing import Router, by_field, by_level_name
from nestlog.sinks import StreamSink
from nestlog.formatters import TextFormatter


# ---------------------------------------------------------------------------
# Minimal stand-ins that satisfy StreamSink's expectations
# ---------------------------------------------------------------------------

class _Level:
    def __init__(self, name: str, value: int) -> None:
        self._name = name
        self.value = value

    def __str__(self) -> str:
        return self._name


class _Record:
    def __init__(self, level_name: str, message: str, **fields):
        self.level = _Level(level_name, 20)
        self.message = message
        self.fields = fields
        self.timestamp = "2024-01-01T00:00:00"

    def __str__(self) -> str:
        return f"[{self.level}] {self.message}"


def _make_stream_sink(buf: io.StringIO) -> StreamSink:
    sink = StreamSink(buf)
    sink.set_formatter(TextFormatter())
    return sink


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestRouterWithRealSinks:
    def test_error_records_go_to_error_stream(self):
        error_buf, default_buf = io.StringIO(), io.StringIO()
        router = (
            Router()
            .add_route(by_level_name("ERROR"), _make_stream_sink(error_buf))
            .set_default(_make_stream_sink(default_buf))
        )
        router.emit(_Record("ERROR", "boom"))
        assert "boom" in error_buf.getvalue()
        assert default_buf.getvalue() == ""

    def test_non_error_records_go_to_default(self):
        error_buf, default_buf = io.StringIO(), io.StringIO()
        router = (
            Router()
            .add_route(by_level_name("ERROR"), _make_stream_sink(error_buf))
            .set_default(_make_stream_sink(default_buf))
        )
        router.emit(_Record("INFO", "hello"))
        assert error_buf.getvalue() == ""
        assert "hello" in default_buf.getvalue()

    def test_field_based_routing(self):
        audit_buf, default_buf = io.StringIO(), io.StringIO()
        router = (
            Router()
            .add_route(by_field("audit", True), _make_stream_sink(audit_buf))
            .set_default(_make_stream_sink(default_buf))
        )
        router.emit(_Record("INFO", "user login", audit=True, user="alice"))
        router.emit(_Record("INFO", "cache miss", audit=False))
        assert "user login" in audit_buf.getvalue()
        assert "cache miss" in default_buf.getvalue()

    def test_non_exclusive_fan_out(self):
        buf1, buf2 = io.StringIO(), io.StringIO()
        router = Router(exclusive=False)
        router.add_route(by_level_name("WARNING"), _make_stream_sink(buf1))
        router.add_route(by_level_name("WARNING"), _make_stream_sink(buf2))
        router.emit(_Record("WARNING", "disk space low"))
        assert "disk space low" in buf1.getvalue()
        assert "disk space low" in buf2.getvalue()
