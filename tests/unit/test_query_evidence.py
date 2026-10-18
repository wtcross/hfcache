"""ID-based metadata reads pin identity and reject filesystem escapes (FS-09/FS-12)."""

import json
from datetime import timedelta
from typing import TYPE_CHECKING

import pytest

from hfcache.config import ApplicationConfig
from hfcache.errors import ConfigurationError, IntegrityError
from hfcache.identity import CommitSha, PublicationId, RepositoryIdentity
from hfcache.reporting import RecoveryReport
from hfcache.services.queries import LocalQueries, PublicationQuery
from tests.fixtures import examples

if TYPE_CHECKING:
    from pathlib import Path

    from hfcache.models import DurableModel


@pytest.fixture
def queries(tmp_path: Path) -> LocalQueries:
    root = tmp_path / "archive"
    root.mkdir()
    config = ApplicationConfig.model_validate(
        {
            "schema_version": 1,
            "storage": {"archive_root": str(root), "archive_id": examples.ARCHIVE_ID},
        }
    )
    return LocalQueries(config)


def _write(path: Path, model: DurableModel) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(model.to_json(), encoding="utf-8")
    return path


def _publication(queries: LocalQueries) -> PublicationQuery:
    identity = RepositoryIdentity.of("model", examples.REPOSITORY_ID)
    request = PublicationQuery(
        identity, CommitSha(examples.SHA), PublicationId(examples.PUBLICATION)
    )
    repository = queries.layout.repository(identity)
    repository.instance(request.commit_sha, request.publication_id).mkdir(parents=True)
    _write(repository.manifest(request.commit_sha, request.publication_id), examples.manifest())
    _write(repository.revision_ref(request.commit_sha), examples.reference())
    _write(repository.current_ref, examples.reference())
    return request


def _recovery_report() -> RecoveryReport:
    payload = examples.run_report().model_dump(mode="python")
    del payload["repositories"]
    del payload["totals"]
    return RecoveryReport.model_validate(payload | {"command": "recover --apply"})


@pytest.mark.parametrize(
    "builder", [examples.run_report, examples.verification_report, _recovery_report]
)
def test_report_reads_preserve_every_existing_report_variant(queries, builder):
    report = builder()
    _write(queries.layout.run_report(report.started_at, report.run_id), report)

    assert queries.read_report(report.run_id) == report
    assert queries.list_reports() == (report.run_id,)


@pytest.mark.parametrize("command", [None, 3, [], {}])
def test_malformed_report_discriminators_are_classified_integrity_errors(queries, command):
    report = examples.run_report()
    path = _write(queries.layout.run_report(report.started_at, report.run_id), report)
    payload = report.model_dump(mode="json") | {"command": command}
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(IntegrityError) as failure:
        queries.read_report(report.run_id)

    assert failure.value.problems[0].code == "HFVER007"


@pytest.mark.parametrize("field", ["run_id", "archive_id", "started_at"])
def test_report_body_must_match_requested_archive_and_filename(queries, field):
    report = examples.run_report()
    path = _write(queries.layout.run_report(report.started_at, report.run_id), report)
    replacements = {
        "run_id": "a" * 32,
        "archive_id": "00000000-0000-0000-0000-000000000001",
        "started_at": report.started_at + timedelta(seconds=1),
    }
    _write(path, report.model_copy(update={field: replacements[field]}))

    with pytest.raises(IntegrityError):
        queries.read_report(report.run_id)


def test_duplicate_report_ids_are_ambiguous_and_never_selected_by_time(queries):
    report = examples.run_report()
    _write(queries.layout.run_report(report.started_at, report.run_id), report)
    later = report.model_copy(update={"started_at": report.started_at + timedelta(seconds=1)})
    _write(queries.layout.run_report(later.started_at, later.run_id), later)

    with pytest.raises(IntegrityError, match="multiple"):
        queries.read_report(report.run_id)


@pytest.mark.parametrize("run_id", ["../escape", "A" * 32, "a" * 31])
def test_invalid_report_ids_fail_before_path_lookup(queries, run_id):
    with pytest.raises(ConfigurationError) as failure:
        queries.read_report(run_id)

    assert failure.value.problems[0].code == "HFARG001"


def test_an_absent_report_is_an_explicit_missing_identity(queries):
    with pytest.raises(ConfigurationError) as failure:
        queries.read_report(examples.RUN)

    assert failure.value.problems[0].code == "HFARG004"


def test_report_symlinks_cannot_read_an_outside_artifact(queries, tmp_path):
    report = examples.run_report()
    outside = _write(tmp_path / "outside.json", report)
    path = queries.layout.run_report(report.started_at, report.run_id)
    path.parent.mkdir(parents=True)
    path.symlink_to(outside)

    with pytest.raises(IntegrityError):
        queries.read_report(report.run_id)

    assert outside.read_text(encoding="utf-8") == report.to_json()


def test_report_parent_symlinks_cannot_escape_the_archive(queries, tmp_path):
    report = examples.run_report()
    outside = tmp_path / "outside"
    _write(outside / queries.layout.run_report(report.started_at, report.run_id).name, report)
    queries.layout.runs.symlink_to(outside, target_is_directory=True)

    with pytest.raises(IntegrityError):
        queries.read_report(report.run_id)


def test_exact_reference_and_manifest_preserve_their_distinct_locator_bases(queries):
    request = _publication(queries)

    assert queries.read_manifest(request) == examples.manifest()
    assert queries.read_reference(request.identity, request.commit_sha) == examples.reference()
    assert queries.read_reference(request.identity) == examples.reference()
    assert str(queries.read_reference(request.identity).tree).startswith("repos/")
    assert str(queries.read_manifest(request).tree).startswith("published/repos/")


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("repository_type", "dataset"),
        ("repository_id", "other/repository"),
        ("commit_sha", examples.OTHER_SHA),
        ("tree", "repos/models/other/repository/tree"),
        ("manifest", "manifests/models/other/repository/manifest.json"),
        ("publication_generation", 2),
    ],
)
def test_a_valid_reference_cannot_claim_another_requested_identity(queries, field, replacement):
    request = _publication(queries)
    path = queries.layout.repository(request.identity).revision_ref(request.commit_sha)
    _write(path, examples.reference().model_copy(update={field: replacement}))

    with pytest.raises(IntegrityError):
        queries.read_reference(request.identity, request.commit_sha)


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("repository_type", "dataset"),
        ("repository_id", "other/repository"),
        ("commit_sha", examples.OTHER_SHA),
        ("publication_id", examples.REPLACEMENT),
        ("tree", "published/repos/models/other/repository/tree"),
    ],
)
def test_a_valid_manifest_cannot_claim_another_publication(queries, field, replacement):
    request = _publication(queries)
    path = queries.layout.repository(request.identity).manifest(
        request.commit_sha, request.publication_id
    )
    _write(path, examples.manifest().model_copy(update={field: replacement}))

    with pytest.raises(IntegrityError) as failure:
        queries.read_manifest(request)

    assert failure.value.problems[0].code == "HFVER007"


@pytest.mark.parametrize("missing", [True, False])
def test_current_must_agree_with_the_retained_reference_it_names(queries, missing):
    request = _publication(queries)
    path = queries.layout.repository(request.identity).revision_ref(request.commit_sha)
    if missing:
        path.unlink()
    else:
        _write(path, examples.reference().model_copy(update={"publication_generation": 2}))

    with pytest.raises(IntegrityError):
        queries.read_reference(request.identity)


@pytest.mark.parametrize("kind", ["manifest", "manifest_parent", "tree"])
def test_publication_evidence_rejects_symlinks_at_every_read_boundary(queries, tmp_path, kind):
    request = _publication(queries)
    repository = queries.layout.repository(request.identity)
    manifest = repository.manifest(request.commit_sha, request.publication_id)
    tree = repository.instance(request.commit_sha, request.publication_id)
    if kind == "manifest":
        outside = _write(tmp_path / "outside.json", examples.manifest())
        manifest.unlink()
        manifest.symlink_to(outside)
    elif kind == "manifest_parent":
        outside = tmp_path / "outside"
        manifest.parent.rename(outside)
        manifest.parent.symlink_to(outside, target_is_directory=True)
    else:
        outside = tmp_path / "outside"
        tree.rename(outside)
        tree.symlink_to(outside, target_is_directory=True)

    with pytest.raises(IntegrityError):
        queries.read_manifest(request)


def test_a_vanished_exact_instance_never_substitutes_another_current_publication(queries):
    request = _publication(queries)
    repository = queries.layout.repository(request.identity)
    repository.instance(request.commit_sha, request.publication_id).rmdir()
    repository.instance(request.commit_sha, PublicationId(examples.REPLACEMENT)).mkdir()
    _write(
        repository.manifest(request.commit_sha, PublicationId(examples.REPLACEMENT)),
        examples.repair_manifest(),
    )
    _write(
        repository.current_ref,
        examples.reference().model_copy(
            update={
                "publication_id": examples.REPLACEMENT,
                "tree": examples.REFERENCE_TREE.replace(examples.PUBLICATION, examples.REPLACEMENT),
                "manifest": examples.REFERENCE_MANIFEST.replace(
                    examples.PUBLICATION, examples.REPLACEMENT
                ),
            }
        ),
    )

    with pytest.raises(IntegrityError):
        queries.read_manifest(request)
