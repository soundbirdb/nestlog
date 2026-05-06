"""Built-in sinks for nestlog."""

from __future__ import annotations

import sys
from typing import IO, Optional

from nestlog.core import LogRecord
from nestlog.filters import BaseFilter


class BaseSink:
    """Abstract base sink. All sinks must implement :meth:`emit`."""

    def __init__(self, filter: Optional[BaseFilter] = None) -> None:
        self._filter: Optional[BaseFilter] = filter

    def set_filter(self, filter: BaseFilter) -> None:
        """Attach a filter to this sink."""
        self._filter = filter

    def _should_emit(self, record: LogRecord) -> bool:
        if self._filter is None:
            return True
        return self._filter.allow(record)

    def emit(self, record: LogRecord) -> None:  # noqa: D102
        raise NotImplementedError

    def close(self) -> None:
        """Release any resources held by the sink."""


class StreamSink(BaseSink):
    """Write formatted log records to a text stream."""

    DEFAULT_FMT = "{level} [{name}] {message}"

    def __init__(
        self,
        stream: IO[str] = sys.stderr,
        fmt: str = DEFAULT_FMT,
        filter: Optional[BaseFilter] = None,
    ) -> None:
        super().__init__(filter=filter)
        self._stream = stream
        self._fmt = fmt

    def emit(self, record: LogRecord) -> None:
        if not self._should_emit(record):
            return
        line = self._fmt.format(
            level=record.level,
            name=record.name,
            message=str(record),
        )
        self._stream.write(line + "\n")
        self._stream.flush()

    def close(self) -> None:
        if self._stream not in (sys.stdout, sys.stderr):
            self._stream.close()


class FileSink(StreamSink):
    """Convenience sink that opens *path* for appending."""

    def __init__(
        self,
        path: str,
        fmt: str = StreamSink.DEFAULT_FMT,
        encoding: str = "utf-8",
        filter: Optional[BaseFilter] = None,
    ) -> None:
        self._path = path
        stream = open(path, "a", encoding=encoding)  # noqa: WPS515
        super().__init__(stream=stream, fmt=fmt, filter=filter)

    def close(self) -> None:
        self._stream.close()


class NullSink(BaseSink):
    """Silently discard every record (useful for testing)."""

    def emit(self, record: LogRecord) -> None:
        pass
