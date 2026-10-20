"""Install an exact offline wheel for private-socket CLI acceptance (CP-02/08)."""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_ISOLATED_ENTRYPOINT = """
import os, runpy, sys
executable, archive, source, endpoint = sys.argv[1:5]
del sys.argv[1:5]
blocked = tuple(os.fsencode(path) for path in (archive, source, '/srv/hfcache', '/etc/hfcache'))
def audit(event, arguments):
    if event in {'open', 'os.listdir', 'os.scandir'} and arguments:
        path = arguments[0]
        if isinstance(path, (str, bytes)):
            selected = os.fsencode(os.path.abspath(path))
            if any(selected == root or selected.startswith(root+b'/') for root in blocked):
                raise RuntimeError('Forbidden client archive, writer-policy or source access')
    if event == 'socket.connect':
        address = arguments[1]
        if not isinstance(address, (str, bytes)) or os.fsdecode(address) != endpoint:
            raise RuntimeError('Forbidden non-fixture network access')
sys.addaudithook(audit)
sys.argv[0] = executable
runpy.run_path(executable, run_name='__main__')
"""


def _checked(arguments, *, cwd):
    completed = subprocess.run(
        arguments, cwd=cwd, capture_output=True, text=True, timeout=120, check=False
    )
    assert completed.returncode == 0, completed.stderr[-8192:]
    return completed.stdout


@dataclass(frozen=True)
class InstalledCli:
    workspace: Path
    python: Path
    executable: Path
    identity: dict

    def invoke(self, settings, archive, endpoint, *arguments):
        # Deliberately poison PYTHONPATH: -I and the installed entrypoint must
        # prevent the source checkout from supplying the executing package.
        environment = os.environ | {"PYTHONPATH": str(ROOT / "src")}
        result = subprocess.run(
            [
                str(self.python),
                "-I",
                "-c",
                _ISOLATED_ENTRYPOINT,
                str(self.executable),
                str(archive),
                str(ROOT / "src"),
                str(endpoint),
                "--json",
                "--client-config",
                str(settings),
                *arguments,
            ],
            cwd=self.workspace,
            env=environment,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert "Forbidden client" not in result.stderr
        assert "Forbidden non-fixture" not in result.stderr
        assert len(result.stdout.encode()) <= 16 * 1024 * 1024
        return result


@pytest.fixture(scope="session")
def installed_cli(tmp_path_factory):
    workspace = tmp_path_factory.mktemp("installed-cli-private-socket")
    uv = shutil.which("uv")
    assert uv is not None, "Installed-wheel acceptance requires the existing locked uv toolchain"
    dist = workspace / "dist"
    _checked([uv, "build", "--offline", "--wheel", "--out-dir", str(dist)], cwd=ROOT)
    (wheel,) = dist.glob("*.whl")
    requirements = workspace / "requirements.txt"
    _checked(
        [
            uv,
            "export",
            "--locked",
            "--offline",
            "--no-dev",
            "--no-emit-project",
            "--no-hashes",
            "--output-file",
            str(requirements),
        ],
        cwd=ROOT,
    )
    environment = workspace / "environment"
    _checked([uv, "venv", "--offline", "--python", sys.executable, str(environment)], cwd=workspace)
    python = environment / "bin/python"
    _checked(
        [uv, "pip", "sync", "--offline", "--python", str(python), str(requirements)],
        cwd=workspace,
    )
    _checked(
        [uv, "pip", "install", "--offline", "--no-deps", "--python", str(python), str(wheel)],
        cwd=workspace,
    )
    executable = environment / "bin/hfcache"
    assert executable.read_text().startswith(f"#!{python}\n")
    assert "from hfcache.cli import app" in executable.read_text()
    package = Path(
        _checked(
            [
                str(python),
                "-I",
                "-c",
                "import pathlib,hfcache; print(pathlib.Path(hfcache.__file__).parent)",
            ],
            cwd=workspace,
        ).strip()
    )
    assert package.is_relative_to(environment)
    inputs = hashlib.sha256()
    count = 0
    with zipfile.ZipFile(wheel) as bundle:
        packaged = {
            name
            for name in bundle.namelist()
            if name.startswith("hfcache/") and name.endswith(".py")
        }
        expected = {
            str(path.relative_to(ROOT / "src")) for path in (ROOT / "src/hfcache").rglob("*.py")
        }
        assert packaged == expected, "Every source module must be included in the installed wheel"
        for name in sorted(bundle.namelist()):
            if not name.startswith("hfcache/") or not name.endswith(".py"):
                continue
            body = bundle.read(name)
            relative = Path(name).relative_to("hfcache")
            assert (package / relative).read_bytes() == body
            assert (ROOT / "src" / name).read_bytes() == body
            inputs.update(name.encode() + b"\0" + body + b"\0")
            count += 1
    assert count > 0
    identity = {
        "wheel_sha256": hashlib.sha256(wheel.read_bytes()).hexdigest(),
        "python_package_source_wheel_sha256": inputs.hexdigest(),
        "matched_python_files": count,
        "locked_base_requirements_sha256": hashlib.sha256(requirements.read_bytes()).hexdigest(),
        "installed_console_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
        "python_version": _checked([str(python), "-I", "--version"], cwd=workspace).strip(),
        "isolated_entrypoint": True,
        "cwd_outside_checkout": not workspace.is_relative_to(ROOT),
    }
    (workspace / "identity.json").write_text(json.dumps(identity, sort_keys=True) + "\n")
    return InstalledCli(workspace, python, executable, identity)
