"""Explicit removal of proven abandoned staging, per `docs/recovery.md`.

Decision 103 limits this operation to empty directories and files whose bytes
still exist in a retained current publication. Terminal publication and recovery
journals remain the durable ownership evidence; deletion only reduces an already
rolled-back staging tree, and a retry proves the remaining subset again (FS-19).
"""

import hashlib
import os
import stat
from contextlib import contextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Final, NoReturn, final

from hfcache.errors import HfcacheError, RetentionError
from hfcache.hashing import ObjectIdentity
from hfcache.identity import CommitSha, PublicationId, RepositoryIdentity, TransactionId
from hfcache.logging import emit
from hfcache.manifests import RevisionManifest
from hfcache.models import ArchiveSentinel, Reference, TransactionJournal
from hfcache.paths import RepositoryLayout
from hfcache.storage import read_model
from hfcache.transactions import CHECKPOINTS, checkpoint_order_problems, read_journal

if TYPE_CHECKING:
    from collections.abc import Generator, Sequence
    from pathlib import Path

    from hfcache.manifests import FileEntry
    from hfcache.paths import ArchiveLayout

__all__ = [
    "QuarantineCleanupPlan",
    "apply_quarantine_cleanup",
    "plan_quarantine_cleanup",
    "plan_quarantine_cleanups",
]

_ROLLBACK: Final = (
    "resolved by recovery: the publication stopped before anything was published, so it rolls back"
)
_PREPUBLICATION: Final = CHECKPOINTS["publication"][:4]


@contextmanager
def _directory_fd(path: Path) -> Generator[int]:
    """Anchor every directory component, including the archive's ancestors."""
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    descriptor = os.open(path.anchor, flags)
    try:
        for component in path.parts[1:]:
            child = os.open(component, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        yield descriptor
    finally:
        os.close(descriptor)


def _same_directory(path: Path, descriptor: int) -> None:
    with _directory_fd(path) as current:
        wanted = os.fstat(descriptor)
        actual = os.fstat(current)
        if (wanted.st_dev, wanted.st_ino) != (actual.st_dev, actual.st_ino):
            _refuse(path, "the directory changed while it was being inspected")


def _state(info: os.stat_result) -> tuple[int, ...]:
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


@contextmanager
def _regular_fd(path: Path, parent: int) -> Generator[int]:
    descriptor = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            _refuse(path, "the candidate or retained copy is not a regular file")
        yield descriptor
    finally:
        os.close(descriptor)


def _digest_fd(path: Path, descriptor: int) -> tuple[str, tuple[int, ...]]:
    before = _state(os.fstat(descriptor))
    digest = hashlib.sha256()
    while block := os.read(descriptor, 1024 * 1024):
        digest.update(block)
    if _state(os.fstat(descriptor)) != before:
        _refuse(path, "the file changed while its bytes were being verified")
    return digest.hexdigest(), before


def _same_file(path: Path, parent: int, descriptor: int, expected: tuple[int, ...]) -> None:
    current = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
    if (
        not stat.S_ISREG(current.st_mode)
        or _state(current) != expected
        or _state(os.fstat(descriptor)) != expected
    ):
        _refuse(path, "the candidate or retained copy changed after hashing")
    _same_directory(path.parent, parent)


def _prove_pair(
    path: Path, retained: Path, *, size: int, sha256: str, remove: bool = False
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    """Hold both proven files and their parents through the exact candidate unlink."""
    with (
        _directory_fd(path.parent) as candidate_parent,
        _directory_fd(retained.parent) as retained_parent,
        _regular_fd(path, candidate_parent) as candidate,
        _regular_fd(retained, retained_parent) as original,
    ):
        candidate_digest, candidate_state = _digest_fd(path, candidate)
        retained_digest, retained_state = _digest_fd(retained, original)
        if any(
            digest != sha256 or state[2] != size
            for digest, state in (
                (candidate_digest, candidate_state),
                (retained_digest, retained_state),
            )
        ):
            _refuse(path, "candidate and retained bytes do not both match the trusted manifest")
        _same_file(path, candidate_parent, candidate, candidate_state)
        _same_file(retained, retained_parent, original, retained_state)
        if remove:
            os.unlink(path.name, dir_fd=candidate_parent)
            os.fsync(candidate_parent)
        return candidate_state, retained_state


def _remove_directory(path: Path) -> None:
    with _directory_fd(path.parent) as parent, _directory_fd(path) as child:
        _same_directory(path.parent, parent)
        named = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
        held = os.fstat(child)
        if not stat.S_ISDIR(named.st_mode) or (named.st_dev, named.st_ino) != (
            held.st_dev,
            held.st_ino,
        ):
            _refuse(path, "the directory changed before its removal")
        os.rmdir(path.name, dir_fd=parent)
        os.fsync(parent)


def _refuse(path: Path, detail: str) -> NoReturn:
    message = f"quarantine cleanup refused: {detail}; any remaining evidence is preserved (FS-19)"
    raise RetentionError.single(
        message,
        code="HFRET010",
        location=str(path),
    )


def _plain_path(layout: ArchiveLayout, path: Path, *, directory: bool = False) -> None:
    """Reject symlinks in every archive-relative ancestor before opening a path."""
    parts = path.relative_to(layout.root).parts
    current = layout.root
    for index, component in enumerate(("", *parts)):
        current = current / component
        info = current.lstat()
        needs_directory = index < len(parts) or directory
        if not (stat.S_ISDIR(info.st_mode) if needs_directory else stat.S_ISREG(info.st_mode)):
            _refuse(current, "expected an ordinary directory or regular file, without symlinks")


def _journal(layout: ArchiveLayout, path: Path) -> TransactionJournal:
    _plain_path(layout, path)
    file = read_journal(layout, path)
    journal = file.journal
    if file.unknown or checkpoint_order_problems(journal):
        _refuse(path, "the journal has unsupported fields or invalid checkpoint order")
    if path != layout.journal(TransactionId(journal.transaction_id)):
        _refuse(path, "the journal transaction id does not match its filename")
    return journal


def _journals(layout: ArchiveLayout) -> tuple[TransactionJournal, ...]:
    _plain_path(layout, layout.transactions, directory=True)
    journals = tuple(
        _journal(layout, path)
        for path in sorted(layout.transactions.iterdir())
        if path.suffix == ".json"
    )
    if any(not journal.is_resolved for journal in journals):
        _refuse(layout.transactions, "an unfinished transaction must be recovered first")
    return journals


def _ownership(
    layout: ArchiveLayout,
    identifier: TransactionId,
    journals: Sequence[TransactionJournal],
) -> tuple[RepositoryIdentity, TransactionId]:
    path = layout.journal(identifier)
    source = next((item for item in journals if item.transaction_id == identifier), None)
    if source is None:
        _refuse(path, "the original publication journal is missing")
    _plain_path(layout, layout.sentinel)
    sentinel = read_model(layout.sentinel, ArchiveSentinel, error=RetentionError, code="HFRET010")
    names = tuple(checkpoint.name for checkpoint in source.checkpoints)
    if (
        source.operation != "publication"
        or source.state != "failed"
        or source.completed_at is None
        or source.error is None
        or source.error.code != "HFTXN003"
        or source.error.message != _ROLLBACK
        or not names
        or names != _PREPUBLICATION[: len(names)]
        or source.archive_id != sentinel.archive_id
        or source.repository_type is None
        or source.repository_id is None
        or source.commit_sha is None
    ):
        _refuse(path, "the source is not a completed recovery rollback of unpublished staging")
    # Download-ahead journals have no publication id: ingestion allocates it
    # later in the manifest, without rewriting this optional journal scope.
    # The pre-publication checkpoint prefix and committed recovery proof own
    # this staging directory independently of a publication instance (TX-03).
    staging = layout.staging_for(identifier).directory
    if staging.exists() or staging.is_symlink():
        _refuse(staging, "the original staging path is still present")
    expected = {
        "resolved_transaction_id": str(identifier),
        "quarantine_path": str(layout.archive_relative(layout.quarantine_for(identifier))),
        "staging_absent": str(layout.archive_relative(staging)),
    }
    for journal in journals:
        if (
            journal.operation == "recovery"
            and journal.state == "committed"
            and journal.completed_at is not None
            and journal.archive_id == sentinel.archive_id
            and tuple(checkpoint.name for checkpoint in journal.checkpoints[-2:])
            == ("recovery_report_written", "recovery_completed")
            and any(
                checkpoint.name == "quarantine_staging" and checkpoint.evidence == expected
                for checkpoint in journal.checkpoints
            )
        ):
            return (
                RepositoryIdentity.of(source.repository_type, source.repository_id),
                TransactionId(journal.transaction_id),
            )
    _refuse(path, "no committed recovery journal proves this exact staging quarantine")


@final
@dataclass(frozen=True, slots=True)
class QuarantineFile:
    """A candidate file and the current retained copy that proves it redundant."""

    path: str
    size: int
    sha256: str
    retained_path: str
    identity: ObjectIdentity
    candidate_state: tuple[int, ...]
    retained_state: tuple[int, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "size": self.size,
            "sha256": self.sha256,
            "retained_path": self.retained_path,
        }


@final
@dataclass(frozen=True, slots=True)
class QuarantineCleanupPlan:
    """Reviewable transient evidence, rebuilt under the writer lock on apply."""

    transaction_id: TransactionId
    repository: str
    quarantine_path: str
    recovery_transaction_id: TransactionId
    files: tuple[QuarantineFile, ...]
    directories: tuple[str, ...]
    already_absent: bool

    @property
    def logical_bytes(self) -> int:
        return sum(entry.size for entry in self.files)

    def to_dict(self) -> dict[str, Any]:
        return {
            "transaction_id": self.transaction_id,
            "repository": self.repository,
            "quarantine_path": self.quarantine_path,
            "recovery_transaction_id": self.recovery_transaction_id,
            "files": [entry.to_dict() for entry in self.files],
            "directories": list(self.directories),
            "logical_bytes": self.logical_bytes,
            "already_absent": self.already_absent,
        }


def _contents(layout: ArchiveLayout, root: Path) -> tuple[tuple[Path, ...], tuple[str, ...]]:
    _plain_path(layout, root, directory=True)
    entries = tuple(root.iterdir())
    if any(entry.name != "tree" for entry in entries):
        _refuse(root, "only an abandoned staging tree is supported; unknown entries remain")
    files: list[Path] = []
    directories = [root]
    queue = list(entries)
    while queue:
        path = queue.pop()
        mode = path.lstat().st_mode
        if stat.S_ISDIR(mode):
            directories.append(path)
            queue.extend(path.iterdir())
        elif stat.S_ISREG(mode) and path != root / "tree":
            files.append(path)
        else:
            _refuse(path, "symlinks, special files and an invalid staging tree are not removable")
    return (
        tuple(sorted(files)),
        tuple(
            str(path.relative_to(root))
            for path in sorted(directories, key=lambda path: (-len(path.parts), str(path)))
        ),
    )


def _current(layout: ArchiveLayout, identity: RepositoryIdentity) -> tuple[Path, RevisionManifest]:
    repository = RepositoryLayout(archive=layout, identity=identity)
    _plain_path(layout, repository.current_ref)
    current = read_model(repository.current_ref, Reference, error=RetentionError, code="HFRET010")
    commit = CommitSha(current.commit_sha)
    publication = PublicationId(current.publication_id)
    retained_path = repository.revision_ref(commit)
    _plain_path(layout, retained_path)
    retained = read_model(retained_path, Reference, error=RetentionError, code="HFRET010")
    tree = repository.instance(commit, publication)
    manifest_path = repository.manifest(commit, publication)
    _plain_path(layout, tree, directory=True)
    _plain_path(layout, manifest_path)
    manifest = read_model(manifest_path, RevisionManifest, error=RetentionError, code="HFRET010")
    if (
        current != retained
        or current.identity != identity
        or current.tree != str(layout.published_relative(tree))
        or current.manifest != str(layout.published_relative(manifest_path))
        or manifest.identity != identity
        or manifest.commit_sha != current.commit_sha
        or manifest.publication_id != current.publication_id
        or manifest.publication_generation != current.publication_generation
        or manifest.tree != str(layout.archive_relative(tree))
        or not manifest.verification.completeness_checked
    ):
        _refuse(
            repository.current_ref, "current reference, retained reference and manifest disagree"
        )
    return tree, manifest


def _matching_file(
    layout: ArchiveLayout, path: Path, root: Path, tree: Path, expected: FileEntry
) -> QuarantineFile:
    retained = tree / expected.path
    _plain_path(layout, path)
    _plain_path(layout, retained)
    candidate_state, retained_state = _prove_pair(
        path, retained, size=expected.size, sha256=expected.sha256
    )
    return QuarantineFile(
        path=str(path.relative_to(root)),
        size=expected.size,
        sha256=expected.sha256,
        retained_path=str(layout.archive_relative(retained)),
        identity=ObjectIdentity(
            device=candidate_state[0], inode=candidate_state[1], size=candidate_state[2]
        ),
        candidate_state=candidate_state,
        retained_state=retained_state,
    )


def _plan(
    layout: ArchiveLayout,
    transaction_id: TransactionId,
    journals: Sequence[TransactionJournal],
) -> QuarantineCleanupPlan:
    root = layout.quarantine_for(transaction_id)
    identity, recovery_id = _ownership(layout, transaction_id, journals)
    _plain_path(layout, layout.quarantine, directory=True)
    absent = not root.exists() and not root.is_symlink()
    files, directories = ((), ()) if absent else _contents(layout, root)
    matches: list[QuarantineFile] = []
    if files:
        tree, manifest = _current(layout, identity)
        entries = {entry.path: entry for entry in manifest.files}
        for path in files:
            name = str(path.relative_to(root / "tree"))
            expected = entries.get(name)
            if expected is None:
                _refuse(path, "the file has no same-path entry in the current retained manifest")
            matches.append(_matching_file(layout, path, root, tree, expected))
    return QuarantineCleanupPlan(
        transaction_id=transaction_id,
        repository=identity.selector,
        quarantine_path=str(layout.archive_relative(root)),
        recovery_transaction_id=recovery_id,
        files=tuple(matches),
        directories=directories,
        already_absent=absent,
    )


def plan_quarantine_cleanups(
    layout: ArchiveLayout, transaction_ids: Sequence[TransactionId]
) -> tuple[QuarantineCleanupPlan, ...]:
    """Validate the complete explicit selection before any target is removed."""
    try:
        journals = _journals(layout)
        return tuple(
            _plan(layout, identifier, journals) for identifier in sorted(set(transaction_ids))
        )
    except (HfcacheError, OSError, ValueError) as exc:
        if isinstance(exc, RetentionError):
            raise
        _refuse(layout.quarantine, str(exc))


def plan_quarantine_cleanup(
    layout: ArchiveLayout, transaction_id: TransactionId
) -> QuarantineCleanupPlan:
    """Read and hash the evidence without creating files or taking a writer lock."""
    return plan_quarantine_cleanups(layout, (transaction_id,))[0]


def apply_quarantine_cleanup(layout: ArchiveLayout, plan: QuarantineCleanupPlan) -> dict[str, Any]:
    """Remove only freshly proven entries; caller holds the guarded writer lock.

    Direct unlinks name individual proven duplicates. Directories use rmdir, so
    an unrecognized or newly introduced entry can never be recursively removed.
    A crash may leave a subset, which the next explicit invocation revalidates.
    """
    fresh = plan_quarantine_cleanup(layout, plan.transaction_id)
    if fresh.to_dict() != plan.to_dict():
        _refuse(layout.quarantine_for(plan.transaction_id), "the reviewed target changed")
    root = layout.quarantine_for(plan.transaction_id)
    try:
        for entry in fresh.files:
            path = root / entry.path
            retained = layout.root / entry.retained_path
            # An earlier unlink can change ctime on an aliased retained inode.
            # Rehash both copies immediately before this unlink instead of
            # mistaking that legitimate hardlink change for lost ownership.
            _prove_pair(path, retained, size=entry.size, sha256=entry.sha256, remove=True)
        for relative in fresh.directories:
            path = root / relative
            _remove_directory(path)
    except OSError as exc:
        _refuse(root, f"cleanup stopped after partial progress: {exc}")
    result = fresh.to_dict() | {
        "removed_files": len(fresh.files),
        "removed_directories": len(fresh.directories),
        "removed_logical_bytes": fresh.logical_bytes,
    }
    emit(
        "quarantine.cleaned",
        transaction_id=fresh.transaction_id,
        recovery_transaction_id=fresh.recovery_transaction_id,
        repository=fresh.repository,
        quarantine_path=fresh.quarantine_path,
        removed_files=len(fresh.files),
        removed_directories=len(fresh.directories),
        removed_logical_bytes=fresh.logical_bytes,
        already_absent=fresh.already_absent,
    )
    return result
