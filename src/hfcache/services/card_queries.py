"""ADR142 exact retained card reads: metadata only, no current/payload fallback."""

import os
from typing import TYPE_CHECKING

from hfcache.card_models import RepositoryCardRead
from hfcache.catalog_extractors import ExtractionBudget
from hfcache.catalog_storage import read_authority, read_repository_card
from hfcache.errors import IntegrityError, RequestError
from hfcache.identity import PublicationId
from hfcache.manifests import RevisionManifest
from hfcache.metadata import MetadataReader, QueryBounds
from hfcache.models import ArchiveSentinel, Reference
from hfcache.paths import ArchiveLayout

if TYPE_CHECKING:
    from hfcache.config import ApplicationConfig
    from hfcache.services.queries import PublicationQuery


def _missing() -> RequestError:
    return RequestError(code="HFAPI007", status_code=404, message="Retained publication absent")


def _archive(layout: ArchiveLayout, archive_id: str, reader: MetadataReader) -> str:
    sentinel, digest = read_authority(layout.sentinel, ArchiveSentinel, reader)
    if sentinel.archive_id != archive_id:
        msg = "Card archive identity disagrees with the installed archive policy"
        raise IntegrityError.single(msg, code="HFVER007")
    return digest


def _retained(
    layout: ArchiveLayout, request: PublicationQuery, reader: MetadataReader
) -> tuple[RevisionManifest, str, str, tuple[int, int]]:
    """Authorize the per-SHA reference, not a leftover repair predecessor manifest."""
    repository = layout.repository(request.identity)
    try:
        reference, ref_digest = read_authority(
            repository.revision_ref(request.commit_sha), Reference, reader, missing_ok=True
        )
        if reference.identity != request.identity or reference.commit_sha != request.commit_sha:
            msg = "Retained reference identity disagrees with the requested repository"
            raise IntegrityError.single(msg, code="HFVER008")
        selected = PublicationId(reference.publication_id)
        if reference.tree != str(
            repository.tree_reference(request.commit_sha, selected)
        ) or reference.manifest != str(repository.manifest_reference(request.commit_sha, selected)):
            msg = "Retained reference has incompatible publication locators"
            raise IntegrityError.single(msg, code="HFVER008")
        if selected != request.publication_id:
            raise _missing()
        manifest, manifest_digest = read_authority(
            repository.manifest(request.commit_sha, selected),
            RevisionManifest,
            reader,
            missing_ok=True,
        )
        if (
            manifest.identity != request.identity
            or manifest.commit_sha != request.commit_sha
            or manifest.publication_id != selected
            or manifest.publication_generation != reference.publication_generation
            or manifest.tree != str(repository.manifest_tree_field(request.commit_sha, selected))
        ):
            msg = "Retained manifest identity disagrees with its reference"
            raise IntegrityError.single(msg, code="HFVER007")
        descriptor = reader.open(
            repository.instance(request.commit_sha, selected), directory=True, metadata_only=True
        )
        try:
            info = os.fstat(descriptor)
            tree_identity = info.st_dev, info.st_ino
        finally:
            os.close(descriptor)
    except FileNotFoundError as exc:
        raise _missing() from exc
    except (OSError, ValueError) as exc:
        msg = "Retained publication metadata is unsafe or unreadable"
        raise IntegrityError.single(msg, code="HFVER007") from exc
    return manifest, manifest_digest, ref_digest, tree_identity


def read_card(
    config: ApplicationConfig, request: PublicationQuery, *, bounds: QueryBounds
) -> RepositoryCardRead:
    """Read only a card plus authoritative metadata, rejoining membership before return."""
    layout = ArchiveLayout(config.storage.archive_root)
    reader = MetadataReader(layout.root, bounds)
    archive_before = _archive(layout, config.storage.archive_id, reader)
    before = _retained(layout, request, reader)
    try:
        record = read_repository_card(
            layout,
            request.identity,
            request.commit_sha,
            request.publication_id,
            config.storage.archive_id,
            reader=reader,
            card_budget=ExtractionBudget(),
        )
    except IntegrityError:
        # A valid repair/prune occurring during the adjunct read is absence,
        # while unchanged authority leaves an actual corrupt adjunct classified.
        _archive(layout, config.storage.archive_id, reader)
        _retained(layout, request, reader)
        raise
    archive_after = _archive(layout, config.storage.archive_id, reader)
    after = _retained(layout, request, reader)
    if archive_before != archive_after or before[1:] != after[1:]:
        msg = "Retained publication changed while reading its card"
        raise IntegrityError.single(msg, code="HFVER007")
    if record is not None:
        return RepositoryCardRead.model_validate(record.to_payload())
    manifest, manifest_digest, _, _ = before
    source = next((entry for entry in manifest.files if entry.path == "README.md"), None)
    return RepositoryCardRead(
        schema_version=1,
        kind="repository_card",
        archive_id=config.storage.archive_id,
        repository_type=request.identity.type,
        repository_id=request.identity.id,
        commit_sha=request.commit_sha,
        publication_id=request.publication_id,
        publication_generation=manifest.publication_generation,
        manifest_path=str(
            layout.archive_relative(
                layout.repository(request.identity).manifest(
                    request.commit_sha, request.publication_id
                )
            )
        ),
        manifest_digest=manifest_digest,
        source_path="README.md" if source is not None else None,
        expected_source_sha256=source.sha256 if source is not None else None,
        captured_at=None,
        presentation_version=None,
        state="not_captured",
        markdown=None,
        presentation_sha256=None,
        diagnostics=(),
    )
