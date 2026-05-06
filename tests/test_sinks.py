"""Tests for nestlog built-in sinks."""

import io
import json
import os
import tempfile
import time
import pytest

from nestlog.sinks import StreamSink, JSONSink, FileSink


class FakeRecord:
    def __init__(self, message="hello", level="INFO", name="test", extra=None):
        self.message = message
        self.level = level
        self.name = name
        self.extra = extra or {}
        self.timestamp = time.time()

    def __str__(self):
        return self.level


# ── StreamSink ────────────────────────────────────────────────────────────────

class TestStreamSink:
    def test_basic_emit(self):
        buf = io.StringIO()
        sink = StreamSink(stream=buf)
        sink.emit(FakeRecord("world"))
        out = buf.getvalue()
        assert "world" in out
        assert "INFO" in out
        assert "test" in out

    def test_extra_fields_appended(self):
        buf = io.StringIO()
        sink = StreamSink(stream=buf)
        sink.emit(FakeRecord(extra={"req_id": "abc123"}))
        assert "req_id" in buf.getvalue()
        assert "abc123" in buf.getvalue()

    def test_custom_format(self):
        buf = io.StringIO()
        sink = StreamSink(stream=buf, fmt="{level}::{message}")
        sink.emit(FakeRecord("msg"))
        assert buf.getvalue().startswith("INFO::msg")

    def test_each_record_ends_with_newline(self):
        buf = io.StringIO()
        sink = StreamSink(stream=buf)
        sink.emit(FakeRecord())
        sink.emit(FakeRecord())
        assert buf.getvalue().count("\n") == 2


# ── JSONSink ──────────────────────────────────────────────────────────────────

class TestJSONSink:
    def test_valid_json_output(self):
        buf = io.StringIO()
        sink = JSONSink(stream=buf)
        sink.emit(FakeRecord("json test"))
        data = json.loads(buf.getvalue())
        assert data["message"] == "json test"
        assert data["level"] == "INFO"
        assert data["name"] == "test"
        assert "timestamp" in data

    def test_extra_fields_merged(self):
        buf = io.StringIO()
        sink = JSONSink(stream=buf)
        sink.emit(FakeRecord(extra={"user": "alice", "status": 200}))
        data = json.loads(buf.getvalue())
        assert data["user"] == "alice"
        assert data["status"] == 200


# ── FileSink ──────────────────────────────────────────────────────────────────

class TestFileSink:
    def test_writes_to_file(self, tmp_path):
        log_file = tmp_path / "app.log"
        sink = FileSink(str(log_file))
        sink.emit(FakeRecord("file record"))
        sink.close()
        content = log_file.read_text()
        assert "file record" in content

    def test_close_is_idempotent(self, tmp_path):
        log_file = tmp_path / "app.log"
        sink = FileSink(str(log_file))
        sink.emit(FakeRecord())
        sink.close()
        sink.close()  # should not raise

    def test_appends_by_default(self, tmp_path):
        log_file = tmp_path / "app.log"
        for _ in range(3):
            sink = FileSink(str(log_file))
            sink.emit(FakeRecord("line"))
            sink.close()
        lines = log_file.read_text().splitlines()
        assert len(lines) == 3
