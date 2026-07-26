"""The per-repository ingestion sequence of plan §13.2.

This module holds the steps between "the bytes are in the cache" and "the
revision is published": proving what landed is what was promised, hashing it,
and describing it. The Hub is reached only through `hfcache.hub`, and the
archive only through `hfcache.publication` and `hfcache.storage`, so the
sequence itself stays testable without either.

The rule that shapes the whole module: **upstream metadata is a claim, and local
bytes are the evidence.** The Hub's tree listing says what a revision should
contain and how large each file should be, and that is what makes it useful for
deciding whether a download is complete. It never becomes what the archive
records as true — a manifest's sizes and digests come from reading the bytes
that actually landed (`AD-18`). The two are compared here precisely so that a
disagreement stops the revision rather than being published as fact.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Self, final

from hfcache.errors import Problem, SynchronizationError
from hfcache.hashing import sha256_file
from hfcache.identity import CommitSha, PublicationId
from hfcache.paths import find_path_collisions, parse_repository_relative
from hfcache.publication import source_problems

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path

    from hfcache.hub import TreeEntry
    from hfcache.identity import RepositoryIdentity
    from hfcache.manifests import RevisionManifest

__all__ = [
    "HashedFile",
    "HashedSnapshot",
    "KnownDigest",
    "ObjectIdentity",
    "completeness_problems",
    "hash_snapshot",
    "published_digests",
    "snapshot_paths",
]


def snapshot_paths(snapshot: Path) -> tuple[str, ...]:
    """Every regular-file path a snapshot directory holds, repository-relative.

    Directories are walked and never reported: what a repository contains is
    files, and the containers are reconstructed by the path grammar.

    `follow_symlinks=False` is load-bearing. The Hub cache reaches every blob
    through a symlink, so a link is an entry in the snapshot whatever it points
    at — including nowhere. Following it would classify a dangling link as
    absent and a link to a directory as a container, and in both cases the entry
    would vanish from this listing while still sitting in the tree that
    publication is about to walk. What each link resolves to is
    `source_problems`' question, asked once, in one place.
    """
    return tuple(
        sorted(
            path.relative_to(snapshot).as_posix()
            for path in snapshot.rglob("*")
            if not path.is_dir(follow_symlinks=False)
        )
    )


def completeness_problems(
    snapshot: Path,
    tree: Sequence[TreeEntry],
    *,
    identity: RepositoryIdentity,
    cache_root: Path,
) -> list[Problem]:
    """Prove the downloaded snapshot is exactly the revision (plan §13.2 steps 6-8).

    Four questions, three codes, and every one of them answered for the whole
    snapshot before returning — an operator fixing an incomplete download should
    see every missing file at once, not the first one.

    * **Is anything missing or extra?** `HFSYN002`. Missing means the download
      did not deliver what the Hub listed. Extra is reported just as firmly:
      the archive publishes the exact path set upstream declared, and a file
      nobody listed is either a stale artifact of an earlier revision or
      something this application does not understand. Publishing it would put
      content in an immutable revision that its own manifest cannot explain.

    * **Does every size agree?** `HFSYN003`. The Hub's size is a claim, so a
      mismatch does not say which side is wrong — it says they disagree, which
      is enough to stop a publication. `HUB-007` hashes the bytes afterwards and
      the manifest records what was read (`AD-18`); this check exists so a
      truncated file is caught before anything expensive happens to it.

    * **Is every source safe to publish from?** `HFSYN004`, delegated to
      `source_problems`, which is the same proof publication itself performs
      (`FS-15`). Running it here means a snapshot containing a symlink out of
      the cache root fails the completeness step rather than surviving to the
      staging loop.

    * **Would two paths collide on disk?** `HFSYN002`. A case or
      Unicode-normalization collision publishes a tree in which two manifest
      entries resolve to one file, which is silent corruption of the thing being
      archived (`docs/security.md` T-02, decision 15).

    The path *grammar* is checked here too, so a name that could escape is
    refused before it is joined onto anything.
    """
    where = identity.selector
    expected = {entry.path: entry.size for entry in tree}
    problems = [
        *_grammar_problems(expected, where=where),
        *_path_set_problems(expected, snapshot_paths(snapshot), where=where),
    ]
    problems.extend(_collision_problems(expected, where=where))
    problems.extend(_content_problems(snapshot, expected, where=where, cache_root=cache_root))
    return problems


def _grammar_problems(expected: dict[str, int], *, where: str) -> list[Problem]:
    """Refuse an upstream name this application will not join onto a path."""
    problems: list[Problem] = []
    for path in sorted(expected):
        try:
            parse_repository_relative(path, code="HFSYN004")
        except ValueError as exc:
            problems.append(Problem(code="HFSYN004", message=str(exc), repository=where))
    return problems


def _path_set_problems(
    expected: dict[str, int], landed: Sequence[str], *, where: str
) -> list[Problem]:
    """Compare what the Hub listed with what the download produced."""
    problems: list[Problem] = []
    present = set(landed)
    for path in sorted(set(expected) - present):
        message = (
            f"{path} is listed in the Hub tree for {where} but is not in the downloaded "
            f"snapshot; a revision is archived complete or not at all"
        )
        problems.append(Problem(code="HFSYN002", message=message, location=path, repository=where))
    for path in sorted(present - set(expected)):
        message = (
            f"{path} is in the downloaded snapshot for {where} but is not listed in the Hub "
            f"tree; the archive publishes the exact path set upstream declared, and content "
            f"the manifest cannot explain is never published"
        )
        problems.append(Problem(code="HFSYN002", message=message, location=path, repository=where))
    return problems


def _collision_problems(expected: dict[str, int], *, where: str) -> list[Problem]:
    """Refuse two upstream names that would resolve to one published file."""
    problems: list[Problem] = []
    for key, spellings in find_path_collisions(expected):
        message = (
            f"{where} lists {', '.join(spellings)}, which fold to the same on-disk name "
            f"({key}); a consumer copying the tree onto a case-insensitive or normalizing "
            f"filesystem would silently merge them (`docs/security.md` T-02)"
        )
        problems.append(
            Problem(code="HFSYN002", message=message, location=spellings[0], repository=where)
        )
    return problems


def _content_problems(
    snapshot: Path, expected: dict[str, int], *, where: str, cache_root: Path
) -> list[Problem]:
    """Prove each landed file is safe to read and the size the Hub claimed."""
    problems: list[Problem] = []
    for path in sorted(expected):
        source = snapshot / path
        if not source.exists(follow_symlinks=False):
            # Already reported as missing; saying so twice would make one
            # incomplete download look like two problems.
            #
            # Not `exists()`: that follows the link, so a *dangling* symlink
            # would be skipped here as though it were absent, while
            # `snapshot_paths` counted it as present — and the file would pass
            # completeness with nothing behind it.
            continue
        unsafe = source_problems(source, cache_root=cache_root)
        if unsafe:
            problems.extend(
                Problem(
                    code=problem.code,
                    message=problem.message,
                    location=path,
                    repository=where,
                )
                for problem in unsafe
            )
            continue
        landed = source.resolve().stat().st_size
        if landed != expected[path]:
            message = (
                f"{path} landed at {landed} bytes but the Hub tree for {where} lists "
                f"{expected[path]}; the two disagree, which is enough to stop a publication "
                f"without deciding which is wrong"
            )
            problems.append(
                Problem(code="HFSYN003", message=message, location=path, repository=where)
            )
    return problems


# --------------------------------------------------------------------------- #
# Hashing new content (plan §13.2 step 9, §16.1)
# --------------------------------------------------------------------------- #


@final
@dataclass(frozen=True, slots=True)
class ObjectIdentity:
    """Which physical object a path leads to, on this filesystem, right now.

    `(device, inode)` and nothing else. Plan §16.1 is explicit that a cache path,
    a prior-run inode number, an mtime, a Git SHA-1, or an opaque Xet identifier
    is *insufficient* to prove two files are the same bytes, and the reason is
    that every one of them can be equal for objects that differ. An inode pair
    read from the filesystem during this run is the one identity the kernel is
    answering for at the moment it is asked.
    """

    device: int
    inode: int

    @classmethod
    def of(cls, path: Path) -> Self:
        """Read one object's identity, following the cache's symlink to it."""
        info = path.resolve().stat()
        return cls(device=info.st_dev, inode=info.st_ino)


@final
@dataclass(frozen=True, slots=True)
class KnownDigest:
    """A digest this archive already computed, and the publication it belongs to."""

    commit_sha: CommitSha
    publication_id: PublicationId
    sha256: str
    size: int


@final
@dataclass(frozen=True, slots=True)
class HashedFile:
    """One repository path, with the digest that will go into its manifest.

    `reused_from` is the retained publication whose inode this object shares.
    `None` means the bytes were read during this run, which is the case the
    manifest records as `hashed = true`.
    """

    path: str
    sha256: str
    size: int
    reused_from: KnownDigest | None = None


@final
@dataclass(frozen=True, slots=True)
class HashedSnapshot:
    """What ingestion verification read, ready for a manifest.

    `files` has one entry per repository path; `hashed_objects` and
    `hashed_bytes` count *physical objects*, so two paths hardlinked to one blob
    contribute one object and one file's worth of bytes while still producing two
    manifest entries. That distinction is what `docs/schemas.md` §3.4 means by
    hashed objects, and it is also why a large repository of deduplicated
    content is cheap to re-ingest.
    """

    files: tuple[HashedFile, ...]
    hashed_bytes: int
    hashed_objects: int

    @property
    def reused_digests(self) -> int:
        """Entries whose digest came from a retained publication, not a read."""
        return sum(1 for entry in self.files if entry.reused_from is not None)

    @property
    def total_bytes(self) -> int:
        """Logical size of the revision: every path, whether or not shared."""
        return sum(entry.size for entry in self.files)


def published_digests(tree: Path, manifest: RevisionManifest) -> dict[ObjectIdentity, KnownDigest]:
    """Index one retained publication's objects by the inode they occupy now.

    This is what makes plan §16.1's reuse rule checkable rather than aspirational.
    The manifest supplies the digest — a value this archive computed and has
    since verified — and the filesystem supplies the identity, read at the moment
    the index is built. Neither alone would do: a manifest cannot say which inode
    its bytes live on today, and an inode cannot say what it hashes to.

    A path the manifest lists but the tree no longer holds is skipped rather than
    reported. A missing published file is real corruption, but it is `verify`'s
    finding to make and act on (`AD-13`); all it means here is that there is no
    proven inode to reuse a digest from, so the object gets hashed.
    """
    index: dict[ObjectIdentity, KnownDigest] = {}
    for entry in manifest.files:
        source = tree / entry.path
        try:
            identity = ObjectIdentity.of(source)
        except OSError:
            continue
        index[identity] = KnownDigest(
            commit_sha=CommitSha(manifest.commit_sha),
            publication_id=PublicationId(manifest.publication_id),
            sha256=entry.sha256,
            size=entry.size,
        )
    return index


def hash_snapshot(
    snapshot: Path,
    tree: Sequence[TreeEntry],
    *,
    identity: RepositoryIdentity,
    known: Mapping[ObjectIdentity, KnownDigest] | None = None,
) -> HashedSnapshot:
    """Read every newly introduced unique object once (plan §13.2 step 9).

    Two kinds of reuse, and the difference between them is the whole of §16.1.

    *Within this run*, two repository paths that resolve to one inode are hashed
    once. Both manifest entries still record `hashed = true`, because the bytes
    genuinely were read during this run — what was avoided is a second read of
    the same object, not a second verification.

    *Across runs*, a digest from a retained publication is reused only when the
    object is proven to be the same inode **and** the same size. Both conditions,
    because an inode number is reused by the filesystem after deletion and a size
    that no longer matches is the cheapest possible evidence that it has been.
    Such an entry records `hashed = false` and names the publication it came
    from, so a manifest never contains a digest whose origin cannot be traced
    back to bytes this archive read.

    Everything else is hashed. An upstream digest is never a substitute
    (`AD-18`), and no path is exempt for being large.
    """
    known = known or {}
    hashed: dict[ObjectIdentity, str] = {}
    files: list[HashedFile] = []
    hashed_bytes = 0

    for entry in sorted(tree, key=lambda item: item.path):
        source = snapshot / entry.path
        try:
            object_identity = ObjectIdentity.of(source)
            size = source.resolve().stat().st_size
        except OSError as exc:
            message = (
                f"{entry.path} could not be examined before hashing ({exc.strerror}); the "
                f"completeness check passed, so the object was there and is not now"
            )
            raise SynchronizationError.single(
                message, code="HFSYN009", location=entry.path, repository=identity.selector
            ) from exc

        if (digest := hashed.get(object_identity)) is not None:
            files.append(HashedFile(path=entry.path, sha256=digest, size=size))
            continue

        candidate = known.get(object_identity)
        if candidate is not None and candidate.size == size:
            files.append(
                HashedFile(
                    path=entry.path,
                    sha256=candidate.sha256,
                    size=size,
                    reused_from=candidate,
                )
            )
            continue

        read = sha256_file(source, error=SynchronizationError, code="HFSYN009")
        hashed[object_identity] = read.digest
        hashed_bytes += read.size
        files.append(HashedFile(path=entry.path, sha256=read.digest, size=read.size))

    return HashedSnapshot(files=tuple(files), hashed_bytes=hashed_bytes, hashed_objects=len(hashed))
