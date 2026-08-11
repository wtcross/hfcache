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
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Final, Literal, Self, final

from hfcache.errors import IntegrityError, Problem, SynchronizationError
from hfcache.hashing import FileDigest, ObjectIdentity, sha256_file
from hfcache.identity import TYPE_DIRECTORIES, CommitSha, PublicationId, RepositoryIdentity
from hfcache.manifests import RevisionManifest
from hfcache.models import Reference
from hfcache.paths import RepositoryLayout, resolve_within
from hfcache.reporting import (
    CatalogRevision,
    CurrentRevision,
    RepositoriesCatalog,
    RepositoryCatalogEntry,
    VerificationCatalog,
)
from hfcache.storage import fsync_directory, read_model, temporary_sibling, write_model

if TYPE_CHECKING:
    from collections.abc import Mapping
    from datetime import datetime
    from pathlib import Path

    from hfcache.config import RepositoryConfig
    from hfcache.identity import TransactionId
    from hfcache.paths import ArchiveLayout, StagingPaths

__all__ = [
    "PUBLISHED_DIRECTORY_MODE",
    "PUBLISHED_FILE_MODE",
    "STAGING_MODE",
    "VerificationStates",
    "create_staging",
    "discard_staging",
    "next_generation",
    "prepare_staged_parent",
    "projected_publication_bytes",
    "promote_staging",
    "publish_catalog",
    "publish_current_reference",
    "publish_revision_reference",
    "publish_verification_catalog",
    "published_repositories",
    "read_reference",
    "read_verification_catalog",
    "rebuild_catalog",
    "reference_target_problems",
    "retained_references",
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


def stage_file(  # noqa: PLR0913 - source, destination, and their verification evidence
    source: Path,
    destination: Path,
    *,
    publication_mode: Literal["hardlink", "copy"],
    cache_root: Path,
    expected: FileDigest,
    expected_identity: ObjectIdentity,
) -> FileDigest:
    """Put one repository file into staging, and say what landed there.

    The source is proven contained and regular first (`FS-15`), then either
    linked or copied according to configuration. The mode is never chosen
    automatically: if hardlinks turn out to be unavailable while `"hardlink"` is
    configured, the run fails rather than quietly consuming twice the planned
    space (`AD-11`), and `doctor` check 9 is what establishes that before a
    download begins.

    ``expected`` and ``expected_identity`` are transient evidence from the
    ingestion hash. Hardlink mode proves the landed path is that exact object
    and carries the digest forward without another read. Copy mode hashes the
    distinct landed object and compares it with the same evidence.
    """
    if problems := source_problems(source, cache_root=cache_root):
        raise SynchronizationError(problems)
    try:
        observed = ObjectIdentity.of(source)
    except OSError as exc:
        message = f"publication source {source} could not be examined: {exc.strerror}"
        raise SynchronizationError.single(message, code="HFSYN005", location=str(source)) from exc
    if observed != expected_identity or expected.size != expected_identity.size:
        message = (
            f"publication source {source} no longer matches the object hashed for this "
            "operation; a replacement or size change is never staged"
        )
        raise SynchronizationError.single(message, code="HFSYN005", location=str(source))
    prepare_staged_parent(destination)
    if publication_mode == "hardlink":
        return _link(
            source,
            destination,
            expected=expected,
            expected_identity=expected_identity,
        )
    return _copy(source, destination, expected=expected)


def _link(
    source: Path,
    destination: Path,
    *,
    expected: FileDigest,
    expected_identity: ObjectIdentity,
) -> FileDigest:
    """Hardlink a cache blob into staging (plan §14.1 step 4).

    The destination is never `chmod`ed: it is the same inode as the cache blob,
    so changing one mode changes both (`AD-11`). Read-only access for consumers
    is enforced by the export and by directory permissions, not by file mode.
    """
    try:
        os.link(source, destination, follow_symlinks=True)
    except OSError as exc:
        message = (
            f"{source} could not be hardlinked into staging at {destination}: {exc.strerror}. "
            f"`publication_mode` is never downgraded to copy automatically (`AD-11`)"
        )
        raise SynchronizationError.single(
            message, code="HFSYN005", location=str(destination)
        ) from exc
    try:
        source_identity = ObjectIdentity.of(source)
        landed_identity = ObjectIdentity.of(destination)
    except OSError as exc:
        cleanup = _remove_unproven_link(destination)
        message = (
            f"the hardlink at {destination} could not be proven after creation: "
            f"{exc.strerror}{cleanup}"
        )
        raise SynchronizationError.single(
            message, code="HFSYN005", location=str(destination)
        ) from exc
    if source_identity != expected_identity or landed_identity != expected_identity:
        cleanup = _remove_unproven_link(destination)
        message = (
            f"the hardlink at {destination} is not the exact device, inode, and size "
            f"hashed for this operation; the unproven link was refused{cleanup}"
        )
        raise SynchronizationError.single(message, code="HFSYN005", location=str(destination))
    return expected


def _copy(source: Path, destination: Path, *, expected: FileDigest) -> FileDigest:
    """Copy a resolved regular file into staging, then prove the copy (plan §14.3).

    Temporary sibling and atomic rename per file, so a crash leaves either the
    complete file or nothing. The copy is hashed *and* compared against a fresh
    hash of the source, because copy mode exists for the deployment where
    hardlinks are unavailable — often a different storage topology — and a copy
    that silently lost bytes would be published as though it were the revision.
    The comparison is against the ingestion digest, not a fresh source read, so
    a source replacement after verification cannot become the new expectation.
    """
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

    landed = sha256_file(destination, error=SynchronizationError, code="HFSYN005")
    if landed != expected:
        cleanup = _remove_unproven_link(destination)
        message = (
            f"the copy of {source} at {destination} is {landed.size} bytes with digest "
            f"{landed.digest}, but ingestion read {expected.size} bytes with digest "
            f"{expected.digest}; a copy that lost or replaced bytes is never published"
            f"{cleanup}"
        )
        raise SynchronizationError.single(message, code="HFSYN005", location=str(destination))
    return landed


def _remove_unproven_link(destination: Path) -> str:
    """Remove a staging entry this call created, reporting cleanup failure inline."""
    try:
        destination.unlink()
        fsync_directory(destination.parent)
    except OSError as exc:
        return f"; cleanup could not remove it: {exc.strerror}"
    return ""


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
    write_model(
        path, reference, mode=PUBLISHED_FILE_MODE, code="HFSYN007", error=SynchronizationError
    )
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


# --------------------------------------------------------------------------- #
# The derived catalog (`FS-16`, plan §13.2 step 19)
# --------------------------------------------------------------------------- #


def published_repositories(layout: ArchiveLayout) -> tuple[RepositoryIdentity, ...]:
    """Every repository the archive holds published content for.

    Read off `published/repos/<type>/<org>/<repo>` rather than off configuration,
    because those are different sets and the difference is deliberate: removing a
    repository from configuration never deletes its archive (`AD-06`), so it must
    keep appearing in the catalog as unmanaged.

    A directory whose name is not a valid identifier is skipped rather than
    reported. Nothing about it can be interpreted — there is no repository to
    attribute a problem to — and `recovery.reconcile_storage` is what reports
    unknown entries in application-owned areas (`FS-19`).
    """
    found: list[RepositoryIdentity] = []
    for repository_type, directory in TYPE_DIRECTORIES.items():
        root = layout.repos / directory
        for namespace in _subdirectories(root):
            for name in _subdirectories(namespace):
                try:
                    found.append(
                        RepositoryIdentity.of(repository_type, f"{namespace.name}/{name.name}")
                    )
                except ValueError:
                    continue
    return tuple(sorted(found, key=lambda identity: identity.sort_key))


def _subdirectories(path: Path) -> list[Path]:
    """Immediate subdirectories, or nothing when the parent is absent."""
    try:
        return sorted(entry for entry in path.iterdir() if entry.is_dir())
    except OSError:
        return []


def retained_references(
    layout: ArchiveLayout, identity: RepositoryIdentity
) -> tuple[Reference, ...]:
    """Every per-SHA instance reference one repository holds (`FS-11`).

    `refs/revisions/<sha>.json` is what makes a SHA retained, so this is the
    authoritative retained set — not the revision directories, which can hold a
    superseded repair instance inside its grace period, and not the catalog,
    which is derived from exactly this.

    Ordered by `publication_generation`, which is the immutable retention
    ordering (`AD-05`): wall-clock time and upstream commit time both reorder
    under repair and republication, and the generation does not.
    """
    references = [
        read_reference(layout, path)
        for path in sorted(
            (RepositoryLayout(archive=layout, identity=identity).refs / "revisions").glob("*.json")
        )
    ]
    return tuple(sorted(references, key=lambda reference: reference.publication_generation))


def next_generation(layout: ArchiveLayout, identity: RepositoryIdentity) -> int:
    """The generation a newly published unique SHA receives (plan §13.2 step 11).

    `max(existing) + 1`, never `count + 1`. A prune removes the oldest revision
    and its reference, so counting would reissue a generation that a pruned
    revision already held and break the ordering that retention depends on.
    Gaps after a crash are explicitly acceptable (§15.1); collisions are not.
    """
    references = retained_references(layout, identity)
    return max((reference.publication_generation for reference in references), default=0) + 1


def rebuild_catalog(
    layout: ArchiveLayout,
    *,
    configured: Mapping[str, RepositoryConfig] = MappingProxyType({}),
    generated_at: datetime,
) -> RepositoriesCatalog:
    """Derive the whole catalog from immutable manifests and references (`FS-16`).

    Rebuilt rather than edited, every time. The catalog exists so `status` and
    `list` answer without walking the archive, and the cost of that convenience
    is that it can be stale or wrong; the cost is only acceptable because it is
    never authority. Where it disagrees with a manifest or a reference, they win,
    and this function is how it is brought back into agreement.

    `configured` is keyed by selector so a repository present in one set and not
    the other is described correctly: configured-and-published is `managed` with
    its `enabled` flag, published-but-not-configured is `managed = false` with
    `enabled = null`, and configured-but-never-published simply has no entry yet.
    """
    states = VerificationStates.of(layout)
    entries = [
        _catalog_entry(layout, identity, configured.get(identity.selector), states)
        for identity in published_repositories(layout)
    ]
    return RepositoriesCatalog(
        generated_at=generated_at,
        repositories=tuple(sorted(entries, key=lambda e: (e.repository_type, e.repository_id))),
    )


def _catalog_entry(
    layout: ArchiveLayout,
    identity: RepositoryIdentity,
    configured: RepositoryConfig | None,
    states: VerificationStates,
) -> RepositoryCatalogEntry:
    """One repository's retained state, read from its references and manifests."""
    repository = RepositoryLayout(archive=layout, identity=identity)
    revisions: list[CatalogRevision] = []
    for reference in retained_references(layout, identity):
        manifest = read_model(
            repository.manifest(
                CommitSha(reference.commit_sha), PublicationId(reference.publication_id)
            ),
            RevisionManifest,
            error=IntegrityError,
            code="HFVER007",
        )
        revisions.append(
            CatalogRevision(
                commit_sha=manifest.commit_sha,
                file_count=manifest.file_count,
                publication_generation=manifest.publication_generation,
                publication_id=manifest.publication_id,
                published_at=manifest.published_at,
                total_bytes=manifest.total_bytes,
                verification_state=states.state_of(
                    identity, manifest.commit_sha, manifest.publication_id
                ),
            )
        )
    current = _current(layout, repository)
    published = [revision.published_at for revision in revisions]
    return RepositoryCatalogEntry(
        current=current,
        enabled=configured.enabled if configured else None,
        first_published_at=min(published) if published else None,
        last_published_at=max(published) if published else None,
        managed=configured is not None,
        repository_id=identity.id,
        repository_type=identity.type,
        requested_revision=configured.revision if configured else None,
        revisions=tuple(revisions),
    )


def _current(layout: ArchiveLayout, repository: RepositoryLayout) -> CurrentRevision | None:
    """Which revision consumers are pointed at, or `None` before the first one."""
    if not repository.current_ref.exists():
        return None
    reference = read_reference(layout, repository.current_ref)
    return CurrentRevision(
        commit_sha=reference.commit_sha,
        publication_generation=reference.publication_generation,
        publication_id=reference.publication_id,
    )


def read_verification_catalog(layout: ArchiveLayout) -> VerificationCatalog | None:
    """`published/catalog/verification.json`, or `None` when there is nothing to read.

    `None` covers both an absent catalog and one that will not load, and that is
    deliberate rather than lazy. The catalog is derived (`FS-16`): it is rebuilt
    wholesale by the next `verify --full`, and every caller uses it to *raise*
    confidence — to say a revision was verified, or to predict how long the next
    verification will take. Treating an unreadable one as "nothing has been
    verified" understates confidence, which is the direction a damaged archive
    should err in; raising instead would let a corrupt derived file fail the
    publication transaction that rebuilds the other catalog beside it.

    What it must never do is silently hide corruption, and it does not: a
    catalog that will not load leaves every revision reading `unverified`, which
    is exactly the signal an operator acts on.
    """
    try:
        return read_model(
            layout.verification_catalog,
            VerificationCatalog,
            error=IntegrityError,
            code="HFVER007",
            location=str(layout.archive_relative(layout.verification_catalog)),
        )
    except IntegrityError:
        return None


@final
@dataclass(frozen=True, slots=True)
class VerificationStates:
    """What `catalog/verification.json` says about each retained revision.

    The one source of truth behind every `verification_state` this application
    reports — the derived catalog, `status`, and `list` all read it through here,
    so the three cannot disagree (decision 51).

    A revision with no entry is `unverified`. Ingestion hashing does not make a
    revision `verified`: it read the bytes in the Hub cache *before* the
    published tree existed, and `verify` is what reads the tree. Reporting
    `verified` for a revision nothing has ever re-read would make the field
    unfalsifiable — which is exactly why `failed` was previously unreachable.
    """

    outcomes: Mapping[tuple[str, str, str, str], str]

    @classmethod
    def of(cls, layout: ArchiveLayout) -> Self:
        """Read the verification catalog once, for a command about to use it."""
        catalog = read_verification_catalog(layout)
        if catalog is None:
            return cls(outcomes={})
        return cls(
            outcomes={
                (
                    entry.repository_type,
                    entry.repository_id,
                    revision.commit_sha,
                    revision.publication_id,
                ): revision.outcome
                for entry in catalog.repositories
                for revision in entry.revisions
                # An entry naming no instance contributes nothing, so every
                # revision reads `unverified` against it. `publication_id` is
                # optional in the schema because a *finding* may not be able to
                # name an instance (decision 49); a catalog entry that cannot
                # either is one whose verification cannot be attributed to
                # anything on disk, and the conservative answer to "was this
                # instance re-read?" is no.
                if revision.publication_id is not None
            }
        )

    def state_of(
        self, identity: RepositoryIdentity, commit_sha: str, publication_id: str
    ) -> Literal["verified", "unverified", "failed"]:
        """This *instance's* verification state, keyed the way the catalog records it.

        The publication id is part of the key, not decoration (decision 62). A
        verification re-reads the bytes of one published instance, and two
        instances of the same SHA are different bytes in different places: a
        repair replaces one, and a prune followed by a later republication of the
        same SHA produces another. Keyed by SHA alone, a freshly published
        instance inherits the verification of one that no longer exists — which
        is `verified` for content nothing has ever re-read, exactly the
        unfalsifiable field decision 51 existed to close.
        """
        outcome = self.outcomes.get((identity.type, identity.id, commit_sha, publication_id))
        if outcome == "clean":
            return "verified"
        if outcome == "failed":
            return "failed"
        return "unverified"


def publish_verification_catalog(layout: ArchiveLayout, catalog: VerificationCatalog) -> Path:
    """Replace `published/catalog/verification.json` atomically.

    The archive's health headline (`docs/schemas.md` §5.2), written by `verify`
    and read by `status`, `list`, and the estimator. Atomic for the same reason
    the repositories catalog is: a consumer or a `status` run reading a
    half-written file would see an archive that never existed.
    """
    path = layout.verification_catalog
    path.parent.mkdir(mode=PUBLISHED_DIRECTORY_MODE, parents=True, exist_ok=True)
    write_model(
        path, catalog, mode=PUBLISHED_FILE_MODE, code="HFSYN007", error=SynchronizationError
    )
    fsync_directory(path.parent)
    return path


def publish_catalog(layout: ArchiveLayout, catalog: RepositoriesCatalog) -> Path:
    """Replace `published/catalog/repositories.json` atomically.

    Derived state, so a failure to write it is not a failure of the publication
    that preceded it — but it is still an atomic replacement, because a consumer
    or a `status` run reading a half-written catalog would see an archive that
    never existed.
    """
    path = layout.repositories_catalog
    path.parent.mkdir(mode=PUBLISHED_DIRECTORY_MODE, parents=True, exist_ok=True)
    write_model(
        path, catalog, mode=PUBLISHED_FILE_MODE, code="HFSYN007", error=SynchronizationError
    )
    fsync_directory(path.parent)
    return path
