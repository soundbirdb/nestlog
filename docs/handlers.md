# Handlers

Handlers wrap a [`BaseSink`](../nestlog/sinks.py) and add delivery semantics
on top of it — buffering, batching, or asynchronous dispatch.

---

## AsyncHandler

Emits records in a dedicated background daemon thread so that the calling
thread is never blocked by I/O.

```python
from nestlog.sinks import StreamSink
from nestlog.handlers import AsyncHandler

sink = StreamSink()
handler = AsyncHandler(sink, maxsize=500)

handler.emit(record)   # returns immediately
handler.flush()        # block until the queue drains
handler.close()        # flush + stop the worker thread
```

### Constructor

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `sink` | `BaseSink` | — | Sink that receives the records. |
| `maxsize` | `int` | `1000` | Max queue depth. Records are **silently dropped** when the queue is full. |

### Methods

- **`emit(record)`** — Enqueue a record. Non-blocking; drops the record if the
  queue is at capacity.
- **`flush()`** — Block the calling thread until every queued record has been
  delivered to the sink.
- **`close()`** — Send a sentinel to the worker, then join the thread. Always
  call this during application shutdown.

---

## BatchHandler

Accumulates records in an in-memory buffer and forwards them to the sink
together once the configured `batch_size` is reached.

```python
from nestlog.sinks import StreamSink
from nestlog.handlers import BatchHandler

sink = StreamSink()
handler = BatchHandler(sink, batch_size=100)

for record in records:
    handler.emit(record)

handler.close()   # flush any remaining records
```

### Constructor

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `sink` | `BaseSink` | — | Sink that receives the records. |
| `batch_size` | `int` | `50` | Number of records to accumulate before an automatic flush. Must be ≥ 1. |

### Methods

- **`emit(record)`** — Buffer the record. Triggers an automatic flush when the
  buffer reaches `batch_size`.
- **`flush()`** — Immediately deliver all buffered records to the sink and
  clear the buffer.
- **`close()`** — Alias for `flush()`. Call during application shutdown to
  ensure no records are lost.

### Thread safety

`BatchHandler` uses an internal `threading.Lock`, so it is safe to call
`emit` and `flush` from multiple threads concurrently.
