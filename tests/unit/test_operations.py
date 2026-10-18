"""Receipt authority, independent schemas and non-resuming lifecycle (INV-014)."""

import errno
from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from hfcache.api.auth import CredentialClass, Principal
from hfcache.api.operations import OperationLimits, OperationReceipt, OperationStore, request_digest
from hfcache.config import load_config
from hfcache.errors import OperationError
from hfcache.models import dump
from hfcache.reporting import Envelope, EnvelopeProblem
from hfcache.server_config import PolicySnapshot
from tests.fixtures import examples

WRITER = Principal(CredentialClass.REST_WRITER)
READER = Principal(CredentialClass.REST_READER)
ROUTE = "/api/v1/sync"


@pytest.fixture
def snapshot(tmp_path):
    policy = tmp_path / "archive.toml"
    policy.write_text(
        f'schema_version=1\n[storage]\narchive_root="{tmp_path / "archive"}"\n'
        f'archive_id="{examples.ARCHIVE_ID}"\n'
    )
    config = load_config(policy)
    return lambda: PolicySnapshot(config, config.fingerprint())


def envelope(*, failed=False):
    return Envelope(
        command="sync",
        completed_at="2026-10-17T12:00:00.000000Z",
        started_at="2026-10-17T11:59:00.000000Z",
        run_id=examples.RUN,
        exit_code=40 if failed else 0,
        outcome="failed" if failed else "success",
        errors=(EnvelopeProblem(code="HFVER007", message="integrity finding"),) if failed else (),
        data={"partial": True} if failed else {"repositories": []},
    )


def test_canonical_binding_precedes_new_policy_and_has_no_raw_request_or_key(tmp_path, snapshot):
    key = "submission-key-42"
    secret = "candidate-secret-not-an-api-token"
    with OperationStore(tmp_path / "state") as store:
        first = store.admit(WRITER, key, ROUTE, {"z": secret, "a": 1}, snapshot)
        assert first.created

        def invalid_policy():
            pytest.fail("retry attempted fresh policy validation")

        retry = store.admit(WRITER, key, ROUTE, {"a": 1, "z": secret}, invalid_policy)
        assert not retry.created
        assert retry.receipt == first.receipt
        assert store.lookup(WRITER, key) == first.receipt
        raw = (tmp_path / "state" / (first.receipt.operation_id + ".json")).read_bytes()
        assert key.encode() not in raw
        assert secret.encode() not in raw
        assert raw == dump(first.receipt)


@pytest.mark.parametrize("failed", [False, True])
def test_terminal_results_preserve_exact_domain_envelope_and_run_identity(
    tmp_path, snapshot, failed
):
    with OperationStore(tmp_path / "state") as store:
        admitted = store.admit(WRITER, "key", ROUTE, {}, snapshot).receipt
        store.transition(admitted.operation_id, "waiting_lock")
        store.transition(admitted.operation_id, "running")
        result = envelope(failed=failed)
        terminal = store.transition(
            admitted.operation_id,
            "failed" if failed else "succeeded",
            envelope=result,
            transaction_ids=(examples.TRANSACTION,),
        )
        assert store.result(admitted.operation_id) == result
        assert terminal.domain_run_id == result.run_id
        assert terminal.operation_id != terminal.domain_run_id
        assert terminal.transaction_ids == (examples.TRANSACTION,)
        assert terminal.result is not None
        assert terminal.result.operation_id == admitted.operation_id
        assert store.lookup(WRITER, "key") == terminal
        assert store.list() == (terminal,)
    with OperationStore(tmp_path / "state") as reopened:
        assert reopened.result(admitted.operation_id) == result
        assert reopened.interrupt_unfinished() == ()


def test_reader_namespace_and_startup_classification_never_replay(tmp_path, snapshot):
    with OperationStore(tmp_path / "state") as store:
        writer = store.admit(WRITER, "same", ROUTE, {}, snapshot).receipt
        reader = store.admit(READER, "same", "/api/v1/plan", {}, snapshot).receipt
        assert writer.operation_id != reader.operation_id
        assert store.lookup(READER, "same") == reader
        interrupted = store.interrupt_unfinished()
        assert set(interrupted) == {writer.operation_id, reader.operation_id}
        assert store.interrupt_unfinished() == ()
        assert store.lookup(WRITER, "same").state == "interrupted"
        with pytest.raises(OperationError) as caught:
            store.transition(writer.operation_id, "running")
        assert caught.value.problems[0].code == "HFAPI015"
        assert caught.value.exit_code == 20


def test_events_are_sequenced_bounded_suffix_with_explicit_gap(tmp_path, snapshot):
    limits = OperationLimits(max_events=2)
    with OperationStore(tmp_path / "state", limits=limits) as store:
        receipt = store.admit(WRITER, "key", ROUTE, {}, snapshot).receipt
        for number in range(4):
            store.append_event(receipt.operation_id, "progress", str(number))
        page = store.events(receipt.operation_id, after=0, limit=1)
        assert page.truncated
        assert page.oldest_sequence == 3
        assert [event.sequence for event in page.events] == [3]
        second = store.events(receipt.operation_id, after=page.next_cursor, limit=2)
        assert [event.sequence for event in second.events] == [4]
        assert not second.truncated
        assert second.next_cursor == 4


def test_expiry_requires_explicit_terminal_proof_and_never_ages_interrupted(tmp_path, snapshot):
    moment = [datetime(2026, 10, 17, tzinfo=UTC)]
    with OperationStore(tmp_path / "state", clock=lambda: moment[0]) as store:
        done = store.admit(WRITER, "done", ROUTE, {}, snapshot).receipt
        unfinished = store.admit(WRITER, "unfinished", ROUTE, {}, snapshot).receipt
        store.transition(done.operation_id, "running")
        store.transition(done.operation_id, "succeeded", envelope=envelope())
        store.interrupt_unfinished()
        moment[0] += timedelta(days=29)
        assert store.expire() == ()
        moment[0] += timedelta(days=2)
        assert store.expire() == (done.operation_id,)
        assert store.get(unfinished.operation_id).state == "interrupted"
        with pytest.raises(OperationError) as caught:
            store.lookup(WRITER, "done")
        assert caught.value.problems[0].code == "HFAPI013"
        assert caught.value.exit_code == 20


@pytest.mark.parametrize(
    "change",
    [
        {"schema_version": 2},
        {"schema_version": True},
        {"unexpected": 1},
        {"state": "succeeded"},
        {"next_event_sequence": 9},
        {"state": "interrupted"},
    ],
)
def test_operation_schema_rejects_incompatible_and_contradictory_records(change):
    payload = examples.operation_receipt().model_dump()
    with pytest.raises(ValidationError):
        OperationReceipt.model_validate(payload | change)


def test_request_digest_is_order_independent_and_route_specific():
    assert request_digest(ROUTE, {"b": 2, "a": 1}) == request_digest(ROUTE, {"a": 1, "b": 2})
    assert request_digest(ROUTE, {}) != request_digest("/api/v1/repair", {})


def test_known_unfinished_result_differs_from_missing_history(tmp_path, snapshot):
    with OperationStore(tmp_path / "state") as store:
        receipt = store.admit(WRITER, "key", ROUTE, {}, snapshot).receipt
        with pytest.raises(OperationError) as pending:
            store.result(receipt.operation_id)
        with pytest.raises(OperationError) as missing:
            store.result("f" * 32)
        assert pending.value.status_code == 409
        assert pending.value.problems[0].code == "HFAPI015"
        assert missing.value.status_code == 404
        assert missing.value.problems[0].code == "HFAPI013"


def test_control_schema_version_is_independent_of_archive_version(monkeypatch):
    monkeypatch.setattr("hfcache.models.SCHEMA_VERSION", 9)
    receipt = examples.operation_receipt()
    assert receipt.schema_version == 1
    assert OperationReceipt.model_validate_json(dump(receipt)) == receipt


def test_generated_id_collision_preserves_original_binding(tmp_path, snapshot, monkeypatch):
    with OperationStore(tmp_path / "state") as store:
        first = store.admit(WRITER, "one", ROUTE, {}, snapshot).receipt
        monkeypatch.setattr(
            "hfcache.api.operations.secrets.token_hex", lambda _: first.operation_id
        )
        with pytest.raises(OperationError):
            store.admit(WRITER, "two", ROUTE, {}, snapshot)
        assert store.get(first.operation_id) == first
        assert store.lookup(WRITER, "one") == first


def test_terminal_identity_refusal_does_not_publish_result(tmp_path, snapshot):
    with OperationStore(tmp_path / "state") as store:
        receipt = store.admit(WRITER, "key", ROUTE, {}, snapshot).receipt
        store.transition(receipt.operation_id, "running")
        with pytest.raises(OperationError):
            store.transition(
                receipt.operation_id, "succeeded", envelope=envelope(), domain_run_id="f" * 32
            )
        assert store.get(receipt.operation_id).state == "running"
        assert not (tmp_path / "state" / (receipt.operation_id + ".result.json")).exists()


@pytest.mark.parametrize("replacement", ["domain", "transactions"])
def test_transitions_never_replace_previously_bound_domain_evidence(
    tmp_path, snapshot, replacement
):
    with OperationStore(tmp_path / "state") as store:
        receipt = store.admit(WRITER, "key", ROUTE, {}, snapshot).receipt
        known = store.transition(
            receipt.operation_id,
            "running",
            domain_run_id=examples.RUN,
            transaction_ids=(examples.TRANSACTION,),
        )
        result = envelope()
        if replacement == "domain":
            result = result.model_copy(update={"run_id": "f" * 32})
            transaction_ids = (examples.TRANSACTION,)
        else:
            transaction_ids = ("f" * 32,)
        with pytest.raises(OperationError) as caught:
            store.transition(
                receipt.operation_id, "succeeded", envelope=result, transaction_ids=transaction_ids
            )
        assert caught.value.problems[0].code == "HFAPI015"
        assert store.get(receipt.operation_id) == known
        assert not (tmp_path / "state" / (receipt.operation_id + ".result.json")).exists()
        final = store.transition(
            receipt.operation_id,
            "succeeded",
            envelope=envelope(),
            transaction_ids=(examples.TRANSACTION, "e" * 32),
        )
        assert final.transaction_ids == (examples.TRANSACTION, "e" * 32)


@pytest.mark.parametrize("phase", ["admission", "result"])
def test_fsync_disk_full_refuses_acknowledgement_and_preserves_binding(
    tmp_path,
    snapshot,
    monkeypatch,
    phase,
):
    with OperationStore(tmp_path / "state") as store:
        known = None
        if phase == "result":
            known = store.admit(WRITER, "key", ROUTE, {}, snapshot).receipt
            known = store.transition(known.operation_id, "running")

        def full(_):
            message = "injected filesystem capacity exhaustion"
            raise OSError(errno.ENOSPC, message)

        def attempt():
            if known is None:
                store.admit(WRITER, "key", ROUTE, {}, snapshot)
            else:
                store.transition(known.operation_id, "succeeded", envelope=envelope())

        with monkeypatch.context() as failure:
            failure.setattr("hfcache.storage.os.fsync", full)
            with pytest.raises(OperationError) as caught:
                attempt()
        assert caught.value.problems[0].code == "HFAPI014"
        assert caught.value.exit_code == 20
        if known is None:
            assert store.list() == ()
        else:
            assert store.get(known.operation_id) == known
            assert store.lookup(WRITER, "key") == known
            assert not (tmp_path / "state" / (known.operation_id + ".result.json")).exists()
