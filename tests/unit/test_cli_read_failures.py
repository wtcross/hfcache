"""Read presentation must not replace original failed Envelopes with a traceback."""

import json

import httpx
import pytest
from typer.testing import CliRunner

from hfcache import cli, cli_client
from hfcache.client import ApiClient
from hfcache.reporting import Envelope
from tests.unit.test_api_client_adversarial import _read
from tests.unit.test_cli_client_describe import _capabilities
from tests.unit.test_cli_client_describe import settings as client_settings  # noqa: F401


@pytest.fixture
def settings(request):
    return request.getfixturevalue("client_settings")


def _remote(monkeypatch, payload, *, writer=False):
    requests = []

    def handle(request):
        requests.append(request)
        assert request.method == "GET"
        return httpx.Response(
            200,
            json=_capabilities("rest-writer" if writer else "rest-reader")
            if request.url.path.endswith("capabilities")
            else payload,
        )

    monkeypatch.setattr(
        cli_client,
        "ApiClient",
        lambda config: ApiClient(config, transport=httpx.MockTransport(handle)),
    )
    return requests


def _failed(command, data):
    payload = _read(data=data)
    payload["envelope"].update(
        command=command,
        exit_code=20,
        outcome="failed",
        errors=[
            {
                "code": "HFAPI003",
                "message": "Original read refusal",
                "context": {},
                "repository": None,
            }
        ],
    )
    return payload


@pytest.mark.parametrize("machine", [False, True])
@pytest.mark.parametrize(
    "case",
    [
        (["verify", "--estimate"], "verify --estimate", {"repositories": 3}),
        (["list"], "list", {"repositories": [{}]}),
        (["list", "--revisions"], "list", {"repositories": [{}]}),
        (["archive", "init", "--inspect"], "archive init", {"state": "unknown"}),
        (
            ["archive", "init", "--inspect", "--archive-root", "/different-fixture-root"],
            "archive init",
            {"archive_root": "/fixture-root"},
        ),
    ],
)
def test_failed_read_partial_payload_preserves_original_envelope(
    settings, monkeypatch, machine, case
):
    arguments, command, data = case
    selected, _token = settings
    payload = _failed(command, data)
    requests = _remote(monkeypatch, payload)
    result = CliRunner().invoke(
        cli.app, [*(["--json"] if machine else []), "--client-config", str(selected), *arguments]
    )
    assert result.exit_code == 20, result.exception
    assert "HFAPI003" in result.stderr
    assert "Original read refusal" in result.stderr
    if machine:
        assert json.loads(result.stdout) == payload["envelope"]
    assert all(request.method == "GET" for request in requests)


@pytest.mark.parametrize("machine", [False, True])
@pytest.mark.parametrize("checks", [[{}], "malformed", [{"name": 12}]])
def test_failed_doctor_malformed_partial_checks_preserves_original_envelope(
    settings, monkeypatch, machine, checks
):
    selected, _token = settings
    payload = _failed("doctor", {"checks": checks})
    _remote(monkeypatch, payload)
    monkeypatch.setattr(
        cli, "_submit", lambda *_a, **_k: Envelope.model_validate(payload["envelope"])
    )
    result = CliRunner().invoke(
        cli.app,
        [
            *(["--json"] if machine else []),
            "--client-config",
            str(selected),
            "doctor",
            "--read-only",
        ],
    )
    assert result.exit_code == 20, result.exception
    assert "HFAPI003" in result.stderr
    if machine:
        assert json.loads(result.stdout) == payload["envelope"]


def test_human_partial_doctor_retains_valid_checks_without_registered_credential(
    settings, monkeypatch
):
    selected, token = settings
    secret = token.read_text()
    payload = _failed(
        "doctor", {"checks": [{"name": "configuration", "outcome": "fail", "detail": secret}]}
    )
    _remote(monkeypatch, payload)
    monkeypatch.setattr(
        cli, "_submit", lambda *_a, **_k: Envelope.model_validate(payload["envelope"])
    )
    result = CliRunner().invoke(
        cli.app, ["--client-config", str(selected), "doctor", "--read-only"]
    )
    assert result.exit_code == 20, result.exception
    assert "configuration" in result.stdout
    assert "fail" in result.stdout
    assert secret not in result.output


@pytest.mark.parametrize("failed", [False, True])
@pytest.mark.parametrize(
    "case",
    [
        (["sync"], "sync", {"repositories": [{}]}),
        (["plan"], "plan", {"repositories": [{}]}),
        (["verify", "--full"], "verify --full", {"report": "fixture-report"}),
        (["prune", "--dry-run"], "prune --dry-run", {"plans": [{}]}),
        (["purge", "--dry-run", "--all-unmanaged"], "purge --dry-run", {"plans": [{}]}),
        (["recover", "--dry-run"], "recover --dry-run", {"actionable": 1}),
        (["quarantine", "--dry-run", "a" * 32], "quarantine --dry-run", {"plans": [{}]}),
        (["repair", "model:example/model@" + "a" * 40], "repair", {"commit_sha": "a" * 40}),
        (["catalog", "refresh"], "catalog refresh", {"repositories": [{}], "counts": {}}),
    ],
)
def test_json_terminal_results_never_depend_on_human_job_formatter_fields(
    settings, monkeypatch, failed, case
):
    arguments, command, data = case
    selected, _token = settings
    payload = _failed(command, data)
    if not failed:
        payload["envelope"].update(exit_code=0, outcome="success", errors=[])
    _remote(monkeypatch, payload, writer=True)
    observed = []

    def terminal(_client, route, body, **_options):
        observed.append((route, body))
        return Envelope.model_validate(payload["envelope"])

    monkeypatch.setattr(cli_client, "submit_job", terminal)
    monkeypatch.setattr(
        cli,
        "load_config",
        lambda *_a, **_k: pytest.fail("JSON terminal display opened writer policy"),
    )
    result = CliRunner().invoke(cli.app, ["--json", "--client-config", str(selected), *arguments])
    assert result.exit_code == (20 if failed else 0), result.exception
    assert json.loads(result.stdout) == payload["envelope"]
    assert len(observed) == 1
