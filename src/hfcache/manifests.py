"""The revision manifest — the archive's evidence about what it holds.

`docs/schemas.md` §3 is the contract. A manifest is immutable once published
(`FS-06`): its expected sizes and digests are never rewritten to match a later
observation, not by `verify`, not by `repair` (`AD-13`, `AD-18`). Everything in
this module exists to make that stance mechanical.

The internal-consistency rules are enforced by the model rather than by whoever
writes one. `file_count` must equal `len(files)`, `total_bytes` must equal the
sum of the sizes, `files` must be sorted byte-wise by path with no two entries
colliding, and `reused_digests` must equal the number of entries that were not
hashed. A manifest that fails any of them is not a weaker manifest — it is one
whose arithmetic does not describe any real tree, so it is refused at both ends:
it cannot be constructed, and it cannot be read back.
"""

from itertools import pairwise
from typing import Annotated, Literal, Self, final

from pydantic import BeforeValidator, model_validator

from hfcache.identity import RepositoryIdentity
from hfcache.models import (
    ArchivePath,
    ByteCount,
    CommitShaField,
    Count,
    DurableModel,
    Generation,
    PublicationIdField,
    RepositoryIdField,
    RepositoryPath,
    RepositoryTypeField,
    Sha256,
    Timestamp,
    TransactionIdField,
    VersionedModel,
    as_tuple,
)
from hfcache.paths import find_path_collisions

__all__ = [
    "DependencyObservation",
    "FileEntry",
    "FileProvenance",
    "HashReuse",
    "RepairProvenance",
    "RevisionManifest",
    "UpstreamIdentifiers",
    "VerificationSummary",
]


@final
class UpstreamIdentifiers(DurableModel):
    """What upstream said about an object's identity.

    Comparison values only. They are recorded because they help explain a
    discrepancy later, never because they substitute for reading the bytes
    (`AD-18`). Each is `null` when the Hub does not supply it.
    """

    git_oid: str | None = None
    lfs_sha256: str | None = None
    xet_hash: str | None = None


@final
class HashReuse(DurableModel):
    """The retained publication whose inode was proven identical."""

    commit_sha: CommitShaField
    publication_id: PublicationIdField


@final
class FileProvenance(DurableModel):
    """How one object's bytes were obtained.

    `hashed = false` is permitted only with a `hash_reused_from` naming a
    retained, already-verified publication proven to be the same physical inode
    at the same size. Every other case must hash, so a digest in a manifest is
    always something this archive computed rather than something it was told.
    """

    cache_root: Literal["canonical", "repair"]
    hash_reused_from: HashReuse | None = None
    hashed: bool
    source: Literal["hub_download", "cache_reuse", "repair_download"]

    @model_validator(mode="after")
    def _check(self) -> Self:
        if self.hashed and self.hash_reused_from is not None:
            message = "hash_reused_from is recorded only when this object was not hashed"
            raise ValueError(message)
        if not self.hashed and self.hash_reused_from is None:
            message = (
                "an unhashed object must name the verified publication whose inode it shares; "
                "without that, nothing in this archive ever read these bytes"
            )
            raise ValueError(message)
        if self.source == "repair_download" and self.cache_root != "repair":
            message = "a repair download comes from the repair cache root (`FS-14`)"
            raise ValueError(message)
        return self


@final
class FileEntry(DurableModel):
    """One published object: where it is, how big, and what it hashes to."""

    path: RepositoryPath
    provenance: FileProvenance
    sha256: Sha256
    size: ByteCount
    upstream: UpstreamIdentifiers


@final
class DependencyObservation(DurableModel):
    """A dependency detected in static metadata, never resolved (`AD-07`).

    Detection reads a fixed set of known metadata files and never executes
    repository content (`AD-15`). Unparseable or ambiguous metadata is recorded
    with `low` confidence rather than guessed at or skipped silently.
    """

    confidence: Literal["high", "medium", "low"]
    declared: bool
    detected_id: str
    managed: bool
    source_field: str
    source_file: RepositoryPath


@final
class VerificationSummary(DurableModel):
    """What ingestion verification actually read (`docs/schemas.md` §3.4)."""

    algorithm: Literal["sha256"] = "sha256"
    completeness_checked: bool
    hashed_bytes: ByteCount
    hashed_objects: Count
    outcome: Literal["verified"]
    reused_digests: Count
    verified_at: Timestamp


@final
class RepairProvenance(DurableModel):
    """Present only when this instance replaces a damaged one (`FS-07`)."""

    reason: str
    repair_of: PublicationIdField
    repair_of_manifest: ArchivePath
    repaired_at: Timestamp
    transaction_id: TransactionIdField


@final
class RevisionManifest(VersionedModel):
    """One immutable publication instance, described completely."""

    application_version: str
    commit_sha: CommitShaField
    dependencies: Annotated[tuple[DependencyObservation, ...], BeforeValidator(as_tuple)] = ()
    download_completed_at: Timestamp
    download_started_at: Timestamp
    file_count: Count
    files: Annotated[tuple[FileEntry, ...], BeforeValidator(as_tuple)]
    first_observed_at: Timestamp
    hub_endpoint: str
    huggingface_hub_version: str
    publication_generation: Generation
    publication_id: PublicationIdField
    publication_mode: Literal["hardlink", "copy"]
    published_at: Timestamp
    python_version: str
    repair: RepairProvenance | None = None
    repository_id: RepositoryIdField
    repository_type: RepositoryTypeField
    requested_revision: str
    total_bytes: ByteCount
    tree: ArchivePath
    verification: VerificationSummary
    verified_at: Timestamp

    @model_validator(mode="after")
    def _check_arithmetic(self) -> Self:
        if self.file_count != len(self.files):
            message = f"file_count {self.file_count} does not equal len(files) {len(self.files)}"
            raise ValueError(message)
        total = sum(entry.size for entry in self.files)
        if self.total_bytes != total:
            message = f"total_bytes {self.total_bytes} does not equal the sum of sizes {total}"
            raise ValueError(message)
        reused = sum(1 for entry in self.files if not entry.provenance.hashed)
        if self.verification.reused_digests != reused:
            message = (
                f"verification.reused_digests {self.verification.reused_digests} does not equal "
                f"the {reused} entries with hashed = false"
            )
            raise ValueError(message)
        return self

    @model_validator(mode="after")
    def _check_paths(self) -> Self:
        paths = [entry.path for entry in self.files]
        if paths != sorted(paths):
            message = "files must be sorted byte-wise ascending by path (`docs/schemas.md` §3.1)"
            raise ValueError(message)
        if collisions := find_path_collisions(paths):
            spellings = ", ".join(repr(spelling) for _, group in collisions for spelling in group)
            message = (
                f"two entries resolve to the same on-disk path: {spellings}. A consumer copying "
                f"this tree to a case-insensitive or normalizing filesystem would hold fewer "
                f"files than the manifest lists"
            )
            raise ValueError(message)
        return self

    @model_validator(mode="after")
    def _check_ordering(self) -> Self:
        expected = sorted(
            self.dependencies,
            key=lambda item: (item.source_file, item.source_field, item.detected_id),
        )
        if list(self.dependencies) != expected:
            message = "dependencies must be sorted by (source_file, source_field, detected_id)"
            raise ValueError(message)
        return self

    @model_validator(mode="after")
    def _check_timeline(self) -> Self:
        # Ordered as the operation runs. `first_observed_at` is excluded: it can
        # predate this manifest by weeks, because it records when the SHA was
        # first seen for this repository, not when this instance was built.
        stages = (
            ("download_started_at", self.download_started_at),
            ("download_completed_at", self.download_completed_at),
            ("verified_at", self.verified_at),
            ("published_at", self.published_at),
        )
        for (earlier_name, earlier), (later_name, later) in pairwise(stages):
            if later < earlier:
                message = f"{later_name} is before {earlier_name}"
                raise ValueError(message)
        if self.first_observed_at > self.download_started_at:
            message = "first_observed_at is after the download it belongs to started"
            raise ValueError(message)
        if self.verification.verified_at != self.verified_at:
            message = "verification.verified_at and verified_at describe the same moment"
            raise ValueError(message)
        return self

    @property
    def identity(self) -> RepositoryIdentity:
        """The repository this manifest describes."""
        return RepositoryIdentity.of(self.repository_type, self.repository_id)

    @property
    def is_repair(self) -> bool:
        """Whether this instance replaces a damaged one."""
        return self.repair is not None
