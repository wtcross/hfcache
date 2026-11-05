"""Current REST configuration/docs and disabled optional imports (API-016)."""

import asyncio
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING, cast

import httpx
import pytest
from fastmcp import Client, FastMCP

from hfcache import client as client_module
from hfcache import client_config
from hfcache.client import ApiClient
from hfcache.client_config import resolve_client_config
from hfcache.client_errors import ClientConnectionError
from hfcache.config import load_config
from hfcache.mcp_tools import install_read_tools
from hfcache.models import Reference
from hfcache.server_config import load_server_config
from hfcache.services.mcp_queries import MetadataRead
from tests.docs_contract import CHECKER
from tests.unit.test_api_client_adversarial import (
    BASE,
    OPERATION,
    TOKEN,
    _accepted,
    _capabilities,
    _operation,
    _read,
    _response,
)

if TYPE_CHECKING:
    from hfcache.mcp_tools import MetadataReadPort

ROOT = Path(__file__).resolve().parents[2]
INTERFACE_DOCS = (
    "README.md",
    "docs/api.md",
    "docs/server.md",
    "docs/api-client.md",
    "docs/mcp.md",
    "docs/quickstart.md",
    "docs/cli.md",
    "docs/consumers.md",
    "docs/configuration.md",
    "docs/security.md",
    "docs/invariants.md",
)


def documented_example(relative, name, language, *, kind="executable"):
    document = (ROOT / relative).read_text()
    marker = re.escape(f"<!-- {kind}-example: {name} -->")
    examples = re.findall(rf"(?ms)^{marker}\n```{language}\n(.*?)^```", document)
    assert len(examples) == 1, (relative, name)
    return examples[0]


@pytest.mark.parametrize(
    ("relative", "loader"),
    [
        ("examples/config.toml", load_config),
        ("packaging/server.toml", load_server_config),
        ("packaging/client.example.toml", resolve_client_config),
        ("packaging/scheduled-client.example.toml", resolve_client_config),
    ],
)
def test_current_configuration_examples_use_their_strict_independent_loader(relative, loader):
    # Parse only. Loading settings neither resolves a credential nor opens the
    # configured archive, starts a daemon or contacts the Hub/API.
    path = ROOT / relative
    before = path.read_bytes()
    parsed = loader(path)
    assert parsed.schema_version == 1
    assert path.read_bytes() == before


def test_documented_minimal_archive_policy_and_focused_extension_parse(tmp_path):
    minimal = documented_example("docs/configuration.md", "archive-minimal", "toml", kind="schema")
    extension = documented_example(
        "docs/configuration.md", "archive-repository-extension", "toml", kind="schema"
    )
    policy = tmp_path / "candidate.toml"
    policy.write_text(minimal)
    assert load_config(policy).repositories == ()
    policy.write_text(minimal + "\n" + extension)
    parsed = load_config(policy)
    assert len(parsed.repositories) == 1
    assert not parsed.repositories[0].enabled
    assert parsed.repositories[0].tags == ("coding", "local-inference")


def test_documented_protected_file_sdk_example_sends_the_selected_header(tmp_path, monkeypatch):
    token = tmp_path / "reader.token"
    token.write_text(TOKEN)
    token.chmod(0o600)
    settings = tmp_path / "client.toml"
    settings.write_text(f'schema_version=1\napi_url="{BASE}"\napi_token_file="{token}"\n')
    before = (settings.read_bytes(), token.read_bytes())
    seen = []

    def respond(request):
        seen.append((request.url.path, request.headers.get("Authorization")))
        if request.url.path.endswith("/capabilities"):
            return _response(_capabilities())
        payload = _read(data={"application": "fixture"})
        payload["envelope"]["command"] = "version"
        return _response(payload)

    monkeypatch.setattr(client_config, "DEFAULT_CLIENT_CONFIG", settings)
    monkeypatch.setattr(
        client_module,
        "ApiClient",
        lambda config: ApiClient(config, transport=httpx.MockTransport(respond)),
    )
    example = documented_example("docs/api-client.md", "reader-version", "python")
    namespace = {}
    exec(compile(example, "documented SDK example", "exec"), namespace)
    assert seen == [
        ("/management/api/v1/capabilities", "Bearer " + TOKEN),
        ("/management/api/v1/version", "Bearer " + TOKEN),
    ]
    assert namespace["envelope"].command == "version"
    assert (settings.read_bytes(), token.read_bytes()) == before


@pytest.mark.parametrize("outcome", ["acknowledged", "lost", "lookup-unavailable"])
def test_documented_uncertain_sizing_observes_original_key_without_replaying(
    tmp_path, monkeypatch, outcome
):
    token = tmp_path / "reader.token"
    token.write_text(TOKEN)
    token.chmod(0o600)
    settings = tmp_path / "client.toml"
    settings.write_text(
        f'schema_version=1\napi_url="{BASE}"\napi_token_file="{token}"\nread_retries=0\n'
    )
    seen = []

    def respond(request):
        seen.append(request)
        if request.url.path.endswith("/capabilities"):
            return _response(_capabilities())
        if request.method == "POST":
            assert request.url.path == "/management/api/v1/plans"
            assert json.loads(request.content) == {"selectors": []}
            if outcome != "acknowledged":
                message = "synthetic lost acknowledgement"
                raise httpx.ReadTimeout(message, request=request)
            accepted = _accepted()
            accepted["operation"]["route"] = "/api/v1/plans"
            accepted["operation"]["principal"] = "rest-reader"
            return _response(
                accepted, status=202, headers={"location": accepted["links"]["status"]}
            )
        if request.url.path.endswith("/result"):
            result = _read(data={"repositories": []})
            result["envelope"]["command"] = "plan"
            return _response(result)
        if request.url.path.endswith("/lookup") and outcome == "lookup-unavailable":
            message = "synthetic unavailable lookup"
            raise httpx.ReadTimeout(message, request=request)
        operation = _operation(state="succeeded")
        operation["route"] = "/api/v1/plans"
        operation["principal"] = "rest-reader"
        result = _read(data={"operation": operation})
        result["envelope"]["command"] = (
            "operations lookup" if request.url.path.endswith("/lookup") else "operations show"
        )
        return _response(result)

    monkeypatch.setattr(client_config, "DEFAULT_CLIENT_CONFIG", settings)
    monkeypatch.setattr(
        client_module,
        "ApiClient",
        lambda config: ApiClient(config, transport=httpx.MockTransport(respond)),
    )
    example = documented_example("docs/api-client.md", "uncertain-sizing", "python")
    namespace = {}
    if outcome == "lookup-unavailable":
        with pytest.raises(ClientConnectionError) as failure:
            exec(compile(example, "documented uncertain sizing", "exec"), namespace)
        assert failure.value.key == namespace["original_key"]
        assert "envelope" not in namespace
    else:
        exec(compile(example, "documented uncertain sizing", "exec"), namespace)
        assert namespace["envelope"].command == "plan"
        assert namespace["operation_id"] == OPERATION
    posts = [request for request in seen if request.method == "POST"]
    lookups = [request for request in seen if request.url.path.endswith("/lookup")]
    assert len(posts) == 1
    assert len(lookups) == (outcome != "acknowledged")
    for request in [*posts, *lookups]:
        assert request.headers["Idempotency-Key"] == namespace["original_key"]
    assert all(request.headers["Authorization"] == "Bearer " + TOKEN for request in seen)


def test_documented_mcp_pin_uses_registered_arguments_and_valid_reference_output():
    request = json.loads(
        documented_example("docs/mcp.md", "mcp-current-request", "json", kind="schema")
    )
    response = json.loads(
        documented_example("docs/mcp.md", "mcp-current-response", "json", kind="schema")
    )
    frame = MetadataRead.model_validate(response)
    reference = Reference.model_validate(frame.envelope.data["reference"])
    arguments = request["params"]["arguments"]
    assert request["method"] == "tools/call"
    assert frame.envelope.command == "reference read"
    assert frame.envelope.data["locator_base"] == "published/"
    assert arguments == {
        "repository_type": reference.repository_type,
        "repository_id": reference.repository_id,
    }

    class ReferenceReads:
        async def get_current_reference(self, repository_type, repository_id):
            assert (repository_type, repository_id) == (
                reference.repository_type,
                reference.repository_id,
            )
            return frame

    server = FastMCP("documented reference")
    install_read_tools(server, cast("MetadataReadPort", ReferenceReads()), max_page_size=1000)

    async def call():
        async with Client(server) as client:
            result = await client.call_tool(request["params"]["name"], arguments)
            assert not result.is_error
            assert result.structured_content == response

    asyncio.run(call())


def without_fences(text):
    return re.sub(r"(?ms)^```[^\n]*\n.*?^```[ \t]*$", "", text)


def anchors(path):
    return CHECKER["markdown_references"](path.read_text())[1]


def test_current_interface_documentation_has_resolvable_local_files_and_anchors():
    assert CHECKER["check_links"](ROOT, [ROOT / relative for relative in INTERFACE_DOCS]) == []


def test_disabled_server_factory_imports_no_mcp_and_creates_no_archive_or_control_state(tmp_path):
    # Use a fresh interpreter so later optional-extra test collection cannot
    # conceal an eager import. This remains meaningful with MCP installed.
    code = """
import json, sys
from pathlib import Path
from hfcache.api.app import create_app
from hfcache.server_config import validate_server_config_mapping
root = Path(sys.argv[1])
server = validate_server_config_mapping({
    'schema_version': 1,
    'archive_config': str(root / 'absent-policy.toml'),
    'state_directory': str(root / 'absent-state'),
    'credentials': {
        'writer': {'file': str(root / 'absent-writer.token')},
        'mcp_reader': {'file': str(root / 'absent-mcp.token')},
    },
    'mcp_enabled': False,
})
app = create_app(server, instance_lock_path=root / 'absent-instance.lock')
loaded = [name for name in sys.modules if name in {'fastmcp', 'mcp'}
          or name.startswith(('fastmcp.', 'mcp.'))]
print(json.dumps({'loaded': loaded, 'created': list(root.iterdir()),
                  'paths': [getattr(route, 'path', None) for route in app.routes]}))
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", code, str(tmp_path)],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    payload = json.loads(result.stdout)
    assert payload["loaded"] == []
    assert payload["created"] == []
    assert not any(path.startswith("/mcp") for path in payload["paths"])
