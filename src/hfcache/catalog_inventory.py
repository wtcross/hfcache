"""Bounded canonical reference inventory for offline discovery work (FS-08/11, INV-018)."""

import re
import stat
from typing import TYPE_CHECKING, Literal

from hfcache.catalog_storage import read_authority
from hfcache.errors import IntegrityError
from hfcache.identity import CommitSha, PublicationId, RepositoryIdentity
from hfcache.models import Reference

if TYPE_CHECKING:
    from pathlib import Path

    from hfcache.metadata import MetadataReader
    from hfcache.paths import ArchiveLayout


def _invalid() -> IntegrityError:
    return IntegrityError.single(
        "Catalog reference inventory is unsafe or inconsistent", code="HFVER008"
    )


class CatalogInventory:
    """One shared no-follow metadata reader, with no payload, credentials or writer methods."""

    def __init__(self, layout: ArchiveLayout, reader: MetadataReader) -> None:
        self.layout, self.reader = layout, reader

    def _reference(self, identity: RepositoryIdentity, path: Path) -> Reference:
        try:
            reference, _ = read_authority(path, Reference, self.reader)
            repository = self.layout.repository(identity)
            sha, publication = (
                CommitSha(reference.commit_sha),
                PublicationId(reference.publication_id),
            )
            if (
                reference.identity != identity
                or reference.tree != str(repository.tree_reference(sha, publication))
                or reference.manifest != str(repository.manifest_reference(sha, publication))
                or (path != repository.current_ref and path != repository.revision_ref(sha))
            ):
                raise _invalid()
        except (OSError, ValueError) as exc:
            raise _invalid() from exc
        return reference

    def retained(self, identity: RepositoryIdentity) -> tuple[Reference, ...]:
        """Only per-SHA refs confer retention; unknown/future/corrupt selected evidence refuses."""
        found = []
        try:
            for entry in self.reader.entries(self.layout.repository(identity).refs / "revisions"):
                if re.fullmatch(r"[0-9a-f]{40}\.json\.tmp-[0-9a-f]{16}", entry.path.name):
                    continue
                if not re.fullmatch(r"[0-9a-f]{40}\.json", entry.path.name) or not stat.S_ISREG(
                    entry.info.st_mode
                ):
                    raise _invalid()
                found.append(self._reference(identity, entry.path))
        except (OSError, ValueError) as exc:
            raise _invalid() from exc
        return tuple(sorted(found, key=lambda ref: (ref.publication_generation, ref.commit_sha)))

    def current(self, identity: RepositoryIdentity) -> Reference | None:
        """Explicit current and per-SHA identities must agree; no highest-generation fallback."""
        repository = self.layout.repository(identity)
        try:
            self.reader.stat(repository.current_ref)
        except FileNotFoundError:
            return None
        except (OSError, ValueError) as exc:
            raise _invalid() from exc
        current = self._reference(identity, repository.current_ref)
        retained = self._reference(identity, repository.revision_ref(CommitSha(current.commit_sha)))
        if current.model_dump(exclude={"updated_at"}) != retained.model_dump(
            exclude={"updated_at"}
        ):
            raise _invalid()
        return current

    def publications(
        self, identity: RepositoryIdentity, revision_scope: Literal["current", "retained"]
    ) -> tuple[Reference, ...]:
        if revision_scope == "retained":
            return self.retained(identity)
        current = self.current(identity)
        return (current,) if current is not None else ()

    def archived(self) -> dict[RepositoryIdentity, tuple[Reference, ...]]:
        """A directory, orphan tree or metadata record alone never adds an archived repository."""
        found = {}
        try:
            for kind, directory in (("model", "models"), ("dataset", "datasets")):
                for namespace in self.reader.entries(self.layout.repos / directory):
                    if not stat.S_ISDIR(namespace.info.st_mode):
                        raise _invalid()
                    for name in self.reader.entries(namespace.path):
                        if not stat.S_ISDIR(name.info.st_mode):
                            raise _invalid()
                        identity = RepositoryIdentity.of(
                            kind, f"{namespace.path.name}/{name.path.name}"
                        )
                        if references := self.retained(identity):
                            found[identity] = references
        except (OSError, ValueError) as exc:
            raise _invalid() from exc
        return found
