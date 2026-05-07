"""Context-local fields that are automatically merged into every LogRecord."""

import threading
from typing import Any, Dict, Iterator

_local = threading.local()


def _get_stack() -> list:
    if not hasattr(_local, "stack"):
        _local.stack = [{}]
    return _local.stack


def bind(**fields: Any) -> None:
    """Merge *fields* into the current context frame."""
    _get_stack()[-1].update(fields)


def unbind(*keys: str) -> None:
    """Remove *keys* from the current context frame."""
    frame = _get_stack()[-1]
    for key in keys:
        frame.pop(key, None)


def clear() -> None:
    """Remove all fields from the current context frame."""
    _get_stack()[-1].clear()


def current_fields() -> Dict[str, Any]:
    """Return a merged snapshot of all stacked context frames."""
    merged: Dict[str, Any] = {}
    for frame in _get_stack():
        merged.update(frame)
    return merged


class bound_context:
    """Context-manager / decorator that pushes a new frame with *fields*
    and pops it on exit, leaving outer frames untouched.

    Usage::

        with bound_context(request_id="abc"):
            logger.info("handling request")
    """

    def __init__(self, **fields: Any) -> None:
        self._fields = fields

    def __enter__(self) -> "bound_context":
        _get_stack().append(dict(self._fields))
        return self

    def __exit__(self, *_: Any) -> None:
        stack = _get_stack()
        if len(stack) > 1:
            stack.pop()

    def __call__(self, func):  # type: ignore[override]
        import functools

        @functools.wraps(func)
        def wrapper(*args, **kwargs):  # type: ignore[misc]
            with bound_context(**self._fields):
                return func(*args, **kwargs)

        return wrapper
