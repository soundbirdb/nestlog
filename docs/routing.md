# Log Record Routing

The `nestlog.routing` module lets you dispatch log records to different sinks
based on arbitrary predicates, without changing the rest of your pipeline.

## Quick start

```python
from nestlog.routing import Router, by_level_name, by_field
from nestlog.sinks import StreamSink

error_sink = StreamSink(open("errors.log", "a"))
audit_sink  = StreamSink(open("audit.log",  "a"))
catchall    = StreamSink(sys.stdout)

router = (
    Router()
    .add_route(by_level_name("ERROR"),      error_sink)
    .add_route(by_field("audit", True),     audit_sink)
    .set_default(catchall)
)

# Pass the router as a sink to your logger
logger.add_sink(router)
```

## Router

### `Router(exclusive=True)`

| Parameter   | Type   | Default | Description                                      |
|-------------|--------|---------|--------------------------------------------------|
| `exclusive` | `bool` | `True`  | Stop after the first matching rule when `True`.  |

#### Methods

| Method                          | Returns  | Description                                   |
|---------------------------------|----------|-----------------------------------------------|
| `add_route(rule, sink)`         | `Router` | Register a (rule, sink) pair. Chainable.       |
| `set_default(sink)`             | `Router` | Sink for records that match no rule. Chainable.|
| `emit(record)`                  | `None`   | Dispatch the record according to the routes.  |

## Built-in rule factories

### `by_level_name(name)`

Matches records whose level string equals *name* (case-insensitive).

```python
by_level_name("ERROR")
```

### `by_field(key, value)`

Matches records whose `fields[key] == value`.

```python
by_field("component", "database")
```

### `by_predicate(fn)`

Pass-through helper that accepts any `Callable[[LogRecord], bool]`.

```python
by_predicate(lambda rec: "password" not in rec.fields)
```

## Non-exclusive routing

Set `exclusive=False` to fan a record out to *all* matching sinks:

```python
router = Router(exclusive=False)
router.add_route(by_level_name("ERROR"), pagerduty_sink)
router.add_route(by_level_name("ERROR"), slack_sink)
```

The default sink is **not** invoked when at least one rule matched,
regardless of the `exclusive` setting.
