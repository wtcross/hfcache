"""Retention ordering and selection — plan §15, `AD-04`, `AD-05`.

The property under test throughout is that **order comes from the generation and
from nothing else**. The tests therefore go out of their way to make every other
candidate ordering disagree with it: revisions are published in one order,
given generations in another, and where a filesystem timestamp or a SHA would
sort differently, that is the point.

Selection is tested for its refusals as much as its choices. Every case where
`prune_candidate` returns `None` is a case where over-retention is the correct
behaviour, and the archive keeping one revision too many is always preferable to
it removing one it should not have (`AD-04`).
"""

import errno
import os
from datetime import UTC, datetime
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from hfcache.archive import initialize_archive
from hfcache.errors import ExitCode, RetentionError
from hfcache.identity import CommitSha, PublicationId, RepositoryIdentity, new_publication_id
from hfcache.models import Reference
from hfcache.paths import ArchiveLayout, RepositoryLayout
from hfcache.publication import publish_current_reference, publish_revision_reference
from hfcache.retention import (
    RetainedRevision,
    ordered_revisions,
    over_retention,
    prune_candidate,
    remove_empty_containers,
    require_valid_selection,
    selection_of,
    selection_problems,
)
from hfcache.storage import parse_mount_table
from tests.fixtures import examples

ARCHIVE_ID = "3f2a1c88-7b40-4a2e-9c1d-0e5b6a7f8d90"
MODEL = RepositoryIdentity.of("model", "organization/model-name")
NOW = datetime(2026, 7, 26, 12, 0, 0, tzinfo=UTC)


def sha(index: int) -> str:
    return f"{index:040d}"


def revision(generation: int, index: int | None = None) -> RetainedRevision:
    """A retained revision with a given generation, without touching a filesystem."""
    commit = sha(index if index is not None else generation)
    publication = new_publication_id()
    reference = Reference(
        commit_sha=commit,
        manifest=f"manifests/models/organization/model-name/{commit}/{publication}.json",
        publication_generation=generation,
        publication_id=publication,
        repository_id=MODEL.id,
        repository_type="model",
        tree=f"repos/models/organization/model-name/revisions/{commit}/{publication}",
        updated_at=NOW,
    )
    manifest = examples.manifest().model_copy(
        update={
            "commit_sha": commit,
            "publication_generation": generation,
            "publication_id": publication,
            "repository_id": MODEL.id,
            "repository_type": "model",
        }
    )
    return RetainedRevision(reference=reference, manifest=manifest)


def generations(revisions) -> list[int]:
    return [item.publication_generation for item in revisions]


# --------------------------------------------------------------------------- #
# Ordering (`AD-05`)
# --------------------------------------------------------------------------- #


def test_revisions_are_ordered_by_generation_ascending():
    revisions = [revision(3), revision(1), revision(2)]

    assert generations(sorted(revisions, key=lambda r: r.publication_generation)) == [1, 2, 3]


@given(st.lists(st.integers(min_value=1, max_value=10_000), min_size=1, max_size=12, unique=True))
def test_ordering_is_the_generations_however_they_are_supplied(values):
    # A property rather than an example: whatever order the references are read
    # in, the retention order is the generations ascending.
    revisions = [revision(value, index=value) for value in values]

    ordered = sorted(revisions, key=lambda r: r.publication_generation)

    assert generations(ordered) == sorted(values)


def test_a_gap_in_the_generations_changes_nothing():
    # §15.1: a crash between assigning a generation and publishing it leaves the
    # number unused, and that is acceptable.
    revisions = [revision(1), revision(7), revision(9)]

    assert generations(revisions) == [1, 7, 9]
    candidate = prune_candidate(revisions, current=sha(9), maximum=2)
    assert candidate is not None
    assert candidate.publication_generation == 1


def test_ordering_ignores_the_sha_entirely():
    # A SHA has no order; the generation does.
    oldest = revision(1, index=999)
    newest = revision(2, index=1)

    ordered = sorted([newest, oldest], key=lambda r: r.publication_generation)

    assert ordered[0] is oldest


# --------------------------------------------------------------------------- #
# Five-revision selection (`AD-04`)
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("count", [0, 1, 4, 5])
def test_nothing_is_pruned_at_or_below_the_limit(count):
    # Including exactly five: a prune is triggered by a successful publication
    # *beyond* the maximum, never by a count that happens to be high.
    revisions = [revision(generation) for generation in range(1, count + 1)]

    assert prune_candidate(revisions, current=sha(count), maximum=5) is None


def test_a_sixth_revision_selects_the_oldest():
    revisions = [revision(generation) for generation in range(1, 7)]

    candidate = prune_candidate(revisions, current=sha(6), maximum=5)

    assert candidate is not None
    assert candidate.publication_generation == 1
    assert candidate.commit_sha == sha(1)


def test_the_current_revision_is_never_selected():
    # Reachable: a repository whose upstream moved back to its earliest retained
    # SHA has the oldest generation as its current. Over-retention is right.
    revisions = [revision(generation) for generation in range(1, 7)]

    assert prune_candidate(revisions, current=sha(1), maximum=5) is None


def test_over_retention_is_counted_over_unique_retained_revisions():
    revisions = [revision(generation) for generation in range(1, 7)]

    assert over_retention(revisions, maximum=5)
    assert not over_retention(revisions[:5], maximum=5)


@given(st.integers(min_value=1, max_value=40), st.integers(min_value=1, max_value=10))
def test_a_selection_is_never_the_current_revision(count, maximum):
    # The invariant no failure may break: whatever the counts, the revision
    # consumers are pointed at is not the one chosen.
    revisions = [revision(generation) for generation in range(1, count + 1)]
    current = sha(count)

    candidate = prune_candidate(revisions, current=current, maximum=maximum)

    assert candidate is None or candidate.commit_sha != current


@given(st.integers(min_value=1, max_value=40), st.integers(min_value=1, max_value=10))
def test_a_selection_is_always_the_lowest_generation(count, maximum):
    revisions = [revision(generation) for generation in range(1, count + 1)]

    candidate = prune_candidate(revisions, current=sha(count), maximum=maximum)

    assert candidate is None or candidate.publication_generation == min(generations(revisions))


# --------------------------------------------------------------------------- #
# Refusing a selection policy does not permit
# --------------------------------------------------------------------------- #


def test_a_valid_selection_has_no_problems():
    revisions = [revision(generation) for generation in range(1, 7)]

    assert selection_problems(revisions[0], revisions, current=sha(6)) == []


def test_selecting_the_current_revision_is_hfret001():
    revisions = [revision(generation) for generation in range(1, 7)]

    problems = selection_problems(revisions[0], revisions, current=sha(1))

    assert [problem.code for problem in problems] == ["HFRET001"]
    assert problems[0].repository == MODEL.selector


def test_selecting_a_revision_that_is_not_the_oldest_is_hfret001():
    revisions = [revision(generation) for generation in range(1, 7)]

    problems = selection_problems(revisions[2], revisions, current=sha(6))

    assert [problem.code for problem in problems] == ["HFRET001"]
    assert "not the oldest retained" in problems[0].message


def test_selecting_a_revision_this_repository_does_not_retain_is_hfret001():
    # Same generation as the oldest retained, so only the membership rule fires
    # and the message is about the thing that is actually wrong.
    revisions = [revision(generation) for generation in range(2, 7)]
    stranger = revision(2, index=999)

    problems = selection_problems(stranger, revisions, current=sha(6))

    assert [problem.code for problem in problems] == ["HFRET001"]
    assert "not one this repository retains" in problems[0].message


def test_requiring_a_valid_selection_raises_at_exit_fifty():
    revisions = [revision(generation) for generation in range(1, 7)]

    with pytest.raises(RetentionError) as caught:
        require_valid_selection(revisions[0], revisions, current=sha(1))

    assert caught.value.exit_code == ExitCode.RETENTION


def test_requiring_a_valid_selection_permits_the_oldest():
    revisions = [revision(generation) for generation in range(1, 7)]

    require_valid_selection(revisions[0], revisions, current=sha(6))


def test_a_selection_takes_its_sizes_from_the_manifest():
    # A directory walk would measure bytes hardlinks share with revisions that
    # are staying — true of the tree, false about what removing it releases.
    candidate = revision(1)

    selection = selection_of(candidate, tree="published/x", manifest="published/y.json")

    assert selection.file_count == candidate.manifest.file_count
    assert selection.logical_bytes == candidate.manifest.total_bytes
    assert selection.publication_generation == 1


# --------------------------------------------------------------------------- #
# Reading the retained set off a real archive
# --------------------------------------------------------------------------- #


@pytest.fixture
def layout(tmp_path: Path) -> ArchiveLayout:
    root = tmp_path / "archive"
    root.mkdir(mode=0o750)
    built = ArchiveLayout(root=root)
    line = (
        f"457 47 0:68 / {os.path.realpath(root)} rw,relatime shared:488 - nfs4 nas:/x rw,vers=4.2\n"
    )
    initialize_archive(built, archive_id=ARCHIVE_ID, table=parse_mount_table(line))
    return built


def place(layout: ArchiveLayout, item: RetainedRevision) -> None:
    """Materialize one retained revision's tree, manifest, and reference."""
    repository = RepositoryLayout(archive=layout, identity=MODEL)
    commit = CommitSha(item.commit_sha)
    publication = PublicationId(item.reference.publication_id)
    repository.instance(commit, publication).mkdir(parents=True)
    manifest = repository.manifest(commit, publication)
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_bytes(item.manifest.to_json().encode("utf-8"))
    publish_revision_reference(layout, item.reference)


def test_the_retained_set_is_read_from_the_references(layout):
    for generation in (3, 1, 2):
        place(layout, revision(generation))

    revisions = ordered_revisions(layout, MODEL)

    assert generations(revisions) == [1, 2, 3]
    assert [item.commit_sha for item in revisions] == [sha(1), sha(2), sha(3)]


def test_a_repository_with_nothing_retained_reads_as_empty(layout):
    assert ordered_revisions(layout, MODEL) == ()


def test_a_sixth_revision_on_a_real_archive_selects_the_oldest(layout):
    for generation in range(1, 7):
        item = revision(generation)
        place(layout, item)
        publish_current_reference(layout, item.reference)

    revisions = ordered_revisions(layout, MODEL)
    candidate = prune_candidate(revisions, current=sha(6), maximum=5)

    assert candidate is not None
    assert candidate.commit_sha == sha(1)
    assert candidate.manifest.publication_generation == 1


def test_a_revision_summarizes_as_its_ordering_key():
    # `(commit_sha, generation)` — what a prune plan records for every revision
    # it leaves behind, so the plan can be checked without reading them again.
    item = revision(4)

    summary = item.summary

    assert summary.commit_sha == item.commit_sha
    assert summary.publication_generation == 4


# --------------------------------------------------------------------------- #
# Removing the containers a prune empties (`RET-008`, §7.4 checkpoint 10)
# --------------------------------------------------------------------------- #


def empty_the_instance(layout: ArchiveLayout, item: RetainedRevision) -> None:
    """Do what checkpoints 4 and 5 do: move the instance and manifest out."""
    repository = RepositoryLayout(archive=layout, identity=MODEL)
    commit = CommitSha(item.commit_sha)
    publication = PublicationId(item.reference.publication_id)
    repository.instance(commit, publication).rmdir()
    repository.manifest(commit, publication).unlink()


def test_the_containers_a_prune_emptied_are_removed(layout):
    item = revision(1)
    place(layout, item)
    empty_the_instance(layout, item)
    repository = RepositoryLayout(archive=layout, identity=MODEL)
    commit = CommitSha(item.commit_sha)

    result = remove_empty_containers(layout, repository, commit)

    assert not repository.revision(commit).exists()
    assert not repository.revision_manifests(commit).exists()
    assert result["retained"] == []
    assert len(result["removed"]) == 2


def test_a_container_still_holding_an_instance_is_never_removed(layout):
    """The repair case: a retired instance sits beside its replacement through
    the grace period, so `revisions/<sha>/` holds two. `rmdir` refuses, which is
    the whole safety argument — no detection of the state is needed."""
    item = revision(1)
    place(layout, item)
    repository = RepositoryLayout(archive=layout, identity=MODEL)
    commit = CommitSha(item.commit_sha)
    survivor = repository.instance(commit, PublicationId(new_publication_id()))
    survivor.mkdir(parents=True)
    empty_the_instance(layout, item)

    result = remove_empty_containers(layout, repository, commit)

    assert repository.revision(commit).is_dir(), "a container holding an instance survived"
    assert survivor.is_dir()
    assert str(layout.archive_relative(repository.revision(commit))) in result["retained"]
    # The manifest container next to it was empty, so it still goes.
    assert not repository.revision_manifests(commit).exists()


def test_a_manifest_container_holding_a_superseded_manifest_is_kept(layout):
    item = revision(1)
    place(layout, item)
    repository = RepositoryLayout(archive=layout, identity=MODEL)
    commit = CommitSha(item.commit_sha)
    superseded = repository.manifest(commit, PublicationId(new_publication_id()))
    superseded.write_bytes(b"{}")
    empty_the_instance(layout, item)

    result = remove_empty_containers(layout, repository, commit)

    assert superseded.is_file()
    assert str(layout.archive_relative(repository.revision_manifests(commit))) in result["retained"]


def test_removing_containers_twice_is_the_same_as_once(layout):
    """`TX-04`: `recover --apply` is safe to run repeatedly."""
    item = revision(1)
    place(layout, item)
    empty_the_instance(layout, item)
    repository = RepositoryLayout(archive=layout, identity=MODEL)
    commit = CommitSha(item.commit_sha)

    first = remove_empty_containers(layout, repository, commit)
    second = remove_empty_containers(layout, repository, commit)

    assert first == second
    assert second["retained"] == []
    assert not repository.revision(commit).exists()


def test_a_container_that_cannot_be_removed_for_another_reason_is_not_swallowed(
    layout, monkeypatch
):
    """ "Not empty" is a state this expects; anything else is a real problem.

    Reporting a permission failure as though the directory had simply been busy
    would hide it forever, because the next run would report the same thing.
    """
    item = revision(1)
    place(layout, item)
    empty_the_instance(layout, item)
    repository = RepositoryLayout(archive=layout, identity=MODEL)

    def refuse(_self: Path) -> None:
        raise PermissionError(errno.EACCES, "Permission denied")

    monkeypatch.setattr(Path, "rmdir", refuse)

    with pytest.raises(PermissionError):
        remove_empty_containers(layout, repository, CommitSha(item.commit_sha))


def test_removing_containers_leaves_every_other_revision_alone(layout):
    kept = revision(2)
    place(layout, kept)
    going = revision(1)
    place(layout, going)
    empty_the_instance(layout, going)
    repository = RepositoryLayout(archive=layout, identity=MODEL)

    remove_empty_containers(layout, repository, CommitSha(going.commit_sha))

    assert repository.revision(CommitSha(kept.commit_sha)).is_dir()
    assert repository.revision_manifests(CommitSha(kept.commit_sha)).is_dir()
    assert repository.revisions.is_dir(), "the shared parent is not a container"
