#!/usr/bin/python3
"""Retain the original local flock without NAS file I/O.

The host mount table is checked once before READY. The descriptor remains held
until this process stops; no lock is created, rewritten, truncated or removed.
"""

import fcntl
import json
import os
import re
import signal
import socket
import stat
import sys
from contextlib import contextmanager
from pathlib import Path

LOCK_PATH = Path("/run/hfcache/hfcache.lock")
MOUNTINFO = Path("/proc/1/mountinfo")
SERVICE_UID = 981
SERVICE_GID = 981
_LOCK_MODE = 0o600
_MAX_MOUNT_BYTES = 1048576
_MIN_MOUNT_FIELDS = 6
_MIN_MOUNT_TRAILING_FIELDS = 3
_ERRORS = (OSError, ValueError, UnicodeError)


def refuse(message):
    raise ValueError(message)


def require_readonly_host_mount():
    """PID 1 sees host flags, independently of ProtectSystem=strict's view."""
    with MOUNTINFO.open("rb") as stream:
        body = stream.read(_MAX_MOUNT_BYTES + 1)
    if len(body) > _MAX_MOUNT_BYTES:
        refuse("host mount accounting exceeds bound")
    mounts = []
    for line in body.decode().splitlines():
        left, separator, right = line.partition(" - ")
        before, after = left.split(), right.split()
        if (
            not separator
            or len(before) < _MIN_MOUNT_FIELDS
            or len(after) < _MIN_MOUNT_TRAILING_FIELDS
        ):
            refuse("host mount accounting is unavailable")
        path = re.sub(r"\\([0-7]{3})", lambda match: chr(int(match[1], 8)), before[4])
        if path == "/srv/hfcache" and after[0] != "autofs":
            mounts.append((after[0], set(before[5].split(","))))
    if (
        len(mounts) != 1
        or mounts[0][0] not in {"nfs", "nfs4"}
        or "ro" not in mounts[0][1]
        or "rw" in mounts[0][1]
    ):
        refuse("host read-only NFS barrier is unavailable")


@contextmanager
def hold_original_lock():
    parent = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    descriptor = -1
    try:
        for part in LOCK_PATH.parent.parts[1:]:
            child = os.open(
                part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=parent
            )
            os.close(parent)
            parent = child
        descriptor = os.open(
            LOCK_PATH.name,
            os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
            dir_fd=parent,
        )
        info = os.fstat(descriptor)
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_uid != SERVICE_UID
            or info.st_gid != SERVICE_GID
            or stat.S_IMODE(info.st_mode) != _LOCK_MODE
            or info.st_nlink != 1
        ):
            refuse("original archive lock is unsafe")
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        linked = os.stat(LOCK_PATH.name, dir_fd=parent, follow_symlinks=False)
        if (linked.st_dev, linked.st_ino) != (info.st_dev, info.st_ino):
            refuse("original archive lock path changed")
        require_readonly_host_mount()
        yield info
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        os.close(parent)


def notify_ready():
    address = os.environ.get("NOTIFY_SOCKET", "")
    if not address or address[0] not in {"/", "@"} or "\0" in address:
        refuse("notification endpoint is unavailable")
    if address.startswith("@"):
        address = "\0" + address[1:]
    with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as notifier:
        notifier.sendto(
            b"READY=1\nSTATUS=Original archive lock held; host NFS is read-only", address
        )


class Stopped(BaseException):
    """Only main's signal handlers end the lifetime of the held descriptor."""


def stop(_signum, _frame):
    raise Stopped


def main():
    if sys.argv[1:] in (["--help"], ["-h"]):
        print(
            "Usage: /usr/local/libexec/hfcache-readonly-guard\n"
            "System-service host guard, independent of the application selector. "
            "Requires the existing original /run/hfcache/hfcache.lock and host "
            "read-only NFS mount evidence; holds its descriptor until stopped. "
            "No lock creation or NAS content I/O. Help takes no lock or signals."
        )
        return 0
    if len(sys.argv) != 1:
        sys.stderr.write("hfcache read-only guard accepts no arguments\n")
        return 20
    previous = {number: signal.signal(number, stop) for number in (signal.SIGTERM, signal.SIGINT)}
    try:
        with hold_original_lock() as info:
            notify_ready()
            print(
                json.dumps(
                    {
                        "state": "readonly-guard-held",
                        "device": info.st_dev,
                        "inode": info.st_ino,
                        "uid": info.st_uid,
                        "gid": info.st_gid,
                        "host_nfs_readonly": True,
                    },
                    sort_keys=True,
                ),
                flush=True,
            )
            while True:
                signal.pause()
    except Stopped:
        return 0
    except _ERRORS:
        sys.stderr.write("hfcache read-only guard refused; original state preserved\n")
        return 20
    finally:
        for number, handler in previous.items():
            signal.signal(number, handler)


if __name__ == "__main__":
    raise SystemExit(main())
