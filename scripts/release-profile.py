#!/usr/bin/env python3
"""Read-only positive native release classification; never execute candidate code.

Used by the native installer and diagnostics. Container, mixed and incomplete
layouts refuse. This identifies layout, not artifact authenticity or quiescence.
"""

import argparse
import hashlib
import json
import os
import re
import stat
import sys
import tomllib
from pathlib import Path

VERSION = re.compile(r"[0-9][A-Za-z0-9.+-]*\Z")
MAX_METADATA = 4194304
MAX_INDEX_FILES = 8192
MAX_INDEX_PATH = 1024
CONTAINER_MARKERS = ("container-release.json", "artifact-index.json", "rendered")
PROFILE_ERRORS = (OSError, ValueError, TypeError, KeyError)


def refuse(message):
    raise ValueError(message)


def directory(path, *, allow_missing=False):
    """Every component must be an ordinary directory, never a selected alias."""
    if not path.is_absolute() or ".." in path.parts:
        refuse("native profile requires an absolute ordinary directory")
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current /= part
        try:
            info = current.lstat()
        except FileNotFoundError:
            if allow_missing:
                return
            raise
        if not stat.S_ISDIR(info.st_mode):
            refuse("native profile directory is missing or linked")


def read_metadata(path, *, binary=False, maximum=MAX_METADATA):
    directory(path.parent)
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    try:
        before = os.fstat(descriptor)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_nlink != 1
            or not 0 <= before.st_size <= maximum
            or (not binary and before.st_size == 0)
        ):
            refuse("native profile metadata is not a bounded ordinary file")
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            raw = stream.read(maximum + 1)
        after = os.fstat(descriptor)
        if len(raw) != before.st_size or any(
            getattr(before, field) != getattr(after, field)
            for field in ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
        ):
            refuse("native profile metadata changed")
        return raw if binary else raw.decode("utf-8")
    finally:
        os.close(descriptor)


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            refuse("duplicate native index field")
        result[key] = value
    return result


def native_web_layout(path, version):  # noqa: PLR0912 - bounded native index structure and copied bytes
    if not os.path.lexists(path / "web-release.json"):
        return
    raw = read_metadata(path / "web-release.json")
    index = json.loads(raw, object_pairs_hook=_unique)
    if (
        not isinstance(index, dict)
        or set(index)
        != {
            "schema_version",
            "kind",
            "version",
            "source_commit",
            "source_files",
            "files",
            "ui_manifest_sha256",
        }
        or type(index["schema_version"]) is not int
        or index["schema_version"] != 1
        or index["kind"] != "hfcache_web_release"
        or index["version"] != version
        or not isinstance(index["source_commit"], str)
        or not re.fullmatch(r"[0-9a-f]{40}", index["source_commit"])
        or not isinstance(index["ui_manifest_sha256"], str)
        or not re.fullmatch(r"[0-9a-f]{64}", index["ui_manifest_sha256"])
        or json.dumps(index, sort_keys=True, indent=2, ensure_ascii=False) + "\n" != raw
    ):
        refuse("native web asset layout not proven")
    for field in ("source_files", "files"):
        records = index[field]
        if not isinstance(records, dict) or not records or len(records) > MAX_INDEX_FILES:
            refuse("native web index map not proven")
        for name, expected in records.items():
            if (
                not isinstance(name, str)
                or len(name) > MAX_INDEX_PATH
                or not re.fullmatch(r"[A-Za-z0-9._/@-]+", name)
                or name.startswith("/")
                or name.endswith("/")
                or any(part in {"", ".", ".."} for part in name.split("/"))
                or not isinstance(expected, str)
                or not re.fullmatch(r"[0-9a-f]{64}", expected)
            ):
                refuse("native web index member not proven")
    copied = {
        name: expected
        for name, expected in index["files"].items()
        if name.startswith(("ui/", "host-helper/"))
    }
    helpers = {
        "host-helper/" + name
        for name in (
            "host-helper.py",
            "hfcache-host-helper.service",
            "hfcache-host-helper.cil",
            "host_policy.py",
            "host_protocol.py",
            "host_peer.py",
            "host_configuration.py",
            "host_actions.py",
            "host_selinux.py",
        )
    }
    if (
        not helpers <= copied.keys()
        or copied.get("ui/manifest.json") != index["ui_manifest_sha256"]
    ):
        refuse("native web closure not proven")
    for name, expected in copied.items():
        if (
            hashlib.sha256(read_metadata(path / name, binary=True, maximum=8388608)).hexdigest()
            != expected
        ):
            refuse("native web member hash mismatch")
    actual = set()
    entries = 0
    for folder in ("ui", "host-helper"):
        directory(path / folder)
        for current, names, leaves in os.walk(path / folder, followlinks=False):
            entries += len(names) + len(leaves)
            if entries > MAX_INDEX_FILES:
                refuse("native web closure exceeds bound")
            for name in names:
                directory(Path(current) / name)
            for name in leaves:
                actual.add((Path(current) / name).relative_to(path).as_posix())
                if len(actual) > MAX_INDEX_FILES:
                    refuse("native web closure exceeds bound")
    if actual != copied.keys():
        refuse("native web closure differs")


def native_layout(path, *, installed=False, version=None):
    directory(path)
    if any(os.path.lexists(path / name) for name in CONTAINER_MARKERS):
        refuse("container or mixed release: use install-container-release.py")
    # WEB-021 adds one explicit native asset index. Unknown metadata still
    # refuses; this layout check grants neither authenticity nor activation.
    if any(item.suffix == ".json" and item.name != "web-release.json" for item in path.iterdir()):
        refuse("unknown release metadata: native profile not proven")
    project = tomllib.loads(read_metadata(path / "pyproject.toml")).get("project", {})
    if not isinstance(project, dict):
        refuse("native hfcache project not proven")
    found = project.get("version")
    if (
        project.get("name") != "hfcache"
        or not isinstance(found, str)
        or not VERSION.fullmatch(found)
        or (version is not None and found != version)
    ):
        refuse("native hfcache project/version not proven")
    if not re.fullmatch(r"3\.[0-9]+(?:\.[0-9]+)?\n?", read_metadata(path / ".python-version")):
        refuse("native Python pin not proven")
    lock = tomllib.loads(read_metadata(path / "uv.lock"))
    if type(lock.get("version")) is not int or not any(
        isinstance(row, dict) and row.get("name") == "hfcache" and row.get("version") == found
        for row in lock.get("package", [])
    ):
        refuse("native locked project not proven")
    for relative in ("src/hfcache/__init__.py", "src/hfcache/cli.py"):
        read_metadata(path / relative)
    native_web_layout(path, found)
    if installed:
        directory(path / ".venv/bin")
        read_metadata(path / ".venv/pyvenv.cfg")
        entrypoint = path / ".venv/bin/hfcache"
        read_metadata(entrypoint)
        # A managed venv's Python is legitimately a symlink. Never execute it to
        # classify the release; executable availability is structural evidence.
        python = path / ".venv/bin/python"
        if (
            not os.access(entrypoint, os.X_OK)
            or not os.access(python, os.X_OK)
            or not stat.S_ISREG(python.stat().st_mode)
        ):
            refuse("native built environment not proven")
    return found


def native_selection(prefix, *, allow_missing=False):
    directory(prefix, allow_missing=allow_missing)
    current = prefix / "current"
    if not os.path.lexists(current):
        if allow_missing:
            if prefix.exists():
                directory(prefix)
                if any(os.path.lexists(prefix / name) for name in CONTAINER_MARKERS):
                    refuse("container profile at install prefix")
            return None
        refuse("native current selector missing")
    directory(prefix / "releases")
    if not current.is_symlink():
        refuse("unknown current selector preserved")
    selected = os.readlink(current)  # noqa: PTH115 - preserve raw selector spelling for exact grammar
    match = re.fullmatch(r"releases/([0-9][A-Za-z0-9.+-]*)", selected)
    if match is None:
        refuse("external or malformed current selector preserved")
    target = prefix / selected
    native_layout(target, installed=True, version=match[1])
    return target


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prefix", type=Path, required=True, help="native install prefix")
    parser.add_argument(
        "--source", type=Path, help="positive native source tree; permits fresh install"
    )
    parser.add_argument("--target", help="existing native release version to select")
    parser.add_argument(
        "--print-source-version",
        action="store_true",
        help="emit the validated TOML project version for native staging",
    )
    options = parser.parse_args(argv)
    version = None
    try:
        native_selection(
            options.prefix, allow_missing=options.source is not None or options.target is not None
        )
        if options.source is not None:
            version = native_layout(options.source)
            destination = options.prefix / "releases" / version
            if os.path.lexists(destination):
                native_layout(destination, installed=True, version=version)
        elif options.print_source_version:
            refuse("source version output requires a source")
        if options.target is not None:
            if not VERSION.fullmatch(options.target):
                refuse("invalid native target version")
            native_layout(
                options.prefix / "releases" / options.target,
                installed=True,
                version=options.target,
            )
    except PROFILE_ERRORS:
        print(
            "native profile refused: container, mixed, unknown or incomplete layout; "
            "use the matching profile installer and preserve current/state",
            file=sys.stderr,
        )
        return 20
    if options.print_source_version:
        print(version)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
