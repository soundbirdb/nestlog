"""Tests for nestlog.processors."""

import sys
from unittest.mock import MagicMock

import pytest

from nestlog.processors import (
    BaseProcessor,
    ChainedProcessor,
    ExceptionProcessor,
    FieldRenameProcessor,
)


def _make_record(message="test", **fields):
    record = MagicMock()
    record.level = MagicMock()
    record.message = message
    record.fields = fields
    record.timestamp = 0.0
    return record


# ---------------------------------------------------------------------------
# BaseProcessor
# ---------------------------------------------------------------------------

class TestBaseProcessor:
    def test_process_raises(self):
        with pytest.raises(NotImplementedError):
            BaseProcessor().process(_make_record())

    def test_add_returns_chained(self):
        class Passthrough(BaseProcessor):
            def process(self, record):
                return record

        a, b = Passthrough(), Passthrough()
        chained = a + b
        assert isinstance(chained, ChainedProcessor)


# ---------------------------------------------------------------------------
# ChainedProcessor
# ---------------------------------------------------------------------------

class TestChainedProcessor:
    def test_passes_record_through_all(self):
        calls = []

        class Tracker(BaseProcessor):
            def __init__(self, name):
                self.name = name

            def process(self, record):
                calls.append(self.name)
                return record

        chain = ChainedProcessor(Tracker("a"), Tracker("b"), Tracker("c"))
        record = _make_record()
        result = chain.process(record)
        assert result is record
        assert calls == ["a", "b", "c"]

    def test_drops_record_when_processor_returns_none(self):
        class Dropper(BaseProcessor):
            def process(self, record):
                return None

        class Passthrough(BaseProcessor):
            def process(self, record):
                return record

        chain = ChainedProcessor(Dropper(), Passthrough())
        assert chain.process(_make_record()) is None


# ---------------------------------------------------------------------------
# ExceptionProcessor
# ---------------------------------------------------------------------------

class TestExceptionProcessor:
    def test_no_exc_info_returns_record_unchanged(self):
        proc = ExceptionProcessor()
        record = _make_record(foo="bar")
        assert proc.process(record) is record

    def test_formats_exception_into_field(self):
        proc = ExceptionProcessor(field="exception")
        try:
            raise ValueError("boom")
        except ValueError:
            exc_info = sys.exc_info()

        from nestlog.core import LogRecord, Level
        level = MagicMock()
        record = LogRecord(level=level, message="oops", fields={"exc_info": exc_info})
        result = proc.process(record)
        assert "exc_info" not in result.fields
        assert "ValueError" in result.fields["exception"]
        assert "boom" in result.fields["exception"]


# ---------------------------------------------------------------------------
# FieldRenameProcessor
# ---------------------------------------------------------------------------

class TestFieldRenameProcessor:
    def test_renames_specified_fields(self):
        from nestlog.core import LogRecord
        level = MagicMock()
        record = LogRecord(level=level, message="hi", fields={"lvl": "INFO", "msg": "hi"})
        proc = FieldRenameProcessor({"lvl": "level", "msg": "message"})
        result = proc.process(record)
        assert "level" in result.fields
        assert "message" in result.fields
        assert "lvl" not in result.fields

    def test_no_matching_keys_returns_same_record(self):
        from nestlog.core import LogRecord
        level = MagicMock()
        record = LogRecord(level=level, message="hi", fields={"foo": 1})
        proc = FieldRenameProcessor({"bar": "baz"})
        assert proc.process(record) is record
