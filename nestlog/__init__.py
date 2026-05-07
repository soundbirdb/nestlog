"""nestlog — Lightweight structured logging with pluggable sinks."""

from nestlog.core import Level, Logger, LogRecord
from nestlog.sinks import BaseSink, StreamSink
from nestlog.filters import BaseFilter, LevelFilter
from nestlog.formatters import BaseFormatter, JSONFormatter, TextFormatter
from nestlog.enrichers import BaseEnricher, StaticEnricher
from nestlog.processors import BaseProcessor
from nestlog.samplers import RateLimitFilter, SamplingFilter
from nestlog.redactors import RedactKeysProcessor, RedactPatternsProcessor
from nestlog.serializers import JSONSerializer
from nestlog.routing import Router, by_field, by_level_name, by_predicate

__all__ = [
    "Level",
    "Logger",
    "LogRecord",
    "BaseSink",
    "StreamSink",
    "BaseFilter",
    "LevelFilter",
    "BaseFormatter",
    "JSONFormatter",
    "TextFormatter",
    "BaseEnricher",
    "StaticEnricher",
    "BaseProcessor",
    "SamplingFilter",
    "RateLimitFilter",
    "RedactKeysProcessor",
    "RedactPatternsProcessor",
    "JSONSerializer",
    "Router",
    "by_field",
    "by_level_name",
    "by_predicate",
]
