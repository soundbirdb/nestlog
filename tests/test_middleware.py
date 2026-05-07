"""Tests for nestlog.middleware (WSGI) and nestlog.asgi_middleware (ASGI)."""

import pytest

from nestlog.context import current_fields
from nestlog.middleware import RequestLoggingMiddleware
from nestlog.asgi_middleware import ASGIRequestLoggingMiddleware


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _FakeLogger:
    def __init__(self):
        self.records = []

    def info(self, msg, **kw):
        self.records.append({"msg": msg, **kw})


def _simple_wsgi_app(environ, start_response):
    start_response("200 OK", [("Content-Type", "text/plain")])
    return [b"hello"]


def _make_environ(method="GET", path="/test", request_id=None):
    env = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
    }
    if request_id:
        env["HTTP_X_REQUEST_ID"] = request_id
    return env


# ---------------------------------------------------------------------------
# WSGI middleware tests
# ---------------------------------------------------------------------------

class TestRequestLoggingMiddleware:
    def _make(self, app=_simple_wsgi_app, logger=None):
        return RequestLoggingMiddleware(
            app, logger=logger, generate_id=lambda: "test-id-123"
        )

    def test_passes_through_response(self):
        mw = self._make()
        responses = []
        def sr(status, headers, exc_info=None):
            responses.append(status)
        result = mw(_make_environ(), sr)
        assert b"".join(result) == b"hello"
        assert responses == ["200 OK"]

    def test_logs_completion(self):
        logger = _FakeLogger()
        mw = self._make(logger=logger)
        mw(_make_environ(), lambda s, h, exc_info=None: None)
        assert len(logger.records) == 1
        rec = logger.records[0]
        assert rec["msg"] == "request completed"
        assert rec["status_code"] == 200
        assert "duration_ms" in rec

    def test_uses_incoming_request_id(self):
        logger = _FakeLogger()
        mw = RequestLoggingMiddleware(_simple_wsgi_app, logger=logger)
        env = _make_environ(request_id="my-custom-id")
        mw(env, lambda s, h, exc_info=None: None)
        assert logger.records[0]["status_code"] == 200

    def test_context_cleared_after_request(self):
        mw = self._make()
        mw(_make_environ(), lambda s, h, exc_info=None: None)
        assert current_fields() == {}

    def test_context_cleared_on_exception(self):
        def _bad_app(environ, start_response):
            raise RuntimeError("boom")

        mw = self._make(app=_bad_app)
        with pytest.raises(RuntimeError):
            mw(_make_environ(), lambda s, h, exc_info=None: None)
        assert current_fields() == {}


# ---------------------------------------------------------------------------
# ASGI middleware tests
# ---------------------------------------------------------------------------

class TestASGIRequestLoggingMiddleware:
    def _make_scope(self, method="GET", path="/", headers=None):
        return {
            "type": "http",
            "method": method,
            "path": path,
            "headers": headers or [],
        }

    def _run(self, app, scope, logger=None):
        import asyncio
        mw = ASGIRequestLoggingMiddleware(
            app, logger=logger, generate_id=lambda: "asgi-id-1"
        )
        messages = []

        async def _send(msg):
            messages.append(msg)

        async def _receive():
            return {"type": "http.request", "body": b""}

        asyncio.get_event_loop().run_until_complete(mw(scope, _receive, _send))
        return messages

    def test_passes_non_http_scope(self):
        import asyncio
        called = []

        async def _app(scope, receive, send):
            called.append(scope["type"])

        async def _run():
            mw = ASGIRequestLoggingMiddleware(_app)
            await mw({"type": "websocket"}, None, None)

        asyncio.get_event_loop().run_until_complete(_run())
        assert called == ["websocket"]

    def test_logs_http_request(self):
        import asyncio
        logger = _FakeLogger()

        async def _app(scope, receive, send):
            await send({"type": "http.response.start", "status": 201})
            await send({"type": "http.response.body", "body": b""})

        scope = self._make_scope()
        self._run(_app, scope, logger=logger)
        assert logger.records[0]["status_code"] == 201

    def test_context_cleared_after_asgi_request(self):
        import asyncio

        async def _app(scope, receive, send):
            await send({"type": "http.response.start", "status": 200})
            await send({"type": "http.response.body", "body": b""})

        self._run(_app, self._make_scope())
        assert current_fields() == {}
