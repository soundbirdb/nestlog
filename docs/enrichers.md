# Enrichers

Enrichers automatically attach extra fields to every log record before it
reaches a sink. They are composable and have zero side-effects on the original
field dict.

## Built-in enrichers

### `StaticEnricher(**kwargs)`

Attaches a fixed set of key/value pairs. Record-level fields always take
precedence over static values.

```python
from nestlog.enrichers import StaticEnricher

enricher = StaticEnricher(env="production", region="eu-west-1")
fields = enricher.enrich({"message": "started"})
# {'env': 'production', 'region': 'eu-west-1', 'message': 'started'}
```

### `HostnameEnricher()`

Attaches the machine hostname under the key `hostname`.

```python
from nestlog.enrichers import HostnameEnricher

enricher = HostnameEnricher()
fields = enricher.enrich({})
# {'hostname': 'my-server.local'}
```

### `ProcessEnricher()`

Attaches the current process ID (`pid`) and thread identifier (`thread_id`).

```python
from nestlog.enrichers import ProcessEnricher

enricher = ProcessEnricher()
fields = enricher.enrich({})
# {'pid': 12345, 'thread_id': 140234567890}
```

### `CallableEnricher(fn)`

Delegates enrichment to any callable that accepts and returns a `dict`.

```python
import time
from nestlog.enrichers import CallableEnricher

enricher = CallableEnricher(lambda f: {**f, "ts": time.time()})
```

## Chaining enrichers

Enrichers support the `+` operator to build a pipeline:

```python
from nestlog.enrichers import HostnameEnricher, ProcessEnricher, StaticEnricher

pipeline = StaticEnricher(env="prod") + HostnameEnricher() + ProcessEnricher()
fields = pipeline.enrich({"message": "ready"})
```

Each enricher in the chain receives the output of the previous one.

## Writing a custom enricher

Subclass `BaseEnricher` and implement `enrich`:

```python
from nestlog.enrichers import BaseEnricher

class RequestIdEnricher(BaseEnricher):
    def __init__(self, request_id: str) -> None:
        self._request_id = request_id

    def enrich(self, fields):
        return {"request_id": self._request_id, **fields}
```
