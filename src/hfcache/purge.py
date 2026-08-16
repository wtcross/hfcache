"""Explicit, transactional removal of repositories no longer configured.

`AD-20` is deliberately narrower than ordinary retention.  A purge target must
already be absent from configuration, the operator must select it explicitly or
use ``--all-unmanaged``, and the published repository must have exactly the
layout its retained references and manifests explain.  Anything unexpected is
`HFRET001` and is preserved (`FS-19`).

The transaction reuses ``operation = "prune"`` and its commit point so recovery
keeps the same rule: before ``prune_logically_committed`` everything is restored;
after it, consumer-visible removal stands and only audit/physical cleanup is
finished.  All references move first as one directory rename, then all revision
trees, then all manifests.  No reference can name a tree that has moved (`FS-10`).
"""

import errno
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Final, final

from hfcache.errors import Problem, RetentionError
from hfcache.hub import delete_cache_revisions
from hfcache.identity import (
    CommitSha,
    PublicationId,
    RepositoryIdentity,
    RunId,
    TransactionId,
    new_publication_id,
    new_transaction_id,
)
from hfcache.manifests import RevisionManifest
from hfcache.models import PrunedRevisionRecord, PruneSelection, PurgePlan, RevisionSummary
from hfcache.paths import RepositoryLayout
from hfcache.publication import (
    PUBLISHED_DIRECTORY_MODE,
    publish_catalog,
    read_reference,
    rebuild_catalog,
)
from hfcache.retention import AUDIT_FILE_MODE, AUDIT_MODE, ordered_revisions, selection_of
from hfcache.storage import atomic_write_bytes, fsync_directory, read_model, write_model
from hfcache.transactions import open_transaction

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path
    from typing import Any

    from hfcache.paths import ArchiveLayout

__all__ = [
    "apply_purge",
    "complete_purge",
    "plan_all_purges",
    "plan_purge",
    "rollback_purge",
]


TRASH_MODE: Final = 0o700
_NOT_EMPTY: Final = frozenset({errno.ENOTEMPTY, errno.EEXIST})


@final
@dataclass(frozen=True, slots=True)
class PurgeTrash:
    """Transaction-owned tombstones for one complete repository."""

    directory: Path
    refs: Path
    revisions: Path
    manifests: Path


def _trash(layout: ArchiveLayout, transaction_id: TransactionId) -> PurgeTrash:
    directory = layout.trash_for(transaction_id).directory
    return PurgeTrash(
        directory=directory,
        refs=directory / "refs",
        revisions=directory / "revisions",
        manifests=directory / "manifests",
    )


def _layout_problem(
    layout: ArchiveLayout,
    identity: RepositoryIdentity,
    path: Path,
    detail: str,
) -> Problem:
    return Problem(
        code="HFRET001",
        message=f"repository purge refused: {detail}; unexpected content is preserved (`FS-19`)",
        location=str(layout.archive_relative(path)),
        repository=identity.selector,
    )


def _exact_entries(
    layout: ArchiveLayout,
    identity: RepositoryIdentity,
    directory: Path,
    *,
    files: Sequence[str] = (),
    directories: Sequence[str] = (),
) -> list[Problem]:
    """Prove one shallow application-owned directory has exactly known entries."""
    if directory.is_symlink() or not directory.is_dir():
        return [_layout_problem(layout, identity, directory, "expected a real directory")]
    try:
        entries = {entry.name: entry for entry in directory.iterdir()}
    except OSError as exc:
        return [
            _layout_problem(
                layout, identity, directory, f"directory could not be read: {exc.strerror}"
            )
        ]
    expected = set(files) | set(directories)
    problems = [
        _layout_problem(layout, identity, entries[name], f"unrecognized entry {name!r}")
        for name in sorted(entries.keys() - expected)
    ]
    problems.extend(
        _layout_problem(layout, identity, directory / name, "expected entry missing")
        for name in sorted(expected - entries.keys())
    )
    for name in files:
        entry = entries.get(name)
        if entry is not None and (entry.is_symlink() or not entry.is_file()):
            problems.append(_layout_problem(layout, identity, entry, "expected a regular file"))
    for name in directories:
        entry = entries.get(name)
        if entry is not None and (entry.is_symlink() or not entry.is_dir()):
            problems.append(_layout_problem(layout, identity, entry, "expected a real directory"))
    return problems


def _layout_problems(
    layout: ArchiveLayout,
    identity: RepositoryIdentity,
    selections: Sequence[PruneSelection],
) -> list[Problem]:
    """Refuse any repository shape the purge plan does not explain (`FS-19`)."""
    repository = RepositoryLayout(archive=layout, identity=identity)
    commits = [selection.commit_sha for selection in selections]
    problems = [
        *_exact_entries(
            layout,
            identity,
            repository.directory,
            directories=("refs", "revisions"),
        ),
        *_exact_entries(
            layout,
            identity,
            repository.refs,
            files=("current.json",),
            directories=("revisions",),
        ),
        *_exact_entries(
            layout,
            identity,
            repository.refs / "revisions",
            files=tuple(f"{commit}.json" for commit in commits),
        ),
        *_exact_entries(
            layout,
            identity,
            repository.revisions,
            directories=tuple(commits),
        ),
        *_exact_entries(
            layout,
            identity,
            repository.manifests,
            directories=tuple(commits),
        ),
    ]
    for selection in selections:
        problems.extend(
            _exact_entries(
                layout,
                identity,
                repository.revision(CommitSha(selection.commit_sha)),
                directories=(selection.publication_id,),
            )
        )
        problems.extend(
            _exact_entries(
                layout,
                identity,
                repository.revision_manifests(CommitSha(selection.commit_sha)),
                files=(f"{selection.publication_id}.json",),
            )
        )
    return problems


def plan_purge(
    layout: ArchiveLayout,
    identity: RepositoryIdentity,
    *,
    generated_at: datetime,
) -> PurgePlan | None:
    """Build the exact complete-repository removal plan, without mutation."""
    retained = ordered_revisions(layout, identity)
    if not retained:
        return None
    repository = RepositoryLayout(archive=layout, identity=identity)
    current = read_reference(layout, repository.current_ref)
    selections = tuple(
        selection_of(
            revision,
            tree=str(
                layout.archive_relative(
                    repository.instance(
                        CommitSha(revision.commit_sha),
                        PublicationId(revision.reference.publication_id),
                    )
                )
            ),
            manifest=str(
                layout.archive_relative(
                    repository.manifest(
                        CommitSha(revision.commit_sha),
                        PublicationId(revision.reference.publication_id),
                    )
                )
            ),
        )
        for revision in retained
    )
    if problems := _layout_problems(layout, identity, selections):
        raise RetentionError(problems)
    matching_current = [
        revision
        for revision in retained
        if revision.commit_sha == current.commit_sha
        and revision.reference.publication_id == current.publication_id
        and revision.publication_generation == current.publication_generation
    ]
    if len(matching_current) != 1:
        message = "current reference does not exactly match one retained revision"
        raise RetentionError([_layout_problem(layout, identity, repository.current_ref, message)])
    return PurgePlan(
        cache_revisions_to_delete=tuple(revision.commit_sha for revision in retained),
        current=RevisionSummary(
            commit_sha=current.commit_sha,
            publication_generation=current.publication_generation,
        ),
        generated_at=generated_at,
        plan_id=new_publication_id(),
        reason="operator_requested_repository_purge",
        repository_id=identity.id,
        repository_type=identity.type,
        revisions=selections,
        unique_bytes_released_estimate=sum(selection.logical_bytes for selection in selections),
    )


def plan_all_purges(
    layout: ArchiveLayout,
    identities: Sequence[RepositoryIdentity],
    *,
    generated_at: datetime,
) -> tuple[PurgePlan, ...]:
    """Plans for selected unmanaged repositories, in repository order."""
    plans = [
        plan
        for identity in sorted(identities, key=lambda item: item.sort_key)
        if (plan := plan_purge(layout, identity, generated_at=generated_at)) is not None
    ]
    return tuple(plans)


def _audit_purge(
    layout: ArchiveLayout,
    plan: PurgePlan,
    transaction_id: TransactionId,
    *,
    now: datetime,
) -> tuple[PrunedRevisionRecord, ...]:
    """Preserve every original manifest and write one reason record per revision."""
    identity = RepositoryIdentity.of(plan.repository_type, plan.repository_id)
    repository = RepositoryLayout(archive=layout, identity=identity)
    trash = _trash(layout, transaction_id)
    records = []
    for selection in plan.revisions:
        commit = CommitSha(selection.commit_sha)
        publication = PublicationId(selection.publication_id)
        source = trash.manifests / selection.commit_sha / f"{selection.publication_id}.json"
        archived = repository.pruned_manifest(commit, publication)
        audit = repository.pruned_records(commit)
        audit.mkdir(mode=AUDIT_MODE, parents=True, exist_ok=True)
        if archived.is_file():
            if source.is_file() and archived.read_bytes() != source.read_bytes():
                message = (
                    f"purge audit manifest disagrees with tombstone for {selection.commit_sha}"
                )
                raise RetentionError.single(
                    message, code="HFRET010", location=str(layout.archive_relative(archived))
                )
        elif source.is_file():
            atomic_write_bytes(archived, source.read_bytes(), mode=AUDIT_FILE_MODE)
        else:
            message = f"purged manifest evidence is missing for {selection.commit_sha}"
            raise RetentionError.single(
                message, code="HFRET010", location=str(layout.archive_relative(audit))
            )
        # Parsing proves an existing archived copy is still the complete durable
        # artifact this transaction planned, rather than trusting its filename.
        manifest = read_model(archived, RevisionManifest, error=RetentionError, code="HFRET010")
        if (
            manifest.repository_type != plan.repository_type
            or manifest.repository_id != plan.repository_id
            or manifest.commit_sha != selection.commit_sha
            or manifest.publication_id != selection.publication_id
            or manifest.publication_generation != selection.publication_generation
            or manifest.tree != selection.tree
            or manifest.file_count != selection.file_count
            or manifest.total_bytes != selection.logical_bytes
        ):
            message = f"purge audit manifest disagrees with its plan for {selection.commit_sha}"
            raise RetentionError.single(
                message, code="HFRET010", location=str(layout.archive_relative(archived))
            )
        record = PrunedRevisionRecord(
            commit_sha=selection.commit_sha,
            file_count=selection.file_count,
            logical_bytes=selection.logical_bytes,
            manifest_archived_at=now,
            plan_id=plan.plan_id,
            publication_generation=selection.publication_generation,
            publication_id=selection.publication_id,
            pruned_at=now,
            reason=plan.reason,
            repository_id=plan.repository_id,
            repository_type=plan.repository_type,
            retained_after=(),
            transaction_id=transaction_id,
            tree=selection.tree,
        )
        record_path = repository.prune_record(commit, publication)
        if record_path.is_file():
            existing = read_model(
                record_path,
                PrunedRevisionRecord,
                error=RetentionError,
                code="HFRET010",
            )
            comparable = {
                "commit_sha",
                "file_count",
                "logical_bytes",
                "plan_id",
                "publication_generation",
                "publication_id",
                "reason",
                "repository_id",
                "repository_type",
                "retained_after",
                "transaction_id",
                "tree",
            }
            if any(getattr(existing, field) != getattr(record, field) for field in comparable):
                message = f"purge audit record disagrees with its plan for {selection.commit_sha}"
                raise RetentionError.single(
                    message,
                    code="HFRET010",
                    location=str(layout.archive_relative(record_path)),
                )
        else:
            write_model(
                record_path,
                record,
                mode=AUDIT_FILE_MODE,
                code="HFRET010",
                error=RetentionError,
            )
        fsync_directory(audit)
        records.append(record)
    return tuple(records)


def _remove_empty_namespace_containers(
    layout: ArchiveLayout, repository: RepositoryLayout
) -> dict[str, list[str]]:
    """Remove only now-empty namespace containers; unknown content keeps them."""
    removed: list[str] = []
    retained: list[str] = []
    for container in (repository.directory.parent, repository.manifests.parent):
        relative = str(layout.archive_relative(container))
        try:
            container.rmdir()
        except FileNotFoundError:
            removed.append(relative)
        except OSError as exc:
            if exc.errno not in _NOT_EMPTY:
                raise
            retained.append(relative)
        else:
            fsync_directory(container.parent)
            removed.append(relative)
    return {"removed": sorted(removed), "retained": sorted(retained)}


def apply_purge(
    layout: ArchiveLayout,
    plan: PurgePlan,
    *,
    envelope: Mapping[str, Any],
    now: datetime | None = None,
) -> tuple[PrunedRevisionRecord, ...]:
    """Execute one validated repository purge through the prune commit point."""
    stamp = now or datetime.now(UTC)
    identity = RepositoryIdentity.of(plan.repository_type, plan.repository_id)
    repository = RepositoryLayout(archive=layout, identity=identity)
    transaction_id = new_transaction_id()
    transaction = open_transaction(
        layout,
        transaction_id=transaction_id,
        operation="prune",
        run_id=RunId(str(envelope["run_id"])),
        archive_id=str(envelope["archive_id"]),
        config_fingerprint=str(envelope["config_fingerprint"]),
        repository_id=plan.repository_id,
        repository_type=plan.repository_type,
        commit_sha=plan.current.commit_sha,
    )
    transaction.checkpoint("plan_persisted", plan=plan.model_dump(mode="json"))

    freed = delete_cache_revisions(
        layout.hub_cache,
        tuple(CommitSha(commit_sha) for commit_sha in plan.cache_revisions_to_delete),
    )
    transaction.checkpoint(
        "cache_revision_deleted",
        commit_shas=list(plan.cache_revisions_to_delete),
        expected_freed_bytes=freed,
    )

    trash = _trash(layout, transaction_id)
    trash.directory.mkdir(mode=TRASH_MODE, parents=True)
    repository.refs.rename(trash.refs)
    fsync_directory(trash.directory)
    transaction.checkpoint(
        "revision_ref_removed",
        references_absent=str(layout.archive_relative(repository.refs)),
    )

    repository.revisions.rename(trash.revisions)
    fsync_directory(trash.directory)
    transaction.checkpoint(
        "tree_tombstoned",
        tombstoned_tree=str(layout.archive_relative(trash.revisions)),
        file_count=sum(revision.file_count for revision in plan.revisions),
    )

    repository.manifests.rename(trash.manifests)
    fsync_directory(trash.directory)
    transaction.checkpoint(
        "manifest_tombstoned",
        tombstoned_manifest=str(layout.archive_relative(trash.manifests)),
        manifest_count=len(plan.revisions),
    )

    repository.directory.rmdir()
    fsync_directory(repository.directory.parent)
    transaction.checkpoint(
        "repository_container_removed",
        repository_absent=str(layout.archive_relative(repository.directory)),
    )

    catalog_path = publish_catalog(layout, rebuild_catalog(layout, generated_at=stamp))
    transaction.checkpoint(
        "catalog_published", catalog_path=str(layout.archive_relative(catalog_path))
    )
    transaction.checkpoint("prune_logically_committed", retained=0)

    records = _audit_purge(layout, plan, transaction_id, now=stamp)
    transaction.checkpoint(
        "audit_record_written",
        audit_paths=[
            str(layout.archive_relative(repository.pruned_records(CommitSha(revision.commit_sha))))
            for revision in plan.revisions
        ],
    )

    shutil.rmtree(trash.directory)
    fsync_directory(layout.trash)
    transaction.checkpoint(
        "trash_removed", trash_absent=str(layout.archive_relative(trash.directory))
    )

    containers = _remove_empty_namespace_containers(layout, repository)
    transaction.checkpoint(
        "containers_removed",
        containers_absent=containers["removed"],
        containers_retained=containers["retained"],
    )
    transaction.checkpoint("prune_completed", state="committed")
    transaction.commit()
    return records


def _restore_directory(source: Path, destination: Path) -> None:
    """Restore one purge tombstone, refusing an ambiguous double presence."""
    if source.exists() and destination.exists():
        message = f"both purge tombstone {source} and destination {destination} exist"
        raise RetentionError.single(message, code="HFRET005", location=str(destination))
    if not source.exists():
        return
    destination.parent.mkdir(mode=PUBLISHED_DIRECTORY_MODE, parents=True, exist_ok=True)
    source.rename(destination)
    fsync_directory(destination.parent)


def rollback_purge(
    layout: ArchiveLayout, plan: PurgePlan, transaction_id: TransactionId
) -> dict[str, Any]:
    """Restore a purge that stopped before its commit point (`TX-06`)."""
    identity = RepositoryIdentity.of(plan.repository_type, plan.repository_id)
    repository = RepositoryLayout(archive=layout, identity=identity)
    trash = _trash(layout, transaction_id)
    repository.directory.mkdir(mode=PUBLISHED_DIRECTORY_MODE, parents=True, exist_ok=True)
    # Trees and manifests return before refs, preserving `FS-10` throughout.
    _restore_directory(trash.revisions, repository.revisions)
    _restore_directory(trash.manifests, repository.manifests)
    _restore_directory(trash.refs, repository.refs)
    publish_catalog(layout, rebuild_catalog(layout, generated_at=datetime.now(UTC)))
    if trash.directory.is_dir() and not any(trash.directory.iterdir()):
        trash.directory.rmdir()
        fsync_directory(layout.trash)
    return {
        "repository": identity.selector,
        "restored_revisions": len(plan.revisions),
    }


def complete_purge(
    layout: ArchiveLayout, plan: PurgePlan, transaction_id: TransactionId
) -> dict[str, Any]:
    """Finish audit and physical cleanup after a committed purge (`TX-04`)."""
    identity = RepositoryIdentity.of(plan.repository_type, plan.repository_id)
    repository = RepositoryLayout(archive=layout, identity=identity)
    records = _audit_purge(layout, plan, transaction_id, now=datetime.now(UTC))
    trash = _trash(layout, transaction_id)
    if trash.directory.is_dir():
        shutil.rmtree(trash.directory)
        fsync_directory(layout.trash)
    _remove_empty_namespace_containers(layout, repository)
    return {"repository": identity.selector, "purged_revisions": len(records)}
