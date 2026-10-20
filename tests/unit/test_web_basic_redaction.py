"""Unregistered Basic Authorization material never reaches shared output paths."""

import base64
import io
import json
import logging as stdlib_logging
import secrets

import pytest

from hfcache import redaction
from hfcache.errors import Problem
from hfcache.logging import LOGGER_NAME, configure, emit, reset
from hfcache.redaction import REDACTED, redact_text, sanitize


@pytest.mark.parametrize("scheme", ["Basic", "basic", "BASIC", "bAsIc"])
@pytest.mark.parametrize("separator", [" ", "  ", "\t", "\r\n "])
def test_basic_text_is_scrubbed_without_registering_any_password(scheme, separator):
    password = secrets.token_urlsafe(32)
    encoded = base64.b64encode(("operator:" + password).encode()).decode()
    before = frozenset(redaction._registered)
    assert redact_text(f"Authorization: {scheme}{separator}{encoded}") == REDACTED
    assert redact_text(f"request failed ({scheme}{separator}{encoded})") == REDACTED
    assert frozenset(redaction._registered) == before


@pytest.mark.parametrize(
    "value", ["", "Basic", "Basic !!!", "Basic\x00malformed", "unclassified-header"]
)
def test_structured_authorization_key_is_unconditionally_redacted(value):
    assert sanitize({"Authorization": value}) == {"Authorization": REDACTED}
    assert sanitize({"nested": [{"authorization": value}]}) == {
        "nested": [{"authorization": REDACTED}]
    }


def test_nested_unknown_fields_errors_problem_snapshots_and_logs_scrub_basic():
    password = secrets.token_urlsafe(32)
    encoded = base64.b64encode(("operator:" + password).encode()).decode()
    header = "Basic " + encoded
    before = frozenset(redaction._registered)
    safe = sanitize({"detail": [header, {"unexpected": RuntimeError(header)}], header: "value"})
    assert encoded not in json.dumps(safe)
    problem = Problem(
        "HFAPI001", header, location=header, repository=header, context={"detail": header}
    )
    assert problem.message == problem.location == problem.repository == REDACTED
    assert problem.context == {"detail": REDACTED}
    assert encoded not in json.dumps(problem.as_envelope_entry())
    stream = io.StringIO()
    configure(stream=stream, run_id="0" * 32)
    try:
        emit("run.started", detail=header, headers={"Authorization": header})
        stdlib_logging.getLogger(LOGGER_NAME).warning(header)
    finally:
        reset()
    output = stream.getvalue()
    assert encoded not in output
    assert password not in output
    assert REDACTED in output
    assert frozenset(redaction._registered) == before


def test_plain_nonsecret_values_and_existing_bearer_scrubbing_remain_compatible():
    assert redact_text("authentication unavailable") == "authentication unavailable"
    assert redact_text("https://archive.example") == "https://archive.example"
    assert redact_text("Bearer unregistered-opaque-value") == REDACTED
    assert sanitize({"password": "anything", "enabled": True, "count": 2}) == {
        "password": REDACTED,
        "enabled": True,
        "count": 2,
    }
