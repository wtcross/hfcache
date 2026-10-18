"""Explicit maintenance scopes reject preview documents and implicit apply (API-010)."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from hfcache.api.maintenance_models import (
    InitializationSubmission,
    PruneSubmission,
    PurgeSubmission,
    QuarantineSubmission,
    RecoverySubmission,
    RepairSubmission,
)
from hfcache.errors import HfcacheError
from tests.fixtures import examples

SELECTOR = "model:organization/model-name"
REVISION = SELECTOR + "@" + examples.SHA


@pytest.mark.parametrize(
    ("model", "scope"),
    [
        (PruneSubmission, {}),
        (PurgeSubmission, {"all_unmanaged": True}),
        (RecoverySubmission, {}),
        (QuarantineSubmission, {"transaction_ids": [examples.TRANSACTION]}),
        (RepairSubmission, {"revision": REVISION}),
        (
            InitializationSubmission,
            {"archive_root": "/tmp/archive", "archive_id": examples.ARCHIVE_ID, "confirm": True},
        ),
    ],
)
@pytest.mark.parametrize("extra", ["apply", "dry_run", "mode", "preview", "plans", "command"])
def test_url_is_the_only_maintenance_mode_and_preview_is_not_authority(model, scope, extra):
    with pytest.raises(ValidationError):
        model.model_validate(scope | {extra: True})


def test_prune_selection_preserves_configured_repository_semantics():
    request = PruneSubmission.model_validate(
        {"selectors": [REVISION, "dataset:organization/data", SELECTOR]}
    )
    assert request.selectors == ("dataset:organization/data", SELECTOR)


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"selectors": []},
        {"all_unmanaged": False},
        {"selectors": [SELECTOR], "all_unmanaged": True},
        {"selectors": [REVISION]},
        {"selectors": [1]},
        {"all_unmanaged": "true"},
        {"all_unmanaged": 1},
    ],
)
def test_purge_has_one_explicit_whole_repository_scope(body):
    with pytest.raises((ValidationError, HfcacheError)):
        PurgeSubmission.model_validate(body)


def test_equivalent_purge_and_quarantine_scopes_have_one_canonical_body():
    first = PurgeSubmission.model_validate({"selectors": [SELECTOR, SELECTOR]})
    second = PurgeSubmission.model_validate({"selectors": [SELECTOR], "all_unmanaged": False})
    assert first.model_dump(mode="json") == second.model_dump(mode="json")
    identifiers = ["f" * 32, examples.TRANSACTION, "f" * 32]
    quarantine = QuarantineSubmission.model_validate({"transaction_ids": identifiers})
    identifiers.clear()
    assert quarantine.transaction_ids == tuple(sorted((examples.TRANSACTION, "f" * 32)))


@pytest.mark.parametrize(
    "identifiers", [[], None, "a" * 32, [1], ["A" * 32], ["../x"], ["a" * 32] * 101]
)
def test_quarantine_requires_bounded_exact_ids(identifiers):
    with pytest.raises(ValidationError):
        QuarantineSubmission.model_validate({"transaction_ids": identifiers})


@pytest.mark.parametrize(
    "body", [{}, {"revision": SELECTOR}, {"revision": REVISION, "reason": 1}, {"revision": 1}]
)
def test_repair_requires_one_immutable_revision_and_strict_reason(body):
    with pytest.raises((ValidationError, HfcacheError)):
        RepairSubmission.model_validate(body)


def test_repair_preserves_ordinary_reason_without_claiming_deletion_authority():
    reason = "checksum mismatch; reviewed with operator\nTicket 123 — retained original"
    request = RepairSubmission(revision=REVISION, reason=reason).service_request()
    assert request.selector == REVISION
    assert request.commit_sha == examples.SHA
    assert request.reason == reason
    assert RepairSubmission(revision=REVISION).reason == "operator_requested"
    assert RepairSubmission(revision=REVISION, reason="").reason == ""
    with pytest.raises(ValidationError):
        RepairSubmission(revision=REVISION, reason="x" * 2049)


@pytest.mark.parametrize("confirm", [False, 0, 1, "true", None])
def test_initialization_confirmation_is_exact_boolean_true(confirm):
    with pytest.raises(ValidationError):
        InitializationSubmission.model_validate(
            {"archive_root": "/tmp/archive", "archive_id": examples.ARCHIVE_ID, "confirm": confirm}
        )


@pytest.mark.parametrize(
    "scope",
    [
        {"archive_id": examples.ARCHIVE_ID, "confirm": True},
        {"archive_root": "/tmp/archive", "confirm": True},
        {"archive_root": "/tmp/archive", "archive_id": examples.ARCHIVE_ID},
        {
            "archive_root": "/tmp/archive",
            "archive_id": examples.ARCHIVE_ID.upper(),
            "confirm": True,
        },
        {"archive_root": "/tmp/archive", "archive_id": True, "confirm": True},
    ],
)
def test_initialization_requires_restatement_of_both_authority_fields(scope):
    with pytest.raises(ValidationError):
        InitializationSubmission.model_validate(scope)


@pytest.mark.parametrize(
    "root",
    ["relative", "/tmp/../archive", "/tmp/./archive", "/tmp/a\x00b", "/tmp/a\nb", "/tmp/a\\b", 1],
)
def test_initialization_target_is_an_absolute_nonescaping_path(root):
    with pytest.raises(ValidationError):
        InitializationSubmission.model_validate(
            {"archive_root": root, "archive_id": examples.ARCHIVE_ID, "confirm": True}
        )


def test_initialization_body_is_a_restatement_not_a_file_loader(monkeypatch):
    def forbidden(*_args, **_kwargs):
        pytest.fail("initialization DTO inspected a caller-selected path")

    monkeypatch.setattr(Path, "stat", forbidden)
    monkeypatch.setattr(Path, "read_bytes", forbidden)
    body = InitializationSubmission.model_validate(
        {"archive_root": "/tmp/archive", "archive_id": examples.ARCHIVE_ID, "confirm": True}
    )
    assert body.model_dump(mode="json") == {
        "archive_root": "/tmp/archive",
        "archive_id": examples.ARCHIVE_ID,
        "confirm": True,
    }
