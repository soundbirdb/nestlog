"""ASGI-compatible request logging middleware for nestlog."""

import time
import uuid
from typing import Callable, Optional

from .context import bind, clear
from .core import Logger


class ASGIRequestLoggingMiddleware:
    """ASGI middleware that binds request metadata into the log context.

    Supports the ASGI 3.0 interface (HTTP scope only; other scopes are
    passed through unchanged).

    Example::

        from nestlog import get_logger
        from nestlog.asgi_middleware import ASGIRequestLoggingMiddleware

        logger = get_logger("myapp")
        app = ASGIRequestLoggingMiddleware(asgi_app, logger=logger)
    """

    def __init__(
        self,
        app: Callable,
        logger: Optional[Logger] = None,
        generate_id: Callable[[], str] = lambda: str(uuid.uuid4()),
    ) -> None:
        self._app = app
        self._logger = logger
        self._generate_id = generate_id

    async def __call__(self, scope: dict, receive: Callable, send: Callable) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        request_id = self._generate_id()
        headers = dict(scope.get("headers", []))
        request_id = (
            headers.get(b"x-request-id", b"").decode() or request_id
        )
        method = scope.get("method", "GET")
        path = scope.get("path", "/")

        bind(request_id=request_id, http_method=method, http_path=path)
        start = time.monotonic()
        status_holder: list = []

        async def _send(message: dict) -> None:
            if message["type"] == "http.response.start":
                status_holder.append(message.get("status", 0))
            await send(message)

        try:
            await self._app(scope, receive, _send)
        finally:
            duration_ms = round((time.monotonic() - start) * 1000, 2)
            status_code = status_holder[0] if status_holder else 0
            if self._logger is not None:
                self._logger.info(
                    "request completed",
                    status_code=status_code,
                    duration_ms=duration_ms,
                )
            clear()
