"""Which revisions the archive keeps, and which one goes when a sixth arrives.

Plan §15. The whole policy rests on one property, `AD-05`: **retention order is
the immutable per-repository `publication_generation`, and nothing else.**

Every alternative ordering key was rejected for the same kind of reason.
Wall-clock publication time reorders when a repair republishes an old SHA.
Upstream commit time reorders when a repository force-pushes or when a branch is
reset to an older commit. Directory modification time reorders when anything
touches the filesystem, including a backup. A SHA has no order at all. The
generation is assigned once, under the global lock, when a unique SHA is first
published, and is never reassigned — a repair keeps it, a re-observation keeps
it, and a prune retires it without reissuing it.

That is what makes retention explainable after the fact: an operator reading
`refs/revisions/` can say why a particular revision was the one that went,
without knowing what order things happened in or what the clock said.
"""

import hashlib
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Final, final

from hfcache.errors import IntegrityError, Problem, RetentionError
from hfcache.hub import delete_cache_revision
from hfcache.identity import (
    CommitSha,
    PublicationId,
    RepositoryIdentity,
    RunId,
    new_publication_id,
    new_transaction_id,
)
from hfcache.manifests import RevisionManifest
from hfcache.models import PrunedRevisionRecord, PrunePlan, PruneSelection, RevisionSummary
from hfcache.paths import RepositoryLayout
from hfcache.publication import (
    publish_catalog,
    read_reference,
    rebuild_catalog,
    retained_references,
)
from hfcache.storage import atomic_write_bytes, fsync_directory, read_model, write_model
from hfcache.transactions import open_transaction

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from typing import Any

    from hfcache.models import Reference
    from hfcache.paths import ArchiveLayout

__all__ = [
    "RetainedRevision",
    "apply_prune",
    "ordered_revisions",
    "over_retention",
    "plan_all",
    "plan_prune",
    "prune_candidate",
    "require_valid_selection",
    "selection_of",
    "selection_problems",
]


TRASH_MODE: Final = 0o700
"""Trash lives under `.store`, which is private to the writer (§5.2)."""

AUDIT_MODE: Final = 0o700
AUDIT_FILE_MODE: Final = 0o600
"""`audit/` outlives the data it describes and is never consumer-visible."""


def sha256_bytes(payload: bytes) -> str:
    """The digest of a small in-memory artifact.

    Distinct from `hashing.sha256_file`, which streams: a manifest is bounded and
    already in memory here because it is being moved byte for byte, and reading
    it a second time from disk to hash it would let the two disagree.
    """
    return hashlib.sha256(payload).hexdigest()


@final
@dataclass(frozen=True, slots=True)
class RetainedRevision:
    """One revision the archive holds, with everything retention needs about it.

    The reference and the manifest together, because neither alone is enough: the
    reference says which instance is active and what generation it holds, and the
    manifest says how large it is and what it contains. A prune plan needs both,
    and reading them once here keeps the ordering code from reaching into the
    filesystem while it sorts.
    """

    reference: Reference
    manifest: RevisionManifest

    @property
    def commit_sha(self) -> str:
        return self.reference.commit_sha

    @property
    def publication_generation(self) -> int:
        return self.reference.publication_generation

    @property
    def summary(self) -> RevisionSummary:
        """The `(commit_sha, generation)` pair a prune plan records."""
        return RevisionSummary(
            commit_sha=self.commit_sha, publication_generation=self.publication_generation
        )


def ordered_revisions(
    layout: ArchiveLayout, identity: RepositoryIdentity
) -> tuple[RetainedRevision, ...]:
    """Every retained revision, in retention order (`AD-05`).

    Ascending by `publication_generation`, so index 0 is the oldest and the last
    is the newest. Gaps are expected and mean nothing: a crash between assigning
    a generation and publishing it leaves the number unused, and §15.1 says that
    is acceptable — what matters is that two distinct SHAs never share one.

    Reads `refs/revisions/<sha>.json` rather than the revision directories,
    because a directory can hold a superseded repair instance inside its
    seven-day grace period (plan §16.5) and that instance is not retained — it is
    the one being replaced.
    """
    revisions = []
    for reference in retained_references(layout, identity):
        repository = RepositoryLayout(archive=layout, identity=identity)
        manifest = read_model(
            repository.manifest(
                CommitSha(reference.commit_sha), PublicationId(reference.publication_id)
            ),
            RevisionManifest,
            error=IntegrityError,
            code="HFVER007",
        )
        revisions.append(RetainedRevision(reference=reference, manifest=manifest))
    return tuple(sorted(revisions, key=lambda revision: revision.publication_generation))


def over_retention(revisions: Sequence[RetainedRevision], *, maximum: int) -> bool:
    """Whether this repository holds more revisions than policy allows.

    Counted over *unique retained SHAs*, which is what `refs/revisions/` holds
    one of each of. Publication instances are not counted: a repair leaves two
    directories for one SHA during its grace period, and that is one revision.
    """
    return len(revisions) > maximum


def prune_candidate(
    revisions: Sequence[RetainedRevision], *, current: str, maximum: int
) -> RetainedRevision | None:
    """The one revision a prune would remove, or `None` when nothing should go.

    Plan §15.2 step 3: the oldest non-current revision. Three conditions, and
    each refusal is a case where doing nothing is the correct behaviour rather
    than a limitation.

    * **Not over the limit** — including the ordinary case of exactly five. A
      prune is triggered by a *successful publication beyond* the maximum
      (`AD-04`), never by a count that happens to be high.
    * **The oldest is current** — the current revision is never pruned (§15.1).
      This is reachable: a repository whose upstream moved back to its earliest
      retained SHA has the oldest generation as its current. Over-retention is
      the right answer, and it resolves itself at the next new revision.
    * **Nothing retained** — a repository with no revisions has nothing to
      choose from, which is the state before its first sync.

    Returning `None` rather than raising is deliberate: "nothing to prune" is the
    answer for the overwhelming majority of runs, and a caller should not have to
    catch an exception to learn that retention is already satisfied.
    """
    if not over_retention(revisions, maximum=maximum):
        return None
    oldest = revisions[0]
    if oldest.commit_sha == current:
        return None
    return oldest


def selection_problems(
    candidate: RetainedRevision, revisions: Sequence[RetainedRevision], *, current: str
) -> list[Problem]:
    """Refuse a selection that retention policy does not permit (`HFRET001`).

    `PrunePlan` enforces the same rules when one is constructed, which is not
    duplication: the model refuses a plan that was *recorded* wrong, and this
    refuses a selection before a plan is built, so a caller assembling one gets
    a coded problem naming the policy rather than a validation error naming a
    field. Both are cheap and the cost of being wrong here is deleting the wrong
    revision.
    """
    problems: list[Problem] = []
    where = f"{candidate.reference.repository_type}:{candidate.reference.repository_id}"
    if candidate.commit_sha == current:
        message = "the current revision is never pruned (§15.1); a plan naming it is refused"
        problems.append(Problem(code="HFRET001", message=message, repository=where))
    generations = [revision.publication_generation for revision in revisions]
    if generations and candidate.publication_generation != min(generations):
        message = (
            f"generation {candidate.publication_generation} is not the oldest retained "
            f"({min(generations)}); retention order comes from the generation, never from time"
        )
        problems.append(Problem(code="HFRET001", message=message, repository=where))
    if candidate not in revisions:
        message = "the selected revision is not one this repository retains"
        problems.append(Problem(code="HFRET001", message=message, repository=where))
    return problems


def require_valid_selection(
    candidate: RetainedRevision, revisions: Sequence[RetainedRevision], *, current: str
) -> None:
    """Raise unless this selection is one policy permits."""
    if problems := selection_problems(candidate, revisions, current=current):
        raise RetentionError(problems)


def selection_of(candidate: RetainedRevision, tree: str, manifest: str) -> PruneSelection:
    """Describe the selected instance for a prune plan.

    Sizes come from the manifest rather than from the filesystem, because the
    manifest is what this archive proved and a directory walk during a prune
    would be measuring bytes that hardlinks share with revisions that are
    staying — the number would be true of the tree and false about what removing
    it releases.
    """
    return PruneSelection(
        commit_sha=candidate.commit_sha,
        file_count=candidate.manifest.file_count,
        logical_bytes=candidate.manifest.total_bytes,
        manifest=manifest,
        publication_generation=candidate.publication_generation,
        publication_id=candidate.reference.publication_id,
        tree=tree,
    )


# --------------------------------------------------------------------------- #
# Planning a prune (plan §15.2 steps 1-4)
# --------------------------------------------------------------------------- #


def plan_prune(
    layout: ArchiveLayout,
    identity: RepositoryIdentity,
    *,
    maximum: int,
    generated_at: datetime,
) -> PrunePlan | None:
    """Describe the prune this repository needs, or `None` when it needs none.

    Plan §15.2 steps 1-4, and the whole of what `prune --dry-run` reports. It is
    built from the same reads a prune performs — the per-SHA references, the
    current reference, and the immutable manifests — so a plan an operator
    reviewed is the plan that runs, not an approximation of it.

    Non-mutating by construction: nothing here writes, and the plan is a value.
    Persisting it is checkpoint 1 of the prune transaction and belongs to
    `--apply`, because a plan that was written down is a commitment and reading
    one should not be.

    `None` covers every case `prune_candidate` refuses plus one more: a
    repository with no current reference at all. That is a repository whose first
    publication has not completed, and pruning it would remove a revision while
    consumers have nothing to be pointed at.
    """
    revisions = ordered_revisions(layout, identity)
    repository = RepositoryLayout(archive=layout, identity=identity)
    if not repository.current_ref.exists():
        return None
    current = read_reference(layout, repository.current_ref)
    candidate = prune_candidate(revisions, current=current.commit_sha, maximum=maximum)
    if candidate is None:
        return None
    require_valid_selection(candidate, revisions, current=current.commit_sha)

    commit = CommitSha(candidate.commit_sha)
    publication = PublicationId(candidate.reference.publication_id)
    return PrunePlan(
        # Exactly the one revision going away. Blobs it shares with revisions
        # that are staying survive because those publications hold hardlinks to
        # them; the Hub cache API decides which blobs that leaves unreferenced,
        # and this application never reasons about it (`FS-14`).
        cache_revisions_to_delete=(candidate.commit_sha,),
        current=RevisionSummary(
            commit_sha=current.commit_sha,
            publication_generation=current.publication_generation,
        ),
        generated_at=generated_at,
        plan_id=new_publication_id(),
        reason="sixth_unique_revision_published",
        repository_id=identity.id,
        repository_type=identity.type,
        retained=tuple(item.summary for item in revisions),
        selected=selection_of(
            candidate,
            tree=str(layout.archive_relative(repository.instance(commit, publication))),
            manifest=str(layout.archive_relative(repository.manifest(commit, publication))),
        ),
        # An estimate, and named one. The logical size of the tree is an upper
        # bound on what its removal releases: blobs shared with retained
        # revisions release nothing, and ZFS snapshots may hold the rest for
        # weeks (§15.3). Reporting the bound is honest; reporting a computed
        # figure would imply a precision the storage layer does not offer.
        unique_bytes_released_estimate=candidate.manifest.total_bytes,
    )


def plan_all(
    layout: ArchiveLayout,
    identities: Sequence[RepositoryIdentity],
    *,
    maximum: int,
    generated_at: datetime,
) -> tuple[PrunePlan, ...]:
    """Every prune the archive currently needs, in repository order.

    One plan per repository at most: §15.2 removes *the* oldest eligible
    revision after a sixth is published, not every revision above the limit. A
    repository somehow holding eight would be brought down one revision per run,
    which is slower and is the behaviour that cannot delete four things by
    mistake.
    """
    plans = [
        plan
        for identity in identities
        if (plan := plan_prune(layout, identity, maximum=maximum, generated_at=generated_at))
    ]
    return tuple(plans)


# --------------------------------------------------------------------------- #
# Performing a prune (plan §15.2, `docs/architecture.md` §7.4)
# --------------------------------------------------------------------------- #


def apply_prune(
    layout: ArchiveLayout,
    plan: PrunePlan,
    *,
    envelope: Mapping[str, Any],
    now: datetime | None = None,
) -> PrunedRevisionRecord:
    """Execute one validated prune, checkpoint by checkpoint (§7.4).

    **Checkpoint 7 is the commit point**, and it divides the transaction into two
    failure regimes that behave oppositely. Before it, a failure rolls the
    archive back to six published revisions — over-retention is always preferable
    to a revision that should not have gone. At or after it, a failure never
    republishes: exactly five revisions are consumer-visible and the complete
    manifest is still recoverable from trash, so re-adding the sixth would
    contradict a decision the archive already recorded.

    The order of steps 3 and 4 is deliberate and reversed from plan §15.2's
    original text (decision 4). The per-SHA reference is removed *before* the
    tree is tombstoned, because the reverse leaves a window in which a reference
    names a tree that has been renamed away — which breaks `FS-10` and would be
    visible to `verify` and `repair`, both of which resolve per-SHA references.
    Recovery never needed the reference to find the tree: the persisted plan
    names it.

    Cache deletion at step 2 happens while all six revisions are still published,
    so the published hardlinks hold the bytes whatever the cache does.
    """
    stamp = now or datetime.now(UTC)
    identity = RepositoryIdentity.of(plan.repository_type, plan.repository_id)
    repository = RepositoryLayout(archive=layout, identity=identity)
    commit = CommitSha(plan.selected.commit_sha)
    publication = PublicationId(plan.selected.publication_id)

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
        commit_sha=plan.selected.commit_sha,
        publication_id=plan.selected.publication_id,
    )
    transaction.checkpoint("plan_persisted", plan=plan.model_dump(mode="json"))

    freed = delete_cache_revision(layout.hub_cache, commit)
    transaction.checkpoint("cache_revision_deleted", commit_sha=commit, expected_freed_bytes=freed)

    reference = repository.revision_ref(commit)
    reference.unlink(missing_ok=True)
    fsync_directory(reference.parent)
    transaction.checkpoint(
        "revision_ref_removed", revision_ref_absent=str(layout.archive_relative(reference))
    )

    trash = layout.trash_for(transaction_id)
    trash.directory.mkdir(mode=TRASH_MODE, parents=True)
    tree = repository.instance(commit, publication)
    tree.rename(trash.tree)
    fsync_directory(trash.directory)
    transaction.checkpoint(
        "tree_tombstoned",
        tombstoned_tree_path=str(layout.archive_relative(trash.tree)),
        file_count=plan.selected.file_count,
    )

    manifest_path = repository.manifest(commit, publication)
    manifest_bytes = manifest_path.read_bytes()
    manifest_path.rename(trash.manifest)
    fsync_directory(trash.directory)
    transaction.checkpoint(
        "manifest_tombstoned",
        tombstoned_manifest_path=str(layout.archive_relative(trash.manifest)),
        manifest_sha256=sha256_bytes(manifest_bytes),
    )

    catalog_path = publish_catalog(layout, rebuild_catalog(layout, generated_at=stamp))
    transaction.checkpoint(
        "catalog_published", catalog_path=str(layout.archive_relative(catalog_path))
    )

    # The commit point. Above it the archive can still be put back; below it,
    # five revisions are what consumers see and that is now the truth.
    transaction.checkpoint("prune_logically_committed", retained=len(plan.retained) - 1)

    record = PrunedRevisionRecord(
        commit_sha=plan.selected.commit_sha,
        file_count=plan.selected.file_count,
        logical_bytes=plan.selected.logical_bytes,
        manifest_archived_at=stamp,
        plan_id=plan.plan_id,
        publication_generation=plan.selected.publication_generation,
        publication_id=plan.selected.publication_id,
        pruned_at=stamp,
        reason=plan.reason,
        repository_id=plan.repository_id,
        repository_type=plan.repository_type,
        retained_after=tuple(
            summary for summary in plan.retained if summary.commit_sha != plan.selected.commit_sha
        ),
        transaction_id=transaction_id,
        tree=plan.selected.tree,
    )
    audit = repository.pruned_records(commit)
    audit.mkdir(mode=AUDIT_MODE, parents=True, exist_ok=True)
    # The original manifest, byte for byte. It is the evidence of what was there,
    # and re-serializing it from a parsed model would be this release's rendering
    # of it rather than the bytes the archive published (`FS-06`).
    atomic_write_bytes(
        repository.pruned_manifest(commit, publication), manifest_bytes, mode=AUDIT_FILE_MODE
    )
    write_model(
        repository.prune_record(commit, publication), record, mode=AUDIT_FILE_MODE, code="HFRET004"
    )
    fsync_directory(audit)
    transaction.checkpoint("audit_record_written", audit_path=str(layout.archive_relative(audit)))

    shutil.rmtree(trash.directory)
    transaction.checkpoint(
        "trash_removed", trash_absent=str(layout.archive_relative(trash.directory))
    )
    transaction.checkpoint("prune_completed", state="committed")
    transaction.commit()
    return record
