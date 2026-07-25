"""Writing the references a consumer reads, and refusing to write a broken one.

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
from hfcache.paths import ArchiveLayout
from hfcache.publication import (
    PUBLISHED_FILE_MODE,
    publish_current_reference,
    publish_revision_reference,
    read_reference,
    reference_target_problems,
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
