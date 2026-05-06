"""Tests for nestlog.sinks (StreamSink, FileSink, NullSink) including filter integration."""

from __future__ import annotations

import io
import os
import tempfile

import pytest

from nestlog.core import Level, LogRecord
from nestlog.filters import LevelFilter, NameFilter
from nestlog.sinks import FileSink, NullSink, StreamSink


class FakeRecord:
    """Minimal stand-in for LogRecord."""

    def __init__(self, level: Level = Level.INFO, name: str = "test", message: str = "hello") -> None:
        self.level = level
        self.name = name
        self.message = message

    def __str__(self) -> str:
        return self.message


class TestStreamSink:
    def test_basic_emit(self):
        buf = io.StringIO()
        sink = StreamSink(stream=buf)
        sink.emit(FakeRecord())
        assert "hello" in buf.getvalue()

    def test_format_contains_level_and_name(self):
        buf = io.StringIO()
        sink = StreamSink(stream=buf)
        sink.emit(FakeRecord(Level.WARNING, "myapp"))
        output = buf.getvalue()
        assert "myapp" in output
        assert "WARNING" in output

    def test_custom_format(self):
        buf = io.StringIO()
        sink = StreamSink(stream=buf, fmt="{message}")
        sink.emit(FakeRecord(message="custom"))
        assert buf.getvalue().strip() == "custom"

    def test_filter_blocks_record(self):
        buf = io.StringIO()
        sink = StreamSink(stream=buf, filter=LevelFilter(min_level=Level.ERROR))
        sink.emit(FakeRecord(Level.DEBUG))
        assert buf.getvalue() == ""

    def test_filter_allows_record(self):
        buf = io.StringIO()
        sink = StreamSink(stream=buf, filter=LevelFilter(min_level=Level.INFO))
        sink.emit(FakeRecord(Level.INFO))
        assert buf.getvalue() != ""

    def test_set_filter_after_construction(self):
        buf = io.StringIO()
        sink = StreamSink(stream=buf)
        sink.set_filter(NameFilter("special"))
        sink.emit(FakeRecord(name="other"))
        assert buf.getvalue() == ""

    def test_close_does_not_close_stderr(self, capsys):
        import sys
        sink = StreamSink(stream=sys.stderr)
        sink.close()  # should not raise or close stderr


class TestFileSink:
    def test_writes_to_file(self):
        with tempfile.NamedTemporaryFile(mode="r", suffix=".log", delete=False) as f:
            path = f.name
        try:
            sink = FileSink(path)
            sink.emit(FakeRecord(message="file-test"))
            sink.close()
            content = open(path).read()
            assert "file-test" in content
        finally:
            os.unlink(path)

    def test_appends_on_reopen(self):
        with tempfile.NamedTemporaryFile(mode="r", suffix=".log", delete=False) as f:
            path = f.name
        try:
            for msg in ("first", "second"):
                sink = FileSink(path)
                sink.emit(FakeRecord(message=msg))
                sink.close()
            content = open(path).read()
            assert "first" in content and "second" in content
        finally:
            os.unlink(path)


class TestNullSink:
    def test_discards_records(self):
        sink = NullSink()
        sink.emit(FakeRecord())  # should not raise

    def test_close_is_noop(self):
        sink = NullSink()
        sink.close()  # should not raise
