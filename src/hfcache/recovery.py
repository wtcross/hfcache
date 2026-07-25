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

from dataclasses import dataclass
from datetime import UTC, datetime
from functools import partial
from typing import TYPE_CHECKING, Any, Final, Literal, final

from hfcache.errors import ExitCode, Problem, RetentionError, SafetyError
from hfcache.identity import OPAQUE_ID_LENGTH, TransactionId, new_run_id, new_transaction_id
from hfcache.reporting import RecoveryReport, Remediation
from hfcache.storage import (
    BYTES_PER_GIB,
    describe_capacity,
    effective_reserve,
    fsync_directory,
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

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from hfcache.config import StorageConfig
    from hfcache.identity import RunId
    from hfcache.models import TransactionJournal
    from hfcache.paths import ArchiveLayout
    from hfcache.transactions import JournalFile

__all__ = [
    "BLOCKED",
    "QUARANTINE_MODE",
    "REPORT_MODE",
    "SECONDS_PER_HOUR",
    "ArchiveHealth",
    "AreaFinding",
    "PlannedRemediation",
    "Reconciliation",
    "RecoveryPlan",
    "Remedy",
    "apply_recovery",
    "measure_health",
    "plan_recovery",
    "reconcile_storage",
]

SECONDS_PER_HOUR: Final = 3600

QUARANTINE_MODE: Final = 0o700
"""Quarantine and `runs/` are private to the writer (§5.2)."""

REPORT_MODE: Final = 0o600
"""A run report is the writer's record, not consumer data."""

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
    return [
        Problem(
            code="HFWRN002",
            message=(
                f"{finding.path} is a prune tombstone whose physical removal is outstanding; "
                f"the revision is logically pruned and the bytes are still on the dataset"
            ),
            location=finding.path,
        )
        for finding in findings
        if finding.area == ".store/trash"
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

Remedy = Literal["quarantine_staging", "close_journal", "operator", "wait"]
"""What recovery proposes to do about one unfinished transaction.

`wait` is a real answer, not an absence of one: a staging directory younger than
`sync.stale_staging_age_hours` may belong to work an operator started, and §7.8
requires all three of name, journal, and age before anything is acted on.
"""

BLOCKED: Final = "operator"


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
        return tuple(
            entry
            for entry in self.remediations
            if entry.remedy in {"quarantine_staging", "close_journal"}
        )

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
) -> RecoveryPlan:
    """Decide what to do about every unfinished journal, without touching anything.

    This is `recover --dry-run` in full, and the analysis a mutating command runs
    before it acts (`TX-07`). Every journal is validated first — schema, then
    checkpoint order, then evidence against the filesystem — because a journal
    that cannot be trusted is not a journal a remedy may be chosen from.
    """
    moment = datetime.now(UTC) if now is None else now
    return RecoveryPlan(
        remediations=tuple(
            _remediation(layout, file, stale_staging_age_hours=stale_staging_age_hours, now=moment)
            for file in open_journals(layout)
        )
    )


def _remediation(
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

    if journal.operation == "publication" and _before_the_tree_was_renamed(names):
        return _staging_remediation(
            layout, journal, last, stale_staging_age_hours=stale_staging_age_hours, now=now
        )

    message = (
        f"transaction {journal.transaction_id} is a {journal.operation} that stopped after "
        f"{last!r}; resolving it needs evidence recovery cannot obtain on its own"
    )
    return blocked(
        reason=f"no unambiguous resolution for a {journal.operation} at {last!r}",
        problems=(Problem(code="HFTXN004", message=message, location=str(journal.transaction_id)),),
    )


def _before_the_tree_was_renamed(names: list[str]) -> bool:
    """Whether a publication crashed before checkpoint 5 (§7.3 crash matrix).

    Before the rename nothing published changed, so rolling back is always
    correct. At or after it a tree exists and the resolution is to roll forward,
    which needs the manifest machinery that publishes it.
    """
    return "revision_tree_renamed" not in names


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


def _perform(
    layout: ArchiveLayout, entry: PlannedRemediation, transaction: Transaction
) -> Remediation:
    """Carry out one remedy and checkpoint it, or record that it was left alone."""
    identifier = TransactionId(entry.transaction_id)
    if entry.remedy == "wait":
        return Remediation(
            outcome="pending", reason=entry.reason, remedy=entry.remedy, transaction_id=identifier
        )
    evidence: dict[str, Any] = {}
    if entry.remedy == "quarantine_staging":
        evidence = _quarantine(layout, identifier)
    _close_resolved(layout, identifier, entry)
    transaction.checkpoint(entry.remedy, resolved_transaction_id=entry.transaction_id, **evidence)
    return Remediation(
        evidence=evidence,
        outcome="applied",
        reason=entry.reason,
        remedy=entry.remedy,
        transaction_id=identifier,
    )


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


def _close_resolved(
    layout: ArchiveLayout, transaction_id: TransactionId, entry: PlannedRemediation
) -> None:
    """Close the journal recovery just resolved, so a second run finds nothing."""
    file = read_journal(layout, layout.journal(transaction_id))
    resumed = Transaction(layout=layout, file=file)
    if entry.remedy == "close_journal" and _is_complete(file.journal):
        resumed.commit()
    else:
        resumed.fail("HFTXN003", f"resolved by recovery: {entry.reason}")


def _is_complete(journal: TransactionJournal) -> bool:
    """Whether every documented checkpoint for this operation was recorded."""
    names = [checkpoint.name for checkpoint in journal.checkpoints]
    return journal.operation in CHECKPOINTS and names == list(CHECKPOINTS[journal.operation])


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
    write_model(path, report, mode=REPORT_MODE, code="HFRET010")
