"""Tests for nestlog.pipeline.Pipeline."""

from __future__ import annotations

import pytest

from nestlog.pipeline import Pipeline
from nestlog.processors import BaseProcessor
from nestlog.sinks import BaseSink
from nestlog.core import LogRecord


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _Level:
    def __init__(self, name: str, value: int) -> None:
        self.name = name
        self.value = value

    def __str__(self) -> str:
        return self.name


def _make_record(msg: str = "hello", **fields) -> LogRecord:
    return LogRecord(
        level=_Level("INFO", 20),
        message=msg,
        fields=fields,
    )


class CaptureSink(BaseSink):
    def __init__(self) -> None:
        super().__init__()
        self.received: list[LogRecord] = []
        self.flushed = False
        self.closed = False

    def emit(self, record: LogRecord) -> None:
        self.received.append(record)

    def flush(self) -> None:
        self.flushed = True

    def close(self) -> None:
        self.closed = True


class PassthroughProcessor(BaseProcessor):
    def process(self, record: LogRecord):
        return record


class DroppingProcessor(BaseProcessor):
    """Always drops the record."""

    def process(self, record: LogRecord):
        return None


class TaggingProcessor(BaseProcessor):
    """Adds a 'tagged' field to the record."""

    def process(self, record: LogRecord):
        record.fields["tagged"] = True
        return record


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_emit_reaches_sink_with_no_processors():
    sink = CaptureSink()
    pipeline = Pipeline(sink=sink)
    rec = _make_record()
    pipeline.emit(rec)
    assert len(sink.received) == 1
    assert sink.received[0] is rec


def test_passthrough_processor_does_not_drop():
    sink = CaptureSink()
    pipeline = Pipeline(sink=sink, processors=[PassthroughProcessor()])
    pipeline.emit(_make_record())
    assert len(sink.received) == 1


def test_dropping_processor_prevents_sink_emit():
    sink = CaptureSink()
    pipeline = Pipeline(sink=sink, processors=[DroppingProcessor()])
    pipeline.emit(_make_record())
    assert sink.received == []


def test_processor_order_is_preserved():
    """DroppingProcessor after Tagging still drops the record."""
    sink = CaptureSink()
    pipeline = Pipeline(
        sink=sink,
        processors=[TaggingProcessor(), DroppingProcessor()],
    )
    pipeline.emit(_make_record())
    assert sink.received == []


def test_tagging_processor_mutates_fields():
    sink = CaptureSink()
    pipeline = Pipeline(sink=sink, processors=[TaggingProcessor()])
    rec = _make_record()
    pipeline.emit(rec)
    assert sink.received[0].fields.get("tagged") is True


def test_add_processor_returns_self_for_chaining():
    sink = CaptureSink()
    pipeline = Pipeline(sink=sink)
    result = pipeline.add_processor(PassthroughProcessor())
    assert result is pipeline


def test_flush_delegates_to_sink():
    sink = CaptureSink()
    pipeline = Pipeline(sink=sink)
    pipeline.flush()
    assert sink.flushed is True


def test_close_delegates_to_sink():
    sink = CaptureSink()
    pipeline = Pipeline(sink=sink)
    pipeline.close()
    assert sink.closed is True


def test_flush_is_noop_when_sink_has_no_flush():
    """Pipeline.flush() must not raise when sink lacks flush."""

    class MinimalSink(BaseSink):
        def emit(self, record):
            pass

    pipeline = Pipeline(sink=MinimalSink())
    pipeline.flush()  # should not raise


def test_multiple_records_all_emitted():
    sink = CaptureSink()
    pipeline = Pipeline(sink=sink, processors=[PassthroughProcessor()])
    records = [_make_record(f"msg-{i}") for i in range(5)]
    for r in records:
        pipeline.emit(r)
    assert len(sink.received) == 5
