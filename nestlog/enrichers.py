"""Enrichers automatically attach extra fields to log records before emission."""

import os
import socket
import threading
from typing import Any, Callable, Dict


class BaseEnricher:
    """Base class for all enrichers."""

    def enrich(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Return a (possibly modified) copy of *fields* with extra data added."""
        raise NotImplementedError

    def __add__(self, other: "BaseEnricher") -> "ChainedEnricher":
        return ChainedEnricher(self, other)


class ChainedEnricher(BaseEnricher):
    """Applies two enrichers in sequence."""

    def __init__(self, first: BaseEnricher, second: BaseEnricher) -> None:
        self._first = first
        self._second = second

    def enrich(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        return self._second.enrich(self._first.enrich(fields))


class StaticEnricher(BaseEnricher):
    """Attaches a fixed set of key/value pairs to every record."""

    def __init__(self, **kwargs: Any) -> None:
        self._extra = kwargs

    def enrich(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        merged = dict(self._extra)
        merged.update(fields)  # record-level fields win
        return merged


class HostnameEnricher(BaseEnricher):
    """Attaches the current machine hostname under the key ``hostname``."""

    def __init__(self) -> None:
        self._hostname = socket.gethostname()

    def enrich(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        out = dict(fields)
        out.setdefault("hostname", self._hostname)
        return out


class ProcessEnricher(BaseEnricher):
    """Attaches ``pid`` and ``thread_id`` to every record."""

    def enrich(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        out = dict(fields)
        out.setdefault("pid", os.getpid())
        out.setdefault("thread_id", threading.get_ident())
        return out


class CallableEnricher(BaseEnricher):
    """Delegates enrichment to an arbitrary callable.

    The callable receives the current *fields* dict and must return a dict.
    """

    def __init__(self, fn: Callable[[Dict[str, Any]], Dict[str, Any]]) -> None:
        self._fn = fn

    def enrich(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        return self._fn(dict(fields))
