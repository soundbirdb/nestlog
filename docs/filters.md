# Filters

Filters let you control which `LogRecord`s a sink actually processes.
Every `BaseSink` accepts an optional `filter` argument and exposes
`set_filter()` to attach one later.

## Built-in filters

### `LevelFilter`

Allow records whose level falls within `[min_level, max_level]`.

```python
from nestlog.filters import LevelFilter
from nestlog.core import Level
from nestlog.sinks import StreamSink

# Only emit WARNING and above
sink = StreamSink(filter=LevelFilter(min_level=Level.WARNING))
```

### `NameFilter`

Allow records whose logger name starts with a given prefix.

```python
from nestlog.filters import NameFilter

sink = StreamSink(filter=NameFilter("myapp"))
```

### `CallableFilter`

Wrap any callable that accepts a `LogRecord` and returns `bool`.

```python
from nestlog.filters import CallableFilter

sink = StreamSink(filter=CallableFilter(lambda r: "secret" not in r.message))
```

## Composing filters

Filters support `&` (AND) and `|` (OR) operators:

```python
from nestlog.filters import LevelFilter, NameFilter
from nestlog.core import Level

f = LevelFilter(min_level=Level.INFO) & NameFilter("myapp")
sink = StreamSink(filter=f)
```

You can also build a `CompositeFilter` directly:

```python
from nestlog.filters import CompositeFilter, LevelFilter, NameFilter
from nestlog.core import Level

f = CompositeFilter(
    [LevelFilter(min_level=Level.DEBUG), NameFilter("worker")],
    mode="any",   # OR semantics
)
```

## Writing a custom filter

Subclass `BaseFilter` and implement `allow`:

```python
from nestlog.filters import BaseFilter
from nestlog.core import LogRecord

class SamplingFilter(BaseFilter):
    """Let through every *n*-th record."""

    def __init__(self, n: int) -> None:
        self._n = n
        self._count = 0

    def allow(self, record: LogRecord) -> bool:
        self._count += 1
        return self._count % self._n == 0
```
