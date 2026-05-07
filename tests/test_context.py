"""Tests for nestlog.context — thread-local structured context fields."""

import threading

import pytest

from nestlog.context import (
    bind,
    bound_context,
    clear,
    current_fields,
    unbind,
)


def setup_function():
    """Ensure a clean context before every test."""
    clear()


# ---------------------------------------------------------------------------
# bind / unbind / clear
# ---------------------------------------------------------------------------

def test_bind_adds_fields():
    bind(user="alice", env="prod")
    assert current_fields() == {"user": "alice", "env": "prod"}


def test_unbind_removes_key():
    bind(user="alice", env="prod")
    unbind("env")
    assert current_fields() == {"user": "alice"}


def test_unbind_missing_key_is_noop():
    bind(user="alice")
    unbind("nonexistent")  # should not raise
    assert "user" in current_fields()


def test_clear_removes_all():
    bind(a=1, b=2)
    clear()
    assert current_fields() == {}


# ---------------------------------------------------------------------------
# bound_context context-manager
# ---------------------------------------------------------------------------

def test_bound_context_adds_fields_inside_block():
    with bound_context(request_id="xyz"):
        assert current_fields()["request_id"] == "xyz"


def test_bound_context_removes_fields_after_block():
    with bound_context(request_id="xyz"):
        pass
    assert "request_id" not in current_fields()


def test_bound_context_does_not_pollute_outer_frame():
    bind(outer="yes")
    with bound_context(inner="no"):
        assert current_fields()["outer"] == "yes"
        assert current_fields()["inner"] == "no"
    assert "inner" not in current_fields()
    assert current_fields()["outer"] == "yes"


def test_bound_context_nested():
    with bound_context(a=1):
        with bound_context(b=2):
            fields = current_fields()
            assert fields["a"] == 1
            assert fields["b"] == 2
        assert "b" not in current_fields()
    assert "a" not in current_fields()


# ---------------------------------------------------------------------------
# bound_context as decorator
# ---------------------------------------------------------------------------

def test_bound_context_decorator():
    @bound_context(service="worker")
    def job():
        return current_fields().get("service")

    assert job() == "worker"
    assert "service" not in current_fields()


# ---------------------------------------------------------------------------
# Thread isolation
# ---------------------------------------------------------------------------

def test_context_is_thread_local():
    results: dict = {}

    def worker(name: str) -> None:
        bind(thread=name)
        import time; time.sleep(0.02)
        results[name] = current_fields().get("thread")

    threads = [threading.Thread(target=worker, args=(n,)) for n in ("t1", "t2")]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert results["t1"] == "t1"
    assert results["t2"] == "t2"
