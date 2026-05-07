"""Tests for nestlog.redactors."""

from __future__ import annotations

import re
import pytest

from nestlog.core import LogRecord, Level
from nestlog.redactors import RedactKeysProcessor, RedactPatternsProcessor


def _make_record(**fields) -> LogRecord:
    return LogRecord(level=Level.INFO, message="test", fields=fields)


# ---------------------------------------------------------------------------
# RedactKeysProcessor
# ---------------------------------------------------------------------------

class TestRedactKeysProcessor:
    def test_redacts_specified_key(self):
        proc = RedactKeysProcessor(["password"])
        out = proc.process(_make_record(user="alice", password="s3cr3t"))
        assert out.fields["password"] == "***"
        assert out.fields["user"] == "alice"

    def test_non_listed_keys_are_unchanged(self):
        proc = RedactKeysProcessor(["token"])
        out = proc.process(_make_record(token="abc", request_id="xyz"))
        assert out.fields["request_id"] == "xyz"

    def test_custom_mask(self):
        proc = RedactKeysProcessor(["secret"], mask="[REDACTED]")
        out = proc.process(_make_record(secret="hunter2"))
        assert out.fields["secret"] == "[REDACTED]"

    def test_empty_key_list_returns_equivalent_record(self):
        proc = RedactKeysProcessor([])
        record = _make_record(foo="bar")
        out = proc.process(record)
        assert out.fields == record.fields

    def test_does_not_mutate_original_record(self):
        proc = RedactKeysProcessor(["pw"])
        record = _make_record(pw="original")
        proc.process(record)
        assert record.fields["pw"] == "original"

    def test_multiple_keys_redacted(self):
        proc = RedactKeysProcessor(["pw", "ssn", "card"])
        out = proc.process(_make_record(pw="x", ssn="y", card="z", safe="ok"))
        assert out.fields["pw"] == "***"
        assert out.fields["ssn"] == "***"
        assert out.fields["card"] == "***"
        assert out.fields["safe"] == "ok"

    def test_level_and_message_preserved(self):
        proc = RedactKeysProcessor(["pw"])
        record = _make_record(pw="x")
        out = proc.process(record)
        assert out.level == record.level
        assert out.message == record.message


# ---------------------------------------------------------------------------
# RedactPatternsProcessor
# ---------------------------------------------------------------------------

class TestRedactPatternsProcessor:
    def test_masks_matching_substring(self):
        proc = RedactPatternsProcessor(r"\d{4}-\d{4}-\d{4}-\d{4}")
        out = proc.process(_make_record(info="card: 1234-5678-9012-3456"))
        assert "1234-5678-9012-3456" not in out.fields["info"]
        assert "***" in out.fields["info"]

    def test_non_string_values_are_untouched(self):
        proc = RedactPatternsProcessor(r"secret")
        out = proc.process(_make_record(count=42, ratio=0.5))
        assert out.fields["count"] == 42
        assert out.fields["ratio"] == 0.5

    def test_accepts_compiled_pattern(self):
        pattern = re.compile(r"token=[^&\s]+")
        proc = RedactPatternsProcessor(pattern)
        out = proc.process(_make_record(url="/api?token=abc123&page=1"))
        assert "abc123" not in out.fields["url"]
        assert "page=1" in out.fields["url"]

    def test_custom_mask(self):
        proc = RedactPatternsProcessor(r"password", mask="<hidden>")
        out = proc.process(_make_record(msg="password leak"))
        assert out.fields["msg"] == "<hidden> leak"

    def test_does_not_mutate_original_record(self):
        proc = RedactPatternsProcessor(r"\d+")
        record = _make_record(code="1234")
        proc.process(record)
        assert record.fields["code"] == "1234"

    def test_chained_with_redact_keys(self):
        key_proc = RedactKeysProcessor(["api_key"])
        pat_proc = RedactPatternsProcessor(r"Bearer \S+")
        combined = key_proc + pat_proc
        record = _make_record(api_key="secret", auth="Bearer tok123")
        out = combined.process(record)
        assert out.fields["api_key"] == "***"
        assert "tok123" not in out.fields["auth"]
