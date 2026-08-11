"""Reading bytes and saying what they are.

`AD-18`: every newly introduced unique physical object is read and SHA-256 hashed
locally before publication. Identifiers supplied by the Hub are never trusted as
digests — an ETag, a Xet hash, or a filename that looks like a digest says
something about a transfer, not about the bytes that ended up on this dataset.

Size is returned alongside the digest because both come from the same read.
Hashing a file and then `stat`ing it would leave a window in which the two
describe different content, and every caller needs both.
"""

import hashlib
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final, Self, final

from hfcache.errors import HfcacheError, IntegrityError

if TYPE_CHECKING:
    from pathlib import Path

__all__ = [
    "CHUNK_BYTES",
    "DIGEST_ALGORITHM",
    "FileDigest",
    "IdentifiedDigest",
    "ObjectIdentity",
    "sha256_file",
    "sha256_identified_file",
]

DIGEST_ALGORITHM: Final = "sha256"
"""The only algorithm schema version 1 permits (`docs/configuration.md` §5)."""

CHUNK_BYTES: Final = 1 << 20
"""How much is read at a time.

A megabyte is large enough that a multi-gigabyte model is not dominated by
syscall overhead, and small enough that memory is bounded regardless of the file
— which matters because the largest objects here are exactly the ones that would
not fit.
"""


@final
@dataclass(frozen=True, slots=True)
class FileDigest:
    """What one object is: its SHA-256 and its size, from a single read."""

    digest: str
    size: int


@final
@dataclass(frozen=True, slots=True)
class ObjectIdentity:
    """The physical object and size a filesystem path names right now.

    This is transient, same-operation evidence rather than durable provenance.
    It lets hardlink publication prove that a destination is the exact object
    whose bytes were already hashed, without reading that inode a second time.
    """

    device: int
    inode: int
    size: int

    @classmethod
    def of(cls, path: Path) -> Self:
        """Read identity while following a Hub-cache symlink to its blob."""
        info = path.resolve(strict=True).stat()
        return cls(device=info.st_dev, inode=info.st_ino, size=info.st_size)


@final
@dataclass(frozen=True, slots=True)
class IdentifiedDigest:
    """A digest and the identity of the open object whose bytes produced it."""

    digest: str
    size: int
    identity: ObjectIdentity

    @property
    def file_digest(self) -> FileDigest:
        """The durable content evidence, without transient inode information."""
        return FileDigest(digest=self.digest, size=self.size)


def sha256_file(
    path: Path,
    *,
    error: type[HfcacheError] = IntegrityError,
    code: str = "HFVER006",
) -> FileDigest:
    """Hash one file, streaming it.

    `code` is the caller's because an unreadable object means different things at
    different times: `HFVER006` when `verify` is reading the archive, and a
    synchronization code when a run is ingesting. It defaults to the verification
    reading, which is the common one.

    `error` travels with it, following decision 19. The exit an error carries
    comes from its *class*, while the classification `docs/cli.md` §5 publishes
    comes from the code's *family*, so a call that paired `IntegrityError` with
    an `HFSYN` code would exit `40` for a condition the taxonomy calls `30` —
    telling an operator the archive is corrupt when a download failed. Passing
    both keeps the two from disagreeing, and `tests/unit/test_hashing.py` asserts
    that they agree for every call site.
    """
    identified = sha256_identified_file(path, error=error, code=code)
    return identified.file_digest


def sha256_identified_file(
    path: Path,
    *,
    error: type[HfcacheError] = IntegrityError,
    code: str = "HFVER006",
) -> IdentifiedDigest:
    """Hash one opened object and return its same-descriptor identity.

    Both identity observations use ``fstat`` on the descriptor being read. A
    snapshot symlink replacement therefore cannot pair one object's digest with
    another object's inode evidence.
    """
    digest = hashlib.sha256()
    size = 0
    try:
        with path.open("rb") as handle:
            before = os.fstat(handle.fileno())
            while chunk := handle.read(CHUNK_BYTES):
                digest.update(chunk)
                size += len(chunk)
            after = os.fstat(handle.fileno())
    except OSError as exc:
        message = f"{path} could not be read for hashing: {exc.strerror}"
        raise error.single(message, code=code, location=str(path)) from exc
    before_identity = ObjectIdentity(
        device=before.st_dev,
        inode=before.st_ino,
        size=before.st_size,
    )
    after_identity = ObjectIdentity(
        device=after.st_dev,
        inode=after.st_ino,
        size=after.st_size,
    )
    if before_identity != after_identity or size != before_identity.size:
        message = (
            f"{path} changed identity or size while it was being hashed; "
            "the read is not valid content evidence"
        )
        raise error.single(message, code=code, location=str(path))
    return IdentifiedDigest(
        digest=digest.hexdigest(),
        size=size,
        identity=before_identity,
    )
