#!/usr/bin/env python3
"""Build the UBI micro image from authenticated local inputs.

Run as a login/service user, never root. Inputs and output must be on local
storage. Base images must already exist locally; this script never pulls/pushes.
The new context and all failed-build evidence are retained for review.
"""

import argparse
import hashlib
import io
import json
import os
import re
import shutil
import stat
import subprocess
import tarfile
import zipfile
from email.parser import BytesParser
from pathlib import Path, PurePosixPath
from typing import NoReturn

REPOSITORY = Path(__file__).resolve().parents[1]
PINS = json.loads((REPOSITORY / "packaging/containers/images.json").read_bytes())
PYTHON_BASE = PINS["python"]
BUILD_BASE = PINS["build"]
UV_BUILDER = PINS["uv_binary_image"]  # Binary donor only; every FROM is UBI micro.
CA_IMAGE = PINS["ca_bundle_image"]
CA_SHA256 = PINS["ca_bundle_sha256"]
PYTHON_DISTRIBUTION = PINS["python_distribution"]
_HEX = re.compile(r"[0-9a-f]{64}\Z")
_IMAGE = re.compile(r"localhost/hfcache:[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}\Z")
_MOUNT_MIN_FIELDS = 5
_METADATA_LIMIT = 65536
_LOCAL_FILESYSTEMS = frozenset({"btrfs", "ext2", "ext3", "ext4", "overlay", "tmpfs", "xfs"})
_MAX_PYTHON_ARCHIVE = 128 * 1024 * 1024
_MAX_PYTHON_EXPANDED = 512 * 1024 * 1024
_MAX_PYTHON_MEMBERS = 16384


def refuse(message: str) -> NoReturn:
    raise ValueError(message)


def executable(name: str) -> str:
    if (path := shutil.which(name)) is None:
        refuse("required local build tool is unavailable")
    return path


def digest(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def local_path(path: Path, *, mountinfo: str | None = None) -> Path:
    """Reject NAS/aliases before opening input or creating output (decision 126)."""
    path = Path(os.path.abspath(path))  # noqa: PTH100 - lexical normalization must not follow NAS aliases
    if path == Path("/srv") or Path("/srv") in path.parents:
        refuse("container build/probe paths must use local storage")
    table = Path("/proc/self/mountinfo").read_text() if mountinfo is None else mountinfo
    matches = []
    for line in table.splitlines():
        before, _, after = line.partition(" - ")
        fields = before.split()
        if len(fields) < _MOUNT_MIN_FIELDS or not after:
            continue
        where = Path(re.sub(r"\\([0-7]{3})", lambda m: chr(int(m[1], 8)), fields[4]))
        if path == where or where in path.parents:
            matches.append((len(where.parts), after.split()[0]))
    if not matches or max(matches)[1] not in _LOCAL_FILESYSTEMS:
        refuse("container build/probe paths must use a proven local filesystem")
    current = Path("/")
    for part in path.parts[1:]:
        current /= part
        try:
            info = current.lstat()
        except FileNotFoundError:
            break
        if stat.S_ISLNK(info.st_mode):
            refuse("container build/probe paths must not traverse symlinks")
    return path


def wheel_input(path: Path, expected: str) -> tuple[bytes, str]:
    """Prove the supplied artifact before invoking an installer or image builder."""
    if not _HEX.fullmatch(expected):
        refuse("wheel SHA256 must be explicit lowercase hexadecimal")
    path = local_path(path)
    info = path.stat()
    if not stat.S_ISREG(info.st_mode) or info.st_size > 16 * 1024 * 1024:
        refuse("wheel is not a bounded regular file")
    body = path.read_bytes()
    if digest(body) != expected:
        refuse("wheel SHA256 does not match")
    with zipfile.ZipFile(io.BytesIO(body)) as wheel:
        metadata = [
            entry for entry in wheel.infolist() if entry.filename.endswith(".dist-info/METADATA")
        ]
        if len(metadata) != 1 or metadata[0].file_size > _METADATA_LIMIT:
            refuse("wheel metadata is invalid")
        parsed = BytesParser().parsebytes(wheel.read(metadata[0]))
    version = parsed.get("Version", "")
    if (
        parsed.get("Name") != "hfcache"
        or not re.fullmatch(r"[0-9]+(?:\.[0-9]+){2}(?:[a-z0-9.]+)?", version)
        or path.name != f"hfcache-{version}-py3-none-any.whl"
    ):
        refuse("input must be the exact hfcache universal release wheel")
    return body, version


def python_archive_input(path: Path) -> bytes:
    """Authenticate the complete interpreter before parsing or extracting it."""
    path = local_path(path)
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    try:
        before = os.fstat(descriptor)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_nlink != 1
            or not 0 < before.st_size <= _MAX_PYTHON_ARCHIVE
        ):
            refuse("Python input must be a bounded regular archive")
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            body = stream.read(_MAX_PYTHON_ARCHIVE + 1)
        after = os.fstat(descriptor)
        if len(body) != before.st_size or any(
            getattr(before, field) != getattr(after, field)
            for field in (
                "st_dev",
                "st_ino",
                "st_mode",
                "st_nlink",
                "st_size",
                "st_mtime_ns",
                "st_ctime_ns",
            )
        ):
            refuse("Python input changed during authentication")
        if digest(body) != PYTHON_DISTRIBUTION["sha256"]:
            refuse("Python archive SHA256 does not match the pinned distribution")
        return body
    finally:
        os.close(descriptor)


def extract_python(body: bytes, context: Path) -> None:
    """Bound a fresh Python-only tree; never extract devices, hardlinks or escapes."""
    destination = context / "python"
    destination.mkdir(mode=0o755)
    members: list[tarfile.TarInfo] = []
    seen: set[str] = set()
    expanded = 0
    with tarfile.open(fileobj=io.BytesIO(body), mode="r:gz") as archive:
        for item in archive:
            name = PurePosixPath(item.name)
            if (
                not name.parts
                or name.is_absolute()
                or name.parts[0] != "python"
                or ".." in name.parts
                or "\\" in item.name
                or any(not character.isprintable() for character in item.name)
                or not (item.isfile() or item.isdir() or item.issym())
                or item.sparse is not None
                or item.size < 0
            ):
                refuse("unsafe Python archive member")
            relative = PurePosixPath(*name.parts[1:]).as_posix()
            expanded += item.size
            if (
                relative in seen
                or len(members) >= _MAX_PYTHON_MEMBERS
                or expanded > _MAX_PYTHON_EXPANDED
            ):
                refuse("Python archive exceeds its tree bounds")
            seen.add(relative)
            if relative == "." and not item.isdir():
                refuse("Python archive root must be a directory")
            members.append(item.replace(name=relative))
        # The data filter resolves symlinks against the Python-only destination,
        # not the larger context, so no link can gain authority over other inputs.
        archive.extractall(destination, members=members, filter="data")
    executable_path = destination / "bin/python3.14"
    info = executable_path.lstat()
    if not stat.S_ISREG(info.st_mode) or not info.st_mode & stat.S_IXUSR:
        refuse("Python archive lacks the expected executable")


def hashed_requirements(body: bytes) -> bytes:
    """Accept only the public pinned/hash-bearing closure, never editable paths."""
    if not body or len(body) > 8 * 1024 * 1024:
        refuse("locked dependency export is empty or oversized")
    text = body.decode("utf-8")
    logical = text.replace("\\\n", " ")
    dependencies = 0
    for raw_line in logical.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if (
            not re.match(r"[A-Za-z0-9][A-Za-z0-9_.-]*(?:\[[A-Za-z0-9_,.-]+\])?==", line)
            or "--hash=sha256:" not in line
            or " @ " in line
        ):
            refuse("locked export must contain only pinned hashed dependencies")
        dependencies += 1
    if not dependencies:
        refuse("locked dependency export contains no dependencies")
    return body.rstrip() + b"\n"


def validate_containerfile(body: bytes) -> None:
    """Pins describe actual UBI stages and binary/CA-only external copies."""
    text = body.decode("utf-8")
    stages = re.findall(r"^FROM (\S+)(?: AS \w+)?$", text, re.MULTILINE)
    donors = re.findall(r"^COPY --from=(\S+) ", text, re.MULTILINE)
    if stages != [BUILD_BASE, PYTHON_BASE] or donors != [UV_BUILDER, CA_IMAGE, *["build"] * 4]:
        refuse("Containerfile differs from its pinned UBI stages or donors")
    if (
        f"COPY --from={UV_BUILDER} /uv /usr/local/bin/uv" not in text
        or f"COPY --from={CA_IMAGE} "
        "/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem /etc/ssl/cert.pem"
        not in text
        or CA_SHA256 not in text
    ):
        refuse("Containerfile differs from its pinned binary or CA inputs")


def build(
    wheel: Path, expected: str, context: Path, image: str, *, python_archive: Path
) -> dict[str, object]:
    if os.geteuid() == 0:
        refuse("build as the rootless login/service account, never root")
    if not _IMAGE.fullmatch(image):
        refuse("image tag must be local localhost/hfcache:<tag>")
    wheel_body, version = wheel_input(wheel, expected)
    interpreter = python_archive_input(python_archive)
    context = local_path(context)
    containerfile = local_path(REPOSITORY / "packaging/containers/Containerfile")
    recipe = containerfile.read_bytes()
    validate_containerfile(recipe)
    # Never merge into or delete an unexplained prior build directory.
    context.mkdir(mode=0o700)
    extract_python(interpreter, context)
    closure = hashed_requirements(
        subprocess.run(  # noqa: S603 - fixed argv, validated local paths and no shell
            [
                executable("uv"),
                "export",
                "--locked",
                "--no-dev",
                "--extra",
                "server",
                "--extra",
                "mcp",
                "--no-emit-project",
                "--format",
                "requirements-txt",
            ],
            cwd=REPOSITORY,
            check=True,
            stdout=subprocess.PIPE,
        ).stdout
    )
    (context / "wheels").mkdir(mode=0o700)
    (context / "wheels" / wheel.name).write_bytes(wheel_body)
    requirements = closure + f"/build/wheels/{wheel.name} --hash=sha256:{expected}\n".encode()
    (context / "requirements.txt").write_bytes(requirements)
    (context / "Containerfile").write_bytes(recipe)
    commit = subprocess.run(  # noqa: S603 - fixed argv, validated local paths and no shell
        [executable("git"), "rev-parse", "HEAD"],
        cwd=REPOSITORY,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    dirty = bool(
        subprocess.run(  # noqa: S603 - fixed argv, validated local paths and no shell
            [executable("git"), "status", "--porcelain"],
            cwd=REPOSITORY,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    )
    evidence: dict[str, object] = {
        "schema_version": 1,
        "source_commit": commit,
        "source_dirty": dirty,
        "version": version,
        "wheel": wheel.name,
        "wheel_sha256": expected,
        "uv_lock_sha256": digest((REPOSITORY / "uv.lock").read_bytes()),
        "dependency_closure_sha256": digest(closure),
        "requirements_sha256": digest(requirements),
        "containerfile_sha256": digest(recipe),
        "python_base": PYTHON_BASE,
        "build_base": BUILD_BASE,
        "uv_binary_image": UV_BUILDER,
        "ca_bundle_image": CA_IMAGE,
        "ca_bundle_sha256": CA_SHA256,
        "python_distribution": PYTHON_DISTRIBUTION,
        "platform": PINS["platform"],
        "image_tag": image,
    }
    (context / "inputs.json").write_text(json.dumps(evidence, sort_keys=True, indent=2) + "\n")
    subprocess.run(  # noqa: S603 - fixed argv, validated local paths and no shell
        [
            executable("podman"),
            "--remote=false",
            "build",
            "--pull=never",
            "--http-proxy=false",
            "--platform=linux/amd64",
            "--tag",
            image,
            "--iidfile",
            str(context / "image.id"),
            str(context),
        ],
        check=True,
    )
    identity = (context / "image.id").read_text().strip()
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", identity):
        refuse("builder did not return an exact image identity")
    evidence["image_id"] = identity
    (context / "build.json").write_text(json.dumps(evidence, sort_keys=True, indent=2) + "\n")
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel", type=Path, required=True)
    parser.add_argument("--wheel-sha256", required=True)
    parser.add_argument("--python-archive", type=Path, required=True)
    parser.add_argument("--context", type=Path, required=True, help="new local directory; retained")
    parser.add_argument("--tag", required=True, help="localhost/hfcache:<tag>")
    options = parser.parse_args()
    try:
        evidence = build(
            options.wheel,
            options.wheel_sha256,
            options.context,
            options.tag,
            python_archive=options.python_archive,
        )
    except OSError, ValueError, tarfile.TarError, zipfile.BadZipFile, subprocess.CalledProcessError:
        print("container build refused or failed; retained context contains available evidence")
        return 1
    print(json.dumps(evidence, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
