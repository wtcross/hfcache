"""Current REST configuration/docs and disabled optional imports (API-016)."""

import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

import pytest

from hfcache.client_config import resolve_client_config
from hfcache.config import load_config
from hfcache.server_config import load_server_config

ROOT = Path(__file__).resolve().parents[2]
INTERFACE_DOCS = (
    "README.md",
    "docs/api.md",
    "docs/server.md",
    "docs/api-client.md",
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


def without_fences(text):
    return re.sub(r"(?ms)^```[^\n]*\n.*?^```[ \t]*$", "", text)


def anchors(path):
    text = without_fences(path.read_text())
    result = set(re.findall(r'<a\s+(?:id|name)="([^"]+)"', text))
    counts = {}
    for heading in re.findall(r"(?m)^#{1,6}\s+(.+?)(?:\s+#+)?$", text):
        label = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", heading)
        slug = "".join(
            character for character in label.lower() if character.isalnum() or character in " _-"
        )
        slug = slug.replace(" ", "-")
        number = counts.get(slug, 0)
        counts[slug] = number + 1
        result.add(slug if number == 0 else f"{slug}-{number}")
    return result


def test_current_interface_documentation_has_resolvable_local_files_and_anchors():
    failures = []
    known_anchors = {}
    for relative in INTERFACE_DOCS:
        path = ROOT / relative
        text = without_fences(path.read_text())
        links = re.findall(r"\[[^\]\n]+\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)", text)
        links += re.findall(r"(?m)^\s*\[[^\]]+\]:\s*(\S+)", text)
        for link in links:
            parsed = urlsplit(link.strip("<>"))
            if parsed.scheme or parsed.netloc:
                continue
            target = path if not parsed.path else (path.parent / unquote(parsed.path)).resolve()
            if parsed.path.startswith("/"):
                target = ROOT / unquote(parsed.path).lstrip("/")
            if not target.exists():
                failures.append(f"{relative}: missing {link}")
            elif parsed.fragment and target.suffix == ".md":
                if target not in known_anchors:
                    known_anchors[target] = anchors(target)
                if unquote(parsed.fragment) not in known_anchors[target]:
                    failures.append(f"{relative}: missing anchor {link}")
    assert not failures, "\n".join(failures)


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
