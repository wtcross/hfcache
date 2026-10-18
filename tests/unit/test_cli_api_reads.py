"""Reader CLI output and candidate input cross the actual HTTP boundary (API-012)."""

import json

import httpx
import pytest
from typer.testing import CliRunner

from hfcache import cli, cli_client
from hfcache.client import ApiClient
from hfcache.client_config import ClientConfig
from hfcache.client_errors import ClientProtocolError
from tests.api_cli import api_cli
from tests.unit.test_api_client_adversarial import _read
from tests.unit.test_api_commands import configured as command_archive  # noqa: F401 - fixture
from tests.unit.test_synchronize import DATASET, MODEL


@pytest.fixture
def configured(request):
    return request.getfixturevalue("command_archive")


@pytest.mark.parametrize(
    "arguments",
    [
        ["status"],
        ["list"],
        ["list", "--revisions"],
        ["verify", "--estimate"],
        ["archive", "init", "--inspect"],
        ["version", "--server"],
        ["config", "validate"],
        ["doctor", "--read-only"],
        ["plan"],
    ],
)
def test_reader_modes_need_no_client_archive_config_or_hub_credentials(
    configured, monkeypatch, arguments
):
    policy, _, _, _ = configured

    def forbidden(*args, **kwargs):
        pytest.fail("API reader attempted local writer configuration/service execution")

    monkeypatch.setattr(cli, "load_config", forbidden)
    with api_cli(policy.archive_config, reader=True) as remote:
        result = remote.invoke(arguments)
        assert result.exit_code == 0, result.output
        assert json.loads(result.stdout)["schema_version"] == 1
        assert len(result.stdout.splitlines()) == 1


@pytest.mark.parametrize(
    "arguments",
    [
        ["status"],
        ["list"],
        ["verify", "--estimate"],
        ["archive", "init", "--inspect"],
        ["version", "--server"],
        ["doctor", "--read-only"],
    ],
)
def test_explicit_archive_config_is_a_migration_error_on_non_candidates(tmp_path, arguments):
    result = CliRunner().invoke(
        cli.app, ["--json", "--config", str(tmp_path / "missing.toml"), *arguments]
    )
    assert result.exit_code == 10
    payload = json.loads(result.stdout)
    assert payload["errors"][0]["code"] == "HFARG002"
    assert "candidate" in payload["errors"][0]["message"]


@pytest.mark.parametrize(
    "arguments", [["status"], ["plan"], ["config", "validate"], ["doctor", "--read-only"]]
)
def test_hub_token_override_is_never_sent_to_api(tmp_path, arguments):
    result = CliRunner().invoke(
        cli.app, ["--json", "--token-file", str(tmp_path / "unknown.token"), *arguments]
    )
    assert result.exit_code == 10
    payload = json.loads(result.stdout)
    assert payload["errors"][0]["code"] == "HFARG002"
    assert "--api-token-file" in payload["errors"][0]["message"]


@pytest.mark.parametrize("arguments", [["plan"], ["config", "validate"]])
def test_candidate_token_override_refuses_before_candidate_file_access(tmp_path, arguments):
    result = CliRunner().invoke(
        cli.app,
        [
            "--json",
            "--config",
            str(tmp_path / "missing.toml"),
            "--token-file",
            str(tmp_path / "unknown.token"),
            *arguments,
        ],
    )
    assert result.exit_code == 10
    assert json.loads(result.stdout)["errors"][0]["code"] == "HFARG002"


def test_absent_api_is_transport_failure_without_local_fallback(tmp_path, monkeypatch):
    token, settings = tmp_path / "reader.token", tmp_path / "client.toml"
    token.write_text("reader-token-" + "T" * 40)
    token.chmod(0o600)
    settings.write_text("schema_version=1\nread_retries=0\n")

    def forbidden(*args, **kwargs):
        pytest.fail("unavailable API fell back to local writer state")

    monkeypatch.setattr(cli, "load_config", forbidden)
    outcome = CliRunner().invoke(
        cli.app,
        [
            "--json",
            "--client-config",
            str(settings),
            "--api-socket",
            str(tmp_path / "absent.sock"),
            "--api-token-file",
            str(token),
            "status",
        ],
    )
    assert outcome.exit_code == 20
    assert json.loads(outcome.stdout)["errors"][0]["code"] == "HFAPI019"


def _publish(remote, selector, key):
    headers = {"Authorization": "Bearer " + remote.token.read_text(), "Idempotency-Key": key}
    response = remote.web.post("/api/v1/syncs", headers=headers, json={"selectors": [selector]})
    assert response.status_code == 202, response.text
    operation = response.json()["operation"]["operation_id"]
    assert remote.application.state.runner.wait(operation, timeout=10).exit_code == 0


def test_status_walks_every_page_and_preserves_first_server_envelope(configured, monkeypatch):
    policy, _, _, _ = configured
    captured = []
    original = ApiClient.read

    def record(client, path, *args, **kwargs):
        result = original(client, path, *args, **kwargs)
        if path == "/api/v1/status":
            captured.append(result.envelope.to_payload())
        return result

    monkeypatch.setattr(ApiClient, "read", record)
    with api_cli(policy.archive_config, page_size=1) as remote:
        _publish(remote, MODEL.selector, "publish-model")
        _publish(remote, DATASET.selector, "publish-dataset")
        result = remote.invoke(["status"])
        assert result.exit_code == 0, result.output
    emitted = json.loads(result.stdout)
    assert len(captured) == 2
    assert len(emitted["data"]["repositories"]) == 2
    assert {key: value for key, value in emitted.items() if key != "data"} == {
        key: value for key, value in captured[0].items() if key != "data"
    }
    assert emitted["data"]["repositories"] == [
        row for envelope in captured for row in envelope["data"]["repositories"]
    ]


def test_real_inventory_includes_unmanaged_revisions_and_known_empty_selection(configured):
    policy, _, _, _ = configured
    with api_cli(policy.archive_config, page_size=1) as remote:
        _publish(remote, MODEL.selector, "publish")
        text = policy.archive_config.read_text()
        # This fixture owns the policy file; retain dataset while removing model intent.
        model_section = text.index("[[repositories]]")
        dataset_section = text.index("[[repositories]]", model_section + 1)
        policy.archive_config.write_text(text[:model_section] + text[dataset_section:])
        result = remote.invoke(["list", "--revisions"])
        assert result.exit_code == 0, result.output
        (repository,) = json.loads(result.stdout)["data"]["repositories"]
        assert repository["repository_id"] == MODEL.id
        assert repository["managed"] is False
        assert repository["enabled"] is None
        assert len(repository["revisions"]) == 1
        empty = remote.invoke(["list", DATASET.selector, "--revisions"])
        assert empty.exit_code == 0, empty.output
        assert json.loads(empty.stdout)["data"]["repositories"] == []


@pytest.mark.parametrize("mismatch", [False, True])
def test_revision_join_preserves_empty_rows_and_pins_current_publication(tmp_path, mismatch):
    token = tmp_path / "token"
    token.write_text("reader-" + "X" * 40)
    token.chmod(0o600)
    current = {
        "repository_type": "model",
        "repository_id": "org/model",
        "managed": True,
        "enabled": True,
        "current_commit_sha": "a" * 40,
        "current_publication_id": "b" * 32,
        "retained_revisions": 1,
    }
    empty = current | {
        "repository_id": "org/empty",
        "current_commit_sha": None,
        "current_publication_id": None,
        "retained_revisions": 0,
    }
    revision = {
        "repository_type": "model",
        "repository_id": "org/model",
        "commit_sha": "a" * 40,
        "publication_id": ("c" if mismatch else "b") * 32,
        "publication_generation": 1,
        "file_count": 1,
        "total_bytes": 1,
        "published_at": "2026-10-18T00:00:00Z",
        "verification_state": "unknown",
    }

    def handle(request):
        payload = _read(
            data={"repositories": [empty, current]}
            if request.url.path.endswith("/repositories")
            else {"revisions": [revision]}
        )
        payload["envelope"]["command"] = "list"
        return httpx.Response(200, json=payload)

    settings = ClientConfig(
        schema_version=1, api_url="https://archive.example", api_token_file=token
    )
    with ApiClient(settings, transport=httpx.MockTransport(handle)) as client:
        if mismatch:
            with pytest.raises(ClientProtocolError):
                cli_client.inventory(client, {}, revisions=True)
        else:
            result = cli_client.inventory(client, {}, revisions=True)
            assert result.data["repositories"][0]["revisions"] == []
            assert result.data["repositories"][1]["revisions"][0]["publication_id"] == "b" * 32


def test_candidate_cli_sends_content_and_preserves_validation_compatibility(configured, tmp_path):
    policy, _, _, _ = configured
    candidate = tmp_path / "candidate.toml"
    candidate.write_text(
        policy.archive_config.read_text().replace(
            'endpoint = "https://huggingface.co"', 'endpoint = "https://attacker.example"'
        )
    )
    # The fixture's default Hub endpoint is implicit; add an explicit authority change.
    candidate.write_text(
        candidate.read_text().replace(
            "[sync]", '[hub]\nendpoint="https://attacker.example"\n[sync]'
        )
    )
    with api_cli(policy.archive_config) as remote:
        result = remote.invoke(["--config", str(candidate), "config", "validate"])
        assert result.exit_code == 0, result.output
        payload = json.loads(result.stdout)["data"]
        assert payload["syntax_valid"] is True
        assert payload["authority_compatible"] is False
        assert "hub.endpoint" in payload["authority_mismatches"]
        assert str(candidate) not in result.stdout


def test_inventory_aggregate_budget_is_enforced_without_revision_expansion(tmp_path):
    token = tmp_path / "token"
    token.write_text("reader-" + "A" * 40)
    token.chmod(0o600)

    def handle(request):
        index = int(request.url.params.get("cursor", "0"))
        row = {
            "repository_type": "model",
            "repository_id": f"org/model-{index}",
            "managed": True,
            "enabled": True,
            "current_commit_sha": None,
            "current_publication_id": None,
            "retained_revisions": 0,
            "padding": "x" * 1500,
        }
        return httpx.Response(
            200,
            json=_read(data={"repositories": [row]}, cursor=str(index + 1) if index < 2 else None),
        )

    settings = ClientConfig(
        schema_version=1,
        api_url="https://archive.example",
        api_token_file=token,
        max_response_bytes=4096,
    )
    with (
        ApiClient(settings, transport=httpx.MockTransport(handle)) as client,
        pytest.raises(ClientProtocolError),
    ):
        cli_client.inventory(client, {}, revisions=False)
