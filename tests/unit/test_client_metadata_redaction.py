"""Derived public authority must not collide with a registered credential (INV-002)."""

import json

import httpx
import pytest
from typer.testing import CliRunner

from hfcache import cli, cli_client
from hfcache.client import ApiClient
from hfcache.client_config import resolve_client_config
from hfcache.client_metadata import describe_client
from hfcache.redaction import register_secret
from tests.unit.test_cli_client_describe import _capabilities, _version
from tests.unit.test_server_bootstrap import ARCHIVE_ID


@pytest.fixture
def authority_fixture(tmp_path, monkeypatch):
    token = tmp_path / "synthetic-rest.token"
    token.write_text("synthetic-rest-initial-" + "Q" * 40)
    token.chmod(0o600)
    selected = tmp_path / "client.toml"
    selected.write_text(
        'schema_version=1\napi_url="https://fixture.example/management"\n'
        f'api_token_file="{token}"\nexpected_archive_id="{ARCHIVE_ID}"\nread_retries=0\n'
    )
    requests = []

    def handle(request):
        requests.append((request.method, request.url.path))
        return httpx.Response(
            200,
            json=_capabilities() if request.url.path.endswith("capabilities") else _version(),
        )

    def client(config):
        return ApiClient(config, transport=httpx.MockTransport(handle))

    monkeypatch.setattr(cli_client, "ApiClient", client)
    with client(resolve_client_config(selected)) as session:
        original = describe_client(session, selected)
    assert isinstance(original, dict)
    requests.clear()
    return selected, token, original, requests


@pytest.mark.parametrize(
    "field",
    ["profile_fingerprint", "authority_fingerprint", "archive_id", "instance_id", "hash_substring"],
)
@pytest.mark.parametrize("json_output", [False, True])
def test_registered_credential_collision_refuses_before_json_or_human_metadata_output(
    authority_fixture, field, json_output
):
    selected, token, original, requests = authority_fixture
    secret = original["profile_fingerprint"][8:40] if field == "hash_substring" else original[field]
    token.write_text(secret)
    arguments = ["--client-config", str(selected), "client", "describe"]
    if json_output:
        arguments.insert(0, "--json")
    result = CliRunner().invoke(cli.app, arguments)
    exposed = result.exit_code == 0 and secret in result.output
    assert not exposed, "A registered credential reached metadata output"
    assert result.exit_code == 10
    assert secret not in result.output
    assert "HFAPI017" in result.output
    if json_output:
        envelope = json.loads(result.stdout)
        assert envelope["command"] == "client describe"
        assert envelope["errors"][0]["code"] == "HFAPI017"
        assert envelope["data"] == {}
    assert requests == [
        ("GET", "/management/api/v1/capabilities"),
        ("GET", "/management/api/v1/version"),
    ]


def test_final_check_covers_public_strings_registered_after_initial_endpoint_check(
    authority_fixture, monkeypatch
):
    selected, _token, _original, requests = authority_fixture

    def handle(request):
        requests.append((request.method, request.url.path))
        if request.url.path.endswith("version"):
            register_secret("rest-writer")
        return httpx.Response(
            200,
            json=_capabilities() if request.url.path.endswith("capabilities") else _version(),
        )

    monkeypatch.setattr(
        cli_client,
        "ApiClient",
        lambda config: ApiClient(config, transport=httpx.MockTransport(handle)),
    )
    result = CliRunner().invoke(
        cli.app, ["--json", "--client-config", str(selected), "client", "describe"]
    )
    assert result.exit_code == 10
    assert "rest-writer" not in result.output
    envelope = json.loads(result.stdout)
    assert envelope["errors"][0]["code"] == "HFAPI017"
    assert envelope["data"] == {}
    assert all(method == "GET" for method, _path in requests)
