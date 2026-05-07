"""Built-in enrichers for nestlog.

Enrichers add or merge extra fields into a LogRecord before it reaches
a sink.  Chain multiple enrichers with the ``+`` operator.
"""

from __future__ import annotations

from typing import Any, Dict

from .core import LogRecord
from . import context as _ctx


class BaseEnricher:
    """Abstract base class for enrichers."""

    def enrich(self, record: LogRecord) -> LogRecord:
        raise NotImplementedError

    def __add__(self, other: "BaseEnricher") -> "ChainedEnricher":
        return ChainedEnricher(self, other)


class ChainedEnricher(BaseEnricher):
    """Applies two enrichers in sequence."""

    def __init__(self, first: BaseEnricher, second: BaseEnricher) -> None:
        self._first = first
        self._second = second

    def enrich(self, record: LogRecord) -> LogRecord:
        return self._second.enrich(self._first.enrich(record))


class StaticEnricher(BaseEnricher):
    """Merges a fixed set of fields into every record.

    Fields already present on the record take precedence.
    """

    def __init__(self, **fields: Any) -> None:
        self._fields: Dict[str, Any] = fields

    def enrich(self, record: LogRecord) -> LogRecord:
        merged = {**self._fields, **record.fields}
        return LogRecord(
            level=record.level,
            message=record.message,
            fields=merged,
        )


class ContextEnricher(BaseEnricher):
    """Merges the current thread-local context into every record.

    Fields already present on the record take precedence over context
    fields, which in turn take precedence over nothing.

    Example::

        from nestlog.context import bind
        from nestlog.enrichers import ContextEnricher

        logger.add_enricher(ContextEnricher())
        with bind(user_id=42):
            logger.info("hello")  # record will contain user_id=42
    """

    def enrich(self, record: LogRecord) -> LogRecord:
        ctx = _ctx.current_fields()
        if not ctx:
            return record
        merged = {**ctx, **record.fields}
        return LogRecord(
            level=record.level,
            message=record.message,
            fields=merged,
        )


class CallableEnricher(BaseEnricher):
    """Wraps an arbitrary callable as an enricher.

    The callable receives the current :class:`LogRecord` and must return
    a (possibly new) :class:`LogRecord`.
    """

    def __init__(self, fn) -> None:
        self._fn = fn

    def enrich(self, record: LogRecord) -> LogRecord:
        return self._fn(record)
