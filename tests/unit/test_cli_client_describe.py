"""Client authority metadata uses authenticated reads, never recovery submission (CP-08)."""

import asyncio
import hashlib
import json
import subprocess
import sys
from typing import Any

import httpx
import pytest
from typer.testing import CliRunner

from hfcache import cli, cli_client
from hfcache.api.app import create_app
from hfcache.client import ApiClient
from hfcache.server import build_server, listeners
from hfcache.server_config import validate_server_config_mapping
from tests.unit.test_api_client_adversarial import _accepted, _read
from tests.unit.test_server_bootstrap import (
    ARCHIVE_ID,
    exercise,
    isolate_logging,  # noqa: F401 - autouse fixture
)
from tests.unit.test_server_bootstrap import policy as socket_policy  # noqa: F401 - fixture


@pytest.fixture
def settings(tmp_path):
    token, selected = tmp_path / "secret-source", tmp_path / "client.toml"
    token.write_text("synthetic-rest-token-" + "Q" * 40)
    token.chmod(0o600)
    selected.write_text(
        'schema_version=1\napi_url="https://Archive.Example:443/management/"\n'
        f'api_token_file="{token}"\nexpected_archive_id="{ARCHIVE_ID}"\nread_retries=0\n'
    )
    return selected, token


def _capabilities(credential_class="rest-writer") -> dict[str, Any]:
    result = _read(
        data={
            "api_version": 1,
            "credential_class": credential_class,
            "capabilities": ["read", "write"] if credential_class == "rest-writer" else ["read"],
            "instance_id": "e" * 32,
            "reads": True,
            "operations": True,
            "operation_history": True,
            "mcp": False,
            "maintenance_enabled": False,
            "max_page_size": 100,
        }
    )
    result["envelope"]["command"] = "capabilities"
    return result


def _version() -> dict[str, Any]:
    result = _read(data={"application_version": "0.2.1"})
    result["envelope"]["command"] = "version"
    return result


def _invoke(selected, *flags, json_output=True):
    arguments = ["--client-config", str(selected), *flags, "client", "describe"]
    if json_output:
        arguments.insert(0, "--json")
    return CliRunner().invoke(cli.app, arguments)


def _process(selected, *arguments) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-I",
            "-m",
            "hfcache",
            "--json",
            "--client-config",
            str(selected),
            *arguments,
        ],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )


@pytest.mark.parametrize("credential_class", ["rest-reader", "rest-writer"])
def test_client_describe_returns_only_validated_nonsecret_authority(
    settings, monkeypatch, credential_class
):
    selected, token = settings
    requests = []

    def handle(request):
        requests.append(request)
        assert request.method == "GET"
        assert request.headers["authorization"] == "Bearer " + token.read_text()
        return httpx.Response(
            200,
            json=_capabilities(credential_class)
            if request.url.path.endswith("capabilities")
            else _version(),
        )

    monkeypatch.setattr(
        cli_client,
        "ApiClient",
        lambda config: ApiClient(config, transport=httpx.MockTransport(handle)),
    )
    result = _invoke(selected)
    assert result.exit_code == 0, result.output
    envelope = json.loads(result.stdout)
    assert envelope["command"] == "client describe"
    assert envelope["exit_code"] == 0
    expected = {
        "metadata_schema_version": 1,
        "profile_fingerprint": hashlib.sha256(
            json.dumps(
                {
                    "metadata_schema_version": 1,
                    "endpoint": "https://archive.example/management",
                    "selected_settings": str(selected),
                    "expected_archive_id": ARCHIVE_ID,
                    "credential_class": credential_class,
                    "ca_file": None,
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest(),
        "endpoint": "https://archive.example/management",
        "credential_class": credential_class,
        "archive_id": ARCHIVE_ID,
        "instance_id": "e" * 32,
    }
    expected["authority_fingerprint"] = hashlib.sha256(
        json.dumps(
            {key: value for key, value in expected.items() if key != "instance_id"},
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
    assert envelope["data"] == expected
    assert [request.url.path for request in requests] == [
        "/management/api/v1/capabilities",
        "/management/api/v1/version",
    ]
    assert len(result.stdout.splitlines()) == 1
    for excluded in (
        str(selected),
        str(token),
        token.read_text(),
        "api_token_file",
        "credential_name",
        "capabilities",
    ):
        assert excluded not in result.stdout


@pytest.mark.parametrize(
    "flags",
    [
        ["--detach"],
        ["--idempotency-key", "do-not-send"],
        ["--wait-timeout", "5"],
        ["--config", "/missing/writer-policy"],
        ["--token-file", "/missing/hub-token"],
    ],
)
def test_client_describe_forbidden_options_refuse_before_any_settings_or_credential_read(
    tmp_path, monkeypatch, flags
):
    def forbidden(*args, **kwargs):
        pytest.fail("read-only metadata opened settings, credentials or writer policy")

    monkeypatch.setattr(cli_client, "resolve_client_config", forbidden)
    monkeypatch.setattr(cli, "load_config", forbidden)
    result = _invoke(tmp_path / "missing-client.toml", *flags)
    assert result.exit_code == 10
    envelope = json.loads(result.stdout)
    assert envelope["command"] == "client describe"
    assert envelope["errors"][0]["code"] == "HFARG002"


@pytest.fixture
def policy(request):
    return request.getfixturevalue("socket_policy")


@pytest.mark.parametrize("role", ["writer", "reader", "wrong"])
def test_actual_cli_describe_uses_only_authenticated_unix_reads_without_archive_access(  # noqa: PLR0915 - one real daemon lifecycle with reader/writer/refusal evidence
    policy, tmp_path, role
):
    token = policy.credentials.writer.file
    if role == "reader":
        token = tmp_path / "reader.token"
        token.write_text("synthetic-reader-token-" + "R" * 40)
        token.chmod(0o600)
        policy = validate_server_config_mapping(
            policy.model_dump(mode="json")
            | {
                "credentials": policy.credentials.model_dump(mode="json")
                | {"reader": {"file": str(token)}}
            }
        )
    elif role == "wrong":
        token = tmp_path / "wrong.token"
        token.write_text("synthetic-wrong-token-" + "X" * 40)
        token.chmod(0o600)
    selected = tmp_path / "client.toml"
    selected.write_text(
        f'schema_version=1\napi_socket="{policy.listener.unix_socket}"\n'
        f'api_token_file="{token}"\nexpected_archive_id="{ARCHIVE_ID}"\nread_retries=0\n'
    )
    application = create_app(policy, instance_lock_path=tmp_path / "daemon.lock")
    observed = []
    keys = []

    @application.middleware("http")
    async def capture(request, call_next):
        observed.append((request.method, request.url.path))
        if "idempotency-key" in request.headers:
            keys.append(request.headers["idempotency-key"])
        return await call_next(request)

    server = build_server(application, policy)
    with listeners(policy.listener) as channels:

        def invoke() -> subprocess.CompletedProcess[str]:
            return _process(selected, "client", "describe")

        async def request():
            result = await asyncio.to_thread(invoke)
            if role == "wrong":
                assert result.returncode == 10, result.stderr
                assert json.loads(result.stdout)["errors"][0]["code"] == "HFAPI001"
                return
            assert result.returncode == 0, result.stderr
            data = json.loads(result.stdout)["data"]
            assert data["endpoint"] == "unix:" + str(policy.listener.unix_socket)
            assert data["archive_id"] == ARCHIVE_ID
            assert data["credential_class"] == (
                "rest-reader" if role == "reader" else "rest-writer"
            )
            assert len(data["instance_id"]) == 32
            assert len(data["profile_fingerprint"]) == 64
            assert str(token) not in result.stdout
            assert token.read_text() not in result.stdout
            assert application.state.operations.list() == ()
            if role == "writer":
                wrong_scope = await asyncio.to_thread(
                    _process,
                    selected,
                    "--expected-client-scope",
                    "f" * 64,
                    "operations",
                    "lookup",
                    "--",
                    "original-key",
                )
                assert wrong_scope.returncode == 10, wrong_scope.stderr
                assert json.loads(wrong_scope.stdout)["errors"][0]["code"] == "HFAPI017"
                assert keys == []
                lookup = await asyncio.to_thread(
                    _process,
                    selected,
                    "--expected-client-scope",
                    data["authority_fingerprint"],
                    "operations",
                    "lookup",
                    "--",
                    "original-key",
                )
                assert lookup.returncode == 20, lookup.stderr
                assert json.loads(lookup.stdout)["errors"][0]["code"] == "HFAPI013"
                assert keys == ["original-key"]
                assert application.state.operations.list() == ()

        asyncio.run(exercise(server, channels, request))
    expected = [("GET", "/api/v1/capabilities")] + (
        [] if role == "wrong" else [("GET", "/api/v1/version")]
    )
    if role == "writer":
        expected += [("GET", "/api/v1/capabilities"), ("GET", "/api/v1/version")] * 2
        expected += [("GET", "/api/v1/capabilities"), ("GET", "/api/v1/operations/lookup")]
    assert observed == expected
    assert not (tmp_path / "archive").exists()
    assert not policy.listener.unix_socket.exists()


@pytest.mark.parametrize("stage", ["capabilities", "version"])
@pytest.mark.parametrize("code", ["HFAPI003", "HFAPI017", "HFAPI018", "HFAPI019"])
def test_describe_preserves_exact_failed_server_envelope(settings, monkeypatch, stage, code):
    selected, _ = settings
    payload = _capabilities() if stage == "capabilities" else _version()
    failure = payload["envelope"]
    failure.update(
        exit_code=20 if code == "HFAPI019" else 10,
        outcome="failed",
        data={},
        errors=[{"code": code, "message": "Synthetic refusal", "repository": None, "context": {}}],
    )
    requests = []

    def handle(request):
        requests.append(request)
        return httpx.Response(
            200, json=payload if request.url.path.endswith(stage) else _capabilities()
        )

    monkeypatch.setattr(
        cli_client,
        "ApiClient",
        lambda config: ApiClient(config, transport=httpx.MockTransport(handle)),
    )
    result = _invoke(selected)
    assert result.exit_code == failure["exit_code"]
    assert json.loads(result.stdout) == failure
    assert all(request.method == "GET" for request in requests)


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://LOCALHOST:80/cache/",
        "http://[::1]:8080/cache/",
        "https://Archive.Example:443/cache/",
    ],
)
def test_describe_canonicalizes_only_already_validated_urls(settings, monkeypatch, endpoint):
    selected, _ = settings
    monkeypatch.setattr(
        cli_client,
        "ApiClient",
        lambda config: ApiClient(
            config,
            transport=httpx.MockTransport(
                lambda request: httpx.Response(
                    200,
                    json=_capabilities()
                    if request.url.path.endswith("capabilities")
                    else _version(),
                )
            ),
        ),
    )
    result = _invoke(selected, "--api-url", endpoint)
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)["data"]["endpoint"] == str(httpx.URL(endpoint)).rstrip("/")


def test_describe_unknown_archive_is_null_and_new_instance_keeps_known_authority(
    settings, monkeypatch
):
    selected, _ = settings
    selected.write_text(selected.read_text().replace(f'expected_archive_id="{ARCHIVE_ID}"\n', ""))
    archive, instance = None, "e" * 32

    def handle(request):
        payload = _capabilities() if request.url.path.endswith("capabilities") else _version()
        payload["archive_id"] = archive
        if request.url.path.endswith("capabilities"):
            payload["envelope"]["data"]["instance_id"] = instance
        return httpx.Response(200, json=payload)

    monkeypatch.setattr(
        cli_client,
        "ApiClient",
        lambda config: ApiClient(config, transport=httpx.MockTransport(handle)),
    )
    unknown = json.loads(_invoke(selected).stdout)["data"]
    assert unknown["archive_id"] is None
    archive = ARCHIVE_ID
    original = json.loads(_invoke(selected).stdout)["data"]
    instance = "f" * 32
    restarted = json.loads(_invoke(selected).stdout)["data"]
    assert original["instance_id"] != restarted["instance_id"]
    assert original["authority_fingerprint"] == restarted["authority_fingerprint"]
    assert original["authority_fingerprint"] != unknown["authority_fingerprint"]


@pytest.mark.parametrize(
    "target",
    [
        ["sync"],
        ["operations", "lookup", "--", "original-key"],
        ["operations", "show", "c" * 32],
        ["operations", "wait", "c" * 32],
    ],
)
@pytest.mark.parametrize("change", ["endpoint", "settings", "credential", "archive", "unknown"])
def test_scope_pin_rechecks_same_client_and_refuses_changed_or_unknown_authority_before_target(
    settings, tmp_path, monkeypatch, target, change
):
    selected, _ = settings
    requests = []
    changed = False

    def handle(request):
        requests.append(request)
        assert request.method == "GET"
        assert request.url.path.endswith(("capabilities", "version")), (
            "Scope mismatch followed a handle or submitted"
        )
        payload = (
            _capabilities("rest-reader" if changed and change == "credential" else "rest-writer")
            if request.url.path.endswith("capabilities")
            else _version()
        )
        if changed and change in {"archive", "unknown"}:
            payload["archive_id"] = (
                None if change == "unknown" else "00000000-0000-4000-8000-000000000001"
            )
        return httpx.Response(200, json=payload)

    monkeypatch.setattr(
        cli_client,
        "ApiClient",
        lambda config: ApiClient(config, transport=httpx.MockTransport(handle)),
    )
    original = json.loads(_invoke(selected).stdout)["data"]["authority_fingerprint"]
    requests.clear()
    changed = True
    flags = []
    if change == "endpoint":
        flags = ["--api-url", "https://different.example/management"]
    elif change == "settings":
        replacement = tmp_path / "different-client.toml"
        replacement.write_text(selected.read_text())
        selected = replacement
    elif change == "unknown":
        selected.write_text(
            selected.read_text().replace(f'expected_archive_id="{ARCHIVE_ID}"\n', "")
        )
    result = CliRunner().invoke(
        cli.app,
        [
            "--json",
            "--client-config",
            str(selected),
            *flags,
            "--expected-client-scope",
            original,
            *target,
        ],
    )
    assert result.exit_code == 10, result.output
    assert json.loads(result.stdout)["errors"][0]["code"] in {"HFAPI017", "HFAPI018"}
    assert requests
    assert all(
        request.method == "GET" and request.url.path.endswith(("capabilities", "version"))
        for request in requests
    )


@pytest.mark.parametrize(
    "target",
    [
        ["status"],
        ["version"],
        ["version", "--server"],
        ["config", "validate", "--local"],
        ["client", "describe"],
        ["archive", "init", "--inspect"],
    ],
)
def test_scope_pin_is_not_a_routing_option_on_ordinary_reads(settings, monkeypatch, target):
    selected, _ = settings
    monkeypatch.setattr(
        cli_client,
        "resolve_client_config",
        lambda *_args, **_kwargs: pytest.fail("Invalid scope intent read settings"),
    )
    result = CliRunner().invoke(
        cli.app,
        ["--json", "--client-config", str(selected), "--expected-client-scope", "a" * 64, *target],
    )
    assert result.exit_code == 10
    assert json.loads(result.stdout)["errors"][0]["code"] == "HFARG002"


def test_matching_scope_allows_one_original_keyed_submission(settings, monkeypatch):
    selected, _ = settings
    requests = []

    def handle(request):
        requests.append(request)
        if request.method == "POST":
            assert request.headers["idempotency-key"] == "original-key"
            assert request.url.path == "/management/api/v1/syncs"
            acceptance = _accepted()
            return httpx.Response(
                202, json=acceptance, headers={"location": acceptance["links"]["status"]}
            )
        return httpx.Response(
            200, json=_capabilities() if request.url.path.endswith("capabilities") else _version()
        )

    monkeypatch.setattr(
        cli_client,
        "ApiClient",
        lambda config: ApiClient(config, transport=httpx.MockTransport(handle)),
    )
    metadata = json.loads(_invoke(selected).stdout)["data"]
    requests.clear()
    result = CliRunner().invoke(
        cli.app,
        [
            "--json",
            "--client-config",
            str(selected),
            "--expected-client-scope",
            metadata["authority_fingerprint"],
            "--idempotency-key",
            "original-key",
            "--detach",
            "sync",
        ],
    )
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)["idempotency_key"] == "original-key"
    assert [(request.method, request.url.path) for request in requests[:2]] == [
        ("GET", "/management/api/v1/capabilities"),
        ("GET", "/management/api/v1/version"),
    ]
    assert sum(request.method == "POST" for request in requests) == 1


@pytest.mark.parametrize("pin", ["", "A" * 64, "a" * 63, "a" * 65, "../secret", "not-a-digest"])
def test_malformed_scope_pin_refuses_before_settings(settings, monkeypatch, pin):
    selected, _ = settings
    monkeypatch.setattr(
        cli_client,
        "resolve_client_config",
        lambda *_a, **_k: pytest.fail("Malformed pin accessed settings"),
    )
    result = CliRunner().invoke(
        cli.app,
        ["--json", "--client-config", str(selected), "--expected-client-scope", pin, "sync"],
    )
    assert result.exit_code == 10
    assert json.loads(result.stdout)["errors"][0]["code"] == "HFARG002"


@pytest.mark.parametrize("command", ["lookup", "show"])
def test_scope_pin_does_not_authorize_wait_timeout_for_lookup_or_show(
    settings, monkeypatch, command
):
    selected, _ = settings
    monkeypatch.setattr(
        cli_client,
        "resolve_client_config",
        lambda *_a, **_k: pytest.fail("Metadata read timeout accessed settings"),
    )
    result = CliRunner().invoke(
        cli.app,
        [
            "--json",
            "--client-config",
            str(selected),
            "--expected-client-scope",
            "a" * 64,
            "--wait-timeout",
            "5",
            "operations",
            command,
            "original-key" if command == "lookup" else "c" * 32,
        ],
    )
    assert result.exit_code == 10
    assert json.loads(result.stdout)["errors"][0]["code"] == "HFARG002"


def test_scope_metadata_failure_preserves_exact_envelope_and_never_sends_key(settings, monkeypatch):
    selected, _ = settings
    requests = []
    payload = _version()
    failure = payload["envelope"]
    failure.update(
        exit_code=10,
        outcome="failed",
        data={},
        errors=[
            {
                "code": "HFAPI003",
                "message": "Synthetic original refusal",
                "repository": None,
                "context": {},
            }
        ],
    )

    def handle(request):
        requests.append(request)
        assert request.headers.get("idempotency-key") is None
        assert request.url.path.endswith(("capabilities", "version"))
        return httpx.Response(
            200, json=_capabilities() if request.url.path.endswith("capabilities") else payload
        )

    monkeypatch.setattr(
        cli_client,
        "ApiClient",
        lambda config: ApiClient(config, transport=httpx.MockTransport(handle)),
    )
    result = CliRunner().invoke(
        cli.app,
        [
            "--json",
            "--client-config",
            str(selected),
            "--expected-client-scope",
            "a" * 64,
            "operations",
            "lookup",
            "--",
            "original-key",
        ],
    )
    assert result.exit_code == 10
    assert json.loads(result.stdout) == failure
    assert len(requests) == 2


@pytest.mark.parametrize(
    "changes",
    [
        {"credential_class": "root"},
        {"instance_id": "bad"},
        {"credential_class": "rest-writer", "capabilities": ["read"]},
        {"reads": False},
    ],
)
def test_describe_never_presents_unvalidated_capability_metadata(settings, monkeypatch, changes):
    selected, _ = settings
    payload = _capabilities()
    payload["envelope"]["data"].update(changes)
    requests = []

    def handle(request):
        requests.append(request)
        return httpx.Response(200, json=payload)

    monkeypatch.setattr(
        cli_client,
        "ApiClient",
        lambda config: ApiClient(config, transport=httpx.MockTransport(handle)),
    )
    result = _invoke(selected)
    assert result.exit_code == 10
    envelope = json.loads(result.stdout)
    assert envelope["errors"][0]["code"] == "HFAPI018"
    assert envelope["data"] == {}
    assert len(requests) == 1


def test_even_matching_unknown_archive_pin_cannot_follow_an_original_handle(settings, monkeypatch):
    selected, _ = settings
    selected.write_text(selected.read_text().replace(f'expected_archive_id="{ARCHIVE_ID}"\n', ""))
    requests = []

    def handle(request):
        requests.append(request)
        assert request.url.path.endswith(("capabilities", "version"))
        payload = _capabilities() if request.url.path.endswith("capabilities") else _version()
        payload["archive_id"] = None
        return httpx.Response(200, json=payload)

    monkeypatch.setattr(
        cli_client,
        "ApiClient",
        lambda config: ApiClient(config, transport=httpx.MockTransport(handle)),
    )
    metadata = json.loads(_invoke(selected).stdout)["data"]
    assert metadata["archive_id"] is None
    requests.clear()
    result = CliRunner().invoke(
        cli.app,
        [
            "--json",
            "--client-config",
            str(selected),
            "--expected-client-scope",
            metadata["authority_fingerprint"],
            "operations",
            "lookup",
            "--",
            "original-key",
        ],
    )
    assert result.exit_code == 10
    assert json.loads(result.stdout)["errors"][0]["code"] == "HFAPI017"
    assert len(requests) == 2


def test_profile_hash_excludes_credential_source_bytes_and_timing_options(
    settings, tmp_path, monkeypatch
):
    selected, token = settings

    def handle(request):
        return httpx.Response(
            200, json=_capabilities() if request.url.path.endswith("capabilities") else _version()
        )

    monkeypatch.setattr(
        cli_client,
        "ApiClient",
        lambda config: ApiClient(config, transport=httpx.MockTransport(handle)),
    )
    first = json.loads(_invoke(selected).stdout)["data"]
    replacement = tmp_path / "other-secret-source"
    replacement.write_text("synthetic-replacement-token-" + "M" * 40)
    replacement.chmod(0o600)
    selected.write_text(
        selected.read_text().replace(str(token), str(replacement)) + "read_timeout=12.0\n"
    )
    second = json.loads(_invoke(selected).stdout)["data"]
    assert second == first


def test_unrepresentable_endpoint_is_a_safe_classified_failure_before_http(settings, monkeypatch):
    selected, _ = settings
    monkeypatch.setattr(
        cli_client,
        "ApiClient",
        lambda config: ApiClient(
            config,
            transport=httpx.MockTransport(
                lambda _request: pytest.fail("Unrepresentable endpoint attempted an HTTP request")
            ),
        ),
    )
    result = _invoke(selected, "--api-url", "https://☃.example")
    assert result.exit_code == 10, result.output
    assert json.loads(result.stdout)["errors"][0]["code"] == "HFAPI017"
    assert "☃" not in result.stdout


@pytest.mark.parametrize("candidate", [False, True])
@pytest.mark.parametrize("matching", [False, True])
def test_remote_synchronous_validation_compares_scope_without_job_authority(
    settings, tmp_path, monkeypatch, candidate, matching
):
    selected, _ = settings
    requests = []
    content = "schema_version=1\n# SYNTHETIC_CANDIDATE_NEVER_IN_METADATA\n"
    path = tmp_path / "candidate.toml"
    path.write_text(content)

    def handle(request):
        requests.append(request)
        assert request.headers.get("idempotency-key") is None
        if request.method == "POST":
            assert matching
            assert request.url.path == "/management/api/v1/config/validate"
            assert json.loads(request.content) == ({"candidate": content} if candidate else {})
            payload = _read(data={"valid": True})
            payload["envelope"]["command"] = "config validate"
        else:
            payload = _capabilities() if request.url.path.endswith("capabilities") else _version()
        return httpx.Response(200, json=payload)

    monkeypatch.setattr(
        cli_client,
        "ApiClient",
        lambda config: ApiClient(config, transport=httpx.MockTransport(handle)),
    )
    metadata = json.loads(_invoke(selected).stdout)["data"]
    requests.clear()
    result = CliRunner().invoke(
        cli.app,
        [
            "--json",
            "--client-config",
            str(selected),
            "--expected-client-scope",
            metadata["authority_fingerprint"] if matching else "f" * 64,
            *(["--config", str(path)] if candidate else []),
            "config",
            "validate",
        ],
    )
    assert result.exit_code == (0 if matching else 10), result.output
    assert sum(request.method == "POST" for request in requests) == (1 if matching else 0)
    assert "Idempotency key:" not in result.stderr
    if not matching:
        assert json.loads(result.stdout)["errors"][0]["code"] == "HFAPI017"
