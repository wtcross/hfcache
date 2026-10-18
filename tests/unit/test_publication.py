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

import hashlib
import os
import stat
from pathlib import Path
from typing import TYPE_CHECKING, Literal

import pytest

from hfcache.archive import initialize_archive
from hfcache.errors import ExitCode, IntegrityError, SynchronizationError
from hfcache.hashing import FileDigest, ObjectIdentity, sha256_file
from hfcache.identity import TransactionId, new_transaction_id
from hfcache.paths import ArchiveLayout
from hfcache.publication import (
    PUBLISHED_DIRECTORY_MODE,
    PUBLISHED_FILE_MODE,
    STAGING_MODE,
    create_staging,
    discard_staging,
    prepare_staged_parent,
    projected_publication_bytes,
    promote_staging,
    publish_current_reference,
    publish_revision_reference,
    read_reference,
    reference_target_problems,
    source_problems,
    stage_file,
    staged_path,
)
from hfcache.storage import parse_mount_table
from tests.fixtures import examples

if TYPE_CHECKING:
    from hfcache.models import Reference

ARCHIVE_ID = "3f2a1c88-7b40-4a2e-9c1d-0e5b6a7f8d90"


def nfs_line(mount_point: str) -> str:
    return (
        f"457 47 0:68 / {mount_point} rw,nosuid,nodev,relatime shared:488 "
        f"- nfs4 nas.lab.example.com:/mnt/tank/hf rw,vers=4.2"
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
# What a publication costs (docs/cli.md doctor contract)
# --------------------------------------------------------------------------- #


def test_hardlink_publication_costs_nothing_beyond_metadata():
    # The whole reason `publication_mode` is an explicit choice (`AD-11`): the
    # blobs are already on the dataset, and a hardlink adds a directory entry.
    assert projected_publication_bytes(10 * 1024**3, publication_mode="hardlink") == 0


def test_copy_publication_costs_a_second_copy_of_every_byte():
    assert projected_publication_bytes(10 * 1024**3, publication_mode="copy") == 10 * 1024**3


# --------------------------------------------------------------------------- #
# Staging one file (docs/architecture.md publication contract, the explicit copy contract)
# --------------------------------------------------------------------------- #

PAYLOAD = b"the bytes of one repository file\n"


def _stage_file(
    source: Path,
    destination: Path,
    *,
    publication_mode: Literal["hardlink", "copy"],
    cache_root: Path,
) -> FileDigest:
    """Stage with the transient evidence a real ingestion hash supplies."""
    return stage_file(
        source,
        destination,
        publication_mode=publication_mode,
        cache_root=cache_root,
        expected=sha256_file(source),
        expected_identity=ObjectIdentity.of(source),
    )


@pytest.fixture
def cached(cache_root) -> Path:
    """A blob reached through a snapshot symlink, the way the Hub cache lays it out."""
    blob = cache_root / "blobs" / "abcdef"
    blob.parent.mkdir(parents=True)
    blob.write_bytes(PAYLOAD)
    snapshot = cache_root / "snapshots" / "sha" / "model.safetensors"
    snapshot.parent.mkdir(parents=True)
    snapshot.symlink_to(blob)
    return snapshot


@pytest.mark.parametrize("mode", ["hardlink", "copy"])
def test_a_staged_file_holds_the_bytes_it_came_from(layout, transaction, cached, cache_root, mode):
    paths = create_staging(layout, transaction)
    destination = staged_path(paths, "model.safetensors")

    digest = _stage_file(cached, destination, publication_mode=mode, cache_root=cache_root)

    assert destination.read_bytes() == PAYLOAD
    assert digest.size == len(PAYLOAD)
    assert digest.digest == hashlib.sha256(PAYLOAD).hexdigest()


def test_hardlink_mode_publishes_the_same_inode(layout, transaction, cached, cache_root):
    # `AD-11`: the whole point is that a published revision does not double the
    # bytes its cache blob already occupies.
    paths = create_staging(layout, transaction)
    destination = staged_path(paths, "model.safetensors")

    _stage_file(cached, destination, publication_mode="hardlink", cache_root=cache_root)

    assert destination.stat().st_ino == cached.resolve().stat().st_ino
    assert destination.stat().st_nlink == 2


def test_hardlink_staging_does_not_hash_the_same_inode_again(
    layout, transaction, cached, cache_root, monkeypatch: pytest.MonkeyPatch
):
    paths = create_staging(layout, transaction)
    destination = staged_path(paths, "model.safetensors")
    expected = sha256_file(cached)
    expected_identity = ObjectIdentity.of(cached)

    def unexpected_hash(*args, **kwargs):
        message = "hardlink staging must carry the ingestion digest"
        raise AssertionError(message)

    monkeypatch.setattr("hfcache.publication.sha256_file", unexpected_hash)
    landed = stage_file(
        cached,
        destination,
        publication_mode="hardlink",
        cache_root=cache_root,
        expected=expected,
        expected_identity=expected_identity,
    )

    assert landed == expected
    assert destination.samefile(cached)


def test_a_source_replaced_after_hashing_is_never_hardlinked(
    layout, transaction, cached, cache_root
):
    paths = create_staging(layout, transaction)
    destination = staged_path(paths, "model.safetensors")
    expected = sha256_file(cached)
    expected_identity = ObjectIdentity.of(cached)
    replacement = cache_root / "blobs" / "replacement"
    replacement.write_bytes(b"x" * len(PAYLOAD))
    cached.unlink()
    cached.symlink_to(replacement)

    with pytest.raises(SynchronizationError) as caught:
        stage_file(
            cached,
            destination,
            publication_mode="hardlink",
            cache_root=cache_root,
            expected=expected,
            expected_identity=expected_identity,
        )

    assert codes(caught.value.problems) == ["HFSYN005"]
    assert not destination.exists()


def test_an_unproven_link_is_removed_after_the_link_call(
    layout,
    transaction,
    cached,
    cache_root,
    monkeypatch: pytest.MonkeyPatch,
):
    paths = create_staging(layout, transaction)
    destination = staged_path(paths, "model.safetensors")
    expected = sha256_file(cached)
    expected_identity = ObjectIdentity.of(cached)

    def copy_instead_of_link(source, landed, *, follow_symlinks):
        assert follow_symlinks is True
        Path(landed).write_bytes(Path(source).resolve().read_bytes())

    monkeypatch.setattr("hfcache.publication.os.link", copy_instead_of_link)
    with pytest.raises(SynchronizationError) as caught:
        stage_file(
            cached,
            destination,
            publication_mode="hardlink",
            cache_root=cache_root,
            expected=expected,
            expected_identity=expected_identity,
        )

    assert codes(caught.value.problems) == ["HFSYN005"]
    assert not destination.exists()


def test_copy_mode_publishes_a_separate_inode_and_never_a_symlink(
    layout, transaction, cached, cache_root
):
    paths = create_staging(layout, transaction)
    destination = staged_path(paths, "model.safetensors")

    _stage_file(cached, destination, publication_mode="copy", cache_root=cache_root)

    assert destination.stat().st_ino != cached.resolve().stat().st_ino
    assert not destination.is_symlink(), "a cache symlink is resolved, never reproduced"


@pytest.mark.parametrize("mode", ["hardlink", "copy"])
def test_staging_creates_the_parent_directories_it_needs(
    layout, transaction, cached, cache_root, mode
):
    paths = create_staging(layout, transaction)
    destination = staged_path(paths, "nested/deep/model.safetensors")

    _stage_file(cached, destination, publication_mode=mode, cache_root=cache_root)

    assert destination.is_file()


@pytest.mark.parametrize("mode", ["hardlink", "copy"])
def test_a_source_outside_the_cache_root_is_never_staged(
    layout, transaction, cache_root, tmp_path: Path, mode
):
    outside = tmp_path / "outside"
    outside.write_bytes(PAYLOAD)
    paths = create_staging(layout, transaction)
    destination = staged_path(paths, "model.safetensors")

    with pytest.raises(SynchronizationError) as caught:
        _stage_file(outside, destination, publication_mode=mode, cache_root=cache_root)

    assert codes(caught.value.problems) == ["HFSYN004"]
    assert not destination.exists()


def test_an_unavailable_hardlink_is_never_downgraded_to_a_copy(
    layout, transaction, cached, cache_root, monkeypatch: pytest.MonkeyPatch
):
    # `AD-11`: a mode is never silently downgraded. Failing here is what stops a
    # deployment from quietly consuming twice the planned space.
    def refuse(source, destination, *, follow_symlinks):
        assert follow_symlinks is True
        raise OSError(1, "Operation not permitted", str(destination))

    monkeypatch.setattr("hfcache.publication.os.link", refuse)
    paths = create_staging(layout, transaction)
    destination = staged_path(paths, "model.safetensors")

    with pytest.raises(SynchronizationError) as caught:
        _stage_file(cached, destination, publication_mode="hardlink", cache_root=cache_root)

    assert codes(caught.value.problems) == ["HFSYN005"]
    assert "AD-11" in caught.value.problems[0].message
    assert not destination.exists()


def test_a_copy_that_lost_bytes_is_never_published(
    layout, transaction, cached, cache_root, monkeypatch: pytest.MonkeyPatch
):
    # Copy mode exists for a deployment where hardlinks are unavailable, often a
    # different storage topology, so the copy is proven rather than assumed.
    def truncate(source, destination):
        Path(destination).write_bytes(PAYLOAD[:4])

    monkeypatch.setattr("hfcache.publication.shutil.copyfile", truncate)
    paths = create_staging(layout, transaction)
    destination = staged_path(paths, "model.safetensors")

    with pytest.raises(SynchronizationError) as caught:
        _stage_file(cached, destination, publication_mode="copy", cache_root=cache_root)

    assert codes(caught.value.problems) == ["HFSYN005"]
    assert "never published" in caught.value.problems[0].message


def test_a_copy_that_cannot_be_written_leaves_no_partial_file(
    layout, transaction, cached, cache_root, monkeypatch: pytest.MonkeyPatch
):
    def fail(source, destination):
        Path(destination).write_bytes(PAYLOAD[:4])
        raise OSError(28, "No space left on device", str(destination))

    monkeypatch.setattr("hfcache.publication.shutil.copyfile", fail)
    paths = create_staging(layout, transaction)
    destination = staged_path(paths, "model.safetensors")

    with pytest.raises(SynchronizationError) as caught:
        _stage_file(cached, destination, publication_mode="copy", cache_root=cache_root)

    assert codes(caught.value.problems) == ["HFSYN005"]
    assert list(destination.parent.iterdir()) == [], "no temporary survives the failure"


# --------------------------------------------------------------------------- #
# Promotion (docs/cli.md sync contract)
# --------------------------------------------------------------------------- #


def test_promotion_makes_the_revision_visible_in_one_step(layout, transaction, published):
    paths = create_staging(layout, transaction)
    (paths.tree / "model.safetensors").write_bytes(PAYLOAD)
    destination = layout.published / str(published.tree) / "promoted"

    promote_staging(layout, paths, destination)

    assert (destination / "model.safetensors").read_bytes() == PAYLOAD
    assert not paths.tree.exists(), "the staged tree moved rather than being copied"


def test_promotion_keeps_the_mode_the_tree_was_built_with(layout, transaction, published):
    paths = create_staging(layout, transaction)
    destination = layout.published / str(published.tree) / "promoted"

    promote_staging(layout, paths, destination)

    assert stat.S_IMODE(destination.stat().st_mode) == PUBLISHED_DIRECTORY_MODE


def test_promotion_never_replaces_an_existing_publication_instance(layout, transaction, published):
    # `FS-05`: an instance directory is immutable once renamed into place, and
    # `rename` onto an existing directory failing is what enforces it.
    paths = create_staging(layout, transaction)
    destination = layout.published / str(published.tree) / "promoted"
    destination.mkdir(parents=True)
    (destination / "already-there").write_text("x", encoding="utf-8")

    with pytest.raises(SynchronizationError) as caught:
        promote_staging(layout, paths, destination)

    assert codes(caught.value.problems) == ["HFSYN006"]
    assert (destination / "already-there").exists()


def test_an_empty_existing_destination_is_refused_too(layout, transaction, published):
    # `rename(2)` fails on a non-empty directory but happily replaces an empty
    # one, so the syscall alone would enforce `FS-05` for most publications and
    # break it for an instance directory a crash left empty.
    paths = create_staging(layout, transaction)
    destination = layout.published / str(published.tree) / "promoted"
    destination.mkdir(parents=True)

    with pytest.raises(SynchronizationError) as caught:
        promote_staging(layout, paths, destination)

    assert codes(caught.value.problems) == ["HFSYN006"]
    assert "FS-05" in caught.value.problems[0].message


def test_a_failed_promotion_says_the_previous_reference_is_unchanged(
    layout, transaction, published, monkeypatch: pytest.MonkeyPatch
):
    def refuse(self, target):
        raise OSError(30, "Read-only file system", str(target))

    monkeypatch.setattr(Path, "rename", refuse)
    paths = create_staging(layout, transaction)
    destination = layout.published / str(published.tree) / "promoted"

    with pytest.raises(SynchronizationError) as caught:
        promote_staging(layout, paths, destination)

    assert codes(caught.value.problems) == ["HFSYN006"]
    assert "previous reference is unchanged" in caught.value.problems[0].message


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
        # `SynchronizationError`, not `SafetyError`: the exit an error carries
        # comes from its class and the classification `docs/cli.md` §5 publishes
        # comes from the code's family, so `HFSYN007` has to arrive as a `30`
        # (decision 52). The mount checks passed — what failed is the run.
        with pytest.raises(SynchronizationError) as caught:
            publish_current_reference(layout, published)
    finally:
        repository.refs.chmod(0o2750)

    assert codes(caught.value.problems) == ["HFSYN007"]
    assert caught.value.exit_code == ExitCode.SYNC


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
