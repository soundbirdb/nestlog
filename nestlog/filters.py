"""Log record filters for nestlog."""

from __future__ import annotations

from typing import Callable, Optional

from nestlog.core import Level, LogRecord


class BaseFilter:
    """Base class for all filters. Subclass and override :meth:`allow`."""

    def allow(self, record: LogRecord) -> bool:  # noqa: D102
        raise NotImplementedError

    def __and__(self, other: "BaseFilter") -> "CompositeFilter":
        return CompositeFilter([self, other], mode="all")

    def __or__(self, other: "BaseFilter") -> "CompositeFilter":
        return CompositeFilter([self, other], mode="any")


class LevelFilter(BaseFilter):
    """Allow records at or above *min_level* and at or below *max_level*."""

    def __init__(
        self,
        min_level: Level = Level.DEBUG,
        max_level: Level = Level.CRITICAL,
    ) -> None:
        self.min_level = min_level
        self.max_level = max_level

    def allow(self, record: LogRecord) -> bool:
        return self.min_level <= record.level <= self.max_level


class NameFilter(BaseFilter):
    """Allow records whose logger name starts with *prefix*."""

    def __init__(self, prefix: str) -> None:
        self.prefix = prefix

    def allow(self, record: LogRecord) -> bool:
        return record.name.startswith(self.prefix)


class CallableFilter(BaseFilter):
    """Wrap an arbitrary callable as a filter."""

    def __init__(self, fn: Callable[[LogRecord], bool]) -> None:
        self._fn = fn

    def allow(self, record: LogRecord) -> bool:
        return bool(self._fn(record))


class CompositeFilter(BaseFilter):
    """Combine multiple filters with *mode* ``'all'`` (AND) or ``'any'`` (OR)."""

    def __init__(
        self,
        filters: list[BaseFilter],
        mode: str = "all",
    ) -> None:
        if mode not in ("all", "any"):
            raise ValueError("mode must be 'all' or 'any'")
        self._filters = list(filters)
        self._mode = mode

    def allow(self, record: LogRecord) -> bool:
        if self._mode == "all":
            return all(f.allow(record) for f in self._filters)
        return any(f.allow(record) for f in self._filters)
