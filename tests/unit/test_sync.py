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

import hashlib
import os
from typing import TYPE_CHECKING, Any

import pytest

from hfcache.errors import ExitCode, SynchronizationError
from hfcache.hub import TreeEntry
from hfcache.identity import CommitSha, PublicationId, RepositoryIdentity
from hfcache.manifests import DependencyObservation, HashReuse, RevisionManifest
from hfcache.paths import ArchiveLayout, RepositoryLayout
from hfcache.reporting import RuntimeVersions
from hfcache.sync import (
    KnownDigest,
    ObjectIdentity,
    Timeline,
    build_manifest,
    completeness_problems,
    hash_snapshot,
    published_digests,
    snapshot_paths,
)
from tests.fixtures import examples

if TYPE_CHECKING:
    from pathlib import Path

MODEL = RepositoryIdentity.of("model", "organization/model-name")
SHA = "0123456789abcdef0123456789abcdef01234567"
OTHER_SHA = "89abcdef0123456789abcdef0123456789abcdef"
PUBLICATION = "0f1e2d3c4b5a69788796a5b4c3d2e1f0"


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
# Completeness (docs/cli.md sync contract)
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


# --------------------------------------------------------------------------- #
# Hashing new content (docs/cli.md sync contract, AD-18)
# --------------------------------------------------------------------------- #

PAYLOAD = b"the bytes of one repository file"
OTHER = b"different bytes entirely!"
PAYLOAD_DIGEST = hashlib.sha256(PAYLOAD).hexdigest()
OTHER_DIGEST = hashlib.sha256(OTHER).hexdigest()


def hashed(snapshot: Path, tree, **keywords):
    return hash_snapshot(snapshot, tree, identity=MODEL, **keywords)


def test_every_object_is_read_and_hashed(cache, snapshot):
    landed(cache, snapshot, "config.json", PAYLOAD)
    landed(cache, snapshot, "model.bin", OTHER)
    tree = [
        TreeEntry(path="config.json", size=len(PAYLOAD)),
        TreeEntry(path="model.bin", size=len(OTHER)),
    ]

    result = hashed(snapshot, tree)

    assert [entry.sha256 for entry in result.files] == [PAYLOAD_DIGEST, OTHER_DIGEST]
    assert result.hashed_objects == 2
    assert result.hashed_bytes == len(PAYLOAD) + len(OTHER)
    assert result.reused_digests == 0


def test_entries_come_back_sorted_by_path(cache, snapshot):
    landed(cache, snapshot, "z.json", PAYLOAD)
    landed(cache, snapshot, "a.bin", OTHER)
    tree = [TreeEntry(path="z.json", size=len(PAYLOAD)), TreeEntry(path="a.bin", size=len(OTHER))]

    result = hashed(snapshot, tree)

    assert [entry.path for entry in result.files] == ["a.bin", "z.json"]


def test_an_upstream_digest_is_never_substituted_for_reading(cache, snapshot):
    # `AD-18`: the manifest records what this archive read, not what it was told.
    landed(cache, snapshot, "model.bin", PAYLOAD)

    result = hashed(snapshot, [TreeEntry(path="model.bin", size=len(PAYLOAD))])

    assert result.files[0].sha256 == PAYLOAD_DIGEST
    assert result.files[0].reused_from is None


def test_two_paths_sharing_one_inode_are_read_once(cache, snapshot):
    # A unique *physical object*, which is what AD-18 counts. Both paths still
    # become manifest entries; what was avoided is the second read.
    target = blob(cache, "shared", PAYLOAD)
    for name in ("first.bin", "second.bin"):
        (snapshot / name).symlink_to(target)
    tree = [TreeEntry(path=name, size=len(PAYLOAD)) for name in ("first.bin", "second.bin")]

    result = hashed(snapshot, tree)

    assert len(result.files) == 2
    assert {entry.sha256 for entry in result.files} == {PAYLOAD_DIGEST}
    assert result.hashed_objects == 1
    assert result.hashed_bytes == len(PAYLOAD)
    # Both were read during this run, so neither is a cross-run reuse.
    assert result.reused_digests == 0
    assert result.total_bytes == 2 * len(PAYLOAD)


def test_a_digest_is_reused_for_a_proven_identical_inode(cache, snapshot):
    # The only reuse AD-18 permits: same physical inode, same size, and a digest
    # from a retained publication.
    source = landed(cache, snapshot, "model.bin", PAYLOAD)
    known = {
        ObjectIdentity.of(source): KnownDigest(
            commit_sha=CommitSha(OTHER_SHA),
            publication_id=PublicationId(PUBLICATION),
            sha256="a" * 64,
            size=len(PAYLOAD),
        )
    }

    result = hashed(snapshot, [TreeEntry(path="model.bin", size=len(PAYLOAD))], known=known)

    assert result.files[0].sha256 == "a" * 64
    assert result.files[0].reused_from is not None
    assert result.files[0].reused_from.commit_sha == OTHER_SHA
    assert result.hashed_objects == 0
    assert result.hashed_bytes == 0
    assert result.reused_digests == 1


def test_a_size_that_no_longer_matches_refuses_the_reuse(cache, snapshot):
    # An inode number is reused by the filesystem after deletion, so the inode
    # alone is not proof. A changed size is the cheapest evidence it happened.
    source = landed(cache, snapshot, "model.bin", PAYLOAD)
    known = {
        ObjectIdentity.of(source): KnownDigest(
            commit_sha=CommitSha(OTHER_SHA),
            publication_id=PublicationId(PUBLICATION),
            sha256="a" * 64,
            size=len(PAYLOAD) + 1,
        )
    }

    result = hashed(snapshot, [TreeEntry(path="model.bin", size=len(PAYLOAD))], known=known)

    assert result.files[0].sha256 == PAYLOAD_DIGEST
    assert result.files[0].reused_from is None
    assert result.hashed_objects == 1


def test_a_different_inode_is_never_reused_however_similar(cache, snapshot):
    # Same bytes, same size, different object: it gets read.
    landed(cache, snapshot, "model.bin", PAYLOAD)
    elsewhere = blob(cache, "unrelated", PAYLOAD)
    known = {
        ObjectIdentity.of(elsewhere): KnownDigest(
            commit_sha=CommitSha(OTHER_SHA),
            publication_id=PublicationId(PUBLICATION),
            sha256="a" * 64,
            size=len(PAYLOAD),
        )
    }

    result = hashed(snapshot, [TreeEntry(path="model.bin", size=len(PAYLOAD))], known=known)

    assert result.files[0].sha256 == PAYLOAD_DIGEST
    assert result.hashed_objects == 1


def test_an_empty_snapshot_hashes_nothing(snapshot):
    result = hashed(snapshot, [])

    assert result.files == ()
    assert (result.hashed_objects, result.hashed_bytes, result.total_bytes) == (0, 0, 0)


def test_an_object_that_vanished_after_the_completeness_check_is_hfsyn009(cache, snapshot):
    result = hash_snapshot
    tree = [TreeEntry(path="model.bin", size=len(PAYLOAD))]

    with pytest.raises(SynchronizationError) as caught:
        result(snapshot, tree, identity=MODEL)

    assert codes(caught.value.problems) == ["HFSYN009"]
    assert caught.value.exit_code == ExitCode.SYNC
    assert caught.value.problems[0].repository == MODEL.selector


def test_an_unreadable_object_is_hfsyn009_not_an_integrity_failure(cache, snapshot):
    # A cache object that cannot be read means the sync failed, not that the
    # archive is corrupt — nothing has been published yet.
    source = landed(cache, snapshot, "model.bin", PAYLOAD)
    source.resolve().chmod(0o000)
    try:
        with pytest.raises(SynchronizationError) as caught:
            hashed(snapshot, [TreeEntry(path="model.bin", size=len(PAYLOAD))])
    finally:
        source.resolve().chmod(0o600)

    assert codes(caught.value.problems) == ["HFSYN009"]
    assert caught.value.exit_code == ExitCode.SYNC


# --------------------------------------------------------------------------- #
# Indexing a retained publication's digests
# --------------------------------------------------------------------------- #


def test_a_published_tree_is_indexed_by_the_inode_each_object_occupies_now(tmp_path):
    # The manifest supplies the digest and the filesystem supplies the identity;
    # neither alone would let AD-18's reuse rule be checked.
    manifest = examples.manifest()
    tree = tmp_path / "tree"
    tree.mkdir()
    files = {}
    for entry in manifest.files:
        path = tree / entry.path
        path.write_bytes(b"x" * entry.size if entry.size < 100 else b"")
        files[entry.path] = path

    index = published_digests(tree, manifest)

    for entry in manifest.files:
        known = index[ObjectIdentity.of(files[entry.path])]
        assert known.sha256 == entry.sha256
        assert known.size == entry.size
        assert known.commit_sha == manifest.commit_sha
        assert known.publication_id == manifest.publication_id


def test_a_manifest_path_the_tree_no_longer_holds_is_skipped(tmp_path):
    # A missing published file is real corruption, but it is `verify`'s finding
    # to make; here it only means there is no proven inode to reuse from.
    manifest = examples.manifest()
    tree = tmp_path / "tree"
    tree.mkdir()

    assert published_digests(tree, manifest) == {}


# --------------------------------------------------------------------------- #
# Describing the revision (docs/cli.md sync contract, the manifest schema)
# --------------------------------------------------------------------------- #

TIMELINE = Timeline(
    first_observed_at=examples.at("2026-07-26T09:00:00.000000Z"),
    download_started_at=examples.at("2026-07-26T09:00:01.000000Z"),
    download_completed_at=examples.at("2026-07-26T09:00:30.000000Z"),
    verified_at=examples.at("2026-07-26T09:00:45.000000Z"),
    published_at=examples.at("2026-07-26T09:00:50.000000Z"),
)


@pytest.fixture
def repository_layout(tmp_path: Path) -> RepositoryLayout:
    return RepositoryLayout(archive=ArchiveLayout(root=tmp_path / "archive"), identity=MODEL)


def described(hashed_snapshot, tree, layout, **overrides):
    arguments: dict[str, Any] = {
        "identity": MODEL,
        "requested_revision": "main",
        "commit_sha": CommitSha(SHA),
        "publication_id": PublicationId(PUBLICATION),
        "publication_generation": 1,
        "publication_mode": "hardlink",
        "tree": tree,
        "hashed": hashed_snapshot,
        "layout": layout,
        "hub_endpoint": "https://huggingface.co",
        "timeline": TIMELINE,
    }
    return build_manifest(**(arguments | overrides))


def test_a_manifest_describes_every_file_that_was_published(cache, snapshot, repository_layout):
    landed(cache, snapshot, "config.json", PAYLOAD)
    landed(cache, snapshot, "model.bin", OTHER)
    tree = [
        TreeEntry(path="config.json", size=len(PAYLOAD), git_oid="a" * 40),
        TreeEntry(path="model.bin", size=len(OTHER), lfs_sha256="b" * 64, xet_hash="c" * 64),
    ]

    manifest = described(hashed(snapshot, tree), tree, repository_layout)

    assert manifest.file_count == 2
    assert [entry.path for entry in manifest.files] == ["config.json", "model.bin"]
    assert manifest.total_bytes == len(PAYLOAD) + len(OTHER)
    assert manifest.commit_sha == SHA
    assert manifest.repository_id == MODEL.id
    assert manifest.publication_generation == 1


def test_sizes_and_digests_come_from_what_was_read_not_from_the_hub(
    cache, snapshot, repository_layout
):
    # `AD-18`: the Hub's size is a claim. Completeness already made them agree,
    # so the way to see which one reached the manifest is to make them differ.
    landed(cache, snapshot, "model.bin", PAYLOAD)
    tree = [TreeEntry(path="model.bin", size=len(PAYLOAD))]
    result = hashed(snapshot, tree)

    manifest = described(result, [TreeEntry(path="model.bin", size=999_999)], repository_layout)

    assert manifest.files[0].size == len(PAYLOAD)
    assert manifest.files[0].sha256 == PAYLOAD_DIGEST


def test_upstream_identifiers_are_recorded_as_comparison_values(cache, snapshot, repository_layout):
    landed(cache, snapshot, "model.bin", PAYLOAD)
    tree = [
        TreeEntry(
            path="model.bin",
            size=len(PAYLOAD),
            git_oid="a" * 40,
            lfs_sha256="b" * 64,
            xet_hash="c" * 64,
        )
    ]

    manifest = described(hashed(snapshot, tree), tree, repository_layout)

    upstream = manifest.files[0].upstream
    assert (upstream.git_oid, upstream.lfs_sha256, upstream.xet_hash) == (
        "a" * 40,
        "b" * 64,
        "c" * 64,
    )
    # Recorded beside the digest, never as it.
    assert manifest.files[0].sha256 == PAYLOAD_DIGEST


def test_an_object_the_hub_said_nothing_about_records_no_identifiers(
    cache, snapshot, repository_layout
):
    landed(cache, snapshot, "model.bin", PAYLOAD)
    tree = [TreeEntry(path="model.bin", size=len(PAYLOAD))]

    manifest = described(hashed(snapshot, tree), tree, repository_layout)

    upstream = manifest.files[0].upstream
    assert (upstream.git_oid, upstream.lfs_sha256, upstream.xet_hash) == (None, None, None)


def test_a_hashed_object_records_that_it_was_downloaded_and_read(
    cache, snapshot, repository_layout
):
    landed(cache, snapshot, "model.bin", PAYLOAD)
    tree = [TreeEntry(path="model.bin", size=len(PAYLOAD))]

    manifest = described(hashed(snapshot, tree), tree, repository_layout)

    provenance = manifest.files[0].provenance
    assert provenance.hashed is True
    assert provenance.source == "hub_download"
    assert provenance.cache_root == "canonical"
    assert provenance.hash_reused_from is None
    assert manifest.verification.reused_digests == 0


def test_a_reused_digest_names_the_publication_it_came_from(cache, snapshot, repository_layout):
    # So no manifest holds a digest whose origin cannot be traced to bytes this
    # archive read.
    source = landed(cache, snapshot, "model.bin", PAYLOAD)
    known = {
        ObjectIdentity.of(source): KnownDigest(
            commit_sha=CommitSha(OTHER_SHA),
            publication_id=PublicationId(PUBLICATION),
            sha256="a" * 64,
            size=len(PAYLOAD),
        )
    }
    tree = [TreeEntry(path="model.bin", size=len(PAYLOAD))]

    manifest = described(hashed(snapshot, tree, known=known), tree, repository_layout)

    provenance = manifest.files[0].provenance
    assert provenance.hashed is False
    assert provenance.source == "cache_reuse"
    assert provenance.hash_reused_from == HashReuse(
        commit_sha=OTHER_SHA, publication_id=PUBLICATION
    )
    assert manifest.verification.reused_digests == 1


def test_a_repair_download_records_the_isolated_cache_it_came_from(
    cache, snapshot, repository_layout
):
    # `FS-14`: a repair never reuses the canonical cache, and the manifest says so.
    landed(cache, snapshot, "model.bin", PAYLOAD)
    tree = [TreeEntry(path="model.bin", size=len(PAYLOAD))]

    manifest = described(hashed(snapshot, tree), tree, repository_layout, cache_root="repair")

    assert manifest.files[0].provenance.cache_root == "repair"
    assert manifest.files[0].provenance.source == "repair_download"


def test_the_verification_summary_counts_objects_not_paths(cache, snapshot, repository_layout):
    target = blob(cache, "shared", PAYLOAD)
    for name in ("first.bin", "second.bin"):
        (snapshot / name).symlink_to(target)
    tree = [TreeEntry(path=name, size=len(PAYLOAD)) for name in ("first.bin", "second.bin")]

    manifest = described(hashed(snapshot, tree), tree, repository_layout)

    assert manifest.file_count == 2
    assert manifest.verification.hashed_objects == 1
    assert manifest.verification.hashed_bytes == len(PAYLOAD)
    assert manifest.total_bytes == 2 * len(PAYLOAD)
    assert manifest.verification.completeness_checked is True


def test_the_manifest_names_its_own_tree_archive_relative(cache, snapshot, repository_layout):
    landed(cache, snapshot, "model.bin", PAYLOAD)
    tree = [TreeEntry(path="model.bin", size=len(PAYLOAD))]

    manifest = described(hashed(snapshot, tree), tree, repository_layout)

    # Decision 13: only a *reference* is relative to `published/`.
    assert manifest.tree.startswith("published/repos/models/")
    assert manifest.tree == str(
        repository_layout.manifest_tree_field(CommitSha(SHA), PublicationId(PUBLICATION))
    )


def test_the_timeline_is_the_callers_because_it_records_when_work_happened(
    cache, snapshot, repository_layout
):
    landed(cache, snapshot, "model.bin", PAYLOAD)
    tree = [TreeEntry(path="model.bin", size=len(PAYLOAD))]

    manifest = described(hashed(snapshot, tree), tree, repository_layout)

    assert manifest.download_started_at == TIMELINE.download_started_at
    assert manifest.published_at == TIMELINE.published_at
    assert manifest.verified_at == manifest.verification.verified_at


def test_this_processs_versions_are_recorded(cache, snapshot, repository_layout):
    landed(cache, snapshot, "model.bin", PAYLOAD)
    tree = [TreeEntry(path="model.bin", size=len(PAYLOAD))]

    manifest = described(hashed(snapshot, tree), tree, repository_layout)

    versions = RuntimeVersions.measured()
    assert manifest.application_version == versions.application
    assert manifest.python_version == versions.python
    assert manifest.huggingface_hub_version == versions.huggingface_hub


def test_dependencies_are_sorted_however_they_arrive(cache, snapshot, repository_layout):
    # The manifest model requires the ordering; the builder supplies it rather
    # than making every caller remember to.
    landed(cache, snapshot, "model.bin", PAYLOAD)
    tree = [TreeEntry(path="model.bin", size=len(PAYLOAD))]
    observations = [
        DependencyObservation(
            confidence="high",
            declared=False,
            detected_id="z/base",
            managed=False,
            source_field="base_model",
            source_file="README.md",
        ),
        DependencyObservation(
            confidence="medium",
            declared=True,
            detected_id="a/base",
            managed=True,
            source_field="base_model_name_or_path",
            source_file="adapter_config.json",
        ),
    ]

    manifest = described(hashed(snapshot, tree), tree, repository_layout, dependencies=observations)

    # Byte-wise, so `README.md` precedes `adapter_config.json`: `R` is 0x52 and
    # `a` is 0x61. Deterministic bytes matter more here than alphabetical taste.
    assert [item.source_file for item in manifest.dependencies] == [
        "README.md",
        "adapter_config.json",
    ]


def test_a_manifest_round_trips_through_its_durable_form(cache, snapshot, repository_layout):
    # The point of building one: it is written and read back later, and the
    # model refuses anything whose arithmetic does not describe a real tree.
    landed(cache, snapshot, "config.json", PAYLOAD)
    landed(cache, snapshot, "model.bin", OTHER)
    tree = [
        TreeEntry(path="config.json", size=len(PAYLOAD)),
        TreeEntry(path="model.bin", size=len(OTHER)),
    ]

    manifest = described(hashed(snapshot, tree), tree, repository_layout)

    assert RevisionManifest.model_validate_json(manifest.to_json()) == manifest


def test_a_copy_mode_publication_records_the_mode_it_used(cache, snapshot, repository_layout):
    landed(cache, snapshot, "model.bin", PAYLOAD)
    tree = [TreeEntry(path="model.bin", size=len(PAYLOAD))]

    manifest = described(hashed(snapshot, tree), tree, repository_layout, publication_mode="copy")

    assert manifest.publication_mode == "copy"
