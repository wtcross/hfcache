"""The structured event log (`docs/plan.md` §24, `src/hfcache/logging.py`).

Three things are worth testing here and the rest is plumbing. That the
vocabulary is closed, because that is what makes an operator's journald filter
survive a release. That the run id reaches every line, because §24 asks for it
and a line without one cannot be joined to a run report. And that a secret never
does, which is the only property here whose failure is not merely inconvenient.
"""

import io
import json
import logging as stdlib_logging
from typing import TYPE_CHECKING

import pytest
from typer.testing import CliRunner

from hfcache.cli import app
from hfcache.logging import (
    DEBUG_EVENTS,
    EVENTS,
    LOGGER_NAME,
    REDACTED,
    bind_run,
    configure,
    current_run_id,
    emit,
    level_for,
    reset,
    scoped_context,
    under_systemd,
)

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

VALID = """
schema_version = 1

[storage]
archive_root = "/srv/hfcache"
archive_id = "3f2a1c88-7b40-4a2e-9c1d-0e5b6a7f8d90"

[[repositories]]
id = "organization/model-name"
type = "model"
"""


@pytest.fixture
def config_file(tmp_path: Path) -> Path:
    path = tmp_path / "config.toml"
    path.write_text(VALID, encoding="utf-8")
    return path


@pytest.fixture
def stream() -> Iterator[io.StringIO]:
    """A configured logger writing somewhere a test can read."""
    captured = io.StringIO()
    configure(stream=captured, run_id="0" * 32)
    yield captured
    reset()


def fields(line: str) -> dict[str, str]:
    """Parse one logfmt line back into a mapping, honouring quoted values.

    The leading `<N>` is stripped rather than rejected, so these tests read the
    same whether or not the suite itself happens to be running under systemd.
    """
    out: dict[str, str] = {}
    rest = line.strip()
    if rest.startswith("<") and rest[2:3] == ">":
        rest = rest[3:]
    while rest:
        key, _, rest = rest.partition("=")
        if rest.startswith('"'):
            value, rest = _quoted(rest)
        else:
            value, _, rest = rest.partition(" ")
        out[key.strip()] = value
    return out


def _quoted(text: str) -> tuple[str, str]:
    """Read one double-quoted logfmt value, returning it and what follows."""
    index, buffer = 1, []
    while text[index] != '"':
        if text[index] == "\\":
            index += 1
            buffer.append({"n": "\n"}.get(text[index], text[index]))
        else:
            buffer.append(text[index])
        index += 1
    return "".join(buffer), text[index + 1 :].lstrip()


# --------------------------------------------------------------------------- #
# The vocabulary is closed
# --------------------------------------------------------------------------- #


def test_every_plan_event_family_is_in_the_vocabulary():
    # Plan §24's list, verbatim. If the plan grows a family this fails, which is
    # the point: the recommended set and the emitted set are one thing.
    assert set(EVENTS) == {
        "run.started",
        "preflight.failed",
        "repository.resolved",
        "repository.queued",
        "repository.skipped",
        "download.started",
        "download.completed",
        "hash.started",
        "hash.completed",
        "verification.completed",
        "dependency.undeclared",
        "publication.completed",
        "retention.pruned",
        "retention.deferred",
        "quarantine.cleaned",
        "repository.failed",
        "run.completed",
    }


def test_an_unknown_event_name_is_a_programming_error(stream: io.StringIO):
    # Not a silently-dropped line. A name outside the vocabulary is a typo, and a
    # typo that reaches a journal is one nobody's filter will ever match.
    with pytest.raises(ValueError, match="not a known event"):
        emit("repository.resolve")
    assert stream.getvalue() == ""


@pytest.mark.parametrize("name", [*EVENTS, *DEBUG_EVENTS])
def test_every_declared_event_can_be_emitted(name: str, stream: io.StringIO):
    configure(stream=stream, verbose=1, run_id="0" * 32)
    emit(name, repository="model:organization/name")
    assert fields(stream.getvalue())["event"] == name


# --------------------------------------------------------------------------- #
# Levels
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("verbose", "quiet", "expected"),
    [
        (0, False, stdlib_logging.INFO),
        (1, False, stdlib_logging.DEBUG),
        (3, False, stdlib_logging.DEBUG),
        (0, True, stdlib_logging.WARNING),
        (2, True, stdlib_logging.WARNING),
    ],
)
def test_verbosity_selects_a_level(verbose: int, quiet: bool, expected: int):  # noqa: FBT001 - the parametrized case is the argument
    # `--quiet` wins over `--verbose`: `docs/cli.md` §1 makes quiet the stronger
    # statement, and an operator who passed both meant the suppression.
    assert level_for(verbose=verbose, quiet=quiet) == expected


def test_the_default_level_emits_the_families_and_hides_the_detail(stream: io.StringIO):
    emit("run.started", command="sync")
    emit("capacity.evaluated", needed_bytes=1)
    lines = stream.getvalue().splitlines()
    assert [fields(line)["event"] for line in lines] == ["run.started"]


def test_verbose_adds_the_debug_detail(stream: io.StringIO):
    configure(stream=stream, verbose=1, run_id="0" * 32)
    emit("run.started", command="sync")
    emit("capacity.evaluated", needed_bytes=1)
    lines = stream.getvalue().splitlines()
    assert [fields(line)["event"] for line in lines] == ["run.started", "capacity.evaluated"]


def test_quiet_keeps_warnings_and_errors(stream: io.StringIO):
    configure(stream=stream, quiet=True, run_id="0" * 32)
    emit("run.started", command="sync")
    emit("dependency.undeclared", detected="organization/base")
    emit("repository.failed", codes="HFHUB004")
    levels = [fields(line)["level"] for line in stream.getvalue().splitlines()]
    # The informational line is gone; the two an operator has to see are not.
    assert levels == ["warning", "error"]


def test_retention_deferred_is_a_warning_and_pruned_is_not(stream: io.StringIO):
    emit("retention.pruned", commit_sha="a" * 40)
    emit("retention.deferred", tombstone=".store/trash/x")
    assert [fields(line)["level"] for line in stream.getvalue().splitlines()] == ["info", "warning"]


# --------------------------------------------------------------------------- #
# The run id
# --------------------------------------------------------------------------- #


def test_every_event_carries_the_run_id(stream: io.StringIO):
    for name in EVENTS:
        emit(name)
    lines = stream.getvalue().splitlines()
    assert len(lines) == len(EVENTS)
    assert {fields(line)["run_id"] for line in lines} == {"0" * 32}


def test_configure_binds_a_run_id_when_none_is_given():
    reset()
    assert current_run_id() is None
    configure(stream=io.StringIO())
    assert current_run_id() is not None
    reset()


def test_binding_a_run_renames_subsequent_events(stream: io.StringIO):
    emit("run.started", command="sync")
    bind_run("f" * 32)
    emit("run.completed", command="sync")
    first, second = (fields(line)["run_id"] for line in stream.getvalue().splitlines())
    assert (first, second) == ("0" * 32, "f" * 32)


def test_delayed_record_formatting_uses_emission_context(stream, monkeypatch):
    logger = stdlib_logging.getLogger(LOGGER_NAME)
    handler = logger.handlers[0]
    records = []
    monkeypatch.setattr(handler, "emit", records.append)
    with scoped_context(run_id="a" * 32, request_id="b" * 32):
        emit("run.started")
    with scoped_context(run_id="c" * 32):
        rendered = fields(handler.format(records[0]))
    assert rendered["run_id"] == "a" * 32
    assert rendered["request_id"] == "b" * 32


def test_an_unbound_run_still_produces_a_parseable_line(stream: io.StringIO):
    bind_run(None)
    emit("run.started", command="sync")
    assert fields(stream.getvalue())["run_id"] == "-"


# --------------------------------------------------------------------------- #
# Secrets (`docs/security.md` T-07, plan §24)
# --------------------------------------------------------------------------- #

TOKEN = "hf_ABCdef0123456789ABCdef0123456789ABCd"


def test_a_token_pushed_through_a_field_never_reaches_the_output(stream: io.StringIO):
    # The test plan §24 asks for: push a real-shaped token through and search the
    # output for it. Through a field named for what it is...
    emit("run.started", token=TOKEN)
    # ...and through one that hides it, which is the case the key list misses.
    emit("run.completed", detail=f"failed while using {TOKEN}")
    output = stream.getvalue()
    assert TOKEN not in output
    assert output.count(REDACTED) == 2


@pytest.mark.parametrize(
    "key",
    ["token", "Authorization", "PASSWORD", "secret", "api_key", "cookie", "credential", "header"],
)
def test_a_secret_field_name_is_redacted_whatever_it_holds(key: str, stream: io.StringIO):
    # Matched case-insensitively, because the caller picks the keyword and
    # `Authorization` is the spelling anyone reaching for that name would use.
    emit("run.started", **{key: "anything at all"})
    assert fields(stream.getvalue())[key] == REDACTED
    assert "anything at all" not in stream.getvalue()


@pytest.mark.parametrize(
    "value",
    [
        "Bearer sk-not-a-real-secret",
        "https://cdn-lfs.hf.co/repos/x/model.safetensors?X-Amz-Signature=deadbeef",
        "https://example.invalid/f?token=abc123",
        "https://storage.googleapis.com/b/o?X-Goog-Signature=aa",
    ],
)
def test_a_secret_shaped_value_is_redacted_under_an_innocent_name(value: str, stream: io.StringIO):
    emit("download.completed", location=value)
    assert fields(stream.getvalue())["location"] == REDACTED


def test_an_ordinary_url_is_not_redacted(stream: io.StringIO):
    # Over-redaction has a cost too: an endpoint an operator cannot read is a
    # line that does not help. Only a *signed* URL is a secret.
    emit("run.started", endpoint="https://huggingface.co")
    assert fields(stream.getvalue())["endpoint"] == "https://huggingface.co"


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "value",
    [
        "plain",
        "",
        "has space",
        "has=equals",
        'has"quote',
        "has\\backslash",
        "has\nnewline",
    ],
)
def test_values_survive_a_round_trip(value: str, stream: io.StringIO):
    # Whatever the quoting rule is, parsing the line back has to return what went
    # in — that is the only property a log consumer depends on. A newline matters
    # most: unescaped, one field would become two journal entries.
    emit("run.started", detail=value)
    assert fields(stream.getvalue())["detail"] == value
    assert len(stream.getvalue().splitlines()) == 1


def test_fields_are_ordered_so_two_runs_read_the_same(stream: io.StringIO):
    emit("run.started", zulu=1, alpha=2, mike=3)
    assert stream.getvalue().split("run_id=")[1].split(" ", 1)[1].strip() == (
        "alpha=2 mike=3 zulu=1"
    )


def test_a_record_logged_without_the_extras_still_renders(stream: io.StringIO):
    # Nothing in the application does this, but a dependency that grabbed the
    # `hfcache` logger would, and a formatter that raised on it would take the
    # run down over a log line.
    stdlib_logging.getLogger(LOGGER_NAME).warning("something happened")
    assert fields(stream.getvalue())["event"] == "something happened"


# --------------------------------------------------------------------------- #
# Handler management
# --------------------------------------------------------------------------- #


def test_configure_replaces_rather_than_accumulates(stream: io.StringIO):
    second = io.StringIO()
    configure(stream=second, run_id="0" * 32)
    emit("run.started", command="sync")
    # One line, in one place. Configuring twice must not double every event.
    assert stream.getvalue() == ""
    assert len(second.getvalue().splitlines()) == 1


def test_events_do_not_propagate_to_the_root_logger(stream: io.StringIO):
    root = io.StringIO()
    handler = stdlib_logging.StreamHandler(root)
    stdlib_logging.getLogger().addHandler(handler)
    try:
        emit("run.started", command="sync")
    finally:
        stdlib_logging.getLogger().removeHandler(handler)
    # A dependency that configured root logging must not be able to duplicate
    # these onto stdout, which is where the JSON envelope lives.
    assert root.getvalue() == ""


def test_reset_leaves_no_handler_behind():
    configure(stream=io.StringIO())
    reset()
    assert stdlib_logging.getLogger(LOGGER_NAME).handlers == []
    assert current_run_id() is None


def test_configure_defaults_to_stderr(capsys: pytest.CaptureFixture[str]):
    configure(run_id="0" * 32)
    try:
        emit("run.started", command="sync")
    finally:
        reset()
    captured = capsys.readouterr()
    # stdout is reserved for the envelope (`docs/cli.md` §4).
    assert captured.out == ""
    assert fields(captured.err)["event"] == "run.started"


# --------------------------------------------------------------------------- #
# systemd
# --------------------------------------------------------------------------- #


def test_under_systemd_reads_the_invocation_id(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("INVOCATION_ID", raising=False)
    assert under_systemd() is False
    monkeypatch.setenv("INVOCATION_ID", "c0a12f5f43ea4f7281f5689724927971")
    assert under_systemd() is True


def test_a_syslog_priority_prefix_is_added_only_under_systemd(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("INVOCATION_ID", "c0a12f5f43ea4f7281f5689724927971")
    captured = io.StringIO()
    configure(stream=captured, run_id="0" * 32)
    try:
        emit("run.started", command="sync")
        emit("repository.failed", codes="HFHUB004")
    finally:
        reset()
    # journald turns these into PRIORITY, which is what makes
    # `journalctl -p err -u hfcache-sync.service` select failures.
    info, error = captured.getvalue().splitlines()
    assert info.startswith("<6>event=run.started")
    assert error.startswith("<3>event=repository.failed")


def test_no_prefix_when_an_operator_runs_it(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("INVOCATION_ID", raising=False)
    captured = io.StringIO()
    configure(stream=captured, run_id="0" * 32)
    try:
        emit("run.started", command="sync")
    finally:
        reset()
    assert captured.getvalue().startswith("event=run.started")


# --------------------------------------------------------------------------- #
# The CLI wiring
# --------------------------------------------------------------------------- #


def test_the_envelope_and_the_log_name_the_same_run(config_file: Path):
    # §24 wants the run id in every event; §4 wants it in the envelope. A command
    # that writes no durable report used to mint a second id for the envelope,
    # which gave an operator two identifiers and no way to join them.
    result = CliRunner().invoke(
        app, ["--json", "--config", str(config_file), "config", "validate", "--local"]
    )

    assert result.exit_code == 0
    assert json.loads(result.stdout)["run_id"] == current_run_id()
