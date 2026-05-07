"""nestlog — Lightweight structured logging with pluggable sinks."""

from nestlog.core import Level, Logger, LogRecord
from nestlog.sinks import BaseSink, StreamSink
from nestlog.formatters import BaseFormatter, TextFormatter, JsonFormatter
from nestlog.filters import BaseFilter, LevelFilter
from nestlog.handlers import AsyncHandler, BatchHandler

__all__ = [
    # core
    "Level",
    "Logger",
    "LogRecord",
    # sinks
    "BaseSink",
    "StreamSink",
    # formatters
    "BaseFormatter",
    "TextFormatter",
    "JsonFormatter",
    # filters
    "BaseFilter",
    "LevelFilter",
    # handlers
    "AsyncHandler",
    "BatchHandler",
]
