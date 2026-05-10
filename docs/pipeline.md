# Pipeline

A `Pipeline` composes an ordered list of **processors** with a **sink** into a
single, reusable unit.  Records flow through every processor in order; if any
processor returns `None` the record is silently dropped and the sink is never
called.

## Basic usage

```python
import sys
from nestlog.pipeline import Pipeline
from nestlog.sinks import StreamSink
from nestlog.redactors import RedactKeysProcessor
from nestlog.throttle import ThrottleProcessor

pipeline = Pipeline(
    sink=StreamSink(sys.stdout),
    processors=[
        RedactKeysProcessor(["password", "token"]),
        ThrottleProcessor(max_per_second=100),
    ],
)

pipeline.emit(record)
```

## Constructor

```python
Pipeline(sink: BaseSink, processors: Iterable[BaseProcessor] | None = None)
```

| Parameter    | Type                          | Description                                      |
|--------------|-------------------------------|--------------------------------------------------|
| `sink`       | `BaseSink`                    | Destination that receives fully processed records |
| `processors` | `Iterable[BaseProcessor]`     | Optional ordered list of processors              |

## Methods

### `emit(record)`

Run *record* through every processor in order.  The first processor that
returns `None` stops the chain and the sink is **not** called.

### `add_processor(processor) -> Pipeline`

Append a processor at the end of the chain.  Returns `self` so calls can be
chained:

```python
pipeline.add_processor(RedactKeysProcessor(["ssn"])).add_processor(ThrottleProcessor(50))
```

### `flush()`

Forwards to `sink.flush()` if the sink exposes that method.  Safe to call even
if the sink does not implement `flush`.

### `close()`

Forwards to `sink.close()` if the sink exposes that method.  Call this during
application shutdown to release file handles or network connections.

## Integrating with the Logger

```python
from nestlog.core import Logger
from nestlog.pipeline import Pipeline
from nestlog.sinks import StreamSink
import sys

pipeline = Pipeline(sink=StreamSink(sys.stdout))
logger = Logger(sink=pipeline)  # Pipeline satisfies the sink protocol
logger.info("application started")
```

Because `Pipeline` exposes an `emit` method with the same signature as
`BaseSink.emit`, it can be used anywhere a sink is expected.
