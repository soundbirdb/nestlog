# Buffering Processor

The `BufferingProcessor` accumulates log records in memory and releases them in
batches.  This is useful when you want to:

- Reduce I/O pressure by writing to a sink in bulk.
- Collect records during a request and forward them only on error.
- Implement a "tail-on-failure" pattern.

## Basic usage

```python
from nestlog.buffering import BufferingProcessor
from nestlog.sinks import StreamSink

sink = StreamSink()  # or any other sink

def flush_to_sink(records):
    for record in records:
        sink.emit(record)

bp = BufferingProcessor(capacity=50, flush_fn=flush_to_sink)
```

Attach it to your logger pipeline like any other processor:

```python
logger = Logger(processor=bp)
```

## Parameters

| Parameter    | Type       | Default | Description                                         |
|------------- |------------|---------|-----------------------------------------------------|
| `capacity`   | `int`      | `100`   | Max records before auto-flush is triggered.         |
| `flush_fn`   | `Callable` | no-op   | Called with the list of records when flushing.      |
| `auto_flush` | `bool`     | `True`  | Flush automatically when `capacity` is reached.     |

## Manual flushing

Call `flush()` at any point to drain the buffer regardless of capacity:

```python
try:
    handle_request()
except Exception:
    bp.flush()   # emit everything collected so far
    raise
```

## Inspecting the buffer

```python
print(f"{len(bp.buffered)} records waiting")
```

`buffered` returns a **copy** of the internal list, so iterating over it is
safe even if records continue to arrive concurrently.

## Tail-on-failure pattern

```python
bp = BufferingProcessor(capacity=200, auto_flush=False)

try:
    process_job()
except Exception:
    bp.flush()   # only emit logs when something goes wrong
```
