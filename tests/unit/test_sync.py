"""The per-repository ingestion sequence — `hfcache.sync`.

The completeness check is the last thing between a download and a publication,
so what is asserted here is mostly refusal: a snapshot missing a file, holding
an extra one, disagreeing about a size, reaching outside the cache, or naming
two files that would become one. Each of those, allowed through, would produce
an immutable revision that is wrong in a way no later verification could
distinguish from corruption — because the manifest would describe exactly what
was published.

The snapshots here are built by hand rather than downloaded, laid out the way
the Hub cache lays one out: a `blobs/` directory of real content and a
`snapshots/<sha>/` tree of symlinks into it. That is what makes the containment
and symlink cases testable at all.
"""

import os
from typing import TYPE_CHECKING

import pytest

from hfcache.hub import TreeEntry
from hfcache.identity import RepositoryIdentity
from hfcache.sync import completeness_problems, snapshot_paths

if TYPE_CHECKING:
    from pathlib import Path

MODEL = RepositoryIdentity.of("model", "organization/model-name")
SHA = "0123456789abcdef0123456789abcdef01234567"


@pytest.fixture
def cache(tmp_path: Path) -> Path:
    """A private Hub cache root."""
    root = tmp_path / "hub"
    root.mkdir()
    return root


@pytest.fixture
def snapshot(cache: Path) -> Path:
    """An empty snapshot directory inside that cache."""
    path = cache / "models--organization--model-name" / "snapshots" / SHA
    path.mkdir(parents=True)
    return path


def blob(cache: Path, name: str, payload: bytes) -> Path:
    """A cache blob, which is where the bytes really live."""
    blobs = cache / "models--organization--model-name" / "blobs"
    blobs.mkdir(parents=True, exist_ok=True)
    path = blobs / name
    path.write_bytes(payload)
    return path


def landed(cache: Path, snapshot: Path, relative: str, payload: bytes) -> Path:
    """One repository file, reached through a symlink the way the cache does."""
    target = blob(cache, relative.replace("/", "_"), payload)
    link = snapshot / relative
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(target)
    return link


def codes(problems) -> list[str]:
    return [problem.code for problem in problems]


def check(snapshot: Path, tree, cache: Path):
    return completeness_problems(snapshot, tree, identity=MODEL, cache_root=cache)


# --------------------------------------------------------------------------- #
# Reading what landed
# --------------------------------------------------------------------------- #


def test_a_snapshot_reports_its_files_repository_relative(cache, snapshot):
    landed(cache, snapshot, "config.json", b"{}")
    landed(cache, snapshot, "nested/model.bin", b"weights")

    assert snapshot_paths(snapshot) == ("config.json", "nested/model.bin")


def test_directories_are_walked_and_never_reported(cache, snapshot):
    landed(cache, snapshot, "a/b/c/deep.bin", b"x")

    assert snapshot_paths(snapshot) == ("a/b/c/deep.bin",)


def test_an_empty_snapshot_reports_nothing(snapshot):
    assert snapshot_paths(snapshot) == ()


# --------------------------------------------------------------------------- #
# Completeness (plan §13.2 steps 6-8)
# --------------------------------------------------------------------------- #


def test_a_complete_snapshot_has_no_problems(cache, snapshot):
    landed(cache, snapshot, "config.json", b"{}")
    landed(cache, snapshot, "model.bin", b"weights!")
    tree = [TreeEntry(path="config.json", size=2), TreeEntry(path="model.bin", size=8)]

    assert check(snapshot, tree, cache) == []


def test_a_missing_file_is_hfsyn002(cache, snapshot):
    landed(cache, snapshot, "config.json", b"{}")
    tree = [TreeEntry(path="config.json", size=2), TreeEntry(path="model.bin", size=8)]

    problems = check(snapshot, tree, cache)

    assert codes(problems) == ["HFSYN002"]
    assert problems[0].location == "model.bin"
    assert problems[0].repository == MODEL.selector


def test_every_missing_file_is_reported_at_once(cache, snapshot):
    # An operator fixing an incomplete download should see the whole gap.
    tree = [TreeEntry(path=name, size=1) for name in ("a.bin", "b.bin", "c.bin")]

    problems = check(snapshot, tree, cache)

    assert [problem.location for problem in problems] == ["a.bin", "b.bin", "c.bin"]


def test_an_extra_file_is_hfsyn002(cache, snapshot):
    # Content the manifest cannot explain is never published.
    landed(cache, snapshot, "config.json", b"{}")
    landed(cache, snapshot, "leftover.bin", b"from an earlier revision")

    problems = check(snapshot, [TreeEntry(path="config.json", size=2)], cache)

    assert codes(problems) == ["HFSYN002"]
    assert problems[0].location == "leftover.bin"
    assert "not listed in the Hub tree" in problems[0].message


def test_a_size_disagreement_is_hfsyn003(cache, snapshot):
    landed(cache, snapshot, "model.bin", b"only eight")

    problems = check(snapshot, [TreeEntry(path="model.bin", size=99)], cache)

    assert codes(problems) == ["HFSYN003"]
    assert problems[0].location == "model.bin"


def test_a_size_disagreement_does_not_claim_which_side_is_wrong(cache, snapshot):
    # The Hub's size is a claim, not evidence; the manifest records what was
    # read (`AD-18`). This check only has to stop the publication.
    landed(cache, snapshot, "model.bin", b"12345")

    problems = check(snapshot, [TreeEntry(path="model.bin", size=9)], cache)

    assert "disagree" in problems[0].message


def test_a_missing_file_is_not_also_reported_as_a_size_mismatch(cache, snapshot):
    # One incomplete download is one problem per file, not two.
    problems = check(snapshot, [TreeEntry(path="model.bin", size=8)], cache)

    assert codes(problems) == ["HFSYN002"]


def test_a_source_that_escapes_the_cache_root_is_hfsyn004(tmp_path, cache, snapshot):
    # The same proof publication performs (`FS-15`), run here so an escaping
    # link fails completeness rather than surviving to the staging loop.
    outside = tmp_path / "outside.bin"
    outside.write_bytes(b"weights!")
    (snapshot / "model.bin").symlink_to(outside)

    problems = check(snapshot, [TreeEntry(path="model.bin", size=8)], cache)

    assert codes(problems) == ["HFSYN004"]
    assert problems[0].location == "model.bin"


def test_a_dangling_link_is_hfsyn004(cache, snapshot):
    (snapshot / "model.bin").symlink_to(cache / "blobs" / "never-written")

    problems = check(snapshot, [TreeEntry(path="model.bin", size=8)], cache)

    assert codes(problems) == ["HFSYN004"]


def test_a_source_that_is_not_a_regular_file_is_hfsyn004(cache, snapshot):
    os.mkfifo(snapshot / "model.bin")

    problems = check(snapshot, [TreeEntry(path="model.bin", size=8)], cache)

    assert codes(problems) == ["HFSYN004"]


def test_a_link_to_a_directory_is_one_problem_not_two(cache, snapshot):
    # Counted as an entry of the snapshot rather than as a container, so it is
    # refused for what it is instead of being reported missing *and* unsafe.
    container = cache / "models--organization--model-name" / "blobs"
    container.mkdir(parents=True, exist_ok=True)
    (snapshot / "model.bin").symlink_to(container)

    problems = check(snapshot, [TreeEntry(path="model.bin", size=8)], cache)

    assert codes(problems) == ["HFSYN004"]
    assert "not a regular file" in problems[0].message


def test_a_dangling_link_never_passes_as_a_complete_file(cache, snapshot):
    # The trap this pair of `follow_symlinks=False` calls exists for: following
    # the link makes the entry look absent to one check and present to the
    # other, and the file passes completeness with nothing behind it.
    (snapshot / "model.bin").symlink_to(cache / "blobs" / "never-written")

    assert snapshot_paths(snapshot) == ("model.bin",)
    assert check(snapshot, [TreeEntry(path="model.bin", size=8)], cache) != []


def test_an_unsafe_source_is_not_also_reported_as_a_size_mismatch(tmp_path, cache, snapshot):
    outside = tmp_path / "outside.bin"
    outside.write_bytes(b"a different length entirely")
    (snapshot / "model.bin").symlink_to(outside)

    assert codes(check(snapshot, [TreeEntry(path="model.bin", size=8)], cache)) == ["HFSYN004"]


def test_two_upstream_names_that_fold_together_are_hfsyn002(cache, snapshot):
    # A consumer copying onto APFS or NTFS would silently merge them, and the
    # tree would then not match the manifest it was verified against (T-02).
    landed(cache, snapshot, "Model.bin", b"weights!")
    landed(cache, snapshot, "model.bin", b"weights!")
    tree = [TreeEntry(path="Model.bin", size=8), TreeEntry(path="model.bin", size=8)]

    problems = check(snapshot, tree, cache)

    assert codes(problems) == ["HFSYN002"]
    assert "fold to the same on-disk name" in problems[0].message


def test_an_upstream_name_that_could_escape_is_hfsyn004(cache, snapshot):
    # Refused before it is joined onto anything.
    problems = check(snapshot, [TreeEntry(path="../escape.bin", size=1)], cache)

    assert "HFSYN004" in codes(problems)


def test_every_problem_carries_the_repository_it_belongs_to(cache, snapshot):
    landed(cache, snapshot, "extra.bin", b"x")
    tree = [TreeEntry(path="missing.bin", size=1)]

    problems = check(snapshot, tree, cache)

    assert problems
    assert all(problem.repository == MODEL.selector for problem in problems)
