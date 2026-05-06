"""Core logging primitives for nestlog.

Provides the Logger class, log levels, and the LogRecord dataclass
that flows through the sink pipeline.
"""

from __future__ import annotations

import time
import traceback
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Dict, List, Optional


class Level(IntEnum):
    """Numeric log levels, compatible with the stdlib logging module."""

    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50

    def __str__(self) -> str:  # noqa: D105
        return self.name


@dataclass
class LogRecord:
    """Immutable snapshot of a single log event."""

    level: Level
    message: str
    logger_name: str
    timestamp: float = field(default_factory=time.time)
    context: Dict[str, Any] = field(default_factory=dict)
    exc_info: Optional[str] = None  # pre-formatted traceback string


class Logger:
    """Structured logger that dispatches LogRecords to registered sinks.

    Example::

        from nestlog import Logger, Level
        from nestlog.sinks import ConsoleSink

        log = Logger("myapp", sinks=[ConsoleSink()])
        log.info("server started", port=8080)
    """

    def __init__(
        self,
        name: str,
        level: Level = Level.DEBUG,
        sinks: Optional[List[Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.name = name
        self.level = level
        self._sinks: List[Any] = list(sinks or [])
        self._context: Dict[str, Any] = dict(context or {})

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def bind(self, **kwargs: Any) -> "Logger":
        """Return a child logger with additional context fields merged in."""
        merged = {**self._context, **kwargs}
        child = Logger(
            name=self.name,
            level=self.level,
            sinks=self._sinks,
            context=merged,
        )
        return child

    def add_sink(self, sink: Any) -> None:
        """Register a new sink at runtime."""
        self._sinks.append(sink)

    def debug(self, message: str, **kwargs: Any) -> None:
        self._log(Level.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        self._log(Level.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        self._log(Level.WARNING, message, **kwargs)

    def error(self, message: str, exc: Optional[BaseException] = None, **kwargs: Any) -> None:
        exc_info: Optional[str] = None
        if exc is not None:
            exc_info = "".join(
                traceback.format_exception(type(exc), exc, exc.__traceback__)
            )
        self._log(Level.ERROR, message, exc_info=exc_info, **kwargs)

    def critical(self, message: str, **kwargs: Any) -> None:
        self._log(Level.CRITICAL, message, **kwargs)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _log(
        self,
        level: Level,
        message: str,
        exc_info: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        if level < self.level:
            return

        record = LogRecord(
            level=level,
            message=message,
            logger_name=self.name,
            context={**self._context, **kwargs},
            exc_info=exc_info,
        )

        for sink in self._sinks:
            try:
                sink.emit(record)
            except Exception:  # noqa: BLE001 — sinks must not crash the app
                pass
