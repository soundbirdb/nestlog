"""Log record routing: dispatch records to different sinks based on rules."""

from __future__ import annotations

from typing import Callable, List, Tuple

from nestlog.core import LogRecord
from nestlog.sinks import BaseSink


Rule = Callable[[LogRecord], bool]


class Router:
    """Route log records to one or more sinks based on predicate rules.

    Rules are evaluated in order; the first matching rule wins unless
    *exclusive* is set to False, in which case all matching sinks receive
    the record.
    """

    def __init__(self, exclusive: bool = True) -> None:
        self._exclusive = exclusive
        self._routes: List[Tuple[Rule, BaseSink]] = []
        self._default: BaseSink | None = None

    def add_route(self, rule: Rule, sink: BaseSink) -> "Router":
        """Register *sink* to receive records for which *rule* returns True."""
        self._routes.append((rule, sink))
        return self

    def set_default(self, sink: BaseSink) -> "Router":
        """Sink that receives records not matched by any rule."""
        self._default = sink
        return self

    def emit(self, record: LogRecord) -> None:
        """Dispatch *record* according to registered routes."""
        matched = False
        for rule, sink in self._routes:
            if rule(record):
                sink.emit(record)
                matched = True
                if self._exclusive:
                    return
        if not matched and self._default is not None:
            self._default.emit(record)


def by_level_name(name: str) -> Rule:
    """Return a rule that matches records whose level name equals *name*."""
    name_upper = name.upper()
    return lambda record: str(record.level).upper() == name_upper


def by_field(key: str, value: object) -> Rule:
    """Return a rule that matches records containing *key* == *value*."""
    return lambda record: record.fields.get(key) == value


def by_predicate(fn: Rule) -> Rule:
    """Pass-through helper for explicit typing / documentation clarity."""
    return fn
