# nestlog

Lightweight structured logging library for Python with pluggable sinks and zero dependencies.

---

## Installation

```bash
pip install nestlog
```

---

## Usage

```python
import nestlog

logger = nestlog.get_logger(name="myapp")

logger.info("Server started", port=8080, env="production")
logger.warning("High memory usage", used_mb=1024, threshold_mb=900)
logger.error("Request failed", status=500, path="/api/users")
```

**Output:**

```json
{"level": "INFO", "name": "myapp", "message": "Server started", "port": 8080, "env": "production", "timestamp": "2024-01-15T10:23:45Z"}
```

### Pluggable Sinks

nestlog supports custom sinks to route log output wherever you need it.

```python
from nestlog import get_logger, FileSink, ConsoleSink

logger = get_logger(
    name="myapp",
    sinks=[
        ConsoleSink(level="DEBUG"),
        FileSink(path="app.log", level="WARNING"),
    ]
)
```

### Context Binding

```python
request_log = logger.bind(request_id="abc-123", user_id=42)
request_log.info("Processing request")
```

---

## Features

- Structured JSON output by default
- Pluggable sink architecture
- Context binding with `bind()`
- Zero external dependencies
- Python 3.8+

---

## License

MIT © nestlog contributors