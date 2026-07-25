"""The archive layout, and the rules that keep a path inside it.

`docs/architecture.md` §5.1 draws the tree this module builds and §5.2 gives the
modes. Three invariants are what it exists to make mechanical:

* **`FS-04`** — staging and every destination it is renamed into are computed
  from the same root, so publication is always a `rename(2)`.
* **`FS-09`** — every path written into a durable artifact is relative, carries
  no `.` or `..`, and is validated to stay under its root when read back.
* **`FS-15`** — a path derived from upstream data is validated before anything
  is linked, copied, or written at it (`docs/security.md` T-02).

The division of labour with `hfcache.identity` is deliberate. Identity owns the
grammar of *names*; this module owns the grammar of *paths* and the mapping from
names to locations. A `RepositoryIdentity` validates itself on construction, so
its segments are joined here as-is. The identifier `NewType`s cannot validate
themselves — a `NewType` is a no-op at run time — so this module re-checks them
before they become path segments. That check is unreachable through the type
system and exists for the case where it is bypassed.

Everything here is pure computation. Nothing in this module touches the
filesystem, so it holds before a mount exists and cannot be defeated by a
symlink appearing between a check and a use. Physical containment — proving a
resolved source is a regular file inside an approved cache root — is a
filesystem operation and belongs to Phase 3.
"""

import re
import unicodedata
from dataclasses import dataclass
from datetime import UTC
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, Final, final

from hfcache.errors import CodedError
from hfcache.identity import (
    COMMIT_SHA_LENGTH,
    OPAQUE_ID_LENGTH,
    PROBE_ID_LENGTH,
    CommitSha,
    ProbeId,
    PublicationId,
    RepositoryIdentity,
    RunId,
    TransactionId,
)

if TYPE_CHECKING:
    from collections.abc import Iterable
    from datetime import datetime

__all__ = [
    "MAXIMUM_COMPONENT_BYTES",
    "MAXIMUM_RELATIVE_PATH_BYTES",
    "PUBLISHED_DIRECTORY",
    "SENTINEL_NAME",
    "STORE_DIRECTORY",
    "ArchiveLayout",
    "DirectorySpec",
    "RepositoryLayout",
    "StagingPaths",
    "collision_key",
    "find_path_collisions",
    "parse_archive_relative",
    "parse_repository_relative",
    "resolve_within",
]

SENTINEL_NAME = ".hfcache-root"
STORE_DIRECTORY = ".store"
PUBLISHED_DIRECTORY = "published"

MAXIMUM_COMPONENT_BYTES = 255
"""`NAME_MAX` on every filesystem this archive can live on."""

MAXIMUM_RELATIVE_PATH_BYTES = 1024
"""Cap on a relative path from a repository or a durable artifact.

The longest absolute path this produces is the archive root, plus the deepest
prefix the layout builds (`published/repos/<type>/<org>/<repo>/revisions/<sha>/
<publication-id>/`, under 250 bytes), plus this — which leaves a repository path
far inside `PATH_MAX` even under a deeply nested mount point.
"""

_CONTROL = re.compile(r"[\x00-\x1f\x7f]")
_HEX = re.compile(r"[0-9a-f]+")

_STORE_MODE: Final = 0o700
"""Cache, journals, staging, provenance, and reports are not consumer data."""

_PUBLISHED_MODE: Final = 0o2750
"""Group-traversable and setgid, so the read identity keeps its group (§5.2)."""


def _parse_relative(value: object, *, code: str, what: str) -> PurePosixPath:
    """Validate one relative POSIX path, rejecting anything that could escape.

    The rule this draws the line on: reject what can *escape*, allow what is
    merely awkward. A backslash is rejected because it is a path separator on a
    consumer platform, so `a\\..\\..\\b` would traverse there even though it is
    an ordinary filename here. A trailing space or a name like `CON` is awkward
    on such a platform but cannot escape, so it is left alone — this application
    does not get to decide what a repository may call its files.
    """
    if not isinstance(value, str):
        message = f"{what} must be a string"
        raise CodedError(message, code=code)
    if not value:
        message = f"{what} is empty"
        raise CodedError(message, code=code)
    if value.startswith("/"):
        message = f"invalid {what} {value!r}: must be relative, with no leading '/'"
        raise CodedError(message, code=code)
    if value.endswith("/"):
        message = f"invalid {what} {value!r}: must name a path, not a directory with a trailing '/'"
        raise CodedError(message, code=code)
    if _CONTROL.search(value):
        message = f"invalid {what}: contains a control character or a NUL byte"
        raise CodedError(message, code=code)
    if "\\" in value:
        message = (
            f"invalid {what} {value!r}: contains a backslash, which is a path separator "
            f"on a consumer platform and could traverse there"
        )
        raise CodedError(message, code=code)
    if len(value.encode("utf-8")) > MAXIMUM_RELATIVE_PATH_BYTES:
        message = f"invalid {what}: longer than {MAXIMUM_RELATIVE_PATH_BYTES} bytes"
        raise CodedError(message, code=code)
    for component in value.split("/"):
        if not component:
            message = f"invalid {what} {value!r}: contains an empty path component"
            raise CodedError(message, code=code)
        if component in {".", ".."}:
            message = f"invalid {what} {value!r}: contains a {component!r} component"
            raise CodedError(message, code=code)
        if len(component.encode("utf-8")) > MAXIMUM_COMPONENT_BYTES:
            message = (
                f"invalid {what} {value!r}: component {component[:32]!r}... exceeds "
                f"{MAXIMUM_COMPONENT_BYTES} bytes"
            )
            raise CodedError(message, code=code)
    return PurePosixPath(value)


def parse_repository_relative(value: object, *, code: str) -> PurePosixPath:
    """Validate a path named by upstream repository content.

    `code` is the caller's, because the same malformed path means different
    things at different times: `HFSYN004` while ingesting a Hub tree,
    `HFVER007` when read back out of a manifest.
    """
    return _parse_relative(value, code=code, what="repository-relative path")


def parse_archive_relative(value: object, *, code: str) -> PurePosixPath:
    """Validate a path field read out of a durable artifact (`docs/schemas.md` §1)."""
    return _parse_relative(value, code=code, what="archive-relative path")


def resolve_within(root: Path, value: object, *, code: str) -> Path:
    """Join a relative path onto a root, having proven it cannot leave.

    Containment is established by the grammar rather than re-derived after the
    join: `_parse_relative` accepts no absolute path, no `..` component, and no
    separator that a consumer platform would interpret differently, so the join
    of an accepted value is under `root` by construction. That equivalence is
    the property `tests/unit/test_paths.py` asserts over generated adversarial
    paths, which is a stronger check than an `if` that no input can reach.
    """
    if not root.is_absolute():
        message = f"containment root {root} must be absolute"
        raise ValueError(message)
    return root / _parse_relative(value, code=code, what="relative path")


def collision_key(value: str | PurePosixPath) -> str:
    """Fold a path to the key on which two spellings collide.

    The archive dataset is case-sensitive and does not normalize, so these
    spellings are genuinely distinct here. They are still refused, because a
    consumer copying the tree to APFS or NTFS would silently resolve two
    manifest entries to one file and get a tree that does not match the manifest
    it was verified against (`docs/security.md` T-02).

    The fold is NFC plus `str.casefold`, which is slightly stricter than any one
    filesystem's rule — full case folding also maps a handful of ligatures and
    similar multi-character sequences, so `ﬁle` and `file` are treated as a
    collision even though nothing would actually merge them. That direction is
    deliberate. Refusing a pair of names is visible, explainable, and recoverable
    by the operator; silently publishing a tree in which two manifest entries
    resolve to one file is neither (`AD-16`).

    NFKC is still not applied. It folds far more aggressively than casefold —
    superscripts, width variants, whole compatibility blocks — and would start
    refusing names that no plausible consumer could confuse.
    """
    return unicodedata.normalize("NFC", str(value)).casefold()


def find_path_collisions(
    values: Iterable[str | PurePosixPath],
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    """Group spellings that collide, sorted, for a caller to reject.

    Returns one entry per colliding group: the folded key, and every distinct
    spelling that folded to it. Identical repeated spellings are one group too —
    a manifest listing the same path twice is equally unpublishable.
    """
    groups: dict[str, list[str]] = {}
    for value in values:
        groups.setdefault(collision_key(value), []).append(str(value))
    return tuple(
        (key, tuple(sorted(spellings)))
        for key, spellings in sorted(groups.items())
        if len(spellings) > 1
    )


def _hex_segment(value: str, *, length: int, what: str) -> str:
    """Re-check an identifier that is about to become a path component.

    Defence in depth for the `NewType` identifiers, which carry no run-time
    identity of their own. `hfcache.identity` is where an operator-facing coded
    error comes from; reaching here with a bad value means the type system was
    bypassed, so this raises rather than reporting.
    """
    if not isinstance(value, str) or len(value) != length or not _HEX.fullmatch(value):
        message = f"{what} {value!r} is not {length} lowercase hex characters"
        raise ValueError(message)
    return value


def _sha(value: CommitSha) -> str:
    return _hex_segment(value, length=COMMIT_SHA_LENGTH, what="commit SHA")


def _publication(value: PublicationId) -> str:
    return _hex_segment(value, length=OPAQUE_ID_LENGTH, what="publication id")


def _transaction(value: TransactionId) -> str:
    return _hex_segment(value, length=OPAQUE_ID_LENGTH, what="transaction id")


@final
@dataclass(frozen=True, slots=True)
class DirectorySpec:
    """One directory `archive init` creates, with the mode §5.2 requires."""

    path: Path
    mode: int


@final
@dataclass(frozen=True, slots=True)
class StagingPaths:
    """A tree under construction and the manifest that describes it.

    Trash uses the same shape: a tombstone is the publication it replaced, moved
    wholesale, so recovery reads it back with exactly the layout it was written
    with (`docs/architecture.md` §7.4).
    """

    directory: Path
    tree: Path
    manifest: Path


@final
@dataclass(frozen=True, slots=True)
class RepositoryLayout:
    """Every path one repository owns, across `published/` and `audit/`."""

    archive: ArchiveLayout
    identity: RepositoryIdentity

    @property
    def _key(self) -> tuple[str, str, str]:
        """The `<type>/<org>/<repo>` triple, already proven safe by `identity`."""
        return (self.identity.directory, self.identity.namespace, self.identity.name)

    @property
    def directory(self) -> Path:
        """`published/repos/<type>/<org>/<repo>`."""
        return self.archive.repos.joinpath(*self._key)

    @property
    def refs(self) -> Path:
        """The reference directory a consumer reads."""
        return self.directory / "refs"

    @property
    def current_ref(self) -> Path:
        """`refs/current.json` — the one file a consumer must read."""
        return self.refs / "current.json"

    def revision_ref(self, commit_sha: CommitSha) -> Path:
        """`refs/revisions/<sha>.json` — which instance of this SHA is active."""
        return self.refs / "revisions" / f"{_sha(commit_sha)}.json"

    @property
    def revisions(self) -> Path:
        """The directory holding every retained revision of this repository."""
        return self.directory / "revisions"

    def revision(self, commit_sha: CommitSha) -> Path:
        """Every published instance of one SHA."""
        return self.revisions / _sha(commit_sha)

    def instance(self, commit_sha: CommitSha, publication_id: PublicationId) -> Path:
        """One immutable publication instance directory (`FS-05`)."""
        return self.revision(commit_sha) / _publication(publication_id)

    @property
    def manifests(self) -> Path:
        """`published/manifests/<type>/<org>/<repo>`."""
        return self.archive.manifests.joinpath(*self._key)

    def revision_manifests(self, commit_sha: CommitSha) -> Path:
        """Every manifest written for one SHA, including superseded instances."""
        return self.manifests / _sha(commit_sha)

    def manifest(self, commit_sha: CommitSha, publication_id: PublicationId) -> Path:
        """The immutable manifest for one publication instance (`FS-06`)."""
        return self.revision_manifests(commit_sha) / f"{_publication(publication_id)}.json"

    def tree_reference(self, commit_sha: CommitSha, publication_id: PublicationId) -> PurePosixPath:
        """The `tree` field of a reference: relative to `published/`, not the root."""
        return self.archive.published_relative(self.instance(commit_sha, publication_id))

    def manifest_reference(
        self, commit_sha: CommitSha, publication_id: PublicationId
    ) -> PurePosixPath:
        """The `manifest` field of a reference: relative to `published/`."""
        return self.archive.published_relative(self.manifest(commit_sha, publication_id))

    def manifest_tree_field(
        self, commit_sha: CommitSha, publication_id: PublicationId
    ) -> PurePosixPath:
        """The manifest's own `tree` field, which is archive-relative (§3.1)."""
        return self.archive.archive_relative(self.instance(commit_sha, publication_id))

    def pruned_records(self, commit_sha: CommitSha) -> Path:
        """`audit/pruned/<type>/<org>/<repo>/<sha>` — provenance that outlives the data."""
        return self.archive.pruned_audit.joinpath(*self._key) / _sha(commit_sha)

    def pruned_manifest(self, commit_sha: CommitSha, publication_id: PublicationId) -> Path:
        """The pruned instance's manifest, preserved byte-for-byte."""
        return self.pruned_records(commit_sha) / f"{_publication(publication_id)}.manifest.json"

    def prune_record(self, commit_sha: CommitSha, publication_id: PublicationId) -> Path:
        """Why, when, and under which transaction an instance was pruned."""
        return self.pruned_records(commit_sha) / f"{_publication(publication_id)}.prune.json"

    def repair_records(self, commit_sha: CommitSha) -> Path:
        """`audit/repairs/<type>/<org>/<repo>/<sha>`."""
        return self.archive.repair_audit.joinpath(*self._key) / _sha(commit_sha)

    def retired_manifest(self, commit_sha: CommitSha, publication_id: PublicationId) -> Path:
        """The retired instance's original manifest (`FS-07`)."""
        return self.repair_records(commit_sha) / f"{_publication(publication_id)}.manifest.json"

    def retirement_record(self, commit_sha: CommitSha, publication_id: PublicationId) -> Path:
        """Repair provenance and grace expiry for a retired instance."""
        return self.repair_records(commit_sha) / f"{_publication(publication_id)}.retirement.json"


@final
@dataclass(frozen=True, slots=True)
class ArchiveLayout:
    """Maps the archive root onto every path in `docs/architecture.md` §5.1."""

    root: Path

    def __post_init__(self) -> None:
        """Refuse a root that is not absolute and normalized.

        Configuration already guarantees this (`HFCFG006`), so a failure here is
        a caller that built a root some other way — a programming error, not
        operator input, and therefore not a coded one.
        """
        if not self.root.is_absolute():
            message = f"archive root {self.root} must be an absolute path"
            raise ValueError(message)
        # `Path` drops `.` components as it parses, but keeps `..`, which would
        # make every derived path depend on what the parent directory is now.
        if ".." in self.root.parts:
            message = f"archive root {self.root} must be normalized: no '..' components"
            raise ValueError(message)

    @property
    def sentinel(self) -> Path:
        """`.hfcache-root` — written last, so its existence proves the layout (`FS-23`)."""
        return self.root / SENTINEL_NAME

    @property
    def store(self) -> Path:
        """`.store` — private to the writer, never consumer-visible."""
        return self.root / STORE_DIRECTORY

    @property
    def hub_cache(self) -> Path:
        """The canonical `huggingface_hub` cache (`AD-09`)."""
        return self.store / "hub"

    @property
    def health(self) -> Path:
        """Where preflight write probes are made."""
        return self.store / "health"

    @property
    def quarantine(self) -> Path:
        """Evidence preserved for an operator, never reclaimed automatically."""
        return self.store / "quarantine"

    @property
    def repair_caches(self) -> Path:
        """Transaction-scoped isolated caches (`FS-14`'s single exception)."""
        return self.store / "repair"

    @property
    def staging(self) -> Path:
        """Publication trees under construction, on the same filesystem (`FS-04`)."""
        return self.store / "staging"

    @property
    def transactions(self) -> Path:
        """Durable journals (`FS-17`)."""
        return self.store / "transactions"

    @property
    def trash(self) -> Path:
        """Prune tombstones, held until cleanup commits."""
        return self.store / "trash"

    @property
    def published(self) -> Path:
        """The only consumer-visible subtree, and the root a reference is relative to."""
        return self.root / PUBLISHED_DIRECTORY

    @property
    def repos(self) -> Path:
        """Publication trees and references, by repository."""
        return self.published / "repos"

    @property
    def manifests(self) -> Path:
        """Immutable manifests, by repository and SHA."""
        return self.published / "manifests"

    @property
    def catalog(self) -> Path:
        """Derived indexes, always rebuildable from manifests and refs (`FS-16`)."""
        return self.published / "catalog"

    @property
    def repositories_catalog(self) -> Path:
        """`catalog/repositories.json`."""
        return self.catalog / "repositories.json"

    @property
    def verification_catalog(self) -> Path:
        """`catalog/verification.json`."""
        return self.catalog / "verification.json"

    @property
    def audit(self) -> Path:
        """Provenance that outlives the data it describes."""
        return self.root / "audit"

    @property
    def pruned_audit(self) -> Path:
        """`audit/pruned`."""
        return self.audit / "pruned"

    @property
    def repair_audit(self) -> Path:
        """`audit/repairs`."""
        return self.audit / "repairs"

    @property
    def runs(self) -> Path:
        """One report per invocation of a mutating command."""
        return self.root / "runs"

    def journal(self, transaction_id: TransactionId) -> Path:
        """`.store/transactions/<transaction-id>.json`."""
        return self.transactions / f"{_transaction(transaction_id)}.json"

    def staging_for(self, transaction_id: TransactionId) -> StagingPaths:
        """The staging area one transaction owns (`FS-18`)."""
        directory = self.staging / _transaction(transaction_id)
        return StagingPaths(
            directory=directory, tree=directory / "tree", manifest=directory / "manifest.json"
        )

    def trash_for(self, transaction_id: TransactionId) -> StagingPaths:
        """The tombstone area one prune transaction owns."""
        directory = self.trash / _transaction(transaction_id)
        return StagingPaths(
            directory=directory, tree=directory / "tree", manifest=directory / "manifest.json"
        )

    def quarantine_for(self, transaction_id: TransactionId) -> Path:
        """Where one transaction's preserved evidence goes."""
        return self.quarantine / _transaction(transaction_id)

    def repair_cache_for(self, transaction_id: TransactionId) -> Path:
        """The isolated cache one repair downloads into, never `.store/hub` (`FS-14`)."""
        return self.repair_caches / _transaction(transaction_id) / "hub"

    def probe(self, probe_id: ProbeId) -> Path:
        """One preflight write probe directory."""
        checked = _hex_segment(probe_id, length=PROBE_ID_LENGTH, what="probe id")
        return self.health / f"probe-{checked}"

    def run_report(self, started_at: datetime, run_id: RunId) -> Path:
        """`runs/<YYYYMMDD>T<HHMMSS>Z-<run-id>.json` (`docs/schemas.md` §6).

        The timestamp sorts the directory chronologically for an operator; the
        run id is what makes the name unique, since two runs can start inside
        one second.
        """
        if started_at.tzinfo is None:
            message = "run report timestamps must be timezone-aware; local time is never written"
            raise ValueError(message)
        stamp = started_at.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")
        checked = _hex_segment(run_id, length=OPAQUE_ID_LENGTH, what="run id")
        return self.runs / f"{stamp}-{checked}.json"

    def repository(self, identity: RepositoryIdentity) -> RepositoryLayout:
        """Every path belonging to one repository."""
        return RepositoryLayout(archive=self, identity=identity)

    def archive_relative(self, path: Path) -> PurePosixPath:
        """Express an absolute path in the archive-relative form artifacts record."""
        return self._relative(path, self.root, "archive root")

    def published_relative(self, path: Path) -> PurePosixPath:
        """Express an absolute path relative to `published/`, for a reference.

        A reference is the consumer's contract, and a consumer mounts
        `published/` — so a path relative to the archive root would not resolve
        on the mount it is read from (`docs/schemas.md` §4.1).
        """
        return self._relative(path, self.published, "published root")

    @staticmethod
    def _relative(path: Path, root: Path, what: str) -> PurePosixPath:
        try:
            return PurePosixPath(path.relative_to(root))
        except ValueError as exc:
            message = f"{path} is not inside the {what} {root}"
            raise ValueError(message) from exc

    def resolve(self, value: object, *, code: str) -> Path:
        """Resolve an archive-relative path field read from a durable artifact."""
        return resolve_within(self.root, value, code=code)

    def resolve_published(self, value: object, *, code: str) -> Path:
        """Resolve a `tree` or `manifest` field read from a reference."""
        return resolve_within(self.published, value, code=code)

    def required_directories(self) -> tuple[DirectorySpec, ...]:
        """Every directory `archive init` creates, parents first (`FS-21`).

        Ordered so a single pass creates the tree, and returned with modes so
        initialization reads the layout from here rather than restating §5.2.
        """
        store = [
            self.store,
            self.hub_cache,
            self.health,
            self.quarantine,
            self.repair_caches,
            self.staging,
            self.transactions,
            self.trash,
        ]
        consumer = [self.published, self.repos, self.manifests, self.catalog]
        private = [self.audit, self.pruned_audit, self.repair_audit, self.runs]
        return tuple(
            [DirectorySpec(path=path, mode=_STORE_MODE) for path in store]
            + [DirectorySpec(path=path, mode=_PUBLISHED_MODE) for path in consumer]
            + [DirectorySpec(path=path, mode=_STORE_MODE) for path in private]
        )
