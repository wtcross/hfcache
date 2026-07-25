"""Building a staged tree, and writing the references that name it.

`FS-10` is the property this file is mostly about: a reference is written only
after both of its targets are durable. It is enforced at the point of the write
rather than by the caller, so the tests provoke it by publishing against an
archive where the tree, the manifest, or both are missing.

The archive here is a real temporary directory with the real layout, created by
`initialize_archive` — the modes, the setgid `published/` subtree, and the
`published/`-relative resolution of a reference's fields are all things a fake
would have to reproduce exactly to be worth anything.
"""

import os
import stat
from typing import TYPE_CHECKING

import pytest

from hfcache.archive import initialize_archive
from hfcache.errors import ExitCode, IntegrityError, SafetyError, SynchronizationError
from hfcache.identity import TransactionId, new_transaction_id
from hfcache.paths import ArchiveLayout
from hfcache.publication import (
    PUBLISHED_DIRECTORY_MODE,
    PUBLISHED_FILE_MODE,
    STAGING_MODE,
    create_staging,
    discard_staging,
    prepare_staged_parent,
    publish_current_reference,
    publish_revision_reference,
    read_reference,
    reference_target_problems,
    source_problems,
    staged_path,
)
from hfcache.storage import parse_mount_table
from tests.fixtures import examples

if TYPE_CHECKING:
    from pathlib import Path

    from hfcache.models import Reference

ARCHIVE_ID = "3f2a1c88-7b40-4a2e-9c1d-0e5b6a7f8d90"


def nfs_line(mount_point: str) -> str:
    return (
        f"457 47 0:68 / {mount_point} rw,nosuid,nodev,relatime shared:488 "
        f"- nfs4 nas.lab.cross.solutions:/mnt/tank/hf rw,vers=4.2"
    )


@pytest.fixture
def layout(tmp_path: Path) -> ArchiveLayout:
    """A real initialized archive on a temporary directory."""
    root = tmp_path / "archive"
    root.mkdir()
    built = ArchiveLayout(root=root)
    table = parse_mount_table(nfs_line(os.path.realpath(root)))
    initialize_archive(built, archive_id=ARCHIVE_ID, table=table)
    return built


@pytest.fixture
def reference() -> Reference:
    return examples.reference()


@pytest.fixture
def published(layout: ArchiveLayout, reference: Reference) -> Reference:
    """The same reference, with both of its targets actually created."""
    tree = layout.published / str(reference.tree)
    tree.mkdir(parents=True)
    manifest = layout.published / str(reference.manifest)
    manifest.parent.mkdir(parents=True)
    manifest.write_text("{}", encoding="utf-8")
    return reference


def codes(problems) -> list[str]:
    return [problem.code for problem in problems]


# --------------------------------------------------------------------------- #
# Staging (`FS-18`, `FS-04`)
# --------------------------------------------------------------------------- #


@pytest.fixture
def transaction() -> TransactionId:
    return new_transaction_id()


def test_staging_is_created_where_the_transaction_owns_it(layout, transaction):
    paths = create_staging(layout, transaction)

    assert paths.directory == layout.staging / transaction
    assert paths.tree.is_dir()
    assert str(layout.archive_relative(paths.directory)) == f".store/staging/{transaction}"


def test_staging_shares_a_filesystem_with_its_destination(layout, transaction):
    # `FS-04`: publication is a rename, so staging and `published/` must be one
    # filesystem. Both come from the same archive root, which is what guarantees
    # it — this asserts the guarantee rather than restating the construction.
    paths = create_staging(layout, transaction)

    assert paths.tree.stat().st_dev == layout.repos.stat().st_dev


def test_the_staged_tree_carries_the_mode_it_will_be_published_with(layout, transaction):
    # A rename does not change a directory's mode, so what is built here is what
    # a consumer sees.
    paths = create_staging(layout, transaction)

    assert stat.S_IMODE(paths.tree.stat().st_mode) == PUBLISHED_DIRECTORY_MODE
    assert stat.S_IMODE(paths.directory.stat().st_mode) == STAGING_MODE


def test_the_umask_does_not_reach_the_staged_modes(layout, transaction):
    original = os.umask(0o077)
    try:
        paths = create_staging(layout, transaction)
    finally:
        os.umask(original)

    assert stat.S_IMODE(paths.tree.stat().st_mode) == PUBLISHED_DIRECTORY_MODE


def test_staging_is_empty_when_it_is_created(layout, transaction):
    paths = create_staging(layout, transaction)

    assert list(paths.tree.iterdir()) == []


def test_a_second_transaction_gets_its_own_area(layout, transaction):
    first = create_staging(layout, transaction)
    second = create_staging(layout, new_transaction_id())

    assert first.directory != second.directory


def test_staging_that_already_exists_is_hfsyn005_rather_than_reused(layout, transaction):
    # Building into an area another transaction owns is the one thing a staging
    # directory named by transaction id exists to prevent.
    create_staging(layout, transaction)

    with pytest.raises(SynchronizationError) as caught:
        create_staging(layout, transaction)

    assert codes(caught.value.problems) == ["HFSYN005"]


def test_staging_that_cannot_be_created_is_hfsyn005(layout, transaction):
    layout.staging.chmod(0o500)
    try:
        with pytest.raises(SynchronizationError) as caught:
            create_staging(layout, transaction)
    finally:
        layout.staging.chmod(STAGING_MODE)

    assert codes(caught.value.problems) == ["HFSYN005"]
    assert caught.value.problems[0].location == f".store/staging/{transaction}"


def test_staging_is_discarded_wholesale(layout, transaction):
    paths = create_staging(layout, transaction)
    (paths.tree / "partial").mkdir()
    (paths.tree / "partial" / "file").write_text("half a revision", encoding="utf-8")

    assert discard_staging(layout, transaction)
    assert not paths.directory.exists()
    assert layout.staging.is_dir(), "the staging root itself is part of the layout"


def test_discarding_an_area_that_is_not_there_is_not_an_error(layout, transaction):
    # Recovery discards whatever a crashed run left, and "nothing" is a valid
    # thing to have left.
    assert not discard_staging(layout, transaction)


def test_only_a_transaction_shaped_name_can_be_discarded(layout):
    # `FS-18` and `FS-19`: the path is derived from a validated id, so a name
    # that is not one cannot become a path component at all.
    stranger = layout.staging / "somebody-elses-directory"
    stranger.mkdir()

    with pytest.raises(ValueError, match="transaction id"):
        discard_staging(layout, TransactionId("somebody-elses-directory"))

    assert stranger.is_dir(), "nothing outside the naming contract is removed"


# --------------------------------------------------------------------------- #
# Sources (`FS-15`)
# --------------------------------------------------------------------------- #


@pytest.fixture
def cache_root(layout) -> Path:
    return layout.hub_cache


def test_a_regular_file_inside_the_cache_root_is_accepted(cache_root):
    blob = cache_root / "blobs" / "abc123"
    blob.parent.mkdir(parents=True)
    blob.write_text("bytes", encoding="utf-8")

    assert source_problems(blob, cache_root=cache_root) == []


def test_a_cache_symlink_is_resolved_rather_than_refused(cache_root):
    # This is how `huggingface_hub` lays out every file it downloads, so
    # refusing symlinks outright would refuse every normal ingestion.
    blob = cache_root / "blobs" / "abc123"
    blob.parent.mkdir(parents=True)
    blob.write_text("bytes", encoding="utf-8")
    snapshot = cache_root / "snapshots" / "sha" / "config.json"
    snapshot.parent.mkdir(parents=True)
    snapshot.symlink_to(blob)

    assert source_problems(snapshot, cache_root=cache_root) == []


def test_a_link_that_escapes_the_cache_root_is_hfsyn004(cache_root, tmp_path: Path):
    outside = tmp_path / "outside"
    outside.write_text("not ours", encoding="utf-8")
    escaping = cache_root / "escaping"
    escaping.symlink_to(outside)

    problems = source_problems(escaping, cache_root=cache_root)

    assert codes(problems) == ["HFSYN004"]
    assert "outside the approved cache root" in problems[0].message


def test_a_path_outside_the_cache_root_is_hfsyn004(cache_root, tmp_path: Path):
    outside = tmp_path / "outside"
    outside.write_text("not ours", encoding="utf-8")

    assert codes(source_problems(outside, cache_root=cache_root)) == ["HFSYN004"]


def test_a_dangling_link_is_hfsyn004(cache_root):
    dangling = cache_root / "dangling"
    dangling.symlink_to(cache_root / "never-existed")

    problems = source_problems(dangling, cache_root=cache_root)

    assert codes(problems) == ["HFSYN004"]
    assert "dangling" in problems[0].message


def test_a_source_that_is_not_there_is_hfsyn004(cache_root):
    assert codes(source_problems(cache_root / "absent", cache_root=cache_root)) == ["HFSYN004"]


def test_a_directory_is_not_a_publishable_source(cache_root):
    directory = cache_root / "blobs"
    directory.mkdir()

    problems = source_problems(directory, cache_root=cache_root)

    assert codes(problems) == ["HFSYN004"]
    assert "not a regular file" in problems[0].message


def test_a_fifo_is_not_a_publishable_source(cache_root):
    fifo = cache_root / "fifo"
    os.mkfifo(fifo)

    assert codes(source_problems(fifo, cache_root=cache_root)) == ["HFSYN004"]


def test_escaping_and_non_regular_are_both_reported(cache_root, tmp_path: Path):
    outside = tmp_path / "outside"
    outside.mkdir()
    escaping = cache_root / "escaping"
    escaping.symlink_to(outside)

    assert codes(source_problems(escaping, cache_root=cache_root)) == ["HFSYN004", "HFSYN004"]


# --------------------------------------------------------------------------- #
# Destinations (`T-02`)
# --------------------------------------------------------------------------- #


def test_a_repository_path_lands_under_the_staging_tree(layout, transaction):
    paths = create_staging(layout, transaction)

    assert staged_path(paths, "config.json") == paths.tree / "config.json"
    assert staged_path(paths, "nested/dir/model.safetensors").is_relative_to(paths.tree)


@pytest.mark.parametrize(
    "relative",
    [
        "/etc/passwd",
        "../escape",
        "nested/../../escape",
        "a\\..\\..\\b",
        "",
        "trailing/",
    ],
)
def test_a_path_that_could_escape_is_refused_before_the_join(layout, transaction, relative):
    paths = create_staging(layout, transaction)

    with pytest.raises(ValueError, match="relative path"):
        staged_path(paths, relative)


def test_a_destination_parent_is_created_at_the_published_mode(layout, transaction):
    paths = create_staging(layout, transaction)
    target = staged_path(paths, "nested/deep/model.safetensors")

    prepare_staged_parent(target)

    assert target.parent.is_dir()
    assert stat.S_IMODE(target.parent.stat().st_mode) == PUBLISHED_DIRECTORY_MODE


def test_preparing_a_parent_twice_is_not_an_error(layout, transaction):
    paths = create_staging(layout, transaction)
    target = staged_path(paths, "nested/a.bin")

    prepare_staged_parent(target)
    prepare_staged_parent(target)


def test_a_destination_parent_that_cannot_be_created_is_hfsyn005(layout, transaction):
    paths = create_staging(layout, transaction)
    paths.tree.chmod(0o500)
    try:
        with pytest.raises(SynchronizationError) as caught:
            prepare_staged_parent(staged_path(paths, "nested/a.bin"))
    finally:
        paths.tree.chmod(PUBLISHED_DIRECTORY_MODE)

    assert codes(caught.value.problems) == ["HFSYN005"]


# --------------------------------------------------------------------------- #
# FS-10: both targets exist before the reference names them
# --------------------------------------------------------------------------- #


def test_a_reference_whose_targets_exist_has_no_problems(layout, published):
    assert reference_target_problems(layout, published) == []


def test_a_missing_tree_is_hfsyn007(layout, published):
    (layout.published / str(published.tree)).rmdir()

    problems = reference_target_problems(layout, published)

    assert codes(problems) == ["HFSYN007"]
    assert "FS-10" in problems[0].message


def test_a_missing_manifest_is_hfsyn007(layout, published):
    (layout.published / str(published.manifest)).unlink()

    assert codes(reference_target_problems(layout, published)) == ["HFSYN007"]


def test_both_missing_targets_are_reported_at_once(layout, reference):
    # An operator reconstructing an interrupted publication should learn
    # everything that is not there, not the first thing.
    assert codes(reference_target_problems(layout, reference)) == ["HFSYN007", "HFSYN007"]


def test_a_tree_that_is_a_file_is_not_a_publication_instance(layout, published):
    tree = layout.published / str(published.tree)
    tree.rmdir()
    tree.write_text("", encoding="utf-8")

    assert codes(reference_target_problems(layout, published)) == ["HFSYN007"]


def test_a_manifest_that_is_a_directory_is_refused(layout, published):
    manifest = layout.published / str(published.manifest)
    manifest.unlink()
    manifest.mkdir()

    assert codes(reference_target_problems(layout, published)) == ["HFSYN007"]


def test_a_field_that_tries_to_escape_published_is_refused(layout, published):
    # `FS-09`: the field is resolved under `published/`, and the grammar is what
    # establishes containment rather than a check after the join.
    escaping = published.model_copy(update={"tree": "../../etc/passwd"})

    problems = reference_target_problems(layout, escaping)

    assert codes(problems) == ["HFSYN007"]
    assert "tree=" in str(problems[0].location)


# --------------------------------------------------------------------------- #
# Publishing
# --------------------------------------------------------------------------- #


def test_the_per_sha_reference_lands_where_a_consumer_looks_for_it(layout, published):
    path = publish_revision_reference(layout, published)

    assert path == layout.repository(published.identity).revision_ref(published.commit_sha)
    assert read_reference(layout, path) == published


def test_the_current_reference_lands_where_a_consumer_looks_for_it(layout, published):
    path = publish_current_reference(layout, published)

    assert path.name == "current.json"
    assert read_reference(layout, path) == published


def test_a_reference_is_readable_by_the_export_identity_and_writable_by_nobody(layout, published):
    path = publish_revision_reference(layout, published)

    assert stat.S_IMODE(path.stat().st_mode) == PUBLISHED_FILE_MODE


def test_the_umask_does_not_reach_a_published_reference(layout, published):
    original = os.umask(0o077)
    try:
        path = publish_current_reference(layout, published)
    finally:
        os.umask(original)

    assert stat.S_IMODE(path.stat().st_mode) == PUBLISHED_FILE_MODE


def test_publishing_replaces_a_reference_rather_than_editing_it(layout, published):
    first = publish_current_reference(layout, published)
    moved = published.model_copy(update={"publication_generation": 2})

    publish_current_reference(layout, moved)

    assert read_reference(layout, first).publication_generation == 2
    assert [path.name for path in first.parent.iterdir()] == ["current.json"], (
        "no temporary survives the replacement"
    )


def test_publishing_refuses_a_reference_whose_targets_are_not_there(layout, reference):
    with pytest.raises(SynchronizationError) as caught:
        publish_revision_reference(layout, reference)

    assert codes(caught.value.problems) == ["HFSYN007", "HFSYN007"]
    assert caught.value.exit_code == ExitCode.SYNC
    assert not layout.repository(reference.identity).refs.exists(), "nothing was created"


def test_a_reference_directory_that_cannot_be_created_is_hfsyn007(layout, published):
    directory = layout.repository(published.identity).directory
    directory.chmod(0o500)
    try:
        with pytest.raises(SynchronizationError) as caught:
            publish_revision_reference(layout, published)
    finally:
        directory.chmod(0o2750)

    assert codes(caught.value.problems) == ["HFSYN007"]


def test_a_reference_that_cannot_be_written_is_hfsyn007(layout, published):
    repository = layout.repository(published.identity)
    repository.refs.mkdir(parents=True)
    repository.refs.chmod(0o500)
    try:
        # `write_model` raises `SafetyError`, because a filesystem that refuses a
        # durable write is a storage failure whatever was being written; the code
        # is the caller's and stays `HFSYN007`.
        with pytest.raises(SafetyError) as caught:
            publish_current_reference(layout, published)
    finally:
        repository.refs.chmod(0o2750)

    assert codes(caught.value.problems) == ["HFSYN007"]


# --------------------------------------------------------------------------- #
# Reading one back
# --------------------------------------------------------------------------- #


def test_an_absent_reference_is_hfver008(layout):
    # Reading happens while something is being checked, so an unusable reference
    # is an integrity finding about the archive rather than a failure of the run.
    with pytest.raises(IntegrityError) as caught:
        read_reference(layout, layout.published / "repos" / "absent.json")

    assert codes(caught.value.problems) == ["HFVER008"]
    assert caught.value.exit_code == ExitCode.INTEGRITY


def test_a_malformed_reference_is_hfver008(layout, published):
    path = publish_current_reference(layout, published)
    path.write_text("{ not json", encoding="utf-8")

    with pytest.raises(IntegrityError) as caught:
        read_reference(layout, path)

    assert codes(caught.value.problems) == ["HFVER008"]


def test_a_reference_from_a_newer_release_is_refused_rather_than_read(layout, published):
    path = publish_current_reference(layout, published)
    path.write_text(
        path.read_text(encoding="utf-8").replace('"schema_version": 1', '"schema_version": 2'),
        encoding="utf-8",
    )

    with pytest.raises(IntegrityError) as caught:
        read_reference(layout, path)

    assert "newer" in caught.value.problems[0].message


def test_a_reference_reports_its_location_archive_relative(layout, published):
    path = publish_current_reference(layout, published)
    path.write_text("{ not json", encoding="utf-8")

    with pytest.raises(IntegrityError) as caught:
        read_reference(layout, path)

    assert str(caught.value.problems[0].location).startswith("published/repos/")
