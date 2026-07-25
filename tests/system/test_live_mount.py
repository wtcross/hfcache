"""`doctor --read-only` against the real NFS archive on this writer.

Marked `nfs` and deselected by default. Run it with `pytest -m nfs`.

Every other test in the suite substitutes a temporary directory and a fabricated
mountinfo line for the archive. That substitution is what makes the suite
portable, and it is also exactly what a mount proof must not rely on: a parser
that agrees with a line this repository wrote proves nothing about the line the
kernel writes. So this file reads `/proc/self/mountinfo` for real, against the
real `nas.lab.cross.solutions:/mnt/tank/huggingface-archive` mount, and checks
that `docs/cli.md` §2 rows 2-5 pass on it.

`--read-only` is not a convenience here, it is the whole safety argument: the
archive is live, it is not yet initialized, and initialization is authorized
exactly once at the §29 rollout checkpoint. Nothing in this file writes, and one
test asserts that by comparing the mount's contents before and after.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.nfs

ARCHIVE_ROOT = Path("/srv/hfcache")

# Any UUID validates; the sentinel it would be compared against does not exist
# yet, and the checks exercised here never read one.
ARCHIVE_ID = "3f2a1c88-7b40-4a2e-9c1d-0e5b6a7f8d90"

CONFIG = f"""
schema_version = 1

[storage]
archive_root = "{ARCHIVE_ROOT}"
archive_id = "{ARCHIVE_ID}"

[[repositories]]
id = "hf-internal-testing/tiny-random-gpt2"
type = "model"
"""


@pytest.fixture(scope="module")
def config_file(tmp_path_factory: pytest.TempPathFactory) -> Path:
    path = tmp_path_factory.mktemp("live-mount") / "config.toml"
    path.write_text(CONFIG, encoding="utf-8")
    return path


def run(config_file: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    """Invoke the CLI out of process, so nothing this suite patched can apply."""
    return subprocess.run(
        [sys.executable, "-m", "hfcache", "--json", "--config", str(config_file), *arguments],
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )


@pytest.fixture(scope="module")
def checks(config_file: Path) -> dict[str, dict]:
    result = run(config_file, "doctor", "--read-only")
    envelope = json.loads(result.stdout)
    return {check["name"]: check for check in envelope["data"]["checks"]}


def test_the_archive_root_is_a_read_write_nfs_mount(checks: dict[str, dict]):
    # `docs/cli.md` §2 rows 2-5, proven against the kernel's own mount table.
    for name in ("archive_root", "mount_point", "filesystem_type", "mount_writable"):
        assert checks[name]["outcome"] == "pass", f"{name}: {checks[name]['detail']}"


def test_the_filesystem_is_reported_as_nfs4(checks: dict[str, dict]):
    assert "nfs4" in checks["filesystem_type"]["detail"]


def test_the_writability_probe_is_skipped_under_read_only(checks: dict[str, dict]):
    assert checks["directory_writability"]["outcome"] == "skipped"
    assert "read-only" in checks["directory_writability"]["detail"]


def test_the_archive_is_reported_as_not_yet_initialized(checks: dict[str, dict]):
    # Initialization is authorized exactly once, at the §29 rollout checkpoint
    # after `HOST-004`. Until then this is the expected answer, and it is
    # operator state rather than a failure.
    for name in ("sentinel", "staging_filesystem"):
        assert checks[name]["outcome"] == "skipped"
        assert "not initialized" in checks[name]["detail"]


def test_read_only_exits_zero_against_the_live_mount(config_file: Path):
    assert run(config_file, "doctor", "--read-only").returncode == 0


def test_nothing_is_written_to_the_live_mount(config_file: Path):
    before = sorted(path.name for path in ARCHIVE_ROOT.iterdir())

    run(config_file, "doctor", "--read-only")

    assert sorted(path.name for path in ARCHIVE_ROOT.iterdir()) == before
