"""Bounded adjunct reads and independent atomic writer units (INV-018, schemas §17)."""

import hashlib
import json
import os
import re
import stat
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from pydantic import ValidationError

from hfcache.catalog_cards import validate_card_presentation
from hfcache.catalog_extractors import ExtractionBudget
from hfcache.catalog_models import (
    MAXIMUM_CARD_RECORD_BYTES,
    MAXIMUM_CARD_SOURCE_BYTES,
    MAXIMUM_RECORD_BYTES,
    CatalogRecord,
    PublicationObservation,
    RepositoryCard,
    RepositoryTagSnapshot,
)
from hfcache.catalog_parsing import ExtractionError
from hfcache.errors import IntegrityError, SafetyError
from hfcache.identity import CommitSha, PublicationId, RepositoryIdentity, TransactionId
from hfcache.locking import require_archive_lock
from hfcache.manifests import RevisionManifest
from hfcache.metadata import MetadataReader, QueryBounds, QueryLimitError
from hfcache.models import (
    ArchiveSentinel,
    Reference,
    RepairRetirementRecord,
    TransactionJournal,
    VersionedModel,
    dump,
    load,
)
from hfcache.preflight import CHECK_ORDER, require_storage_safety
from hfcache.publication import PUBLISHED_DIRECTORY_MODE, PUBLISHED_FILE_MODE
from hfcache.storage import atomic_write_bytes
from hfcache.transactions import checkpoint_order_problems

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from hfcache.config import StorageConfig
    from hfcache.paths import ArchiveLayout
    from hfcache.preflight import Check
    from hfcache.storage import MountEntry

RECORD_BOUNDS = QueryBounds(
    maximum_entries=100_000,
    maximum_artifact_bytes=MAXIMUM_RECORD_BYTES,
    maximum_total_bytes=128 * 1024 * 1024,
)
MAXIMUM_JSON_DEPTH = 32
MAXIMUM_JSON_NODES = 100_000
_JSON_STRUCTURE = re.compile(rb'[\[\]{},:"]')
_JSON_BACKSLASH = ord("\\")
_MINIMUM_CACHED_MANIFEST_BYTES = 64 * 1024
_MAXIMUM_CACHED_MANIFEST_BYTES = 8 * 1024 * 1024
_MAXIMUM_CACHED_REFERENCE_BYTES = 4 * 1024


def _invalid() -> IntegrityError:
    return IntegrityError.single(
        "supplemental metadata is unsafe, corrupt or incompatible", code="HFVER007"
    )


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            msg = "duplicate metadata JSON key"
            raise ValueError(msg)
        result[key] = value
    return result


def _constant(_: str) -> None:
    msg = "nonfinite metadata JSON value"
    raise ValueError(msg)


def _json_structure(raw: bytes) -> None:
    """Bound structure before JSON allocates nested containers, counting skipped content too."""
    depth = tokens = position = 0
    while match := _JSON_STRUCTURE.search(raw, position):
        character = match[0]
        position = match.end()
        if character == b'"':
            while True:
                quote = raw.find(b'"', position)
                if quote < 0:
                    return  # The normal JSON parser rejects an unterminated string.
                backslashes = quote
                while backslashes > position and raw[backslashes - 1] == _JSON_BACKSLASH:
                    backslashes -= 1
                position = quote + 1
                if (quote - backslashes) % 2 == 0:
                    break
        elif character in (b"[", b"{"):
            depth += 1
            tokens += 1
        elif character in (b"]", b"}"):
            depth -= 1
        else:
            tokens += 1  # A comma or colon outside a quoted string.
        if depth > MAXIMUM_JSON_DEPTH or tokens > MAXIMUM_JSON_NODES:
            raise _invalid()


def parse_record[RecordT: CatalogRecord](model: type[RecordT], raw: bytes) -> RecordT:
    """Reject ambiguous JSON locally, without widening or rewriting old evidence formats."""
    maximum = MAXIMUM_CARD_RECORD_BYTES if model is RepositoryCard else MAXIMUM_RECORD_BYTES
    if len(raw) > maximum:
        raise _invalid()
    _json_structure(raw)
    try:
        payload = json.loads(
            raw.decode("utf-8"), object_pairs_hook=_pairs, parse_constant=_constant
        )
        pending = [(payload, 0)]
        nodes = 0
        while pending:
            value, depth = pending.pop()
            nodes += 1
            if depth > MAXIMUM_JSON_DEPTH or nodes > MAXIMUM_JSON_NODES:
                raise _invalid()
            if isinstance(value, dict):
                pending.extend((item, depth + 1) for item in value.values())
            elif isinstance(value, list):
                pending.extend((item, depth + 1) for item in value)
        if (
            not isinstance(payload, dict)
            or type(payload.get("schema_version")) is not int
            or payload["schema_version"] != 1
        ):
            raise _invalid()
        record = model.model_validate(payload)
        if record.to_payload() != payload or len(dump(record)) > maximum:
            raise _invalid()
    except (UnicodeError, ValueError, RecursionError, ValidationError) as exc:
        raise _invalid() from exc
    else:
        return record


def check_namespace(layout: ArchiveLayout, reader: MetadataReader) -> None:
    try:
        for entry in reader.walk(layout.metadata):
            kind = layout.supplemental_entry_kind(entry.path)
            if not (
                (kind == "directory" and stat.S_ISDIR(entry.info.st_mode))
                or (kind == "file" and stat.S_ISREG(entry.info.st_mode))
            ):
                raise _invalid()
    except (OSError, ValueError) as exc:
        raise _invalid() from exc


def _optional[RecordT: CatalogRecord](
    path: Path, model: type[RecordT], reader: MetadataReader
) -> RecordT | None:
    try:
        maximum = MAXIMUM_CARD_RECORD_BYTES if model is RepositoryCard else MAXIMUM_RECORD_BYTES
        raw = reader.read(path, maximum_bytes=maximum)
    except FileNotFoundError:
        return None
    except (OSError, ValueError) as exc:
        raise _invalid() from exc
    return parse_record(model, raw)


def read_tag_snapshot(
    layout: ArchiveLayout,
    identity: RepositoryIdentity,
    archive_id: str,
    *,
    reader: MetadataReader | None = None,
) -> RepositoryTagSnapshot | None:
    reader = reader or MetadataReader(layout.root, RECORD_BOUNDS)
    record = _optional(layout.repository(identity).tag_snapshot, RepositoryTagSnapshot, reader)
    if record is not None and (record.archive_id, record.repository_type, record.repository_id) != (
        archive_id,
        identity.type,
        identity.id,
    ):
        raise _invalid()
    return record


def _uncached_authority[ModelT: VersionedModel](model: type[ModelT], raw: bytes) -> ModelT:
    _json_structure(raw)
    return load(model, raw, error=IntegrityError, code="HFVER007")


@lru_cache(maxsize=1)
def _cached_manifest(raw: bytes, _structural_limits: tuple[int, int]) -> RevisionManifest:
    """Memoize frozen parsing only; the caller has already charged a fresh read."""
    if not _MINIMUM_CACHED_MANIFEST_BYTES <= len(raw) <= _MAXIMUM_CACHED_MANIFEST_BYTES:
        raise _invalid()
    return _uncached_authority(RevisionManifest, raw)


@lru_cache(maxsize=512)
def _cached_reference(raw: bytes, _structural_limits: tuple[int, int]) -> Reference:
    if len(raw) > _MAXIMUM_CACHED_REFERENCE_BYTES:
        raise _invalid()
    return _uncached_authority(Reference, raw)


def _parse_authority[ModelT: VersionedModel](model: type[ModelT], raw: bytes) -> ModelT:
    # Decision157 / INV-018: limits are part of each key so a changed ceiling cannot reuse
    # an earlier result. Model families have separate bounded caches; mutable
    # journal/operation records and small scan manifests remain uncached.
    limits = MAXIMUM_JSON_DEPTH, MAXIMUM_JSON_NODES
    if (
        model is RevisionManifest
        and _MINIMUM_CACHED_MANIFEST_BYTES <= len(raw) <= _MAXIMUM_CACHED_MANIFEST_BYTES
    ):
        return cast("ModelT", _cached_manifest(raw, limits))
    if model is Reference and len(raw) <= _MAXIMUM_CACHED_REFERENCE_BYTES:
        return cast("ModelT", _cached_reference(raw, limits))
    return _uncached_authority(model, raw)


def read_authority[ModelT: VersionedModel](
    path: Path,
    model: type[ModelT],
    reader: MetadataReader,
    *,
    missing_ok: bool = False,
) -> tuple[ModelT, str]:
    try:
        raw = reader.read(path, maximum_bytes=MAXIMUM_RECORD_BYTES)
        value = _parse_authority(model, raw)
    except FileNotFoundError as exc:
        if missing_ok:
            raise
        raise _invalid() from exc
    except (OSError, ValueError, RecursionError) as exc:
        raise _invalid() from exc
    return value, hashlib.sha256(raw).hexdigest()


def publication_binding(
    layout: ArchiveLayout,
    identity: RepositoryIdentity,
    sha: CommitSha,
    publication: PublicationId,
    *,
    reader: MetadataReader,
) -> tuple[RevisionManifest, str]:
    """Read canonical authoritative metadata only, never tree payloads or confidence."""
    repository = layout.repository(identity)
    reference, _ = read_authority(repository.revision_ref(sha), Reference, reader)
    if (
        reference.identity != identity
        or reference.commit_sha != sha
        or reference.publication_id != publication
        or reference.tree != str(repository.tree_reference(sha, publication))
        or reference.manifest != str(repository.manifest_reference(sha, publication))
    ):
        raise _invalid()
    manifest, digest = read_authority(
        repository.manifest(sha, publication), RevisionManifest, reader
    )
    if (
        manifest.identity != identity
        or manifest.commit_sha != sha
        or manifest.publication_id != publication
        or manifest.publication_generation != reference.publication_generation
        or manifest.tree != str(repository.manifest_tree_field(sha, publication))
    ):
        raise _invalid()
    return manifest, digest


def _bind(
    record: PublicationObservation, layout: ArchiveLayout, archive_id: str, reader: MetadataReader
) -> None:
    identity = RepositoryIdentity.of(record.repository_type, record.repository_id)
    sha, publication = CommitSha(record.commit_sha), PublicationId(record.publication_id)
    manifest, digest = publication_binding(layout, identity, sha, publication, reader=reader)
    if (
        record.archive_id != archive_id
        or record.manifest_digest != digest
        or record.publication_generation != manifest.publication_generation
        or record.manifest_path
        != str(layout.archive_relative(layout.repository(identity).manifest(sha, publication)))
    ):
        raise _invalid()
    files = {file.path: file for file in manifest.files}
    for source in record.sources:
        if source.path not in files or source.sha256 != files[source.path].sha256:
            raise _invalid()
    for variant in record.variants:
        if any(path not in files for path in variant.source_paths):
            raise _invalid()
        for member in variant.members:
            if member.path not in files or member.size_bytes != files[member.path].size:
                raise _invalid()


def read_publication_observation(  # noqa: PLR0913 - exact publication and archive identities
    layout: ArchiveLayout,
    identity: RepositoryIdentity,
    sha: CommitSha,
    publication: PublicationId,
    archive_id: str,
    *,
    reader: MetadataReader | None = None,
) -> PublicationObservation | None:
    reader = reader or MetadataReader(layout.root, RECORD_BOUNDS)
    record = _optional(
        layout.repository(identity).observation(sha, publication), PublicationObservation, reader
    )
    if record is not None:
        if (
            record.repository_type,
            record.repository_id,
            record.commit_sha,
            record.publication_id,
        ) != (identity.type, identity.id, sha, publication):
            raise _invalid()
        _bind(record, layout, archive_id, reader)
    return record


def _bind_card(
    record: RepositoryCard,
    layout: ArchiveLayout,
    archive_id: str,
    reader: MetadataReader,
    card_budget: ExtractionBudget,
) -> None:
    identity = RepositoryIdentity.of(record.repository_type, record.repository_id)
    sha, publication = CommitSha(record.commit_sha), PublicationId(record.publication_id)
    manifest, digest = publication_binding(layout, identity, sha, publication, reader=reader)
    if (
        record.archive_id != archive_id
        or record.manifest_digest != digest
        or record.publication_generation != manifest.publication_generation
        or record.manifest_path
        != str(layout.archive_relative(layout.repository(identity).manifest(sha, publication)))
    ):
        raise _invalid()
    source = next((entry for entry in manifest.files if entry.path == "README.md"), None)
    if source is None:
        if record.state != "absent":
            raise _invalid()
    elif (
        record.state == "absent"
        or record.expected_source_sha256 != source.sha256
        or (record.state == "present" and source.size > MAXIMUM_CARD_SOURCE_BYTES)
    ):
        raise _invalid()
    if record.state == "present":
        # Structural/digest validation alone does not make foreign presentation safe.
        if record.markdown is None:
            raise _invalid()
        try:
            validate_card_presentation(record.markdown, card_budget)
        except ExtractionError as exc:
            if exc.reason == "work_limit":
                msg = "Repository card presentation work budget exceeded"
                raise QueryLimitError.single(msg, code="HFAPI005") from exc
            raise _invalid() from exc


def read_repository_card(  # noqa: PLR0913 - exact publication and archive identities
    layout: ArchiveLayout,
    identity: RepositoryIdentity,
    sha: CommitSha,
    publication: PublicationId,
    archive_id: str,
    *,
    reader: MetadataReader | None = None,
    card_budget: ExtractionBudget | None = None,
) -> RepositoryCard | None:
    """Read an exact retained adjunct; never open README or adopt orphan presentation."""
    reader = reader or MetadataReader(layout.root, RECORD_BOUNDS)
    card_budget = card_budget if card_budget is not None else ExtractionBudget()
    # Missing adjuncts still do not grant authority to an absent/pruned publication.
    publication_binding(layout, identity, sha, publication, reader=reader)
    record = _optional(layout.repository(identity).card(sha, publication), RepositoryCard, reader)
    if record is not None:
        if (
            record.repository_type,
            record.repository_id,
            record.commit_sha,
            record.publication_id,
        ) != (identity.type, identity.id, sha, publication):
            raise _invalid()
        _bind_card(record, layout, archive_id, reader, card_budget)
    return record


class CatalogWriter:
    """Caller-owned lock/preflight capability; each record is one independent atomic unit."""

    def __init__(  # noqa: PLR0913 - original writer guards plus one shared extraction budget
        self,
        layout: ArchiveLayout,
        *,
        storage: StorageConfig,
        checks: tuple[Check, ...] | None = None,
        table: Sequence[MountEntry] | None = None,
        active_sync: TransactionJournal | None = None,
        card_budget: ExtractionBudget | None = None,
    ) -> None:
        self._ownership = require_archive_lock()
        self.card_budget = card_budget if card_budget is not None else ExtractionBudget()
        if layout.root != storage.archive_root:
            raise _invalid()
        checks = (
            checks
            if checks is not None
            else require_storage_safety(layout, storage=storage, table=table)
        )
        names = set(CHECK_ORDER[1 : CHECK_ORDER.index("credential")])
        if (
            {check.name for check in checks} != names
            or len(checks) != len(names)
            or any(
                check.blocking_code
                or check.problems
                or (
                    check.outcome != "pass"
                    and not (
                        check.name == "hardlink_capability"
                        and check.outcome == "skipped"
                        and storage.publication_mode == "copy"
                    )
                )
                for check in checks
            )
        ):
            msg = "supplemental writes require complete storage preflight"
            raise SafetyError.single(msg, code="HFMNT008")
        self.layout = layout
        self.archive_id = storage.archive_id
        self.reader = MetadataReader(layout.root, RECORD_BOUNDS)
        sentinel, _ = read_authority(layout.sentinel, ArchiveSentinel, self.reader)
        if sentinel.archive_id != self.archive_id:
            raise _invalid()
        self._journals(active_sync)
        try:
            allowed = {layout.repos, layout.manifests, layout.catalog, layout.metadata}
            if any(
                entry.path not in allowed or not stat.S_ISDIR(entry.info.st_mode)
                for entry in self.reader.entries(layout.published, missing_ok=False)
            ):
                raise _invalid()
            check_namespace(layout, self.reader)
        except (OSError, ValueError) as exc:
            raise _invalid() from exc
        descriptor = self.reader.open(layout.published, directory=True)
        try:
            info = os.fstat(descriptor)
            self._published_identity = info.st_dev, info.st_ino
        finally:
            os.close(descriptor)

    def _journals(self, active_sync: TransactionJournal | None) -> None:
        """No unexplained unfinished work; only the exact caller's active run is exempt."""
        for entry in self.reader.entries(self.layout.transactions, missing_ok=False):
            if not re.fullmatch(r"[0-9a-f]{32}\.json", entry.path.name) or not stat.S_ISREG(
                entry.info.st_mode
            ):
                raise _invalid()
            journal, _ = read_authority(entry.path, TransactionJournal, self.reader)
            if journal.archive_id != self.archive_id or entry.path != self.layout.journal(
                TransactionId(journal.transaction_id)
            ):
                raise _invalid()
            if checkpoint_order_problems(journal):
                raise _invalid()
            if journal.is_resolved:
                continue
            if self._committed_repair(journal):
                continue
            if (
                journal == active_sync
                and journal.operation == "sync"
                and journal.state == "open"
                and tuple(cp.name for cp in journal.checkpoints)
                == ("run_started", "preflight_passed", "journals_reconciled")
            ):
                continue
            msg = (
                "supplemental metadata requires resolved archive journals or the exact active sync"
            )
            raise SafetyError.single(msg, code="HFTXN001")

    def _committed_repair(self, journal: TransactionJournal) -> bool:
        """AD-13: a validated committed repair waits for grace without closing its journal."""
        names = tuple(checkpoint.name for checkpoint in journal.checkpoints)
        if (
            journal.operation != "repair"
            or journal.state != "open"
            or names[-1:] != ("repair_committed",)
        ):
            return False
        checkpoint = next(
            cp for cp in journal.checkpoints if cp.name == "retirement_record_written"
        )
        if (
            journal.repository_type is None
            or journal.repository_id is None
            or journal.commit_sha is None
            or journal.publication_id is None
        ):
            raise _invalid()
        identity = RepositoryIdentity.of(journal.repository_type, journal.repository_id)
        repository = self.layout.repository(identity)
        sha = CommitSha(journal.commit_sha)
        retired = PublicationId(journal.publication_id)
        path = repository.retirement_record(sha, retired)
        if checkpoint.evidence.get("retirement_record_path") != str(
            self.layout.archive_relative(path)
        ):
            raise _invalid()
        record, _ = read_authority(path, RepairRetirementRecord, self.reader)
        replacement = PublicationId(record.replacement_publication_id)
        if (
            record.transaction_id != journal.transaction_id
            or (
                record.repository_type,
                record.repository_id,
                record.commit_sha,
                record.retired_publication_id,
            )
            != (identity.type, identity.id, sha, retired)
            or record.cleanup.state != "pending"
            or record.retired_tree != str(repository.manifest_tree_field(sha, retired))
            or record.replacement_tree != str(repository.manifest_tree_field(sha, replacement))
        ):
            raise _invalid()
        manifest, _ = publication_binding(
            self.layout, identity, sha, replacement, reader=self.reader
        )
        if manifest.publication_generation != record.publication_generation:
            raise _invalid()
        return True

    def _parent(self, path: Path) -> int:
        descriptor = self.reader.open(self.layout.published, directory=True)
        try:
            info = os.fstat(descriptor)
            if (info.st_dev, info.st_ino) != self._published_identity:
                raise _invalid()
            for part in path.parent.relative_to(self.layout.published).parts:
                created = False
                try:
                    os.mkdir(part, PUBLISHED_DIRECTORY_MODE, dir_fd=descriptor)
                    created = True
                except FileExistsError:
                    pass
                child = os.open(
                    part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor
                )
                try:
                    if os.fstat(child).st_dev != self._published_identity[0]:
                        raise _invalid()  # noqa: TRY301 - close the pinned child on every failure
                    if created:
                        os.fchmod(child, PUBLISHED_DIRECTORY_MODE)
                        os.fsync(child)
                        os.fsync(descriptor)
                except BaseException:
                    os.close(child)
                    raise
                os.close(descriptor)
                descriptor = child
            result, descriptor = descriptor, -1
            return result
        finally:
            if descriptor >= 0:
                os.close(descriptor)

    def write(
        self,
        record: RepositoryTagSnapshot | PublicationObservation | RepositoryCard,
        *,
        checkpoint: Callable[[str], None] | None = None,
    ) -> Path:
        require_archive_lock(expected=self._ownership)
        record = parse_record(type(record), dump(record))
        identity = RepositoryIdentity.of(record.repository_type, record.repository_id)
        if record.archive_id != self.archive_id:
            raise _invalid()
        repository = self.layout.repository(identity)
        if isinstance(record, RepositoryTagSnapshot):
            path = repository.tag_snapshot
            read_tag_snapshot(self.layout, identity, self.archive_id, reader=self.reader)
        elif isinstance(record, PublicationObservation):
            path = repository.observation(
                CommitSha(record.commit_sha), PublicationId(record.publication_id)
            )
            _bind(record, self.layout, self.archive_id, self.reader)
            read_publication_observation(
                self.layout,
                identity,
                CommitSha(record.commit_sha),
                PublicationId(record.publication_id),
                self.archive_id,
                reader=self.reader,
            )
        else:
            path = repository.card(
                CommitSha(record.commit_sha), PublicationId(record.publication_id)
            )
            _bind_card(record, self.layout, self.archive_id, self.reader, self.card_budget)
            read_repository_card(
                self.layout,
                identity,
                CommitSha(record.commit_sha),
                PublicationId(record.publication_id),
                self.archive_id,
                reader=self.reader,
                card_budget=self.card_budget,
            )
        try:
            descriptor = self._parent(path)
            try:
                atomic_write_bytes(
                    Path(path.name),
                    dump(record),
                    mode=PUBLISHED_FILE_MODE,
                    dir_fd=descriptor,
                    checkpoint=checkpoint,
                )
            finally:
                os.close(descriptor)
        except (OSError, ValueError) as exc:
            msg = "supplemental atomic metadata replacement failed"
            raise SafetyError.single(msg, code="HFMNT008") from exc
        return path
