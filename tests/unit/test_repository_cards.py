"""ADR142: independent bounded presentation and exact retained atomic storage."""

import hashlib
import json

import pytest
from pydantic import ValidationError

from hfcache import catalog_models, catalog_storage
from hfcache.catalog_extractors import ExtractionBudget
from hfcache.catalog_models import (
    MAXIMUM_CARD_PRESENTATION_BYTES,
    MAXIMUM_CARD_RECORD_BYTES,
    RepositoryCard,
)
from hfcache.catalog_storage import parse_record, read_repository_card
from hfcache.errors import IntegrityError, SafetyError
from hfcache.identity import CommitSha, PublicationId
from hfcache.metadata import MetadataReader, QueryLimitError
from hfcache.models import dump
from hfcache.redaction import clear_registered_secrets, register_secret
from tests.fixtures import examples
from tests.unit import test_catalog_storage as storage

archive = storage.archive
writer = storage.writer


def present(markdown="# Archived fixture\n", **updates):
    payload = examples.repository_card().to_payload()
    payload.update(
        state="present",
        source_path="README.md",
        expected_source_sha256=examples.DIGEST,
        markdown=markdown,
        presentation_sha256=hashlib.sha256(markdown.encode()).hexdigest(),
        diagnostics=[],
    )
    payload.update(updates)
    return RepositoryCard.model_validate(payload)


def publication(archive, *, readme=False):
    manifest = storage.published(archive)
    if readme:
        payload = manifest.to_payload()
        entry = dict(payload["files"][0], path="README.md")
        payload["files"] = [entry, *payload["files"]]
        payload["file_count"] += 1
        payload["total_bytes"] += entry["size"]
        manifest = type(manifest).model_validate(payload)
        path = (
            archive[0]
            .repository(manifest.identity)
            .manifest(CommitSha(manifest.commit_sha), PublicationId(manifest.publication_id))
        )
        path.write_bytes(dump(manifest))
    return manifest


def bound_card(manifest, *, markdown="# Archived fixture\n"):
    record = (
        present(markdown)
        if any(entry.path == "README.md" for entry in manifest.files)
        else examples.repository_card()
    )
    return record.model_copy(update={"manifest_digest": hashlib.sha256(dump(manifest)).hexdigest()})


def read_card(layout, manifest, **options):
    return read_repository_card(
        layout,
        manifest.identity,
        CommitSha(manifest.commit_sha),
        PublicationId(manifest.publication_id),
        examples.ARCHIVE_ID,
        **options,
    )


@pytest.mark.parametrize("version", [True, "1", 0, 2, None])
def test_card_schema_is_independent_and_strict(version):
    payload = examples.repository_card().to_payload()
    payload["schema_version"] = version
    with pytest.raises(ValidationError):
        RepositoryCard.model_validate(payload)
    with pytest.raises(IntegrityError):
        parse_record(RepositoryCard, json.dumps(payload).encode())


@pytest.mark.parametrize(
    "update",
    [
        {"state": "not_captured"},
        {"source_path": "../README.md"},
        {"source_path": "subdir/README.md"},
        {"source_path": "readme.md"},
        {"expected_source_sha256": None},
        {"source_path": None},
        {"markdown": None},
        {"presentation_sha256": None},
        {"presentation_sha256": "0" * 64},
        {"presentation_version": "markdown-2"},
        {"markdown": 1},
        {"diagnostics": ["raw rejected source"]},
        {"diagnostics": ["work_limit", "read_failed"]},
        {"diagnostics": ["work_limit", "work_limit"]},
        {"raw_source": "not a public or durable field"},
    ],
)
def test_present_card_refuses_incoherent_or_arbitrary_fields(update):
    with pytest.raises(ValidationError):
        RepositoryCard.model_validate(present().to_payload() | update)


@pytest.mark.parametrize("state", ["unsupported", "oversize", "unsafe", "failed"])
def test_nonpresent_card_keeps_expected_source_but_withholds_presentation(state):
    payload = present().to_payload()
    payload.update(state=state, markdown=None, presentation_sha256=None)
    record = RepositoryCard.model_validate(payload)
    assert record.source_path == "README.md"
    assert record.expected_source_sha256 == examples.DIGEST
    for field in ("markdown", "presentation_sha256"):
        corrupt = payload | {field: present().to_payload()[field]}
        with pytest.raises(ValidationError):
            RepositoryCard.model_validate(corrupt)
    with pytest.raises(ValidationError):
        RepositoryCard.model_validate(
            payload | {"source_path": None, "expected_source_sha256": None}
        )


def test_absent_requires_both_source_and_presentation_pairs_null():
    record = examples.repository_card()
    assert parse_record(RepositoryCard, dump(record)) == record
    for update in (
        {"source_path": "README.md", "expected_source_sha256": examples.DIGEST},
        {"markdown": "", "presentation_sha256": hashlib.sha256(b"").hexdigest()},
    ):
        with pytest.raises(ValidationError):
            RepositoryCard.model_validate(record.to_payload() | update)
    assert present("").markdown == ""


@pytest.mark.parametrize(
    "markdown",
    [
        "x" * (MAXIMUM_CARD_PRESENTATION_BYTES - 2),
        "é" * (MAXIMUM_CARD_PRESENTATION_BYTES // 2 - 1),
        "\n" * (MAXIMUM_CARD_PRESENTATION_BYTES // 2 - 1),
    ],
)
def test_utf8_and_json_string_limits_are_both_inclusive(markdown):
    assert len(json.dumps(markdown, ensure_ascii=False).encode()) == MAXIMUM_CARD_PRESENTATION_BYTES
    record = present(markdown)
    assert parse_record(RepositoryCard, dump(record)) == record
    with pytest.raises(ValidationError):
        present(markdown + markdown[0])


def test_utf8_and_whole_record_limits_are_independent(monkeypatch):
    with pytest.raises(ValidationError):
        present("😀" * (MAXIMUM_CARD_PRESENTATION_BYTES // 4 + 1))
    with pytest.raises(ValidationError):
        RepositoryCard.model_validate(present().to_payload() | {"markdown": "\ud800"})
    size = len(dump(present()))
    monkeypatch.setattr(catalog_models, "MAXIMUM_CARD_RECORD_BYTES", size - 1)
    with pytest.raises(ValidationError):
        present()


def test_raw_card_bound_precedes_json_parsing(monkeypatch):
    def forbidden(*args, **options):
        pytest.fail("oversize record reached JSON allocation")

    monkeypatch.setattr(catalog_storage.json, "loads", forbidden)
    with pytest.raises(IntegrityError):
        parse_record(RepositoryCard, b" " * (MAXIMUM_CARD_RECORD_BYTES + 1))


@pytest.mark.parametrize("readme", [False, True])
def test_card_round_trip_preserves_all_old_evidence_and_never_opens_payload(
    archive, readme, monkeypatch
):
    layout = archive[0]
    manifest = publication(archive, readme=readme)
    old = {path: path.read_bytes() for path in layout.root.rglob("*") if path.is_file()}
    card = bound_card(manifest)
    original_open = MetadataReader.open
    tree = layout.repository(manifest.identity).instance(
        CommitSha(manifest.commit_sha), PublicationId(manifest.publication_id)
    )

    def metadata_only(self, path, **options):
        assert not path.is_relative_to(tree), "card storage opened immutable source payload"
        return original_open(self, path, **options)

    monkeypatch.setattr(MetadataReader, "open", metadata_only)
    assert read_card(layout, manifest) is None
    with writer(archive) as store:
        path = store.write(card)
    assert path == layout.repository(manifest.identity).card(
        CommitSha(manifest.commit_sha), PublicationId(manifest.publication_id)
    )
    assert read_card(layout, manifest) == card
    assert {path: path.read_bytes() for path in old} == old
    assert not tuple(layout.transactions.iterdir())


@pytest.mark.parametrize(
    "update",
    [
        {"archive_id": "bbbbbbbb-bbbb-4bbb-bbbb-bbbbbbbbbbbb"},
        {"manifest_digest": "0" * 64},
        {"manifest_path": "published/manifests/unrelated.json"},
        {"publication_generation": 2},
        {"expected_source_sha256": "0" * 64},
        {"repository_id": "other/repository"},
        {"publication_id": "f" * 32},
    ],
)
def test_card_cannot_claim_unrelated_manifest_or_expected_source(archive, update):
    manifest = publication(archive, readme=True)
    with pytest.raises(IntegrityError), writer(archive) as store:
        store.write(bound_card(manifest).model_copy(update=update))
    assert not archive[0].metadata.exists()


@pytest.mark.parametrize("manifest_readme", [False, True])
def test_absent_state_must_agree_with_authoritative_manifest(archive, manifest_readme):
    manifest = publication(archive, readme=manifest_readme)
    card = (examples.repository_card() if manifest_readme else present()).model_copy(
        update={"manifest_digest": hashlib.sha256(dump(manifest)).hexdigest()}
    )
    with pytest.raises(IntegrityError), writer(archive) as store:
        store.write(card)


def test_present_card_cannot_claim_an_oversize_manifest_source(archive):
    manifest = publication(archive, readme=True)
    payload = manifest.to_payload()
    old_size = payload["files"][0]["size"]
    payload["files"][0]["size"] = catalog_models.MAXIMUM_CARD_SOURCE_BYTES + 1
    payload["total_bytes"] += payload["files"][0]["size"] - old_size
    manifest = type(manifest).model_validate(payload)
    path = (
        archive[0]
        .repository(manifest.identity)
        .manifest(CommitSha(manifest.commit_sha), PublicationId(manifest.publication_id))
    )
    path.write_bytes(dump(manifest))
    with pytest.raises(IntegrityError), writer(archive) as store:
        store.write(bound_card(manifest))


@pytest.mark.parametrize("change", ["version", "identity", "extra", "symlink", "oversize"])
def test_prior_unsupported_unsafe_or_oversize_card_is_preserved(archive, change):
    layout = archive[0]
    manifest = publication(archive, readme=True)
    card = bound_card(manifest)
    with writer(archive) as store:
        path = store.write(card)
    payload = card.to_payload()
    if change == "version":
        payload["schema_version"] = 2
    elif change == "identity":
        payload["publication_id"] = "f" * 32
    elif change == "extra":
        payload["unexpected"] = "preserve"
    elif change == "symlink":
        path.unlink()
        target = layout.root / "retained-card.json"
        target.write_bytes(dump(card))
        path.symlink_to(target)
    if change != "symlink":
        raw = json.dumps(payload).encode()
        if change == "oversize":
            raw += b" " * (MAXIMUM_CARD_RECORD_BYTES + 1 - len(raw))
        path.write_bytes(raw)
    before = path.lstat()
    raw = path.read_bytes()
    with pytest.raises((IntegrityError, QueryLimitError)), writer(archive) as store:
        store.write(card)
    assert path.lstat() == before
    assert path.read_bytes() == raw


@pytest.mark.parametrize(
    ("point", "new_visible"),
    [
        ("before_file_fsync", False),
        ("after_file_fsync", False),
        ("before_rename", False),
        ("after_rename", True),
        ("before_directory_fsync", True),
        ("after_directory_fsync", True),
    ],
)
def test_card_crashes_leave_a_whole_old_or_new_record(archive, point, new_visible):
    manifest = publication(archive, readme=True)
    first = bound_card(manifest)
    second = bound_card(manifest, markdown="Changed inert presentation\n")
    with writer(archive) as store:
        path = store.write(first)

        def fail(checkpoint):
            if checkpoint == point:
                msg = "injected independent card write failure"
                raise OSError(msg)

        with pytest.raises(SafetyError):
            store.write(second, checkpoint=fail)
    assert path.read_bytes() == dump(second if new_visible else first)
    assert read_card(archive[0], manifest) == (second if new_visible else first)


def test_orphan_card_and_missing_adjunct_never_grant_publication_authority(archive):
    layout = archive[0]
    manifest = publication(archive)
    with writer(archive) as store:
        path = store.write(bound_card(manifest))
    original = path.read_bytes()
    layout.repository(manifest.identity).revision_ref(CommitSha(manifest.commit_sha)).unlink()
    with pytest.raises(IntegrityError):
        read_card(layout, manifest)
    assert path.read_bytes() == original
    path.unlink()
    with pytest.raises(IntegrityError):
        read_card(layout, manifest)


@pytest.mark.parametrize(
    "markdown",
    [
        "<script>unexpected()</script>\n",
        "export const active = <Widget />\n",
        "![asset](https://example.invalid/image.png)\n",
        "[unsafe](javascript:unexpected)\n",
        "hf_" + "S" * 24,
        "owned-registered-private-value",
    ],
)
def test_matching_digest_does_not_authorize_unsafe_new_or_existing_presentation(archive, markdown):
    layout = archive[0]
    manifest = publication(archive, readme=True)
    safe = bound_card(manifest)
    unsafe = bound_card(manifest, markdown=markdown)
    register_secret("owned-registered-private-value")
    try:
        with pytest.raises(IntegrityError), writer(archive) as store:
            store.write(unsafe)
        assert not layout.metadata.exists()
        with writer(archive) as store:
            path = store.write(safe)
        path.write_bytes(dump(unsafe))
        before, raw = path.lstat(), path.read_bytes()
        with pytest.raises(IntegrityError) as failure:
            read_card(layout, manifest)
        assert markdown not in str(failure.value)
        with pytest.raises(IntegrityError), writer(archive) as store:
            store.write(safe)
        assert path.lstat() == before
        assert path.read_bytes() == raw
    finally:
        clear_registered_secrets()


def test_card_work_budget_is_shared_across_writer_new_and_prior_record_reads(archive):
    manifest = publication(archive, readme=True)
    card = bound_card(manifest)
    budget = ExtractionBudget()
    layout, settings, table = archive
    with storage.exclusive_lock(
        layout.root.parent / "card-budget.lock", command="catalog refresh", wait_seconds=0
    ):
        store = catalog_storage.CatalogWriter(
            layout, storage=settings, table=table, card_budget=budget
        )
        assert store.card_budget is budget
        path = store.write(card)
        spent = budget.work
        assert spent > 0
        store.write(card)
        assert budget.work > 2 * spent, "the prior presentation shares the new-record budget"
        raw, before = path.read_bytes(), path.lstat()
        budget.maximum_work = budget.work
        with pytest.raises(QueryLimitError) as failure:
            store.write(card)
        assert failure.value.problems[0].code == "HFAPI005"
    assert path.read_bytes() == raw
    assert path.lstat() == before
    with pytest.raises(QueryLimitError):
        read_card(archive[0], manifest, card_budget=ExtractionBudget(maximum_work=1))
    assert read_card(archive[0], manifest) == card
