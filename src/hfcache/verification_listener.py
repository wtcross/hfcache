"""Decision 128: own one protected listener and readiness socket using only stdlib.

Importing these bootstrap helpers resolves no policy, credential or Hub state.
The caller holds the worker instance lock through binding, joined drain and
cleanup. A reserved unbound descriptor grants no pathname deletion authority.
"""

import errno
import os
import re
import socket
import stat
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, NoReturn

if TYPE_CHECKING:
    from collections.abc import Iterator
    from threading import Event

_DESCRIPTOR = 3
_NOTIFY_TIMEOUT = 1.0
_UNIX_ADDRESS_BYTES = 107
DIRECTORY_MODE = 0o700
SOCKET_MODE = 0o600
MOUNTINFO = Path("/proc/self/mountinfo")
_MAX_MOUNTINFO = 1048576
_MOUNT_FIELDS = 6
_MOUNT_TRAILING = 3
_LOCAL_FILESYSTEMS = frozenset({"btrfs", "ext2", "ext3", "ext4", "overlay", "tmpfs", "xfs"})


def _refuse() -> NoReturn:
    message = "private listener bootstrap refused"
    raise OSError(message)


def reserve_listener() -> socket.socket:
    """Reserve internal FD3 after inheritance audit, before NSS/runtime imports."""
    channel = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        if channel.fileno() != _DESCRIPTOR:
            try:
                os.fstat(_DESCRIPTOR)
            except OSError as error:
                if error.errno != errno.EBADF:
                    raise
            else:
                _refuse()  # Never overwrite a descriptor absent from the caller's audit.
            os.dup2(channel.fileno(), _DESCRIPTOR, inheritable=False)
            channel.close()
            channel = socket.socket(fileno=_DESCRIPTOR)
        channel.set_inheritable(False)
    except BaseException:
        channel.close()
        raise
    return channel


def _require_local(path: Path) -> None:
    """Read kernel metadata before traversing a possibly network-backed IPC path."""
    with MOUNTINFO.open("rb") as stream:
        body = stream.read(_MAX_MOUNTINFO + 1)
    if len(body) > _MAX_MOUNTINFO:
        _refuse()
    matches: list[tuple[int, str]] = []
    for line in body.decode().splitlines():
        before, separator, after = line.partition(" - ")
        fields, trailing = before.split(), after.split()
        if not separator or len(fields) < _MOUNT_FIELDS or len(trailing) < _MOUNT_TRAILING:
            _refuse()
        where = Path(re.sub(r"\\([0-7]{3})", lambda match: chr(int(match[1], 8)), fields[4]))
        if where in (path, *path.parents):
            matches.append((len(where.parts), trailing[0]))
    deepest = max((depth for depth, _ in matches), default=-1)
    if not matches or any(
        kind not in _LOCAL_FILESYSTEMS for depth, kind in matches if depth == deepest
    ):
        _refuse()


def _parent(path: Path) -> int:
    if (
        not path.is_absolute()
        or ".." in path.parts
        or not path.name
        or "\\" in str(path)
        or any(not character.isprintable() for character in str(path))
    ):
        _refuse()
    _require_local(path.parent)
    descriptor = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        for part in path.parent.parts[1:]:
            child = os.open(
                part,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                dir_fd=descriptor,
            )
            os.close(descriptor)
            descriptor = child
        info = os.fstat(descriptor)
        if (
            info.st_uid != os.geteuid()
            or info.st_gid != os.getegid()
            or stat.S_IMODE(info.st_mode) != DIRECTORY_MODE
        ):
            _refuse()
    except BaseException:
        os.close(descriptor)
        raise
    return descriptor


@dataclass(frozen=True)
class OwnedListener:
    """Trusted bind spelling and filesystem identity, never caller-supplied scope."""

    bound_address: str
    identity: tuple[int, int]


@contextmanager
def owned_listener(channel: socket.socket, path: Path) -> Iterator[OwnedListener]:
    """Refuse existing paths and remove only this invocation's socket after drain."""
    parent = _parent(path)
    owned: tuple[int, int] | None = None
    try:
        try:
            os.stat(path.name, dir_fd=parent, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            _refuse()
        address = f"/proc/self/fd/{parent}/{path.name}"
        previous = os.umask(0o177)
        try:
            channel.bind(address)
        finally:
            os.umask(previous)
        info = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
        if (
            not stat.S_ISSOCK(info.st_mode)
            or info.st_uid != os.geteuid()
            or info.st_gid != os.getegid()
            or stat.S_IMODE(info.st_mode) != SOCKET_MODE
        ):
            _refuse()
        owned = (info.st_dev, info.st_ino)
        # Creation already gives exact 0600; no later pathname chmod can touch
        # an unexplained replacement. Private parent and instance ownership stand.
        channel.listen(8)
        yield OwnedListener(address, owned)
    finally:
        channel.close()
        try:
            if owned is not None:
                try:
                    current = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
                except FileNotFoundError:
                    pass
                else:
                    if stat.S_ISSOCK(current.st_mode) and (current.st_dev, current.st_ino) == owned:
                        os.unlink(path.name, dir_fd=parent)
        finally:
            os.close(parent)


def notify_ready(stop: Event) -> bool:
    """Send fixed readiness only for an initialized owned worker not shutting down."""
    if stop.is_set():
        return False
    address = os.environ.get("NOTIFY_SOCKET", "")
    if (
        not address
        or address[0] not in {"/", "@"}
        or len(address.encode("utf-8")) > _UNIX_ADDRESS_BYTES
        or any(not character.isprintable() for character in address)
    ):
        _refuse()
    if address.startswith("@"):
        address = "\0" + address[1:]
    with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as notifier:
        notifier.settimeout(_NOTIFY_TIMEOUT)
        if stop.is_set():
            return False
        notifier.sendto(b"READY=1", address)
    return True
