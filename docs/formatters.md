# Formatters

Formatters control how a `LogRecord` is serialised into a string before a sink
writes it to its destination.

## BaseFormatter

All formatters inherit from `nestlog.formatters.BaseFormatter` and must
implement a single method:

```python
def format(self, record) -> str:
    ...
```

## TextFormatter

Produces a human-readable single-line string.

```python
from nestlog.formatters import TextFormatter

# Default: "[INFO] 2024-01-15T12:00:00 myapp: user logged in"
fmt = TextFormatter()

# Custom pattern — supports: {level}, {timestamp}, {name}, {message}
fmt = TextFormatter(
    pattern="{timestamp} | {level:8s} | {name} — {message}",
    time_fmt="%Y-%m-%d %H:%M:%S",
)
```

### Constructor parameters

| Parameter  | Type  | Default                                         | Description                      |
|------------|-------|-------------------------------------------------|----------------------------------|
| `pattern`  | `str` | `"[{level}] {timestamp} {name}: {message}"`     | Python format string             |
| `time_fmt` | `str` | `"%Y-%m-%dT%H:%M:%S"`                           | `strftime` format for timestamps |

## JSONFormatter

Produces a single-line JSON object — ideal for structured log pipelines
(Elasticsearch, Loki, Datadog …).

```python
from nestlog.formatters import JSONFormatter

# Basic usage
fmt = JSONFormatter()
# → {"timestamp": "2024-01-15T12:00:00+00:00", "level": "INFO", "name": "myapp", "message": "ok"}

# Include extra attributes stored on the record
fmt = JSONFormatter(extra_fields=["request_id", "user_id"])
```

### Constructor parameters

| Parameter      | Type            | Default | Description                                                     |
|----------------|-----------------|---------|-----------------------------------------------------------------|
| `extra_fields` | `list[str]`     | `[]`    | Record attribute names to include; silently skipped if absent. |

## Attaching a formatter to a sink

Pass the formatter when constructing a sink, or set it afterwards:

```python
from nestlog.sinks import StreamSink
from nestlog.formatters import JSONFormatter

sink = StreamSink(formatter=JSONFormatter(extra_fields=["trace_id"]))
```

> **Note:** if no formatter is provided, sinks fall back to calling `str(record)`.
