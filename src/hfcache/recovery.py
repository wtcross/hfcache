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
own — reclamation will also require a journal — but it is what stops a concurrent
operator command from having its working directory pulled out from under it
(`docs/progress.md` decision 5).
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Final, final

from hfcache.errors import Problem
from hfcache.identity import OPAQUE_ID_LENGTH
from hfcache.storage import BYTES_PER_GIB, describe_capacity, effective_reserve

if TYPE_CHECKING:
    from hfcache.config import StorageConfig
    from hfcache.paths import ArchiveLayout

__all__ = [
    "SECONDS_PER_HOUR",
    "ArchiveHealth",
    "AreaFinding",
    "Reconciliation",
    "measure_health",
    "reconcile_storage",
]

SECONDS_PER_HOUR: Final = 3600

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
