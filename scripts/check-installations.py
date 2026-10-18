#!/usr/bin/env python3
"""Install locked base, server and server-plus-MCP wheels into isolated environments.

Default gate runs offline from uv's cache populated by its implemented-extra sync.
This proves optional imports and packaging rather than hiding packages in mocks.
"""

import argparse
import json
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(arguments, *, cwd):
    try:
        return subprocess.run(  # noqa: S603 - fixed repository-owned gate commands, no shell
            arguments, cwd=cwd, check=True, text=True, capture_output=True
        ).stdout
    except subprocess.CalledProcessError as exc:
        print(exc.stdout, file=sys.stderr)
        print(exc.stderr, file=sys.stderr)
        raise


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    version = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    wheels = sorted((ROOT / "dist").glob(f"hfcache-{version}-*.whl"))
    if len(wheels) != 1:
        message = "expected exactly one freshly built hfcache wheel"
        raise SystemExit(message)
    with tempfile.TemporaryDirectory(prefix="hfcache-install-") as directory:
        scratch = Path(directory)
        for extras in ((), ("server",), ("server", "mcp")):
            label = "+".join(extras) or "base"
            environment = scratch / label
            requirements = scratch / f"{label}-requirements.txt"
            export = [
                "uv",
                "export",
                "--locked",
                "--no-dev",
                "--no-emit-project",
                "--no-hashes",
                "--format",
                "requirements-txt",
                "--output-file",
                str(requirements),
            ]
            for extra in extras:
                export.extend(("--extra", extra))
            run(export, cwd=ROOT)
            run(["uv", "venv", "--python", sys.executable, str(environment)], cwd=scratch)
            python = environment / "bin" / "python"
            run(
                ["uv", "pip", "sync", "--offline", "--python", str(python), str(requirements)],
                cwd=scratch,
            )
            run(
                [
                    "uv",
                    "pip",
                    "install",
                    "--offline",
                    "--no-deps",
                    "--python",
                    str(python),
                    str(wheels[0]),
                ],
                cwd=scratch,
            )
            code = (
                "import importlib.util,json; "
                "from hfcache import __version__; "
                "import hfcache.cli,hfcache.http_transport,hfcache.api.auth; "
                "import hfcache.client,hfcache.client_config; "
                "import hfcache.scheduled_client,hfcache.verification_worker; "
                "print(json.dumps({'version':__version__,'server':"
                "importlib.util.find_spec('fastapi') is not None,'uvicorn':"
                "importlib.util.find_spec('uvicorn') is not None,'mcp':"
                "importlib.util.find_spec('fastmcp') is not None,'cold':"
                "not any(name in __import__('sys').modules for name in "
                "('hfcache.services.commands','hfcache.archive','hfcache.hub',"
                "'huggingface_hub','hfcache.verification_executor')),'frameworks_cold':"
                "not any(name in __import__('sys').modules for name in "
                "('fastapi','uvicorn','fastmcp','mcp'))}))"
            )
            result = json.loads(run([str(python), "-I", "-c", code], cwd=scratch))
            assert result["server"] is ("server" in extras), result
            assert result["uvicorn"] is ("server" in extras), result
            assert result["mcp"] is ("mcp" in extras), result
            assert result["cold"] is True, result
            assert result["frameworks_cold"] is True, result
            executable = environment / "bin" / "hfcache"
            assert "Usage:" in run([str(executable), "--help"], cwd=scratch)
            reported = json.loads(run([str(executable), "--json", "version"], cwd=scratch))
            assert reported["schema_version"] == 1, reported
            assert reported["exit_code"] == 0, reported
            if "server" in extras:
                run(
                    [
                        str(python),
                        "-I",
                        "-c",
                        (
                            "import hfcache.api.security,uvicorn; "
                            "from fastapi.security import HTTPBearer"
                        ),
                    ],
                    cwd=scratch,
                )
                run(
                    [
                        str(python),
                        "-I",
                        "-c",
                        """import asyncio
import sys
from pathlib import Path
from hfcache.api.app import create_app
from hfcache.errors import ConfigurationError
from hfcache.server_config import validate_server_config_mapping

root = Path(sys.argv[1]) / 'never-created'
settings = validate_server_config_mapping({
    'schema_version': 1,
    'archive_config': str(root / 'archive.toml'),
    'state_directory': str(root / 'state'),
    'credentials': {
        'writer': {'file': str(root / 'writer.token')},
        'mcp_reader': {'file': str(root / 'mcp.token')},
    },
})
disabled = create_app(settings)
assert 'fastmcp' not in sys.modules and 'mcp' not in sys.modules
assert all(getattr(route, 'path', None) != '/mcp' for route in disabled.routes)
try:
    enabled = create_app(settings.model_copy(update={'mcp_enabled': True}))
except ConfigurationError as error:
    assert sys.argv[2] == 'absent'
    assert error.problems[0].code == 'HFCFG005'
else:
    assert sys.argv[2] == 'present'
    assert any(getattr(route, 'path', None) == '/mcp' for route in enabled.routes)
    from hfcache.mcp_tools import TOOL_NAMES
    tools = asyncio.run(enabled.state.mcp_server.list_tools())
    assert len(tools) == 9
    assert {tool.name for tool in tools} == TOOL_NAMES
    assert asyncio.run(enabled.state.mcp_server.list_resources()) == []
    assert asyncio.run(enabled.state.mcp_server.list_resource_templates()) == []
    assert asyncio.run(enabled.state.mcp_server.list_prompts()) == []
assert not root.exists()
""",
                        str(environment),
                        "present" if "mcp" in extras else "absent",
                    ],
                    cwd=scratch,
                )
            if "mcp" in extras:
                run(
                    [
                        str(python),
                        "-I",
                        "-c",
                        (
                            "from fastmcp import FastMCP; "
                            "from fastmcp.server.auth import TokenVerifier,AccessToken; "
                            "import hfcache.mcp"
                        ),
                    ],
                    cwd=scratch,
                )
            print(f"locked {label} wheel installation/import/help/version passed")


if __name__ == "__main__":
    main()
