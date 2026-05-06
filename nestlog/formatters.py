"""Formatters for converting LogRecords to strings."""

import json
from datetime import datetime, timezone


class BaseFormatter:
    """Base class for all formatters."""

    def format(self, record) -> str:
        raise NotImplementedError


class TextFormatter(BaseFormatter):
    """Formats a LogRecord as a human-readable text line.

    Default pattern: ``[LEVEL] timestamp logger_name: message``
    """

    DEFAULT_PATTERN = "[{level}] {timestamp} {name}: {message}"

    def __init__(self, pattern: str = DEFAULT_PATTERN, time_fmt: str = "%Y-%m-%dT%H:%M:%S"):
        self._pattern = pattern
        self._time_fmt = time_fmt

    def format(self, record) -> str:
        timestamp = datetime.fromtimestamp(record.created, tz=timezone.utc).strftime(self._time_fmt)
        return self._pattern.format(
            level=str(record.level),
            timestamp=timestamp,
            name=record.name,
            message=record.message,
        )


class JSONFormatter(BaseFormatter):
    """Formats a LogRecord as a single-line JSON object.

    Extra fields stored on the record are included automatically.
    """

    def __init__(self, extra_fields: list[str] | None = None):
        """Args:
            extra_fields: additional attribute names to pull from the record.
        """
        self._extra_fields = extra_fields or []

    def format(self, record) -> str:
        payload: dict = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": str(record.level),
            "name": record.name,
            "message": record.message,
        }
        for field in self._extra_fields:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value
        return json.dumps(payload, default=str)
