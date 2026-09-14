"""Durable artifact models and the one serializer every writer goes through.

`docs/schemas.md` is the contract. This module implements §1's conventions once,
so they cannot drift per call site (§11), and §1.1's version rule, which is what
makes rolling a release back safe: an older binary refuses newer state instead of
misreading it.

Three properties hold for every model here:

* `extra="forbid"` — a key this version does not know is an anomaly, reported
  with its location, never quietly dropped on the way through.
* `strict=True` — `"14"` is not a file count. Values come from JSON, which
  already distinguishes a string from an integer, so a type error means the
  writer was wrong rather than the reader being fussy.
* `frozen=True` — a manifest is evidence (`FS-06`). A model that could be
  mutated after loading would make "the manifest says" a statement about
  process state rather than about a file.

Reading is deliberately asymmetric with writing. `dump` takes a validated model
and cannot fail; `load` takes bytes from a filesystem that may have been
corrupted, truncated, or written by another version, and reports every problem
it finds at once with the caller's error code, because an operator should fix one
file once rather than one field per run.
"""

import json
from datetime import UTC, datetime
from typing import Annotated, Any, Literal, Self, final

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    PlainSerializer,
    ValidationError,
    model_validator,
)

from hfcache.errors import HfcacheError, Problem
from hfcache.identity import (
    RepositoryIdentity,
    parse_commit_sha,
    parse_publication_id,
    parse_repository_id,
    parse_repository_type,
    parse_run_id,
    parse_transaction_id,
)
from hfcache.paths import parse_archive_relative, parse_repository_relative

__all__ = [
    "INDENT",
    "LAYOUT_VERSION",
    "SCHEMA_VERSION",
    "ArchivePath",
    "ArchiveSentinel",
    "ByteCount",
    "Checkpoint",
    "CommitShaField",
    "Count",
    "DurableModel",
    "Generation",
    "Provenance",
    "PrunePlan",
    "PruneSelection",
    "PrunedRevisionRecord",
    "PublicationIdField",
    "PublishedPath",
    "PurgePlan",
    "Reference",
    "RepairCleanup",
    "RepairRetirementRecord",
    "RepositoryIdField",
    "RepositoryPath",
    "RepositoryTypeField",
    "RevisionSummary",
    "RunIdField",
    "Sha256",
    "Timestamp",
    "TransactionError",
    "TransactionIdField",
    "TransactionJournal",
    "VersionedModel",
    "as_tuple",
    "dump",
    "format_timestamp",
    "load",
    "parse_timestamp",
    "serialize",
]

SCHEMA_VERSION = 1
"""Every durable format in `docs/schemas.md` begins at 1 and moves together."""

LAYOUT_VERSION = 1
"""Version of the directory layout in `docs/architecture.md` §5.1."""

INDENT = 2
"""Durable files are indented; the `--json` envelope is not (`docs/cli.md` §4).

A manifest can list thousands of files and is read by operators and diffed
during an incident. The envelope is one machine-read line on a pipe. Both go
through `serialize`, so sorting, encoding, and the trailing newline cannot
differ between them.
"""


def serialize(payload: object, *, indent: int | None = INDENT) -> str:
    """Render a JSON payload in the one form this application ever writes.

    Sorted keys, `(",", ": ")` separators, `ensure_ascii=False`, and a single
    trailing newline (`docs/schemas.md` §1). Identical logical content produces
    byte-identical output, which is what lets a golden fixture detect a
    serialization change that no `schema_version` bump accounted for.
    """
    body = json.dumps(
        payload,
        indent=indent,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ": "),
        allow_nan=False,
    )
    return f"{body}\n"


def format_timestamp(value: datetime) -> str:
    """Render an aware datetime as RFC 3339 UTC with a literal `Z`.

    Microsecond precision always, so two timestamps written a moment apart sort
    correctly as strings and every timestamp field has the same width.
    """
    if value.tzinfo is None:
        message = "timestamps must be timezone-aware; local time is never written"
        raise ValueError(message)
    return value.astimezone(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


def parse_timestamp(value: object) -> datetime:
    """Accept the durable timestamp form, or an aware datetime."""
    if isinstance(value, datetime):
        if value.tzinfo is None:
            message = "timestamps must be timezone-aware; local time is never written"
            raise ValueError(message)
        return value.astimezone(UTC)
    if not isinstance(value, str):
        # ValueError, not TypeError: Pydantic converts ValueError and
        # AssertionError into validation errors and lets anything else escape,
        # so a TypeError here would leave `load` reporting a bare exception
        # instead of a coded problem naming the field.
        message = f"timestamp must be a string, not {type(value).__name__}"
        raise ValueError(message)  # noqa: TRY004 - Pydantic only collects ValueError
    if not value.endswith("Z"):
        message = f"timestamp {value!r} must be UTC with a literal 'Z'"
        raise ValueError(message)
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        message = f"timestamp {value!r} is not RFC 3339"
        raise ValueError(message) from exc
    if parsed.tzinfo is None:  # pragma: no cover - a trailing 'Z' always sets it
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _parse_sha256(value: object) -> str:
    if not isinstance(value, str):
        message = f"digest must be a string, not {type(value).__name__}"
        raise ValueError(message)  # noqa: TRY004 - Pydantic only collects ValueError
    if len(value) != 64 or not all(character in "0123456789abcdef" for character in value):  # noqa: PLR2004 - a sha256 is 64 hex characters
        message = f"digest {value!r} must be 64 lowercase hex characters"
        raise ValueError(message)
    return value


def _archive_path(value: object) -> str:
    return str(parse_archive_relative(value))


def _repository_path(value: object) -> str:
    return str(parse_repository_relative(value))


def as_tuple(value: object) -> object:
    """Accept a JSON array for a tuple field.

    Strict mode will not turn a `list` into a `tuple`, and JSON arrays decode to
    lists. The fields stay tuples because a frozen model holding a mutable list
    is not actually immutable.
    """
    if isinstance(value, list):
        return tuple(value)
    return value


Timestamp = Annotated[
    datetime,
    BeforeValidator(parse_timestamp),
    PlainSerializer(format_timestamp, return_type=str, when_used="json"),
]
Sha256 = Annotated[str, BeforeValidator(_parse_sha256)]
CommitShaField = Annotated[str, BeforeValidator(parse_commit_sha)]
PublicationIdField = Annotated[str, BeforeValidator(parse_publication_id)]
TransactionIdField = Annotated[str, BeforeValidator(parse_transaction_id)]
RunIdField = Annotated[str, BeforeValidator(parse_run_id)]
RepositoryIdField = Annotated[str, BeforeValidator(parse_repository_id)]
RepositoryTypeField = Annotated[Literal["model", "dataset"], BeforeValidator(parse_repository_type)]

ArchivePath = Annotated[str, BeforeValidator(_archive_path)]
"""A path field relative to the archive root — everything except a reference."""

PublishedPath = Annotated[str, BeforeValidator(_archive_path)]
"""A reference's `tree` or `manifest`, relative to `published/`.

Structurally identical to `ArchivePath`; distinct because the base differs and
`docs/schemas.md` §4.1 is the only place it does. Naming the difference in the
type is what stops a writer from joining one onto the wrong root.
"""

RepositoryPath = Annotated[str, BeforeValidator(_repository_path)]
"""A path inside a repository, as upstream spelled it (`docs/architecture.md` §5.3)."""

ByteCount = Annotated[int, Field(ge=0)]
Count = Annotated[int, Field(ge=0)]
Generation = Annotated[int, Field(ge=1)]


class DurableModel(BaseModel):
    """Base for every durable artifact: no unknown keys, no coercion, immutable."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    def to_payload(self) -> dict[str, Any]:
        """Render as the JSON-compatible mapping that gets written."""
        return self.model_dump(mode="json")

    def to_json(self, *, indent: int | None = INDENT) -> str:
        """Render as the exact text this artifact is stored as."""
        return serialize(self.to_payload(), indent=indent)


class VersionedModel(DurableModel):
    """A durable artifact carrying its own `schema_version` (`docs/schemas.md` §1.1)."""

    schema_version: int = SCHEMA_VERSION

    @model_validator(mode="after")
    def _check_schema_version(self) -> Self:
        if self.schema_version != SCHEMA_VERSION:
            message = (
                f"schema_version {self.schema_version} is not {SCHEMA_VERSION}, "
                f"which is the only version this release writes"
            )
            raise ValueError(message)
        return self


def dump(model: DurableModel, *, indent: int | None = INDENT) -> bytes:
    """Render a validated model as the bytes to write.

    UTF-8 with no BOM. The caller writes these to a temporary sibling, fsyncs,
    renames, and fsyncs the parent (`docs/schemas.md` §1) — this function has no
    opinion about where they go and never touches the filesystem.
    """
    return model.to_json(indent=indent).encode("utf-8")


def _location(loc: tuple[int | str, ...]) -> str:
    parts: list[str] = []
    for item in loc:
        if isinstance(item, int):
            parts.append(f"[{item}]")
        elif parts:
            parts.append(f".{item}")
        else:
            parts.append(str(item))
    return "".join(parts) or "<root>"


def _problems(exc: ValidationError, *, code: str, location: str | None) -> list[Problem]:
    """Turn every validation failure into one problem carrying the artifact's code.

    The code names the *artifact* — `HFVER007` for a manifest, `HFTXN001` for a
    journal — and the location names the field. That division is why the field
    validators in `hfcache.paths` and `hfcache.identity` do not need to know
    which artifact is being read.
    """

    def where(loc: tuple[int | str, ...]) -> str:
        field = _location(loc)
        return f"{location}:{field}" if location else field

    problems = [
        Problem(code=code, message=error["msg"], location=where(error["loc"]))
        for error in exc.errors()
    ]
    problems.sort(key=lambda problem: problem.location or "")
    return problems


def _declared_version(
    payload: object, *, error: type[HfcacheError], code: str, location: str | None
) -> int:
    """Read `schema_version` before anything else, so §1.1 can be applied first."""
    if not isinstance(payload, dict):
        message = "a durable artifact is a JSON object"
        raise error.single(message, code=code, location=location)
    version = payload.get("schema_version")
    if not isinstance(version, int) or isinstance(version, bool):
        message = "schema_version is missing or is not an integer"
        raise error.single(message, code=code, location=location)
    return version


def load[ModelT: VersionedModel](
    model_type: type[ModelT],
    raw: bytes | str,
    *,
    error: type[HfcacheError],
    code: str,
    location: str | None = None,
) -> ModelT:
    """Read, version-check, and validate one durable artifact.

    `error` and `code` are the caller's, because the same malformed file means
    different things depending on which artifact it is: a bad manifest is
    `HFVER007` and exits `40`, a bad journal is `HFTXN001` and exits `20`.

    A file whose `schema_version` is *greater* than this release's is refused
    without being read further (`docs/schemas.md` §1.1, `AD-16`). That refusal is
    what makes a rollback safe: an older binary that guessed at newer state could
    corrupt it, and one that stops cannot.
    """
    try:
        text = raw.decode("utf-8") if isinstance(raw, bytes) else raw
    except UnicodeDecodeError as exc:
        message = "not valid UTF-8"
        raise error.single(message, code=code, location=location) from exc
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        message = f"not valid JSON: {exc.msg} at line {exc.lineno} column {exc.colno}"
        raise error.single(message, code=code, location=location) from exc

    version = _declared_version(payload, error=error, code=code, location=location)
    if version > SCHEMA_VERSION:
        message = (
            f"schema_version {version} is newer than {SCHEMA_VERSION}, which is what this "
            f"release understands; refusing to read it rather than guess at its meaning"
        )
        raise error.single(message, code=code, location=location)
    if version < SCHEMA_VERSION:
        message = (
            f"schema_version {version} is older than {SCHEMA_VERSION} and no migration exists; "
            f"this release is the first, so such a file was not written by it"
        )
        raise error.single(message, code=code, location=location)

    try:
        return model_type.model_validate(payload)
    except ValidationError as exc:
        raise error(_problems(exc, code=code, location=location)) from exc


# --------------------------------------------------------------------------- #
# §2 Archive sentinel
# --------------------------------------------------------------------------- #


@final
class Provenance(DurableModel):
    """Which build of the application produced an artifact."""

    application_version: str
    hostname: str


@final
class ArchiveSentinel(VersionedModel):
    """`.hfcache-root` — the interlock against writing to the wrong mount.

    Written once by `archive init`, last in the sequence (`FS-23`), and never
    rewritten. A mismatch between `archive_id` and `storage.archive_id` is fatal
    and is never repaired, regenerated, or ignored (`FS-03`).
    """

    archive_id: str
    created_at: Timestamp
    created_by: Provenance
    layout_version: int = LAYOUT_VERSION

    @model_validator(mode="after")
    def _check(self) -> Self:
        if self.layout_version != LAYOUT_VERSION:
            message = (
                f"layout_version {self.layout_version} is not {LAYOUT_VERSION}; this archive "
                f"was created by a release with a different directory layout"
            )
            raise ValueError(message)
        return self


# --------------------------------------------------------------------------- #
# §4 References
# --------------------------------------------------------------------------- #


@final
class Reference(VersionedModel):
    """`refs/current.json` and `refs/revisions/<sha>.json` (`FS-08`).

    The only durable artifact whose paths are relative to `published/` rather
    than to the archive root, because a consumer mounts `published/` and joins
    these onto it directly (`docs/schemas.md` §4.1).
    """

    commit_sha: CommitShaField
    manifest: PublishedPath
    publication_generation: Generation
    publication_id: PublicationIdField
    repository_id: RepositoryIdField
    repository_type: RepositoryTypeField
    tree: PublishedPath
    updated_at: Timestamp

    @property
    def identity(self) -> RepositoryIdentity:
        """The repository this reference belongs to."""
        return RepositoryIdentity.of(self.repository_type, self.repository_id)


# --------------------------------------------------------------------------- #
# §8 Prune plan
# --------------------------------------------------------------------------- #


@final
class RevisionSummary(DurableModel):
    """A `(commit_sha, publication_generation)` pair, the retention ordering key."""

    commit_sha: CommitShaField
    publication_generation: Generation


@final
class PruneSelection(DurableModel):
    """The one instance a prune plan proposes to remove."""

    commit_sha: CommitShaField
    file_count: Count
    logical_bytes: ByteCount
    manifest: ArchivePath
    publication_generation: Generation
    publication_id: PublicationIdField
    tree: ArchivePath


@final
class PrunePlan(VersionedModel):
    """`prune --dry-run` output, persisted before any mutation (`docs/schemas.md` §8).

    The validity rules are enforced here rather than at the call site: a plan is
    valid only if `selected` is the lowest generation in `retained`, is not
    `current`, and `retained` exceeds the retention limit. A plan that fails any
    of them is refused and every revision stays (`AD-04`, `AD-05`).
    """

    cache_revisions_to_delete: Annotated[tuple[CommitShaField, ...], BeforeValidator(as_tuple)]
    current: RevisionSummary
    generated_at: Timestamp
    plan_id: PublicationIdField
    reason: Literal["sixth_unique_revision_published"]
    repository_id: RepositoryIdField
    repository_type: RepositoryTypeField
    retained: Annotated[tuple[RevisionSummary, ...], BeforeValidator(as_tuple)]
    selected: PruneSelection
    unique_bytes_released_estimate: ByteCount

    @model_validator(mode="after")
    def _check(self) -> Self:
        generations = [revision.publication_generation for revision in self.retained]
        if len(set(generations)) != len(generations):
            message = "retained revisions must have distinct publication generations (`FS-20`)"
            raise ValueError(message)
        if self.selected.publication_generation != min(generations, default=0):
            message = (
                f"selected generation {self.selected.publication_generation} is not the lowest "
                f"retained generation; retention order comes from the generation, never from time"
            )
            raise ValueError(message)
        if self.selected.commit_sha == self.current.commit_sha:
            message = "the current revision is never selected for pruning"
            raise ValueError(message)
        return self


@final
class PurgePlan(VersionedModel):
    """One unmanaged repository an operator explicitly chose to remove.

    Unlike a retention prune, purge removes every retained revision together.
    The tuple is ordered by immutable publication generation and names every
    active tree and manifest the transaction is allowed to tombstone (`FS-19`).
    """

    cache_revisions_to_delete: Annotated[tuple[CommitShaField, ...], BeforeValidator(as_tuple)]
    current: RevisionSummary
    generated_at: Timestamp
    plan_id: PublicationIdField
    reason: Literal["operator_requested_repository_purge"]
    repository_id: RepositoryIdField
    repository_type: RepositoryTypeField
    revisions: Annotated[tuple[PruneSelection, ...], BeforeValidator(as_tuple)]
    unique_bytes_released_estimate: ByteCount

    @model_validator(mode="after")
    def _check(self) -> Self:
        if not self.revisions:
            message = "a purge plan must name at least one retained revision"
            raise ValueError(message)
        generations = [revision.publication_generation for revision in self.revisions]
        if generations != sorted(generations) or len(set(generations)) != len(generations):
            message = (
                "purge revisions must be ordered by distinct publication generations (`FS-20`)"
            )
            raise ValueError(message)
        commits = tuple(revision.commit_sha for revision in self.revisions)
        if len(set(commits)) != len(commits):
            message = "purge revisions must name distinct commit SHAs"
            raise ValueError(message)
        if self.cache_revisions_to_delete != commits:
            message = "cache revisions must exactly match the ordered purge revisions"
            raise ValueError(message)
        current = [
            revision
            for revision in self.revisions
            if revision.commit_sha == self.current.commit_sha
        ]
        if len(current) != 1:
            message = "purge revisions must contain the current revision exactly once"
            raise ValueError(message)
        if current[0].publication_generation != self.current.publication_generation:
            message = "purge current revision generation does not match its selected revision"
            raise ValueError(message)
        if self.unique_bytes_released_estimate != sum(
            revision.logical_bytes for revision in self.revisions
        ):
            message = "purge logical-byte estimate must equal the selected revisions"
            raise ValueError(message)
        return self


# --------------------------------------------------------------------------- #
# §9 Audit records
# --------------------------------------------------------------------------- #


@final
class PrunedRevisionRecord(VersionedModel):
    """What remains of a revision after its bytes are gone (`docs/schemas.md` §9.1).

    Written beside the pruned instance's original manifest, preserved
    byte-for-byte. Together they prove what was there and why it went.
    """

    commit_sha: CommitShaField
    file_count: Count
    logical_bytes: ByteCount
    manifest_archived_at: Timestamp
    plan_id: PublicationIdField
    publication_generation: Generation
    publication_id: PublicationIdField
    pruned_at: Timestamp
    reason: Literal["sixth_unique_revision_published", "operator_requested_repository_purge"]
    repository_id: RepositoryIdField
    repository_type: RepositoryTypeField
    retained_after: Annotated[tuple[RevisionSummary, ...], BeforeValidator(as_tuple)]
    transaction_id: TransactionIdField
    tree: ArchivePath


@final
class RepairCleanup(DurableModel):
    """Whether a retired instance's tree has been moved to quarantine yet."""

    completed_at: Timestamp | None = None
    quarantine_path: ArchivePath | None = None
    state: Literal["pending", "completed"] = "pending"

    @model_validator(mode="after")
    def _check(self) -> Self:
        completed = self.state == "completed"
        if completed != (self.completed_at is not None):
            message = "cleanup state and completed_at must agree"
            raise ValueError(message)
        return self


@final
class RepairRetirementRecord(VersionedModel):
    """Why an instance was replaced, and when its grace expires (§9.2).

    The retired tree and its manifest stay at their original locators until
    `grace_expires_at` so an in-flight consumer copy can finish (`AD-13`).
    """

    cleanup: RepairCleanup
    commit_sha: CommitShaField
    evidence: Annotated[tuple[str, ...], BeforeValidator(as_tuple)]
    grace_expires_at: Timestamp
    publication_generation: Generation
    reason: str
    replacement_publication_id: PublicationIdField
    replacement_tree: ArchivePath
    repository_id: RepositoryIdField
    repository_type: RepositoryTypeField
    retired_at: Timestamp
    retired_publication_id: PublicationIdField
    retired_tree: ArchivePath
    transaction_id: TransactionIdField

    @model_validator(mode="after")
    def _check(self) -> Self:
        if self.grace_expires_at <= self.retired_at:
            message = "grace_expires_at must be after retired_at"
            raise ValueError(message)
        if self.replacement_publication_id == self.retired_publication_id:
            message = "a repair replaces an instance with a new publication id (`FS-07`)"
            raise ValueError(message)
        return self


# --------------------------------------------------------------------------- #
# §10 Transaction journal
# --------------------------------------------------------------------------- #


@final
class Checkpoint(DurableModel):
    """One durable boundary that has already been crossed.

    Evidence is re-observable fact — an archive-relative path, a digest, a count
    — never an intention. That is what lets recovery read the filesystem and
    decide, rather than replay what a dead process meant to do (`AD-14`).
    """

    evidence: dict[str, Any] = Field(default_factory=dict)
    name: str
    recorded_at: Timestamp
    sequence: Annotated[int, Field(ge=1)]


@final
class TransactionError(DurableModel):
    """A compact record of why a transaction failed. Redacted of any secret."""

    at: Timestamp
    code: str
    message: str


@final
class TransactionJournal(VersionedModel):
    """`.store/transactions/<transaction-id>.json` (`FS-17`).

    Records what has already happened and is durable, never what the process
    intends to do. Checkpoints are append-only with strictly increasing
    sequence, and re-recording one whose evidence already holds is a no-op —
    which is what lets `recover --apply` run repeatedly without harm.
    """

    archive_id: str
    checkpoints: Annotated[tuple[Checkpoint, ...], BeforeValidator(as_tuple)] = ()
    commit_sha: CommitShaField | None = None
    completed_at: Timestamp | None = None
    config_fingerprint: str
    created_at: Timestamp
    error: TransactionError | None = None
    last_checkpoint_at: Timestamp | None = None
    operation: Literal["sync", "publication", "prune", "repair", "recovery"]
    publication_id: PublicationIdField | None = None
    repository_id: RepositoryIdField | None = None
    repository_type: RepositoryTypeField | None = None
    run_id: RunIdField
    state: Literal["open", "committed", "failed", "needs_operator"]
    transaction_id: TransactionIdField

    @model_validator(mode="after")
    def _check(self) -> Self:
        sequences = [checkpoint.sequence for checkpoint in self.checkpoints]
        if sequences != list(range(1, len(sequences) + 1)):
            message = (
                "checkpoint sequences must start at 1 and increase by one; a gap or a repeat "
                "is a combination no valid execution produces (`HFTXN002`)"
            )
            raise ValueError(message)
        if (self.last_checkpoint_at is None) != (not self.checkpoints):
            message = "last_checkpoint_at is set exactly when at least one checkpoint exists"
            raise ValueError(message)
        if (self.state == "open") and self.completed_at is not None:
            message = "an open transaction has no completed_at"
            raise ValueError(message)
        if (self.repository_id is None) != (self.repository_type is None):
            message = "repository_id and repository_type are set together or not at all"
            raise ValueError(message)
        return self

    @property
    def is_resolved(self) -> bool:
        """Whether recovery can leave this journal alone."""
        return self.state in {"committed", "failed"}
