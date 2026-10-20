"""Run reads retain exact REST pages and durable identities (decision 136)."""

import json
from typing import Any

import httpx
import pytest
from typer.testing import CliRunner

from hfcache import cli, cli_client
from hfcache.client import ApiClient
from hfcache.reporting import RecoveryReport
from tests.fixtures import examples
from tests.unit.test_api_client_adversarial import _read
from tests.unit.test_cli_client_describe import _capabilities
from tests.unit.test_cli_client_describe import settings as client_settings  # noqa: F401 - fixture

PREFIX = "Run read metadata: "
NEXT = "YWJjOjE="


@pytest.fixture
def settings(request):
    return request.getfixturevalue("client_settings")


def _page(runs=None, cursor=None) -> dict[str, Any]:
    payload = _read(data={"runs": [examples.RUN] if runs is None else runs}, cursor=cursor)
    payload["envelope"]["command"] = "runs"
    return payload


def _detail() -> dict[str, Any]:
    payload = _read(data={"report": examples.run_report().model_dump(mode="json")})
    payload["envelope"].update(command="runs read", run_id=examples.RUN)
    return payload


def _invoke(selected, *arguments, flags=()):
    return CliRunner().invoke(
        cli.app, ["--json", "--client-config", str(selected), *flags, "runs", *arguments]
    )


def _remote(monkeypatch, token, payload, *, page_size=100):
    requests = []

    def handle(request):
        requests.append(request)
        assert request.method == "GET"
        assert request.headers["authorization"] == "Bearer " + token.read_text()
        assert "idempotency-key" not in request.headers
        if request.url.path.endswith("capabilities"):
            capabilities = _capabilities("rest-reader")
            capabilities["envelope"]["data"]["max_page_size"] = page_size
            return httpx.Response(200, json=capabilities)
        return httpx.Response(200, json=payload)

    monkeypatch.setattr(
        cli_client,
        "ApiClient",
        lambda config: ApiClient(config, transport=httpx.MockTransport(handle)),
    )
    return requests


def _metadata(result):
    lines = [line for line in result.stderr.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1
    assert len(lines[0].encode("utf-8")) <= 2048
    return json.loads(lines[0][len(PREFIX) :])


def test_runs_list_is_one_exact_page_with_bound_metadata_and_no_archive_access(
    settings, monkeypatch
):
    selected, token = settings
    payload = _page(cursor=NEXT)
    requests = _remote(monkeypatch, token, payload)
    monkeypatch.setattr(
        cli, "load_config", lambda *_a, **_k: pytest.fail("REST report read opened local archive")
    )
    result = _invoke(selected, "list", "--limit", "1")
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout) == payload["envelope"]
    assert _metadata(result) == {
        "schema_version": 1,
        "command": "runs",
        "run_id": payload["envelope"]["run_id"],
        "request_id": payload["request_id"],
        "archive_id": payload["archive_id"],
        "config_fingerprint": payload["config_fingerprint"],
        "next_cursor": NEXT,
    }
    assert [(row.url.path, dict(row.url.params)) for row in requests] == [
        ("/management/api/v1/capabilities", {}),
        ("/management/api/v1/runs", {"limit": "1"}),
    ]


@pytest.mark.parametrize("page_size", [1, 50, 100, 200])
def test_default_page_limit_respects_authenticated_server_limit(settings, monkeypatch, page_size):
    selected, token = settings
    requests = _remote(monkeypatch, token, _page(), page_size=page_size)
    result = _invoke(selected, "list")
    assert result.exit_code == 0, result.output
    assert requests[-1].url.params["limit"] == str(min(100, page_size))


@pytest.mark.parametrize("arguments", [("list",), ("show", "--", examples.RUN)])
def test_quiet_reads_still_emit_one_notice_and_original_envelope(settings, monkeypatch, arguments):
    selected, token = settings
    payload = _page([]) if arguments[0] == "list" else _detail()
    _remote(monkeypatch, token, payload)
    result = _invoke(selected, *arguments, flags=("--quiet",))
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout) == payload["envelope"]
    assert _metadata(result)["next_cursor"] is None
    if arguments[0] == "show":
        # The report is historical; current policy fingerprint is independent.
        assert (
            payload["envelope"]["data"]["report"]["config_fingerprint"]
            != payload["config_fingerprint"]
        )


@pytest.mark.parametrize("mode", ["list", "show"])
@pytest.mark.parametrize("stage", ["capabilities", "target"])
def test_failed_reads_preserve_original_codes_and_envelopes(settings, monkeypatch, mode, stage):
    selected, _token = settings
    payload = _page() if mode == "list" else _detail()
    failure = _capabilities() if stage == "capabilities" else payload
    failure["envelope"].update(
        exit_code=40,
        outcome="failed",
        data={},
        errors=[
            {"code": "HFVER007", "message": "Original refusal", "repository": None, "context": {}}
        ],
    )
    calls = []

    def handle(request):
        calls.append(request)
        return httpx.Response(
            200,
            json=failure
            if stage == "capabilities" or not request.url.path.endswith("capabilities")
            else _capabilities(),
        )

    monkeypatch.setattr(
        cli_client,
        "ApiClient",
        lambda config: ApiClient(config, transport=httpx.MockTransport(handle)),
    )
    result = _invoke(selected, mode, *(["--", examples.RUN] if mode == "show" else []))
    assert result.exit_code == 40, result.output
    assert json.loads(result.stdout) == failure["envelope"]
    assert PREFIX not in result.stderr
    assert len(calls) == (1 if stage == "capabilities" else 2)


@pytest.mark.parametrize(
    "arguments",
    [
        ("list", "--limit", "0"),
        ("list", "--limit", "10001"),
        ("list", "--cursor="),
        ("list", "--cursor=has space"),
        ("list", "--cursor=has\nnewline"),
        ("list", "--cursor=" + "X" * 257),
        ("show", "--", "../SYNTHETIC_SECRET_PATH"),
        ("show", "--", "https://SYNTHETIC_SECRET.invalid"),
        ("show", "--", "--help"),
        ("show", "--", "A" * 32),
        ("show", "--", "a" * 31),
    ],
)
def test_invalid_run_read_arguments_refuse_without_settings_access(
    tmp_path, monkeypatch, arguments
):
    monkeypatch.setattr(
        cli_client,
        "resolve_client_config",
        lambda *_a, **_k: pytest.fail("Invalid input read settings"),
    )
    result = _invoke(tmp_path / "absent.toml", *arguments)
    assert result.exit_code == 10, result.output
    assert json.loads(result.stdout)["errors"][0]["code"] in {"HFARG001", "HFARG002"}
    assert "SYNTHETIC_SECRET" not in result.output


@pytest.mark.parametrize("mode", ["list", "show"])
@pytest.mark.parametrize(
    "flags",
    [
        ("--detach",),
        ("--idempotency-key", "forbidden"),
        ("--wait-timeout", "5"),
        ("--expected-client-scope", "a" * 64),
        ("--config", "/missing/forbidden-candidate"),
        ("--token-file", "/missing/forbidden-hub-credential"),
    ],
)
def test_reports_reject_candidate_and_job_modes_before_credential_access(
    tmp_path, monkeypatch, mode, flags
):
    monkeypatch.setattr(
        cli_client,
        "resolve_client_config",
        lambda *_a, **_k: pytest.fail("Invalid mode read settings"),
    )
    result = _invoke(
        tmp_path / "absent.toml", mode, *([examples.RUN] if mode == "show" else []), flags=flags
    )
    assert result.exit_code == 10, result.output
    assert json.loads(result.stdout)["errors"][0]["code"] == "HFARG002"


@pytest.mark.parametrize(
    "change",
    [
        "command",
        "missing",
        "wrong-type",
        "duplicate",
        "bad-id",
        "extra",
        "over-page",
        "empty-cursor",
        "cursor-loop",
        "unsafe-cursor",
        "unknown-archive",
        "unknown-policy",
    ],
)
def test_malformed_list_success_is_classified_without_partial_notice(settings, monkeypatch, change):
    selected, token = settings
    payload = _page(cursor=NEXT)
    data = payload["envelope"]["data"]
    if change == "command":
        payload["envelope"]["command"] = "status"
    elif change == "missing":
        data.clear()
    elif change == "wrong-type":
        data["runs"] = examples.RUN
    elif change == "duplicate":
        data["runs"] *= 2
    elif change == "bad-id":
        data["runs"] = ["../SYNTHETIC_SECRET_PATH"]
    elif change == "extra":
        data["extra"] = "SYNTHETIC_SECRET"
    elif change == "over-page":
        data["runs"] = [examples.RUN, "e" * 32]
    elif change == "empty-cursor":
        data["runs"] = []
    elif change == "unsafe-cursor":
        payload["next_cursor"] = "SYNTHETIC_SECRET\nmore"
    elif change == "unknown-archive":
        payload["archive_id"] = None
    elif change == "unknown-policy":
        payload["config_fingerprint"] = None
    requests = _remote(monkeypatch, token, payload)
    arguments = ["list", "--limit", "1"]
    if change == "cursor-loop":
        arguments += ["--cursor=" + NEXT]
    result = _invoke(selected, *arguments)
    assert result.exit_code == 10, result.output
    assert json.loads(result.stdout)["errors"][0]["code"] == "HFAPI018"
    assert PREFIX not in result.stderr
    assert "SYNTHETIC_SECRET" not in result.output
    assert len(requests) == 2


@pytest.mark.parametrize(
    "change",
    [
        "command",
        "missing",
        "not-model",
        "extra",
        "wrong-run",
        "wrong-envelope-run",
        "archive",
        "cursor",
        "missing-version",
        "bool-version",
    ],
)
def test_malformed_detail_success_binds_exact_report_and_archive(settings, monkeypatch, change):
    selected, token = settings
    payload = _detail()
    report = payload["envelope"]["data"]["report"]
    if change == "command":
        payload["envelope"]["command"] = "status"
    elif change == "missing":
        payload["envelope"]["data"] = {}
    elif change == "not-model":
        report.clear()
    elif change == "extra":
        report["arbitrary"] = "SYNTHETIC_SECRET"
    elif change == "wrong-run":
        report["run_id"] = "e" * 32
    elif change == "wrong-envelope-run":
        payload["envelope"]["run_id"] = "e" * 32
    elif change == "archive":
        report["archive_id"] = "00000000-0000-4000-8000-000000000001"
    elif change == "cursor":
        payload["next_cursor"] = NEXT
    elif change == "missing-version":
        del report["schema_version"]
    elif change == "bool-version":
        report["schema_version"] = True
    _remote(monkeypatch, token, payload)
    result = _invoke(selected, "show", "--", examples.RUN)
    assert result.exit_code == 10, result.output
    assert json.loads(result.stdout)["errors"][0]["code"] == "HFAPI018"
    assert PREFIX not in result.stderr
    assert "SYNTHETIC_SECRET" not in result.output


def test_server_page_cap_refuses_before_target_get(settings, monkeypatch):
    selected, token = settings
    requests = _remote(monkeypatch, token, _page(), page_size=1)
    result = _invoke(selected, "list", "--limit", "2")
    assert result.exit_code == 10
    assert json.loads(result.stdout)["errors"][0]["code"] == "HFARG002"
    assert len(requests) == 1


def test_option_like_cursor_is_inert_query_data(settings, monkeypatch):
    selected, token = settings
    requests = _remote(monkeypatch, token, _page())
    result = _invoke(selected, "list", "--cursor=--help")
    assert result.exit_code == 0, result.output
    assert requests[-1].url.params["cursor"] == "--help"


def test_secret_registered_credential_cannot_be_emitted_as_cursor(settings, monkeypatch):
    selected, token = settings
    payload = _page(cursor=token.read_text())
    _remote(monkeypatch, token, payload)
    result = _invoke(selected, "list")
    assert result.exit_code == 10, result.output
    assert PREFIX not in result.stderr
    assert token.read_text() not in result.output


@pytest.mark.parametrize("kind", ["verification", "recovery"])
def test_show_uses_existing_report_models_and_keeps_failed_domain_outcome(
    settings, monkeypatch, kind
):
    selected, token = settings
    report = (
        examples.verification_report()
        if kind == "verification"
        else RecoveryReport.model_validate(
            {
                key: value
                for key, value in examples.run_report().model_dump(mode="json").items()
                if key not in {"repositories", "totals"}
            }
            | {"command": "recover --dry-run", "remediations": []}
        )
    )
    payload = _detail()
    payload["envelope"]["data"]["report"] = report.model_dump(mode="json")
    _remote(monkeypatch, token, payload)
    result = _invoke(selected, "show", "--", examples.RUN)
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout) == payload["envelope"]
    assert _metadata(result)["run_id"] == report.run_id
    if kind == "verification":
        assert json.loads(result.stdout)["data"]["report"]["outcome"] == "failed"
        assert json.loads(result.stdout)["data"]["report"]["exit_code"] == 40


@pytest.mark.parametrize("mode", ["list", "show"])
def test_unavailable_api_is_original_connection_error_without_local_fallback(
    tmp_path, monkeypatch, mode
):
    token, selected = tmp_path / "token", tmp_path / "client.toml"
    token.write_text("synthetic-run-reader-" + "Q" * 40)
    token.chmod(0o600)
    selected.write_text(
        f'schema_version=1\napi_socket="{tmp_path / "missing.sock"}"\n'
        f'api_token_file="{token}"\nread_retries=0\n'
    )
    monkeypatch.setattr(
        cli,
        "load_config",
        lambda *_a, **_k: pytest.fail("Unavailable REST read opened local policy"),
    )
    result = _invoke(selected, mode, *([examples.RUN] if mode == "show" else []))
    assert result.exit_code == 20, result.output
    assert json.loads(result.stdout)["errors"][0]["code"] == "HFAPI019"
    assert PREFIX not in result.stderr


@pytest.mark.parametrize("defect", ["oversized", "duplicate-json-key", "wrong-archive"])
def test_generic_rest_bounds_and_wire_checks_apply_to_reports(settings, monkeypatch, defect):
    selected, _token = settings
    selected.write_text(selected.read_text() + "max_response_bytes=4096\n")
    payload = _detail()
    report = payload["envelope"]["data"]["report"]
    if defect == "oversized":
        report["warnings"] = ["SYNTHETIC_SECRET_" + "X" * 5000]
        report["outcome"] = "success_with_warnings"
    elif defect == "wrong-archive":
        payload["archive_id"] = "00000000-0000-4000-8000-000000000001"
    encoded = json.dumps(payload)
    if defect == "duplicate-json-key":
        encoded = '{"schema_version":1,' + encoded[1:]

    def handle(request):
        return (
            httpx.Response(200, json=_capabilities("rest-reader"))
            if request.url.path.endswith("capabilities")
            else httpx.Response(200, content=encoded, headers={"content-type": "application/json"})
        )

    monkeypatch.setattr(
        cli_client,
        "ApiClient",
        lambda config: ApiClient(config, transport=httpx.MockTransport(handle)),
    )
    result = _invoke(selected, "show", "--", examples.RUN)
    assert result.exit_code == 10, result.output
    assert json.loads(result.stdout)["errors"][0]["code"] == "HFAPI018"
    assert PREFIX not in result.stderr
    assert "SYNTHETIC_SECRET" not in result.output


def test_metadata_refuses_registered_secret_even_when_it_has_valid_identifier_shape(
    settings, monkeypatch
):
    selected, token = settings
    token.write_text("e" * 32)
    payload = _page()
    payload["request_id"] = token.read_text()
    _remote(monkeypatch, token, payload)
    result = _invoke(selected, "list")
    assert result.exit_code == 10, result.output
    assert PREFIX not in result.stderr
    assert token.read_text() not in result.output
