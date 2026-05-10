"""nestlog — Lightweight structured logging library for Python."""

from nestlog.core import Level, LogRecord, Logger
from nestlog.sinks import BaseSink, StreamSink, NullSink
from nestlog.formatters import BaseFormatter, TextFormatter, JSONFormatter
from nestlog.filters import BaseFilter, LevelFilter
from nestlog.enrichers import BaseEnricher, StaticEnricher, ChainedEnricher
from nestlog.processors import BaseProcessor, ChainedProcessor
from nestlog.handlers import AsyncHandler
from nestlog.samplers import SamplingFilter, RateLimitFilter
from nestlog.context import bind, unbind, clear, current_fields
from nestlog.routing import Router
from nestlog.redactors import RedactKeysProcessor, RedactPatternsProcessor
from nestlog.serializers import JSONSerializer
from nestlog.throttle import ThrottleProcessor
from nestlog.deduplicator import DeduplicatorProcessor
from nestlog.buffering import BufferingProcessor
from nestlog.pipeline import Pipeline

__all__ = [
    # core
    "Level", "LogRecord", "Logger",
    # sinks
    "BaseSink", "StreamSink", "NullSink",
    # formatters
    "BaseFormatter", "TextFormatter", "JSONFormatter",
    # filters
    "BaseFilter", "LevelFilter",
    # enrichers
    "BaseEnricher", "StaticEnricher", "ChainedEnricher",
    # processors
    "BaseProcessor", "ChainedProcessor",
    # handlers
    "AsyncHandler",
    # samplers
    "SamplingFilter", "RateLimitFilter",
    # context
    "bind", "unbind", "clear", "current_fields",
    # routing
    "Router",
    # redactors
    "RedactKeysProcessor", "RedactPatternsProcessor",
    # serializers
    "JSONSerializer",
    # throttle / dedup / buffering
    "ThrottleProcessor", "DeduplicatorProcessor", "BufferingProcessor",
    # pipeline
    "Pipeline",
]
