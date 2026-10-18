"""HTTP metadata work budgets and descriptor containment hold across shared reads."""

import os
from dataclasses import replace

import pytest

from hfcache.config import ApplicationConfig
from hfcache.errors import IntegrityError
from hfcache.identity import CommitSha, PublicationId
from hfcache.metadata import MetadataReader, QueryBounds, QueryLimitError
from hfcache.services.queries import LocalQueries, PublicationQuery, RepositoryQuery
from tests.fixtures import examples


@pytest.fixture
def queries(tmp_path):
    root = tmp_path / "archive"
    root.mkdir()
    config = ApplicationConfig.model_validate(
        {
            "schema_version": 1,
            "storage": {
                "archive_root": str(root),
                "archive_id": examples.ARCHIVE_ID,
            },
        }
    )
    queries = LocalQueries(config)
    reference = examples.reference()
    repository = queries.layout.repository(reference.identity)
    tree = repository.instance(CommitSha(examples.SHA), PublicationId(examples.PUBLICATION))
    tree.mkdir(parents=True)
    for path, model in (
        (repository.current_ref, reference),
        (repository.revision_ref(CommitSha(examples.SHA)), reference),
        (
            repository.manifest(CommitSha(examples.SHA), PublicationId(examples.PUBLICATION)),
            examples.manifest(),
        ),
        (queries.layout.verification_catalog, examples.verification_catalog()),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(model.to_json(), encoding="utf-8")
    return queries


@pytest.mark.parametrize(
    "method", ["archive_status", "list_repositories", "estimate_verification", "list_reports"]
)
def test_scan_budget_is_visible_instead_of_partial_or_empty_success(queries, method):
    queries.layout.runs.mkdir(parents=True, exist_ok=True)
    for number in range(3):
        (queries.layout.runs / f"unknown-{number}").touch()
    limited = replace(queries, bounds=QueryBounds(maximum_entries=1))
    with pytest.raises(QueryLimitError) as failure:
        getattr(limited, method)()
    assert failure.value.problems[0].code == "HFAPI005"


@pytest.mark.parametrize("method", ["archive_status", "list_repositories", "estimate_verification"])
def test_derived_catalog_budget_is_not_silently_treated_as_missing(queries, method):
    limited = replace(queries, bounds=QueryBounds(maximum_artifact_bytes=1))
    with pytest.raises(QueryLimitError):
        getattr(limited, method)()


def test_exact_reports_and_manifests_share_the_same_artifact_limit(queries):
    report = examples.run_report()
    path = queries.layout.run_report(report.started_at, report.run_id)
    path.parent.mkdir(parents=True)
    path.write_text(report.to_json(), encoding="utf-8")
    limited = replace(queries, bounds=QueryBounds(maximum_artifact_bytes=1))
    with pytest.raises(QueryLimitError):
        limited.read_report(report.run_id)
    request = PublicationQuery(
        examples.reference().identity, CommitSha(examples.SHA), PublicationId(examples.PUBLICATION)
    )
    with pytest.raises(QueryLimitError):
        limited.read_manifest(request)


def test_total_read_limit_applies_across_artifacts_and_open_file_growth(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.write_bytes(b"123")
    second.write_bytes(b"456")
    reader = MetadataReader(tmp_path, QueryBounds(maximum_total_bytes=5))
    assert reader.read(first) == b"123"
    with pytest.raises(QueryLimitError):
        reader.read(second)


@pytest.mark.parametrize("method", ["archive_status", "list_repositories", "estimate_verification"])
@pytest.mark.parametrize("component", ["namespace", "repository", "refs"])
def test_metadata_queries_refuse_symlink_components(queries, tmp_path, method, component):
    repository = queries.layout.repository(examples.reference().identity)
    paths = {
        "namespace": queries.layout.repos / "models" / "organization",
        "repository": repository.refs.parent,
        "refs": repository.refs,
    }
    original = paths[component]
    outside = tmp_path / "outside"
    original.rename(outside)
    original.symlink_to(outside, target_is_directory=True)
    if method == "archive_status" and component == "refs":
        row = queries.archive_status().data["repositories"][0]
        assert row["current_commit_sha"] is None
        assert row["verification_state"] == "unverified"
    elif method == "estimate_verification" and component == "refs":
        with pytest.raises(IntegrityError):
            queries.estimate_verification()
    else:
        with pytest.raises(IntegrityError):
            getattr(queries, method)()


def test_derived_catalog_symlink_never_supplies_verification_confidence(queries, tmp_path):
    catalog = queries.layout.verification_catalog
    outside = tmp_path / "external-catalog"
    catalog.rename(outside)
    catalog.symlink_to(outside)
    row = queries.list_repositories(RepositoryQuery(revisions=True)).data["repositories"][0]
    assert row["revisions"][0]["verification_state"] == "unverified"
    assert (
        queries.archive_status().data["archive"]["verification"]["last_full_verification"] is None
    )


def test_latest_run_status_checks_archive_and_filename_identity(queries):
    report = examples.run_report().model_copy(
        update={"archive_id": "00000000-0000-0000-0000-000000000001"}
    )
    path = queries.layout.run_report(report.started_at, report.run_id)
    path.parent.mkdir(parents=True)
    path.write_text(report.to_json(), encoding="utf-8")
    assert queries.archive_status().data["repositories"][0]["last_run_status"] is None


def test_missing_manifest_cannot_leave_a_verified_status_headline(queries):
    reference = examples.reference()
    repository = queries.layout.repository(reference.identity)
    repository.manifest(CommitSha(examples.SHA), PublicationId(examples.PUBLICATION)).unlink()
    row = queries.archive_status().data["repositories"][0]
    assert row["current_commit_sha"] == examples.SHA
    assert row["verification_state"] == "unverified"


def test_estimate_stats_artifacts_without_opening_them_for_content(queries, monkeypatch):
    repository = queries.layout.repository(examples.reference().identity)
    tree = repository.instance(CommitSha(examples.SHA), PublicationId(examples.PUBLICATION))
    for entry in examples.manifest().files:
        path = tree / str(entry.path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"123")
    original = os.open
    names = {str(entry.path).split("/")[-1] for entry in examples.manifest().files}
    seen = []

    def tracked(path, flags, *args, **kwargs):
        if str(path) in names:
            assert flags & os.O_PATH
            seen.append(path)
        return original(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", tracked)
    estimate = queries.estimate_verification().data
    assert seen
    assert estimate["unreadable_objects"] == 0
    assert estimate["unique_objects"] == len(examples.manifest().files)


def test_estimate_preserves_separate_broken_current_diagnostic(queries):
    repository = queries.layout.repository(examples.reference().identity)
    repository.current_ref.write_text("invalid", encoding="utf-8")
    assert queries.estimate_verification().data["revisions"] == 2


def test_parent_swap_between_scan_and_read_never_follows_external_target(tmp_path):
    root = tmp_path / "archive"
    directory = root / "metadata"
    directory.mkdir(parents=True)
    (directory / "record").write_bytes(b"original")
    reader = MetadataReader(root)
    entry = reader.entries(directory)[0]
    moved = tmp_path / "external"
    directory.rename(moved)
    directory.symlink_to(moved, target_is_directory=True)
    with pytest.raises(NotADirectoryError):
        reader.read(entry.path)
    assert (moved / "record").read_bytes() == b"original"


@pytest.mark.parametrize("current_damaged", [False, True])
def test_estimate_counts_a_damaged_retained_reference_once_unless_current_is_also_damaged(
    queries, current_damaged
):
    repository = queries.layout.repository(examples.reference().identity)
    repository.revision_ref(CommitSha(examples.SHA)).write_text("broken", encoding="utf-8")
    if current_damaged:
        repository.current_ref.write_text("broken", encoding="utf-8")
    assert queries.estimate_verification().data["revisions"] == 1 + int(current_damaged)


@pytest.mark.parametrize("current_changed", [False, True])
def test_estimate_keeps_manifest_damage_and_a_distinct_current_mismatch_separate(
    queries, current_changed
):
    reference = examples.reference()
    repository = queries.layout.repository(reference.identity)
    repository.manifest(CommitSha(examples.SHA), PublicationId(examples.PUBLICATION)).unlink()
    if current_changed:
        replacement = reference.model_copy(
            update={
                "publication_id": examples.REPLACEMENT,
                "tree": str(reference.tree).replace(examples.PUBLICATION, examples.REPLACEMENT),
                "manifest": str(reference.manifest).replace(
                    examples.PUBLICATION, examples.REPLACEMENT
                ),
            }
        )
        repository.current_ref.write_text(replacement.to_json(), encoding="utf-8")
    result = queries.estimate_verification()
    assert result.exit_code == 0
    assert result.data["revisions"] == 1 + int(current_changed)
