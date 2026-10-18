"""`doctor --read-only` against the real NFS archive on this writer.

Marked `nfs` and deselected by default. Run it with `pytest -m nfs`.

Every other test in the suite substitutes a temporary directory and a fabricated
mountinfo line for the archive. That substitution is what makes the suite
portable, and it is also exactly what a mount proof must not rely on: a parser
that agrees with a line this repository wrote proves nothing about the line the
kernel writes. So this file reads `/proc/self/mountinfo` for real, against the
real `nas.lab.example.com:/mnt/tank/huggingface-archive` mount, and checks
that `docs/cli.md` §2 rows 2-5 pass on it.

`--read-only` is not a convenience here, it is the whole safety argument: the
archive is live, and initialization is authorized exactly once at the §29 rollout
checkpoint. Nothing in the read-only half of this file writes, and one test
asserts that by comparing the mount's contents before and after.

The file runs against a deployment in either state. Before the checkpoint the
archive is uninitialized and the checks that need a sentinel skip; after it they
are the ones that matter most, because docs/storage-requirements.md effective writability means
effective
writability and the three the doctor capability contract publication capabilities cannot be
established on
this export any other way than by performing them.
"""

import json
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

pytestmark = pytest.mark.nfs

ARCHIVE_ROOT = Path("/srv/hfcache")
DEPLOYED_CONFIG = Path("/etc/hfcache/config.toml")

SENTINEL = ARCHIVE_ROOT / ".hfcache-root"

# Any UUID validates when no sentinel exists to compare it against. Once the
# archive is initialized the id has to be the one the archive actually carries,
# or every check past the sentinel reports `HFMNT007` and proves nothing.
FALLBACK_ARCHIVE_ID = "3f2a1c88-7b40-4a2e-9c1d-0e5b6a7f8d90"


def archive_id() -> str:
    """The deployment's archive id, from the best source this user can read.

    `/etc/hfcache/config.toml` first, which is the deployment's own answer. It is
    mode `0640` root:hfcache and the suite runs as an ordinary developer account,
    so that usually fails — and it must keep failing rather than the account be
    added to the group, because the mode is the contract (docs/deployment-centos-stream-10.md
    native profile).

    The sentinel is the fallback and is readable here for the reason docs/storage-requirements.md
    effective writability
    gives: the export maps every client identity to the dataset owner. Taking the
    id from there does make the `sentinel` check's *comparison* trivially satisfy
    itself — what it still proves on the live mount is that the sentinel parses,
    that its schema version is one this build knows, and that the layout behind it
    is intact. `FS-03`'s mismatch path is unit-tested against a fabricated
    sentinel, where a mismatch can be arranged without corrupting a live archive.
    """
    for source, extract in (
        (DEPLOYED_CONFIG, lambda payload: payload["storage"]["archive_id"]),
        (SENTINEL, lambda payload: payload["archive_id"]),
    ):
        try:
            raw = source.read_bytes()
        except OSError:
            continue
        payload = tomllib.loads(raw.decode()) if source.suffix == ".toml" else json.loads(raw)
        return str(extract(payload))
    return FALLBACK_ARCHIVE_ID


CONFIG = f"""
schema_version = 1

[storage]
archive_root = "{ARCHIVE_ROOT}"
archive_id = "{archive_id()}"

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


def test_read_only_exits_zero_against_the_live_mount(config_file: Path):
    assert run(config_file, "doctor", "--read-only").returncode == 0


def test_nothing_is_written_to_the_live_mount(config_file: Path):
    before = sorted(path.name for path in ARCHIVE_ROOT.iterdir())

    run(config_file, "doctor", "--read-only")

    assert sorted(path.name for path in ARCHIVE_ROOT.iterdir()) == before


# --------------------------------------------------------------------------- #
# The mutating doctor (`STO-009`)
# --------------------------------------------------------------------------- #
#
# These are the assertions that need an initialized archive, so they could not
# run until the §29 rollout checkpoint spent the §36.4 one-time authorization —
# after `HOST-004`, not before. They were written at `STO-009` and skipped until
# then, so the checkpoint ran tests that already existed rather than ones written
# to fit whatever it found.


def initialized() -> bool:
    return (ARCHIVE_ROOT / ".hfcache-root").is_file()


needs_archive = pytest.mark.skipif(
    not initialized(),
    reason="the archive is not initialized; `archive init` runs once at the §29 checkpoint",
)

before_archive = pytest.mark.skipif(
    initialized(),
    reason="the archive is initialized; this is the pre-checkpoint contract",
)


@before_archive
def test_the_archive_is_reported_as_not_yet_initialized(checks: dict[str, dict]):
    # The state a fresh deployment is in, before the §29 rollout checkpoint.
    # Operator state rather than a failure, so `--read-only` still exits `0`.
    for name in ("sentinel", "staging_filesystem"):
        assert checks[name]["outcome"] == "skipped"
        assert "not initialized" in checks[name]["detail"]


@needs_archive
def test_the_sentinel_and_layout_are_readable_without_writing(checks: dict[str, dict]):
    # The counterpart, once the archive exists: both answers come from reading,
    # so `--read-only` proves the archive's identity and that staging and every
    # publication destination are on one filesystem (`FS-04`) without touching it.
    for name in ("sentinel", "staging_filesystem"):
        assert checks[name]["outcome"] == "pass", checks[name]["detail"]


@pytest.fixture(scope="module")
def mutating_checks(config_file: Path) -> dict[str, dict]:
    result = run(config_file, "doctor")
    envelope = json.loads(result.stdout)
    return {check["name"]: check for check in envelope["data"]["checks"]}


@needs_archive
def test_the_sentinel_on_the_live_mount_names_the_configured_archive(
    mutating_checks: dict[str, dict],
):
    assert mutating_checks["sentinel"]["outcome"] == "pass"


@needs_archive
def test_the_live_mount_is_effectively_writable(mutating_checks: dict[str, dict]):
    # Under the Mapall export this cannot be established any other way: the
    # owner has no local account, so only performing the write answers it
    # (docs/storage-requirements.md effective writability).
    assert mutating_checks["directory_writability"]["outcome"] == "pass"


@needs_archive
def test_every_publication_capability_holds_on_the_real_dataset(
    mutating_checks: dict[str, dict],
):
    # docs/architecture.md publication contract. Hardlink, atomic directory rename, and atomic ref
    # replacement
    # are the three things a publication is made of, and NFS is exactly where an
    # assumption about them would be wrong.
    for name in ("hardlink_capability", "atomic_directory_rename", "reference_replacement"):
        assert mutating_checks[name]["outcome"] == "pass", mutating_checks[name]["detail"]


@needs_archive
def test_the_mutating_doctor_is_clean_on_the_live_mount(config_file: Path):
    assert run(config_file, "doctor").returncode == 0


@needs_archive
def test_the_mutating_doctor_leaves_no_probe_behind(config_file: Path):
    probes = ARCHIVE_ROOT / ".store" / "health"

    run(config_file, "doctor")

    assert list(probes.iterdir()) == []
