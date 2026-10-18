#!/usr/bin/env python3
"""Build decision 127's local image from an exact wheel and the locked closure.

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
import zipfile
from email.parser import BytesParser
from pathlib import Path
from typing import NoReturn

REPOSITORY = Path(__file__).resolve().parents[1]
PYTHON_BASE = (
    "docker.io/library/python@sha256:"
    "b921fe7e7522f828d45197a47656ec465a9b15689b27fa8e1fba2864fca5b967"
)
UV_BUILDER = (
    "ghcr.io/astral-sh/uv@sha256:0d127b3a7049b879a6e18a79c7f33fea59aa83c226464248f89cfb716a6b96f5"
)
_HEX = re.compile(r"[0-9a-f]{64}\Z")
_IMAGE = re.compile(r"localhost/hfcache:[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}\Z")
_MOUNT_MIN_FIELDS = 5
_METADATA_LIMIT = 65536
_LOCAL_FILESYSTEMS = frozenset({"btrfs", "ext2", "ext3", "ext4", "overlay", "tmpfs", "xfs"})


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


def build(wheel: Path, expected: str, context: Path, image: str) -> dict[str, object]:
    if os.geteuid() == 0:
        refuse("build as the rootless login/service account, never root")
    if not _IMAGE.fullmatch(image):
        refuse("image tag must be local localhost/hfcache:<tag>")
    wheel_body, version = wheel_input(wheel, expected)
    context = local_path(context)
    # Never merge into or delete an unexplained prior build directory.
    context.mkdir(mode=0o700)
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
    containerfile = REPOSITORY / "packaging/containers/Containerfile"
    shutil.copyfile(containerfile, context / "Containerfile")
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
        "containerfile_sha256": digest(containerfile.read_bytes()),
        "python_base": PYTHON_BASE,
        "uv_builder": UV_BUILDER,
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
    parser.add_argument("--context", type=Path, required=True, help="new local directory; retained")
    parser.add_argument("--tag", required=True, help="localhost/hfcache:<tag>")
    options = parser.parse_args()
    try:
        evidence = build(options.wheel, options.wheel_sha256, options.context, options.tag)
    except OSError, ValueError, zipfile.BadZipFile, subprocess.CalledProcessError:
        print("container build refused or failed; retained context contains available evidence")
        return 1
    print(json.dumps(evidence, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
