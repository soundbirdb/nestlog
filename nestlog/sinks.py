"""Built-in sink implementations for nestlog."""

import sys
import json
import datetime
from typing import TextIO


class BaseSink:
    """Abstract base class for all sinks."""

    def emit(self, record) -> None:
        raise NotImplementedError

    def close(self) -> None:
        pass


class StreamSink(BaseSink):
    """Writes formatted log records to a text stream (stdout/stderr/file)."""

    DEFAULT_FORMAT = "{time} [{level}] {name}: {message}"

    def __init__(self, stream: TextIO = None, fmt: str = None):
        self.stream = stream or sys.stderr
        self.fmt = fmt or self.DEFAULT_FORMAT

    def emit(self, record) -> None:
        time_str = datetime.datetime.fromtimestamp(
            record.timestamp, tz=datetime.timezone.utc
        ).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        line = self.fmt.format(
            time=time_str,
            level=str(record.level),
            name=record.name,
            message=record.message,
        )
        if record.extra:
            extras = " ".join(f"{k}={v!r}" for k, v in record.extra.items())
            line = f"{line} | {extras}"
        self.stream.write(line + "\n")
        self.stream.flush()


class JSONSink(BaseSink):
    """Writes log records as newline-delimited JSON to a stream."""

    def __init__(self, stream: TextIO = None):
        self.stream = stream or sys.stdout

    def emit(self, record) -> None:
        payload = {
            "timestamp": record.timestamp,
            "level": str(record.level),
            "name": record.name,
            "message": record.message,
        }
        if record.extra:
            payload.update(record.extra)
        self.stream.write(json.dumps(payload) + "\n")
        self.stream.flush()


class FileSink(StreamSink):
    """Writes formatted log records to a file, opening it on first emit."""

    def __init__(self, path: str, fmt: str = None, mode: str = "a", encoding: str = "utf-8"):
        self.path = path
        self.mode = mode
        self.encoding = encoding
        self._file: TextIO | None = None
        super().__init__(stream=None, fmt=fmt)

    def _ensure_open(self) -> None:
        if self._file is None:
            self._file = open(self.path, self.mode, encoding=self.encoding)
            self.stream = self._file

    def emit(self, record) -> None:
        self._ensure_open()
        super().emit(record)

    def close(self) -> None:
        if self._file is not None:
            self._file.close()
            self._file = None
