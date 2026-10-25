"""Bounded descriptor-pinned credential bytes, independent of any verifier."""

import os
import stat
import struct
from pathlib import Path
from typing import TYPE_CHECKING

from hfcache.errors import ConfigurationError

if TYPE_CHECKING:
    from collections.abc import Mapping

    from hfcache.server_config import CredentialSource

MAXIMUM_CREDENTIAL_BYTES = 8192
SYSTEMD_ACL_MODE = 0o440


def invalid_credential() -> ConfigurationError:
    return ConfigurationError.single(
        "API credential source is missing, unsafe, changed while reading or malformed",
        code="HFAPI003",
    )


def _metadata(status: os.stat_result) -> tuple[int, ...]:
    return (
        status.st_dev,
        status.st_ino,
        status.st_mode,
        status.st_uid,
        status.st_gid,
        status.st_nlink,
        status.st_size,
        status.st_mtime_ns,
        status.st_ctime_ns,
    )


def _systemd_user_acl(descriptor: int, status: os.stat_result) -> bytes:
    """Accept only the fixed read-only root-owned named-user delivery ACL."""
    if status.st_uid != 0 or status.st_gid != 0 or stat.S_IMODE(status.st_mode) != SYSTEMD_ACL_MODE:
        raise invalid_credential()
    expected = struct.pack("<I", 2) + b"".join(
        struct.pack("<HHI", tag, permissions, identifier)
        for tag, permissions, identifier in (
            (0x01, 0x04, 0xFFFFFFFF),
            (0x02, 0x04, os.geteuid()),
            (0x04, 0x00, 0xFFFFFFFF),
            (0x10, 0x04, 0xFFFFFFFF),
            (0x20, 0x00, 0xFFFFFFFF),
        )
    )
    actual = os.getxattr(descriptor, "system.posix_acl_access")
    if actual != expected:
        raise invalid_credential()
    return actual


def read_protected_bytes(path: Path, maximum: int) -> bytes:
    """Read only the checked regular inode, without following any symlink.

    A pathname replacement cannot redirect the open descriptor. Changes to that
    inode's contents, ownership, permissions or metadata during reading refuse.
    Directory handles require search access only; no directory data is read.
    No credential bytes are registered, decoded or included in a diagnostic.
    """
    if (
        type(maximum) is not int
        or not 0 < maximum <= MAXIMUM_CREDENTIAL_BYTES
        or not path.is_absolute()
        or ".." in path.parts
        or "\\" in str(path)
        or any(not character.isprintable() for character in str(path))
    ):
        raise invalid_credential()
    directory = -1
    descriptor = -1
    try:
        directory = os.open("/", os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
        for component in path.parts[1:-1]:
            child = os.open(
                component,
                os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                dir_fd=directory,
            )
            os.close(directory)
            directory = child
        descriptor = os.open(
            path.name,
            os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
            dir_fd=directory,
        )
        before = os.fstat(descriptor)
        delivery_acl = None
        if before.st_mode & stat.S_IRGRP and before.st_gid not in {os.getegid(), *os.getgroups()}:
            delivery_acl = _systemd_user_acl(descriptor, before)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_uid not in {0, os.geteuid()}
            or stat.S_IMODE(before.st_mode) not in {0o400, 0o440, 0o600, 0o640}
            or (
                before.st_mode & stat.S_IRGRP
                and before.st_gid not in {os.getegid(), *os.getgroups()}
                and delivery_acl is None
            )
            or before.st_nlink != 1
            or not 0 < before.st_size <= maximum
        ):
            raise invalid_credential()
        raw = bytearray()
        while len(raw) <= maximum:
            part = os.read(descriptor, maximum + 1 - len(raw))
            if not part:
                break
            raw.extend(part)
        after_acl = (
            os.getxattr(descriptor, "system.posix_acl_access") if delivery_acl is not None else None
        )
        after = os.fstat(descriptor)
        if (
            _metadata(before) != _metadata(after)
            or len(raw) != before.st_size
            or after_acl != delivery_acl
        ):
            raise invalid_credential()
    except OSError:
        raise invalid_credential() from None
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if directory >= 0:
            os.close(directory)
    return bytes(raw)


def source_path(source: CredentialSource, environ: Mapping[str, str]) -> Path:
    """Resolve only the explicit file or named systemd delivery directory."""
    if source.file is not None:
        return source.file
    directory = environ.get("CREDENTIALS_DIRECTORY", "")
    if not directory or not Path(directory).is_absolute() or source.systemd_name is None:
        raise invalid_credential()
    return Path(directory) / source.systemd_name
