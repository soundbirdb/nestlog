"""Pipeline: chain processors and a sink into a single callable unit."""

from __future__ import annotations

from typing import Iterable, Optional

from nestlog.processors import BaseProcessor
from nestlog.sinks import BaseSink
from nestlog.core import LogRecord


class Pipeline:
    """Applies a sequence of processors to a record then forwards it to a sink.

    Processors are applied in order.  If any processor returns ``None`` the
    record is dropped and the sink is never called.

    Example::

        pipeline = Pipeline(
            processors=[RedactKeysProcessor(["password"]), ThrottleProcessor(10)],
            sink=StreamSink(sys.stdout),
        )
        pipeline.emit(record)
    """

    def __init__(
        self,
        sink: BaseSink,
        processors: Optional[Iterable[BaseProcessor]] = None,
    ) -> None:
        self._sink = sink
        self._processors: list[BaseProcessor] = list(processors or [])

    # ------------------------------------------------------------------
    # Mutation helpers
    # ------------------------------------------------------------------

    def add_processor(self, processor: BaseProcessor) -> "Pipeline":
        """Append *processor* and return *self* for chaining."""
        self._processors.append(processor)
        return self

    # ------------------------------------------------------------------
    # Core
    # ------------------------------------------------------------------

    def emit(self, record: LogRecord) -> None:
        """Run the record through all processors then emit to the sink."""
        current: Optional[LogRecord] = record
        for processor in self._processors:
            current = processor.process(current)  # type: ignore[arg-type]
            if current is None:
                return
        self._sink.emit(current)  # type: ignore[arg-type]

    def flush(self) -> None:
        """Flush the underlying sink if it supports it."""
        flush = getattr(self._sink, "flush", None)
        if callable(flush):
            flush()

    def close(self) -> None:
        """Close the underlying sink if it supports it."""
        close = getattr(self._sink, "close", None)
        if callable(close):
            close()
