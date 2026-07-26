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

from dataclasses import dataclass
from typing import TYPE_CHECKING, final

from hfcache.errors import IntegrityError, Problem, RetentionError
from hfcache.identity import CommitSha, PublicationId
from hfcache.manifests import RevisionManifest
from hfcache.models import PruneSelection, RevisionSummary
from hfcache.paths import RepositoryLayout
from hfcache.publication import retained_references
from hfcache.storage import read_model

if TYPE_CHECKING:
    from collections.abc import Sequence

    from hfcache.identity import RepositoryIdentity
    from hfcache.models import Reference
    from hfcache.paths import ArchiveLayout

__all__ = [
    "RetainedRevision",
    "ordered_revisions",
    "over_retention",
    "prune_candidate",
    "require_valid_selection",
    "selection_of",
    "selection_problems",
]


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
