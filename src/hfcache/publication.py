"""Building a publication tree, and the references a consumer reads.

A revision is published by building it somewhere private, proving it, and then
renaming it into place — so this module has two halves.

**Staging.** `.store/staging/<transaction-id>/` is one transaction's own area
(`FS-18`), on the same filesystem as its destination so the publication that
follows is a `rename(2)` and never a cross-device copy (`FS-04`). Two rules keep
it safe: a source is only ever used after it is proven to be a regular file
inside the operation's approved cache root (`FS-15`), and a repository-relative
path is only ever joined after the grammar has proven it cannot escape
(`docs/security.md` T-02). Staging is acted on only when it matches the
transaction naming contract, which is what keeps `FS-19` intact — nothing the
application did not create is ever removed.

**References.** `refs/current.json` names the revision consumers should take, and
`refs/revisions/<sha>.json` names which published instance of each retained SHA
is active (`FS-08`). They are small, versioned, replaced by atomic rename, and
never edited in place — which is what gives `FS-12` its guarantee that a consumer
reading a reference once either succeeds or sees a failure it can retry, and
never copies a mixture of two revisions.

Two rules are enforced here rather than left to callers.

`FS-10` — a reference is written only after both of its targets are durable. A
reference that names a tree or a manifest which is not there is worse than no
reference at all: `verify` reports it as corruption and a consumer copy fails
partway. So the targets are resolved and checked immediately before the write,
and a reference whose targets are missing is refused rather than published.

`FS-09` — a reference's `tree` and `manifest` are relative to `published/`,
not to the archive root, because a consumer mounts `published/` and joins them
onto that. Resolution therefore goes through `resolve_published`, and a field
that tries to escape is a coded refusal rather than a path outside the archive.
"""

import os
import shutil
import stat
from typing import TYPE_CHECKING, Final, Literal

from hfcache.errors import IntegrityError, Problem, SynchronizationError
from hfcache.hashing import sha256_file
from hfcache.identity import CommitSha
from hfcache.models import Reference
from hfcache.paths import resolve_within
from hfcache.storage import fsync_directory, read_model, temporary_sibling, write_model

if TYPE_CHECKING:
    from pathlib import Path

    from hfcache.hashing import FileDigest
    from hfcache.identity import TransactionId
    from hfcache.paths import ArchiveLayout, RepositoryLayout, StagingPaths

__all__ = [
    "PUBLISHED_DIRECTORY_MODE",
    "PUBLISHED_FILE_MODE",
    "STAGING_MODE",
    "create_staging",
    "discard_staging",
    "prepare_staged_parent",
    "projected_publication_bytes",
    "promote_staging",
    "publish_current_reference",
    "publish_revision_reference",
    "read_reference",
    "reference_target_problems",
    "source_problems",
    "stage_file",
    "staged_path",
]

PUBLISHED_FILE_MODE: Final = 0o640
"""`UMask=0027`: readable by the export identity, writable by nobody (§5.2).

Set explicitly rather than left to the umask, because `atomic_write_bytes`
applies the mode before the rename and a consumer-visible file must never be
reachable at its final name with a mode this application did not choose. Note
that published *content* files are never `chmod`ed — in hardlink mode a published
file and its cache blob are one inode (`AD-11`) — but a reference is written by
this application and owned by it, so its mode is ours to set.
"""

PUBLISHED_DIRECTORY_MODE: Final = 0o2750
"""Group-traversable and setgid, so the read identity keeps its group (§5.2)."""

STAGING_MODE: Final = 0o700
"""Staging lives under `.store`, which is private to the writer (§5.2).

This is the mode of the transaction's own container, which never becomes
consumer-visible. The `tree/` inside it is built at `PUBLISHED_DIRECTORY_MODE`
instead, because publication is a rename and a rename does not change a
directory's mode — whatever is built there is exactly what a consumer will see.
"""


# --------------------------------------------------------------------------- #
# Staging
# --------------------------------------------------------------------------- #


def create_staging(layout: ArchiveLayout, transaction_id: TransactionId) -> StagingPaths:
    """Make `.store/staging/<transaction-id>/tree`, empty and owned by this run.

    Exclusive by construction: the directory is created with `O_EXCL` semantics
    (`mkdir` without `exist_ok`), so a transaction id that somehow collided with
    an existing area fails here rather than building into someone else's tree.

    The tree itself is created at the *published* mode, because publication is a
    rename and a rename does not change a directory's mode — whatever is built
    here is exactly what a consumer will see (§5.2).
    """
    paths = layout.staging_for(transaction_id)
    try:
        paths.directory.mkdir(mode=STAGING_MODE)
        paths.directory.chmod(STAGING_MODE)
        paths.tree.mkdir(mode=PUBLISHED_DIRECTORY_MODE)
        paths.tree.chmod(PUBLISHED_DIRECTORY_MODE)
        fsync_directory(paths.directory)
    except OSError as exc:
        message = f"staging {paths.directory} could not be created: {exc.strerror}"
        raise SynchronizationError.single(
            message, code="HFSYN005", location=str(layout.archive_relative(paths.directory))
        ) from exc
    return paths


def discard_staging(layout: ArchiveLayout, transaction_id: TransactionId) -> bool:
    """Remove one transaction's staging area, wholesale. Returns whether it was there.

    The only deletion in this module, and it is inside `FS-19` because the path
    is *derived* from a validated transaction id rather than taken from the
    filesystem: `ArchiveLayout.staging_for` re-checks the id against the 32-hex
    grammar before it becomes a path component, so this can only ever name a
    directory matching the naming contract (`FS-18`).
    """
    paths = layout.staging_for(transaction_id)
    if not paths.directory.is_dir():
        return False
    shutil.rmtree(paths.directory)
    fsync_directory(layout.staging)
    return True


def source_problems(source: Path, *, cache_root: Path) -> list[Problem]:
    """Prove one publication source is safe to link or copy from (`FS-15`).

    Symlinks are *resolved*, not rejected. The `huggingface_hub` cache reaches
    every file through a symlink into `blobs/` by design, so refusing them would
    refuse every normal ingestion; what must be rejected is a link that leaves
    the approved root, dangles, or lands on something that is not a regular file
    (plan §14.1 item 6, §14.3). Containment is checked on the *resolved* path,
    since that is the one that will actually be read.
    """
    where = str(source)
    try:
        resolved = source.resolve(strict=True)
    except OSError as exc:
        message = (
            f"publication source {source} could not be resolved ({exc.strerror}); a dangling "
            f"link is never followed and never published"
        )
        return [Problem(code="HFSYN004", message=message, location=where)]

    problems: list[Problem] = []
    root = cache_root.resolve()
    if not resolved.is_relative_to(root):
        message = (
            f"publication source {source} resolves to {resolved}, which is outside the "
            f"approved cache root {root}; every source must be contained by it (`FS-15`)"
        )
        problems.append(Problem(code="HFSYN004", message=message, location=where))
    if not stat.S_ISREG(resolved.lstat().st_mode):
        message = (
            f"publication source {source} resolves to {resolved}, which is not a regular file; "
            f"devices, sockets, and FIFOs are never published"
        )
        problems.append(Problem(code="HFSYN004", message=message, location=where))
    return problems


def staged_path(staging: StagingPaths, relative: object) -> Path:
    """Where one repository-relative path lands inside the staging tree.

    The path comes from upstream repository metadata, so it goes through the
    published grammar before it is joined: no absolute path, no `..`, no
    backslash, no component a consumer platform would resolve differently
    (`docs/security.md` T-02, `FS-15`). Containment is established by the
    grammar rather than re-derived after the join.
    """
    return resolve_within(staging.tree, relative, code="HFSYN004")


def prepare_staged_parent(path: Path) -> None:
    """Create the destination's parent directories in staging (plan §14.1 step 3)."""
    try:
        path.parent.mkdir(mode=PUBLISHED_DIRECTORY_MODE, parents=True, exist_ok=True)
    except OSError as exc:
        message = f"the staging directory {path.parent} could not be created: {exc.strerror}"
        raise SynchronizationError.single(
            message, code="HFSYN005", location=str(path.parent)
        ) from exc


def projected_publication_bytes(
    logical_bytes: int, *, publication_mode: Literal["hardlink", "copy"]
) -> int:
    """What publishing a revision of this size will itself consume.

    The whole reason `publication_mode` is an explicit configuration choice
    rather than an automatic fallback (`AD-11`): hardlink publication adds
    directory entries pointing at cache blobs that are already on the dataset, so
    it costs nothing beyond metadata, while copy publication writes a second
    physical copy of every byte. Plan §19 item 9 requires the second number to be
    in the free-space calculation before a download starts, and `plan` reports it
    because that is the figure the dataset quota is sized from.

    Stated once, here, so the estimate an operator reads and the reserve a sync
    enforces cannot disagree about what a publication costs.
    """
    return logical_bytes if publication_mode == "copy" else 0


def stage_file(
    source: Path,
    destination: Path,
    *,
    publication_mode: Literal["hardlink", "copy"],
    cache_root: Path,
) -> FileDigest:
    """Put one repository file into staging, and say what landed there.

    The source is proven contained and regular first (`FS-15`), then either
    linked or copied according to configuration. The mode is never chosen
    automatically: if hardlinks turn out to be unavailable while `"hardlink"` is
    configured, the run fails rather than quietly consuming twice the planned
    space (`AD-11`), and `doctor` check 9 is what establishes that before a
    download begins.

    The returned digest is of the bytes now in staging, not of the source, so a
    caller writing a manifest is describing what it actually published.
    """
    if problems := source_problems(source, cache_root=cache_root):
        raise SynchronizationError(problems)
    prepare_staged_parent(destination)
    if publication_mode == "hardlink":
        return _link(source, destination)
    return _copy(source, destination)


def _link(source: Path, destination: Path) -> FileDigest:
    """Hardlink a cache blob into staging (plan §14.1 step 4).

    The destination is never `chmod`ed: it is the same inode as the cache blob,
    so changing one mode changes both (`AD-11`). Read-only access for consumers
    is enforced by the export and by directory permissions, not by file mode.
    """
    try:
        os.link(source, destination)
    except OSError as exc:
        message = (
            f"{source} could not be hardlinked into staging at {destination}: {exc.strerror}. "
            f"`publication_mode` is never downgraded to copy automatically (`AD-11`)"
        )
        raise SynchronizationError.single(
            message, code="HFSYN005", location=str(destination)
        ) from exc
    return sha256_file(destination, code="HFSYN005")


def _copy(source: Path, destination: Path) -> FileDigest:
    """Copy a resolved regular file into staging, then prove the copy (plan §14.3).

    Temporary sibling and atomic rename per file, so a crash leaves either the
    complete file or nothing. The copy is hashed *and* compared against a fresh
    hash of the source, because copy mode exists for the deployment where
    hardlinks are unavailable — often a different storage topology — and a copy
    that silently lost bytes would be published as though it were the revision.
    """
    expected = sha256_file(source, code="HFSYN005")
    temporary = temporary_sibling(destination)
    try:
        # `copyfile` follows the source and writes a plain regular file, so a
        # cache symlink is resolved rather than reproduced (plan §14.3).
        shutil.copyfile(source, temporary)
        with temporary.open("rb") as handle:
            os.fsync(handle.fileno())
        temporary.replace(destination)
    except OSError as exc:
        temporary.unlink(missing_ok=True)
        message = f"{source} could not be copied into staging at {destination}: {exc.strerror}"
        raise SynchronizationError.single(
            message, code="HFSYN005", location=str(destination)
        ) from exc
    fsync_directory(destination.parent)

    landed = sha256_file(destination, code="HFSYN005")
    if landed != expected:
        message = (
            f"the copy of {source} at {destination} is {landed.size} bytes with digest "
            f"{landed.digest}, but the source is {expected.size} bytes with digest "
            f"{expected.digest}; a copy that lost bytes is never published"
        )
        raise SynchronizationError.single(message, code="HFSYN005", location=str(destination))
    return landed


def promote_staging(layout: ArchiveLayout, staging: StagingPaths, destination: Path) -> None:
    """Rename a finished staged tree into place — the moment a revision exists.

    Plan §13.2 step 15, and the single operation that makes a publication
    visible. One `rename(2)` within one filesystem (`FS-04`), so a consumer
    either sees the complete revision or does not see it at all (`FS-12`); the
    tree is fsynced first, so what becomes visible is also durable.

    An existing destination is refused explicitly rather than left to `rename`.
    `rename(2)` fails on a *non-empty* directory but happily replaces an empty
    one, so the syscall alone would enforce `FS-05` for most publications and
    silently break it for an instance directory a crash left empty. The mutating
    lock is what makes the check-then-rename safe (`AD-17`).
    """
    if destination.exists():
        message = (
            f"{destination} already exists; a publication instance is immutable once it has "
            f"been renamed into place and is never replaced (`FS-05`)"
        )
        raise SynchronizationError.single(
            message, code="HFSYN006", location=str(layout.archive_relative(destination))
        )
    try:
        fsync_directory(staging.tree)
        destination.parent.mkdir(mode=PUBLISHED_DIRECTORY_MODE, parents=True, exist_ok=True)
        staging.tree.rename(destination)
        fsync_directory(destination.parent)
    except OSError as exc:
        message = (
            f"publishing {staging.tree} to {destination} failed: {exc.strerror}; the previous "
            f"reference is unchanged and no revision was published"
        )
        raise SynchronizationError.single(
            message, code="HFSYN006", location=str(layout.archive_relative(destination))
        ) from exc


# --------------------------------------------------------------------------- #
# References
# --------------------------------------------------------------------------- #


def reference_target_problems(layout: ArchiveLayout, reference: Reference) -> list[Problem]:
    """Prove both of a reference's targets exist before it names them (`FS-10`).

    Checked immediately before the write rather than by the caller, because
    "the reference is written last" is the invariant, and an invariant enforced
    at the point of the write is one a future caller cannot forget.
    """
    problems: list[Problem] = []
    for field, value in (("tree", reference.tree), ("manifest", reference.manifest)):
        try:
            target = layout.resolve_published(str(value), code="HFSYN007")
        except ValueError as exc:
            problems.append(Problem(code="HFSYN007", message=str(exc), location=f"{field}={value}"))
            continue
        if field == "tree" and not target.is_dir():
            message = (
                f"reference {field} {value} does not name a publication instance directory; "
                f"a reference is written only after its targets are durable (`FS-10`)"
            )
            problems.append(Problem(code="HFSYN007", message=message, location=str(target)))
        elif field == "manifest" and not target.is_file():
            message = (
                f"reference {field} {value} does not name a manifest file; a reference is "
                f"written only after its targets are durable (`FS-10`)"
            )
            problems.append(Problem(code="HFSYN007", message=message, location=str(target)))
    return problems


def publish_revision_reference(layout: ArchiveLayout, reference: Reference) -> Path:
    """Write `refs/revisions/<sha>.json` for the instance this reference names.

    One exists for exactly the set of SHAs a repository retains (`FS-11`), so
    this is what makes a newly published revision retained, and `prune` removing
    it is what makes one no longer retained.
    """
    repository = layout.repository(reference.identity)
    # A validated `CommitShaField` already satisfies the grammar; the `NewType`
    # call is how that is stated to the type system, and `paths` re-checks it
    # anyway before it becomes a path component.
    path = repository.revision_ref(CommitSha(reference.commit_sha))
    _publish(layout, repository, reference, path)
    return path


def publish_current_reference(layout: ArchiveLayout, reference: Reference) -> Path:
    """Replace `refs/current.json` — the one file a consumer must read (`FS-08`).

    Written after the per-SHA reference, never before: `current.json` always
    names a SHA that also has a `refs/revisions/<sha>.json`, and both must agree
    on `publication_id` (`docs/schemas.md` §4.2).
    """
    repository = layout.repository(reference.identity)
    path = repository.current_ref
    _publish(layout, repository, reference, path)
    return path


def _publish(
    layout: ArchiveLayout,
    repository: RepositoryLayout,
    reference: Reference,
    path: Path,
) -> None:
    """Refuse unless both targets are durable, then replace the reference."""
    if problems := reference_target_problems(layout, reference):
        raise SynchronizationError(problems)
    try:
        path.parent.mkdir(mode=PUBLISHED_DIRECTORY_MODE, parents=True, exist_ok=True)
    except OSError as exc:
        message = f"the reference directory {path.parent} could not be created: {exc.strerror}"
        raise SynchronizationError.single(
            message, code="HFSYN007", location=str(path.parent)
        ) from exc
    write_model(path, reference, mode=PUBLISHED_FILE_MODE, code="HFSYN007")
    # The rename made the reference visible and fsynced its own directory; this
    # makes the `refs/revisions/` directory entry durable too when the write
    # created it, so a crash cannot leave a reference the parent does not list.
    fsync_directory(repository.refs)


def read_reference(layout: ArchiveLayout, path: Path) -> Reference:
    """Read a reference back, as `verify`, `status`, and `repair` all do.

    `HFVER008` rather than `HFSYN007`: reading a reference happens when something
    is being checked, and a reference that will not load is an integrity finding
    about the archive, not a failure of the run that is reading it.
    """
    return read_model(
        path,
        Reference,
        error=IntegrityError,
        code="HFVER008",
        location=str(layout.archive_relative(path)),
    )
