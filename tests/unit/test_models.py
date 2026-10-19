"""Durable formats: serialization, versioning, and internal consistency.

`docs/schemas.md` §11 requires a golden fixture for every format, so that a
serialization change altering bytes without a `schema_version` bump fails the
suite. That is the first section here. The rest provokes each consistency rule
the models enforce, because a rule nothing tests is a comment.
"""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from hfcache.api.operations import OperationEvent, OperationReceipt, ResultReference
from hfcache.catalog_models import CatalogRecord, PublicationObservation, RepositoryTagSnapshot
from hfcache.catalog_storage import parse_record
from hfcache.errors import ExitCode, HfcacheError, IntegrityError, SafetyError
from hfcache.manifests import FileProvenance, RevisionManifest
from hfcache.models import (
    INDENT,
    SCHEMA_VERSION,
    ArchiveSentinel,
    PrunePlan,
    PurgePlan,
    Reference,
    RepairCleanup,
    RevisionSummary,
    TransactionJournal,
    dump,
    format_timestamp,
    load,
    parse_timestamp,
    serialize,
)
from hfcache.reporting import (
    RepositoriesCatalog,
    RepositoryCatalogEntry,
    RepositoryRunResult,
    RunReport,
    VerificationCatalog,
    VerificationReport,
)
from tests.fixtures import examples
from tests.fixtures.examples import EXAMPLES, at

FIXTURES = Path(__file__).parent.parent / "fixtures" / "schemas"

MODEL_FOR = {
    "repository-tag-snapshot": RepositoryTagSnapshot,
    "publication-observation": PublicationObservation,
    "operation-event": OperationEvent,
    "operation-result-reference": ResultReference,
    "operation-receipt": OperationReceipt,
    "journal": TransactionJournal,
    "manifest": RevisionManifest,
    "prune-plan": PrunePlan,
    "pruned-record": examples.PrunedRevisionRecord,
    "purge-plan": PurgePlan,
    "reference": Reference,
    "repair-manifest": RevisionManifest,
    "repair-retirement": examples.RepairRetirementRecord,
    "repositories-catalog": RepositoriesCatalog,
    "run-report": RunReport,
    "sentinel": ArchiveSentinel,
    "verification-catalog": VerificationCatalog,
    "verification-catalog-degraded": VerificationCatalog,
    "verification-report": VerificationReport,
}


# --------------------------------------------------------------------------- #
# Golden fixtures (`docs/schemas.md` §11)
# --------------------------------------------------------------------------- #


def test_every_format_has_a_fixture():
    on_disk = {path.stem for path in FIXTURES.glob("*.json")}

    assert on_disk == set(EXAMPLES), "a durable format gained or lost its golden fixture"
    assert set(MODEL_FOR) == set(EXAMPLES)


@pytest.mark.parametrize("name", sorted(EXAMPLES))
def test_serialization_is_byte_stable(name):
    # The whole point of a golden fixture: a change to the serializer, to field
    # ordering, or to a default that alters bytes fails here rather than in an
    # archive an operator is trying to read with a different release.
    assert dump(EXAMPLES[name]()) == (FIXTURES / f"{name}.json").read_bytes()


@pytest.mark.parametrize("name", sorted(EXAMPLES))
def test_every_fixture_round_trips(name):
    raw = (FIXTURES / f"{name}.json").read_bytes()

    expected = EXAMPLES[name]()
    parsed = (
        parse_record(type(expected), raw)
        if isinstance(expected, CatalogRecord)
        else load(type(expected), raw, error=IntegrityError, code="HFVER007")
    )

    assert dump(parsed) == raw
    assert parsed == EXAMPLES[name]()


@pytest.mark.parametrize("name", sorted(EXAMPLES))
def test_every_fixture_obeys_the_conventions(name):
    raw = (FIXTURES / f"{name}.json").read_bytes()
    text = raw.decode("utf-8")

    assert text.endswith("}\n")
    assert not text.endswith("\n\n")
    assert not text.startswith("﻿"), "no BOM"
    payload = json.loads(text)
    assert payload["schema_version"] == SCHEMA_VERSION
    assert text == json.dumps(payload, indent=INDENT, sort_keys=True, ensure_ascii=False) + "\n"


# --------------------------------------------------------------------------- #
# The serializer
# --------------------------------------------------------------------------- #


def test_serialize_sorts_keys_and_ends_with_one_newline():
    text = serialize({"b": 1, "a": 2})

    assert text == '{\n  "a": 2,\n  "b": 1\n}\n'


def test_serialize_without_indent_is_one_line():
    text = serialize({"b": 1, "a": 2}, indent=None)

    assert text == '{"a": 2,"b": 1}\n'
    assert text.count("\n") == 1


def test_serialize_keeps_non_ascii_readable():
    # ensure_ascii=False: an operator reading a manifest should see the file
    # name the repository actually used, not an escape sequence.
    assert "café" in serialize({"path": "café.txt"})


def test_serialize_refuses_nan():
    # NaN is not JSON, and Python emits it anyway unless told not to. A throughput
    # figure that serialized as NaN would make the file unparseable elsewhere.
    with pytest.raises(ValueError, match="Out of range"):
        serialize({"rate": float("nan")})


# --------------------------------------------------------------------------- #
# Timestamps
# --------------------------------------------------------------------------- #


def test_timestamps_are_utc_with_microseconds_and_a_literal_z():
    assert format_timestamp(datetime(2026, 7, 24, 20, 57, 31, 123456, tzinfo=UTC)) == (
        "2026-07-24T20:57:31.123456Z"
    )


def test_a_whole_second_still_carries_microseconds():
    # Fixed width keeps string ordering and timestamp ordering the same thing.
    assert format_timestamp(datetime(2026, 7, 24, tzinfo=UTC)) == "2026-07-24T00:00:00.000000Z"


def test_a_non_utc_timestamp_is_converted_not_rejected():
    eastern = datetime.fromisoformat("2026-07-24T16:57:31.123456-04:00")

    assert format_timestamp(eastern) == "2026-07-24T20:57:31.123456Z"


@pytest.mark.parametrize(
    "value",
    [
        datetime(2026, 7, 24, 20, 57, 31),  # noqa: DTZ001 - naive is the case under test
        "2026-07-24T20:57:31.123456+00:00",
        "2026-07-24T20:57:31",
        "not a timestamp",
        "2026-07-24T20:57:31.123456z",
    ],
)
def test_timestamps_without_explicit_utc_are_refused(value):
    with pytest.raises(ValueError, match=r"timezone-aware|literal 'Z'"):
        parse_timestamp(value)


def test_a_non_string_timestamp_is_refused():
    # A ValueError specifically: Pydantic turns those into validation errors and
    # lets a TypeError escape uncoded past `load`.
    with pytest.raises(ValueError, match="must be a string"):
        parse_timestamp(1753398000)


def test_writing_a_naive_timestamp_is_refused():
    with pytest.raises(ValueError, match="timezone-aware"):
        format_timestamp(datetime(2026, 7, 24))  # noqa: DTZ001 - naive is the case under test


@pytest.mark.parametrize("value", ["2026-13-45T99:99:99.000000Z", "Z", "2026-07-24TZ"])
def test_a_z_suffix_does_not_make_something_a_timestamp(value):
    with pytest.raises(ValueError, match="not RFC 3339"):
        parse_timestamp(value)


@pytest.mark.parametrize(
    "digest",
    [
        "",
        "abc",
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b85",
        "A" * 64,
        "g" * 64,
    ],
)
def test_a_digest_must_be_64_lowercase_hex(digest):
    payload = examples.run_report().to_payload()
    payload["config_fingerprint"] = digest

    with pytest.raises(ValueError, match="64 lowercase hex"):
        RunReport.model_validate(payload)


def test_a_non_string_digest_is_refused():
    payload = examples.run_report().to_payload()
    payload["config_fingerprint"] = 12345

    with pytest.raises(ValueError, match="must be a string"):
        RunReport.model_validate(payload)


@given(
    moment=st.datetimes(
        min_value=datetime(2000, 1, 1),  # noqa: DTZ001 - hypothesis wants naive bounds
        max_value=datetime(2100, 1, 1),  # noqa: DTZ001
        timezones=st.just(UTC),
    )
)
def test_any_timestamp_round_trips_through_its_text(moment):
    assert parse_timestamp(format_timestamp(moment)) == moment


# --------------------------------------------------------------------------- #
# Version compatibility (`docs/schemas.md` §1.1)
# --------------------------------------------------------------------------- #


def test_a_newer_schema_version_is_refused_rather_than_guessed_at():
    payload = json.loads((FIXTURES / "sentinel.json").read_text())
    payload["schema_version"] = SCHEMA_VERSION + 1

    with pytest.raises(SafetyError) as raised:
        load(ArchiveSentinel, serialize(payload), error=SafetyError, code="HFMNT006")

    problem = raised.value.problems[0]
    assert problem.code == "HFMNT006"
    assert "newer" in problem.message
    assert raised.value.exit_code == ExitCode.SAFETY


def test_an_older_schema_version_is_refused_because_no_migration_exists():
    payload = json.loads((FIXTURES / "sentinel.json").read_text())
    payload["schema_version"] = 0

    with pytest.raises(SafetyError, match="older"):
        load(ArchiveSentinel, serialize(payload), error=SafetyError, code="HFMNT006")


def test_the_version_is_checked_before_the_rest_of_the_file():
    # A future release may add required fields. Reporting those as missing would
    # send an operator to fix a file that this release simply must not read.
    with pytest.raises(SafetyError, match="newer"):
        load(
            ArchiveSentinel,
            serialize({"schema_version": 99}),
            error=SafetyError,
            code="HFMNT006",
        )


@pytest.mark.parametrize(
    "payload",
    ['{"schema_version": "1"}', '{"schema_version": true}', "{}", "[]", '"a string"', "12"],
)
def test_a_missing_or_non_integer_version_is_refused(payload):
    with pytest.raises(SafetyError, match=r"schema_version|JSON object"):
        load(ArchiveSentinel, payload, error=SafetyError, code="HFMNT006")


def test_malformed_json_is_reported_with_its_position():
    with pytest.raises(SafetyError, match="line 1 column"):
        load(ArchiveSentinel, "{not json", error=SafetyError, code="HFMNT006")


def test_bytes_that_are_not_utf8_are_refused():
    with pytest.raises(SafetyError, match="UTF-8"):
        load(ArchiveSentinel, b"\xff\xfe{}", error=SafetyError, code="HFMNT006")


def test_the_caller_chooses_the_error_class_and_code():
    # A bad manifest is exit 40; a bad journal is exit 20. Same malformed file,
    # different meaning, so `load` does not decide.
    for error, code, exit_code in (
        (IntegrityError, "HFVER007", ExitCode.INTEGRITY),
        (SafetyError, "HFTXN001", ExitCode.SAFETY),
    ):
        with pytest.raises(HfcacheError) as raised:
            load(ArchiveSentinel, '{"schema_version": 1}', error=error, code=code)
        assert raised.value.exit_code == exit_code
        assert {problem.code for problem in raised.value.problems} == {code}


def test_every_validation_problem_is_reported_at_once():
    with pytest.raises(IntegrityError) as raised:
        load(ArchiveSentinel, '{"schema_version": 1}', error=IntegrityError, code="HFVER007")

    locations = [problem.location for problem in raised.value.problems]
    assert locations == ["archive_id", "created_at", "created_by"]


def test_a_location_prefix_names_the_file():
    with pytest.raises(IntegrityError) as raised:
        load(
            ArchiveSentinel,
            '{"schema_version": 1}',
            error=IntegrityError,
            code="HFVER007",
            location="/srv/hfcache/.hfcache-root",
        )

    assert raised.value.problems[0].location == "/srv/hfcache/.hfcache-root:archive_id"


def test_an_unknown_key_is_reported_not_dropped():
    payload = json.loads((FIXTURES / "sentinel.json").read_text())
    payload["future_field"] = "something this release does not know"

    with pytest.raises(IntegrityError) as raised:
        load(ArchiveSentinel, serialize(payload), error=IntegrityError, code="HFVER007")

    assert raised.value.problems[0].location == "future_field"


def test_a_model_cannot_be_constructed_with_the_wrong_version():
    with pytest.raises(ValueError, match="schema_version"):
        examples.sentinel().model_copy(update={"schema_version": 2}).model_validate(
            examples.sentinel().to_payload() | {"schema_version": 2}
        )


# --------------------------------------------------------------------------- #
# Immutability and strictness
# --------------------------------------------------------------------------- #


def test_a_loaded_manifest_cannot_be_mutated():
    manifest = examples.manifest()

    with pytest.raises(ValueError, match="frozen"):
        # pyrefly: ignore[read-only]
        # A manifest is evidence (`FS-06`); the type checker rejects this too.
        manifest.total_bytes = 0


def test_values_are_not_coerced():
    payload = json.loads((FIXTURES / "manifest.json").read_text())
    payload["file_count"] = "2"

    with pytest.raises(IntegrityError):
        load(RevisionManifest, serialize(payload), error=IntegrityError, code="HFVER007")


# --------------------------------------------------------------------------- #
# Sentinel
# --------------------------------------------------------------------------- #


def test_an_unknown_layout_version_is_refused():
    payload = json.loads((FIXTURES / "sentinel.json").read_text())
    payload["layout_version"] = 2

    with pytest.raises(SafetyError, match="layout_version"):
        load(ArchiveSentinel, serialize(payload), error=SafetyError, code="HFMNT006")


# --------------------------------------------------------------------------- #
# Reference paths
# --------------------------------------------------------------------------- #


def test_a_reference_is_relative_to_published_not_the_archive_root():
    reference = examples.reference()

    assert reference.tree.startswith("repos/")
    assert reference.manifest.startswith("manifests/")
    assert reference.identity.selector == "model:organization/model-name"


@pytest.mark.parametrize("escape", ["../.store/hub", "/srv/hfcache/published/repos", "a/../../b"])
def test_a_reference_path_that_escapes_is_refused(escape):
    payload = json.loads((FIXTURES / "reference.json").read_text())
    payload["tree"] = escape

    with pytest.raises(IntegrityError):
        load(Reference, serialize(payload), error=IntegrityError, code="HFVER008")


# --------------------------------------------------------------------------- #
# Prune plan validity (`docs/schemas.md` §8)
# --------------------------------------------------------------------------- #


def test_a_plan_that_does_not_select_the_lowest_generation_is_refused():
    plan = examples.prune_plan()
    payload = plan.to_payload()
    payload["selected"]["publication_generation"] = 3

    with pytest.raises(ValueError, match="lowest retained generation"):
        PrunePlan.model_validate(payload)


def test_a_plan_that_selects_the_current_revision_is_refused():
    payload = examples.prune_plan().to_payload()
    payload["current"] = {
        "commit_sha": payload["selected"]["commit_sha"],
        "publication_generation": 1,
    }

    with pytest.raises(ValueError, match="current revision is never selected"):
        PrunePlan.model_validate(payload)


def test_a_plan_with_a_repeated_generation_is_refused():
    payload = examples.prune_plan().to_payload()
    payload["retained"][1]["publication_generation"] = 1

    with pytest.raises(ValueError, match="distinct publication generations"):
        PrunePlan.model_validate(payload)


def test_a_generation_below_one_is_refused():
    with pytest.raises(ValueError, match="greater than or equal to 1"):
        RevisionSummary(commit_sha=examples.SHA, publication_generation=0)


# --------------------------------------------------------------------------- #
# Purge plan validity (`docs/schemas.md` §8.1)
# --------------------------------------------------------------------------- #


def test_a_purge_plan_cache_scope_must_match_every_revision():
    payload = examples.purge_plan().to_payload()
    payload["cache_revisions_to_delete"] = [examples.OTHER_SHA]

    with pytest.raises(ValueError, match="cache revisions must exactly match"):
        PurgePlan.model_validate(payload)


def test_a_purge_plan_must_contain_its_current_revision():
    payload = examples.purge_plan().to_payload()
    payload["current"]["commit_sha"] = examples.OTHER_SHA

    with pytest.raises(ValueError, match="contain the current revision exactly once"):
        PurgePlan.model_validate(payload)


def test_a_purge_plan_must_not_repeat_a_commit():
    payload = examples.purge_plan().to_payload()
    duplicate = dict(payload["revisions"][0])
    duplicate["publication_generation"] = 2
    payload["revisions"].append(duplicate)
    payload["cache_revisions_to_delete"].append(duplicate["commit_sha"])
    payload["unique_bytes_released_estimate"] *= 2

    with pytest.raises(ValueError, match="distinct commit SHAs"):
        PurgePlan.model_validate(payload)


# --------------------------------------------------------------------------- #
# Transaction journal (`docs/schemas.md` §10)
# --------------------------------------------------------------------------- #


def test_checkpoint_sequences_must_be_contiguous_from_one():
    payload = examples.journal().to_payload()
    payload["checkpoints"][1]["sequence"] = 3

    with pytest.raises(ValueError, match="sequences must start at 1"):
        TransactionJournal.model_validate(payload)


def test_a_journal_with_no_checkpoints_has_no_last_checkpoint_time():
    payload = examples.journal().to_payload()
    payload["checkpoints"] = []

    with pytest.raises(ValueError, match="last_checkpoint_at"):
        TransactionJournal.model_validate(payload)


def test_an_open_transaction_has_no_completion_time():
    payload = examples.journal().to_payload()
    payload["completed_at"] = "2026-07-24T20:41:50.000000Z"

    with pytest.raises(ValueError, match="open transaction"):
        TransactionJournal.model_validate(payload)


def test_repository_identity_is_all_or_nothing():
    payload = examples.journal().to_payload()
    payload["repository_type"] = None

    with pytest.raises(ValueError, match="set together or not at all"):
        TransactionJournal.model_validate(payload)


@pytest.mark.parametrize(
    ("state", "resolved"),
    [("open", False), ("committed", True), ("failed", True), ("needs_operator", False)],
)
def test_only_a_settled_journal_is_resolved(state, resolved):
    payload = examples.journal().to_payload()
    payload["state"] = state
    if state != "open":
        payload["completed_at"] = "2026-07-24T20:41:50.000000Z"

    assert TransactionJournal.model_validate(payload).is_resolved is resolved


# --------------------------------------------------------------------------- #
# Repair retirement (`docs/schemas.md` §9.2)
# --------------------------------------------------------------------------- #


def test_a_grace_period_must_extend_past_retirement():
    payload = examples.repair_retirement().to_payload()
    payload["grace_expires_at"] = payload["retired_at"]

    with pytest.raises(ValueError, match="after retired_at"):
        examples.RepairRetirementRecord.model_validate(payload)


def test_a_repair_must_produce_a_new_publication_id():
    payload = examples.repair_retirement().to_payload()
    payload["replacement_publication_id"] = payload["retired_publication_id"]

    with pytest.raises(ValueError, match="new publication id"):
        examples.RepairRetirementRecord.model_validate(payload)


@pytest.mark.parametrize(
    ("state", "completed_at"),
    [("completed", None), ("pending", "2026-07-25T09:14:02.000000Z")],
)
def test_cleanup_state_and_timestamp_must_agree(state, completed_at):
    with pytest.raises(ValueError, match="must agree"):
        RepairCleanup(state=state, completed_at=completed_at)


# --------------------------------------------------------------------------- #
# Reports
# --------------------------------------------------------------------------- #


def test_an_outcome_that_contradicts_its_exit_code_is_refused():
    payload = examples.run_report().to_payload()
    payload["exit_code"] = 30

    with pytest.raises(ValueError, match="contradicts exit_code"):
        RunReport.model_validate(payload)


def test_an_undeclared_exit_code_is_refused():
    payload = examples.run_report().to_payload()
    payload["exit_code"] = 7

    with pytest.raises(ValueError, match="is not one of"):
        RunReport.model_validate(payload)


def test_success_with_warnings_requires_warnings():
    payload = examples.run_report().to_payload()
    payload["outcome"] = "success_with_warnings"

    with pytest.raises(ValueError, match="exactly when warnings"):
        RunReport.model_validate(payload)


def test_a_successful_run_report_cannot_hide_warnings():
    payload = examples.run_report().to_payload()
    payload["warnings"] = ["HFDEP001"]

    with pytest.raises(ValueError, match="exactly when warnings"):
        RunReport.model_validate(payload)


def test_a_failed_run_report_preserves_warnings_alongside_errors():
    payload = examples.run_report().to_payload()
    payload.update(
        exit_code=30,
        outcome="failed",
        errors=["HFHUB004"],
        warnings=["HFDEP001"],
    )

    report = RunReport.model_validate(payload)

    assert report.errors == ("HFHUB004",)
    assert report.warnings == ("HFDEP001",)


def test_run_report_repositories_are_sorted_and_unique():
    payload = examples.run_report().to_payload()
    payload["repositories"] = [payload["repositories"][0], payload["repositories"][0]]

    with pytest.raises(ValueError, match="at most once"):
        RunReport.model_validate(payload)


def test_a_failed_repository_must_say_why():
    with pytest.raises(ValueError, match="at least one error code"):
        RepositoryRunResult(
            repository_id="organization/model-name",
            repository_type="model",
            requested_revision="main",
            status="failed",
        )


def test_completed_with_warnings_must_carry_a_warning_code():
    with pytest.raises(ValueError, match="at least one warning code"):
        RepositoryRunResult(
            repository_id="organization/model-name",
            repository_type="model",
            requested_revision="main",
            status="completed_with_warnings",
        )


def test_run_report_repositories_must_be_sorted():
    payload = examples.run_report().to_payload()
    first = payload["repositories"][0]
    second = dict(first)
    second["repository_type"] = "dataset"
    payload["repositories"] = [first, second]

    with pytest.raises(ValueError, match="sorted by"):
        RunReport.model_validate(payload)


def test_a_published_repository_names_its_instance():
    with pytest.raises(ValueError, match="names the instance"):
        RepositoryRunResult(
            repository_id="organization/model-name",
            repository_type="model",
            requested_revision="main",
            status="published",
        )


def test_report_duration_comes_from_its_own_timestamps():
    report = examples.run_report()

    assert report.duration_seconds == pytest.approx(214.502)


def test_a_report_cannot_complete_before_it_started():
    payload = examples.run_report().to_payload()
    payload["completed_at"] = "2026-07-24T20:00:00.000000Z"

    with pytest.raises(ValueError, match="before started_at"):
        RunReport.model_validate(payload)


# --------------------------------------------------------------------------- #
# Verification report and catalog
# --------------------------------------------------------------------------- #


def test_findings_and_outcome_must_agree():
    payload = examples.verification_report().to_payload()
    payload["verification_outcome"] = "clean"

    with pytest.raises(ValueError, match="must agree"):
        VerificationReport.model_validate(payload)


def test_a_clean_report_has_no_findings():
    payload = examples.verification_report().to_payload()
    payload["findings"] = []
    payload["errors"] = []
    payload["exit_code"] = 0
    payload["outcome"] = "success"

    with pytest.raises(ValueError, match="must agree"):
        VerificationReport.model_validate(payload)


def test_findings_must_be_sorted():
    report = examples.verification_report()
    payload = report.to_payload()
    second = dict(payload["findings"][0])
    second["path"] = "config.json"
    payload["findings"] = [payload["findings"][0], second]

    with pytest.raises(ValueError, match="findings must be sorted"):
        VerificationReport.model_validate(payload)


def test_verification_catalog_repositories_must_be_sorted():
    payload = examples.verification_catalog().to_payload()
    first = payload["repositories"][0]
    second = dict(first)
    second["repository_type"] = "dataset"
    payload["repositories"] = [first, second]

    with pytest.raises(ValueError, match="sorted by"):
        VerificationCatalog.model_validate(payload)


def test_verification_catalog_revisions_must_be_sorted_by_sha():
    payload = examples.verification_catalog().to_payload()
    entry = payload["repositories"][0]
    later = dict(entry["revisions"][0])
    later["commit_sha"] = examples.OTHER_SHA
    entry["revisions"] = [later, entry["revisions"][0]]

    with pytest.raises(ValueError, match="sorted ascending by commit_sha"):
        VerificationCatalog.model_validate(payload)


def test_one_revision_has_one_most_recent_verification_outcome():
    payload = examples.verification_catalog().to_payload()
    entry = payload["repositories"][0]
    entry["revisions"] = [entry["revisions"][0], dict(entry["revisions"][0])]

    with pytest.raises(ValueError, match="one most recent verification outcome"):
        VerificationCatalog.model_validate(payload)


def test_outstanding_failures_must_be_sorted():
    payload = examples.degraded_verification_catalog().to_payload()
    first = payload["outstanding_failures"][0]
    earlier = dict(first)
    earlier["commit_sha"] = "0" * 40
    payload["outstanding_failures"] = [first, earlier]

    with pytest.raises(ValueError, match="outstanding_failures must be sorted"):
        VerificationCatalog.model_validate(payload)


def test_a_repeated_generation_in_the_catalog_is_refused():
    payload = examples.repositories_catalog().to_payload()
    entry = payload["repositories"][0]
    duplicate = dict(entry["revisions"][0])
    duplicate["commit_sha"] = examples.OTHER_SHA
    entry["revisions"] = [entry["revisions"][0], duplicate]

    with pytest.raises(ValueError, match="its own publication generation"):
        RepositoriesCatalog.model_validate(payload)


def test_outstanding_failures_make_the_archive_degraded():
    assert examples.verification_catalog().is_degraded is False
    assert examples.degraded_verification_catalog().is_degraded is True


def test_catalog_revisions_are_ordered_by_generation():
    payload = examples.repositories_catalog().to_payload()
    entry = payload["repositories"][0]
    second = dict(entry["revisions"][0])
    second["publication_generation"] = 0 + 2
    second["commit_sha"] = examples.OTHER_SHA
    entry["revisions"] = [second, entry["revisions"][0]]

    with pytest.raises(ValueError, match="sorted ascending by publication_generation"):
        RepositoriesCatalog.model_validate(payload)


def test_current_must_be_a_retained_revision():
    payload = examples.repositories_catalog().to_payload()
    payload["repositories"][0]["current"]["commit_sha"] = examples.OTHER_SHA

    with pytest.raises(ValueError, match="does not retain"):
        RepositoriesCatalog.model_validate(payload)


def test_an_unmanaged_repository_has_no_enabled_flag():
    # `enabled` is a configuration fact. A repository no longer in configuration
    # has no such fact, and reporting `false` would imply it was turned off.
    with pytest.raises(ValueError, match="enabled is null"):
        RepositoryCatalogEntry(
            managed=False,
            enabled=False,
            repository_id="organization/model-name",
            repository_type="model",
        )


def test_an_unmanaged_repository_is_still_listed():
    entry = RepositoryCatalogEntry(
        managed=False, repository_id="organization/model-name", repository_type="model"
    )

    assert entry.enabled is None
    assert entry.upstream_state == "unknown"


def test_catalogs_are_sorted_by_type_then_id():
    payload = examples.repositories_catalog().to_payload()
    first = payload["repositories"][0]
    second = dict(first)
    second["repository_type"] = "dataset"
    payload["repositories"] = [first, second]

    with pytest.raises(ValueError, match="sorted by"):
        RepositoriesCatalog.model_validate(payload)


# --------------------------------------------------------------------------- #
# Manifest consistency (`docs/schemas.md` §3)
# --------------------------------------------------------------------------- #


def test_file_count_must_match_the_files_listed():
    payload = examples.manifest().to_payload()
    payload["file_count"] = 3

    with pytest.raises(ValueError, match="does not equal len"):
        RevisionManifest.model_validate(payload)


def test_total_bytes_must_match_the_sum_of_sizes():
    payload = examples.manifest().to_payload()
    payload["total_bytes"] = 1

    with pytest.raises(ValueError, match="sum of sizes"):
        RevisionManifest.model_validate(payload)


def test_reused_digests_must_match_the_unhashed_entries():
    payload = examples.manifest().to_payload()
    payload["verification"]["reused_digests"] = 0

    with pytest.raises(ValueError, match="reused_digests"):
        RevisionManifest.model_validate(payload)


def test_files_must_be_sorted_by_path():
    payload = examples.manifest().to_payload()
    payload["files"] = list(reversed(payload["files"]))

    with pytest.raises(ValueError, match="sorted byte-wise"):
        RevisionManifest.model_validate(payload)


def test_two_files_that_collide_on_disk_are_refused():
    payload = examples.manifest().to_payload()
    second = dict(payload["files"][0])
    second["path"] = "Config.json"
    payload["files"] = sorted([payload["files"][0], second], key=lambda item: item["path"])
    payload["file_count"] = 3
    payload["files"].append(payload["files"].pop(0))

    # Rebuild cleanly: two spellings of one name, correct arithmetic.
    entries = [dict(payload["files"][0]), second]
    entries[0]["path"] = "config.json"
    entries.sort(key=lambda item: item["path"])
    payload["files"] = entries
    payload["file_count"] = 2
    payload["total_bytes"] = sum(entry["size"] for entry in entries)
    payload["verification"]["reused_digests"] = sum(
        1 for entry in entries if not entry["provenance"]["hashed"]
    )

    with pytest.raises(ValueError, match="same on-disk path"):
        RevisionManifest.model_validate(payload)


def test_dependencies_must_be_sorted():
    payload = examples.manifest().to_payload()
    first = dict(payload["dependencies"][0])
    second = dict(first)
    second["detected_id"] = "aaa/aaa"
    payload["dependencies"] = [first, second]

    with pytest.raises(ValueError, match="dependencies must be sorted"):
        RevisionManifest.model_validate(payload)


def test_the_publication_timeline_must_run_forwards():
    payload = examples.manifest().to_payload()
    payload["published_at"] = "2026-07-24T20:00:00.000000Z"

    with pytest.raises(ValueError, match="published_at is before verified_at"):
        RevisionManifest.model_validate(payload)


def test_first_observed_may_predate_the_download_but_not_follow_it():
    payload = examples.manifest().to_payload()
    payload["first_observed_at"] = "2026-06-01T00:00:00.000000Z"
    assert RevisionManifest.model_validate(payload).first_observed_at == at(
        "2026-06-01T00:00:00.000000Z"
    )

    payload["first_observed_at"] = "2026-07-24T20:41:00.000000Z"
    with pytest.raises(ValueError, match="first_observed_at is after"):
        RevisionManifest.model_validate(payload)


def test_the_two_verified_at_fields_must_agree():
    payload = examples.manifest().to_payload()
    payload["verification"]["verified_at"] = "2026-07-24T20:41:40.000000Z"

    with pytest.raises(ValueError, match="same moment"):
        RevisionManifest.model_validate(payload)


def test_an_unhashed_object_must_name_where_its_digest_came_from():
    with pytest.raises(ValueError, match="ever read these bytes"):
        FileProvenance(cache_root="canonical", hashed=False, source="cache_reuse")


def test_a_hashed_object_does_not_claim_reuse():
    with pytest.raises(ValueError, match="only when this object was not hashed"):
        FileProvenance(
            cache_root="canonical",
            hash_reused_from=examples.HashReuse(
                commit_sha=examples.SHA, publication_id=examples.PUBLICATION
            ),
            hashed=True,
            source="hub_download",
        )


def test_a_repair_download_comes_from_the_repair_cache():
    with pytest.raises(ValueError, match="repair cache root"):
        FileProvenance(cache_root="canonical", hashed=True, source="repair_download")


def test_a_repair_manifest_preserves_the_original_expectations():
    original = examples.manifest()
    repaired = examples.repair_manifest()

    assert repaired.is_repair
    assert original.is_repair is False
    assert repaired.publication_id != original.publication_id
    assert repaired.publication_generation == original.publication_generation
    assert [(f.path, f.size, f.sha256) for f in repaired.files] == [
        (f.path, f.size, f.sha256) for f in original.files
    ]
    assert repaired.repair is not None
    assert repaired.repair.repair_of == original.publication_id


def test_a_manifest_path_is_repository_relative():
    payload = examples.manifest().to_payload()
    payload["files"][0]["path"] = "../../../etc/passwd"

    with pytest.raises(IntegrityError):
        load(RevisionManifest, serialize(payload), error=IntegrityError, code="HFVER007")


def test_a_manifest_tree_keeps_the_published_prefix():
    # Unlike a reference, a manifest's `tree` is archive-relative: it is read by
    # the writer, which sees the whole archive (`docs/schemas.md` §3.1).
    assert examples.manifest().tree.startswith("published/repos/")


@given(size=st.integers(min_value=-(2**40), max_value=-1))
def test_a_negative_byte_count_is_refused(size):
    payload = examples.manifest().to_payload()
    payload["files"][0]["size"] = size

    with pytest.raises(ValueError, match="greater than or equal to 0"):
        RevisionManifest.model_validate(payload)


def test_a_manifest_knows_its_repository():
    assert examples.manifest().identity.directory == "models"


def test_timestamps_survive_a_round_trip_through_the_file():
    raw = dump(examples.manifest())
    reloaded = load(RevisionManifest, raw, error=IntegrityError, code="HFVER007")

    assert reloaded.published_at - reloaded.verified_at == timedelta(seconds=4, microseconds=539000)
