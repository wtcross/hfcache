"""Current REST configuration/docs and disabled optional imports (API-016)."""

import json
import re
import subprocess
import sys
from pathlib import Path

import httpx
import pytest

from hfcache import client as client_module
from hfcache import client_config
from hfcache.client import ApiClient
from hfcache.client_config import resolve_client_config
from hfcache.config import load_config
from hfcache.server_config import load_server_config
from tests.docs_contract import CHECKER
from tests.unit.test_api_client_adversarial import BASE, TOKEN, _capabilities, _read, _response

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
    "docs/cockpit.md",
    "docs/cockpit-plugin/README.md",
    "docs/cockpit-plugin/installation.md",
    "docs/cockpit-plugin/usage.md",
    "docs/cockpit-plugin/troubleshooting.md",
)


@pytest.mark.parametrize(
    ("relative", "loader"),
    [
        ("examples/config.toml", load_config),
        ("packaging/server.toml", load_server_config),
        ("packaging/client.example.toml", resolve_client_config),
        ("packaging/scheduled-client.example.toml", resolve_client_config),
        ("packaging/cockpit-client.toml", resolve_client_config),
    ],
)
def test_all_five_current_configuration_examples_use_their_strict_independent_loader(
    relative, loader
):
    # Parse only. Loading settings neither resolves a credential nor opens the
    # configured archive, starts a daemon or contacts the Hub/API.
    path = ROOT / relative
    before = path.read_bytes()
    parsed = loader(path)
    assert parsed.schema_version == 1
    assert path.read_bytes() == before


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
    document = (ROOT / "docs/api-client.md").read_text()
    (example,) = re.findall(r"(?ms)^```python\n(.*?)^```", document)
    namespace = {}
    exec(compile(example, "documented SDK example", "exec"), namespace)
    assert seen == [
        ("/management/api/v1/capabilities", "Bearer " + TOKEN),
        ("/management/api/v1/version", "Bearer " + TOKEN),
    ]
    assert namespace["envelope"].command == "version"
    assert (settings.read_bytes(), token.read_bytes()) == before


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
