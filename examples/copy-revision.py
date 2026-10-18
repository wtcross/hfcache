#!/usr/bin/env python3
"""Copy the current revision of one archived repository, and verify it locally.

This is the reference implementation of the publication identity and copying
contract in `docs/consumers.md`. It runs on a *downstream* host that mounts only the
archive's `published/` directory, read-only, and it deliberately depends on
**nothing but the Python standard library** — a consumer should not have to install
this project, or any project, to take a copy.

Each copy attempt:

1. Read `refs/current.json` **once**. The ref is not re-read during the copy: it
   can change under a running consumer, and a copy that followed it would mix two
   revisions.
2. Resolve the `tree` and `manifest` it names, and prove both stay under the
   mount before opening either.
3. Copy the immutable tree to a temporary directory beside the destination.
4. Verify every file against the manifest — the complete path set, each size, and
   each SHA-256, streamed in bounded chunks.
5. Rename the temporary directory into place, so a partial copy is never mistaken
   for a finished one.

Failure is retryable by design. A repair can retire the instance the ref named
while this is running; the retired tree stays readable for a grace period, but if
this consumer is slow enough, or the grace has expired, the tree can disappear
underneath it. The consumer contract's answer is to discard the partial copy, re-read
`current.json`, and restart from whatever it now names — which is what
`--attempts` does.

Usage:

    ./copy-revision.py --mount /mnt/hfcache \\
        --type model --repository hf-internal-testing/tiny-random-gpt2 \\
        --destination ./tiny-random-gpt2

    ./copy-revision.py --mount /mnt/hfcache --type dataset \\
        --repository hf-internal-testing/fixtures_ade20k \\
        --destination ./ade20k --json

Exit codes are this script's own and are not the application's CLI exit codes:

    0  the copy is complete and every file matched the manifest
    1  the copy failed after exhausting --attempts
    2  the invocation or the archive layout is wrong, and retrying will not help
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

CHUNK = 1024 * 1024
"""Read size for hashing. Model files do not fit in memory and are not loaded."""

TYPES = {"model": "models", "dataset": "datasets"}
"""The configuration/API singular to the on-disk plural (`docs/architecture.md` §5.3)."""

SHA256_HEX = 64
"""Length of a hex-encoded SHA-256, which is what `docs/schemas.md` §3.2 records."""

REPOSITORY_SEGMENTS = 2
"""`<org>/<repo>`. A single-segment identifier is refused (`docs/architecture.md` §5.3)."""

PREVIEW = 5
"""How many verification problems to name before summarising the rest."""


class RetryableError(Exception):
    """The archive moved under us. Re-read the reference and start again."""


class FatalError(Exception):
    """The invocation or the layout is wrong. Retrying would fail the same way."""


# --------------------------------------------------------------------------- #
# Path safety
# --------------------------------------------------------------------------- #


def under(root: Path, relative: str, *, what: str) -> Path:
    """Join an archive-supplied relative path onto the mount, and prove it stayed.

    Every path this script joins comes out of a JSON file on a mount it does not
    control, so each is treated as hostile input (`docs/security.md` T-02). The
    check is done on the *resolved* path, so a symlink inside the archive cannot
    walk out of the mount either.
    """
    if not relative or relative.startswith("/"):
        message = f"{what} is empty or absolute: {relative!r}"
        raise FatalError(message)
    candidate = PurePosixPath(relative)
    if any(part in ("", ".", "..") for part in candidate.parts):
        message = f"{what} has a traversing or empty component: {relative!r}"
        raise FatalError(message)

    resolved_root = root.resolve()
    resolved = (resolved_root / candidate).resolve()
    if resolved != resolved_root and resolved_root not in resolved.parents:
        message = f"{what} resolves outside the mount: {relative!r} -> {resolved}"
        raise FatalError(message)
    return resolved


def read_json(path: Path, *, what: str) -> dict[str, Any]:
    """Read one JSON object, turning a vanished file into a retry rather than a crash."""
    try:
        payload = json.loads(path.read_bytes())
    except FileNotFoundError as error:
        message = f"{what} is gone: {path}"
        raise RetryableError(message) from error
    except OSError as error:
        message = f"{what} could not be read: {path}: {error}"
        raise RetryableError(message) from error
    except json.JSONDecodeError as error:
        message = f"{what} is not valid JSON: {path}: {error}"
        raise FatalError(message) from error
    if not isinstance(payload, dict):
        message = f"{what} is not a JSON object: {path}"
        raise FatalError(message)
    return payload


# --------------------------------------------------------------------------- #
# Resolution
# --------------------------------------------------------------------------- #


def reference_path(mount: Path, repository_type: str, repository_id: str) -> Path:
    """`repos/<type>/<org>/<repo>/refs/current.json`, relative to the mount.

    The mount *is* `published/`, so this is the one file the consumer contract says a consumer
    must read to find out what to take.
    """
    directory = TYPES.get(repository_type)
    if directory is None:
        message = f"--type must be one of {', '.join(sorted(TYPES))}, not {repository_type!r}"
        raise FatalError(message)
    segments = repository_id.split("/")
    if len(segments) != REPOSITORY_SEGMENTS or not all(segments):
        message = f"--repository must be <org>/<name>, not {repository_id!r}"
        raise FatalError(message)
    relative = f"repos/{directory}/{segments[0]}/{segments[1]}/refs/current.json"
    return under(mount, relative, what="the reference path")


def resolve(mount: Path, repository_type: str, repository_id: str) -> dict[str, Any]:
    """Read `current.json` once and resolve what it names.

    `tree` and `manifest` in a reference are relative to **`published/`**, which
    is this mount — not to the archive root. The manifest's *own* `tree` field is
    archive-relative and is deliberately not used here; a consumer cannot see the
    archive root (`docs/schemas.md` §3.1, §4.1).
    """
    path = reference_path(mount, repository_type, repository_id)
    if not path.is_file():
        message = (
            f"no current reference at {path}; the repository is not published "
            f"under this mount, or the mount is not the archive's published/ directory"
        )
        raise FatalError(message)
    reference = read_json(path, what="the reference")
    for field in ("commit_sha", "publication_id", "tree", "manifest"):
        if not isinstance(reference.get(field), str) or not reference[field]:
            message = f"the reference at {path} has no usable {field!r}"
            raise FatalError(message)
    return {
        "reference": reference,
        "tree": under(mount, reference["tree"], what="the reference's tree"),
        "manifest": under(mount, reference["manifest"], what="the reference's manifest"),
    }


def manifest_files(manifest: dict[str, Any], path: Path) -> list[dict[str, Any]]:
    """The `files[]` array, validated enough to be trusted as a work list."""
    files = manifest.get("files")
    if not isinstance(files, list):
        message = f"the manifest at {path} has no files array"
        raise FatalError(message)
    for entry in files:
        if not isinstance(entry, dict):
            message = f"the manifest at {path} has a files entry that is not an object"
            raise FatalError(message)
        if not isinstance(entry.get("path"), str) or not entry["path"]:
            message = f"the manifest at {path} has a file entry with no path"
            raise FatalError(message)
        if not isinstance(entry.get("size"), int) or entry["size"] < 0:
            message = f"the manifest at {path} has a bad size for {entry['path']!r}"
            raise FatalError(message)
        if not isinstance(entry.get("sha256"), str) or len(entry["sha256"]) != SHA256_HEX:
            message = f"the manifest at {path} has a bad sha256 for {entry['path']!r}"
            raise FatalError(message)
    return files


# --------------------------------------------------------------------------- #
# Copy and verify
# --------------------------------------------------------------------------- #


def digest(path: Path) -> str:
    """SHA-256 of one file, streamed. Nothing here loads a model into memory."""
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(CHUNK):
            hasher.update(chunk)
    return hasher.hexdigest()


def copy_tree(source: Path, destination: Path) -> None:
    """Copy the immutable tree, treating its disappearance as retryable.

    `symlinks=False` is deliberate: a published tree is ordinary files and
    directories by construction (`AD-11`), so a symlink here is not something to
    faithfully reproduce.
    """
    try:
        shutil.copytree(source, destination, symlinks=False)
    except FileNotFoundError as error:
        message = f"the published tree went away while it was being copied: {source}"
        raise RetryableError(message) from error
    except OSError as error:
        message = f"the published tree could not be copied: {source}: {error}"
        raise RetryableError(message) from error


def verify(root: Path, files: list[dict[str, Any]]) -> list[str]:
    """Check the copy against the manifest. Returns one line per problem.

    Three failures are distinguished because they mean different things: a file
    the manifest lists and the copy does not have, a file the copy has and the
    manifest does not list, and a file whose bytes are not what was published.
    """
    problems: list[str] = []
    expected: set[str] = set()

    for entry in files:
        relative = entry["path"]
        try:
            path = under(root, relative, what=f"manifest entry {relative!r}")
        except FatalError as error:
            problems.append(str(error))
            continue
        expected.add(str(PurePosixPath(relative)))
        if not path.is_file():
            problems.append(f"missing: {relative}")
            continue
        size = path.stat().st_size
        if size != entry["size"]:
            problems.append(f"size: {relative} is {size}, manifest says {entry['size']}")
            continue
        found = digest(path)
        if found != entry["sha256"]:
            problems.append(f"digest: {relative} is {found}, manifest says {entry['sha256']}")

    for path in sorted(root.rglob("*")):
        if path.is_file():
            relative = str(PurePosixPath(path.relative_to(root)))
            if relative not in expected:
                problems.append(f"extra: {relative}")

    return problems


def attempt(
    mount: Path, repository_type: str, repository_id: str, destination: Path
) -> dict[str, Any]:
    """One whole copy-and-verify, from reading the reference to the final rename."""
    resolved = resolve(mount, repository_type, repository_id)
    reference = resolved["reference"]
    manifest_path = resolved["manifest"]
    manifest = read_json(manifest_path, what="the manifest")
    files = manifest_files(manifest, manifest_path)

    if manifest.get("commit_sha") != reference["commit_sha"] or manifest.get(
        "publication_id"
    ) != reference.get("publication_id"):
        message = (
            f"the manifest at {manifest_path} describes a different instance than the "
            f"reference names; the archive is inconsistent and this is not a retry"
        )
        raise FatalError(message)

    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{destination.name}.", dir=str(destination.parent)))
    working = staging / "tree"
    try:
        copy_tree(resolved["tree"], working)
        problems = verify(working, files)
        if problems:
            # A verification failure against a *complete* manifest is retryable
            # because the instance may disappear during a copy: the likeliest cause is that a repair
            # replaced the instance mid-copy, so the bytes here are a mix. The
            # next attempt re-reads the reference and takes the new instance.
            listed = "; ".join(problems[:PREVIEW])
            more = f" (and {len(problems) - PREVIEW} more)" if len(problems) > PREVIEW else ""
            message = f"the copy does not match the manifest: {listed}{more}"
            raise RetryableError(message)
        if destination.exists():
            shutil.rmtree(destination)
        working.rename(destination)
    finally:
        shutil.rmtree(staging, ignore_errors=True)

    return {
        "commit_sha": reference["commit_sha"],
        "destination": str(destination),
        "file_count": len(files),
        "publication_generation": reference.get("publication_generation"),
        "publication_id": reference["publication_id"],
        "repository_id": repository_id,
        "repository_type": repository_type,
        "total_bytes": sum(entry["size"] for entry in files),
        "verified": True,
    }


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Copy and verify the current revision of an archived repository.",
    )
    parser.add_argument(
        "--mount",
        required=True,
        type=Path,
        help="the archive's published/ directory, as mounted on this host",
    )
    parser.add_argument("--type", required=True, help="model or dataset")
    parser.add_argument("--repository", required=True, help="<org>/<name>")
    parser.add_argument(
        "--destination",
        required=True,
        type=Path,
        help="new revision directory; an existing destination is removed after verification",
    )
    parser.add_argument(
        "--attempts",
        type=int,
        default=3,
        help="how many times to restart from a re-read reference; default 3",
    )
    parser.add_argument("--json", action="store_true", help="emit one JSON object on stdout")
    arguments = parser.parse_args(argv)

    if arguments.attempts < 1:
        print("--attempts must be at least 1", file=sys.stderr)
        return 2
    if not arguments.mount.is_dir():
        print(f"--mount is not a directory: {arguments.mount}", file=sys.stderr)
        return 2

    last = ""
    for number in range(1, arguments.attempts + 1):
        try:
            result = attempt(
                arguments.mount, arguments.type, arguments.repository, arguments.destination
            )
        except FatalError as error:
            print(f"error: {error}", file=sys.stderr)
            return 2
        except RetryableError as error:
            last = str(error)
            print(f"attempt {number}/{arguments.attempts} failed: {error}", file=sys.stderr)
            continue
        result["attempts"] = number
        if arguments.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print(
                f"copied {result['repository_type']} {result['repository_id']} "
                f"@ {result['commit_sha']}\n"
                f"  instance    {result['publication_id']} "
                f"(generation {result['publication_generation']})\n"
                f"  files       {result['file_count']}, {result['total_bytes']} bytes\n"
                f"  verified    every path, size, and SHA-256 against the manifest\n"
                f"  destination {result['destination']}"
            )
        return 0

    print(f"error: giving up after {arguments.attempts} attempts: {last}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
