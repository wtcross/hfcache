#!/usr/bin/python3
"""Bounded, Node-independent installation checks for explicit web releases.

Decision143/147: the original Python UI schema validates construction and API
startup. This standard-library installer verifies the captured manifest and
indexed bytes before effects; it does not grant policy or enable services.
"""

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import tomllib
from email.parser import BytesParser
from pathlib import Path, PurePosixPath

HEX = re.compile(r"[0-9a-f]{64}\Z")
COMMIT = re.compile(r"[0-9a-f]{40}\Z")
COMPONENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,254}\Z")
SOURCE_COMPONENT = re.compile(r"[A-Za-z0-9._@][A-Za-z0-9._@-]{0,254}\Z")
PYTHON_COMPONENT = re.compile(r"[A-Za-z0-9._@+][A-Za-z0-9._@+-]{0,254}\Z")
MAX_MEMBER = 8388608
MAX_TOTAL = 67108864
MAX_MANIFEST = 2097152
MAX_PATH = 1024
MAX_SOURCE_DEPTH = 16
MAX_ASSET_DEPTH = 8
MAX_TOOL = 64
MAX_VERSION = 128
MAX_MEMBERS = 4096
MAX_DIRECTORIES = 4096
MAX_ENTRIES = 8193
MAX_RELEASE_FILES = 8192
MAX_RELEASE_BYTES = 268435456
MOUNT_MIN_FIELDS = 5
DIRECTORY_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
SHIPPED_FILES = frozenset({".python-version", "LICENSE", "README.md", "pyproject.toml", "uv.lock"})
SHIPPED_TREES = frozenset({"src", "scripts", "packaging", "docs", "examples"})
HELPER = {
    "host-helper.py": "scripts/host-helper.py",
    "hfcache-host-helper.service": "packaging/systemd/hfcache-host-helper.service",
    "hfcache-host-helper.cil": "packaging/selinux/hfcache-host-helper.cil",
    **{
        name + ".py": "src/hfcache/" + name + ".py"
        for name in (
            "host_policy",
            "host_protocol",
            "host_peer",
            "host_configuration",
            "host_actions",
            "host_selinux",
        )
    },
}
RELEASE_ERRORS = (
    OSError,
    ValueError,
    TypeError,
    KeyError,
    RecursionError,
    subprocess.SubprocessError,
)
PYTHON_OWNER = 0
MAX_PYTHON_ENTRIES = 32768
MAX_PYTHON_BYTES = 536870912
MAX_PYTHON_DEPTH = 32
MAX_PYTHON_PATH = 4096
MAX_PYTHON_LINKS = 40
MAX_PYTHON_PROBE = 4096
PIP_VERSION = "26.1.2"
MIME = {
    ".html": "text/html",
    ".css": "text/css",
    ".js": "text/javascript",
    ".json": "application/json",
    ".png": "image/png",
    ".webp": "image/webp",
    ".woff2": "font/woff2",
}


def require(condition, message="web release refused"):
    if not condition:
        raise ValueError(message)


def digest(body):
    return hashlib.sha256(body).hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode()


def _unique(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate release field")
        result[key] = value
    return result


def decode(body):
    return json.loads(
        body,
        object_pairs_hook=_unique,
        parse_constant=_nonfinite,
    )


def _nonfinite(_):
    message = "nonfinite release field"
    raise ValueError(message)


def relative(name, *, asset=False):
    require(isinstance(name, str) and 0 < len(name) <= MAX_PATH)
    parts = name.split("/")
    component = COMPONENT if asset else SOURCE_COMPONENT
    require(len(parts) <= MAX_SOURCE_DEPTH and all(component.fullmatch(part) for part in parts))
    require(not asset or len(parts) <= MAX_ASSET_DEPTH)
    require(all(part not in {".", ".."} for part in parts))
    return PurePosixPath(name)


def _identity(info):
    return tuple(
        getattr(info, field)
        for field in (
            "st_dev",
            "st_ino",
            "st_mode",
            "st_uid",
            "st_gid",
            "st_nlink",
            "st_size",
            "st_mtime_ns",
            "st_ctime_ns",
        )
    )


def local(path):
    """Reject network mounts and symlink ancestry before reading release files."""
    path = Path(os.path.abspath(path))  # noqa: PTH100 - no symlink resolution before mount proof
    require(path != Path("/srv") and Path("/srv") not in path.parents)
    matches = []
    for line in Path("/proc/self/mountinfo").read_text().splitlines():
        left, separator, right = line.partition(" - ")
        fields = left.split()
        if separator and len(fields) >= MOUNT_MIN_FIELDS:
            mount = Path(re.sub(r"\\([0-7]{3})", lambda m: chr(int(m[1], 8)), fields[4]))
            if path == mount or mount in path.parents:
                matches.append((len(mount.parts), right.split()[0]))
    require(
        matches and max(matches)[1] in {"ext2", "ext3", "ext4", "xfs", "btrfs", "tmpfs", "overlay"}
    )
    current = Path("/")
    for part in path.parts[1:]:
        current /= part
        require(not stat.S_ISLNK(current.lstat().st_mode), "symlink release path")
    return path


def read_file(path, maximum=MAX_MEMBER, *, directory=None):
    descriptor = os.open(
        path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=directory
    )
    try:
        before = os.fstat(descriptor)
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1)
        require(0 <= before.st_size <= maximum)
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            body = stream.read(maximum + 1)
        require(
            len(body) == before.st_size and _identity(before) == _identity(os.fstat(descriptor))
        )
        require(
            _identity(before) == _identity(os.stat(path, dir_fd=directory, follow_symlinks=False))
        )
        return body
    finally:
        os.close(descriptor)


def open_directory(path):
    """Open an absolute directory without following any ancestor symlink."""
    descriptor = os.open("/", DIRECTORY_FLAGS)
    try:
        for part in path.parts[1:]:
            child = os.open(part, DIRECTORY_FLAGS, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
    except BaseException:
        os.close(descriptor)
        raise
    else:
        return descriptor


def capture_tree(root, descriptor, indexed, raw):
    """Capture the exact indexed tree; directory reads and errors are explicit."""
    directories = {
        parent.as_posix()
        for name in indexed
        for parent in PurePosixPath(name).parents
        if parent != PurePosixPath(".")
    }
    require(len(directories) + 1 <= MAX_DIRECTORIES, "web directory bound exceeded")
    require(len(directories) + len(indexed) + 1 <= MAX_ENTRIES, "web entry bound exceeded")
    files = {}
    entries_seen = 0

    def capture(parent, prefix):
        nonlocal entries_seen
        before = os.fstat(parent)
        require(stat.S_ISDIR(before.st_mode))
        names = []
        with os.scandir(parent) as entries:
            for entry in entries:
                entries_seen += 1
                require(entries_seen <= MAX_ENTRIES, "web entry bound exceeded")
                names.append(entry.name)
        for leaf in sorted(names):
            name = prefix + leaf
            relative(name, asset=True)
            info = os.stat(leaf, dir_fd=parent, follow_symlinks=False)
            require(not stat.S_ISLNK(info.st_mode), "symlink web member")
            if stat.S_ISDIR(info.st_mode):
                require(name in directories, "extra web directory")
                child = os.open(leaf, DIRECTORY_FLAGS, dir_fd=parent)
                try:
                    require(_identity(info) == _identity(os.fstat(child)))
                    capture(child, name + "/")
                finally:
                    os.close(child)
                require(
                    _identity(info)
                    == _identity(os.stat(leaf, dir_fd=parent, follow_symlinks=False))
                )
            else:
                require(name == "manifest.json" or name in indexed, "extra web member")
                if name == "manifest.json":
                    body = read_file(leaf, MAX_MANIFEST, directory=parent)
                    require(body == raw, "web manifest changed during capture")
                else:
                    member = indexed[name]
                    body = read_file(leaf, member["bytes"], directory=parent)
                    require(
                        len(body) == member["bytes"] and digest(body) == member["sha256"],
                        "web member hash mismatch",
                    )
                files[name] = body
        require(_identity(before) == _identity(os.fstat(parent)), "web directory changed")

    before = _identity(os.fstat(descriptor))
    capture(descriptor, "")
    require(set(files) == {"manifest.json", *indexed}, "missing web member")
    fresh = open_directory(root)
    try:
        require(before == _identity(os.fstat(fresh)), "web root changed")
    finally:
        os.close(fresh)
    return files


def parse_assets(  # noqa: PLR0913 - one pure bounded manifest authority
    raw,
    expected,
    *,
    application_version,
    source_commit=None,
    require_clean=False,
    wire_source_digest=None,
    pnpm_lock_sha256=None,
):
    """Validate captured manifest bytes without filesystem or deployment effects."""
    require(isinstance(expected, str) and HEX.fullmatch(expected))
    require(isinstance(raw, bytes) and 0 < len(raw) <= MAX_MANIFEST)
    require(digest(raw) == expected, "web manifest hash mismatch")
    manifest = decode(raw)
    require(
        isinstance(manifest, dict)
        and set(manifest)
        == {
            "schema_version",
            "kind",
            "build",
            "entrypoint",
            "meta_identity",
            "members",
        }
    )
    require(encoded(manifest) == raw, "noncanonical web manifest")
    require(type(manifest["schema_version"]) is int and manifest["schema_version"] == 1)
    require(manifest["kind"] == "hfcache_web_assets" and manifest["entrypoint"] == "index.html")
    require(
        manifest["meta_identity"]
        == {
            "ui_base": "__HFCACHE_UI_BASE_V1__",
            "bootstrap_path": "__HFCACHE_UI_BOOTSTRAP_V1__",
            "asset_fingerprint": "__HFCACHE_UI_FINGERPRINT_V1__",
            "ui_contract": "__HFCACHE_UI_CONTRACT_V1__",
        }
    )
    build = manifest["build"]
    require(
        isinstance(build, dict)
        and set(build)
        == {
            "application_version",
            "source_commit",
            "source_snapshot_sha256",
            "source_dirty",
            "ui_contract_version",
            "rest_api_schema_version",
            "wire_source_digest",
            "pnpm_lock_sha256",
            "toolchain",
            "toolchain_sha256",
            "licenses_sha256",
            "notices_sha256",
        }
    )
    require(build["application_version"] == application_version, "web/backend version mismatch")
    require(
        isinstance(build["application_version"], str)
        and 0 < len(build["application_version"]) <= MAX_VERSION
        and build["application_version"].isascii()
        and build["application_version"].isprintable()
    )
    require(isinstance(build["source_commit"], str) and COMMIT.fullmatch(build["source_commit"]))
    require(source_commit is None or build["source_commit"] == source_commit, "web/source mismatch")
    require(
        type(build["source_dirty"]) is bool and (not require_clean or not build["source_dirty"])
    )
    for key in ("ui_contract_version", "rest_api_schema_version"):
        require(type(build[key]) is int and build[key] == 1)
    for key in (
        "source_snapshot_sha256",
        "wire_source_digest",
        "pnpm_lock_sha256",
        "toolchain_sha256",
        "licenses_sha256",
        "notices_sha256",
    ):
        require(isinstance(build[key], str) and HEX.fullmatch(build[key]))
    require(wire_source_digest is None or build["wire_source_digest"] == wire_source_digest)
    require(pnpm_lock_sha256 is None or build["pnpm_lock_sha256"] == pnpm_lock_sha256)
    tools = build["toolchain"]
    require(isinstance(tools, dict) and set(tools) == {"node", "pnpm", "typescript", "vite"})
    require(
        all(
            isinstance(v, str) and 0 < len(v) <= MAX_TOOL and v.isascii() and v.isprintable()
            for v in tools.values()
        )
    )
    require(digest(encoded(tools)) == build["toolchain_sha256"])
    members = manifest["members"]
    require(isinstance(members, list) and 1 <= len(members) <= MAX_MEMBERS)
    indexed = {}
    total = 0
    for member in members:
        require(isinstance(member, dict) and set(member) == {"path", "bytes", "sha256", "mime"})
        name = member["path"]
        path = relative(name, asset=True)
        require(name not in indexed and name != "manifest.json")
        require(type(member["bytes"]) is int and 0 <= member["bytes"] <= MAX_MEMBER)
        require(isinstance(member["sha256"], str) and HEX.fullmatch(member["sha256"]))
        require(
            name in {"index.html", "licenses.json", "THIRD_PARTY_NOTICES.txt"}
            or name.startswith("assets/")
        )
        mime = "text/plain" if name == "THIRD_PARTY_NOTICES.txt" else MIME.get(path.suffix)
        require(mime is not None and member["mime"] == mime)
        require(member["mime"] != "text/html" or (name == "index.html" and member["bytes"] > 0))
        indexed[name] = member
        total += member["bytes"]
    require(list(indexed) == sorted(indexed) and total <= MAX_TOTAL)
    require({"index.html", "licenses.json", "THIRD_PARTY_NOTICES.txt"} <= indexed.keys())
    require(indexed["licenses.json"]["sha256"] == build["licenses_sha256"])
    require(indexed["THIRD_PARTY_NOTICES.txt"]["sha256"] == build["notices_sha256"])
    return manifest, indexed


def load_assets(  # noqa: PLR0913 - shared pure authority plus protected installation tree capture
    root,
    expected,
    *,
    application_version,
    source_commit=None,
    require_clean=False,
    wire_source_digest=None,
    pnpm_lock_sha256=None,
):
    """Return the canonical manifest and immutable bytes, including manifest.json."""
    require(isinstance(expected, str) and HEX.fullmatch(expected))
    root = local(root)
    descriptor = open_directory(root)
    try:
        raw = read_file("manifest.json", MAX_MANIFEST, directory=descriptor)
    finally:
        os.close(descriptor)
    manifest, indexed = parse_assets(
        raw,
        expected,
        application_version=application_version,
        source_commit=source_commit,
        require_clean=require_clean,
        wire_source_digest=wire_source_digest,
        pnpm_lock_sha256=pnpm_lock_sha256,
    )
    descriptor = open_directory(root)
    try:
        files = capture_tree(root, descriptor, indexed, raw)
    finally:
        os.close(descriptor)
    return manifest, files


def verify_native(release, expected, source):
    """Bind an explicit release index to all native source and artifact bytes."""
    release, source = local(release), local(source)
    require(isinstance(expected, str) and HEX.fullmatch(expected))
    raw = read_file(release / "web-release.json", MAX_MANIFEST)
    require(digest(raw) == expected, "release index hash mismatch")
    index = decode(raw)
    require(
        isinstance(index, dict)
        and set(index)
        == {
            "schema_version",
            "kind",
            "version",
            "source_commit",
            "source_files",
            "files",
            "ui_manifest_sha256",
        }
    )
    require(encoded(index) == raw)
    require(type(index["schema_version"]) is int and index["schema_version"] == 1)
    require(index["kind"] == "hfcache_web_release")
    require(isinstance(index["source_commit"], str) and COMMIT.fullmatch(index["source_commit"]))
    require(
        isinstance(index["version"], str)
        and re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", index["version"])
    )
    require(isinstance(index["files"], dict) and isinstance(index["source_files"], dict))
    require(
        SHIPPED_FILES | set(HELPER.values()) | {"web/src/wire/contracts.json", "web/pnpm-lock.yaml"}
        <= index["source_files"].keys(),
        "missing release source closure",
    )
    require(
        all(
            index["files"].get("host-helper/" + name) == index["source_files"][original]
            for name, original in HELPER.items()
        ),
        "missing or mismatched host helper closure",
    )
    for key, parent in (("source_files", source), ("files", release)):
        records = index[key]
        require(isinstance(records, dict) and 1 <= len(records) <= MAX_RELEASE_FILES)
        total = 0
        for name, wanted in records.items():
            relative(name)
            require(isinstance(wanted, str) and HEX.fullmatch(wanted))
            path = local(parent / name)
            body = read_file(path, MAX_TOTAL)
            total += len(body)
            require(
                total <= MAX_RELEASE_BYTES and digest(body) == wanted, "release input hash mismatch"
            )
    version = tomllib.loads(read_file(source / "pyproject.toml").decode())["project"]["version"]
    wire = decode(read_file(source / "web/src/wire/contracts.json"))["source_digest"]
    require(index["version"] == version)
    _, assets = load_assets(
        release / "ui",
        index["ui_manifest_sha256"],
        application_version=version,
        source_commit=index["source_commit"],
        require_clean=True,
        wire_source_digest=wire,
        pnpm_lock_sha256=digest(read_file(source / "web/pnpm-lock.yaml")),
    )
    ui_files = {"ui/" + name: digest(body) for name, body in assets.items()}
    require(
        {name: value for name, value in index["files"].items() if name.startswith("ui/")}
        == ui_files
    )
    require(
        f"wheels/hfcache-{version}-py3-none-any.whl" in index["files"],
        "missing release wheel",
    )
    require(
        set(index["files"])
        <= {
            *ui_files,
            *("host-helper/" + name for name in HELPER),
            f"wheels/hfcache-{version}-py3-none-any.whl",
            f"wheels/hfcache-{version}.tar.gz",
        },
        "unexpected release artifact",
    )
    for name in ("host-helper", "wheels"):
        descriptor = open_directory(release / name)
        before = _identity(os.fstat(descriptor))
        try:
            with os.scandir(descriptor) as entries:
                actual = set()
                for entry in entries:
                    actual.add(name + "/" + entry.name)
                    require(actual <= index["files"].keys(), "extra release artifact")
                require(
                    actual == {path for path in index["files"] if path.startswith(name + "/")},
                    "missing release artifact",
                )
            require(before == _identity(os.fstat(descriptor)), "release artifact directory changed")
        finally:
            os.close(descriptor)
    verify_shipped_source(source, index["source_files"])
    return index


def verify_shipped_source(source, records):  # noqa: PLR0915 - one bounded exact source walk
    """Refuse missing, extra or aliased content that the native installer ships."""
    require(records.keys() >= SHIPPED_FILES, "missing shipped source")
    wanted = {
        name
        for name in records
        if name in SHIPPED_FILES or PurePosixPath(name).parts[0] in SHIPPED_TREES
    }
    directories = {
        parent.as_posix()
        for name in wanted
        for parent in PurePosixPath(name).parents
        if parent != PurePosixPath(".")
    }
    require(len(directories) <= MAX_RELEASE_FILES, "source directory bound exceeded")
    require(directories >= SHIPPED_TREES, "missing shipped source tree")
    seen = set()
    entries_seen = 0
    total = 0

    def verify(parent, prefix):
        nonlocal entries_seen, total
        before = _identity(os.fstat(parent))
        with os.scandir(parent) as entries:
            for entry in entries:
                entries_seen += 1
                require(entries_seen <= MAX_RELEASE_FILES * 2, "source entry bound exceeded")
                name = prefix + entry.name
                relative(name)
                info = os.stat(entry.name, dir_fd=parent, follow_symlinks=False)
                require(not stat.S_ISLNK(info.st_mode), "symlink shipped source")
                if stat.S_ISDIR(info.st_mode):
                    require(name in directories, "extra shipped source directory")
                    child = os.open(entry.name, DIRECTORY_FLAGS, dir_fd=parent)
                    try:
                        require(_identity(info) == _identity(os.fstat(child)))
                        verify(child, name + "/")
                    finally:
                        os.close(child)
                    require(
                        _identity(info)
                        == _identity(os.stat(entry.name, dir_fd=parent, follow_symlinks=False))
                    )
                else:
                    require(name in wanted, "extra shipped source file")
                    body = read_file(entry.name, MAX_TOTAL, directory=parent)
                    total += len(body)
                    require(
                        total <= MAX_RELEASE_BYTES and digest(body) == records[name],
                        "shipped source hash mismatch",
                    )
                    seen.add(name)
        require(before == _identity(os.fstat(parent)), "shipped source directory changed")

    descriptor = open_directory(local(source))
    try:
        for name in sorted(SHIPPED_FILES):
            body = read_file(name, MAX_TOTAL, directory=descriptor)
            total += len(body)
            require(
                total <= MAX_RELEASE_BYTES and digest(body) == records[name],
                "shipped source hash mismatch",
            )
            seen.add(name)
        for name in sorted(SHIPPED_TREES):
            info = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
            child = os.open(name, DIRECTORY_FLAGS, dir_fd=descriptor)
            try:
                require(_identity(info) == _identity(os.fstat(child)))
                verify(child, name + "/")
            finally:
                os.close(child)
            require(
                _identity(info)
                == _identity(os.stat(name, dir_fd=descriptor, follow_symlinks=False))
            )
    finally:
        os.close(descriptor)
    require(seen == wanted, "missing shipped source file")


def _stage_parent(destination, name, created):
    descriptor = os.dup(destination)
    prefix = ""
    try:
        for part in PurePosixPath(name).parts[:-1]:
            prefix += part + "/"
            if prefix not in created:
                os.mkdir(part, mode=0o755, dir_fd=descriptor)
                created.add(prefix)
            child = os.open(part, DIRECTORY_FLAGS, dir_fd=descriptor)
            os.fchmod(child, 0o755)
            os.close(descriptor)
            descriptor = child
    except BaseException:
        os.close(descriptor)
        raise
    else:
        return descriptor


def _write_new(directory, name, body, *, mode=0o644):
    descriptor = os.open(
        name,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
        mode=mode,
        dir_fd=directory,
    )
    try:
        with os.fdopen(descriptor, "wb", closefd=False) as stream:
            stream.write(body)
            stream.flush()
            os.fchmod(descriptor, mode)
            os.fsync(descriptor)
    finally:
        os.close(descriptor)


def stage_native(release, destination, index, expected):
    """Recheck every copied byte and create only new, descriptor-anchored paths."""
    release, destination = local(release), local(destination)
    verify_shipped_source(destination, index["source_files"])
    descriptor = open_directory(destination)
    created = set()
    try:
        for name in sorted(index["files"]):
            if not name.startswith(("ui/", "host-helper/")):
                continue
            relative(name)
            body = read_file(local(release / name), MAX_TOTAL)
            require(digest(body) == index["files"][name], "release changed before staging")
            parent = _stage_parent(descriptor, name, created)
            try:
                _write_new(parent, PurePosixPath(name).name, body)
            finally:
                os.close(parent)
        raw = read_file(release / "web-release.json", MAX_MANIFEST)
        require(
            digest(raw) == expected and raw == encoded(index),
            "release index changed before staging",
        )
        _write_new(descriptor, "web-release.json", raw)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def python_inventory(root):
    """Capture ordinary protected Python bytes and relative links without executing them."""
    records, identities = {}, {}
    total = 0

    def walk(parent, prefix, depth):
        nonlocal total
        require(depth <= MAX_PYTHON_DEPTH, "Python tree depth exceeded")
        before = os.fstat(parent)
        require(before.st_uid == before.st_gid == PYTHON_OWNER)
        require(stat.S_ISDIR(before.st_mode) and not before.st_mode & 0o7022)
        identities[prefix] = _identity(before)
        with os.scandir(parent) as entries:
            names = []
            for entry in entries:
                require(
                    len(records) + len(names) < MAX_PYTHON_ENTRIES, "Python tree bound exceeded"
                )
                names.append(entry.name)
        for leaf in sorted(names):
            name = prefix + leaf
            require(PYTHON_COMPONENT.fullmatch(leaf), "unsupported Python member name")
            require(len(name) <= MAX_PYTHON_PATH, "Python member path exceeded")
            require(len(records) < MAX_PYTHON_ENTRIES, "Python tree bound exceeded")
            info = os.stat(leaf, dir_fd=parent, follow_symlinks=False)
            require(info.st_uid == info.st_gid == PYTHON_OWNER)
            identities[name] = _identity(info)
            mode = stat.S_IMODE(info.st_mode)
            if stat.S_ISDIR(info.st_mode):
                records[name] = {"kind": "directory", "mode": mode}
                child = os.open(leaf, DIRECTORY_FLAGS, dir_fd=parent)
                try:
                    require(_identity(info) == _identity(os.fstat(child)))
                    walk(child, name + "/", depth + 1)
                finally:
                    os.close(child)
            elif stat.S_ISREG(info.st_mode):
                require(info.st_nlink == 1 and not mode & 0o7022)
                body = read_file(leaf, MAX_TOTAL, directory=parent)
                total += len(body)
                require(total <= MAX_PYTHON_BYTES, "Python byte bound exceeded")
                records[name] = {
                    "kind": "file",
                    "mode": mode,
                    "bytes": len(body),
                    "sha256": digest(body),
                }
            else:
                require(stat.S_ISLNK(info.st_mode) and info.st_nlink == 1, "special Python member")
                target = os.readlink(leaf, dir_fd=parent)
                require(
                    0 < len(target) <= MAX_PYTHON_PATH and not target.startswith("/"),
                    "external Python link",
                )
                records[name] = {"kind": "symlink", "target": target}
            require(
                _identity(info) == _identity(os.stat(leaf, dir_fd=parent, follow_symlinks=False))
            )
        require(_identity(before) == _identity(os.fstat(parent)), "Python directory changed")

    descriptor = open_directory(local(root))
    try:
        walk(descriptor, "", 0)
    finally:
        os.close(descriptor)
    return records, identities


def python_link_target(name, target, records):
    """Resolve only captured relative link text, never follow an external pathname."""
    pending = [*PurePosixPath(name).parent.parts, *target.split("/")]
    parts = []
    links = 0
    while pending:
        part = pending.pop(0)
        if part in {"", "."}:
            continue
        if part == "..":
            require(parts, "escaping Python link")
            parts.pop()
            continue
        require(PYTHON_COMPONENT.fullmatch(part), "unsupported Python link")
        parts.append(part)
        record = records.get("/".join(parts))
        require(record is not None, "dangling Python link")
        if record["kind"] == "symlink":
            links += 1
            require(links <= MAX_PYTHON_LINKS, "cyclic Python link")
            parts.pop()
            pending = [*record["target"].split("/"), *pending]
        elif pending:
            require(record["kind"] == "directory", "nondirectory Python link")
    return "/".join(parts)


def probe_python(interpreter, version, root, *, managers):
    """Run only the already protected exact interpreter, isolated and without bytecode writes."""
    result = subprocess.run(  # noqa: S603 - protected fixed interpreter and literal probe, no shell
        [
            str(interpreter),
            "-I",
            "-B",
            "-c",
            (
                "import importlib.util,json,sys; "
                "print(json.dumps({'version':'.'.join(map(str,sys.version_info[:3])),"
                "'implementation':sys.implementation.name,'prefix':sys.prefix,"
                "'base_prefix':sys.base_prefix,'managers':any(importlib.util.find_spec(n) "
                "is not None for n in ('pip','ensurepip'))},sort_keys=True))"
            ),
        ],
        check=True,
        capture_output=True,
        timeout=30,
        env={
            "PATH": "/usr/bin:/bin",
            "HOME": "/nonexistent",
            "LC_ALL": "C.UTF-8",
            "PYTHONDONTWRITEBYTECODE": "1",
        },
    )
    require(len(result.stdout) <= MAX_PYTHON_PROBE and not result.stderr, "Python probe failed")
    require(
        decode(result.stdout)
        == {
            "version": version,
            "implementation": "cpython",
            "prefix": str(root),
            "base_prefix": str(root),
            "managers": managers,
        },
        "Python version, relocation or package managers differ",
    )


def prepare_python(  # noqa: PLR0912, PLR0915 - one retained immutable copy
    interpreter, python_root, source, index
):
    """Copy the selected native donor; omit only its known optional pip installation."""
    require(os.geteuid() == PYTHON_OWNER, "prepare Python as the protected installer")
    interpreter, python_root = local(interpreter), local(python_root)
    for parent in (python_root, *python_root.parents):
        info = parent.lstat()
        require(stat.S_ISDIR(info.st_mode) and info.st_uid in {0, PYTHON_OWNER})
        require(not info.st_mode & 0o022 or (info.st_uid == 0 and info.st_mode & stat.S_ISVTX))
    pin = read_file(source / ".python-version")
    require(digest(pin) == index["source_files"][".python-version"], "Python pin changed")
    version = pin.decode("ascii").strip()
    require(re.fullmatch(r"3\.[0-9]+\.[0-9]+", version), "full Python patch pin required")
    minor = ".".join(version.split(".")[:2])
    donor = interpreter.parent.parent
    require(
        donor.parent == python_root
        and donor.name == f"cpython-{version}-linux-{os.uname().machine}-gnu",
        "unexpected managed Python donor",
    )
    require(interpreter == donor / "bin" / ("python" + minor), "unexpected Python executable")
    records, identities = python_inventory(donor)
    require(records.get("bin/python" + minor, {}).get("kind") == "file")
    require(records["bin/python" + minor]["mode"] & 0o111, "Python executable is not executable")
    roots = {
        "bin/pip",
        "bin/pip3",
        "bin/pip" + minor,
        f"lib/python{minor}/ensurepip",
        f"lib/python{minor}/site-packages/pip",
        f"lib/python{minor}/site-packages/pip-{PIP_VERSION}.dist-info",
    }
    require(roots <= records.keys(), "known Python installer closure is incomplete")
    require(
        all(not name.startswith("bin/pip") or name in roots for name in records)
        and all(
            not (name.startswith(f"lib/python{minor}/site-packages/pip-") and ".dist-info" in name)
            or name == f"lib/python{minor}/site-packages/pip-{PIP_VERSION}.dist-info"
            or name.startswith(f"lib/python{minor}/site-packages/pip-{PIP_VERSION}.dist-info/")
            for name in records
        ),
        "unknown Python installer member",
    )
    for name in roots:
        require(records[name]["kind"] == ("file" if name.startswith("bin/") else "directory"))
    metadata = BytesParser().parsebytes(
        read_file(
            donor / f"lib/python{minor}/site-packages/pip-{PIP_VERSION}.dist-info/METADATA", 65536
        )
    )
    require(
        metadata.get_all("Name") == ["pip"] and metadata.get_all("Version") == [PIP_VERSION],
        "unexpected Python installer metadata",
    )
    omitted = {
        name
        for name in records
        if any(name == root or name.startswith(root + "/") for root in roots)
    }
    retained = {name: record for name, record in records.items() if name not in omitted}
    for name, record in records.items():
        if record["kind"] == "symlink":
            target = python_link_target(name, record["target"], records)
            require(
                name in omitted or target not in omitted, "Python link depends on omitted installer"
            )
    probe_python(interpreter, version, donor, managers=True)
    require(python_inventory(donor) == (records, identities), "Python donor changed")
    destination = python_root / ("web-" + index["version"] + "-" + index["source_commit"])
    destination.mkdir(mode=0o700)
    for name in sorted(retained, key=lambda item: (len(PurePosixPath(item).parts), item)):
        record = retained[name]
        target = destination / name
        if record["kind"] == "directory":
            target.mkdir(mode=record["mode"])
            target.chmod(record["mode"])
        elif record["kind"] == "symlink":
            target.symlink_to(record["target"])
        else:
            parent = open_directory(donor / PurePosixPath(name).parent)
            try:
                body = read_file(PurePosixPath(name).name, MAX_TOTAL, directory=parent)
            finally:
                os.close(parent)
            require(
                len(body) == record["bytes"] and digest(body) == record["sha256"],
                "Python donor changed during copy",
            )
            parent = open_directory(target.parent)
            try:
                _write_new(parent, target.name, body, mode=record["mode"])
            finally:
                os.close(parent)
    copied, _copied_identities = python_inventory(destination)
    require(copied == retained, "copied Python differs")
    require(python_inventory(donor) == (records, identities), "Python donor changed during copy")
    executable = destination / "bin" / ("python" + minor)
    probe_python(executable, version, destination, managers=False)
    for directory, _names, _leaves in os.walk(destination, topdown=False, followlinks=False):
        descriptor = open_directory(Path(directory))
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    destination.chmod(0o755)
    descriptor = open_directory(destination)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    descriptor = open_directory(python_root)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return executable


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("verify-native", "stage-native", "prepare-python"))
    parser.add_argument("--release", type=Path, required=True)
    parser.add_argument("--index-sha256", required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--destination", type=Path)
    parser.add_argument("--interpreter", type=Path)
    parser.add_argument("--python-root", type=Path)
    options = parser.parse_args()
    try:
        index = verify_native(options.release, options.index_sha256, options.source)
        if options.mode == "prepare-python":
            require(options.interpreter is not None and options.python_root is not None)
            print(prepare_python(options.interpreter, options.python_root, options.source, index))
            return 0
        if options.mode == "stage-native":
            require(options.destination is not None)
            stage_native(options.release, options.destination, index, options.index_sha256)
        print("verified explicit web release " + index["source_commit"])
    except RELEASE_ERRORS:
        print("web release refused; preserve source, artifacts and failed stage", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
