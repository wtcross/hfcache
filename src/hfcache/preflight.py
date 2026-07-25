"""The ordered safety checks, and the gate every mutating command passes.

`docs/plan.md` §19 lists what a mutating command must verify; `docs/cli.md` §2
gives the same list as the named checks `doctor` reports. They are one table, so
they are implemented once, here, and consumed twice:

* `doctor` renders whatever the runner produced, including what it could not
  prove and why, and exits `20` if anything failed.
* a mutating command calls `require_storage_safety`, which raises `SafetyError`
  carrying *every* problem the runner found rather than the first one — an
  operator fixing a deployment should learn everything wrong with it in one run.

The distinction that makes one runner serve both is what a **skipped** check
means. Three things can stop a check from running, and only one of them lets a
mutating command proceed:

* `--read-only` — the operator asked that nothing be written. A mutating command
  never runs in this mode, so the gate never sees these.
* the archive is not initialized — operator state that `archive init` changes.
  `doctor` reports it and still exits `0`; the gate refuses, because a mutating
  command may not assume a check would have passed. The `sentinel` check owns
  this condition and is the only one that reports it, so one missing archive is
  one problem rather than one per check that needed it.
* an earlier check failed — nothing can be said about the filesystem type of a
  path that does not exist. The gate adds nothing for these, because the failure
  that caused them is already in the same report.

A check is **absent** until the package that performs it lands, rather than
being reported as passed or skipped (`docs/progress.md` decision 24). The order
of those that are present is the table's, taken from `CHECK_ORDER` rather than
from the order this module happens to build them in.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Final, Literal, Self, final

from hfcache.errors import Problem, SafetyError
from hfcache.storage import (
    BYTES_PER_GIB,
    capacity_problems,
    capacity_warnings,
    describe_capacity,
    describe_mount,
    effective_reserve,
    is_initialized,
    mount_problems,
    probe_writability,
    publication_destinations,
    read_sentinel,
    same_filesystem_problems,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from hfcache.config import StorageConfig
    from hfcache.paths import ArchiveLayout
    from hfcache.storage import MountEntry, MountFacts

__all__ = [
    "CHECK_ORDER",
    "NOT_INITIALIZED",
    "READ_ONLY",
    "UNPROVABLE_READ_ONLY",
    "Check",
    "order_checks",
    "require_storage_safety",
    "storage_checks",
]

CHECK_ORDER: Final = (
    "configuration",
    "archive_root",
    "mount_point",
    "filesystem_type",
    "mount_writable",
    "sentinel",
    "directory_writability",
    "staging_filesystem",
    "hardlink_capability",
    "atomic_directory_rename",
    "reference_replacement",
    "free_space",
    "credential",
    "hub_endpoint",
    "hub_dns",
    "hub_tls",
    "hub_identity",
)
"""Every check name, in the normative order of the `docs/cli.md` §2 table.

Automation keys on these names and `status` quotes them, so both the spelling
and the sequence are contract. `tests/unit/test_preflight.py` parses the table
out of the document and asserts this tuple against it, in both directions, so
the two cannot drift.
"""

UNPROVABLE_READ_ONLY: Final = (
    "directory_writability",
    "hardlink_capability",
    "atomic_directory_rename",
    "reference_replacement",
)
"""What `--read-only` cannot establish — every row the table marks as writing.

`docs/cli.md` §2 requires these to be reported as unproven rather than passed:
each one is a capability that can only be demonstrated by performing it, and a
mount that must not be touched is a mount on which they are unknown.
"""

READ_ONLY: Final = "--read-only: this capability can only be proven by exercising it"
NOT_INITIALIZED: Final = (
    "the archive is not initialized, so the layout this check needs does not exist; "
    "`archive init` is what changes that"
)
_UNPROVEN: Final = (
    "the archive root was not proven to be a read/write NFS mount, so nothing was read "
    "from it or written to it"
)


@final
@dataclass(frozen=True, slots=True)
class Check:
    """One check and what it proved (`docs/cli.md` §4.1).

    `problems` is what failed, and is empty for anything but a `fail`.
    `warnings` is what a check noticed while passing — free space above the
    reserve but not by much — and never changes an exit code on its own
    (`docs/cli.md` §5.6).

    `blocking_code` is set only on a skip that a mutating command may not proceed
    past; the gate turns it into a problem under that code, and `doctor` ignores
    it, which is the whole difference between the two consumers.
    """

    name: str
    outcome: Literal["pass", "fail", "skipped"]
    detail: str
    problems: tuple[Problem, ...] = ()
    warnings: tuple[Problem, ...] = ()
    blocking_code: str | None = None

    @classmethod
    def passed(cls, name: str, detail: str, *, warnings: Sequence[Problem] = ()) -> Self:
        """Record a check that ran and proved what it set out to."""
        return cls(name=name, outcome="pass", detail=detail, warnings=tuple(warnings))

    @classmethod
    def failed(cls, name: str, problems: Sequence[Problem]) -> Self:
        """Record a check that ran and did not pass.

        The detail is the problems' own messages, so the human table and the
        envelope's `errors` array say the same thing rather than two things.
        """
        return cls(
            name=name,
            outcome="fail",
            detail="; ".join(problem.message for problem in problems),
            problems=tuple(problems),
        )

    @classmethod
    def skipped(cls, name: str, reason: str, *, blocking_code: str | None = None) -> Self:
        """Record a check that did not run, and say why."""
        return cls(name=name, outcome="skipped", detail=reason, blocking_code=blocking_code)

    def as_entry(self) -> dict[str, Any]:
        """Render in the documented `checks[]` shape."""
        return {"detail": self.detail, "name": self.name, "outcome": self.outcome}


def order_checks(checks: Iterable[Check]) -> tuple[Check, ...]:
    """Put checks into the normative order, whatever order they were produced in.

    Sorting by the table rather than appending in code order is what keeps the
    emitted sequence correct as packages land out of order: `credential` and
    `hub_endpoint` were built first and belong at positions 13 and 14, and
    nothing had to move when the storage checks arrived between them.
    """
    return tuple(sorted(checks, key=lambda check: CHECK_ORDER.index(check.name)))


def storage_checks(
    layout: ArchiveLayout,
    *,
    storage: StorageConfig,
    needed_bytes: int = 0,
    read_only: bool = False,
    table: Sequence[MountEntry] | None = None,
) -> list[Check]:
    """Run every storage check that exists today: `docs/cli.md` §2 rows 2-8 and 12.

    Rows 9-11 are absent until `STO-007` and `STO-009` land. The whole
    `[storage]` table is taken rather than the two or three fields used today,
    because these checks are the code that reads that table: `archive_id` for the
    sentinel, the two free-space minimums for the reserve, and `publication_mode`
    for the hardlink check when it arrives.

    `table` is the parsed mount table, supplied by tests so a temporary directory
    can stand in for the NFS archive; production reads the kernel's.
    """
    facts = describe_mount(layout.root, table=table)
    checks = _mount_checks(facts)
    proven = all(check.outcome == "pass" for check in checks)
    checks.append(_sentinel_check(layout, archive_id=storage.archive_id, proven=proven))
    checks.append(_writability_check(layout, proven=proven, read_only=read_only))
    checks.append(_staging_check(layout, proven=proven))
    if proven:
        checks.append(_capacity_check(layout, storage, needed_bytes=needed_bytes))
    else:
        checks.append(Check.skipped("free_space", _UNPROVEN))
    return checks


def _mount_checks(facts: MountFacts) -> list[Check]:
    """Split plan §19's first four requirements into the four checks that report them.

    `mount_problems` short-circuits — nothing can be said about the filesystem
    type of a path that is not a mount point — so the checks it could not reach
    are reported as skipped rather than passed. Saying "pass" for a requirement
    that was never evaluated is the one answer that would be wrong.
    """
    problems = mount_problems(facts)
    where = str(facts.path)
    unreached = [
        Check.skipped(name, _UNPROVEN)
        for name in ("mount_point", "filesystem_type", "mount_writable")
    ]

    if not facts.is_directory:
        # `HFMNT001` for absent, `HFMNT015` for a symlink or a non-directory:
        # both are answers to "is there an archive root here", which is what
        # this check asks.
        return [Check.failed("archive_root", problems), *unreached]

    exists = Check.passed("archive_root", f"{where} exists and is a directory")
    entry = facts.entry
    if entry is None:
        return [exists, Check.failed("mount_point", problems), *unreached[1:]]

    is_mount = Check.passed("mount_point", f"{where} is a mount point of {entry.source}")
    kind = [problem for problem in problems if problem.code == "HFMNT003"]
    writable = [problem for problem in problems if problem.code == "HFMNT004"]
    return [
        exists,
        is_mount,
        Check.failed("filesystem_type", kind)
        if kind
        else Check.passed("filesystem_type", f"{entry.filesystem_type} from {entry.source}"),
        Check.failed("mount_writable", writable)
        if writable
        else Check.passed("mount_writable", "mounted read/write"),
    ]


def _sentinel_check(layout: ArchiveLayout, *, archive_id: str, proven: bool) -> Check:
    """`doctor` check 6 — the archive's identity, and whether it is this one.

    This is the check that owns "there is no archive here": it is the sentinel's
    absence, and the sentinel is written last, so nothing below it can be said
    either (`FS-23`). Checks 7 and 8 therefore skip on the same condition without
    reporting it again — one missing archive is one problem, not three.
    """
    name = "sentinel"
    if not proven:
        return Check.skipped(name, _UNPROVEN)
    if not is_initialized(layout):
        return Check.skipped(name, NOT_INITIALIZED, blocking_code="HFMNT005")
    try:
        sentinel, problems = read_sentinel(layout, archive_id=archive_id)
    except SafetyError as error:
        # Unreadable, malformed, or from a release this one does not understand.
        # `read_sentinel` raises rather than returns for these because a caller
        # that wanted the sentinel has nothing to go on; here the answer is the
        # check's own outcome.
        return Check.failed(name, error.problems)
    if problems:
        return Check.failed(name, problems)
    return Check.passed(name, f"{layout.sentinel} names archive {sentinel.archive_id}")


def _writability_check(layout: ArchiveLayout, *, proven: bool, read_only: bool) -> Check:
    """`doctor` check 7 — the only proof of effective writability there is."""
    name = "directory_writability"
    if read_only:
        return Check.skipped(name, READ_ONLY)
    if not proven:
        return Check.skipped(name, _UNPROVEN)
    if not is_initialized(layout):
        return Check.skipped(name, NOT_INITIALIZED)
    problems = probe_writability(layout)
    if problems:
        return Check.failed(name, problems)
    return Check.passed(name, f"create, fsync, rename, and delete succeeded under {layout.health}")


def _staging_check(layout: ArchiveLayout, *, proven: bool) -> Check:
    """`doctor` check 8 — `FS-04`, proven by `stat(2)` and nothing else."""
    name = "staging_filesystem"
    if not proven:
        return Check.skipped(name, _UNPROVEN)
    if not is_initialized(layout):
        return Check.skipped(name, NOT_INITIALIZED)
    problems = same_filesystem_problems(layout)
    if problems:
        return Check.failed(name, problems)
    destinations = len(publication_destinations(layout))
    return Check.passed(
        name, f"staging and {destinations} publication destinations share one filesystem"
    )


def _capacity_check(layout: ArchiveLayout, storage: StorageConfig, *, needed_bytes: int) -> Check:
    """`doctor` check 12 — free capacity against the need plus the reserve.

    Unlike checks 6-11 this does not need an initialized archive: `statvfs` on a
    proven mount answers whether there is room, and an operator sizing a dataset
    before running `archive init` is exactly who wants the answer
    (`docs/progress.md` decision 39).
    """
    name = "free_space"
    try:
        facts = describe_capacity(layout.root)
    except SafetyError as error:
        return Check.failed(name, error.problems)
    reserve = effective_reserve(
        facts.total_bytes,
        minimum_gib=storage.minimum_free_space_gib,
        minimum_percent=storage.minimum_free_space_percent,
    )
    problems = capacity_problems(facts, reserve_bytes=reserve, needed_bytes=needed_bytes)
    if problems:
        return Check.failed(name, problems)
    warnings = capacity_warnings(facts, reserve_bytes=reserve, needed_bytes=needed_bytes)
    detail = (
        f"{_gib(facts.available_bytes)} free of {_gib(facts.total_bytes)}, reserve {_gib(reserve)}"
    )
    if warnings:
        detail = f"{detail} — approaching the reserve"
    return Check.passed(name, detail, warnings=warnings)


def _gib(value: int) -> str:
    """Render a byte count the way an operator sizing a dataset thinks about it."""
    return f"{value / BYTES_PER_GIB:.1f} GiB"


def require_storage_safety(
    layout: ArchiveLayout,
    *,
    storage: StorageConfig,
    needed_bytes: int = 0,
    table: Sequence[MountEntry] | None = None,
) -> tuple[Check, ...]:
    """Refuse to proceed unless every storage requirement is proven (plan §19).

    The hard gate every mutating command runs before it takes a lock or contacts
    the Hub. It raises with every problem at once, and it treats a check that did
    not run as a check that did not pass — the point of a gate is that nothing
    unproven gets through it, and `--read-only` is deliberately not an option
    here, because a command that is about to write has no business asking for it.

    `needed_bytes` is what this particular run intends to consume: the estimated
    download plus, in copy mode, the projected publication bytes. It defaults to
    zero for a caller that is only establishing that the archive is usable.
    """
    checks = order_checks(
        storage_checks(layout, storage=storage, needed_bytes=needed_bytes, table=table)
    )
    problems: list[Problem] = []
    for check in checks:
        problems.extend(check.problems)
        if check.blocking_code is not None:
            message = f"{check.name} was not proven: {check.detail}"
            problems.append(
                Problem(code=check.blocking_code, message=message, location=str(layout.root))
            )
    if problems:
        raise SafetyError(problems)
    return checks
