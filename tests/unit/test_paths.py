"""The archive layout and path containment (`docs/architecture.md` §5.1, §5.3).

The layout assertions use the exact identifiers from the worked examples in
`docs/schemas.md`, so a drift between this module and the published contract
fails here rather than being discovered by a consumer.

The containment assertions are property-based, as `docs/security.md` §"Path
escapes are rejected" requires: every generated adversarial path must either be
refused or resolve to a location under the root, with no third outcome.
"""

import os
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath

import pytest
from hypothesis import given
from hypothesis import strategies as st

from hfcache.errors import CodedError
from hfcache.identity import (
    RepositoryIdentity,
    new_probe_id,
    new_run_id,
    parse_commit_sha,
    parse_probe_id,
    parse_publication_id,
    parse_run_id,
    parse_transaction_id,
)
from hfcache.paths import (
    MAXIMUM_COMPONENT_BYTES,
    MAXIMUM_RELATIVE_PATH_BYTES,
    ArchiveLayout,
    collision_key,
    find_path_collisions,
    parse_archive_relative,
    parse_repository_relative,
    resolve_within,
)

ROOT = Path("/srv/hfcache")

# Built through the parsers rather than written as bare strings, because that is
# the only way to obtain the identifier types the layout accepts — and it is how
# every caller outside this file is expected to get one. The values themselves
# are the ones used in the worked examples in `docs/schemas.md`.
SHA = parse_commit_sha("0123456789abcdef0123456789abcdef01234567")
PUBLICATION = parse_publication_id("9f14c0b7a2d4423fa0e6b1c8d95e3f27")
TRANSACTION = parse_transaction_id("e5f60718293a4b5c6d7e8f90a1b2c3d4")
RUN = parse_run_id("4c1e8a55b0d24f1e9a3c7d2b6f80e114")
PROBE = parse_probe_id("0123456789abcdef")


@pytest.fixture
def layout() -> ArchiveLayout:
    return ArchiveLayout(root=ROOT)


@pytest.fixture
def repository(layout: ArchiveLayout):
    return layout.repository(RepositoryIdentity.of("model", "organization/model-name"))


# --------------------------------------------------------------------------- #
# The tree in §5.1, path by path
# --------------------------------------------------------------------------- #


def test_top_level_layout(layout: ArchiveLayout):
    assert layout.sentinel == ROOT / ".hfcache-root"
    assert layout.store == ROOT / ".store"
    assert layout.hub_cache == ROOT / ".store/hub"
    assert layout.health == ROOT / ".store/health"
    assert layout.quarantine == ROOT / ".store/quarantine"
    assert layout.repair_caches == ROOT / ".store/repair"
    assert layout.staging == ROOT / ".store/staging"
    assert layout.transactions == ROOT / ".store/transactions"
    assert layout.trash == ROOT / ".store/trash"
    assert layout.published == ROOT / "published"
    assert layout.repos == ROOT / "published/repos"
    assert layout.manifests == ROOT / "published/manifests"
    assert layout.catalog == ROOT / "published/catalog"
    assert layout.repositories_catalog == ROOT / "published/catalog/repositories.json"
    assert layout.verification_catalog == ROOT / "published/catalog/verification.json"
    assert layout.audit == ROOT / "audit"
    assert layout.pruned_audit == ROOT / "audit/pruned"
    assert layout.repair_audit == ROOT / "audit/repairs"
    assert layout.runs == ROOT / "runs"


def test_transaction_scoped_layout(layout: ArchiveLayout):
    assert layout.journal(TRANSACTION) == ROOT / f".store/transactions/{TRANSACTION}.json"

    staging = layout.staging_for(TRANSACTION)
    assert staging.directory == ROOT / f".store/staging/{TRANSACTION}"
    assert staging.tree == ROOT / f".store/staging/{TRANSACTION}/tree"
    assert staging.manifest == ROOT / f".store/staging/{TRANSACTION}/manifest.json"

    trash = layout.trash_for(TRANSACTION)
    assert trash.directory == ROOT / f".store/trash/{TRANSACTION}"
    assert trash.tree == ROOT / f".store/trash/{TRANSACTION}/tree"
    assert trash.manifest == ROOT / f".store/trash/{TRANSACTION}/manifest.json"

    assert layout.quarantine_for(TRANSACTION) == ROOT / f".store/quarantine/{TRANSACTION}"
    assert layout.repair_cache_for(TRANSACTION) == ROOT / f".store/repair/{TRANSACTION}/hub"
    assert layout.probe(PROBE) == ROOT / f".store/health/probe-{PROBE}"


def test_a_tombstone_mirrors_the_staging_shape(layout: ArchiveLayout):
    # Recovery reads a tombstone back with the layout it was written with, so
    # the two areas must not drift apart (`docs/architecture.md` §7.4).
    staging = layout.staging_for(TRANSACTION)
    trash = layout.trash_for(TRANSACTION)

    assert staging.tree.relative_to(staging.directory) == trash.tree.relative_to(trash.directory)
    assert staging.manifest.name == trash.manifest.name


def test_repository_layout(repository):
    base = ROOT / "published/repos/models/organization/model-name"

    assert repository.directory == base
    assert repository.refs == base / "refs"
    assert repository.current_ref == base / "refs/current.json"
    assert repository.revision_ref(SHA) == base / f"refs/revisions/{SHA}.json"
    assert repository.revisions == base / "revisions"
    assert repository.revision(SHA) == base / f"revisions/{SHA}"
    assert repository.instance(SHA, PUBLICATION) == base / f"revisions/{SHA}/{PUBLICATION}"


def test_manifest_layout(repository):
    base = ROOT / "published/manifests/models/organization/model-name"

    assert repository.manifests == base
    assert repository.revision_manifests(SHA) == base / SHA
    assert repository.manifest(SHA, PUBLICATION) == base / SHA / f"{PUBLICATION}.json"


def test_audit_layout(repository):
    pruned = ROOT / "audit/pruned/models/organization/model-name" / SHA
    repairs = ROOT / "audit/repairs/models/organization/model-name" / SHA

    assert repository.pruned_records(SHA) == pruned
    assert repository.pruned_manifest(SHA, PUBLICATION) == pruned / f"{PUBLICATION}.manifest.json"
    assert repository.prune_record(SHA, PUBLICATION) == pruned / f"{PUBLICATION}.prune.json"
    assert repository.repair_records(SHA) == repairs
    assert repository.retired_manifest(SHA, PUBLICATION) == repairs / f"{PUBLICATION}.manifest.json"
    assert (
        repository.retirement_record(SHA, PUBLICATION) == repairs / f"{PUBLICATION}.retirement.json"
    )


def test_a_dataset_uses_the_plural_directory(layout: ArchiveLayout):
    dataset = layout.repository(RepositoryIdentity.of("dataset", "organization/set"))

    assert dataset.directory == ROOT / "published/repos/datasets/organization/set"


# --------------------------------------------------------------------------- #
# Conformance with the published examples
# --------------------------------------------------------------------------- #


def test_reference_fields_match_the_documented_example(repository):
    # `docs/schemas.md` §4.1, verbatim. These two fields are relative to
    # `published/` because that is the directory a consumer mounts.
    assert str(repository.tree_reference(SHA, PUBLICATION)) == (
        f"repos/models/organization/model-name/revisions/{SHA}/{PUBLICATION}"
    )
    assert str(repository.manifest_reference(SHA, PUBLICATION)) == (
        f"manifests/models/organization/model-name/{SHA}/{PUBLICATION}.json"
    )


def test_the_manifest_tree_field_is_archive_relative(repository):
    # `docs/schemas.md` §3.1. A manifest lives beside the archive, not beside
    # the consumer, so its `tree` keeps the `published/` prefix a reference drops.
    assert str(repository.manifest_tree_field(SHA, PUBLICATION)) == (
        f"published/repos/models/organization/model-name/revisions/{SHA}/{PUBLICATION}"
    )


def test_the_run_report_name_matches_the_documented_example(layout: ArchiveLayout):
    started_at = datetime(2026, 7, 24, 20, 59, 31, 123456, tzinfo=UTC)

    report = layout.run_report(started_at, RUN)

    assert layout.archive_relative(report) == PurePosixPath(f"runs/20260724T205931Z-{RUN}.json")


def test_a_run_report_timestamp_is_converted_to_utc(layout: ArchiveLayout):
    eastern = datetime.fromisoformat("2026-07-24T16:59:31-04:00")

    assert layout.run_report(eastern, RUN).name.startswith("20260724T205931Z-")


def test_a_naive_run_report_timestamp_is_refused(layout: ArchiveLayout):
    with pytest.raises(ValueError, match="timezone-aware"):
        layout.run_report(datetime(2026, 7, 24, 20, 59, 31), RUN)  # noqa: DTZ001


def test_minted_identifiers_are_usable_as_path_segments(layout: ArchiveLayout):
    assert layout.probe(new_probe_id()).parent == layout.health
    assert layout.run_report(datetime.now(UTC), new_run_id()).parent == layout.runs


# --------------------------------------------------------------------------- #
# The root itself
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("root", ["srv/hfcache", "./srv", ""])
def test_a_relative_archive_root_is_refused(root):
    with pytest.raises(ValueError, match="absolute"):
        ArchiveLayout(root=Path(root))


@pytest.mark.parametrize("root", ["/srv/../etc", "/../srv"])
def test_an_unnormalized_archive_root_is_refused(root):
    with pytest.raises(ValueError, match="normalized"):
        ArchiveLayout(root=Path(root))


def test_a_dot_component_in_the_root_is_already_gone():
    # `Path` drops `.` as it parses, so there is nothing left to refuse and the
    # derived paths are the same either way.
    assert ArchiveLayout(root=Path("/srv/./hfcache")).root == ROOT


def test_required_directories_are_ordered_parents_first(layout: ArchiveLayout):
    specs = layout.required_directories()
    created: set[Path] = {layout.root}

    for spec in specs:
        assert spec.path.parent in created, f"{spec.path} precedes its parent"
        created.add(spec.path)

    assert layout.sentinel not in {spec.path for spec in specs}, "the sentinel is written last"


def test_required_directory_modes_follow_the_ownership_table(layout: ArchiveLayout):
    modes = {spec.path: spec.mode for spec in layout.required_directories()}

    assert modes[layout.store] == 0o700
    assert modes[layout.audit] == 0o700
    assert modes[layout.runs] == 0o700
    assert modes[layout.published] == 0o2750
    assert modes[layout.repos] == 0o2750
    assert modes[layout.catalog] == 0o2750


# --------------------------------------------------------------------------- #
# Identifiers that would become path segments
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "value",
    ["..", ".", "/etc/passwd", "../../etc", "", "0123456789ABCDEF0123456789abcdef01234567", 7],
)
def test_an_unsafe_sha_cannot_reach_a_path(repository, value):
    # Unreachable through the type system; the guard exists for the case where
    # a NewType, which is a no-op at run time, is bypassed.
    with pytest.raises(ValueError, match="commit SHA"):
        repository.instance(value, PUBLICATION)


def test_an_unsafe_publication_id_cannot_reach_a_path(repository):
    with pytest.raises(ValueError, match="publication id"):
        repository.instance(SHA, "../../../etc")


@pytest.mark.parametrize(
    "method", ["journal", "quarantine_for", "repair_cache_for", "staging_for", "trash_for"]
)
def test_an_unsafe_transaction_id_cannot_reach_a_path(layout: ArchiveLayout, method):
    with pytest.raises(ValueError, match="transaction id"):
        getattr(layout, method)("..")


def test_an_unsafe_probe_id_cannot_reach_a_path(layout: ArchiveLayout):
    with pytest.raises(ValueError, match="probe id"):
        # pyrefly: ignore[bad-argument-type]
        # Bypassing the type is the point: a NewType is a no-op at run time, so
        # the run-time guard has to hold on its own.
        layout.probe("../../etc")


def test_an_unsafe_run_id_cannot_reach_a_path(layout: ArchiveLayout):
    with pytest.raises(ValueError, match="run id"):
        # pyrefly: ignore[bad-argument-type]
        layout.run_report(datetime.now(UTC), "..")


# --------------------------------------------------------------------------- #
# Relative-path grammar
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "value",
    [
        "config.json",
        "model-00001-of-00002.safetensors",
        "subdir/nested/file.bin",
        ".gitattributes",
        "a" * MAXIMUM_COMPONENT_BYTES,
        "naïve/файл.txt",
        "dir/.hidden",
        "trailing.dot.",
        "with space.txt",
    ],
)
def test_valid_repository_relative_paths_are_accepted(value):
    assert parse_repository_relative(value, code="HFSYN004") == PurePosixPath(value)


@pytest.mark.parametrize(
    "value",
    [
        "/absolute",
        "../escape",
        "a/../../escape",
        "a/..",
        "./here",
        "a/./b",
        "a//b",
        "trailing/",
        "",
        "nul\x00byte",
        "carriage\rreturn",
        "new\nline",
        "tab\tseparated",
        "back\\slash",
        "windows\\..\\..\\escape",
        "a" * (MAXIMUM_COMPONENT_BYTES + 1),
        "a/" * 600,
        7,
        None,
        PurePosixPath("already/a/path"),
    ],
)
def test_unsafe_repository_relative_paths_are_refused(value):
    with pytest.raises(CodedError):
        parse_repository_relative(value, code="HFSYN004")


def test_a_multibyte_component_is_measured_in_bytes():
    # 128 two-byte characters is 256 bytes: one over NAME_MAX, even though it is
    # only 128 characters long.
    with pytest.raises(CodedError, match="exceeds"):
        parse_repository_relative("é" * 128, code="HFSYN004")


def test_an_overlong_path_is_measured_in_bytes():
    value = "a/" * (MAXIMUM_RELATIVE_PATH_BYTES // 2) + "a"

    with pytest.raises(CodedError, match="longer than"):
        parse_repository_relative(value, code="HFSYN004")


def test_the_caller_chooses_the_code():
    for code in ("HFSYN004", "HFVER007", "HFTXN003"):
        with pytest.raises(CodedError) as raised:
            parse_archive_relative("../escape", code=code)
        assert raised.value.code == code


def test_a_rejection_message_does_not_echo_a_control_character():
    # The message names the shape of the problem. Echoing the value would put a
    # NUL or an escape sequence into a log line.
    with pytest.raises(CodedError) as raised:
        parse_repository_relative("a\x1b[2Jb", code="HFSYN004")

    assert "\x1b" not in str(raised.value)


def test_archive_relative_accepts_what_the_layout_produces(layout: ArchiveLayout, repository):
    produced = [
        layout.archive_relative(repository.instance(SHA, PUBLICATION)),
        layout.archive_relative(repository.manifest(SHA, PUBLICATION)),
        layout.archive_relative(layout.journal(TRANSACTION)),
        repository.tree_reference(SHA, PUBLICATION),
        repository.manifest_reference(SHA, PUBLICATION),
    ]

    for value in produced:
        assert parse_archive_relative(str(value), code="HFTXN003") == value


# --------------------------------------------------------------------------- #
# Containment
# --------------------------------------------------------------------------- #


def test_resolve_joins_onto_the_archive_root(layout: ArchiveLayout):
    resolved = layout.resolve("published/catalog/repositories.json", code="HFTXN003")

    assert resolved == layout.repositories_catalog


def test_resolve_published_joins_onto_the_consumer_root(layout: ArchiveLayout, repository):
    reference = repository.tree_reference(SHA, PUBLICATION)

    assert layout.resolve_published(str(reference), code="HFVER008") == repository.instance(
        SHA, PUBLICATION
    )


def test_a_reference_that_escapes_is_refused(layout: ArchiveLayout):
    with pytest.raises(CodedError):
        layout.resolve_published("../.store/hub/anything", code="HFVER008")


def test_a_relative_containment_root_is_refused():
    with pytest.raises(ValueError, match="absolute"):
        resolve_within(Path("relative"), "file", code="HFSYN004")


def test_archive_relative_refuses_a_path_outside_the_root(layout: ArchiveLayout):
    with pytest.raises(ValueError, match="not inside the archive root"):
        layout.archive_relative(Path("/etc/passwd"))


def test_published_relative_refuses_a_path_outside_published(layout: ArchiveLayout):
    with pytest.raises(ValueError, match="not inside the published root"):
        layout.published_relative(layout.hub_cache)


adversarial_characters = st.sampled_from(
    ["a", "b", "/", ".", "..", "\\", " ", "\x00", "\n", "é", "-", "~", "%2e", "C:"]
)
adversarial_paths = st.lists(adversarial_characters, min_size=0, max_size=12).map("".join)


@given(value=adversarial_paths)
def test_an_accepted_path_can_never_leave_the_root(value):
    root = Path("/srv/hfcache")
    try:
        resolved = resolve_within(root, value, code="HFSYN004")
    except CodedError:
        return

    assert resolved.is_relative_to(root)
    assert ".." not in resolved.parts
    # Normalization is a no-op on an accepted path, so there is no second
    # spelling of it that resolves somewhere else.
    assert os.path.normpath(resolved) == str(resolved)


@given(value=adversarial_paths)
def test_acceptance_is_the_same_decision_for_every_root(value):
    shallow = Path("/srv")
    deep = Path("/srv/hfcache/published/repos/models/organization/model-name")

    def accepts(root: Path) -> bool:
        try:
            resolve_within(root, value, code="HFSYN004")
        except CodedError:
            return False
        return True

    assert accepts(shallow) == accepts(deep)


# --------------------------------------------------------------------------- #
# Collisions (`docs/security.md` T-02)
# --------------------------------------------------------------------------- #


def test_case_variants_collide():
    assert collision_key("README.md") == collision_key("readme.md")


def test_unicode_normalization_variants_collide():
    composed = "café.txt"
    decomposed = "café.txt"

    assert composed != decomposed
    assert collision_key(composed) == collision_key(decomposed)


def test_full_case_folding_is_stricter_than_any_one_filesystem():
    # `str.casefold` also folds ligatures, so this pair is reported as a
    # collision even though nothing would really merge the two files. Refusing
    # is the recoverable direction; silently merging them is not.
    assert collision_key("ﬁle.txt") == collision_key("file.txt")


def test_nfkc_folding_is_not_applied():
    # NFKC would fold these together. Nothing plausible confuses them, so
    # applying it would refuse legitimate names for no gain.
    assert collision_key("model².bin") != collision_key("model2.bin")


def test_distinct_paths_do_not_collide():
    assert not find_path_collisions(["a.txt", "b.txt", "dir/a.txt"])


def test_collisions_are_reported_with_every_spelling():
    collisions = find_path_collisions(["README.md", "readme.md", "other.txt", "Readme.md"])

    assert collisions == (("readme.md", ("README.md", "Readme.md", "readme.md")),)


def test_a_repeated_spelling_is_a_collision():
    # A manifest listing the same path twice is equally unpublishable.
    assert find_path_collisions(["a.txt", "a.txt"]) == (("a.txt", ("a.txt", "a.txt")),)


def test_collision_groups_are_deterministic():
    values = ["B.txt", "b.txt", "A.txt", "a.txt"]

    assert find_path_collisions(values) == find_path_collisions(reversed(values))
    assert [key for key, _ in find_path_collisions(values)] == ["a.txt", "b.txt"]


def test_collision_keys_accept_pure_paths():
    assert collision_key(PurePosixPath("Dir/File.TXT")) == "dir/file.txt"


@given(
    names=st.lists(
        st.sampled_from(["a.txt", "A.txt", "café", "café", "b/c", "B/C"]),
        min_size=2,
        max_size=6,
    )
)
def test_every_reported_group_really_collides(names):
    for key, spellings in find_path_collisions(names):
        assert len(spellings) > 1
        assert {collision_key(spelling) for spelling in spellings} == {key}
