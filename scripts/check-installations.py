#!/usr/bin/env python3
"""Install the locked base/server wheel into real isolated environments.

Default gate runs offline from uv's cache populated by its server-extra sync.
This proves optional imports and packaging rather than hiding packages in mocks.
"""

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
    version = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    wheels = sorted((ROOT / "dist").glob(f"hfcache-{version}-*.whl"))
    if len(wheels) != 1:
        message = "expected exactly one freshly built hfcache wheel"
        raise SystemExit(message)
    with tempfile.TemporaryDirectory(prefix="hfcache-install-") as directory:
        scratch = Path(directory)
        for extra in (None, "server"):
            label = extra or "base"
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
            if extra:
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
                "print(json.dumps({'version':__version__,'server':"
                "importlib.util.find_spec('fastapi') is not None,'uvicorn':"
                "importlib.util.find_spec('uvicorn') is not None,'mcp':"
                "importlib.util.find_spec('fastmcp') is not None}))"
            )
            result = json.loads(run([str(python), "-I", "-c", code], cwd=scratch))
            assert result["server"] is bool(extra), result
            assert result["uvicorn"] is bool(extra), result
            assert result["mcp"] is False, result
            executable = environment / "bin" / "hfcache"
            assert "Usage:" in run([str(executable), "--help"], cwd=scratch)
            version = json.loads(run([str(executable), "--json", "version"], cwd=scratch))
            assert version["schema_version"] == 1, version
            assert version["exit_code"] == 0, version
            if extra:
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
            print(f"locked {label} wheel installation/import/help/version passed")


if __name__ == "__main__":
    main()
