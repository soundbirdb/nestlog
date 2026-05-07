"""Field redaction support for nestlog.

Provides processors that scrub or mask sensitive fields from log records
before they reach any sink.
"""

from __future__ import annotations

import re
from typing import Collection, Pattern, Union

from nestlog.processors import BaseProcessor
from nestlog.core import LogRecord

_MASK = "***"


class RedactKeysProcessor(BaseProcessor):
    """Replace the values of specific field keys with a mask string.

    Parameters
    ----------
    keys:
        An iterable of field names whose values should be redacted.
    mask:
        Replacement string.  Defaults to ``'***'``.
    """

    def __init__(self, keys: Collection[str], mask: str = _MASK) -> None:
        self._keys = frozenset(keys)
        self._mask = mask

    def process(self, record: LogRecord) -> LogRecord:
        if not self._keys:
            return record
        new_fields = {
            k: (self._mask if k in self._keys else v)
            for k, v in record.fields.items()
        }
        return LogRecord(
            level=record.level,
            message=record.message,
            fields=new_fields,
            timestamp=record.timestamp,
        )


class RedactPatternsProcessor(BaseProcessor):
    """Mask substrings in *string* field values that match a regex pattern.

    Parameters
    ----------
    pattern:
        A compiled ``re.Pattern`` or a pattern string.  Every non-overlapping
        match inside string field values is replaced with *mask*.
    mask:
        Replacement string.  Defaults to ``'***'``.
    """

    def __init__(
        self,
        pattern: Union[str, Pattern[str]],
        mask: str = _MASK,
    ) -> None:
        self._pattern: Pattern[str] = (
            re.compile(pattern) if isinstance(pattern, str) else pattern
        )
        self._mask = mask

    def process(self, record: LogRecord) -> LogRecord:
        new_fields = {
            k: self._pattern.sub(self._mask, v) if isinstance(v, str) else v
            for k, v in record.fields.items()
        }
        return LogRecord(
            level=record.level,
            message=record.message,
            fields=new_fields,
            timestamp=record.timestamp,
        )
