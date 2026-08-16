"""What a crashed run left behind, reported rather than cleaned up.

`.store/staging`, `.store/trash`, `.store/quarantine`, and `.store/repair` are
the four areas where work in progress lives, and every entry in them is named by
transaction id (`FS-18`). After a crash some of those entries are outstanding
work and some are rubbish, and telling them apart is the whole job here.

Three rules shape it.

**Nothing is deleted.** This module only ever *reports* (`FS-19`, `AD-16`). Plan
§13.3 allows a stale staging directory to be reclaimed, but only when it matches
the naming contract, **has a journal**, and exceeds the configured age — and the
journal is what says whether the work it holds was finished. Journals arrive at
`STO-010` and the reclamation that reads them at `STO-011`, so what exists today
is the finding and the warning that surfaces it.

**A name that is not ours is not ours.** An entry in one of these areas whose
name is not a 32-hex transaction id was not created by this application. It is
reported under `HFWRN003` and preserved, whatever it is.

**Age is measured, never assumed.** The delay is not the safety mechanism on its
own — reclamation also requires a journal — but it is what stops a concurrent
operator command from having its working directory pulled out from under it
(`docs/progress.md` decision 5).

The second half of this module plans and applies recovery (plan §18,
`docs/architecture.md` §7.7). Planning reads journals and the filesystem and
proposes a remedy for each unfinished transaction; applying performs only
remedies a plan validated, records one checkpoint per remediation, and writes a
durable report. Recovery is roll-forward oriented and never replaces an expected
digest, chooses a revision by modification time, or removes unknown data
(`AD-16`).

What recovery may *not* resolve on its own it reports as blocked, and a blocked
plan stops a mutating command at exit `20` before Hub contact (§7.9). That is
deliberate: a state two valid executions could both have produced has no single
correct resolution, and guessing at one is how an archive loses data.
"""

import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import partial
from typing import TYPE_CHECKING, Any, Final, Literal, final

from hfcache.errors import ExitCode, IntegrityError, Problem, RetentionError, SafetyError
from hfcache.identity import (
    OPAQUE_ID_LENGTH,
    CommitSha,
    PublicationId,
    RepositoryIdentity,
    TransactionId,
    new_run_id,
    new_transaction_id,
)
from hfcache.logging import emit
from hfcache.manifests import RevisionManifest
from hfcache.models import PrunedRevisionRecord, PrunePlan, PurgePlan, Reference
from hfcache.paths import RepositoryLayout
from hfcache.publication import (
    PUBLISHED_DIRECTORY_MODE,
    PUBLISHED_FILE_MODE,
    discard_staging,
    publish_catalog,
    publish_current_reference,
    publish_revision_reference,
    read_reference,
    rebuild_catalog,
    retained_references,
)
from hfcache.purge import complete_purge, rollback_purge
from hfcache.repair import (
    PendingCleanup,
    finish_cleanup,
    pending_cleanups,
    unreadable_retirements,
)
from hfcache.reporting import RecoveryReport, Remediation
from hfcache.retention import remove_empty_containers
from hfcache.storage import (
    BYTES_PER_GIB,
    atomic_write_bytes,
    describe_capacity,
    effective_reserve,
    fsync_directory,
    read_model,
    write_model,
)
from hfcache.transactions import (
    CHECKPOINTS,
    Transaction,
    checkpoint_order_problems,
    evidence_problems,
    open_journals,
    open_transaction,
    read_journal,
)
from hfcache.verification import ReadSet, VerificationTarget, verify_target

if TYPE_CHECKING:
    from collections.abc import Callable, Collection, Mapping
    from pathlib import Path

    from hfcache.config import StorageConfig
    from hfcache.identity import RunId
    from hfcache.models import TransactionJournal
    from hfcache.paths import ArchiveLayout
    from hfcache.transactions import JournalFile

__all__ = [
    "APPLICABLE",
    "BLOCKED",
    "COMPLETING",
    "QUARANTINE_MODE",
    "REPORT_DIRECTORY_MODE",
    "REPORT_MODE",
    "SECONDS_PER_HOUR",
    "ArchiveHealth",
    "AreaFinding",
    "JournalReconciliation",
    "PlannedRemediation",
    "Reconciliation",
    "RecoveryPlan",
    "Remedy",
    "apply_recovery",
    "measure_health",
    "plan_recovery",
    "publish_current_if_newest",
    "reconcile",
    "reconcile_storage",
]

SECONDS_PER_HOUR: Final = 3600

QUARANTINE_MODE: Final = 0o700
"""Quarantine and `runs/` are private to the writer (§5.2)."""

REPORT_MODE: Final = 0o600
"""A run report is the writer's record, not consumer data."""

REPORT_DIRECTORY_MODE: Final = 0o700
"""`audit/` outlives the data it describes and is never consumer-visible (§5.2)."""

_TRANSACTION_NAME_LENGTH: Final = OPAQUE_ID_LENGTH
_HEX: Final = frozenset("0123456789abcdef")


@final
@dataclass(frozen=True, slots=True)
class AreaFinding:
    """One entry in a transaction-owned area, and how old it is."""

    area: str
    path: str
    transaction_id: str
    age_hours: float
    stale: bool

    def as_payload(self) -> dict[str, Any]:
        """Render for a `--json` payload."""
        return {
            "age_hours": round(self.age_hours, 3),
            "area": self.area,
            "path": self.path,
            "stale": self.stale,
            "transaction_id": self.transaction_id,
        }


@final
@dataclass(frozen=True, slots=True)
class Reconciliation:
    """Everything the four transaction areas hold right now."""

    findings: tuple[AreaFinding, ...]
    unknown: tuple[str, ...]
    warnings: tuple[Problem, ...]

    @property
    def unfinished(self) -> tuple[AreaFinding, ...]:
        """Staging and repair areas, which are work that did not complete."""
        return tuple(
            finding
            for finding in self.findings
            if finding.area in {".store/staging", ".store/repair"}
        )

    @property
    def deferred_cleanup(self) -> tuple[AreaFinding, ...]:
        """Tombstones a prune committed but did not physically remove."""
        return tuple(finding for finding in self.findings if finding.area == ".store/trash")

    def as_payload(self) -> dict[str, Any]:
        """Render for a `--json` payload."""
        return {
            "deferred_cleanup": len(self.deferred_cleanup),
            "findings": [finding.as_payload() for finding in self.findings],
            "unfinished_transactions": len(self.unfinished),
            "unknown_entries": list(self.unknown),
        }


def _is_transaction_name(name: str) -> bool:
    """Whether a directory name is one this application created (`FS-18`)."""
    return len(name) == _TRANSACTION_NAME_LENGTH and set(name) <= _HEX


def reconcile_storage(
    layout: ArchiveLayout,
    *,
    stale_staging_age_hours: int,
    now: datetime | None = None,
) -> Reconciliation:
    """Report what the transaction areas hold, without touching any of it.

    `now` is injectable so a test can age a directory without waiting; production
    passes nothing and gets the clock. Age comes from the directory's `mtime`,
    which is the only timestamp available for work that never got as far as
    writing a journal.
    """
    moment = datetime.now(UTC) if now is None else now
    findings: list[AreaFinding] = []
    unknown: list[str] = []
    warnings: list[Problem] = []

    for area in (layout.staging, layout.trash, layout.quarantine, layout.repair_caches):
        name = str(layout.archive_relative(area))
        try:
            children = sorted(area.iterdir())
        except OSError:
            # An area that is not there is an archive that has not reached this
            # state yet, which is not a finding. An unreadable one is reported by
            # `doctor`'s writability check, not here.
            continue
        for child in children:
            where = str(layout.archive_relative(child))
            if not _is_transaction_name(child.name):
                unknown.append(where)
                continue
            age = (moment.timestamp() - child.stat().st_mtime) / SECONDS_PER_HOUR
            stale = name == ".store/staging" and age >= stale_staging_age_hours
            findings.append(
                AreaFinding(
                    area=name, path=where, transaction_id=child.name, age_hours=age, stale=stale
                )
            )

    warnings.extend(_stale_warnings(findings, stale_staging_age_hours))
    warnings.extend(_deferred_warnings(findings))
    if unknown:
        message = (
            f"{len(unknown)} entries in the archive's transaction areas were not created by "
            f"this application; they are preserved and never removed (`FS-19`)"
        )
        warnings.append(
            Problem(
                code="HFWRN003",
                message=message,
                location=str(layout.store),
                context={"entries": sorted(unknown)},
            )
        )
    return Reconciliation(
        findings=tuple(findings), unknown=tuple(sorted(unknown)), warnings=tuple(warnings)
    )


def _stale_warnings(findings: list[AreaFinding], age_hours: int) -> list[Problem]:
    """`HFWRN004` for each staging area older than the configured age."""
    return [
        Problem(
            code="HFWRN004",
            message=(
                f"staging {finding.path} is {finding.age_hours:.1f} hours old, past the "
                f"configured {age_hours}; it is reported and never removed here, because "
                f"reclamation also requires the transaction journal that says what it holds"
            ),
            location=finding.path,
            context={"age_hours": round(finding.age_hours, 3)},
        )
        for finding in findings
        if finding.stale
    ]


def _deferred_warnings(findings: list[AreaFinding]) -> list[Problem]:
    """`HFWRN002` for each tombstone a prune committed but did not remove."""
    deferred = [finding for finding in findings if finding.area == ".store/trash"]
    for finding in deferred:
        # Plan §24's `retention.deferred`. The tombstone observation is the
        # signal for this state (§7.4): the post-commit steps run inline, a
        # failure there leaves the journal open and the tombstone in place, and
        # this reconciliation is where the state is seen. So the event is
        # emitted here rather than by the prune.
        emit("retention.deferred", tombstone=finding.path, area=finding.area)
    return [
        Problem(
            code="HFWRN002",
            message=(
                f"{finding.path} is a prune tombstone whose physical removal is outstanding; "
                f"the revision is logically pruned and the bytes are still on the dataset"
            ),
            location=finding.path,
        )
        for finding in deferred
    ]


@final
@dataclass(frozen=True, slots=True)
class ArchiveHealth:
    """The archive-level block `status` reports (`docs/cli.md` §2)."""

    available_bytes: int
    total_bytes: int
    reserve_bytes: int
    reconciliation: Reconciliation

    @property
    def headroom_bytes(self) -> int:
        """What is free above the reserve. Negative when the reserve is breached."""
        return self.available_bytes - self.reserve_bytes

    def as_payload(self) -> dict[str, Any]:
        """Render for `status`'s `data.archive` block."""
        return {
            "available_bytes": self.available_bytes,
            "available_gib": round(self.available_bytes / BYTES_PER_GIB, 1),
            "headroom_bytes": self.headroom_bytes,
            "reserve_bytes": self.reserve_bytes,
            "total_bytes": self.total_bytes,
        } | self.reconciliation.as_payload()


def measure_health(
    layout: ArchiveLayout,
    storage: StorageConfig,
    *,
    stale_staging_age_hours: int,
    now: datetime | None = None,
) -> ArchiveHealth:
    """Free space against the reserve, plus whatever the transaction areas hold.

    `status` is the command an operator runs first, so this reads and never
    writes: no probe, no lock, no Hub request (`docs/cli.md` §2).
    """
    capacity = describe_capacity(layout.root)
    return ArchiveHealth(
        available_bytes=capacity.available_bytes,
        total_bytes=capacity.total_bytes,
        reserve_bytes=effective_reserve(
            capacity.total_bytes,
            minimum_gib=storage.minimum_free_space_gib,
            minimum_percent=storage.minimum_free_space_percent,
        ),
        reconciliation=reconcile_storage(
            layout, stale_staging_age_hours=stale_staging_age_hours, now=now
        ),
    )


# --------------------------------------------------------------------------- #
# Planning (plan §18, `docs/architecture.md` §7.7)
# --------------------------------------------------------------------------- #

Remedy = Literal[
    "quarantine_staging",
    "quarantine_tree",
    "complete_publication",
    "rollback_prune",
    "complete_prune",
    "complete_repair",
    "finish_repair_cleanup",
    "close_journal",
    "operator",
    "wait",
]
"""What recovery proposes to do about one unfinished transaction.

`wait` is a real answer, not an absence of one. A staging directory younger than
`sync.stale_staging_age_hours` may belong to work an operator started, and §7.8
requires all three of name, journal, and age before anything is acted on; a
retired repair instance inside its grace period is deliberately waiting, and
finishing early would pull the tree out from under an in-flight consumer copy.
"""

BLOCKED: Final = "operator"

APPLICABLE: Final = frozenset(
    {
        "quarantine_staging",
        "quarantine_tree",
        "complete_publication",
        "rollback_prune",
        "complete_prune",
        "complete_repair",
        "finish_repair_cleanup",
        "close_journal",
    }
)
"""Remedies `recover --apply` performs. `wait` and `operator` are not among them."""


@final
@dataclass(frozen=True, slots=True)
class PlannedRemediation:
    """One unfinished transaction and what recovery proposes to do about it."""

    transaction_id: str
    operation: str
    state: str
    last_checkpoint: str | None
    remedy: Remedy
    reason: str
    problems: tuple[Problem, ...] = ()

    def as_payload(self) -> dict[str, Any]:
        """Render for a `--json` payload."""
        return {
            "last_checkpoint": self.last_checkpoint,
            "operation": self.operation,
            "reason": self.reason,
            "remedy": self.remedy,
            "state": self.state,
            "transaction_id": self.transaction_id,
        }


@final
@dataclass(frozen=True, slots=True)
class RecoveryPlan:
    """Everything `recover --apply` would do, and everything it would refuse to."""

    remediations: tuple[PlannedRemediation, ...]

    @property
    def blocked(self) -> tuple[PlannedRemediation, ...]:
        """States recovery may not resolve on its own (§7.9)."""
        return tuple(entry for entry in self.remediations if entry.remedy == BLOCKED)

    @property
    def actionable(self) -> tuple[PlannedRemediation, ...]:
        """What applying would actually perform."""
        return tuple(entry for entry in self.remediations if entry.remedy in APPLICABLE)

    @property
    def problems(self) -> tuple[Problem, ...]:
        """Every problem behind a blocked remediation, for one refusal."""
        return tuple(problem for entry in self.blocked for problem in entry.problems)

    def as_payload(self) -> dict[str, Any]:
        """Render for `recover`'s `data` payload (`docs/cli.md` §4.1)."""
        return {
            "actionable": len(self.actionable),
            "blocked": len(self.blocked),
            "plan": [entry.as_payload() for entry in self.remediations],
        }


def plan_recovery(
    layout: ArchiveLayout,
    *,
    stale_staging_age_hours: int,
    now: datetime | None = None,
    exclude: Collection[str] = (),
) -> RecoveryPlan:
    """Decide what to do about every unfinished journal, without touching anything.

    This is `recover --dry-run` in full, and the analysis a mutating command runs
    before it acts (`TX-07`). Every journal is validated first — schema, then
    checkpoint order, then evidence against the filesystem — because a journal
    that cannot be trusted is not a journal a remedy may be chosen from.

    `exclude` names transactions to leave out. It exists for the one caller that
    has an open journal of its own while it reconciles: a sync run opens its
    §7.6 journal before it may touch anything (`TX-01`), so without this it
    would find itself unfinished and propose a remedy for a run that is still
    executing. A transaction cannot recover itself.
    """
    moment = datetime.now(UTC) if now is None else now
    skip = frozenset(exclude)
    return RecoveryPlan(
        remediations=tuple(
            _remediation(layout, file, stale_staging_age_hours=stale_staging_age_hours, now=moment)
            for file in open_journals(layout)
            if file.journal.transaction_id not in skip
        )
    )


def _remediation(  # noqa: PLR0911 - one return per state §7 gives a resolution for
    layout: ArchiveLayout,
    file: JournalFile,
    *,
    stale_staging_age_hours: int,
    now: datetime,
) -> PlannedRemediation:
    """Choose one remedy, or refuse to."""
    journal = file.journal
    names = [checkpoint.name for checkpoint in journal.checkpoints]
    last = names[-1] if names else None
    blocked = partial(
        PlannedRemediation,
        transaction_id=journal.transaction_id,
        operation=journal.operation,
        state=journal.state,
        last_checkpoint=last,
        remedy=BLOCKED,
    )

    problems = [
        *checkpoint_order_problems(journal),
        *evidence_problems(layout, journal),
    ]
    if problems:
        return blocked(
            reason="the journal does not describe a state any valid execution produces",
            problems=tuple(problems),
        )
    if journal.state == "needs_operator":
        message = (
            f"transaction {journal.transaction_id} stopped and asked for an operator; "
            f"recovery never resolves what it was told not to"
        )
        return blocked(
            reason="the transaction asked for an operator",
            problems=(
                Problem(
                    code="HFTXN004",
                    message=message,
                    location=str(journal.transaction_id),
                ),
            ),
        )

    if journal.operation in CHECKPOINTS and names == list(CHECKPOINTS[journal.operation]):
        return PlannedRemediation(
            transaction_id=journal.transaction_id,
            operation=journal.operation,
            state=journal.state,
            last_checkpoint=last,
            remedy="close_journal",
            reason="every documented checkpoint is recorded, so only the journal is open",
        )

    if journal.operation == "publication":
        if _before_the_tree_was_renamed(names):
            return _staging_remediation(
                layout, journal, last, stale_staging_age_hours=stale_staging_age_hours, now=now
            )
        return _publication_remediation(layout, journal, last)
    if journal.operation == "prune":
        return _prune_remediation(journal, last)
    if journal.operation == "repair":
        return _repair_remediation(layout, journal, last, now=now)
    if journal.operation == "sync":
        return _sync_remediation(journal, last)

    message = (
        f"transaction {journal.transaction_id} is a {journal.operation} that stopped after "
        f"{last!r}; resolving it needs evidence recovery cannot obtain on its own"
    )
    return blocked(
        reason=f"no unambiguous resolution for a {journal.operation} at {last!r}",
        problems=(Problem(code="HFTXN004", message=message, location=str(journal.transaction_id)),),
    )


def _sync_remediation(journal: TransactionJournal, last: str | None) -> PlannedRemediation:
    """A run journal a crash left open: close it, whatever it got to (§7.6).

    The run transaction owns no filesystem state. Every mutation a run made
    belongs to a publication or a prune journal that has its own remedy, and
    §7.6 says so outright — the per-repository journals are the authority and
    the run journal exists to correlate them and to prove reconciliation
    happened before Hub contact. There is nothing here to roll forward.

    The one whole-run step that does touch the archive is plan §13.1 step 10's
    catalog rebuild, and recovery deliberately does not perform it: that rebuild
    reads *configuration* to decide which repositories are managed (`AD-06`),
    and recovery takes no configuration. Rebuilding without it would mark every
    configured repository unmanaged — a derived file (`FS-16`) made actively
    wrong rather than merely stale. The next sync rebuilds it correctly.
    """
    return PlannedRemediation(
        transaction_id=journal.transaction_id,
        operation=journal.operation,
        state=journal.state,
        last_checkpoint=last,
        remedy="close_journal",
        reason="a run journal correlates the per-repository journals and holds no state of its own",
    )


def _before_the_tree_was_renamed(names: list[str]) -> bool:
    """Whether a publication crashed before checkpoint 5 (§7.3 crash matrix).

    Before the rename nothing published changed, so rolling back is always
    correct. At or after it a tree exists and the resolution is to roll forward.
    """
    return "revision_tree_renamed" not in names


def _publication_remediation(
    layout: ArchiveLayout, journal: TransactionJournal, last: str | None
) -> PlannedRemediation:
    """A publication whose tree was renamed: roll forward, or quarantine it.

    §7.3's crash matrix gives one resolution for each of the four rows from
    "after 5, before 6" onward, and they are the same resolution at different
    depths: validate the published tree against its manifest, then continue from
    wherever the journal stopped. Every remaining step is idempotent, so the
    depth only decides how much is left to do.

    The one branch is the row's own caveat. Between 5 and 6 the manifest lives
    only in staging; if that staged manifest is gone, the tree cannot be
    validated and §7.3 says to quarantine it and report — **never publish an
    unvalidated tree**.
    """
    common = {
        "transaction_id": journal.transaction_id,
        "operation": journal.operation,
        "state": journal.state,
        "last_checkpoint": last,
    }
    if _publication_manifest(layout, journal) is None:
        return PlannedRemediation(
            **common,
            remedy="quarantine_tree",
            reason=(
                "the tree was renamed but no manifest survives to validate it against, so it "
                "is preserved as evidence rather than published"
            ),
        )
    return PlannedRemediation(
        **common,
        remedy="complete_publication",
        reason=(
            f"the published tree can be validated against its manifest and continued from {last!r}"
        ),
    )


_MANIFEST_EVIDENCE: Final = (
    # A publication's published copy, then a repair's, then either one's staged
    # copy. Order matters: a repaired SHA has *two* manifests on disk, and only
    # the journal knows which one this transaction was publishing.
    "manifest_path",
    "replacement_manifest_path",
    "pending_manifest",
)


def _publication_manifest(
    layout: ArchiveLayout, journal: TransactionJournal
) -> RevisionManifest | None:
    """The manifest describing the instance *this* transaction was publishing.

    Located from the journal's own evidence rather than by looking for manifests
    under the SHA. A repaired revision has an original manifest and a replacement
    manifest filed side by side, and choosing between them by directory order
    would let recovery switch a reference to the instance the transaction was
    replacing — the exact opposite of what it was doing.

    The published copy is preferred over the staged one, because after checkpoint
    6 it is the archive's own artifact; the staged copy is what makes the window
    between the rename and that publication recoverable at all (§7.3).
    """
    for key in _MANIFEST_EVIDENCE:
        for checkpoint in journal.checkpoints:
            value = checkpoint.evidence.get(key)
            if not isinstance(value, str):
                continue
            try:
                return read_model(
                    layout.resolve(value, code="HFTXN003"),
                    RevisionManifest,
                    error=IntegrityError,
                    code="HFVER007",
                )
            except IntegrityError:
                continue
    return None


def _prune_remediation(journal: TransactionJournal, last: str | None) -> PlannedRemediation:
    """A prune, resolved by which side of its commit point it stopped on (§7.4).

    Checkpoint 7 divides the transaction into two opposite regimes, and the
    resolution follows the regime rather than the step. Before it: roll back, so
    all six revisions are published again — over-retention is always preferable
    to a revision that should not have gone (`TX-06`). At or after it: never
    republish, because five revisions are what consumers already see and the
    archive recorded that decision; only the post-commit cleanup is retried.
    """
    names = [checkpoint.name for checkpoint in journal.checkpoints]
    common = {
        "transaction_id": journal.transaction_id,
        "operation": journal.operation,
        "state": journal.state,
        "last_checkpoint": last,
    }
    if "prune_logically_committed" in names:
        return PlannedRemediation(
            **common,
            remedy="complete_prune",
            reason=(
                "the prune passed its commit point, so the five consumer-visible revisions "
                "stand and only the deferred cleanup is finished"
            ),
        )
    return PlannedRemediation(
        **common,
        remedy="rollback_prune",
        reason=(
            "the prune stopped before its commit point, so the sixth revision is republished; "
            "over-retention is reportable and a deletion is not reversible"
        ),
    )


def _repair_remediation(
    layout: ArchiveLayout, journal: TransactionJournal, last: str | None, *, now: datetime
) -> PlannedRemediation:
    """A repair, resolved by whether its references switched and its grace expired.

    Two quite different states share one operation. Before `repair_committed`
    the transaction is genuinely unfinished — §7.5's interesting case is a crash
    between 9 and 10, where the per-SHA reference names the new instance and
    `current.json` still names the old one; both trees exist, so `FS-10` holds
    and recovery completes the second switch.

    After `repair_committed` nothing is unfinished at all: the journal is open
    *by design* for the grace period, so that the post-grace cleanup has a
    durable record to be found from. Inside the grace that is `wait`; past it,
    the cleanup runs.
    """
    names = [checkpoint.name for checkpoint in journal.checkpoints]
    common = {
        "transaction_id": journal.transaction_id,
        "operation": journal.operation,
        "state": journal.state,
        "last_checkpoint": last,
    }
    if "replacement_tree_renamed" not in names:
        # Nothing published changed: the revision is still the instance it was,
        # and the isolated download and staging are the only artifacts. That is
        # §7.3's "before 5" shape, and it takes §7.3's answer.
        return _staging_remediation(layout, journal, last, stale_staging_age_hours=0, now=now)
    if "repair_committed" not in names:
        return PlannedRemediation(
            **common,
            remedy="complete_repair",
            reason=f"the repair verified its replacement and stopped at {last!r}; it continues",
        )
    pending = _pending_for(layout, journal.transaction_id)
    if pending is None:
        # `REP-001`: absent and unreadable are not the same answer. A retirement
        # record is the only durable statement that an instance is awaiting its
        # post-grace quarantine, so one that will not parse is damaged work, not
        # finished work — and closing the journal on it would discard the last
        # thing that makes the cleanup reachable from `recover`, while `status`
        # went on citing `recover --apply` as the remedy (`HFWRN008`).
        if damaged := unreadable_retirements(layout):
            return PlannedRemediation(
                **common,
                remedy=BLOCKED,
                reason=(
                    "the repair is committed but a retirement record will not parse, so whether "
                    "its retired instance still awaits quarantine cannot be determined"
                ),
                problems=tuple(
                    Problem(
                        code="HFTXN003",
                        message=(
                            f"the retirement record {layout.archive_relative(path)} cannot be "
                            f"read, so the repair's post-grace cleanup can be neither confirmed "
                            f"nor performed"
                        ),
                        location=str(layout.archive_relative(path)),
                    )
                    for path in damaged
                ),
            )
        return PlannedRemediation(
            **common,
            remedy="close_journal",
            reason="the repair is complete and its retired instance has already been cleaned up",
        )
    if not pending.is_due(now):
        return PlannedRemediation(
            **common,
            remedy="wait",
            reason=(
                f"the retired instance is readable until "
                f"{pending.record.grace_expires_at.isoformat()}, so an in-flight consumer copy "
                f"can still finish"
            ),
        )
    return PlannedRemediation(
        **common,
        remedy="finish_repair_cleanup",
        reason="the grace period expired, so the retired instance is quarantined and archived",
    )


def _pending_for(layout: ArchiveLayout, transaction_id: str) -> PendingCleanup | None:
    """The retirement record this repair transaction wrote, if its cleanup is open."""
    for item in pending_cleanups(layout):
        if item.record.transaction_id == transaction_id:
            return item
    return None


def _staging_remediation(
    layout: ArchiveLayout,
    journal: TransactionJournal,
    last: str | None,
    *,
    stale_staging_age_hours: int,
    now: datetime,
) -> PlannedRemediation:
    """Quarantine abandoned staging, but only once §7.8's three conditions hold."""
    staging = layout.staging_for(TransactionId(journal.transaction_id)).directory
    common = {
        "transaction_id": journal.transaction_id,
        "operation": journal.operation,
        "state": journal.state,
        "last_checkpoint": last,
    }
    if not staging.is_dir():
        return PlannedRemediation(
            **common,
            remedy="close_journal",
            reason="nothing published changed and the staging area is already gone",
        )
    age = (now.timestamp() - staging.stat().st_mtime) / SECONDS_PER_HOUR
    if age < stale_staging_age_hours:
        return PlannedRemediation(
            **common,
            remedy="wait",
            reason=(
                f"staging is {age:.1f} hours old, under the configured "
                f"{stale_staging_age_hours}; it is left alone until it is certainly abandoned"
            ),
        )
    return PlannedRemediation(
        **common,
        remedy="quarantine_staging",
        reason="the publication stopped before anything was published, so it rolls back",
    )


# --------------------------------------------------------------------------- #
# Applying
# --------------------------------------------------------------------------- #


def apply_recovery(
    layout: ArchiveLayout,
    plan: RecoveryPlan,
    *,
    envelope: Mapping[str, Any],
    started_at: datetime,
) -> tuple[Path, tuple[Remediation, ...]]:
    """Perform a validated plan, journalled, and write the durable report.

    Refuses a plan with anything blocked, before performing any of the rest: a
    partially recovered archive with an unresolved transaction still in it is
    harder to reason about than the state it started in.

    Idempotent (`TX-04`). Each remedy closes the journal it resolved, so a
    second run finds nothing left to do — which is what makes `recover --apply`
    safe to run twice.
    """
    if plan.blocked:
        raise SafetyError(list(plan.problems))

    run_id = new_run_id()
    transaction = open_transaction(
        layout,
        transaction_id=new_transaction_id(),
        operation="recovery",
        run_id=run_id,
        archive_id=str(envelope["archive_id"]),
        config_fingerprint=str(envelope["config_fingerprint"]),
    )
    applied = [_perform(layout, entry, transaction) for entry in plan.remediations]

    report_path = layout.run_report(started_at, run_id)
    _write_report(report_path, applied, envelope=envelope, run_id=run_id, started_at=started_at)
    transaction.checkpoint(
        "recovery_report_written", report_path=str(layout.archive_relative(report_path))
    )
    transaction.checkpoint("recovery_completed", remediation_count=len(applied))
    transaction.commit()
    return report_path, tuple(sorted(applied, key=lambda record: record.transaction_id))


@final
@dataclass(frozen=True, slots=True)
class JournalReconciliation:
    """What `TX-07` reconciliation settled before a mutating command acted."""

    resolved: tuple[str, ...]
    pending: tuple[str, ...]
    report: str | None = None

    def as_evidence(self) -> dict[str, Any]:
        """§7.6 checkpoint 3's evidence: the transaction ids, or none found.

        `report` carries no `_path` suffix even though it names one that exists.
        The convention (decision 42) asserts a path *this* transaction must
        still be able to observe, and a recovery report belongs to the recovery
        transaction that wrote it — a later `recover` may legitimately supersede
        it, and a run journal is not the place that should stop the machine.
        """
        evidence: dict[str, Any] = {
            "pending_transaction_ids": list(self.pending),
            "reconciled_transaction_ids": list(self.resolved),
        }
        if self.report is not None:
            evidence["recovery_report"] = self.report
        return evidence


def reconcile(
    layout: ArchiveLayout,
    *,
    stale_staging_age_hours: int,
    envelope: Mapping[str, Any],
    started_at: datetime,
    exclude: Collection[str] = (),
) -> JournalReconciliation:
    """Resolve every unfinished journal before a mutating command acts (`TX-07`).

    Run under the exclusive lock the command already holds and before the Hub is
    contacted, which is the entire point of the rule: an unattended run must not
    download a byte into an archive whose last run stopped somewhere nobody has
    looked at. A blocked plan raises, so the command exits `20` (§7.9) having
    changed nothing — and `status`, `list`, `verify`, and `recover --dry-run`
    still answer, so there is always a way to inspect what stopped it.

    Nothing actionable writes nothing. A `wait` remediation is a real answer and
    not an absence of one: a repair inside its retirement grace is deliberately
    waiting, and a recovery report describing a recovery that recovered nothing
    would be noise in the one directory an operator reads when the archive is
    already suspect.
    """
    plan = plan_recovery(layout, stale_staging_age_hours=stale_staging_age_hours, exclude=exclude)
    if plan.blocked:
        raise SafetyError(list(plan.problems))
    pending = tuple(
        sorted(entry.transaction_id for entry in plan.remediations if entry.remedy == "wait")
    )
    if not plan.actionable:
        return JournalReconciliation(resolved=(), pending=pending)
    report, applied = apply_recovery(layout, plan, envelope=envelope, started_at=started_at)
    return JournalReconciliation(
        resolved=tuple(
            sorted(record.transaction_id for record in applied if record.outcome == "applied")
        ),
        pending=pending,
        report=str(layout.archive_relative(report)),
    )


def _perform(
    layout: ArchiveLayout, entry: PlannedRemediation, transaction: Transaction
) -> Remediation:
    """Carry out one remedy and checkpoint it, or record that it was left alone.

    Each remedy re-performs the *original* transaction's remaining steps in its
    own journal, then closes that journal. `TX-04` makes that safe to repeat: a
    step whose evidence already holds is a no-op, so a `recover --apply` that
    itself crashes half way leaves work the next one finishes.
    """
    identifier = TransactionId(entry.transaction_id)
    if entry.remedy == "wait":
        return Remediation(
            outcome="pending", reason=entry.reason, remedy=entry.remedy, transaction_id=identifier
        )
    evidence = _REMEDIES.get(entry.remedy, _nothing)(layout, identifier)
    _close_resolved(layout, identifier, entry)
    transaction.checkpoint(entry.remedy, resolved_transaction_id=entry.transaction_id, **evidence)
    return Remediation(
        evidence=evidence,
        outcome="applied",
        reason=entry.reason,
        remedy=entry.remedy,
        transaction_id=identifier,
    )


def _nothing(_layout: ArchiveLayout, _transaction_id: TransactionId) -> dict[str, Any]:
    """`close_journal` changes no filesystem state; only the journal closes."""
    return {}


def _quarantine(layout: ArchiveLayout, transaction_id: TransactionId) -> dict[str, Any]:
    """Move abandoned staging into `.store/quarantine/<txn>/`, never delete it.

    A rename rather than a removal, because the staging tree is evidence of what
    a crashed run had built and §7.8 retains it until an operator says otherwise.
    """
    staging = layout.staging_for(transaction_id).directory
    destination = layout.quarantine_for(transaction_id)
    try:
        destination.parent.mkdir(mode=QUARANTINE_MODE, parents=True, exist_ok=True)
        staging.rename(destination)
        fsync_directory(layout.quarantine)
        fsync_directory(layout.staging)
    except OSError as exc:
        message = f"abandoned staging {staging} could not be quarantined: {exc.strerror}"
        raise RetentionError.single(
            message, code="HFRET010", location=str(layout.archive_relative(staging))
        ) from exc
    return {
        "quarantine_path": str(layout.archive_relative(destination)),
        "staging_absent": str(layout.archive_relative(staging)),
    }


def _quarantine_tree(layout: ArchiveLayout, transaction_id: TransactionId) -> dict[str, Any]:
    """Preserve a published tree no surviving manifest can validate (§7.3 row 2).

    The tree is renamed into quarantine, never removed: it may hold the only copy
    of a revision, and the reason it cannot be published is that nothing can
    vouch for it — which is a reason to keep it for an operator, not to destroy
    it (`AD-16`, plan §16.5 item 12).
    """
    journal = read_journal(layout, layout.journal(transaction_id)).journal
    tree = _published_tree(layout, journal)
    destination = layout.quarantine_for(transaction_id)
    if tree is None or not tree.is_dir():  # pragma: no cover - the plan proved it is there
        return {}
    try:
        destination.parent.mkdir(mode=QUARANTINE_MODE, parents=True, exist_ok=True)
        tree.rename(destination)
        fsync_directory(layout.quarantine)
    except OSError as exc:
        message = f"the unvalidatable tree {tree} could not be quarantined: {exc.strerror}"
        raise RetentionError.single(
            message, code="HFRET010", location=str(layout.archive_relative(tree))
        ) from exc
    return {
        "quarantine_path": str(layout.archive_relative(destination)),
        "unvalidatable_tree_absent": str(layout.archive_relative(tree)),
    }


def _published_tree(layout: ArchiveLayout, journal: TransactionJournal) -> Path | None:
    """Where checkpoint 5 renamed the tree to, from its own evidence."""
    value = next(
        (
            checkpoint.evidence["published_tree_path"]
            for checkpoint in journal.checkpoints
            if isinstance(checkpoint.evidence.get("published_tree_path"), str)
        ),
        None,
    )
    if value is None:  # pragma: no cover - checkpoint 5 is what makes this remedy reachable
        return None
    return layout.resolve(value, code="HFTXN003")


def _complete_publication(layout: ArchiveLayout, transaction_id: TransactionId) -> dict[str, Any]:
    """Finish §7.3 from wherever it stopped, having validated the tree first.

    Validation comes first and is not optional: §7.3's whole reason for writing
    the pending manifest into staging *before* the rename is so that a tree found
    at checkpoint 5 can be checked against something. A tree that does not match
    is never referenced — recovery reports it and changes nothing (`AD-16`).

    Steps 6 through 9 are then re-performed unconditionally rather than resumed
    from the recorded checkpoint. Each is an atomic write of a value derived from
    the manifest, so re-doing one that already happened writes the same bytes to
    the same place (`TX-04`), and deciding *which* to skip would be one more
    thing to get wrong.
    """
    journal = read_journal(layout, layout.journal(transaction_id)).journal
    manifest = _publication_manifest(layout, journal)
    if manifest is None:  # pragma: no cover - the plan chose quarantine instead
        return {}
    identity = manifest.identity
    repository = RepositoryLayout(archive=layout, identity=identity)
    commit = CommitSha(manifest.commit_sha)
    publication = PublicationId(manifest.publication_id)
    instance = repository.instance(commit, publication)

    findings = verify_target(
        VerificationTarget(
            identity=identity,
            reference=_reference_for(repository, manifest),
            manifest=manifest,
            tree=instance,
        ),
        ReadSet(),
    )
    if findings:
        raise SafetyError(
            [
                Problem(
                    code="HFTXN003",
                    message=(
                        f"the published tree {layout.archive_relative(instance)} does not match "
                        f"its manifest at {finding.path}: {finding.kind}; an unvalidated tree is "
                        f"never referenced"
                    ),
                    location=str(layout.archive_relative(instance)),
                )
                for finding in findings
            ]
        )

    published_manifest = repository.manifest(commit, publication)
    published_manifest.parent.mkdir(mode=PUBLISHED_DIRECTORY_MODE, parents=True, exist_ok=True)
    write_model(
        published_manifest,
        manifest,
        mode=PUBLISHED_FILE_MODE,
        code="HFRET010",
        error=RetentionError,
    )
    reference = _reference_for(repository, manifest)
    publish_revision_reference(layout, reference)
    publish_current_if_newest(layout, identity, reference)
    publish_catalog(layout, rebuild_catalog(layout, generated_at=datetime.now(UTC)))
    # The transaction's own last act, performed here for the same reason the rest
    # of steps 6-9 are (decision 56): a completion that left staging behind would
    # leave the finished publication reading as unfinished work forever, and this
    # is the only place that will ever run those steps for this transaction.
    discard_staging(layout, transaction_id)
    return {
        "published_tree_path": str(layout.archive_relative(instance)),
        "publication_id": manifest.publication_id,
    }


def _reference_for(repository: RepositoryLayout, manifest: RevisionManifest) -> Reference:
    """The reference a published manifest implies, field for field."""
    commit = CommitSha(manifest.commit_sha)
    publication = PublicationId(manifest.publication_id)
    return Reference(
        commit_sha=commit,
        manifest=str(repository.manifest_reference(commit, publication)),
        publication_generation=manifest.publication_generation,
        publication_id=publication,
        repository_id=manifest.repository_id,
        repository_type=manifest.repository_type,
        tree=str(repository.tree_reference(commit, publication)),
        updated_at=manifest.published_at,
    )


def publish_current_if_newest(
    layout: ArchiveLayout, identity: RepositoryIdentity, reference: Reference
) -> bool:
    """Replace `current.json` only when this is the repository's newest revision.

    §7.3 row 4's own condition, and it compares immutable *generations* rather
    than modification times — which §7.7 forbids recovery from using to choose a
    current revision. An older revision rolled forward is retained and
    discoverable without becoming what consumers are pointed at, which is
    exactly what the row says.
    """
    generations = [held.publication_generation for held in retained_references(layout, identity)]
    if generations and reference.publication_generation < max(generations):
        return False
    publish_current_reference(layout, reference)
    return True


def _rollback_prune(layout: ArchiveLayout, transaction_id: TransactionId) -> dict[str, Any]:
    """Put the sixth revision back (§7.4, before the commit point).

    Every step is the inverse of one the prune performed, in reverse order, and
    each tolerates not having been needed: a rollback from checkpoint 2 finds the
    tree still published and the reference still there, and does nothing to
    either. Over-retention is reportable; a deletion is not reversible (`TX-06`).
    """
    journal = read_journal(layout, layout.journal(transaction_id)).journal
    plan = _prune_plan(journal)
    if isinstance(plan, PurgePlan):
        return rollback_purge(layout, plan, transaction_id)
    identity = RepositoryIdentity.of(plan.repository_type, plan.repository_id)
    repository = RepositoryLayout(archive=layout, identity=identity)
    commit = CommitSha(plan.selected.commit_sha)
    publication = PublicationId(plan.selected.publication_id)
    trash = layout.trash_for(transaction_id)

    _restore(
        trash.manifest, repository.manifest(commit, publication), mode=PUBLISHED_DIRECTORY_MODE
    )
    _restore(trash.tree, repository.instance(commit, publication), mode=PUBLISHED_DIRECTORY_MODE)
    manifest = read_model(
        repository.manifest(commit, publication),
        RevisionManifest,
        error=IntegrityError,
        code="HFVER007",
    )
    publish_revision_reference(layout, _reference_for(repository, manifest))
    publish_catalog(layout, rebuild_catalog(layout, generated_at=datetime.now(UTC)))
    if trash.directory.is_dir() and not any(trash.directory.iterdir()):
        trash.directory.rmdir()
        fsync_directory(layout.trash)
    return {
        "restored_tree_path": str(
            layout.archive_relative(repository.instance(commit, publication))
        ),
        "commit_sha": plan.selected.commit_sha,
    }


def _complete_prune(layout: ArchiveLayout, transaction_id: TransactionId) -> dict[str, Any]:
    """Finish the post-commit cleanup a prune deferred (§7.4, at or after 7).

    Never republishes. Five revisions are what consumers already see and the
    archive recorded that decision at checkpoint 7; re-adding the sixth would
    contradict it. What is left is the audit record and the physical removal of
    the tombstone, and both are idempotent.
    """
    journal = read_journal(layout, layout.journal(transaction_id)).journal
    plan = _prune_plan(journal)
    if isinstance(plan, PurgePlan):
        return complete_purge(layout, plan, transaction_id)
    identity = RepositoryIdentity.of(plan.repository_type, plan.repository_id)
    repository = RepositoryLayout(archive=layout, identity=identity)
    commit = CommitSha(plan.selected.commit_sha)
    publication = PublicationId(plan.selected.publication_id)
    trash = layout.trash_for(transaction_id)

    audit = repository.pruned_records(commit)
    audit.mkdir(mode=REPORT_DIRECTORY_MODE, parents=True, exist_ok=True)
    archived = repository.pruned_manifest(commit, publication)
    if trash.manifest.is_file() and not archived.is_file():
        # Byte for byte, exactly as the prune would have: it is the evidence of
        # what was there, and this release's rendering of it is not the bytes the
        # archive published (`FS-06`).
        atomic_write_bytes(archived, trash.manifest.read_bytes(), mode=REPORT_MODE)
        fsync_directory(audit)
    record = repository.prune_record(commit, publication)
    if not record.is_file():
        # The timestamps are recovery's own clock, and honestly so: they record
        # when the record was written, which is when this ran (§9.1).
        write_model(
            record,
            _pruned_record(plan, transaction_id=transaction_id, now=datetime.now(UTC)),
            mode=REPORT_MODE,
            code="HFRET010",
            error=RetentionError,
        )
        fsync_directory(audit)
    if trash.directory.is_dir():
        shutil.rmtree(trash.directory)
        fsync_directory(layout.trash)
    # §7.4 checkpoint 10, and the reason it sits after the commit point: a prune
    # that stopped anywhere between 7 and 10 has already emptied both containers
    # and will never put the revision back, so removing them is exactly the
    # "only post-commit cleanup is retried later" this remedy exists to perform.
    # `remove_empty_containers` is idempotent by construction, which is what lets
    # this run after a prune that already did it (`TX-04`).
    containers = remove_empty_containers(layout, repository, commit)
    return {
        "trash_absent": str(layout.archive_relative(trash.directory)),
        "commit_sha": plan.selected.commit_sha,
        "containers_absent": containers["removed"],
        "containers_retained": containers["retained"],
    }


def _pruned_record(
    plan: PrunePlan, *, transaction_id: TransactionId, now: datetime
) -> PrunedRevisionRecord:
    """The §9.1 record a prune writes at checkpoint 8, rebuilt from its plan."""
    return PrunedRevisionRecord(
        commit_sha=plan.selected.commit_sha,
        file_count=plan.selected.file_count,
        logical_bytes=plan.selected.logical_bytes,
        manifest_archived_at=now,
        plan_id=plan.plan_id,
        publication_generation=plan.selected.publication_generation,
        publication_id=plan.selected.publication_id,
        pruned_at=now,
        reason=plan.reason,
        repository_id=plan.repository_id,
        repository_type=plan.repository_type,
        retained_after=tuple(
            summary for summary in plan.retained if summary.commit_sha != plan.selected.commit_sha
        ),
        transaction_id=transaction_id,
        tree=plan.selected.tree,
    )


def _prune_plan(journal: TransactionJournal) -> PrunePlan | PurgePlan:
    """The validated plan checkpoint 1 persisted, which names everything else."""
    payload = next(
        (
            checkpoint.evidence["plan"]
            for checkpoint in journal.checkpoints
            if isinstance(checkpoint.evidence.get("plan"), dict)
        ),
        None,
    )
    # Unreachable through the prune itself: checkpoint 1 is the first thing
    # `apply_prune` records, and `checkpoint_order_problems` refuses a journal
    # whose names are not a prefix of the documented sequence. Kept because a
    # `KeyError` from the middle of a rollback is the worst way to learn that.
    if payload is None:  # pragma: no cover - checkpoint 1 is a prune's first act
        message = f"prune journal {journal.transaction_id} records no plan; it cannot be resolved"
        raise SafetyError.single(message, code="HFTXN003", location=str(journal.transaction_id))
    if payload.get("reason") == "operator_requested_repository_purge":
        return PurgePlan.model_validate(payload)
    return PrunePlan.model_validate(payload)


def _restore(source: Path, destination: Path, *, mode: int) -> None:
    """Move a tombstoned artifact back, tolerating it never having gone."""
    try:
        destination.parent.mkdir(mode=mode, parents=True, exist_ok=True)
        if source.exists() and not destination.exists():
            source.rename(destination)
        fsync_directory(destination.parent)
    except OSError as exc:
        message = f"{source} could not be restored to {destination}: {exc.strerror}"
        raise RetentionError.single(message, code="HFRET005", location=str(destination)) from exc


def _complete_repair(layout: ArchiveLayout, transaction_id: TransactionId) -> dict[str, Any]:
    """Finish a repair's reference switches and the steps after them (§7.5).

    §7.5's interesting case is a crash between 9 and 10: the per-SHA reference
    names the new instance while `current.json` still names the old one. Both
    trees exist — the old one is inside its grace period — so `FS-10` holds, no
    consumer sees a dangling reference, and the resolution is simply to complete
    the second switch.

    The replacement is re-verified before either reference moves, for the same
    reason checkpoint 8 does it: a reference only ever switches to an instance
    that has been verified where it now lives.
    """
    journal = read_journal(layout, layout.journal(transaction_id)).journal
    manifest = _publication_manifest(layout, journal)
    if manifest is None:
        message = (
            f"repair {transaction_id} published no replacement manifest, so there is nothing "
            f"to switch a reference to; the original revision is unchanged"
        )
        raise SafetyError.single(message, code="HFTXN004", location=str(transaction_id))
    identity = manifest.identity
    repository = RepositoryLayout(archive=layout, identity=identity)
    commit = CommitSha(manifest.commit_sha)
    publication = PublicationId(manifest.publication_id)
    reference = _reference_for(repository, manifest)
    findings = verify_target(
        VerificationTarget(
            identity=identity,
            reference=reference,
            manifest=manifest,
            tree=repository.instance(commit, publication),
        ),
        ReadSet(),
    )
    if findings:
        raise SafetyError(
            [
                Problem(
                    code="HFTXN003",
                    message=(
                        f"the repair replacement fails verification at {finding.path}: "
                        f"{finding.kind}; no reference is switched to it"
                    ),
                    location=str(transaction_id),
                )
                for finding in findings
            ]
        )
    publish_revision_reference(layout, reference)
    if _current_names(layout, repository, commit):
        publish_current_reference(layout, reference)
    publish_catalog(layout, rebuild_catalog(layout, generated_at=datetime.now(UTC)))
    return {
        "revision_ref_path": str(layout.archive_relative(repository.revision_ref(commit))),
        "publication_id": manifest.publication_id,
    }


def _current_names(layout: ArchiveLayout, repository: RepositoryLayout, commit: CommitSha) -> bool:
    """Whether `current.json` names this SHA, and so has to move with it.

    A repository with no current reference has never completed a publication, so
    there is nothing for a repair to switch — the answer is no rather than an
    error.
    """
    if not repository.current_ref.is_file():  # pragma: no cover - a repair implies a publication
        return False
    return read_reference(layout, repository.current_ref).commit_sha == commit


def _finish_repair_cleanup(layout: ArchiveLayout, transaction_id: TransactionId) -> dict[str, Any]:
    """Run §7.5's checkpoints 16-18 in this recovery's own journal.

    The checkpoints belong to the repair transaction, and the repair's journal is
    resumed to record them — the same journal `repair_revision` left open for
    exactly this. Recovery's own journal records that it did so, which is how a
    reader of either can reconstruct the sequence.
    """
    pending = _pending_for(layout, transaction_id)
    if pending is None:  # pragma: no cover - the plan proved there is one
        return {}
    resumed = Transaction(layout=layout, file=read_journal(layout, layout.journal(transaction_id)))
    return finish_cleanup(layout, resumed, pending)


_REMEDIES: Final[Mapping[str, Callable[[ArchiveLayout, TransactionId], dict[str, Any]]]] = {
    "quarantine_staging": _quarantine,
    "quarantine_tree": _quarantine_tree,
    "complete_publication": _complete_publication,
    "rollback_prune": _rollback_prune,
    "complete_prune": _complete_prune,
    "complete_repair": _complete_repair,
    "finish_repair_cleanup": _finish_repair_cleanup,
}
"""Each remedy's implementation, so `_perform` dispatches rather than branches."""


COMPLETING: Final = frozenset(
    {
        "close_journal",
        "complete_publication",
        "complete_prune",
        "complete_repair",
        "finish_repair_cleanup",
    }
)
"""Remedies that carried a transaction to the end it was working towards.

The rest — quarantining staging, quarantining an unvalidatable tree, rolling a
prune back — resolved the transaction by *undoing* it, and a journal that says
`committed` about work that was undone would misdescribe the archive to the next
reader.
"""


def _close_resolved(
    layout: ArchiveLayout, transaction_id: TransactionId, entry: PlannedRemediation
) -> None:
    """Close the journal recovery just resolved, so a second run finds nothing.

    `committed` when the remedy finished what the transaction was doing, and
    `failed` when it undid it. Both are conclusions; the distinction is what an
    operator reading the journal afterwards needs, because "the revision was
    published in the end" and "the revision was never published" are the two
    different things a roll-forward and a roll-back leave behind.
    """
    file = read_journal(layout, layout.journal(transaction_id))
    resumed = Transaction(layout=layout, file=file)
    if entry.remedy in COMPLETING:
        resumed.commit()
    else:
        resumed.fail("HFTXN003", f"resolved by recovery: {entry.reason}")


def _write_report(
    path: Path,
    applied: list[Remediation],
    *,
    envelope: Mapping[str, Any],
    run_id: RunId,
    started_at: datetime,
) -> None:
    """Persist what recovery did, where every other run report lives (§12)."""
    report = RecoveryReport.model_validate(
        dict(envelope)
        | {
            "command": "recover --apply",
            "completed_at": datetime.now(UTC),
            "exit_code": int(ExitCode.SUCCESS),
            "outcome": "success",
            "remediations": sorted(applied, key=lambda record: record.transaction_id),
            "run_id": run_id,
            "started_at": started_at,
        }
    )
    path.parent.mkdir(mode=QUARANTINE_MODE, parents=True, exist_ok=True)
    write_model(path, report, mode=REPORT_MODE, code="HFRET010", error=RetentionError)
