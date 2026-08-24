from __future__ import annotations

import stat
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = PROJECT_ROOT / "scripts" / "setup-hfcache-consumer-model-store.sh"


def run_script(*arguments: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(SCRIPT), *arguments],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )


def test_consumer_model_store_script_is_executable_bash() -> None:
    assert SCRIPT.stat().st_mode & stat.S_IXUSR
    subprocess.run(["bash", "-n", str(SCRIPT)], check=True, timeout=10)


def test_consumer_model_store_script_help_is_safe_from_any_directory(
    tmp_path: Path,
) -> None:
    result = run_script("--help", cwd=tmp_path)

    assert result.returncode == 0
    assert result.stderr == ""
    assert "COPY_REVISION_PY" in result.stdout
    assert "consumer" in result.stdout


def test_consumer_model_store_script_rejects_unknown_options(tmp_path: Path) -> None:
    result = run_script("--not-an-option", cwd=tmp_path)

    assert result.returncode == 64
    assert "unknown option: --not-an-option" in result.stderr
    assert result.stdout == ""
