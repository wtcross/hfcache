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
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final, final

from hfcache.errors import IntegrityError

if TYPE_CHECKING:
    from pathlib import Path

__all__ = ["CHUNK_BYTES", "DIGEST_ALGORITHM", "FileDigest", "sha256_file"]

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


def sha256_file(path: Path, *, code: str = "HFVER006") -> FileDigest:
    """Hash one file, streaming it.

    `code` is the caller's because an unreadable object means different things
    at different times: `HFVER006` when `verify` is reading the archive, and a
    synchronization code when a run is ingesting. It defaults to the verification
    reading, which is the common one.
    """
    digest = hashlib.sha256()
    size = 0
    try:
        with path.open("rb") as handle:
            while chunk := handle.read(CHUNK_BYTES):
                digest.update(chunk)
                size += len(chunk)
    except OSError as exc:
        message = f"{path} could not be read for hashing: {exc.strerror}"
        raise IntegrityError.single(message, code=code, location=str(path)) from exc
    return FileDigest(digest=digest.hexdigest(), size=size)
