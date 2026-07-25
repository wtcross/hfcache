"""The one command that brings an archive into being, and the look that precedes it.

`archive init` is the only irreversible command this application has and the only
way the layout in `docs/architecture.md` §5.1 ever comes into existence
(`FS-21`). Everything here exists so that command can *refuse* rather than
guess:

* `hfcache.storage` proves the target is a read/write NFS mount before anything
  is created (`FS-02`),
* the tree is walked to prove it holds nothing the application did not put there
  (`FS-22`), and
* the sentinel is written last, so its presence proves the layout beneath it
  (`FS-23`).

The one adoption exception is a single pre-existing `published/` directory, which
TrueNAS requires to exist before the consumer export can be defined (§35.2). It
is adopted only when it is empty and its ownership and mode already match §5.2.

Nothing in this module deletes or rewrites anything outside the application's own
naming contracts (`FS-19`). The single removal it performs is a leftover
temporary sibling of the sentinel — an interrupted durable write of a file this
command owns — and it is reported before it happens.

Ownership is never proven by comparing a local uid against `st_uid`. The writer
export maps every client identity to `hfcache-sync:hfcache-archive`, so files on
the mount carry NAS-side ids with no local account (`docs/plan.md` §35.3);
`published/` is checked against the *archive root's* owner instead, which is the
same comparison in a form that holds under Mapall.
"""

import socket
import stat
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Final, Literal, final

from hfcache import __version__
from hfcache.errors import Problem, SafetyError
from hfcache.models import ArchiveSentinel, Provenance, dump
from hfcache.storage import (
    SENTINEL_MODE,
    atomic_write_bytes,
    describe_mount,
    fsync_directory,
    is_temporary_sibling,
    mount_problems,
    read_sentinel,
)

if TYPE_CHECKING:
    import os
    from collections.abc import Iterable, Sequence
    from pathlib import Path

    from hfcache.paths import ArchiveLayout
    from hfcache.storage import MountEntry, MountFacts

__all__ = [
    "REPORTED_ENTRY_LIMIT",
    "ArchiveInspection",
    "ArchiveState",
    "InitializationResult",
    "initialize_archive",
    "inspect_archive",
    "published_adoption_problems",
]

REPORTED_ENTRY_LIMIT: Final = 20
"""Cap on how many unrecognized entries one report names individually.

An `--archive-root` pointed at the wrong directory can contain any number of
files. The count is always exact; the enumeration is bounded so a refusal stays
readable.
"""


ArchiveState = Literal["uninitialized", "partially_initialized", "initialized", "unusable"]
"""What one look at the target found.

`uninitialized` — nothing of the layout is present beyond an adoptable
`published/`. `partially_initialized` — some of the layout exists and no sentinel
does, which is what an interrupted `archive init` leaves behind and what §6.2
permits a retry from. `initialized` — the sentinel and the whole layout are
present and the sentinel agrees with configuration. `unusable` — something is
present that this application did not put there, or the mount, the sentinel, or
`published/` fails a check; a retry cannot fix any of those without an operator.
"""


@final
@dataclass(frozen=True, slots=True)
class _Contents:
    """What a walk of the archive root found."""

    existing: tuple[Path, ...]
    unknown: tuple[str, ...]
    unknown_count: int
    symlinks: tuple[str, ...]
    temporaries: tuple[Path, ...]
    unreadable: tuple[str, ...]
    sentinel_present: bool


def _bounded(values: list[str]) -> tuple[str, ...]:
    """Keep a report readable when the target is the wrong directory entirely."""
    return tuple(sorted(values)[:REPORTED_ENTRY_LIMIT])


def _walk(layout: ArchiveLayout, known: Iterable[Path]) -> _Contents:
    """Enumerate the archive root, descending only into directories of the layout.

    Descent is bounded on purpose. An unknown directory is reported and not
    entered, so pointing `--archive-root` at a populated filesystem produces one
    refusal rather than a traversal of it.
    """
    expected = set(known)
    existing: list[Path] = []
    unknown: list[str] = []
    symlinks: list[str] = []
    temporaries: list[Path] = []
    unreadable: list[str] = []
    sentinel_present = False

    queue = [layout.root]
    while queue:
        directory = queue.pop(0)
        try:
            children = sorted(directory.iterdir())
        except OSError as exc:
            unreadable.append(f"{layout.archive_relative(directory)}: {exc.strerror}")
            continue
        for child in children:
            where = str(layout.archive_relative(child))
            if child.is_symlink():
                symlinks.append(where)
            elif child == layout.sentinel:
                sentinel_present = True
            elif is_temporary_sibling(child.name) and child.is_file():
                temporaries.append(child)
            elif child in expected and child.is_dir():
                existing.append(child)
                queue.append(child)
            else:
                unknown.append(where)
    return _Contents(
        existing=tuple(existing),
        unknown=_bounded(unknown),
        unknown_count=len(unknown),
        symlinks=_bounded(symlinks),
        temporaries=tuple(temporaries),
        unreadable=_bounded(unreadable),
        sentinel_present=sentinel_present,
    )


def published_adoption_problems(
    root: os.stat_result, published: os.stat_result, *, mode: int, location: str
) -> list[Problem]:
    """Decide whether a pre-existing `published/` may be adopted (`FS-22`).

    Ownership is compared against the *archive root*, never against a local uid.
    Under the Mapall writer export both carry NAS-side ids with no local account,
    so "the same identity owns both" is the only form of §5.2's ownership rule
    that can be evaluated from the writer (`docs/plan.md` §35.3).

    Taken as `os.stat_result` values rather than paths so the policy is separable
    from the syscall and can be exercised for identities this host cannot create.
    """
    problems: list[Problem] = []
    found = stat.S_IMODE(published.st_mode)
    if found != mode:
        message = (
            f"pre-existing {location} has mode {found:04o}, not {mode:04o}; it is adopted only "
            f"when it already matches, because its mode is what the consumer export relies on"
        )
        problems.append(Problem(code="HFMNT014", message=message, location=location))
    if (published.st_uid, published.st_gid) != (root.st_uid, root.st_gid):
        message = (
            f"pre-existing {location} is owned by {published.st_uid}:{published.st_gid} but the "
            f"archive root is owned by {root.st_uid}:{root.st_gid}; adoption requires the same "
            f"identity to own both"
        )
        problems.append(Problem(code="HFMNT014", message=message, location=location))
    return problems


@final
@dataclass(frozen=True, slots=True)
class ArchiveInspection:
    """A non-mutating answer to "can this be initialized, and is it already?"."""

    layout: ArchiveLayout
    mount: MountFacts
    state: ArchiveState
    sentinel: ArchiveSentinel | None
    adopted_published: bool
    existing_directories: tuple[str, ...]
    missing_directories: tuple[str, ...]
    unknown_entries: tuple[str, ...]
    unknown_entry_count: int
    leftover_temporaries: tuple[str, ...]
    problems: tuple[Problem, ...]

    @property
    def initializable(self) -> bool:
        """Whether `archive init --confirm` would proceed against this target."""
        return self.state in {"uninitialized", "partially_initialized"}

    def as_payload(self) -> dict[str, Any]:
        """Render for the `--json` envelope (`docs/cli.md` §4.1)."""
        return {
            "adopted_published": self.adopted_published,
            "archive_id": self.sentinel.archive_id if self.sentinel else None,
            "archive_root": str(self.layout.root),
            "existing_directories": list(self.existing_directories),
            "initializable": self.initializable,
            "leftover_temporaries": list(self.leftover_temporaries),
            "missing_directories": list(self.missing_directories),
            "mount": self.mount.as_payload(),
            "state": self.state,
            "unknown_entries": list(self.unknown_entries),
            "unknown_entry_count": self.unknown_entry_count,
        }


def _classify(
    *,
    problems: Sequence[Problem],
    sentinel_present: bool,
    existing: Sequence[str],
    adopted: bool,
) -> ArchiveState:
    """Name the state a walk found, given what it found and what it objected to."""
    if problems:
        return "unusable"
    if sentinel_present:
        return "initialized"
    # An adopted `published/` is the state TrueNAS leaves behind, not work this
    # application started, so a target holding only that is still uninitialized.
    started = [name for name in existing if not (adopted and name == "published")]
    return "partially_initialized" if started else "uninitialized"


def inspect_archive(
    layout: ArchiveLayout,
    *,
    archive_id: str,
    table: Sequence[MountEntry] | None = None,
) -> ArchiveInspection:
    """Describe the target without touching it (`archive init --inspect`).

    Every objection is collected rather than raised, so one report tells an
    operator everything that must change. The caller decides what a given state
    means: `--inspect` reports it, and `--confirm` refuses anything but
    `uninitialized` or `partially_initialized`.
    """
    mount = describe_mount(layout.root, table=table)
    problems = mount_problems(mount)
    if problems:
        return ArchiveInspection(
            layout=layout,
            mount=mount,
            state="unusable",
            sentinel=None,
            adopted_published=False,
            existing_directories=(),
            missing_directories=(),
            unknown_entries=(),
            unknown_entry_count=0,
            leftover_temporaries=(),
            problems=tuple(problems),
        )

    specs = layout.required_directories()
    contents = _walk(layout, (spec.path for spec in specs))
    existing = set(contents.existing)
    # Sorted, not in creation order: `docs/architecture.md` §5.3 requires every
    # generated array to be byte-wise ascending on the relative path. For these
    # names that also keeps parents ahead of their children, so a reader can
    # still follow the order a retry would create them in.
    missing = tuple(
        sorted(
            str(layout.archive_relative(spec.path)) for spec in specs if spec.path not in existing
        )
    )

    sentinel: ArchiveSentinel | None = None
    if contents.sentinel_present:
        sentinel, sentinel_problems = read_sentinel(layout, archive_id=archive_id)
        problems.extend(sentinel_problems)
        if missing:
            message = (
                f"the sentinel exists but {len(missing)} required directories do not; the "
                f"sentinel is written last, so this layout was not produced by initialization"
            )
            problems.append(
                Problem(
                    code="HFMNT008",
                    message=message,
                    location=str(layout.root),
                    context={"missing": list(missing)},
                )
            )

    adopted = layout.published in existing and not contents.sentinel_present
    if layout.published in existing:
        problems.extend(
            published_adoption_problems(
                layout.root.stat(),
                layout.published.stat(),
                mode=next(spec.mode for spec in specs if spec.path == layout.published),
                location=str(layout.archive_relative(layout.published)),
            )
        )
    problems.extend(_content_problems(layout, contents))

    existing_names = tuple(sorted(str(layout.archive_relative(path)) for path in existing))
    return ArchiveInspection(
        layout=layout,
        mount=mount,
        state=_classify(
            problems=problems,
            sentinel_present=contents.sentinel_present,
            existing=existing_names,
            adopted=adopted,
        ),
        sentinel=sentinel,
        adopted_published=adopted,
        existing_directories=existing_names,
        missing_directories=missing,
        unknown_entries=contents.unknown,
        unknown_entry_count=contents.unknown_count,
        leftover_temporaries=tuple(
            sorted(str(layout.archive_relative(path)) for path in contents.temporaries)
        ),
        problems=tuple(problems),
    )


def _content_problems(layout: ArchiveLayout, contents: _Contents) -> list[Problem]:
    """Turn unrecognized findings into refusals (`FS-19`, `FS-22`)."""
    root = str(layout.root)
    problems: list[Problem] = []
    for where in contents.symlinks:
        message = f"symlink at {where}; the application never creates one and never follows one"
        problems.append(Problem(code="HFMNT015", message=message, location=where))
    if contents.unknown_count:
        message = (
            f"{contents.unknown_count} entries under {root} are not part of the archive layout; "
            f"initialization refuses a target holding anything it did not create, and nothing "
            f"unrecognized is ever deleted"
        )
        problems.append(
            Problem(
                code="HFMNT014",
                message=message,
                location=root,
                context={
                    "entries": list(contents.unknown),
                    "entry_count": contents.unknown_count,
                },
            )
        )
    for detail in contents.unreadable:
        message = f"a directory of the layout could not be read: {detail}"
        problems.append(Problem(code="HFMNT008", message=message, location=root))
    return problems


# --------------------------------------------------------------------------- #
# Initialization
# --------------------------------------------------------------------------- #


@final
@dataclass(frozen=True, slots=True)
class InitializationResult:
    """What `archive init --confirm` created."""

    layout: ArchiveLayout
    sentinel: ArchiveSentinel
    created_directories: tuple[str, ...]
    adopted_published: bool
    removed_temporaries: tuple[str, ...]

    def as_payload(self) -> dict[str, Any]:
        """Render for the `--json` envelope (`docs/cli.md` §4.1)."""
        return {
            "adopted_published": self.adopted_published,
            "archive_id": self.sentinel.archive_id,
            "archive_root": str(self.layout.root),
            "created_directories": list(self.created_directories),
            "removed_temporaries": list(self.removed_temporaries),
            "sentinel": str(self.layout.archive_relative(self.layout.sentinel)),
        }


def initialize_archive(
    layout: ArchiveLayout,
    *,
    archive_id: str,
    table: Sequence[MountEntry] | None = None,
) -> InitializationResult:
    """Create the archive layout and write its sentinel, once (`FS-21`, `FS-23`).

    The target is inspected again here rather than trusted from the caller: the
    command that reported what it would do and the command that does it are
    separated by an operator reading the output, and this is the inspection whose
    result actually governs the mutation.
    """
    inspection = inspect_archive(layout, archive_id=archive_id, table=table)
    if inspection.problems:
        raise SafetyError(inspection.problems)
    if inspection.state == "initialized":
        message = (
            f"archive {layout.root} is already initialized; initialization happens once and "
            f"is never repeated, because a second sentinel would rename an existing archive"
        )
        raise SafetyError.single(message, code="HFMNT014", location=str(layout.root))

    try:
        return _create(layout, inspection, archive_id=archive_id)
    except OSError as exc:
        # A write can still fail after every check passed — a server-side
        # read-only export presents `rw` client options, a quota can be reached,
        # the NAS can go away mid-command. It becomes a coded exit `20` rather
        # than a traceback, and initialization is retryable because `--inspect`
        # recognises everything a half-finished attempt leaves behind.
        message = (
            f"initializing {layout.root} failed at {exc.filename or layout.root}: "
            f"{exc.strerror}; run `archive init --inspect` before retrying"
        )
        raise SafetyError.single(message, code="HFMNT008", location=str(layout.root)) from exc


def _create(
    layout: ArchiveLayout, inspection: ArchiveInspection, *, archive_id: str
) -> InitializationResult:
    """Perform the mutation itself, once every check has passed."""
    specs = layout.required_directories()
    existing = set(inspection.existing_directories)
    created: list[str] = []
    for spec in specs:
        name = str(layout.archive_relative(spec.path))
        if name not in existing:
            spec.path.mkdir(mode=spec.mode)
            created.append(name)
        elif spec.path == layout.published and inspection.adopted_published:
            # Adopted means adopted: its mode was verified to match already, and
            # leaving it untouched keeps this command's only claim on an
            # operator-created directory to a read (`FS-22`).
            continue
        # `mkdir(2)` masks the mode with the umask and drops setgid, so the mode
        # is restated rather than assumed. Restating it for a directory that
        # already existed is what repairs a crash between the two calls on an
        # earlier attempt; every directory here is empty and application-owned,
        # and nothing is consumer-visible until the sentinel exists.
        spec.path.chmod(spec.mode)

    removed: list[str] = []
    for leftover in inspection.leftover_temporaries:
        (layout.root / leftover).unlink(missing_ok=True)
        removed.append(leftover)

    for spec in specs:
        fsync_directory(spec.path)
    fsync_directory(layout.root)

    sentinel = ArchiveSentinel(
        archive_id=archive_id,
        created_at=datetime.now(UTC),
        created_by=Provenance(application_version=__version__, hostname=socket.gethostname()),
    )
    atomic_write_bytes(layout.sentinel, dump(sentinel), mode=SENTINEL_MODE)

    return InitializationResult(
        layout=layout,
        sentinel=sentinel,
        created_directories=tuple(sorted(created)),
        adopted_published=inspection.adopted_published,
        removed_temporaries=tuple(sorted(removed)),
    )
