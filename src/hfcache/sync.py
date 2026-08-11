"""The per-repository ingestion sequence of plan §13.2.

This module holds the steps between "the bytes are in the cache" and "the
revision is published": proving what landed is what was promised, hashing it,
and describing it. The Hub is reached only through `hfcache.hub`, and the
archive only through `hfcache.publication` and `hfcache.storage`, so the
sequence itself stays testable without either.

The rule that shapes the whole module: **upstream metadata is a claim, and local
bytes are the evidence.** The Hub's tree listing says what a revision should
contain and how large each file should be, and that is what makes it useful for
deciding whether a download is complete. It never becomes what the archive
records as true — a manifest's sizes and digests come from reading the bytes
that actually landed (`AD-18`). The two are compared here precisely so that a
disagreement stops the revision rather than being published as fact.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from types import MappingProxyType
from typing import TYPE_CHECKING, Final, Literal, final

from hfcache.dependencies import detect_dependencies, undeclared, undeclared_warnings
from hfcache.errors import (
    ExitCode,
    HfcacheError,
    IntegrityError,
    Problem,
    SynchronizationError,
)
from hfcache.hashing import FileDigest, ObjectIdentity, sha256_file, sha256_identified_file
from hfcache.identity import (
    CommitSha,
    PublicationId,
    RepositoryIdentity,
    TransactionId,
    new_publication_id,
    new_transaction_id,
)
from hfcache.logging import emit
from hfcache.manifests import (
    FileEntry,
    FileProvenance,
    HashReuse,
    RevisionManifest,
    UpstreamIdentifiers,
    VerificationSummary,
)
from hfcache.models import Reference
from hfcache.paths import RepositoryLayout, find_path_collisions, parse_repository_relative
from hfcache.preflight import require_capacity
from hfcache.publication import (
    PUBLISHED_DIRECTORY_MODE,
    PUBLISHED_FILE_MODE,
    create_staging,
    discard_staging,
    next_generation,
    projected_publication_bytes,
    promote_staging,
    publish_catalog,
    publish_current_reference,
    publish_revision_reference,
    read_reference,
    rebuild_catalog,
    retained_references,
    source_problems,
    stage_file,
    staged_path,
)
from hfcache.reporting import (
    PrunedRevision,
    RepositoryRunResult,
    RunReport,
    RuntimeVersions,
    RunTotals,
)
from hfcache.retention import apply_prune, plan_prune
from hfcache.storage import fsync_directory, read_model, write_model
from hfcache.taxonomy import aggregate_exit_code
from hfcache.transactions import Transaction, open_transaction

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path
    from typing import Any

    from hfcache.config import ApplicationConfig, RepositoryConfig
    from hfcache.hub import DownloadEstimate, HubClient, RepositoryFacts, TreeEntry
    from hfcache.identity import RunId
    from hfcache.manifests import DependencyObservation, RepairProvenance
    from hfcache.paths import ArchiveLayout, StagingPaths

__all__ = [
    "HashedFile",
    "HashedSnapshot",
    "KnownDigest",
    "ObjectIdentity",
    "PublicationOutcome",
    "Timeline",
    "build_manifest",
    "completeness_problems",
    "hash_snapshot",
    "publish_revision",
    "published_digests",
    "snapshot_paths",
]


def snapshot_paths(snapshot: Path) -> tuple[str, ...]:
    """Every regular-file path a snapshot directory holds, repository-relative.

    Directories are walked and never reported: what a repository contains is
    files, and the containers are reconstructed by the path grammar.

    `follow_symlinks=False` is load-bearing. The Hub cache reaches every blob
    through a symlink, so a link is an entry in the snapshot whatever it points
    at — including nowhere. Following it would classify a dangling link as
    absent and a link to a directory as a container, and in both cases the entry
    would vanish from this listing while still sitting in the tree that
    publication is about to walk. What each link resolves to is
    `source_problems`' question, asked once, in one place.
    """
    return tuple(
        sorted(
            path.relative_to(snapshot).as_posix()
            for path in snapshot.rglob("*")
            if not path.is_dir(follow_symlinks=False)
        )
    )


def completeness_problems(
    snapshot: Path,
    tree: Sequence[TreeEntry],
    *,
    identity: RepositoryIdentity,
    cache_root: Path,
) -> list[Problem]:
    """Prove the downloaded snapshot is exactly the revision (plan §13.2 steps 6-8).

    Four questions, three codes, and every one of them answered for the whole
    snapshot before returning — an operator fixing an incomplete download should
    see every missing file at once, not the first one.

    * **Is anything missing or extra?** `HFSYN002`. Missing means the download
      did not deliver what the Hub listed. Extra is reported just as firmly:
      the archive publishes the exact path set upstream declared, and a file
      nobody listed is either a stale artifact of an earlier revision or
      something this application does not understand. Publishing it would put
      content in an immutable revision that its own manifest cannot explain.

    * **Does every size agree?** `HFSYN003`. The Hub's size is a claim, so a
      mismatch does not say which side is wrong — it says they disagree, which
      is enough to stop a publication. `HUB-007` hashes the bytes afterwards and
      the manifest records what was read (`AD-18`); this check exists so a
      truncated file is caught before anything expensive happens to it.

    * **Is every source safe to publish from?** `HFSYN004`, delegated to
      `source_problems`, which is the same proof publication itself performs
      (`FS-15`). Running it here means a snapshot containing a symlink out of
      the cache root fails the completeness step rather than surviving to the
      staging loop.

    * **Would two paths collide on disk?** `HFSYN002`. A case or
      Unicode-normalization collision publishes a tree in which two manifest
      entries resolve to one file, which is silent corruption of the thing being
      archived (`docs/security.md` T-02, decision 15).

    The path *grammar* is checked here too, so a name that could escape is
    refused before it is joined onto anything.
    """
    where = identity.selector
    expected = {entry.path: entry.size for entry in tree}
    problems = [
        *_grammar_problems(expected, where=where),
        *_path_set_problems(expected, snapshot_paths(snapshot), where=where),
    ]
    problems.extend(_collision_problems(expected, where=where))
    problems.extend(_content_problems(snapshot, expected, where=where, cache_root=cache_root))
    return problems


def _grammar_problems(expected: dict[str, int], *, where: str) -> list[Problem]:
    """Refuse an upstream name this application will not join onto a path."""
    problems: list[Problem] = []
    for path in sorted(expected):
        try:
            parse_repository_relative(path, code="HFSYN004")
        except ValueError as exc:
            problems.append(Problem(code="HFSYN004", message=str(exc), repository=where))
    return problems


def _path_set_problems(
    expected: dict[str, int], landed: Sequence[str], *, where: str
) -> list[Problem]:
    """Compare what the Hub listed with what the download produced."""
    problems: list[Problem] = []
    present = set(landed)
    for path in sorted(set(expected) - present):
        message = (
            f"{path} is listed in the Hub tree for {where} but is not in the downloaded "
            f"snapshot; a revision is archived complete or not at all"
        )
        problems.append(Problem(code="HFSYN002", message=message, location=path, repository=where))
    for path in sorted(present - set(expected)):
        message = (
            f"{path} is in the downloaded snapshot for {where} but is not listed in the Hub "
            f"tree; the archive publishes the exact path set upstream declared, and content "
            f"the manifest cannot explain is never published"
        )
        problems.append(Problem(code="HFSYN002", message=message, location=path, repository=where))
    return problems


def _collision_problems(expected: dict[str, int], *, where: str) -> list[Problem]:
    """Refuse two upstream names that would resolve to one published file."""
    problems: list[Problem] = []
    for key, spellings in find_path_collisions(expected):
        message = (
            f"{where} lists {', '.join(spellings)}, which fold to the same on-disk name "
            f"({key}); a consumer copying the tree onto a case-insensitive or normalizing "
            f"filesystem would silently merge them (`docs/security.md` T-02)"
        )
        problems.append(
            Problem(code="HFSYN002", message=message, location=spellings[0], repository=where)
        )
    return problems


def _content_problems(
    snapshot: Path, expected: dict[str, int], *, where: str, cache_root: Path
) -> list[Problem]:
    """Prove each landed file is safe to read and the size the Hub claimed."""
    problems: list[Problem] = []
    for path in sorted(expected):
        source = snapshot / path
        if not source.exists(follow_symlinks=False):
            # Already reported as missing; saying so twice would make one
            # incomplete download look like two problems.
            #
            # Not `exists()`: that follows the link, so a *dangling* symlink
            # would be skipped here as though it were absent, while
            # `snapshot_paths` counted it as present — and the file would pass
            # completeness with nothing behind it.
            continue
        unsafe = source_problems(source, cache_root=cache_root)
        if unsafe:
            problems.extend(
                Problem(
                    code=problem.code,
                    message=problem.message,
                    location=path,
                    repository=where,
                )
                for problem in unsafe
            )
            continue
        landed = source.resolve().stat().st_size
        if landed != expected[path]:
            message = (
                f"{path} landed at {landed} bytes but the Hub tree for {where} lists "
                f"{expected[path]}; the two disagree, which is enough to stop a publication "
                f"without deciding which is wrong"
            )
            problems.append(
                Problem(code="HFSYN003", message=message, location=path, repository=where)
            )
    return problems


# --------------------------------------------------------------------------- #
# Hashing new content (plan §13.2 step 9, §16.1)
# --------------------------------------------------------------------------- #


@final
@dataclass(frozen=True, slots=True)
class KnownDigest:
    """A digest this archive already computed, and the publication it belongs to."""

    commit_sha: CommitSha
    publication_id: PublicationId
    sha256: str
    size: int


@final
@dataclass(frozen=True, slots=True)
class HashedFile:
    """One repository path, with the digest that will go into its manifest.

    `reused_from` is the retained publication whose inode this object shares.
    `None` means the bytes were read during this run, which is the case the
    manifest records as `hashed = true`.
    """

    path: str
    sha256: str
    size: int
    object_identity: ObjectIdentity
    reused_from: KnownDigest | None = None


@final
@dataclass(frozen=True, slots=True)
class HashedSnapshot:
    """What ingestion verification read, ready for a manifest.

    `files` has one entry per repository path; `hashed_objects` and
    `hashed_bytes` count *physical objects*, so two paths hardlinked to one blob
    contribute one object and one file's worth of bytes while still producing two
    manifest entries. That distinction is what `docs/schemas.md` §3.4 means by
    hashed objects, and it is also why a large repository of deduplicated
    content is cheap to re-ingest.
    """

    files: tuple[HashedFile, ...]
    hashed_bytes: int
    hashed_objects: int

    @property
    def reused_digests(self) -> int:
        """Entries whose digest came from a retained publication, not a read."""
        return sum(1 for entry in self.files if entry.reused_from is not None)

    @property
    def total_bytes(self) -> int:
        """Logical size of the revision: every path, whether or not shared."""
        return sum(entry.size for entry in self.files)


def published_digests(tree: Path, manifest: RevisionManifest) -> dict[ObjectIdentity, KnownDigest]:
    """Index one retained publication's objects by the inode they occupy now.

    This is what makes plan §16.1's reuse rule checkable rather than aspirational.
    The manifest supplies the digest — a value this archive computed and has
    since verified — and the filesystem supplies the identity, read at the moment
    the index is built. Neither alone would do: a manifest cannot say which inode
    its bytes live on today, and an inode cannot say what it hashes to.

    A path the manifest lists but the tree no longer holds is skipped rather than
    reported. A missing published file is real corruption, but it is `verify`'s
    finding to make and act on (`AD-13`); all it means here is that there is no
    proven inode to reuse a digest from, so the object gets hashed.
    """
    index: dict[ObjectIdentity, KnownDigest] = {}
    for entry in manifest.files:
        source = tree / entry.path
        try:
            identity = ObjectIdentity.of(source)
        except OSError:
            continue
        index[identity] = KnownDigest(
            commit_sha=CommitSha(manifest.commit_sha),
            publication_id=PublicationId(manifest.publication_id),
            sha256=entry.sha256,
            size=entry.size,
        )
    return index


def hash_snapshot(
    snapshot: Path,
    tree: Sequence[TreeEntry],
    *,
    identity: RepositoryIdentity,
    known: Mapping[ObjectIdentity, KnownDigest] | None = None,
) -> HashedSnapshot:
    """Read every newly introduced unique object once (plan §13.2 step 9).

    Two kinds of reuse, and the difference between them is the whole of §16.1.

    *Within this run*, two repository paths that resolve to one inode are hashed
    once. Both manifest entries still record `hashed = true`, because the bytes
    genuinely were read during this run — what was avoided is a second read of
    the same object, not a second verification.

    *Across runs*, a digest from a retained publication is reused only when the
    object is proven to be the same inode **and** the same size. Both conditions,
    because an inode number is reused by the filesystem after deletion and a size
    that no longer matches is the cheapest possible evidence that it has been.
    Such an entry records `hashed = false` and names the publication it came
    from, so a manifest never contains a digest whose origin cannot be traced
    back to bytes this archive read.

    Everything else is hashed. An upstream digest is never a substitute
    (`AD-18`), and no path is exempt for being large.
    """
    known = known or {}
    hashed: dict[ObjectIdentity, str] = {}
    files: list[HashedFile] = []
    hashed_bytes = 0

    for entry in sorted(tree, key=lambda item: item.path):
        source = snapshot / entry.path
        try:
            object_identity = ObjectIdentity.of(source)
            size = object_identity.size
        except OSError as exc:
            message = (
                f"{entry.path} could not be examined before hashing ({exc.strerror}); the "
                f"completeness check passed, so the object was there and is not now"
            )
            raise SynchronizationError.single(
                message, code="HFSYN009", location=entry.path, repository=identity.selector
            ) from exc

        if (digest := hashed.get(object_identity)) is not None:
            files.append(
                HashedFile(
                    path=entry.path,
                    sha256=digest,
                    size=size,
                    object_identity=object_identity,
                )
            )
            continue

        candidate = known.get(object_identity)
        if candidate is not None and candidate.size == size:
            files.append(
                HashedFile(
                    path=entry.path,
                    sha256=candidate.sha256,
                    size=size,
                    object_identity=object_identity,
                    reused_from=candidate,
                )
            )
            continue

        read = sha256_identified_file(source, error=SynchronizationError, code="HFSYN009")
        if read.identity != object_identity:
            message = (
                f"{entry.path} changed objects between examination and hashing; a digest "
                "is carried into publication only for the exact object read"
            )
            raise SynchronizationError.single(
                message, code="HFSYN009", location=entry.path, repository=identity.selector
            )
        hashed[object_identity] = read.digest
        hashed_bytes += read.size
        files.append(
            HashedFile(
                path=entry.path,
                sha256=read.digest,
                size=read.size,
                object_identity=object_identity,
            )
        )

    return HashedSnapshot(files=tuple(files), hashed_bytes=hashed_bytes, hashed_objects=len(hashed))


# --------------------------------------------------------------------------- #
# Describing the revision (plan §13.2 step 12, §10.1)
# --------------------------------------------------------------------------- #


@final
@dataclass(frozen=True, slots=True)
class Timeline:
    """When each stage of one ingestion happened (`docs/schemas.md` §3.1).

    Carried as a value rather than stamped inside the builder because the
    manifest's own validator checks these are ordered, and the moments it
    describes happened in the caller — `download_started_at` before a download
    this function never saw. Stamping them here would record when the manifest
    was assembled and call it when the work occurred.

    `first_observed_at` is separate from the rest and may predate them by weeks:
    it records when this SHA was first seen for this repository, which for a
    republished or repaired revision is not when this instance was built.
    """

    first_observed_at: datetime
    download_started_at: datetime
    download_completed_at: datetime
    verified_at: datetime
    published_at: datetime


def build_manifest(  # noqa: PLR0913 - §10.1 fixes the field set; each argument is one of them
    *,
    identity: RepositoryIdentity,
    requested_revision: str,
    commit_sha: CommitSha,
    publication_id: PublicationId,
    publication_generation: int,
    publication_mode: Literal["hardlink", "copy"],
    tree: Sequence[TreeEntry],
    hashed: HashedSnapshot,
    layout: RepositoryLayout,
    hub_endpoint: str,
    timeline: Timeline,
    dependencies: Sequence[DependencyObservation] = (),
    cache_root: Literal["canonical", "repair"] = "canonical",
    repair: RepairProvenance | None = None,
) -> RevisionManifest:
    """Assemble the immutable description of one publication instance.

    Every number in the result comes from what was read rather than from what
    was claimed: sizes and digests are `HashedSnapshot`'s, and the Hub's tree
    contributes only the three upstream identifiers, which are comparison values
    and never a substitute (`AD-18`, plan §10.1).

    The model does the checking. `file_count` against `len(files)`, `total_bytes`
    against the sum, `reused_digests` against the entries marked unhashed,
    byte-wise path ordering, collision folding, and the timeline's order are all
    enforced by `RevisionManifest` itself, so a manifest that describes no real
    tree cannot be constructed here and cannot be read back later. This function
    is deliberately thin over that: it arranges inputs, it does not decide
    whether they are consistent.

    Nothing is written. Plan §13.2 step 12 writes to a temporary sibling and step
    16 publishes it atomically, and both belong to the transaction that owns the
    filesystem — this returns the value they persist.
    """
    upstream = {entry.path: entry for entry in tree}
    files = tuple(
        FileEntry(
            path=entry.path,
            provenance=_provenance(entry, cache_root=cache_root),
            sha256=entry.sha256,
            size=entry.size,
            upstream=_upstream(upstream.get(entry.path)),
        )
        for entry in hashed.files
    )
    versions = RuntimeVersions.measured()
    return RevisionManifest(
        application_version=versions.application,
        commit_sha=commit_sha,
        dependencies=tuple(
            sorted(
                dependencies,
                key=lambda item: (item.source_file, item.source_field, item.detected_id),
            )
        ),
        download_completed_at=timeline.download_completed_at,
        download_started_at=timeline.download_started_at,
        file_count=len(files),
        files=files,
        first_observed_at=timeline.first_observed_at,
        hub_endpoint=hub_endpoint,
        huggingface_hub_version=versions.huggingface_hub,
        publication_generation=publication_generation,
        publication_id=publication_id,
        publication_mode=publication_mode,
        published_at=timeline.published_at,
        python_version=versions.python,
        repair=repair,
        repository_id=identity.id,
        repository_type=identity.type,
        requested_revision=requested_revision,
        total_bytes=hashed.total_bytes,
        tree=str(layout.manifest_tree_field(commit_sha, publication_id)),
        verification=VerificationSummary(
            completeness_checked=True,
            hashed_bytes=hashed.hashed_bytes,
            hashed_objects=hashed.hashed_objects,
            outcome="verified",
            reused_digests=hashed.reused_digests,
            verified_at=timeline.verified_at,
        ),
        verified_at=timeline.verified_at,
    )


def _provenance(entry: HashedFile, *, cache_root: Literal["canonical", "repair"]) -> FileProvenance:
    """How one object's bytes were obtained, in the manifest's own terms.

    The three fields are not independent, and `FileProvenance` refuses the
    combinations that would misdescribe an object: an unhashed entry must name
    the publication whose inode it shares, and a repair download must come from
    the repair cache root (`FS-14`). What is decided here is only which of the
    permitted combinations this entry is.
    """
    if entry.reused_from is not None:
        return FileProvenance(
            cache_root=cache_root,
            hash_reused_from=HashReuse(
                commit_sha=entry.reused_from.commit_sha,
                publication_id=entry.reused_from.publication_id,
            ),
            hashed=False,
            source="cache_reuse",
        )
    return FileProvenance(
        cache_root=cache_root,
        hash_reused_from=None,
        hashed=True,
        source="repair_download" if cache_root == "repair" else "hub_download",
    )


def _upstream(entry: TreeEntry | None) -> UpstreamIdentifiers:
    """What upstream said about an object, or nothing when it said nothing.

    A path that is not in the tree cannot reach here — completeness refused it
    already — but the lookup is written total rather than trusting that, because
    the alternative is a `KeyError` from the middle of manifest construction
    for a condition that has a perfectly good empty answer.
    """
    if entry is None:  # pragma: no cover - completeness refuses this first
        return UpstreamIdentifiers()
    return UpstreamIdentifiers(
        git_oid=entry.git_oid, lfs_sha256=entry.lfs_sha256, xet_hash=entry.xet_hash
    )


# --------------------------------------------------------------------------- #
# Publishing the revision (plan §13.2 steps 11-19, §7.3)
# --------------------------------------------------------------------------- #


@final
@dataclass(frozen=True, slots=True)
class PublicationOutcome:
    """What one successful ingestion produced."""

    commit_sha: CommitSha
    manifest: RevisionManifest
    publication_generation: int
    publication_id: PublicationId
    tree: Path


def publish_revision(  # noqa: PLR0913 - the §7.3 sequence's inputs, one argument each
    layout: ArchiveLayout,
    transaction: Transaction,
    *,
    identity: RepositoryIdentity,
    snapshot: Path,
    manifest: RevisionManifest,
    hashed: HashedSnapshot,
    staging: StagingPaths,
    publication_mode: Literal["hardlink", "copy"],
    cache_root: Path,
    configured: Mapping[str, RepositoryConfig] = MappingProxyType({}),
) -> PublicationOutcome:
    """Build, rename, reference, and record one revision (§7.3 checkpoints 4-9).

    Every step is one atomic act followed by the checkpoint that names it, in the
    order §7.3 fixes, and `Transaction.checkpoint` refuses a name that is not
    next — so a journal this function produced can only describe an execution
    that really happened.

    The order is not arbitrary and each adjacency is load-bearing:

    * The manifest is written into **staging** before the rename, so the tree
      that appears at checkpoint 5 can always be validated (see
      `PENDING_MANIFEST`).
    * The tree is renamed before the manifest is published, so a manifest never
      names a tree that is not there.
    * Both are durable before `refs/revisions/<sha>.json`, and that before
      `refs/current.json` — `FS-10`, enforced again at the point of each write by
      `publish_revision_reference` and `publish_current_reference`.
    * `current.json` is replaced by a single rename, so the previous current
      revision is usable on both sides of it and a consumer either sees the old
      tree or the new one, never a mixture (`FS-12`).

    The catalog comes last because it is derived (`FS-16`). Nothing reads it to
    decide anything; it is rebuilt from the manifests and references this
    function just made durable.
    """
    # Driven by the manifest, not by the hash result or the Hub tree they both
    # came from: the tree that reaches `published/` then cannot contain a path
    # its own manifest does not list, by construction rather than by agreement
    # between three collections.
    hashed_by_path = {entry.path: entry for entry in hashed.files}
    for entry in manifest.files:
        evidence = hashed_by_path.get(entry.path)
        if evidence is None or evidence.sha256 != entry.sha256 or evidence.size != entry.size:
            message = (
                f"manifest entry {entry.path} does not match this operation's transient "
                "hash evidence; publication was refused"
            )
            raise SynchronizationError.single(
                message,
                code="HFSYN005",
                location=entry.path,
                repository=identity.selector,
            )
        stage_file(
            snapshot / entry.path,
            staged_path(staging, entry.path),
            publication_mode=publication_mode,
            cache_root=cache_root,
            expected=FileDigest(digest=evidence.sha256, size=evidence.size),
            expected_identity=evidence.object_identity,
        )
    # `StagingPaths.manifest` is a sibling of `tree/`, so it does not travel with
    # the rename at checkpoint 5 — which is the point. §7.3 writes it here,
    # *before* the tree moves, because that is what makes a crash between
    # checkpoints 5 and 6 recoverable: the published tree can still be validated
    # against a manifest that already exists. Written after the rename instead,
    # the tree would be one nothing can vouch for, and §7.3's crash matrix
    # quarantines such a tree rather than publishing it.
    pending = staging.manifest
    write_model(
        pending, manifest, mode=PUBLISHED_FILE_MODE, code="HFSYN008", error=SynchronizationError
    )
    fsync_directory(staging.tree)
    transaction.checkpoint(
        "staging_built",
        # `staging_tree` carries no `_path` suffix on purpose (decision 53).
        # Checkpoint 5 renames this directory away, so asserting it still exists
        # would make every journal that got past 5 contradict the filesystem —
        # which is exactly the state recovery has to roll *forward* from. The
        # pending manifest is a sibling of `tree/` and does not travel with the
        # rename, so it keeps the suffix and stays checkable.
        staging_tree=str(layout.archive_relative(staging.tree)),
        file_count=manifest.file_count,
        # `pending_manifest` carries no `_path` suffix either, for decision 53's
        # reason applied to decision 56's change: checkpoint 10 discards the whole
        # staging area now that the manifest is published, so asserting this file
        # still exists would make every committed journal contradict the archive.
        pending_manifest=str(layout.archive_relative(pending)),
    )

    repository = RepositoryLayout(archive=layout, identity=identity)
    commit_sha = CommitSha(manifest.commit_sha)
    publication_id = PublicationId(manifest.publication_id)
    instance = repository.instance(commit_sha, publication_id)
    promote_staging(layout, staging, instance)
    transaction.checkpoint(
        "revision_tree_renamed",
        published_tree_path=str(layout.archive_relative(instance)),
        file_count=manifest.file_count,
    )

    published_manifest = repository.manifest(commit_sha, publication_id)
    published_manifest.parent.mkdir(mode=PUBLISHED_DIRECTORY_MODE, parents=True, exist_ok=True)
    write_model(
        published_manifest,
        manifest,
        mode=PUBLISHED_FILE_MODE,
        code="HFSYN008",
        error=SynchronizationError,
    )
    fsync_directory(published_manifest.parent)
    transaction.checkpoint(
        "manifest_published",
        manifest_path=str(layout.archive_relative(published_manifest)),
        manifest_sha256=sha256_file(published_manifest).digest,
    )

    reference = Reference(
        commit_sha=commit_sha,
        manifest=str(repository.manifest_reference(commit_sha, publication_id)),
        publication_generation=manifest.publication_generation,
        publication_id=publication_id,
        repository_id=identity.id,
        repository_type=identity.type,
        tree=str(repository.tree_reference(commit_sha, publication_id)),
        updated_at=manifest.published_at,
    )
    publish_revision_reference(layout, reference)
    transaction.checkpoint(
        "revision_ref_published",
        revision_ref_path=str(layout.archive_relative(repository.revision_ref(commit_sha))),
        publication_id=publication_id,
    )

    previous = _current_pair(layout, repository)
    publish_current_reference(layout, reference)
    transaction.checkpoint(
        "current_ref_replaced",
        current_ref_path=str(layout.archive_relative(repository.current_ref)),
        new=[commit_sha, publication_id],
        previous=list(previous) if previous else None,
    )

    catalog = rebuild_catalog(layout, configured=configured, generated_at=manifest.published_at)
    catalog_path = publish_catalog(layout, catalog)
    transaction.checkpoint(
        "catalog_rebuilt",
        catalog_path=str(layout.archive_relative(catalog_path)),
        catalog_sha256=sha256_file(catalog_path).digest,
    )

    return PublicationOutcome(
        commit_sha=commit_sha,
        manifest=manifest,
        publication_generation=manifest.publication_generation,
        publication_id=publication_id,
        tree=instance,
    )


def _current_pair(layout: ArchiveLayout, repository: RepositoryLayout) -> tuple[str, str] | None:
    """The `(commit_sha, publication_id)` `current.json` names, before it moves.

    Recorded as checkpoint 8's evidence so recovery can tell a completed switch
    from one that never happened. `None` is the first publication, which is a
    real answer and not a missing one.
    """
    if not repository.current_ref.exists():
        return None
    reference = read_reference(layout, repository.current_ref)
    return (reference.commit_sha, reference.publication_id)


# --------------------------------------------------------------------------- #
# Synchronizing one repository (plan §13.2)
# --------------------------------------------------------------------------- #


@final
@dataclass(frozen=True, slots=True)
class RepositoryOutcome:
    """One repository's result, plus the manifest when it published one."""

    result: RepositoryRunResult
    manifest: RevisionManifest | None = None


def synchronize_repository(  # noqa: PLR0913 - plan §13.2 needs all of these to run
    client: HubClient,
    layout: ArchiveLayout,
    repository: RepositoryConfig,
    config: ApplicationConfig,
    *,
    run_id: RunId,
    configured: Mapping[str, RepositoryConfig],
) -> RepositoryOutcome:
    """Run plan §13.2 for one repository, from resolution to publication.

    The order is the plan's and the reasons are its: resolve to an immutable SHA
    first so nothing below can be about a moving target; skip early if that SHA
    is already held, because re-downloading content the archive already proved is
    the most expensive way to learn nothing; estimate and check capacity before
    downloading rather than after, because discovering the dataset is full
    halfway through a large model wastes the whole transfer.

    A failure raises. Deciding whether one repository's failure ends the run is
    the caller's, because it is a policy question — `sync.continue_on_repository_error`
    — and this function is where the work is, not where the policy is.
    """
    identity = RepositoryIdentity.from_config(repository)
    started = _now()
    facts = client.repository(identity, repository.revision)
    emit(
        "repository.resolved",
        repository=identity.selector,
        requested_revision=repository.revision,
        commit_sha=facts.commit_sha,
    )

    if (held := _already_retained(layout, identity, facts.commit_sha)) is not None:
        result = _retained_result(layout, repository, identity, held, started)
        emit(
            "repository.skipped",
            repository=identity.selector,
            commit_sha=facts.commit_sha,
            status=result.status,
        )
        return RepositoryOutcome(result=result)

    estimate = client.estimate(
        identity,
        facts.commit_sha,
        cache_dir=layout.hub_cache,
        max_workers=config.sync.max_workers,
    )
    needed = estimate.new_bytes + projected_publication_bytes(
        estimate.logical_bytes, publication_mode=config.storage.publication_mode
    )
    warnings = require_capacity(layout, config.storage, needed_bytes=needed)
    emit(
        "capacity.evaluated",
        repository=identity.selector,
        needed_bytes=needed,
        new_bytes=estimate.new_bytes,
        cached_bytes=estimate.cached_bytes,
        logical_bytes=estimate.logical_bytes,
    )

    transaction_id = new_transaction_id()
    transaction = open_transaction(
        layout,
        transaction_id=transaction_id,
        operation="publication",
        run_id=run_id,
        archive_id=config.storage.archive_id,
        config_fingerprint=config.fingerprint(),
        repository_id=identity.id,
        repository_type=identity.type,
        commit_sha=facts.commit_sha,
    )
    try:
        return _ingest(
            client,
            layout,
            transaction,
            repository=repository,
            config=config,
            identity=identity,
            facts=facts,
            estimate=estimate,
            started=started,
            configured=configured,
            warnings=warnings,
            run_id=run_id,
        )
    except HfcacheError as error:
        transaction.fail(error.problems[0].code, error.problems[0].message)
        # §7.3's "Before 5 → roll back", performed by the command that knows it
        # failed rather than left for a recovery that will never look. A journal
        # closed `failed` is *resolved*, so `open_journals` skips it and
        # `plan_recovery` never proposes a remedy for the staging it left — while
        # `reconcile_storage` goes on reporting that directory as unfinished work
        # and warns `HFWRN004` about it once it ages. That is decision 56's
        # problem in the failure path, and this is the same answer.
        #
        # Only before the rename. At or after checkpoint 5 a tree is published
        # and the staged manifest is the only thing that can validate it (§7.3),
        # so it is preserved — a resolved journal past that point is a state an
        # operator has to look at, and deleting its evidence first would be the
        # wrong help.
        if not _tree_was_renamed(transaction):
            discard_staging(layout, transaction_id)
        raise


def _tree_was_renamed(transaction: Transaction) -> bool:
    """Whether this publication got as far as §7.3 checkpoint 5."""
    return any(
        checkpoint.name == "revision_tree_renamed" for checkpoint in transaction.journal.checkpoints
    )


def _ingest(  # noqa: PLR0913 - the §13.2 sequence's inputs, one argument each
    client: HubClient,
    layout: ArchiveLayout,
    transaction: Transaction,
    *,
    repository: RepositoryConfig,
    config: ApplicationConfig,
    identity: RepositoryIdentity,
    facts: RepositoryFacts,
    estimate: DownloadEstimate,
    started: datetime,
    configured: Mapping[str, RepositoryConfig],
    warnings: Sequence[Problem],
    run_id: RunId,
) -> RepositoryOutcome:
    """Plan §13.2 steps 5-20, inside an open journal (§7.3 checkpoints 1-10)."""
    transaction_id = TransactionId(transaction.journal.transaction_id)
    staging = create_staging(layout, transaction_id)
    transaction.checkpoint(
        "staging_created", staging_path=str(layout.archive_relative(staging.directory))
    )

    download_started = _now()
    emit(
        "download.started",
        repository=identity.selector,
        commit_sha=facts.commit_sha,
        new_bytes=estimate.new_bytes,
        file_count=estimate.file_count,
    )
    client.download(
        identity,
        facts.commit_sha,
        cache_dir=layout.hub_cache,
        max_workers=config.sync.max_workers,
    )
    snapshot = client.verify_local(identity, facts.commit_sha, cache_dir=layout.hub_cache)
    download_completed = _now()
    transaction.checkpoint(
        "download_completed",
        commit_sha=facts.commit_sha,
        downloaded_bytes=estimate.new_bytes,
    )
    emit(
        "download.completed",
        repository=identity.selector,
        commit_sha=facts.commit_sha,
        downloaded_bytes=estimate.new_bytes,
        seconds=round((download_completed - download_started).total_seconds(), 3),
    )

    tree = client.tree(identity, facts.commit_sha)
    if problems := completeness_problems(
        snapshot, tree, identity=identity, cache_root=layout.hub_cache
    ):
        raise SynchronizationError(problems)

    hashed = hash_snapshot(
        snapshot, tree, identity=identity, known=_known_digests(layout, identity)
    )
    verified = _now()
    transaction.checkpoint(
        "content_hashed",
        hashed_objects=hashed.hashed_objects,
        hashed_bytes=hashed.hashed_bytes,
        reused_digests=hashed.reused_digests,
    )

    # Plan §13.2 step 10, from the snapshot rather than the Hub: detection reads
    # the same bytes that were hashed and will be published, so it cannot report
    # a dependency the archived revision does not actually declare.
    observations = detect_dependencies(
        snapshot,
        declared=repository.declared_dependencies,
        # Bare repository ids, not selectors: plan §17 asks whether the detected
        # repository "is independently configured for archive management", and a
        # `base_model` value names a repository without a type prefix. Matching
        # across types is deliberate — a dataset and a model sharing an id is
        # pathological, and reporting it managed is the harmless direction.
        managed=sorted({entry.id for entry in configured.values()}),
    )
    dependency_warnings = [
        Problem(
            code=code,
            message=(
                f"{identity.selector} declares dependencies its configuration does not: "
                + ", ".join(item.detected_id for item in undeclared(observations))
            ),
            repository=identity.selector,
        )
        for code in undeclared_warnings(observations)
    ]
    for item in undeclared(observations):
        emit(
            "dependency.undeclared",
            repository=identity.selector,
            commit_sha=facts.commit_sha,
            detected=item.detected_id,
            source=item.source_file,
            confidence=item.confidence,
            managed=item.managed,
        )

    manifest = build_manifest(
        dependencies=observations,
        identity=identity,
        requested_revision=repository.revision,
        commit_sha=facts.commit_sha,
        publication_id=new_publication_id(),
        publication_generation=next_generation(layout, identity),
        publication_mode=config.storage.publication_mode,
        tree=tree,
        hashed=hashed,
        layout=RepositoryLayout(archive=layout, identity=identity),
        hub_endpoint=config.hub.endpoint,
        timeline=Timeline(
            first_observed_at=started,
            download_started_at=download_started,
            download_completed_at=download_completed,
            verified_at=verified,
            published_at=_now(),
        ),
    )
    outcome = publish_revision(
        layout,
        transaction,
        identity=identity,
        snapshot=snapshot,
        manifest=manifest,
        hashed=hashed,
        staging=staging,
        publication_mode=config.storage.publication_mode,
        cache_root=layout.hub_cache,
        configured=configured,
    )
    # Checkpoint 10's act (decision 56). The staging area held the tree, which
    # checkpoint 5 renamed away, and the pending manifest, which checkpoint 6
    # published — so what is left is a redundant copy of an artifact the archive
    # now owns. Discarded here rather than left behind, because a directory under
    # `.store/staging` is how `reconcile_storage` recognises *unfinished* work:
    # one per published revision would report a finished publication as
    # outstanding, and warn `HFWRN004` about it once it aged past the configured
    # staleness. Inside `FS-19` because the path is derived from the transaction
    # id (`FS-18`), never read off the filesystem.
    discard_staging(layout, transaction_id)
    transaction.checkpoint(
        "publication_committed",
        state="committed",
        staging_absent=str(layout.archive_relative(staging.directory)),
    )
    transaction.commit()
    emit(
        "publication.completed",
        repository=identity.selector,
        commit_sha=outcome.commit_sha,
        publication_id=outcome.publication_id,
        publication_generation=outcome.publication_generation,
        file_count=manifest.file_count,
        logical_bytes=manifest.total_bytes,
        hashed_bytes=hashed.hashed_bytes,
        reused_digests=hashed.reused_digests,
        mode=config.storage.publication_mode,
    )

    # Plan §13.2 step 20, and only here: retention is triggered by a *successful*
    # publication (`AD-04`), so it runs after the publication transaction has
    # committed rather than inside it. A prune that failed would then be its own
    # failure with its own journal, and could never take the revision that was
    # just published down with it.
    pruned = _apply_retention(layout, identity, config, run_id=run_id)

    reported = [*warnings, *dependency_warnings]
    return RepositoryOutcome(
        manifest=manifest,
        result=RepositoryRunResult(
            downloaded_bytes=estimate.new_bytes,
            duration_seconds=(_now() - started).total_seconds(),
            file_count=manifest.file_count,
            hashed_bytes=hashed.hashed_bytes,
            publication_generation=outcome.publication_generation,
            publication_id=outcome.publication_id,
            repository_id=identity.id,
            repository_type=identity.type,
            requested_revision=repository.revision,
            resolved_commit_sha=outcome.commit_sha,
            pruned=pruned,
            reused_bytes=estimate.cached_bytes,
            status="completed_with_warnings" if reported else "published",
            warnings=tuple(sorted({warning.code for warning in reported})),
        ),
    )


def _apply_retention(
    layout: ArchiveLayout,
    identity: RepositoryIdentity,
    config: ApplicationConfig,
    *,
    run_id: RunId,
) -> PrunedRevision | None:
    """Rotate the oldest revision out if this publication was the sixth (§15.2).

    Returns what went, for the run report, or `None` when nothing did — which is
    every run in steady state below the limit.

    A prune failure does not fail the repository. The newly published revision is
    kept and the archive reports temporary over-retention (`HFWRN001`), because
    §15.2's failure rule is explicit that a failed prune removes nothing and
    prefers keeping six revisions to losing one.
    """
    plan = plan_prune(
        layout,
        identity,
        maximum=config.storage.maximum_revisions,
        generated_at=_now(),
    )
    if plan is None:
        return None
    record = apply_prune(
        layout,
        plan,
        envelope={
            "archive_id": config.storage.archive_id,
            "config_fingerprint": config.fingerprint(),
            "run_id": run_id,
        },
    )
    emit(
        "retention.pruned",
        repository=identity.selector,
        commit_sha=record.commit_sha,
        publication_generation=record.publication_generation,
        publication_id=record.publication_id,
        logical_bytes=record.logical_bytes,
        file_count=record.file_count,
        retained_after=len(record.retained_after),
    )
    return PrunedRevision(
        commit_sha=record.commit_sha,
        logical_bytes=record.logical_bytes,
        publication_generation=record.publication_generation,
    )


def _already_retained(
    layout: ArchiveLayout, identity: RepositoryIdentity, commit_sha: CommitSha
) -> Reference | None:
    """The active instance reference for a SHA the archive already holds.

    Plan §13.2 step 2. `refs/revisions/<sha>.json` is what makes a SHA retained,
    so this is the whole question — not whether a directory exists, which can be
    a superseded repair instance inside its grace period.
    """
    repository = RepositoryLayout(archive=layout, identity=identity)
    path = repository.revision_ref(commit_sha)
    if not path.exists():
        return None
    return read_reference(layout, path)


def _retained_result(
    layout: ArchiveLayout,
    repository: RepositoryConfig,
    identity: RepositoryIdentity,
    held: Reference,
    started: datetime,
) -> RepositoryRunResult:
    """Report a SHA the archive already holds, moving the current ref if needed.

    Two outcomes look alike from outside and mean different things to an
    operator, which is why `docs/schemas.md` §6 gives them different names.
    `skipped` is upstream not having moved. `ref_moved_to_retained_revision` is
    upstream having moved *back* to something already held — no bytes fetched,
    but consumers are now being pointed somewhere else, which is a change worth
    seeing in a run report.

    Retention order is untouched either way. Re-observing a SHA does not make a
    duplicate or reorder the sequence (§15.1), so the generation stays as it was.
    """
    layout_for = RepositoryLayout(archive=layout, identity=identity)
    current = layout_for.current_ref
    moved = (
        not current.exists()
        or read_reference(layout, current).publication_id != held.publication_id
    )
    if moved:
        publish_current_reference(layout, held)
    return RepositoryRunResult(
        duration_seconds=(_now() - started).total_seconds(),
        publication_generation=held.publication_generation,
        publication_id=held.publication_id,
        repository_id=identity.id,
        repository_type=identity.type,
        requested_revision=repository.revision,
        resolved_commit_sha=held.commit_sha,
        status="ref_moved_to_retained_revision" if moved else "skipped",
    )


def _known_digests(
    layout: ArchiveLayout, identity: RepositoryIdentity
) -> dict[ObjectIdentity, KnownDigest]:
    """Every digest this repository's retained publications already established.

    Built per repository rather than archive-wide, because §16.1's reuse rule
    needs the digest to come from a *retained verified publication*, and the
    references that define that set are per repository. Sharing across
    repositories would be sound — an inode is an inode — but it would also mean
    a manifest citing a publication of a different repository as its evidence,
    which is far harder to follow during an incident than a second read.
    """
    index: dict[ObjectIdentity, KnownDigest] = {}
    repository = RepositoryLayout(archive=layout, identity=identity)
    for reference in retained_references(layout, identity):
        manifest_path = repository.manifest(
            CommitSha(reference.commit_sha), PublicationId(reference.publication_id)
        )
        manifest = read_model(
            manifest_path, RevisionManifest, error=IntegrityError, code="HFVER007"
        )
        index |= published_digests(layout.published / str(reference.tree), manifest)
    return index


def _now() -> datetime:
    """This moment, in UTC. One reader so a run's timeline is self-consistent."""
    return datetime.now(UTC)


# --------------------------------------------------------------------------- #
# Synchronizing a run (plan §13.1)
# --------------------------------------------------------------------------- #


RUN_REPORT_MODE: Final = 0o600
"""Run reports live under `runs/`, which is private to the writer (§5.2).

Not consumer-visible and not meant to be: a run report names transaction ids,
cache paths, and per-repository byte counts, none of which a read-only consumer
has any use for and some of which describe the writer's private areas.
"""


@final
@dataclass(frozen=True, slots=True)
class RunOutcome:
    """What one `sync` run did, and where it recorded it."""

    report: RunReport
    report_path: Path
    exit_code: ExitCode


def synchronize(  # noqa: PLR0913 - plan §13.1's inputs, one argument each
    client: HubClient,
    layout: ArchiveLayout,
    config: ApplicationConfig,
    transaction: Transaction,
    *,
    selected: Sequence[RepositoryConfig],
    envelope: Mapping[str, Any],
    run_id: RunId,
    started_at: datetime,
) -> RunOutcome:
    """Process every selected repository and record the run (plan §13.1 steps 5-11).

    The lock, the storage preflight, and the §7.6 run journal are all the
    caller's, composed at the command boundary in §13.1's order: lock (step 2),
    preflight (step 3), then the journal whose first three checkpoints record
    that the run started, that the preflight passed, and that unfinished
    journals were reconciled before the Hub was contacted (`TX-07`). Holding
    them around this call is what makes every check they performed still true
    while the work happens.

    This function records the remaining four checkpoints, each after the act it
    names is durable (`TX-02`), and closes the journal. A run whose exit code is
    not `0` still commits: the *run transaction* completed, and which
    repositories failed is what the durable report and checkpoint 7's evidence
    are for.

    Deterministic configuration order, always. Not selector order, not
    alphabetical, not "smallest first": two runs naming the same repositories
    must do the same things in the same sequence, because that is what makes a
    partial run's journals interpretable and a failure reproducible.

    A disabled repository is reported rather than omitted. An operator who
    disabled something wants to see that the run knew about it and left it
    alone; silence looks the same as a configuration that never mentioned it.
    """
    configured = {
        RepositoryIdentity.from_config(repository).selector: repository
        for repository in config.repositories
    }
    results: list[RepositoryRunResult] = []
    totals = {"downloaded_bytes": 0, "hashed_bytes": 0, "reused_bytes": 0}
    for repository in selected:
        if not repository.enabled:
            results.append(_disabled_result(repository))
            continue
        try:
            result = synchronize_repository(
                client, layout, repository, config, run_id=run_id, configured=configured
            ).result
        except HfcacheError as error:
            # Every local revision of this repository is preserved regardless
            # (`AD-06`): a failure here means the run learned nothing new about
            # it, never that what it already holds is suspect.
            failed = _failed_result(repository, error)
            emit(
                "repository.failed",
                repository=f"{failed.repository_type}:{failed.repository_id}",
                codes=",".join(failed.errors),
                # The first problem's message, which is the one an operator reads
                # first anyway. `_scrub` still passes over it, because a message
                # is free text and a path in it could carry anything.
                detail=error.problems[0].message,
                continuing=config.sync.continue_on_repository_error,
            )
            results.append(failed)
            if not config.sync.continue_on_repository_error:
                break
            continue
        results.append(result)
        totals["downloaded_bytes"] += result.downloaded_bytes
        totals["hashed_bytes"] += result.hashed_bytes
        totals["reused_bytes"] += result.reused_bytes

    transaction.checkpoint(
        "repositories_processed",
        statuses={
            f"{result.repository_type}:{result.repository_id}": result.status for result in results
        },
    )

    # Plan §13.1 step 10, a *whole-run* step distinct from §7.3 checkpoint 9.
    # The per-publication rebuild keeps the catalog current with each revision;
    # this keeps it current with each *configuration*, which changes without any
    # revision being published — a repository removed from the file is still
    # archived and must start reading as unmanaged (`AD-06`) on the next run
    # rather than on the next time something happens to publish.
    catalog_path = publish_catalog(
        layout, rebuild_catalog(layout, configured=configured, generated_at=_now())
    )
    transaction.checkpoint(
        "catalog_rebuilt",
        catalog_path=str(layout.archive_relative(catalog_path)),
        catalog_sha256=sha256_file(catalog_path).digest,
    )

    codes = [code for result in results for code in result.errors]
    exit_code = aggregate_exit_code(codes)
    report = RunReport.model_validate(
        {
            **envelope,
            "command": "sync",
            "completed_at": _now(),
            "errors": tuple(sorted(set(codes))),
            "exit_code": int(exit_code),
            "outcome": _outcome(exit_code, results),
            "repositories": tuple(
                sorted(results, key=lambda r: (r.repository_type, r.repository_id))
            ),
            "run_id": run_id,
            "started_at": started_at,
            "totals": RunTotals(**totals),
            "warnings": tuple(sorted({w for result in results for w in result.warnings})),
        }
    )
    # `runs/` is created by `archive init` and proven writable by the preflight
    # this run is holding, so it is written into rather than created here.
    path = layout.run_report(started_at, run_id)
    write_model(path, report, mode=RUN_REPORT_MODE, code="HFSYN008", error=SynchronizationError)
    fsync_directory(path.parent)
    transaction.checkpoint("run_report_written", run_report_path=str(layout.archive_relative(path)))
    transaction.checkpoint("run_completed", exit_code=int(exit_code), outcome=report.outcome)
    transaction.commit()
    emit(
        "run.completed",
        command="sync",
        exit_code=int(exit_code),
        outcome=report.outcome,
        repositories=len(results),
        downloaded_bytes=totals["downloaded_bytes"],
        hashed_bytes=totals["hashed_bytes"],
        reused_bytes=totals["reused_bytes"],
        report=str(layout.archive_relative(path)),
    )
    return RunOutcome(report=report, report_path=path, exit_code=exit_code)


def _failed_result(repository: RepositoryConfig, error: HfcacheError) -> RepositoryRunResult:
    """One repository that failed, recorded so the run can continue past it.

    Every code the failure carried, not just the first: a completeness check
    reports one problem per missing file, and an operator fixing an incomplete
    download should see the shape of the gap rather than its first element.
    """
    return RepositoryRunResult(
        errors=tuple(sorted({problem.code for problem in error.problems})),
        repository_id=repository.id,
        repository_type=repository.type,
        requested_revision=repository.revision,
        status="failed",
    )


def _disabled_result(repository: RepositoryConfig) -> RepositoryRunResult:
    """A repository configuration turned off, reported rather than omitted."""
    return RepositoryRunResult(
        repository_id=repository.id,
        repository_type=repository.type,
        requested_revision=repository.revision,
        status="disabled",
    )


def _outcome(exit_code: ExitCode, results: Sequence[RepositoryRunResult]) -> str:
    """The envelope's outcome, which must agree with the exit code it carries."""
    if exit_code != ExitCode.SUCCESS:
        return "failed"
    if any(result.warnings for result in results):
        return "success_with_warnings"
    return "success"
