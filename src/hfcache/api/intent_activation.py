"""Internal offline first activation for the protected release installer (INV-023).

Run only in the selected immutable application runtime, after the installer's
independent actual-executor drain and retained original archive-lock handoff.
The fixed runtime invocation has no network, secrets or archive mount. This
module validates/backs up both bounded local stores and provisions local state;
it never initializes an archive or repairs partial/previous activation.
"""

import argparse
import hashlib
import os
from pathlib import Path

from hfcache.api.intents import INTENT_NAME, MAX_INTENT_BYTES, IntentState, unavailable
from hfcache.api.lifecycle import open_directory
from hfcache.api.operations import OperationStore
from hfcache.models import dump, serialize

PUBLIC_STORE = Path("/var/lib/hfcache/api")
PRIVATE_STORE = Path("/var/lib/hfcache/verification")
COMPANION = Path("/run/hfcache/hfcache.lock.intent")


def _backup(store: OperationStore, target: Path) -> dict[str, str]:
    """Caller holds the pinned original store flock; preserve all validated bytes."""
    target.mkdir(mode=0o700)
    descriptor = open_directory(target)
    hashes = {}
    try:
        with os.scandir(store._fd) as children:  # noqa: SLF001 - offline store transaction
            names = sorted(child.name for child in children)
        for name in names:
            maximum = store.limits.max_store_bytes
            body = store._read(name, maximum)  # noqa: SLF001 - same validator/pinned fd
            output = os.open(
                name,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                0o600,
                dir_fd=descriptor,
            )
            try:
                with os.fdopen(output, "wb", closefd=False) as stream:
                    stream.write(body)
                    stream.flush()
                    os.fsync(output)
            finally:
                os.close(output)
            hashes[name] = hashlib.sha256(body).hexdigest()
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return hashes


def prepare_intent_state(
    archive_id: str,
    backup: Path,
    *,
    public: Path = PUBLIC_STORE,
    private: Path = PRIVATE_STORE,
    companion: Path = COMPANION,
) -> None:
    """Single first-activation transaction; partial evidence is never overwritten."""
    initial = IntentState(schema_version=1, archive_id=archive_id)
    if any(not (root / ".lock").is_file() for root in (public, private)):
        raise unavailable()
    parent = open_directory(companion.parent)
    try:
        if os.path.lexists(companion) or backup.exists():
            raise unavailable()
        with (
            OperationStore(public, private=True) as api,
            OperationStore(private, private=True) as worker,
            api._locked(),  # noqa: SLF001 - coordinated offline transaction
            worker._locked(),  # noqa: SLF001 - coordinated offline transaction
        ):
            records, _ = api._scan()  # noqa: SLF001 - exact predecessor validator
            worker_records, _ = worker._scan()  # noqa: SLF001
            if any(record.archive_id != archive_id for record in (*records, *worker_records)):
                raise unavailable()
            backup_parent = open_directory(backup.parent)
            try:
                os.mkdir(backup.name, mode=0o700, dir_fd=backup_parent)
                os.fsync(backup_parent)
            finally:
                os.close(backup_parent)
            manifest = {
                "schema_version": 1,
                "archive_id": archive_id,
                "api": _backup(api, backup / "api"),
                "worker": _backup(worker, backup / "worker"),
            }
            descriptor = open_directory(backup)
            try:
                manifest_fd = os.open(
                    "manifest.json",
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                    0o600,
                    dir_fd=descriptor,
                )
                try:
                    with os.fdopen(manifest_fd, "wb", closefd=False) as stream:
                        stream.write(serialize(manifest).encode())
                        stream.flush()
                        os.fsync(manifest_fd)
                finally:
                    os.close(manifest_fd)
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
            descriptor = os.open(
                companion.name,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                0o600,
                dir_fd=parent,
            )
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
            os.fsync(parent)
            api._write(INTENT_NAME, dump(initial), MAX_INTENT_BYTES)  # noqa: SLF001 - original store flock retained
    finally:
        os.close(parent)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive-id", required=True)
    parser.add_argument("--backup-directory", type=Path, required=True)
    options = parser.parse_args()
    prepare_intent_state(options.archive_id, options.backup_directory)


if __name__ == "__main__":
    main()
