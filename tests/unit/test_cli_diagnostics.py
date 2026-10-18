"""Public CLI diagnostics preserve exact remote results and observation handles."""

import copy
import json
import sys
from contextlib import contextmanager
from typing import Any, cast

import httpx
import pytest
from typer.testing import CliRunner

from hfcache import cli, cli_client
from hfcache.client import ApiClient
from tests.unit.test_api_client_adversarial import (
    BASE,
    OPERATION,
    TOKEN,
    _accepted,
    _capabilities,
    _envelope,
    _operation,
    _read,
    _response,
)
from tests.unit.test_cli_operation_helpers import _events

FLAGS = ((), ("--quiet",), ("--json",), ("--quiet", "--json"))
WARNING = {"code": "HFDEP001", "message": "fixture warning", "repository": None, "context": {}}
ERROR = {"code": "HFHUB004", "message": "fixture failure", "repository": None, "context": {}}


class TerminalRunner(CliRunner):
    """Give the real command's captured streams an explicit terminal identity."""

    def __init__(self, *, terminal=False):
        super().__init__()
        self.terminal = terminal

    @contextmanager
    def isolation(self, *args, **kwargs):
        with super().isolation(*args, **kwargs) as streams, pytest.MonkeyPatch.context() as patch:
            patch.setattr(sys.stdout, "isatty", lambda: self.terminal)
            patch.setattr(sys.stderr, "isatty", lambda: self.terminal)
            yield streams


@pytest.fixture
def transport_cli(tmp_path, monkeypatch):
    token = tmp_path / "api.token"
    token.write_text(TOKEN)
    token.chmod(0o600)
    settings = tmp_path / "client.toml"
    settings.write_text("schema_version=1\n")
    requests = []
    state = {"envelope": _envelope(), "truncated": False}

    def respond(request):
        requests.append((request.method, request.url.path))
        path = request.url.path
        document: dict[str, Any]
        if path.endswith("/capabilities"):
            document = _capabilities()
            cast("dict[str, Any]", document["envelope"]["data"]).update(
                credential_class="rest-writer", capabilities=["read", "write"]
            )
        elif request.method == "POST":
            document = _accepted()
            return _response(
                document, status=202, headers={"Location": document["links"]["status"]}
            )
        elif path.endswith("/events"):
            after = int(request.url.params.get("after", "0"))
            sequence = 5 if state["truncated"] else 1
            document = _events(
                [sequence] if not after else [],
                oldest=sequence,
                truncated=bool(state["truncated"] and not after),
                after=after,
            )
            for event in document["envelope"]["data"]["events"]:
                event["message"] = "fixture progress"
        elif path.endswith(("/result", "/status", "/version")):
            document = _read()
            document["envelope"] = state["envelope"]
        else:
            operation = _operation(
                state="failed" if state["envelope"]["exit_code"] else "succeeded"
            )
            document = _read(data={"operation": operation})
        return _response(document)

    monkeypatch.setattr(
        cli_client,
        "ApiClient",
        lambda config: ApiClient(
            config, transport=httpx.MockTransport(respond), sleep=lambda _: None
        ),
    )

    def forbidden(*args, **kwargs):
        pytest.fail("operational CLI attempted local archive policy access")

    monkeypatch.setattr(cli, "load_config", forbidden)

    def invoke(envelope, arguments, *, terminal=False, color=False, truncated=False):
        state.update(envelope=copy.deepcopy(envelope), truncated=truncated)
        requests.clear()
        result = TerminalRunner(terminal=terminal).invoke(
            cli.app,
            [
                "--client-config",
                str(settings),
                "--api-url",
                BASE,
                "--api-token-file",
                str(token),
                *arguments,
            ],
            color=color,
        )
        if result.exception is not None and not isinstance(result.exception, SystemExit):
            raise result.exception
        return result

    return invoke, requests


def terminal_result(*, partial=False):
    envelope = _envelope(
        data={
            "report": "runs/fixture.json",
            "exit_code": 30 if partial else 0,
            "repositories": [
                {
                    "repository_type": "model",
                    "repository_id": "owner/published",
                    "status": "published",
                    "resolved_commit_sha": "a" * 40,
                },
                {
                    "repository_type": "model",
                    "repository_id": "owner/failed" if partial else "owner/warned",
                    "status": "failed" if partial else "completed_with_warnings",
                    "resolved_commit_sha": None,
                },
            ],
        }
    )
    envelope.update(
        command="sync",
        exit_code=30 if partial else 0,
        outcome="failed" if partial else "success_with_warnings",
        warnings=[WARNING],
        errors=[ERROR] if partial else [],
    )
    return envelope


@pytest.mark.parametrize("flags", FLAGS)
@pytest.mark.parametrize("partial", [False, True])
def test_remote_diagnostics_survive_quiet_and_json(transport_cli, flags, partial):
    invoke, requests = transport_cli
    envelope = terminal_result(partial=partial)
    result = invoke(envelope, [*flags, "sync"])
    assert result.exit_code == (30 if partial else 0), result.output
    assert "HFDEP001" in result.stderr
    assert "fixture warning" in result.stderr
    assert ("HFHUB004" in result.stderr) is partial
    assert "Idempotency key:" in result.stderr
    assert OPERATION in result.stderr
    assert sum(method == "POST" for method, _ in requests) == 1
    if "--json" in flags:
        assert len(result.stdout.splitlines()) == 1
        assert json.loads(result.stdout) == envelope
    elif "--quiet" in flags:
        assert result.stdout == ""
    else:
        assert "owner/published" in result.stdout


@pytest.mark.parametrize("flags", FLAGS)
def test_successful_status_retains_warning_and_degraded_diagnostics(transport_cli, flags):
    invoke, _ = transport_cli
    envelope = _envelope(
        data={
            "archive": {"verification": {"degraded": True, "outstanding_failures": 2}},
            "repositories": [
                {
                    "repository_type": "model",
                    "repository_id": "owner/model",
                    "managed": True,
                    "enabled": True,
                    "verification_state": "verified",
                }
            ],
        }
    )
    envelope.update(outcome="success_with_warnings", warnings=[WARNING])
    result = invoke(envelope, [*flags, "status"])
    assert result.exit_code == 0, result.output
    assert "HFDEP001" in result.stderr
    assert "archive degraded: 2" in result.stderr
    if "--json" in flags:
        assert json.loads(result.stdout) == envelope
    elif "--quiet" in flags:
        assert result.stdout == ""
    else:
        assert "owner/model" in result.stdout


@pytest.mark.parametrize("terminal", [False, True])
@pytest.mark.parametrize("quiet", [False, True])
def test_progress_requires_terminal_and_retains_diagnostics(transport_cli, terminal, quiet):
    invoke, _ = transport_cli
    flags = ["--quiet"] if quiet else []
    result = invoke(terminal_result(), [*flags, "sync"], terminal=terminal)
    assert result.exit_code == 0, result.output
    assert ("fixture progress" in result.stderr) is (terminal and not quiet)
    assert OPERATION in result.stderr
    assert "HFDEP001" in result.stderr


def test_nonterminal_quiet_retains_event_gap_notice(transport_cli):
    invoke, _ = transport_cli
    result = invoke(terminal_result(), ["--quiet", "sync"], truncated=True)
    assert "Event history gap" in result.stderr


@pytest.mark.parametrize("json_output", [False, True])
def test_quiet_local_version_needs_no_client_or_policy(monkeypatch, json_output):
    def forbidden(*args, **kwargs):
        pytest.fail("local version attempted policy or API access")

    monkeypatch.setattr(cli_client, "connect", forbidden)
    monkeypatch.setattr(cli, "load_config", forbidden)
    arguments = ["--quiet", *(["--json"] if json_output else []), "version"]
    result = CliRunner().invoke(cli.app, arguments)
    assert result.exit_code == 0
    if json_output:
        assert json.loads(result.stdout)["command"] == "version"
    else:
        assert result.stdout == ""


@pytest.mark.parametrize(
    "arguments",
    [
        ["--no-color", "--help"],
        ["--help", "--no-color"],
        ["--no-color", "config", "validate", "--help"],
    ],
)
def test_no_color_applies_before_explicit_help(arguments, monkeypatch):
    monkeypatch.setenv("FORCE_COLOR", "1")
    monkeypatch.setenv("TERM", "xterm-256color")
    control = TerminalRunner(terminal=True).invoke(cli.app, ["--help"], color=True)
    assert "\x1b[" in control.stdout
    result = TerminalRunner(terminal=True).invoke(cli.app, arguments, color=True)
    assert result.exit_code == 0, result.output
    assert "Usage:" in result.stdout
    assert "\x1b" not in result.output


def test_no_color_strips_human_output_without_changing_later_invocations(transport_cli):
    invoke, _ = transport_cli
    envelope = _envelope(data={"application": "\x1b[31mcolored\x1b[0m"})
    envelope["command"] = "version"
    colored = invoke(envelope, ["version", "--server"], terminal=True, color=True)
    plain = invoke(envelope, ["--no-color", "version", "--server"], terminal=True, color=True)
    colored_again = invoke(envelope, ["version", "--server"], terminal=True, color=True)
    assert "\x1b[31m" in colored.stdout
    assert "\x1b" not in plain.stdout
    assert "colored" in plain.stdout
    assert "\x1b[31m" in colored_again.stdout
