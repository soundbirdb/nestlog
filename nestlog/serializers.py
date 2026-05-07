"""JSON and text serialization helpers for LogRecord instances."""

import json
import datetime
from typing import Any, Dict


def _default_encoder(obj: Any) -> Any:
    """Fallback encoder for types not natively handled by json.dumps."""
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    if isinstance(obj, datetime.date):
        return obj.isoformat()
    if isinstance(obj, (set, frozenset)):
        return list(obj)
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    return str(obj)


class JSONSerializer:
    """Serialize a LogRecord to a JSON string.

    Parameters
    ----------
    indent:
        Optional indentation level passed to ``json.dumps``.  Defaults to
        ``None`` (compact, single-line output).
    sort_keys:
        Whether to sort the keys in the output object.  Defaults to ``False``.
    ensure_ascii:
        Passed directly to ``json.dumps``.  Defaults to ``False`` so that
        Unicode characters are preserved as-is.
    """

    def __init__(
        self,
        indent: int | None = None,
        sort_keys: bool = False,
        ensure_ascii: bool = False,
    ) -> None:
        self.indent = indent
        self.sort_keys = sort_keys
        self.ensure_ascii = ensure_ascii

    def serialize(self, record: Any) -> str:
        """Return a JSON string representation of *record*."""
        payload = self._record_to_dict(record)
        return json.dumps(
            payload,
            default=_default_encoder,
            indent=self.indent,
            sort_keys=self.sort_keys,
            ensure_ascii=self.ensure_ascii,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _record_to_dict(self, record: Any) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "level": str(record.level),
            "message": str(record),
        }
        if hasattr(record, "timestamp") and record.timestamp is not None:
            payload["timestamp"] = _default_encoder(record.timestamp)
        if hasattr(record, "fields") and record.fields:
            payload.update(record.fields)
        return payload


class LineSerializer:
    """Serialize a LogRecord to a plain key=value line (logfmt-style).

    The ``level`` and ``message`` keys are always emitted first.
    """

    def serialize(self, record: Any) -> str:
        parts = [
            f"level={str(record.level)}",
            f"msg={self._quote(str(record))}",
        ]
        if hasattr(record, "timestamp") and record.timestamp is not None:
            parts.append(f"ts={_default_encoder(record.timestamp)}")
        if hasattr(record, "fields") and record.fields:
            for key, value in record.fields.items():
                parts.append(f"{key}={self._quote(str(value))}")
        return " ".join(parts)

    @staticmethod
    def _quote(value: str) -> str:
        if " " in value or "=" in value or '"' in value:
            escaped = value.replace('"', '\\"')
            return f'"{escaped}"'
        return value
