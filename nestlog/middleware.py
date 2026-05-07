"""WSGI/ASGI-compatible request logging middleware for nestlog."""

import time
import uuid
from typing import Callable, Optional

from .context import bind, clear
from .core import Logger


class RequestLoggingMiddleware:
    """WSGI middleware that binds request metadata into the log context.

    Automatically assigns a ``request_id`` (UUID4) to each incoming request
    and records method, path, status code, and duration on completion.

    Example::

        from nestlog import get_logger
        from nestlog.middleware import RequestLoggingMiddleware

        logger = get_logger("myapp")
        app = RequestLoggingMiddleware(wsgi_app, logger=logger)
    """

    def __init__(
        self,
        app: Callable,
        logger: Optional[Logger] = None,
        id_header: str = "X-Request-Id",
        generate_id: Callable[[], str] = lambda: str(uuid.uuid4()),
    ) -> None:
        self._app = app
        self._logger = logger
        self._id_header = id_header
        self._generate_id = generate_id

    def __call__(self, environ: dict, start_response: Callable) -> object:
        request_id = (
            environ.get("HTTP_" + self._id_header.upper().replace("-", "_"))
            or self._generate_id()
        )
        method = environ.get("REQUEST_METHOD", "GET")
        path = environ.get("PATH_INFO", "/")

        bind(request_id=request_id, http_method=method, http_path=path)
        start = time.monotonic()
        status_holder: list = []

        def _start_response(status: str, headers: list, exc_info=None):
            status_holder.append(status)
            return start_response(status, headers, exc_info)

        try:
            result = self._app(environ, _start_response)
            return result
        finally:
            duration_ms = round((time.monotonic() - start) * 1000, 2)
            status_code = int(status_holder[0].split(" ")[0]) if status_holder else 0
            if self._logger is not None:
                self._logger.info(
                    "request completed",
                    status_code=status_code,
                    duration_ms=duration_ms,
                )
            clear()
