"""Tests for nestlog.enrichers."""

import os
import threading
from typing import Any, Dict

import pytest

from nestlog.enrichers import (
    CallableEnricher,
    ChainedEnricher,
    HostnameEnricher,
    ProcessEnricher,
    StaticEnricher,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _base() -> Dict[str, Any]:
    return {"message": "hello"}


# ---------------------------------------------------------------------------
# StaticEnricher
# ---------------------------------------------------------------------------

class TestStaticEnricher:
    def test_adds_static_fields(self):
        e = StaticEnricher(env="prod", version="1.0")
        result = e.enrich(_base())
        assert result["env"] == "prod"
        assert result["version"] == "1.0"

    def test_record_fields_win_over_static(self):
        e = StaticEnricher(env="prod")
        result = e.enrich({"message": "hi", "env": "staging"})
        assert result["env"] == "staging"

    def test_does_not_mutate_input(self):
        e = StaticEnricher(foo="bar")
        original = _base()
        e.enrich(original)
        assert "foo" not in original


# ---------------------------------------------------------------------------
# HostnameEnricher
# ---------------------------------------------------------------------------

class TestHostnameEnricher:
    def test_adds_hostname(self):
        e = HostnameEnricher()
        result = e.enrich(_base())
        assert "hostname" in result
        assert isinstance(result["hostname"], str)
        assert len(result["hostname"]) > 0

    def test_does_not_overwrite_existing_hostname(self):
        e = HostnameEnricher()
        result = e.enrich({"hostname": "custom-host"})
        assert result["hostname"] == "custom-host"


# ---------------------------------------------------------------------------
# ProcessEnricher
# ---------------------------------------------------------------------------

class TestProcessEnricher:
    def test_adds_pid(self):
        e = ProcessEnricher()
        result = e.enrich(_base())
        assert result["pid"] == os.getpid()

    def test_adds_thread_id(self):
        e = ProcessEnricher()
        result = e.enrich(_base())
        assert result["thread_id"] == threading.get_ident()


# ---------------------------------------------------------------------------
# CallableEnricher
# ---------------------------------------------------------------------------

class TestCallableEnricher:
    def test_delegates_to_callable(self):
        e = CallableEnricher(lambda f: {**f, "injected": True})
        result = e.enrich(_base())
        assert result["injected"] is True

    def test_callable_receives_copy(self):
        seen = {}

        def capture(fields):
            seen.update(fields)
            return fields

        original = _base()
        CallableEnricher(capture).enrich(original)
        seen["extra"] = "mutated"
        assert "extra" not in original


# ---------------------------------------------------------------------------
# ChainedEnricher (via __add__)
# ---------------------------------------------------------------------------

class TestChainedEnricher:
    def test_add_operator_chains(self):
        e = StaticEnricher(a=1) + StaticEnricher(b=2)
        result = e.enrich(_base())
        assert result["a"] == 1
        assert result["b"] == 2

    def test_chain_applies_in_order(self):
        # second enricher should see output of first
        calls = []
        e1 = CallableEnricher(lambda f: {**f, "step": 1})
        e2 = CallableEnricher(lambda f: (calls.append(f.get("step")), f)[1])
        (e1 + e2).enrich(_base())
        assert calls == [1]
