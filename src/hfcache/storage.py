"""Proving the archive mount, and the one command that brings an archive into being.

`archive init` is the only irreversible command this application has and the only
way the layout in `docs/architecture.md` §5.1 ever comes into existence
(`FS-21`). Everything else here exists so that command can *refuse* rather than
guess:

* the kernel's mount table is read to prove the target is a read/write NFS mount
  before anything is created (`FS-02`),
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

import os
import re
import secrets
import socket
import stat
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, Any, Final, Literal, final

from hfcache import __version__
from hfcache.errors import Problem, SafetyError
from hfcache.identity import new_probe_id
from hfcache.models import ArchiveSentinel, Provenance, dump, load

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

    from hfcache.identity import ProbeId
    from hfcache.paths import ArchiveLayout

__all__ = [
    "MOUNT_TABLE",
    "NFS_FILESYSTEM_TYPES",
    "REPORTED_ENTRY_LIMIT",
    "SENTINEL_MODE",
    "ArchiveInspection",
    "ArchiveState",
    "InitializationResult",
    "MountEntry",
    "MountFacts",
    "atomic_write_bytes",
    "describe_mount",
    "device_problems",
    "fsync_directory",
    "initialize_archive",
    "inspect_archive",
    "is_initialized",
    "is_temporary_sibling",
    "mount_problems",
    "parse_mount_table",
    "probe_writability",
    "publication_destinations",
    "published_adoption_problems",
    "read_mount_table",
    "same_filesystem_problems",
    "temporary_sibling",
]

MOUNT_TABLE = Path("/proc/self/mountinfo")
"""Where Linux publishes the mount table, including the filesystem type.

`statvfs` does not carry a filesystem type on Linux and `Path.is_mount` only
compares device numbers, so neither can answer `HFMNT003`. This file can, it
needs no subprocess, and it distinguishes a stacked automount from the NFS mount
on top of it.
"""

NFS_FILESYSTEM_TYPES: Final = frozenset({"nfs", "nfs4"})
"""The only filesystem types an archive may live on (`FS-02`)."""

SENTINEL_MODE: Final = 0o640
"""`.hfcache-root` is readable to the group, writable only by the writer (§5.2)."""

REPORTED_ENTRY_LIMIT: Final = 20
"""Cap on how many unrecognized entries one report names individually.

An `--archive-root` pointed at the wrong directory can contain any number of
files. The count is always exact; the enumeration is bounded so a refusal stays
readable.
"""

_MOUNTINFO_ESCAPES: Final = {"040": " ", "011": "\t", "012": "\n", "134": "\\"}
"""The four octal escapes `proc_pid_mountinfo(5)` uses in a mount point."""

_MOUNTINFO_FIXED_FIELDS: Final = 6
"""Fields before the optional ones: id, parent, device, root, mount point, options."""

_TEMPORARY = re.compile(r".+\.tmp-[0-9a-f]{16}")
"""A durable write in progress. Matched with `fullmatch`, never anchored."""

_PROBE_DIRECTORY_MODE: Final = 0o700
"""A probe directory is the writer's alone, like everything else under `.store`."""

_PROBE_FILE_MODE: Final = 0o600
"""The probe file outlives nothing; nobody else ever needs to read it."""

_PROBE_FILE: Final = "probe.json"
"""The one file a probe creates, inside the one directory a probe creates."""

_PROBE_PAYLOAD: Final = b'{"probe": "hfcache"}\n'
"""What the probe writes and then reads back.

Read back rather than assumed, because `write` returning success is not the same
statement as the bytes being there: a short write, a truncating filesystem, or a
mode that made the file unreadable to the identity that just created it are all
caught here and none of them are caught by the write alone.
"""


# --------------------------------------------------------------------------- #
# The mount table
# --------------------------------------------------------------------------- #


@final
@dataclass(frozen=True, slots=True)
class MountEntry:
    """One line of `/proc/self/mountinfo`."""

    mount_point: PurePosixPath
    filesystem_type: str
    source: str
    options: tuple[str, ...]
    super_options: tuple[str, ...]

    @property
    def is_nfs(self) -> bool:
        """Whether this mount is one of the NFS flavours `FS-02` permits."""
        return self.filesystem_type in NFS_FILESYSTEM_TYPES

    @property
    def read_only(self) -> bool:
        """Whether writes are refused, by the mount or by the server's export.

        Both fields are consulted because they fail differently: `ro` in the
        per-mount options is a client-side choice, while `ro` in the superblock
        options is what a server-side read-only export looks like from here.
        """
        return "ro" in self.options or "ro" in self.super_options


def _unescape(value: str) -> str:
    """Decode the octal escapes a mount point may carry."""
    if "\\" not in value:
        return value
    decoded: list[str] = []
    index = 0
    while index < len(value):
        escape = None
        if value[index] == "\\":
            escape = _MOUNTINFO_ESCAPES.get(value[index + 1 : index + 4])
        if escape is None:
            decoded.append(value[index])
            index += 1
        else:
            decoded.append(escape)
            index += 4
    return "".join(decoded)


def parse_mount_table(text: str) -> tuple[MountEntry, ...]:
    """Parse mountinfo text into entries, in kernel order.

    A line that does not have the documented shape is skipped rather than
    guessed at: the table is read to *prove* a property, so an entry that cannot
    be parsed must not be able to establish one.
    """
    entries: list[MountEntry] = []
    for line in text.splitlines():
        fields = line.split(" ")
        separator = next(
            (
                index
                for index in range(_MOUNTINFO_FIXED_FIELDS, len(fields))
                if fields[index] == "-"
            ),
            None,
        )
        if separator is None or len(fields) < separator + 3:
            continue
        entries.append(
            MountEntry(
                mount_point=PurePosixPath(_unescape(fields[4])),
                filesystem_type=fields[separator + 1],
                source=_unescape(fields[separator + 2]),
                options=tuple(fields[5].split(",")),
                super_options=tuple(
                    fields[separator + 3].split(",") if len(fields) > separator + 3 else ()
                ),
            )
        )
    return tuple(entries)


def read_mount_table(source: Path | None = None) -> tuple[MountEntry, ...]:
    """Read the kernel's mount table.

    A table that cannot be read is `HFMNT003`: without it the filesystem type is
    unknown, and an unknown type is not NFS.
    """
    path = MOUNT_TABLE if source is None else source
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        message = (
            f"the mount table {path} could not be read ({exc.strerror}), so the archive "
            f"filesystem type cannot be proven"
        )
        raise SafetyError.single(message, code="HFMNT003", location=str(path)) from exc
    return parse_mount_table(text)


@final
@dataclass(frozen=True, slots=True)
class MountFacts:
    """What can be observed about the archive root before anything is written."""

    path: Path
    exists: bool
    is_directory: bool
    is_symlink: bool
    entry: MountEntry | None

    @property
    def is_mount_point(self) -> bool:
        """Whether the root is itself a mount, distinct from its parent (`FS-02`)."""
        return self.entry is not None

    def as_payload(self) -> dict[str, Any]:
        """Render for the `--json` envelope."""
        entry = self.entry
        return {
            "exists": self.exists,
            "filesystem_type": entry.filesystem_type if entry else None,
            "is_mount_point": self.is_mount_point,
            "read_only": entry.read_only if entry else None,
            "source": entry.source if entry else None,
        }


def describe_mount(path: Path, *, table: Sequence[MountEntry] | None = None) -> MountFacts:
    """Observe the archive root and locate it in the mount table.

    The *last* matching entry wins. Mounts stack: on the writer, the NFS mount
    sits on top of the `x-systemd.automount` autofs mount at the same path, and
    the topmost one is what a process actually sees.
    """
    entries = read_mount_table() if table is None else tuple(table)
    try:
        status = path.lstat()
    except OSError:
        return MountFacts(path=path, exists=False, is_directory=False, is_symlink=False, entry=None)
    if stat.S_ISLNK(status.st_mode):
        return MountFacts(path=path, exists=True, is_directory=False, is_symlink=True, entry=None)
    if not stat.S_ISDIR(status.st_mode):
        return MountFacts(path=path, exists=True, is_directory=False, is_symlink=False, entry=None)
    resolved = PurePosixPath(os.path.realpath(path))
    match = next(
        (entry for entry in reversed(entries) if entry.mount_point == resolved),
        None,
    )
    return MountFacts(path=path, exists=True, is_directory=True, is_symlink=False, entry=match)


def mount_problems(facts: MountFacts) -> list[Problem]:
    """Report every way the observed root fails §19's first four requirements.

    Ordered by how early the requirement fails, and short-circuited where a later
    check would be meaningless: nothing can be said about the filesystem type of
    a path that is not a mount point.
    """
    where = str(facts.path)
    if not facts.exists:
        message = f"archive root {where} does not exist"
        return [Problem(code="HFMNT001", message=message, location=where)]
    if facts.is_symlink:
        message = (
            f"archive root {where} is a symlink; the archive root is never followed through "
            f"a link, because what it points at can change between the check and the write"
        )
        return [Problem(code="HFMNT015", message=message, location=where)]
    if not facts.is_directory:
        message = f"archive root {where} exists but is not a directory"
        return [Problem(code="HFMNT015", message=message, location=where)]
    if facts.entry is None:
        message = (
            f"archive root {where} is not a mount point; it is a directory on the parent "
            f"filesystem, so writing there would fill local storage instead of the archive"
        )
        return [Problem(code="HFMNT002", message=message, location=where)]
    problems: list[Problem] = []
    if not facts.entry.is_nfs:
        message = (
            f"archive root {where} is a {facts.entry.filesystem_type} mount, not one of "
            f"{sorted(NFS_FILESYSTEM_TYPES)}"
        )
        problems.append(Problem(code="HFMNT003", message=message, location=where))
    if facts.entry.read_only:
        message = f"archive root {where} is mounted read-only"
        problems.append(Problem(code="HFMNT004", message=message, location=where))
    return problems


# --------------------------------------------------------------------------- #
# Durable writes
# --------------------------------------------------------------------------- #


def temporary_sibling(path: Path) -> Path:
    """Name a temporary file beside `path`, on the same filesystem.

    Beside rather than in a temporary directory, so the rename that follows is
    always within one filesystem and therefore atomic (`FS-04`). The suffix is
    what lets an interrupted write be recognised later as the application's own
    partial artifact rather than as unknown data (`FS-19`).
    """
    return path.with_name(f"{path.name}.tmp-{secrets.token_hex(8)}")


def is_temporary_sibling(name: str) -> bool:
    """Whether a filename is an interrupted durable write of this application."""
    return _TEMPORARY.fullmatch(name) is not None


def fsync_directory(path: Path) -> None:
    """Make a directory's entries durable, not merely its children's contents."""
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def atomic_write_bytes(path: Path, payload: bytes, *, mode: int) -> None:
    """Write a file so that a reader never observes a partial one.

    Temporary sibling, `fsync`, `chmod`, `rename(2)`, then `fsync` of the parent
    (`docs/schemas.md` §1). The mode is applied before the rename so the file is
    never reachable at its final name with a mode derived from the process umask.
    """
    temporary = temporary_sibling(path)
    try:
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.chmod(mode)
        temporary.replace(path)
    except OSError:
        temporary.unlink(missing_ok=True)
        raise
    fsync_directory(path.parent)


# --------------------------------------------------------------------------- #
# Effective writability and filesystem containment
# --------------------------------------------------------------------------- #


def is_initialized(layout: ArchiveLayout) -> bool:
    """Whether the archive has been initialized.

    The sentinel is written last, so its presence is what proves the layout
    beneath it exists (`FS-23`). A check that needs an initialized archive asks
    this, and reports `skipped` rather than failing when the answer is no: an
    uninitialized target is operator state that `archive init` changes, not a
    broken deployment.
    """
    return layout.sentinel.is_file()


def probe_writability(layout: ArchiveLayout, *, probe_id: ProbeId | None = None) -> list[Problem]:
    """Prove create, fsync, rename, and delete succeed under `.store/health/`.

    Plan §19 items 6 and 10, and `doctor` check 7. This is the *only* way
    effective writability is ever established. The Mapall writer export presents
    NAS-side owner ids with no local account, so comparing `st_uid` against the
    service uid proves nothing about whether this process can write
    (`docs/plan.md` §35.3) — and a server-side read-only export presents `rw`
    client options, so the mount table does not answer it either.

    Every artifact is removed before this returns, including after a failed
    probe: a probe that left evidence behind would be found by the next
    inspection and refused as content the application did not put there
    (`FS-22`).
    """
    directory = layout.probe(new_probe_id() if probe_id is None else probe_id)
    where = str(layout.archive_relative(directory))
    try:
        directory.mkdir(mode=_PROBE_DIRECTORY_MODE)
    except OSError as exc:
        message = (
            f"the probe directory {directory} could not be created ({exc.strerror}), so the "
            f"archive is not effectively writable by this identity"
        )
        return [Problem(code="HFMNT008", message=message, location=where)]
    problems = _exercise_probe(directory, where)
    problems.extend(_remove_probe(directory, where))
    return problems


def _exercise_probe(directory: Path, where: str) -> list[Problem]:
    """Perform the four operations plan §19 item 10 names, on the probe's own file."""
    target = directory / _PROBE_FILE
    try:
        # `atomic_write_bytes` is create, fsync, chmod, rename, fsync-parent —
        # exactly the primitive publication uses. Exercising the real one is the
        # point: an approximation could succeed where publication would not.
        atomic_write_bytes(target, _PROBE_PAYLOAD, mode=_PROBE_FILE_MODE)
        observed = target.read_bytes()
        target.unlink()
        fsync_directory(directory)
    except OSError as exc:
        message = (
            f"the write probe under {directory} failed at {exc.filename or directory}: "
            f"{exc.strerror}"
        )
        return [Problem(code="HFMNT008", message=message, location=where)]
    if observed != _PROBE_PAYLOAD:
        message = (
            f"the write probe under {directory} read back {len(observed)} bytes, not the "
            f"{len(_PROBE_PAYLOAD)} it wrote; the archive does not hold what is written to it"
        )
        return [Problem(code="HFMNT008", message=message, location=where)]
    return []


def _remove_probe(directory: Path, where: str) -> list[Problem]:
    """Remove the probe's artifacts, whether or not the probe itself succeeded.

    Only files directly inside the probe directory, because those are the only
    things a probe creates. Anything else is reported rather than removed, which
    keeps this within `FS-19` even in the one case where the application deletes
    something during a read-only-looking command.
    """
    try:
        for child in sorted(directory.iterdir()):
            child.unlink()
        directory.rmdir()
    except OSError as exc:
        message = (
            f"the write probe left {exc.filename or directory} behind ({exc.strerror}); a probe "
            f"removes everything it created, so this is reported rather than passed over"
        )
        return [Problem(code="HFMNT008", message=message, location=where)]
    return []


def publication_destinations(layout: ArchiveLayout) -> tuple[Path, ...]:
    """Every directory a staging or published tree is renamed into (`FS-04`).

    A publication renames staging into `published/repos`; a prune renames a
    published tree into `.store/trash`; a verification failure renames one into
    `.store/quarantine`. `manifests/` and `catalog/` receive durable file writes,
    whose rename is within one directory by construction, and they are listed
    anyway so the proof covers the whole consumer-visible subtree rather than
    the parts that happen to need it most.
    """
    return (
        layout.published,
        layout.repos,
        layout.manifests,
        layout.catalog,
        layout.trash,
        layout.quarantine,
    )


def device_problems(devices: Mapping[str, int], *, root_device: int) -> list[Problem]:
    """Report every path that is not on the archive root's filesystem (`FS-04`).

    Taken as device numbers rather than paths so the policy is separable from
    the syscall, which is what lets it be exercised for a second filesystem this
    test host cannot mount — the same reason `published_adoption_problems` takes
    `os.stat_result` values.
    """
    return [
        Problem(
            code="HFMNT009",
            message=(
                f"{where} is on device {device}, but the archive root is on {root_device}; "
                f"publication is a rename(2) and would become a cross-device copy"
            ),
            location=where,
        )
        for where, device in sorted(devices.items())
        if device != root_device
    ]


def same_filesystem_problems(layout: ArchiveLayout) -> list[Problem]:
    """Prove staging and every publication destination share one filesystem.

    `doctor` check 8 and plan §19 item 7. Reads only: `stat(2)` on directories
    the layout already requires to exist, so this proves nothing about
    writability and is safe under `--read-only`.
    """
    root = layout.root
    try:
        root_device = root.stat().st_dev
    except OSError as exc:
        message = (
            f"the archive root {root} could not be examined ({exc.strerror}), so staging and "
            f"its publication destinations cannot be proven to share a filesystem"
        )
        return [Problem(code="HFMNT008", message=message, location=str(root))]

    devices: dict[str, int] = {}
    problems: list[Problem] = []
    for path in (layout.staging, *publication_destinations(layout)):
        where = str(layout.archive_relative(path))
        try:
            devices[where] = path.stat().st_dev
        except OSError as exc:
            message = f"required directory {path} could not be examined: {exc.strerror}"
            problems.append(Problem(code="HFMNT008", message=message, location=where))
    problems.extend(device_problems(devices, root_device=root_device))
    return problems


# --------------------------------------------------------------------------- #
# Inspection
# --------------------------------------------------------------------------- #

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


def _read_sentinel(
    layout: ArchiveLayout, *, archive_id: str
) -> tuple[ArchiveSentinel, list[Problem]]:
    """Load `.hfcache-root` and check it against configuration (`FS-01`, `FS-03`)."""
    where = str(layout.archive_relative(layout.sentinel))
    try:
        raw = layout.sentinel.read_bytes()
    except OSError as exc:
        message = f"sentinel {layout.sentinel} is unreadable: {exc.strerror}"
        raise SafetyError.single(message, code="HFMNT006", location=where) from exc
    sentinel = load(ArchiveSentinel, raw, error=SafetyError, code="HFMNT006", location=where)
    problems: list[Problem] = []
    if sentinel.archive_id != archive_id:
        message = (
            f"sentinel archive_id {sentinel.archive_id} does not match the configured "
            f"{archive_id}; this is never repaired or regenerated (`FS-03`)"
        )
        problems.append(Problem(code="HFMNT007", message=message, location=where))
    return sentinel, problems


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
        sentinel, sentinel_problems = _read_sentinel(layout, archive_id=archive_id)
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
