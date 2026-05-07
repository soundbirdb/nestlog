"""Record processors that transform or augment log records before emission."""

from __future__ import annotations

import traceback
from typing import Optional

from nestlog.core import LogRecord


class BaseProcessor:
    """Abstract base class for log record processors."""

    def process(self, record: LogRecord) -> Optional[LogRecord]:
        """Process a record, returning the (possibly modified) record or None to drop it."""
        raise NotImplementedError

    def __add__(self, other: "BaseProcessor") -> "ChainedProcessor":
        return ChainedProcessor(self, other)


class ChainedProcessor(BaseProcessor):
    """Runs multiple processors in sequence; drops the record if any returns None."""

    def __init__(self, *processors: BaseProcessor) -> None:
        self._processors = list(processors)

    def process(self, record: LogRecord) -> Optional[LogRecord]:
        current: Optional[LogRecord] = record
        for processor in self._processors:
            if current is None:
                return None
            current = processor.process(current)
        return current


class ExceptionProcessor(BaseProcessor):
    """Adds formatted exception info to the record's fields when exc_info is present."""

    def __init__(self, field: str = "exception") -> None:
        self._field = field

    def process(self, record: LogRecord) -> Optional[LogRecord]:
        exc_info = record.fields.get("exc_info")
        if exc_info and exc_info is not True:
            try:
                formatted = "".join(traceback.format_exception(*exc_info)).rstrip()
            except Exception:
                formatted = repr(exc_info)
            updated = dict(record.fields)
            updated[self._field] = formatted
            updated.pop("exc_info", None)
            return LogRecord(
                level=record.level,
                message=record.message,
                fields=updated,
                timestamp=record.timestamp,
            )
        return record


class FieldRenameProcessor(BaseProcessor):
    """Renames fields in the record according to a mapping."""

    def __init__(self, mapping: dict) -> None:
        self._mapping = mapping

    def process(self, record: LogRecord) -> Optional[LogRecord]:
        if not any(k in record.fields for k in self._mapping):
            return record
        updated = {self._mapping.get(k, k): v for k, v in record.fields.items()}
        return LogRecord(
            level=record.level,
            message=record.message,
            fields=updated,
            timestamp=record.timestamp,
        )
