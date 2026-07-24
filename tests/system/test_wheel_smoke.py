"""The built wheel installs into a clean environment and the CLI runs.

Marked `build` and deselected by default because it builds artifacts and
creates a virtual environment. Run it with `pytest -m build`, or through
`scripts/check.sh --with-build`.

This is the check that catches packaging mistakes the development environment
hides: a missing console script, a module left out of the wheel, or a runtime
import that only resolves because a dev dependency happens to be installed.
"""

import json
import shutil
import subprocess
import tomllib
from pathlib import Path

import pytest

pytestmark = pytest.mark.build

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _uv() -> str:
    uv = shutil.which("uv")
    if uv is None:  # pragma: no cover - environment dependent
        pytest.skip("uv is not on PATH")
    return uv


def _run(*command: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
        timeout=600,
    )


@pytest.fixture(scope="module")
def declared_version() -> str:
    pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return pyproject["project"]["version"]


@pytest.fixture(scope="module")
def installed_cli(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Build both artifacts, install the wheel into a fresh venv, return the CLI."""
    uv = _uv()
    workspace = tmp_path_factory.mktemp("wheel-smoke")
    dist = workspace / "dist"

    _run(uv, "build", "--out-dir", str(dist), cwd=PROJECT_ROOT)

    wheels = sorted(dist.glob("*.whl"))
    sdists = sorted(dist.glob("*.tar.gz"))
    assert len(wheels) == 1, f"expected exactly one wheel, got {wheels}"
    assert len(sdists) == 1, f"expected exactly one sdist, got {sdists}"

    venv = workspace / "venv"
    _run(uv, "venv", "--python", "3.14", str(venv))
    _run(uv, "pip", "install", "--python", str(venv / "bin" / "python"), str(wheels[0]))

    return venv / "bin" / "hfcache"


def test_console_script_is_installed(installed_cli: Path):
    assert installed_cli.is_file()


def test_help_runs_from_a_clean_install(installed_cli: Path):
    result = _run(str(installed_cli), "--help")
    assert "Usage:" in result.stdout


def test_version_reports_the_declared_version(installed_cli: Path, declared_version: str):
    result = _run(str(installed_cli), "--json", "version")
    envelope = json.loads(result.stdout)

    assert envelope["data"]["application"] == declared_version
    assert envelope["exit_code"] == 0
    # The runtime dependency set alone must be enough; no dev package is present
    # in this environment, so a resolved Hub version proves the wheel's metadata.
    assert envelope["data"]["huggingface_hub"] != "unknown"
    assert envelope["data"]["transfer_backend"].startswith("xet ")


def test_module_invocation_works_from_a_clean_install(installed_cli: Path):
    python = installed_cli.parent / "python"
    result = _run(str(python), "-m", "hfcache", "version")
    assert "application" in result.stdout
