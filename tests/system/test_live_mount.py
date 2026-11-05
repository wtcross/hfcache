"""Opt-in application SDK storage checks against the actual NFS mount.

The public CLI is API-only: --config is a candidate input, not a local doctor
transport. These tests exercise the same supported storage-check SDK used by
server diagnostics, in a separate process against the kernel mount table.
Read-only cases skip every write probe and acquire no lock. Mutating cases
require the caller's access to the existing original runtime lock and use the
application's guarded storage-preflight path; they never initialize an archive.

The production plan selects only the read-only cases here. Actual rootless
writer transactions and metadata writes are accepted through separately retained
genuine administrator UI jobs, not inferred from this host SDK test process.
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


_STORAGE_SCRIPT = r"""
import json
import sys
from pathlib import Path

from hfcache.config import load_config
from hfcache.paths import ArchiveLayout
from hfcache.preflight import guarded, storage_checks

config = load_config(Path(sys.argv[1]))
layout = ArchiveLayout(config.storage.archive_root)
if sys.argv[2] == "read-only":
    checks = storage_checks(layout, storage=config.storage, read_only=True)
else:
    # Supported application path retains the common original lock before probes.
    with guarded(layout, storage=config.storage, command="doctor", lock_wait_seconds=0) as held:
        checks = list(held)
failed = any(check.outcome == "fail" for check in checks)
print(json.dumps({"data": {"checks": [check.as_entry() for check in checks]}}))
raise SystemExit(2 if failed else 0)
"""


def run(config_file: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    """Use the application SDK; no API job, Hub call or retired CLI option."""
    assert arguments in (("doctor",), ("doctor", "--read-only"))
    mode = "read-only" if "--read-only" in arguments else "guarded-probes"
    return subprocess.run(
        [sys.executable, "-I", "-B", "-c", _STORAGE_SCRIPT, str(config_file), mode],
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
