# Request Logging Middleware

nestlog ships with thin WSGI and ASGI middleware that automatically binds
per-request context fields (request ID, HTTP method, path) and emits a
single structured log line when each request completes.

## WSGI

```python
from nestlog import get_logger
from nestlog.middleware import RequestLoggingMiddleware

logger = get_logger("myapp")
app = RequestLoggingMiddleware(your_wsgi_app, logger=logger)
```

### Constructor parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `app` | `Callable` | — | The wrapped WSGI application. |
| `logger` | `Logger \| None` | `None` | Logger used to emit the completion record. Pass `None` to skip logging. |
| `id_header` | `str` | `"X-Request-Id"` | HTTP header inspected for an incoming request ID. |
| `generate_id` | `Callable[[], str]` | `uuid4` | Factory used when no ID header is present. |

### Context fields injected

- `request_id` — value of the ID header or a freshly generated UUID.
- `http_method` — e.g. `GET`, `POST`.
- `http_path` — the `PATH_INFO` value.

All fields are cleared from the context after the request finishes, even
if an exception is raised.

## ASGI

```python
from nestlog import get_logger
from nestlog.asgi_middleware import ASGIRequestLoggingMiddleware

logger = get_logger("myapp")
app = ASGIRequestLoggingMiddleware(your_asgi_app, logger=logger)
```

Only `http` scopes are intercepted; `websocket` and `lifespan` scopes are
passed through unchanged.

### Constructor parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `app` | `Callable` | — | The wrapped ASGI application. |
| `logger` | `Logger \| None` | `None` | Logger used to emit the completion record. |
| `generate_id` | `Callable[[], str]` | `uuid4` | Factory for request IDs when the `x-request-id` header is absent. |

## Completion log record

Both middleware variants emit an `INFO`-level record with the message
`"request completed"` and the following extra fields:

```
status_code=200  duration_ms=3.14
```

These fields are in addition to any context fields already bound via
`nestlog.context.bind`.

## Combining with enrichers

Because the middleware uses `nestlog.context`, any `ContextEnricher` you
add to your logger pipeline will automatically pick up `request_id`,
`http_method`, and `http_path` for every record emitted during the
lifetime of the request — not just the completion record.

```python
from nestlog.enrichers import ContextEnricher

logger = get_logger("myapp")
logger.add_enricher(ContextEnricher())
app = RequestLoggingMiddleware(your_wsgi_app, logger=logger)
```
