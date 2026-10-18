"""Concurrent correlation, immutable logger policy and opaque-secret safety (API-004)."""

import asyncio
import io
import json
import logging as stdlib_logging
import os
from concurrent.futures import ThreadPoolExecutor

import pytest

from hfcache import logging as event_logging
from hfcache import redaction
from hfcache.errors import IntegrityError, Problem
from hfcache.identity import RunId
from hfcache.reporting import EnvelopeProblem
from hfcache.services import commands
from hfcache.services.context import ExecutionContext, ServiceResult
from tests.fixtures import examples
from tests.unit.test_command_locking import (
    command_archive as command_archive,  # noqa: PLC0414 - shared pytest fixture
)
from tests.unit.test_logging import fields
from tests.unit.test_verification import MODEL, SHA_A, publish
from tests.unit.test_verify_command import write_run_report


@pytest.fixture(autouse=True)
def isolated_logging():
    event_logging.reset()
    redaction.clear_registered_secrets()
    yield
    event_logging.reset()
    redaction.clear_registered_secrets()


def test_async_requests_and_copied_workers_restore_correlation_after_failures():
    stream = io.StringIO()
    event_logging.configure_daemon(stream=stream)
    outer_run = "0" * 32
    contexts = {
        "read-one": ExecutionContext(
            RunId("a" * 32), examples.at("2026-07-24T20:00:00.000000Z"), request_id="1" * 32
        ),
        "read-two": ExecutionContext(
            RunId("b" * 32), examples.at("2026-07-24T20:00:00.000000Z"), request_id="2" * 32
        ),
        "operation": ExecutionContext(
            RunId("c" * 32),
            examples.at("2026-07-24T20:00:00.000000Z"),
            request_id="3" * 32,
            operation_id="4" * 32,
        ),
    }

    class ExpectedError(Exception):
        pass

    def worker(marker):
        event_logging.emit("run.started", marker=marker, phase="worker")
        if marker == "operation":
            raise ExpectedError
        return event_logging.current_correlation()

    async def request(marker, pool):
        context = contexts[marker]
        try:
            with context.activate():
                event_logging.emit("run.started", marker=marker, phase="before-await")
                await asyncio.sleep(0)
                observed = await asyncio.wrap_future(
                    event_logging.submit_with_context(pool, worker, marker)
                )
                assert observed.run_id == context.run_id
                assert observed.request_id == context.request_id
                event_logging.emit("run.completed", marker=marker, phase="after-await")
        except ExpectedError:
            assert marker == "operation"
        restored = event_logging.current_correlation()
        assert restored.run_id == outer_run
        assert restored.request_id is None
        assert restored.operation_id is None
        event_logging.emit("run.completed", marker=marker, phase="restored")

    async def interleave(pool):
        await asyncio.gather(*(request(marker, pool) for marker in contexts))

    with ThreadPoolExecutor(max_workers=1) as pool:
        with event_logging.scoped_context(run_id=outer_run):
            asyncio.run(interleave(pool))
            assert event_logging.current_run_id() == outer_run
        # A copied context must leave the reused worker's base context intact,
        # including when its prior function raised.
        restored_worker = pool.submit(event_logging.current_correlation).result(timeout=5)
    assert restored_worker.run_id is None
    assert restored_worker.request_id is None
    assert restored_worker.operation_id is None
    assert event_logging.current_run_id() is None

    lines = [fields(line) for line in stream.getvalue().splitlines()]
    assert {item["marker"] for item in lines if item["phase"] == "worker"} == set(contexts)
    for line in lines:
        if line["phase"] == "restored":
            assert line["run_id"] == outer_run
            assert line.get("request_id", "-") == "-"
            assert line.get("operation_id", "-") == "-"
        else:
            expected = contexts[line["marker"]]
            assert line["run_id"] == expected.run_id
            assert line["request_id"] == expected.request_id
            assert line.get("operation_id", "-") == (expected.operation_id or "-")


def test_daemon_logger_keeps_one_handler_and_startup_level_across_request_scopes(capsys):
    stream = io.StringIO()
    event_logging.configure_daemon(stream=stream, level=stdlib_logging.INFO)
    logger = stdlib_logging.getLogger(event_logging.LOGGER_NAME)
    original_handlers = tuple(logger.handlers)
    event_logging.configure_daemon(stream=stream, level=stdlib_logging.INFO)

    with event_logging.scoped_context(run_id="a" * 32, request_id="b" * 32):
        event_logging.configure_daemon(stream=stream, level=stdlib_logging.INFO)
        assert event_logging.current_run_id() == "a" * 32
        assert event_logging.current_correlation().request_id == "b" * 32
        with pytest.raises(RuntimeError):
            event_logging.configure(verbose=1, quiet=True, stream=io.StringIO())
        event_logging.emit("capacity.evaluated", phase="hidden-debug")
        event_logging.emit("run.started", phase="visible-info")

    assert tuple(logger.handlers) == original_handlers
    assert len(logger.handlers) == 1
    assert logger.level == stdlib_logging.INFO
    assert "hidden-debug" not in stream.getvalue()
    assert "visible-info" in stream.getvalue()
    assert capsys.readouterr().out == ""


def test_event_fields_cannot_override_or_invent_authoritative_correlation():
    stream = io.StringIO()
    event_logging.configure_daemon(stream=stream)
    with event_logging.scoped_context(run_id="a" * 32):
        event_logging.emit(
            "run.started",
            run_id="b" * 32,
            request_id="c" * 32,
            operation_id="d" * 32,
            event="repository.failed",
            level="error",
        )
    line = stream.getvalue().strip()
    parsed = fields(line)

    assert parsed["event"] == "run.started"
    assert parsed["level"] == "info"
    assert parsed["run_id"] == "a" * 32
    assert "request_id" not in parsed
    assert "operation_id" not in parsed
    assert line.count("run_id=") == 1
    assert line.count("event=") == 1
    assert line.count("level=") == 1


OPAQUE_SECRET = "opaque-test-secret-7N62bE1Y3rM98cD04LqZ"


def test_registered_opaque_tokens_are_redacted_from_nested_contexts_and_logs():
    redaction.register_secret(OPAQUE_SECRET)
    stream = io.StringIO()
    event_logging.configure_daemon(stream=stream)
    original_record = {"note": f"prefix {OPAQUE_SECRET} suffix", "Authorization": "another secret"}
    original = {
        "records": [original_record],
        OPAQUE_SECRET: {"location": OPAQUE_SECRET},
        "exception": RuntimeError(f"failed with {OPAQUE_SECRET}"),
        "ordinary": "preserved",
    }

    sanitized = redaction.sanitize(original)
    event_logging.emit("repository.failed", detail=original)
    problem = Problem(
        code="HFVER007",
        message=f"message {OPAQUE_SECRET}",
        location=f"path/{OPAQUE_SECRET}",
        repository=f"model:{OPAQUE_SECRET}",
        context=original,
    )
    error = IntegrityError((problem,))

    assert OPAQUE_SECRET not in json.dumps(sanitized)
    assert OPAQUE_SECRET not in stream.getvalue()
    assert OPAQUE_SECRET not in problem.as_line()
    assert OPAQUE_SECRET not in json.dumps(problem.as_envelope_entry())
    assert OPAQUE_SECRET not in str(error)
    assert OPAQUE_SECRET not in str(redaction.sanitize(error))
    assert isinstance(sanitized, dict)
    assert sanitized["ordinary"] == "preserved"
    assert original_record["note"] == f"prefix {OPAQUE_SECRET} suffix"
    assert "another secret" not in json.dumps(sanitized)


def test_registering_a_secret_after_problem_creation_still_protects_output():
    problem = Problem(
        code="HFVER007", message=f"failed with {OPAQUE_SECRET}", context={"detail": OPAQUE_SECRET}
    )
    error = IntegrityError((problem,))
    result = ServiceResult("verify --full", {}, errors=(problem,), exit_code=40)
    redaction.register_secret(OPAQUE_SECRET)
    # Problem contexts remain caller-mutable for compatibility; output must
    # sanitize later additions too, and immutable results keep their own copy.
    problem.context["later"] = {OPAQUE_SECRET: [OPAQUE_SECRET]}

    assert OPAQUE_SECRET not in problem.as_line()
    assert OPAQUE_SECRET not in json.dumps(problem.as_envelope_entry())
    assert OPAQUE_SECRET not in repr(problem)
    assert OPAQUE_SECRET not in EnvelopeProblem.of(problem).to_json()
    assert OPAQUE_SECRET not in result.envelope(ExecutionContext.create()).to_json()
    assert OPAQUE_SECRET not in str(error)
    assert OPAQUE_SECRET not in repr(error)


def test_logger_exception_output_uses_registered_secret_sanitization():
    redaction.register_secret(OPAQUE_SECRET)
    stream = io.StringIO()
    event_logging.configure_daemon(stream=stream)
    logger = stdlib_logging.getLogger(event_logging.LOGGER_NAME)

    def fail():
        message = f"sensitive failure {OPAQUE_SECRET}"
        raise RuntimeError(message)

    try:
        fail()
    except RuntimeError:
        logger.exception("operation failed with %s", OPAQUE_SECRET)

    assert OPAQUE_SECRET not in stream.getvalue()
    assert "operation failed" in stream.getvalue()


def test_execution_context_keeps_schema1_identity_and_restores_nested_scope():
    first = ExecutionContext.create(request_id="1" * 32, operation_id="2" * 32)
    second = ExecutionContext.create(request_id="3" * 32)
    assert first.run_id != second.run_id
    assert len(first.run_id) == 32
    with first.activate():
        assert event_logging.current_run_id() == first.run_id
        with second.activate():
            assert event_logging.current_run_id() == second.run_id
        assert event_logging.current_run_id() == first.run_id
        assert event_logging.current_correlation().operation_id == first.operation_id
    assert event_logging.current_run_id() is None


@pytest.mark.parametrize("mode", ["new", "full", "revision", "estimate"])
def test_shared_verification_never_changes_environment_or_constructs_hub_authority(
    command_archive, monkeypatch, mode
):
    layout, config, _, _ = command_archive
    published = publish(layout)
    _, run_id = write_run_report(
        layout, commit_sha=published.commit_sha, publication_id=published.publication_id
    )
    before = dict(os.environ)

    def forbidden(*args, **kwargs):
        pytest.fail("shared verification touched process environment, credentials or Hub client")

    monkeypatch.setattr(commands, "resolve_token", forbidden)
    monkeypatch.setattr(commands.HubClient, "of", forbidden)
    request = commands.VerificationRequest(
        new=mode == "new",
        full=mode == "full",
        revision=f"{MODEL.selector}@{SHA_A}" if mode == "revision" else None,
        estimate=mode == "estimate",
        run_id=run_id if mode == "new" else None,
    )
    with monkeypatch.context() as environment_guard:
        environment_guard.setattr(type(os.environ), "__setitem__", forbidden)
        environment_guard.setattr(type(os.environ), "__delitem__", forbidden)
        result = commands.CommandServices(config, ExecutionContext.create()).verify(request)

    assert result.exit_code == 0
    assert dict(os.environ) == before
