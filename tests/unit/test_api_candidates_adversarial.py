"""Candidate policy cannot change the installed writer's credential authority."""

import time
import warnings
from threading import Event
from types import SimpleNamespace
from typing import TYPE_CHECKING

import pytest
from starlette.exceptions import StarletteDeprecationWarning

with warnings.catch_warnings():
    warnings.filterwarnings(
        "ignore",
        message=(
            "Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead."
        ),
        category=StarletteDeprecationWarning,
    )
    from fastapi.testclient import TestClient

from hfcache.api.app import create_app
from hfcache.api.auth import authenticate_bearer, load_credentials
from hfcache.config import load_config
from hfcache.hub import DownloadEstimate, RepositoryFacts, TreeEntry
from hfcache.identity import CommitSha
from hfcache.logging import reset
from hfcache.server_config import validate_server_config_mapping
from hfcache.services.context import ServiceResult
from tests.fixtures import examples

if TYPE_CHECKING:
    from pathlib import Path

WRITER = "writer_0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef"
READER = "reader_9876543210zyxwvutsrqponmlkjihgfedcbaZYXWVU"
HUB_TOKEN = "installedHubCredentialForCandidateAuthorityTests"
SHA = "a" * 40
PREFIX = "/api/v1"


def _policy(root: Path) -> str:
    return (
        f'schema_version=1\n[storage]\narchive_root="{root}"\n'
        f'archive_id="{examples.ARCHIVE_ID}"\n'
        '[hub]\nendpoint="https://huggingface.co"\ntoken_mode="required"\n'
        'credential_name="installed-hub"\nexpected_account="installed-account"\n'
        "[sync]\nlock_wait_seconds=30\n"
        '[[repositories]]\ntype="model"\nid="example/model"\nrevision="main"\n'
    )


@pytest.fixture
def configured(tmp_path, monkeypatch):
    reset()
    policy = tmp_path / "archive.toml"
    policy.write_text(_policy(tmp_path / "archive"))
    token = tmp_path / "hub-token"
    token.write_text(HUB_TOKEN)
    credentials = {}
    for name, value in (("writer", WRITER), ("reader", READER)):
        path = tmp_path / name
        path.write_text(value)
        path.chmod(0o600)
        credentials[name] = {"file": str(path)}
    server = validate_server_config_mapping(
        {
            "schema_version": 1,
            "archive_config": str(policy),
            "state_directory": str(tmp_path / "state"),
            "credentials": credentials,
            "listener": {"allowed_hosts": ["testserver"]},
        }
    )
    calls: list[tuple[object, ...]] = []

    class Hub:
        def require_identity(self, account):
            calls.append(("identity", account))

        def repository(self, identity, revision):
            calls.append(("repository", identity.selector, revision))
            return RepositoryFacts(
                identity=identity, commit_sha=CommitSha(SHA), private=False, gated=False
            )

        def tree(self, identity, commit_sha):
            return (TreeEntry(path="config.json", size=13),)

        def estimate(self, identity, commit_sha, *, cache_dir, max_workers):
            calls.append(("estimate", cache_dir, max_workers))
            return DownloadEstimate(file_count=1, logical_bytes=13, new_bytes=13)

    def client_of(resolved, *, endpoint):
        calls.append(("client", resolved.secret, resolved.source.value, endpoint))
        return Hub()

    monkeypatch.setattr("hfcache.services.commands.HubClient.of", client_of)
    app = create_app(server, instance_lock_path=tmp_path / "daemon.lock", hub_token_file=token)
    try:
        with TestClient(app) as client:
            yield SimpleNamespace(
                app=app,
                client=client,
                calls=calls,
                policy=policy,
                token=token,
                server=server,
                root=tmp_path,
            )
    finally:
        reset()


def _headers(*, key=None, token=WRITER):
    value = {"Authorization": f"Bearer {token}"}
    if key is not None:
        value["Idempotency-Key"] = key
    return value


def _post(configured, route, body, *, key="candidate", token=WRITER):
    return configured.client.post(PREFIX + route, json=body, headers=_headers(key=key, token=token))


def _result(configured, response):
    assert response.status_code == 202, response.text
    admitted = response.json()
    deadline = time.monotonic() + 10
    while True:
        observed = configured.client.get(admitted["links"]["status"], headers=_headers())
        assert observed.status_code == 200, observed.text
        state = observed.json()["envelope"]["data"]["operation"]["state"]
        if state in {"succeeded", "failed"}:
            break
        assert state != "interrupted", observed.text
        assert time.monotonic() < deadline
        time.sleep(0.005)
    result = configured.client.get(admitted["links"]["result"], headers=_headers())
    assert result.status_code == 200, result.text
    return result.json()["envelope"]


@pytest.mark.parametrize("route", ["/plans", "/config/validate"])
@pytest.mark.parametrize("candidate", ["invalid TOML", None, 42, ""])
def test_candidate_presence_requires_writer_before_shape_or_syntax(configured, route, candidate):
    response = _post(configured, route, {"candidate": candidate}, token=READER)

    assert response.status_code == 403
    assert response.json()["code"] == "HFAPI002"
    assert configured.app.state.operations.list() == ()
    assert configured.calls == []


@pytest.mark.parametrize("route", ["/plans", "/config/validate"])
@pytest.mark.parametrize(
    "body",
    [
        {"candidate": None},
        {"candidate": 42},
        {"candidate": ""},
        {"candidate_path": "/untrusted/server/config.toml"},
        {"config": "/untrusted/server/config.toml"},
        {"candidate": "schema_version=1", "token_file": "/untrusted/server/token"},
        {"candidate": "schema_version=1", "endpoint": "https://attacker.example"},
    ],
)
def test_candidate_shape_never_accepts_server_paths_or_credential_overrides(
    configured, route, body
):
    response = _post(configured, route, body)

    assert response.status_code == 422, response.text
    assert response.json()["code"] == "HFAPI006"
    assert configured.calls == []
    assert configured.app.state.operations.list() == ()


AUTHORITY_CHANGES = (
    (
        "storage.archive_root",
        lambda text, root: text.replace(str(root / "archive"), str(root / "other")),
    ),
    (
        "storage.archive_id",
        lambda text, _: text.replace(examples.ARCHIVE_ID, "d7b60815-aa51-4c30-8ef3-557de023e5a1"),
    ),
    (
        "hub.endpoint",
        lambda text, _: text.replace("https://huggingface.co", "https://attacker.example"),
    ),
    (
        "hub.token_mode",
        lambda text, _: text.replace('token_mode="required"', 'token_mode="optional"'),
    ),
    (
        "hub.credential_name",
        lambda text, _: text.replace(
            'credential_name="installed-hub"', 'credential_name="attacker-hub"'
        ),
    ),
    (
        "hub.expected_account",
        lambda text, _: text.replace(
            'expected_account="installed-account"', 'expected_account="other-account"'
        ),
    ),
)


@pytest.mark.parametrize(("field", "change"), AUTHORITY_CHANGES)
def test_valid_incompatible_candidate_is_assessed_without_credentials(
    configured, monkeypatch, field, change
):
    def forbidden(*_args, **_kwargs):
        pytest.fail("candidate validation resolved a credential")

    monkeypatch.setattr("hfcache.api.commands.resolve_token", forbidden)
    monkeypatch.setattr("hfcache.services.commands.resolve_token", forbidden)
    candidate = change(configured.policy.read_text(), configured.root)

    response = _post(configured, "/config/validate", {"candidate": candidate})

    assert response.status_code == 200, response.text
    envelope = response.json()["envelope"]
    assert envelope["exit_code"] == 0
    assert envelope["data"]["valid"] is True
    assert envelope["data"]["syntax_valid"] is True
    assert envelope["data"]["authority_compatible"] is False
    assert envelope["data"]["authority_mismatches"] == [field]
    assert configured.calls == []
    assert configured.app.state.operations.list() == ()


@pytest.mark.parametrize(("field", "change"), AUTHORITY_CHANGES)
def test_candidate_plan_refuses_authority_before_credentials_or_hub(
    configured, monkeypatch, field, change
):
    del field

    def forbidden(*_args, **_kwargs):
        pytest.fail("incompatible candidate resolved a credential")

    monkeypatch.setattr("hfcache.api.commands.resolve_token", forbidden)
    monkeypatch.setattr("hfcache.services.commands.resolve_token", forbidden)
    candidate = change(configured.policy.read_text(), configured.root)

    envelope = _result(configured, _post(configured, "/plans", {"candidate": candidate}))

    assert envelope["exit_code"] == 10
    assert [problem["code"] for problem in envelope["errors"]] == ["HFAPI007"]
    assert configured.calls == []


@pytest.mark.parametrize(
    "candidate", ["schema_version = = 1", 'schema_version=1\n[storage]\narchive_root="relative"']
)
def test_malformed_candidate_preserves_configuration_problems(configured, candidate):
    response = _post(configured, "/config/validate", {"candidate": candidate})

    assert response.status_code == 200, response.text
    envelope = response.json()["envelope"]
    assert envelope["exit_code"] == 10
    assert envelope["outcome"] == "failed"
    assert envelope["errors"]
    assert all(problem["code"].startswith("HFCFG") for problem in envelope["errors"])
    assert configured.calls == []


def test_candidate_validation_survives_invalid_installed_policy_without_claiming_compatibility(
    configured, monkeypatch
):
    candidate = configured.policy.read_text()
    configured.policy.write_text("not valid TOML [")

    def forbidden(*_args, **_kwargs):
        pytest.fail("syntax-only assessment resolved credentials")

    monkeypatch.setattr("hfcache.api.commands.resolve_token", forbidden)
    monkeypatch.setattr("hfcache.services.commands.resolve_token", forbidden)

    response = _post(configured, "/config/validate", {"candidate": candidate})

    assert response.status_code == 200, response.text
    envelope = response.json()["envelope"]
    assert envelope["exit_code"] == 0
    assert envelope["data"]["valid"] is True
    assert envelope["data"]["syntax_valid"] is True
    assert envelope["data"]["authority_compatible"] is None
    assert envelope["data"]["installed_policy_valid"] is False
    assert configured.calls == []


@pytest.mark.parametrize("route", ["/plans", "/config/validate"])
def test_candidate_credential_validation_never_echoes_submitted_secret(configured, route):
    opaque = "candidateLiteralCredentialMustNotEscape"
    candidate = configured.policy.read_text().replace("[hub]", f'[hub]\ntoken="{opaque}"')
    response = _post(configured, route, {"candidate": candidate})
    envelope = _result(configured, response) if route == "/plans" else response.json()["envelope"]

    assert envelope["exit_code"] == 10
    assert "HFCFG010" in {problem["code"] for problem in envelope["errors"]}
    assert opaque not in str(envelope)
    assert opaque not in str(configured.app.state.operations.list())
    assert configured.calls == []


def test_candidate_plan_uses_installed_credential_and_candidate_repository_policy(configured):
    candidate = configured.policy.read_text().replace(
        'id="example/model"', 'id="candidate/proposed"'
    )

    envelope = _result(configured, _post(configured, "/plans", {"candidate": candidate}))

    assert envelope["exit_code"] == 0
    assert envelope["data"]["repositories"][0]["repository_id"] == "candidate/proposed"
    assert ("client", HUB_TOKEN, "token-file", "https://huggingface.co") in configured.calls
    assert ("identity", "installed-account") in configured.calls
    assert HUB_TOKEN not in str(envelope)
    assert candidate not in str(configured.app.state.operations.list())
    assert configured.policy.read_text() != candidate


def test_candidate_key_binds_exact_content_but_canonical_selector_set(configured):
    candidate = configured.policy.read_text()
    body = {"candidate": candidate, "selectors": ["model:example/model", "model:example/model"]}
    first = _post(configured, "/plans", body)
    _result(configured, first)
    retry = _post(
        configured, "/plans", {"candidate": candidate, "selectors": ["model:example/model"]}
    )
    changed = _post(
        configured,
        "/plans",
        {"candidate": candidate + "\n", "selectors": ["model:example/model"]},
    )

    assert retry.status_code == 202, retry.text
    assert retry.json()["operation"]["operation_id"] == first.json()["operation"]["operation_id"]
    assert retry.json()["created"] is False
    assert changed.status_code == 409
    assert changed.json()["code"] == "HFAPI012"
    assert sum(call[0] == "client" for call in configured.calls) == 1


@pytest.mark.parametrize(("field", "change"), AUTHORITY_CHANGES)
def test_queued_candidate_rechecks_fresh_installed_authority(
    configured, monkeypatch, field, change
):
    started, release = Event(), Event()
    registry = load_credentials(configured.server)
    principal = authenticate_bearer(registry, f"Bearer {WRITER}")

    def block(_snapshot, _context):
        started.set()
        assert release.wait(10)
        return ServiceResult("plan", {"repositories": []})

    original = configured.policy.read_text()
    before = load_config(configured.policy).fingerprint()
    configured.app.state.runner.submit(
        principal,
        "blocked-trusted-job",
        PREFIX + "/plans",
        {},
        command="plan",
        execute=block,
        wait_seconds=30,
        requires_lock=False,
    )
    assert started.wait(5)
    try:
        accepted = _post(configured, "/plans", {"candidate": original})
        assert accepted.status_code == 202, accepted.text
        configured.policy.write_text(change(original, configured.root))
        if field == "hub.credential_name":
            assert load_config(configured.policy).fingerprint() == before

        def forbidden(*_args, **_kwargs):
            pytest.fail("stale queued candidate resolved a credential")

        monkeypatch.setattr("hfcache.api.commands.resolve_token", forbidden)
        monkeypatch.setattr("hfcache.services.commands.resolve_token", forbidden)
    finally:
        release.set()

    envelope = _result(configured, accepted)

    assert envelope["exit_code"] == 10
    expected = "HFCFG005" if field in {"storage.archive_root", "storage.archive_id"} else "HFAPI007"
    assert [problem["code"] for problem in envelope["errors"]] == [expected]
    assert configured.calls == []


def test_matching_candidate_retry_bypasses_new_invalid_policy_and_preparation(configured):
    candidate = configured.policy.read_text()
    first = _post(configured, "/plans", {"candidate": candidate})
    _result(configured, first)
    configured.policy.write_text("not valid TOML [")

    retry = _post(configured, "/plans", {"candidate": candidate})

    assert retry.status_code == 202, retry.text
    assert retry.json()["created"] is False
    assert retry.json()["operation"]["operation_id"] == first.json()["operation"]["operation_id"]
    assert sum(call[0] == "client" for call in configured.calls) == 1
