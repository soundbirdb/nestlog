"""Sampling filters for nestlog — rate-limit log records probabilistically."""

import random
import threading
from nestlog.filters import BaseFilter


class SamplingFilter(BaseFilter):
    """Allow only a random fraction of log records through.

    Parameters
    ----------
    rate:
        A float in [0.0, 1.0].  ``1.0`` means every record is allowed;
        ``0.0`` means no records pass.
    """

    def __init__(self, rate: float = 1.0) -> None:
        if not 0.0 <= rate <= 1.0:
            raise ValueError(f"rate must be between 0.0 and 1.0, got {rate!r}")
        self._rate = rate

    @property
    def rate(self) -> float:
        return self._rate

    def allow(self, record) -> bool:  # noqa: ANN001
        return random.random() < self._rate


class RateLimitFilter(BaseFilter):
    """Allow at most *max_per_second* records per second (token-bucket style).

    Parameters
    ----------
    max_per_second:
        Maximum number of records allowed in any one-second window.
    """

    def __init__(self, max_per_second: int) -> None:
        if max_per_second <= 0:
            raise ValueError("max_per_second must be a positive integer")
        self._max = max_per_second
        self._lock = threading.Lock()
        self._window_start: float = 0.0
        self._count: int = 0

    def allow(self, record) -> bool:  # noqa: ANN001
        import time

        now = time.monotonic()
        with self._lock:
            if now - self._window_start >= 1.0:
                self._window_start = now
                self._count = 0
            if self._count < self._max:
                self._count += 1
                return True
            return False
