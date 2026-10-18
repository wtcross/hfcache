"""Bounded, descriptor-anchored metadata reads (FS-09/FS-15, API-006).

Readers never create files, follow symlinks, or open artifact content for stat.
A budget refusal is visible; callers must never turn it into an empty page.
"""

import os
import stat
from dataclasses import dataclass
from typing import TYPE_CHECKING

from hfcache.errors import IntegrityError, SafetyError
from hfcache.models import VersionedModel, load
from hfcache.storage import CapacityFacts

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path


@dataclass(frozen=True, slots=True)
class QueryBounds:
    """Optional per-query work ceilings; CLI callers retain complete results."""

    maximum_entries: int | None = None
    maximum_artifact_bytes: int | None = None
    maximum_total_bytes: int | None = None

    def __post_init__(self) -> None:
        for value in (self.maximum_entries, self.maximum_artifact_bytes, self.maximum_total_bytes):
            if value is not None and (type(value) is not int or value < 1):
                message = "metadata query bounds must be positive integers"
                raise ValueError(message)


class QueryLimitError(SafetyError):
    """A query cannot complete inside its configured work budget (HTTP 503)."""


@dataclass(frozen=True, slots=True)
class MetadataEntry:
    path: Path
    info: os.stat_result


UNBOUNDED = QueryBounds()


class MetadataReader:
    """One query's anchored filesystem capability and shared work accounting."""

    def __init__(self, root: Path, bounds: QueryBounds = UNBOUNDED) -> None:
        self.root = root
        self.bounds = bounds
        self._entries = 0
        self._bytes = 0

    def _limit(self) -> None:
        msg = "metadata query budget exceeded"
        raise QueryLimitError.single(msg, code="HFAPI005")

    def _consume(self, count: int = 1) -> None:
        self._entries += count
        if self.bounds.maximum_entries is not None and self._entries > self.bounds.maximum_entries:
            self._limit()

    def open(self, path: Path, *, directory: bool = False, metadata_only: bool = False) -> int:
        """Return a pinned fd, refusing symlinks in every absolute component."""
        descriptor = None
        try:
            path.relative_to(self.root)
            if not path.is_absolute() or ".." in path.parts:
                message = "metadata path is not contained by its archive"
                raise ValueError(message)
            descriptor = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
            for index, part in enumerate(path.parts[1:]):
                is_directory = directory or index < len(path.parts) - 2
                flags = os.O_NOFOLLOW
                flags |= (
                    os.O_RDONLY | os.O_DIRECTORY
                    if is_directory
                    else (os.O_PATH if metadata_only else os.O_RDONLY | os.O_NONBLOCK)
                )
                following = os.open(part, flags, dir_fd=descriptor)
                os.close(descriptor)
                descriptor = following
            mode = os.fstat(descriptor).st_mode
            if (directory and not stat.S_ISDIR(mode)) or (not directory and not stat.S_ISREG(mode)):
                message = "metadata path has an unexpected file type"
                raise ValueError(message)
            result = descriptor
            descriptor = None
            return result
        finally:
            if descriptor is not None:
                os.close(descriptor)

    def entries(self, path: Path, *, missing_ok: bool = True) -> tuple[MetadataEntry, ...]:
        """List a pinned directory without following any entry's symlink."""
        try:
            descriptor = self.open(path, directory=True)
        except FileNotFoundError:
            if missing_ok:
                return ()
            raise
        try:
            found = []
            with os.scandir(descriptor) as iterator:
                for item in iterator:
                    self._consume()
                    try:
                        info = item.stat(follow_symlinks=False)
                    except FileNotFoundError:  # publication/retention may remove an entry
                        continue
                    found.append(MetadataEntry(path / item.name, info))
            return tuple(sorted(found, key=lambda item: item.path.name))
        finally:
            os.close(descriptor)

    def walk(self, path: Path) -> Iterator[MetadataEntry]:
        """Walk metadata with no symlink recursion and one shared traversal budget."""
        pending = [path]
        while pending:
            directory = pending.pop()
            for entry in self.entries(directory):
                yield entry
                if stat.S_ISDIR(entry.info.st_mode):
                    pending.append(entry.path)

    def read(self, path: Path) -> bytes:
        """Read at most the artifact and remaining total budget, including growth."""
        descriptor = self.open(path)
        try:
            self._consume()
            caps = [value for value in (self.bounds.maximum_artifact_bytes,) if value is not None]
            if self.bounds.maximum_total_bytes is not None:
                caps.append(self.bounds.maximum_total_bytes - self._bytes)
            cap = min(caps) if caps else None
            if cap is not None and os.fstat(descriptor).st_size > cap:
                self._limit()
            with os.fdopen(descriptor, "rb", closefd=False) as stream:
                raw = stream.read() if cap is None else stream.read(cap + 1)
            if cap is not None and len(raw) > cap:
                self._limit()
            self._bytes += len(raw)
            return raw
        finally:
            os.close(descriptor)

    def model[ModelT: VersionedModel](self, path: Path, model: type[ModelT]) -> ModelT:
        try:
            raw = self.read(path)
        except (OSError, ValueError) as exc:
            msg = "metadata artifact is absent, unsafe, or unreadable"
            raise IntegrityError.single(msg, code="HFVER007") from exc
        return load(model, raw, error=IntegrityError, code="HFVER007")

    def stat(self, path: Path) -> os.stat_result:
        """Stat a pinned regular file without reading file content."""
        self._consume()
        descriptor = self.open(path, metadata_only=True)
        try:
            return os.fstat(descriptor)
        finally:
            os.close(descriptor)

    def capacity(self) -> CapacityFacts:
        descriptor = self.open(self.root, directory=True)
        try:
            info = os.fstatvfs(descriptor)
            return CapacityFacts(
                path=self.root,
                total_bytes=info.f_blocks * info.f_frsize,
                available_bytes=info.f_bavail * info.f_frsize,
            )
        finally:
            os.close(descriptor)
