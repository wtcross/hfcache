"""Replacing damaged bytes without ever letting them become the expectation.

`docs/architecture.md` §7.5 and plan §16.5. Repair is the only operation that
writes over a revision that already exists, and `AD-13` names the property that
makes it safe: **repair must not be able to launder corrupt bytes into the
expected value.** Everything here follows from that.

The original manifest is the authority and is never rewritten (`FS-06`). A
repair downloads the same immutable SHA into an isolated cache, hashes what
landed, and compares it against that manifest. If a single digest differs the
transaction stops with `HFRET006` and the published revision is untouched —
newly observed bytes are evidence of a *failed* repair, never a new expectation.

The download goes into `.store/repair/<transaction-id>/hub`, which is `FS-14`'s
single exception. The canonical cache is where the corrupt object may already
live, and re-downloading into it could reuse the very blob under suspicion; an
empty cache with no shared objects is the only way to be sure the bytes came
from upstream.

Nothing is ever deleted in place. The replacement is published under a *new*
publication id at a new immutable locator, references switch to it atomically,
and the superseded instance stays readable where it always was for the
configured grace period so an in-flight consumer copy can finish (`AD-13`).
After the grace, cleanup *quarantines* the old tree and archives its manifest;
neither is removed, and quarantine is retained until an operator approves its
removal (plan §16.5 item 12).

Two checkpoints are gates rather than records. Checkpoint 4 is the one above:
the downloaded bytes must match the original manifest exactly. Checkpoint 8 is
the second: the replacement is re-read *from its published location* before any
reference moves, so a reference only ever switches to an instance that has been
verified where it now lives.

The journal stays open past checkpoint 15. Checkpoints 16-18 are the post-grace
cleanup, and they belong to the same transaction because they are the same
transaction — the grace period is a wait inside it, not a boundary between two.
An open journal is also the only durable record `recover` can find on its own,
which is what stops a deferred cleanup from being forgotten.
"""

import shutil
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any, Final, final

from hfcache.errors import IntegrityError, Problem, RetentionError
from hfcache.hashing import FileDigest, sha256_file, sha256_identified_file
from hfcache.hub import TreeEntry, delete_cache_revision
from hfcache.identity import (
    CommitSha,
    PublicationId,
    RepositoryIdentity,
    TransactionId,
    new_publication_id,
    new_transaction_id,
)
from hfcache.manifests import RepairProvenance, RevisionManifest
from hfcache.models import Reference, RepairCleanup, RepairRetirementRecord
from hfcache.paths import RepositoryLayout
from hfcache.publication import (
    PUBLISHED_DIRECTORY_MODE,
    PUBLISHED_FILE_MODE,
    create_staging,
    discard_staging,
    promote_staging,
    publish_catalog,
    publish_current_reference,
    publish_revision_reference,
    read_reference,
    read_verification_catalog,
    rebuild_catalog,
    stage_file,
    staged_path,
)
from hfcache.storage import fsync_directory, read_model, write_model
from hfcache.sync import HashedFile, HashedSnapshot, Timeline, build_manifest
from hfcache.transactions import Transaction, open_transaction
from hfcache.verification import ReadSet, VerificationTarget, verify_target

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path

    from hfcache.config import ApplicationConfig
    from hfcache.hub import HubClient
    from hfcache.identity import RunId
    from hfcache.paths import ArchiveLayout

__all__ = [
    "CACHE_MODE",
    "QUARANTINE_MODE",
    "RETIREMENT_MODE",
    "PendingCleanup",
    "RepairOutcome",
    "cleanup_warnings",
    "due_cleanups",
    "finish_cleanup",
    "grace_expiry",
    "pending_cleanups",
    "preserved_bytes",
    "repair_revision",
    "retirement_record",
    "unreadable_retirements",
]

CACHE_MODE: Final = 0o700
QUARANTINE_MODE: Final = 0o700
RETIREMENT_MODE: Final = 0o700
"""`.store` and `audit/` are private to the writer (§5.2)."""

RETIREMENT_FILE_MODE: Final = 0o600


def _now() -> datetime:
    return datetime.now(UTC)


def grace_expiry(retired_at: datetime, *, grace_hours: int) -> datetime:
    """When a retired instance may be quarantined.

    Configuration floors this at seven days (`HFCFG016`), and the floor exists
    because the window has to outlast the slowest consumer copy that could have
    started just before the switch.
    """
    return retired_at + timedelta(hours=grace_hours)


@final
@dataclass(frozen=True, slots=True)
class RepairOutcome:
    """What one repair produced (`docs/cli.md` §4.1)."""

    commit_sha: str
    grace_expires_at: datetime
    replacement_publication_id: str
    retired_publication_id: str
    retirement_record: str
    transaction_id: str

    def as_payload(self) -> dict[str, Any]:
        """Render for `repair`'s `data` payload."""
        return {
            "commit_sha": self.commit_sha,
            "grace_expires_at": self.grace_expires_at.isoformat().replace("+00:00", "Z"),
            "replacement_publication_id": self.replacement_publication_id,
            "retired_publication_id": self.retired_publication_id,
            "retirement_record": self.retirement_record,
            "transaction_id": self.transaction_id,
            "verified": True,
        }


def _evidence(
    layout: ArchiveLayout, identity: RepositoryIdentity, commit_sha: str
) -> tuple[str, ...]:
    """The verification findings this repair is answering, as recorded evidence.

    Read from `catalog/verification.json` rather than by verifying again: the
    mismatch report is what plan §16.5 step 1 says to *preserve*, and re-reading
    the damaged object here would risk recording a second, different observation
    of bytes that are by definition unstable.

    An empty tuple is a legitimate answer. An operator may repair an instance
    after a ZFS scrub error or a restore without this archive having verified it
    first, and refusing to act because the archive had not noticed yet would
    make repair useless in exactly the situation §16.3 lists it for.
    """
    catalog = read_verification_catalog(layout)
    if catalog is None:
        return ()
    return tuple(
        sorted(
            f"{failure.kind}:{failure.path or '-'}"
            for failure in catalog.outstanding_failures
            if failure.repository_type == identity.type
            and failure.repository_id == identity.id
            and failure.commit_sha == commit_sha
        )
    )


def repair_revision(  # noqa: PLR0913, PLR0915 - §7.5's fifteen checkpoints, in order
    client: HubClient,
    layout: ArchiveLayout,
    config: ApplicationConfig,
    *,
    identity: RepositoryIdentity,
    commit_sha: CommitSha,
    reason: str,
    envelope: Mapping[str, Any],
    run_id: RunId,
    now: datetime | None = None,
) -> RepairOutcome:
    """Perform §7.5 checkpoints 1-15 for one retained revision.

    Every act is followed by the checkpoint that names it, and
    `Transaction.checkpoint` refuses a name that is not next — so a journal this
    function produced can only describe an execution that really happened.

    The journal is deliberately **not** committed at the end. Checkpoints 16-18
    are the post-grace cleanup and belong to this same transaction; leaving it
    open is what lets `recover` find the deferred work later, and is why
    `repair_committed` is a checkpoint rather than a call to `commit`.
    """
    stamp = now or _now()
    repository = RepositoryLayout(archive=layout, identity=identity)
    reference = read_reference(layout, repository.revision_ref(commit_sha))
    retired = PublicationId(reference.publication_id)
    original = read_model(
        repository.manifest(commit_sha, retired),
        RevisionManifest,
        error=IntegrityError,
        code="HFVER007",
    )

    transaction_id = new_transaction_id()
    transaction = open_transaction(
        layout,
        transaction_id=transaction_id,
        operation="repair",
        run_id=run_id,
        archive_id=str(envelope["archive_id"]),
        config_fingerprint=str(envelope["config_fingerprint"]),
        repository_id=identity.id,
        repository_type=identity.type,
        commit_sha=commit_sha,
        publication_id=retired,
    )

    # 1. Evidence is preserved by *not touching it*: the corrupt instance and the
    # mismatch report both stay where they are, and the journal records what they
    # were. Neither path carries a `_path` suffix, because checkpoints 16 and 17
    # move both and this journal outlives them (decision 53).
    transaction.checkpoint(
        "evidence_preserved",
        corrupt_instance=str(layout.archive_relative(repository.instance(commit_sha, retired))),
        original_manifest=str(layout.archive_relative(repository.manifest(commit_sha, retired))),
        findings=list(_evidence(layout, identity, commit_sha)),
    )

    cache = layout.repair_cache_for(transaction_id)
    cache.mkdir(mode=CACHE_MODE, parents=True)
    fsync_directory(cache.parent)
    transaction.checkpoint(
        "isolated_cache_created", isolated_cache=str(layout.archive_relative(cache))
    )

    started = _now()
    snapshot = client.download(
        identity, commit_sha, cache_dir=cache, max_workers=config.sync.max_workers
    )
    client.verify_local(identity, commit_sha, cache_dir=cache)
    downloaded = _now()
    transaction.checkpoint(
        "isolated_download_completed",
        snapshot=str(layout.archive_relative(snapshot)),
        file_count=original.file_count,
    )

    hashed = _verify_against_original(snapshot, original, identity=identity)
    # The manifest's timeline records when this instance was built, so its
    # `verified_at` and `published_at` come from the clock *after* the download
    # rather than from `stamp`, which is when the transaction started. `stamp`
    # goes on the retirement record, where it means when the old instance was
    # retired and from when its grace runs.
    verified = _now()
    transaction.checkpoint(
        "verified_against_original_manifest",
        hashed_objects=hashed.hashed_objects,
        hashed_bytes=hashed.hashed_bytes,
    )

    replacement_id = new_publication_id()
    manifest = build_manifest(
        identity=identity,
        requested_revision=original.requested_revision,
        commit_sha=commit_sha,
        publication_id=replacement_id,
        # The SHA keeps its generation. Retention order is the generation and
        # nothing else (`AD-05`), so a repair that reissued one would move the
        # revision in the prune queue for having been fixed.
        publication_generation=original.publication_generation,
        publication_mode=config.storage.publication_mode,
        tree=_upstream_entries(original),
        hashed=hashed,
        layout=repository,
        hub_endpoint=config.hub.endpoint,
        timeline=Timeline(
            first_observed_at=original.first_observed_at,
            download_started_at=started,
            download_completed_at=downloaded,
            verified_at=verified,
            published_at=verified,
        ),
        dependencies=original.dependencies,
        cache_root="repair",
        repair=RepairProvenance(
            reason=reason,
            repair_of=retired,
            repair_of_manifest=str(
                layout.archive_relative(repository.manifest(commit_sha, retired))
            ),
            repaired_at=stamp,
            transaction_id=transaction_id,
        ),
    )

    staging = create_staging(layout, transaction_id)
    hashed_by_path = {entry.path: entry for entry in hashed.files}
    for entry in manifest.files:
        evidence = hashed_by_path[entry.path]
        stage_file(
            snapshot / entry.path,
            staged_path(staging, entry.path),
            publication_mode=config.storage.publication_mode,
            cache_root=cache,
            expected=FileDigest(digest=evidence.sha256, size=evidence.size),
            expected_identity=evidence.object_identity,
        )
    pending = staging.manifest
    write_model(pending, manifest, mode=PUBLISHED_FILE_MODE, code="HFRET007", error=RetentionError)
    fsync_directory(staging.tree)
    transaction.checkpoint(
        "staging_built",
        staging_tree=str(layout.archive_relative(staging.tree)),
        file_count=manifest.file_count,
        # No `_path` suffix, decision 56: checkpoint 15 discards the whole
        # staging area, and this journal stays open through the retirement grace
        # — so a suffix here would make every `recover` in that window report
        # `HFTXN003` against a repair that succeeded.
        pending_manifest=str(layout.archive_relative(pending)),
    )

    instance = repository.instance(commit_sha, replacement_id)
    promote_staging(layout, staging, instance)
    transaction.checkpoint(
        "replacement_tree_renamed",
        replacement_tree_path=str(layout.archive_relative(instance)),
        file_count=manifest.file_count,
    )

    published_manifest = repository.manifest(commit_sha, replacement_id)
    published_manifest.parent.mkdir(mode=PUBLISHED_DIRECTORY_MODE, parents=True, exist_ok=True)
    write_model(
        published_manifest,
        manifest,
        mode=PUBLISHED_FILE_MODE,
        code="HFRET007",
        error=RetentionError,
    )
    fsync_directory(published_manifest.parent)
    transaction.checkpoint(
        "replacement_manifest_published",
        replacement_manifest_path=str(layout.archive_relative(published_manifest)),
        manifest_sha256=sha256_file(published_manifest).digest,
    )

    replacement_reference = Reference(
        commit_sha=commit_sha,
        manifest=str(repository.manifest_reference(commit_sha, replacement_id)),
        publication_generation=manifest.publication_generation,
        publication_id=replacement_id,
        repository_id=identity.id,
        repository_type=identity.type,
        tree=str(repository.tree_reference(commit_sha, replacement_id)),
        updated_at=verified,
    )
    _reverify(layout, identity, replacement_reference, manifest, instance)
    transaction.checkpoint("replacement_reverified", file_count=manifest.file_count)

    publish_revision_reference(layout, replacement_reference)
    transaction.checkpoint(
        "revision_ref_switched",
        revision_ref_path=str(layout.archive_relative(repository.revision_ref(commit_sha))),
        publication_id=replacement_id,
    )

    switched = _switch_current(layout, repository, replacement_reference)
    transaction.checkpoint(
        "current_ref_switched",
        current_ref_path=str(layout.archive_relative(repository.current_ref)),
        switched=switched,
    )

    catalog_path = publish_catalog(layout, rebuild_catalog(layout, generated_at=stamp))
    transaction.checkpoint(
        "catalog_rebuilt", catalog_path=str(layout.archive_relative(catalog_path))
    )

    record_path = _write_retirement(
        repository,
        record=retirement_record(
            layout,
            repository,
            identity=identity,
            commit_sha=commit_sha,
            evidence=_evidence(layout, identity, commit_sha),
            generation=original.publication_generation,
            reason=reason,
            replacement_id=replacement_id,
            retired_id=retired,
            retired_at=stamp,
            grace_hours=config.repair.retired_instance_grace_hours,
            transaction_id=transaction_id,
        ),
        commit_sha=commit_sha,
        retired=retired,
    )
    transaction.checkpoint(
        "retirement_record_written",
        retirement_record_path=str(layout.archive_relative(record_path)),
        grace_expires_at=grace_expiry(
            stamp, grace_hours=config.repair.retired_instance_grace_hours
        ).isoformat(),
    )

    # The implicated *canonical* cache revision, not the isolated one: the blob
    # under suspicion is the one a future sync would otherwise reuse. Through the
    # library's own API, never by path (`FS-14`).
    delete_cache_revision(layout.hub_cache, commit_sha)
    transaction.checkpoint("implicated_cache_revision_deleted", commit_sha=commit_sha)

    # Only now, because in hardlink mode the published files *are* the isolated
    # cache's blobs until the rename made them the archive's own directory
    # entries. Removing the cache before the tree was durable would remove the
    # bytes with it.
    shutil.rmtree(cache.parent)
    transaction.checkpoint(
        "isolated_cache_removed",
        isolated_cache_absent=str(layout.archive_relative(cache.parent)),
    )
    # Checkpoint 15's act, for the same reason a publication's checkpoint 10
    # does it (decision 56): the tree was renamed away and the pending manifest
    # published, so what remains under `.store/staging` is a redundant copy that
    # `reconcile_storage` would report as unfinished work.
    discard_staging(layout, transaction_id)
    transaction.checkpoint(
        "repair_committed",
        state="committed",
        staging_absent=str(layout.archive_relative(staging.directory)),
    )
    # Deliberately not committed: checkpoints 16-18 are this transaction's
    # post-grace cleanup, and an open journal is what `recover` can find.
    return RepairOutcome(
        commit_sha=commit_sha,
        grace_expires_at=grace_expiry(
            stamp, grace_hours=config.repair.retired_instance_grace_hours
        ),
        replacement_publication_id=replacement_id,
        retired_publication_id=retired,
        retirement_record=str(layout.archive_relative(record_path)),
        transaction_id=transaction_id,
    )


def _verify_against_original(
    snapshot: Path, original: RevisionManifest, *, identity: RepositoryIdentity
) -> HashedSnapshot:
    """Checkpoint 4's gate: the download must match the original manifest exactly.

    Every path, size, and digest, hashed from the isolated cache rather than
    taken from anything upstream said (`AD-18`). A single difference is
    `HFRET006` and stops the transaction with the published revision unchanged —
    the whole point of `AD-13` is that observing different bytes never makes them
    the new expectation.

    The digests this produces are the ones the replacement manifest records, and
    they are identical to the original's by construction: the comparison passed.
    That is how `docs/schemas.md` §3.5's "copies the original's expected set
    exactly" and `AD-18`'s "every digest is one this archive read" hold at once.
    """
    problems: list[Problem] = []
    files: list[HashedFile] = []
    hashed_bytes = 0
    for entry in original.files:
        source = snapshot / entry.path
        try:
            digest = sha256_identified_file(source, error=RetentionError, code="HFRET006")
        except RetentionError as error:
            problems.extend(error.problems)
            continue
        if digest.size != entry.size or digest.digest != entry.sha256:
            message = (
                f"the isolated download of {entry.path} is {digest.size} bytes with digest "
                f"{digest.digest}, and the original manifest expects {entry.size} bytes with "
                f"{entry.sha256}; the published revision is unchanged and these bytes never "
                f"become the expectation (`AD-13`)"
            )
            problems.append(
                Problem(
                    code="HFRET006",
                    message=message,
                    location=entry.path,
                    repository=identity.selector,
                )
            )
            continue
        hashed_bytes += digest.size
        files.append(
            HashedFile(
                path=entry.path,
                sha256=digest.digest,
                size=digest.size,
                object_identity=digest.identity,
            )
        )
    if problems:
        raise RetentionError(problems)
    return HashedSnapshot(files=tuple(files), hashed_bytes=hashed_bytes, hashed_objects=len(files))


def _upstream_entries(original: RevisionManifest) -> Sequence[TreeEntry]:
    """The upstream identifiers the original recorded, carried forward.

    Taken from the original manifest rather than from a fresh Hub listing: they
    describe the revision as it was archived, and a repair reproduces that
    revision rather than re-observing it.
    """
    return tuple(
        TreeEntry(
            path=entry.path,
            size=entry.size,
            git_oid=entry.upstream.git_oid,
            lfs_sha256=entry.upstream.lfs_sha256,
            xet_hash=entry.upstream.xet_hash,
        )
        for entry in original.files
    )


def _reverify(
    layout: ArchiveLayout,
    identity: RepositoryIdentity,
    reference: Reference,
    manifest: RevisionManifest,
    instance: Path,
) -> None:
    """Checkpoint 8's gate: re-read the replacement where it now lives.

    Not a repeat of checkpoint 4. That one read the isolated cache; this reads
    the *published* tree, after the rename, through the same code `verify` uses.
    A reference only ever switches to an instance that has been verified at the
    locator it will be read from — which is what makes the switch at checkpoint 9
    safe even though the bytes travelled between them.
    """
    findings = verify_target(
        VerificationTarget(
            identity=identity, reference=reference, manifest=manifest, tree=instance
        ),
        ReadSet(),
    )
    if not findings:
        return
    raise RetentionError(
        [
            Problem(
                code="HFRET007",
                message=(
                    f"the published replacement failed re-verification at {finding.path}: "
                    f"{finding.kind}; no reference was switched"
                ),
                location=finding.path or str(layout.archive_relative(instance)),
                repository=identity.selector,
            )
            for finding in findings
        ]
    )


def _switch_current(
    layout: ArchiveLayout, repository: RepositoryLayout, reference: Reference
) -> bool:
    """Checkpoint 10: replace `current.json`, but only when it names this SHA.

    Returns whether it did. A repair of a retained-but-not-current revision
    leaves `current.json` alone, and recording that as a checkpoint with
    `switched = false` is what keeps the sequence complete — `Transaction`
    refuses a name that is not next, so a skipped checkpoint would make every
    later one unrecordable.
    """
    if not repository.current_ref.is_file():  # pragma: no cover - a repair implies a publication
        return False
    current = read_reference(layout, repository.current_ref)
    if current.commit_sha != reference.commit_sha:
        return False
    publish_current_reference(layout, reference)
    return True


def retirement_record(  # noqa: PLR0913 - §9.2 fixes the field set
    layout: ArchiveLayout,
    repository: RepositoryLayout,
    *,
    identity: RepositoryIdentity,
    commit_sha: CommitSha,
    evidence: Sequence[str],
    generation: int,
    reason: str,
    replacement_id: PublicationId,
    retired_id: PublicationId,
    retired_at: datetime,
    grace_hours: int,
    transaction_id: TransactionId,
) -> RepairRetirementRecord:
    """Describe the instance being retired and when its grace expires (§9.2)."""
    return RepairRetirementRecord(
        cleanup=RepairCleanup(),
        commit_sha=commit_sha,
        evidence=tuple(evidence),
        grace_expires_at=grace_expiry(retired_at, grace_hours=grace_hours),
        publication_generation=generation,
        reason=reason,
        replacement_publication_id=replacement_id,
        replacement_tree=str(
            layout.archive_relative(repository.instance(commit_sha, replacement_id))
        ),
        repository_id=identity.id,
        repository_type=identity.type,
        retired_at=retired_at,
        retired_publication_id=retired_id,
        retired_tree=str(layout.archive_relative(repository.instance(commit_sha, retired_id))),
        transaction_id=transaction_id,
    )


def _write_retirement(
    repository: RepositoryLayout,
    *,
    record: RepairRetirementRecord,
    commit_sha: CommitSha,
    retired: PublicationId,
) -> Path:
    """Place the retirement record where `audit/` keeps repair provenance."""
    path = repository.retirement_record(commit_sha, retired)
    path.parent.mkdir(mode=RETIREMENT_MODE, parents=True, exist_ok=True)
    write_model(path, record, mode=RETIREMENT_FILE_MODE, code="HFRET008", error=RetentionError)
    fsync_directory(path.parent)
    return path


# --------------------------------------------------------------------------- #
# Post-grace cleanup (§7.5 checkpoints 16-18)
# --------------------------------------------------------------------------- #


@final
@dataclass(frozen=True, slots=True)
class PendingCleanup:
    """A retired instance still waiting for its grace period to expire."""

    record: RepairRetirementRecord
    path: Path

    def is_due(self, now: datetime) -> bool:
        """Whether the grace has expired and cleanup may run."""
        return now >= self.record.grace_expires_at


def pending_cleanups(layout: ArchiveLayout) -> tuple[PendingCleanup, ...]:
    """Every retirement record whose cleanup has not completed.

    Read off `audit/repairs/`, which is where the records live and outlives
    everything else — so an operator asking "what is still waiting" gets the
    same answer whether or not any journal survived.

    A record that will not load is skipped rather than reported here. `verify`
    and `recover` are what report damaged artifacts; this function answers a
    scheduling question, and one unreadable record must not hide the others.

    Callers that turn "no pending cleanup" into a *decision* must consult
    `unreadable_retirements` as well, because absent and unreadable are not the
    same answer and only one of them means the work is done. `REP-001` is what
    happens when they are conflated.
    """
    found: list[PendingCleanup] = []
    for path in sorted(layout.repair_audit.rglob("*.retirement.json")):
        try:
            record = read_model(path, RepairRetirementRecord, error=IntegrityError, code="HFVER007")
        except IntegrityError:
            continue
        if record.cleanup.state == "pending":
            found.append(PendingCleanup(record=record, path=path))
    return tuple(found)


def unreadable_retirements(layout: ArchiveLayout) -> tuple[Path, ...]:
    """Every retirement record that exists and will not parse.

    The counterpart to `pending_cleanups`' skipping. A retirement record is the
    only durable statement that an instance was retired and is awaiting its
    post-grace quarantine, so one that cannot be read is not an absence of work —
    it is work whose description has been damaged, and `TX-06` says that is a
    state to report rather than to resolve by assuming the smaller answer.
    """
    damaged: list[Path] = []
    for path in sorted(layout.repair_audit.rglob("*.retirement.json")):
        try:
            read_model(path, RepairRetirementRecord, error=IntegrityError, code="HFVER007")
        except IntegrityError:
            damaged.append(path)
    return tuple(damaged)


def due_cleanups(
    layout: ArchiveLayout, *, now: datetime | None = None
) -> tuple[PendingCleanup, ...]:
    """The pending cleanups whose grace has expired (`HFWRN008`)."""
    moment = now or _now()
    return tuple(item for item in pending_cleanups(layout) if item.is_due(moment))


def finish_cleanup(
    layout: ArchiveLayout,
    transaction: Transaction,
    pending: PendingCleanup,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Perform §7.5 checkpoints 16-18 on one retired instance.

    A rename into quarantine and a rename into `audit/`, never a removal. Plan
    §16.5 item 12 retains quarantined evidence until an operator confirms storage
    health and explicitly approves its cleanup, so this application has no code
    path that removes it on a schedule.

    The moves are idempotent (`TX-04`): a retired tree already gone from its
    original locator — because a previous attempt got that far — is not an
    error, since the checkpoint's evidence already holds. Recording the
    checkpoints twice is a different matter and is refused by the journal's own
    ordering guard (`HFTXN002`), which is what stops a second cleanup from
    describing an execution no valid one produces.
    """
    stamp = now or _now()
    record = pending.record
    identity = RepositoryIdentity.of(record.repository_type, record.repository_id)
    repository = RepositoryLayout(archive=layout, identity=identity)
    commit = CommitSha(record.commit_sha)
    retired = PublicationId(record.retired_publication_id)

    quarantine = layout.quarantine_for(TransactionId(record.transaction_id))
    tree = repository.instance(commit, retired)
    _rename_once(tree, quarantine, mode=QUARANTINE_MODE)
    transaction.checkpoint(
        "retired_tree_quarantined",
        quarantine_path=str(layout.archive_relative(quarantine)),
        retired_tree_absent=str(layout.archive_relative(tree)),
    )

    manifest = repository.manifest(commit, retired)
    archived = repository.retired_manifest(commit, retired)
    _rename_once(manifest, archived, mode=RETIREMENT_MODE)
    transaction.checkpoint(
        "retired_manifest_archived",
        archived_manifest_path=str(layout.archive_relative(archived)),
        retired_manifest_absent=str(layout.archive_relative(manifest)),
    )

    completed = record.model_copy(
        update={
            "cleanup": RepairCleanup(
                completed_at=stamp,
                quarantine_path=str(layout.archive_relative(quarantine)),
                state="completed",
            )
        }
    )
    write_model(
        pending.path,
        RepairRetirementRecord.model_validate(completed.model_dump(mode="json")),
        mode=RETIREMENT_FILE_MODE,
        code="HFRET009",
        error=RetentionError,
    )
    transaction.checkpoint(
        "repair_cleanup_completed",
        retirement_record_path=str(layout.archive_relative(pending.path)),
    )
    return {
        "quarantine_path": str(layout.archive_relative(quarantine)),
        "retired_publication_id": retired,
    }


def _rename_once(source: Path, destination: Path, *, mode: int) -> None:
    """Move one artifact into its resting place, tolerating having done it already.

    `TX-04` requires every checkpoint be idempotent, and the honest way to make a
    rename idempotent is to notice that the source is already gone rather than to
    re-create it. A destination that already exists is left alone for the same
    reason nothing else in this application overwrites evidence.
    """
    try:
        destination.parent.mkdir(mode=mode, parents=True, exist_ok=True)
        if source.exists() and not destination.exists():
            source.rename(destination)
        fsync_directory(destination.parent)
    except OSError as exc:
        message = f"{source} could not be moved to {destination}: {exc.strerror}"
        raise RetentionError.single(message, code="HFRET009", location=str(source)) from exc


def cleanup_warnings(layout: ArchiveLayout, *, now: datetime | None = None) -> list[Problem]:
    """`HFWRN008` for each retired instance past its grace and awaiting cleanup."""
    return [
        Problem(
            code="HFWRN008",
            message=(
                f"the retired instance {item.record.retired_publication_id} of "
                f"{item.record.repository_type}:{item.record.repository_id}@"
                f"{item.record.commit_sha} passed its grace period at "
                f"{item.record.grace_expires_at.isoformat()} and awaits cleanup; "
                f"`hfcache recover --apply` performs it"
            ),
            location=item.record.retired_tree,
            repository=f"{item.record.repository_type}:{item.record.repository_id}",
        )
        for item in due_cleanups(layout, now=now)
    ]


def preserved_bytes(layout: ArchiveLayout) -> int:
    """How much the quarantine area is holding, for `status` to report.

    Reported rather than reclaimed. Plan §16.5 item 12 keeps quarantined
    evidence until an operator approves its removal, so the useful thing this
    application can say about it is how much space it is costing.
    """
    total = 0
    for path in layout.quarantine.rglob("*"):
        if path.is_file() and not path.is_symlink():
            total += path.lstat().st_size
    return total
