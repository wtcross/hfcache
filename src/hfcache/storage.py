"""Proving the archive mount, and writing to it durably.

Everything a command must establish about `/srv/hfcache` before it may act on
it, and every primitive that acts on it once established:

* the kernel's mount table is read to prove the target is a read/write NFS mount
  (`FS-02`), because `statvfs` carries no filesystem type and `is_mount` only
  compares device numbers,
* a durable write is a temporary sibling, an `fsync`, and a `rename(2)`, so a
  reader never observes a partial file (`docs/schemas.md` §1),
* effective writability is proven by performing it under `.store/health/` and
  never by comparing `st_uid` against a local uid — the Mapall writer export
  presents NAS-side ids with no local account (`docs/plan.md` §35.3),
* staging and every publication destination are proven to share one filesystem,
  so publication is a rename and never a cross-device copy (`FS-04`), and
* the sentinel is read and compared against configuration, which is the archive's
  identity (`FS-01`, `FS-03`).

`hfcache.preflight` orders these into the named checks `doctor` reports and the
gate a mutating command passes. `hfcache.archive` builds on them to inspect and
create an archive. Nothing here decides policy; each function reports what it
observed as coded `Problem`s and lets its caller decide what that means.
"""

import os
import re
import secrets
import shutil
import stat
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, Any, Final, final

from hfcache.errors import HfcacheError, Problem, SafetyError
from hfcache.identity import new_probe_id
from hfcache.models import ArchiveSentinel, DurableModel, VersionedModel, dump, load

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence

    from hfcache.identity import ProbeId
    from hfcache.paths import ArchiveLayout

__all__ = [
    "BYTES_PER_GIB",
    "MOUNT_TABLE",
    "NFS_FILESYSTEM_TYPES",
    "SENTINEL_MODE",
    "CapacityFacts",
    "MountEntry",
    "MountFacts",
    "atomic_write_bytes",
    "capacity_problems",
    "capacity_warnings",
    "describe_capacity",
    "describe_mount",
    "device_problems",
    "effective_reserve",
    "fsync_directory",
    "is_initialized",
    "is_temporary_sibling",
    "mount_problems",
    "parse_mount_table",
    "probe_directory_rename",
    "probe_hardlink",
    "probe_reference_replacement",
    "probe_writability",
    "publication_destinations",
    "read_model",
    "read_mount_table",
    "read_sentinel",
    "same_filesystem_problems",
    "temporary_sibling",
    "write_model",
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

BYTES_PER_GIB: Final = 1024**3
"""`minimum_free_space_gib` is gibibytes, matching how ZFS reports a quota."""

_APPROACHING_RESERVE_PERCENT: Final = 10
"""How close to the reserve free capacity gets before `HFWRN005` is raised.

`docs/cli.md` §5.6 defines the warning but fixes no threshold, so this is the
application's (`docs/progress.md` decision 38). Expressed against the reserve
rather than as an absolute figure, so it scales with the deployment.
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

_EXPECTED_LINK_COUNT: Final = 2
"""A source and its hardlink are one inode reached by two names."""

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


def write_model(path: Path, model: DurableModel, *, mode: int, code: str) -> None:
    """Write one validated durable artifact, atomically (`docs/schemas.md` §1).

    `dump` renders the bytes and `atomic_write_bytes` places them, so every
    durable file this application writes goes through the same serializer and the
    same temporary-sibling-fsync-rename. `code` is the caller's, for the same
    reason `read_model`'s is: a failed manifest write is `HFSYN008` and a failed
    reference write is `HFSYN007`, and only the caller knows which it is doing.
    """
    try:
        atomic_write_bytes(path, dump(model), mode=mode)
    except OSError as exc:
        message = f"writing {path} failed: {exc.strerror}"
        raise SafetyError.single(message, code=code, location=str(path)) from exc


def read_model[ModelT: VersionedModel](
    path: Path,
    model_type: type[ModelT],
    *,
    error: type[HfcacheError],
    code: str,
    location: str | None = None,
) -> ModelT:
    """Read one durable artifact back, mapping an unreadable file to the same code.

    `load` already turns a malformed or too-new artifact into coded problems.
    This adds the one thing it cannot see: the file not being readable at all,
    which for every caller means the same thing as the file being unusable.
    """
    where = str(path) if location is None else location
    try:
        raw = path.read_bytes()
    except OSError as exc:
        message = f"{path} could not be read: {exc.strerror}"
        raise error([Problem(code=code, message=message, location=where)]) from exc
    return load(model_type, raw, error=error, code=code, location=where)


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
    """
    return _run_probe(layout, _exercise_writability, probe_id=probe_id, code="HFMNT008")


def probe_hardlink(layout: ArchiveLayout, *, probe_id: ProbeId | None = None) -> list[Problem]:
    """Prove a regular file can be hardlinked, with the right link count and contents.

    `doctor` check 9 and plan §14.2. Hardlink publication is what keeps a
    published revision from doubling the bytes its cache blob already occupies
    (`AD-11`), and a dataset that cannot do it must fail *before* a download
    rather than silently consume twice the planned space.

    The link is made between two directories inside the probe area rather than
    between `.store` and `published/` (`docs/progress.md` decision 41): a
    publication hardlinks a cache blob into `.store/staging` and then renames the
    *tree*, so it never links into `published/` at all, and check 8 has already
    proven the whole layout is one filesystem.
    """
    return _run_probe(layout, _exercise_hardlink, probe_id=probe_id, code="HFMNT012")


def probe_directory_rename(
    layout: ArchiveLayout, *, probe_id: ProbeId | None = None
) -> list[Problem]:
    """Prove a populated directory renames atomically within the dataset.

    `doctor` check 10. This is the single operation that makes a revision
    visible (plan §13.2 step 15): the staged tree is complete, fsynced, and then
    renamed into place in one step, so a consumer never observes a partial
    publication (`FS-12`).
    """
    return _run_probe(layout, _exercise_directory_rename, probe_id=probe_id, code="HFMNT013")


def probe_reference_replacement(
    layout: ArchiveLayout, *, probe_id: ProbeId | None = None
) -> list[Problem]:
    """Prove a small reference file can be replaced atomically.

    `doctor` check 11. `refs/current.json` is replaced, never edited in place
    (`FS-08`), and a consumer that reads it once must see either the old
    revision or the new one — never a truncated file (`FS-12`).
    """
    return _run_probe(layout, _exercise_reference_replacement, probe_id=probe_id, code="HFMNT013")


def _run_probe(
    layout: ArchiveLayout,
    exercise: Callable[[Path, str, str], list[Problem]],
    *,
    probe_id: ProbeId | None,
    code: str,
) -> list[Problem]:
    """Make a probe area, exercise one capability in it, and remove it again.

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
    problems = exercise(directory, where, code)
    problems.extend(_remove_probe(directory, where, code))
    return problems


def _exercise_writability(directory: Path, where: str, code: str) -> list[Problem]:
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
        return [_probe_failure(directory, where, code, exc)]
    if observed != _PROBE_PAYLOAD:
        message = (
            f"the write probe under {directory} read back {len(observed)} bytes, not the "
            f"{len(_PROBE_PAYLOAD)} it wrote; the archive does not hold what is written to it"
        )
        return [Problem(code=code, message=message, location=where)]
    return []


def _exercise_hardlink(directory: Path, where: str, code: str) -> list[Problem]:
    """Link a file from a cache-like directory into a staging-like one (§14.2)."""
    private = directory / "cache"
    staged = directory / "staging"
    source = private / "blob"
    destination = staged / "file"
    try:
        private.mkdir(mode=_PROBE_DIRECTORY_MODE)
        staged.mkdir(mode=_PROBE_DIRECTORY_MODE)
        atomic_write_bytes(source, _PROBE_PAYLOAD, mode=_PROBE_FILE_MODE)
        os.link(source, destination)
        links = destination.stat().st_nlink
        observed = destination.read_bytes()
    except OSError as exc:
        return [_probe_failure(directory, where, code, exc)]
    problems: list[Problem] = []
    if links != _EXPECTED_LINK_COUNT:
        message = (
            f"a hardlink under {directory} reports {links} links, not {_EXPECTED_LINK_COUNT}; "
            f"the destination is a copy rather than the same inode, so publication would "
            f"silently consume twice the planned space"
        )
        problems.append(Problem(code=code, message=message, location=where))
    if observed != _PROBE_PAYLOAD:
        message = f"a hardlink under {directory} does not read back the bytes it was made from"
        problems.append(Problem(code=code, message=message, location=where))
    return problems


def _exercise_directory_rename(directory: Path, where: str, code: str) -> list[Problem]:
    """Rename a populated directory the way publication renames a staged tree."""
    staged = directory / "staging"
    promoted = directory / "published"
    try:
        staged.mkdir(mode=_PROBE_DIRECTORY_MODE)
        atomic_write_bytes(staged / _PROBE_FILE, _PROBE_PAYLOAD, mode=_PROBE_FILE_MODE)
        fsync_directory(staged)
        staged.rename(promoted)
        fsync_directory(directory)
        moved = (promoted / _PROBE_FILE).read_bytes()
        left_behind = staged.exists()
    except OSError as exc:
        return [_probe_failure(directory, where, code, exc)]
    if left_behind or moved != _PROBE_PAYLOAD:
        message = (
            f"renaming a directory under {directory} did not move it wholesale; a publication "
            f"rename must be one step, or a consumer can observe a partial revision"
        )
        return [Problem(code=code, message=message, location=where)]
    return []


def _exercise_reference_replacement(directory: Path, where: str, code: str) -> list[Problem]:
    """Replace a small file the way `refs/current.json` is replaced (`FS-08`)."""
    reference = directory / "current.json"
    replacement = _PROBE_PAYLOAD + b"replaced\n"
    try:
        atomic_write_bytes(reference, _PROBE_PAYLOAD, mode=_PROBE_FILE_MODE)
        atomic_write_bytes(reference, replacement, mode=_PROBE_FILE_MODE)
        observed = reference.read_bytes()
        siblings = sorted(path.name for path in directory.iterdir())
    except OSError as exc:
        return [_probe_failure(directory, where, code, exc)]
    if observed != replacement:
        message = f"replacing a reference under {directory} did not leave the new contents"
        return [Problem(code=code, message=message, location=where)]
    if siblings != ["current.json"]:
        message = (
            f"replacing a reference under {directory} left {siblings}; the replacement is a "
            f"rename over the original, so nothing else may survive it"
        )
        return [Problem(code=code, message=message, location=where)]
    return []


def _probe_failure(directory: Path, where: str, code: str, exc: OSError) -> Problem:
    """Report an operation the probe could not complete at all."""
    message = f"the probe under {directory} failed at {exc.filename or directory}: {exc.strerror}"
    return Problem(code=code, message=message, location=where)


def _remove_probe(directory: Path, where: str, code: str) -> list[Problem]:
    """Remove the probe area, whether or not the probe itself succeeded.

    Removed wholesale rather than entry by entry. That is inside `FS-19` because
    of the name: `probe-<16 random hex>` was created by this process moments ago
    and cannot contain anything the application did not put there, so there is
    nothing here to preserve. Failing to remove it is still reported, because an
    artifact left behind is what the next inspection would refuse.
    """
    try:
        shutil.rmtree(directory)
    except OSError as exc:
        message = (
            f"the probe left {exc.filename or directory} behind ({exc.strerror}); a probe "
            f"removes everything it created, so this is reported rather than passed over"
        )
        return [Problem(code=code, message=message, location=where)]
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
# Capacity
# --------------------------------------------------------------------------- #


@final
@dataclass(frozen=True, slots=True)
class CapacityFacts:
    """What `statvfs(2)` reports about the filesystem holding the archive.

    `total_bytes` is the dataset's *quota* when one is set, because that is what
    the NFS server reports as the filesystem size — which is exactly what
    `docs/configuration.md` §4's "quota, or capacity when no quota is set" asks
    for, without the writer needing to know which case it is in.

    `available_bytes` is `f_bavail`, not `f_bfree`: the difference is the
    root-reserved portion, and the writer is not root on this filesystem.
    """

    path: Path
    total_bytes: int
    available_bytes: int

    def as_payload(self) -> dict[str, Any]:
        """Render for a `--json` payload."""
        return {
            "available_bytes": self.available_bytes,
            "total_bytes": self.total_bytes,
        }


def describe_capacity(path: Path) -> CapacityFacts:
    """Measure the filesystem holding `path`.

    A `statvfs` that fails is `HFMNT008` rather than `HFMNT011`: the capacity is
    unknown, which is a different statement from "the capacity is too small",
    and only the second one may be reported as a capacity failure.
    """
    try:
        status = os.statvfs(path)
    except OSError as exc:
        message = (
            f"the filesystem holding {path} could not be measured ({exc.strerror}), so free "
            f"capacity cannot be compared against the configured reserve"
        )
        raise SafetyError.single(message, code="HFMNT008", location=str(path)) from exc
    return CapacityFacts(
        path=path,
        total_bytes=status.f_blocks * status.f_frsize,
        available_bytes=status.f_bavail * status.f_frsize,
    )


def effective_reserve(total_bytes: int, *, minimum_gib: int, minimum_percent: int) -> int:
    """The greater of the two configured minimums (`docs/configuration.md` §4).

    Whichever binds harder wins, so a small dataset is protected by the absolute
    floor and a large one by the proportional rule, without an operator having to
    work out which applies.
    """
    return max(minimum_gib * BYTES_PER_GIB, total_bytes * minimum_percent // 100)


def capacity_problems(
    facts: CapacityFacts, *, reserve_bytes: int, needed_bytes: int = 0
) -> list[Problem]:
    """Report `HFMNT011` when free capacity does not cover the need plus the reserve.

    Plan §19 item 9. `needed_bytes` is the estimated download plus, in copy mode,
    the projected publication bytes; `doctor` passes `0`, because it is reporting
    on the archive rather than planning a run.
    """
    required = needed_bytes + reserve_bytes
    if facts.available_bytes >= required:
        return []
    message = (
        f"{facts.path} has {facts.available_bytes} bytes free, but this run requires "
        f"{needed_bytes} plus a reserve of {reserve_bytes}, or {required} in total"
    )
    return [
        Problem(
            code="HFMNT011",
            message=message,
            location=str(facts.path),
            context={
                "available_bytes": facts.available_bytes,
                "needed_bytes": needed_bytes,
                "required_bytes": required,
                "reserve_bytes": reserve_bytes,
            },
        )
    ]


def capacity_warnings(
    facts: CapacityFacts, *, reserve_bytes: int, needed_bytes: int = 0
) -> list[Problem]:
    """Report `HFWRN005` when capacity clears the reserve, but not by much.

    The warning exists so an operator learns before a run *fails*, so the margin
    is expressed against the reserve itself rather than as an absolute figure: a
    deployment that reserved 100 GiB and a deployment that reserved 1 TiB want to
    hear about it at different points. A reserve of zero never warns, which is
    the right reading of an operator who configured no reserve at all.
    """
    margin = reserve_bytes * _APPROACHING_RESERVE_PERCENT // 100
    headroom = facts.available_bytes - needed_bytes - reserve_bytes
    if not margin or headroom >= margin:
        return []
    message = (
        f"{facts.path} has {facts.available_bytes} bytes free, which is within "
        f"{_APPROACHING_RESERVE_PERCENT}% of the {reserve_bytes}-byte reserve"
    )
    return [
        Problem(
            code="HFWRN005",
            message=message,
            location=str(facts.path),
            context={
                "available_bytes": facts.available_bytes,
                "headroom_bytes": headroom,
                "reserve_bytes": reserve_bytes,
            },
        )
    ]


# --------------------------------------------------------------------------- #
# The sentinel
# --------------------------------------------------------------------------- #


def read_sentinel(
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
