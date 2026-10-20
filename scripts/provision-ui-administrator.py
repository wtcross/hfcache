#!/usr/bin/env python3
"""Create one NEW local protected administrator record from non-echoing TTY input.

Run with the optional server environment. Passwords have no argument, environment
or file input. This creates a record only; installation and restart are separate.
"""

import argparse
import getpass
import hmac
import os
import runpy
import stat
import sys
import warnings
from pathlib import Path, PurePosixPath

MAXIMUM_PASSWORD_BYTES = 1024
MAXIMUM_RECORD_BYTES = 8192
RECORD_MODE = 0o600


class Arguments(argparse.ArgumentParser):
    def error(self, message):
        del message
        self.exit(2, "Provisioning arguments are invalid; use --help.\n")


def refuse():
    message = "administrator provisioning refused"
    raise ValueError(message)


def output_path(value):
    pure = PurePosixPath(value)
    if (
        not pure.is_absolute()
        or str(pure) != value
        or value.startswith("//")
        or ".." in pure.parts
        or "\\" in value
        or any(not character.isprintable() for character in value)
    ):
        refuse()
    # Reuse the reviewed local-filesystem/NAS exclusion before target traversal.
    helpers = runpy.run_path(str(Path(__file__).with_name("fetch-container-python.py")))
    return helpers["local_path"](Path(value))


def protected_directory(descriptor):
    info = os.fstat(descriptor)
    if (
        not stat.S_ISDIR(info.st_mode)
        or info.st_uid not in {0, os.geteuid()}
        or stat.S_IMODE(info.st_mode) & 0o022
    ):
        refuse()


def protected_parent(path):
    """Pin and validate EVERY ancestor, including the root, without symlinks."""
    descriptor = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        protected_directory(descriptor)
        for part in path.parent.parts[1:]:
            following = os.open(
                part,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                dir_fd=descriptor,
            )
            try:
                protected_directory(following)
            except BaseException:
                os.close(following)
                raise
            os.close(descriptor)
            descriptor = following
    except BaseException:
        os.close(descriptor)
        raise
    return descriptor


def password_input():
    if not sys.stdin.isatty() or not sys.stderr.isatty():
        refuse()
    with warnings.catch_warnings():
        warnings.simplefilter("error", getpass.GetPassWarning)
        first = getpass.getpass("Password: ").encode("utf-8")
        second = getpass.getpass("Confirm password: ").encode("utf-8")
    if (
        not first
        or len(first) > MAXIMUM_PASSWORD_BYTES
        or len(second) > MAXIMUM_PASSWORD_BYTES
        or not hmac.compare_digest(first, second)
    ):
        refuse()
    return first


def write_record(parent, name, payload):
    """Exclusive creation only; any created evidence survives all failures."""
    if not 0 < len(payload) <= MAXIMUM_RECORD_BYTES:
        refuse()
    descriptor = os.open(
        name,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
        RECORD_MODE,
        dir_fd=parent,
    )
    try:
        os.fchmod(descriptor, RECORD_MODE)
        identity = os.fstat(descriptor)
        view = memoryview(payload)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                refuse()
            view = view[written:]
        os.fsync(descriptor)
        current = os.fstat(descriptor)
        linked = os.stat(name, dir_fd=parent, follow_symlinks=False)
        if (
            not stat.S_ISREG(current.st_mode)
            or current.st_uid != os.geteuid()
            or stat.S_IMODE(current.st_mode) != RECORD_MODE
            or current.st_nlink != 1
            or current.st_size != len(payload)
            or (identity.st_dev, identity.st_ino) != (current.st_dev, current.st_ino)
            or (current.st_dev, current.st_ino) != (linked.st_dev, linked.st_ino)
        ):
            refuse()
        os.fsync(parent)
    finally:
        os.close(descriptor)


def provision(subject, username, output):
    if not sys.stdin.isatty() or not sys.stderr.isatty():
        refuse()
    path = output_path(output)
    parent = protected_parent(path)
    try:
        try:
            os.stat(path.name, dir_fd=parent, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            refuse()
        password = password_input()
        # --help and all preflight checks precede optional application imports.
        from hfcache.api.basic import create_administrator_record
        from hfcache.models import dump

        record = create_administrator_record(subject, username, password)
        payload = dump(record)
        write_record(parent, path.name, payload)
    finally:
        os.close(parent)


def main():
    parser = Arguments(description=__doc__)
    parser.add_argument("subject", help="Stable nonsecret ASCII identity, retained across rotation")
    parser.add_argument("username", help="Nonsecret Basic username")
    parser.add_argument(
        "--output", required=True, help="NEW absolute local file; existing files refuse"
    )
    options = parser.parse_args()
    try:
        provision(options.subject, options.username, options.output)
    except Exception, KeyboardInterrupt:  # noqa: BLE001 - never echo credential input or backend diagnostics
        print(
            "Administrator provisioning refused; retain any created file for review.",
            file=sys.stderr,
        )
        return 1
    print("Created protected administrator record. Installation and restart remain separate.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
