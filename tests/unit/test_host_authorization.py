"""Basic helper admission/dispatch, with unit status fakes (decision150).

These tests never open the archive or claim installed helper/platform acceptance.
"""

import asyncio
import copy
import threading
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from starlette.requests import Request

from hfcache import locking
from hfcache.api.auth import AuthenticationMethod, CredentialClass, Principal
from hfcache.api.command_models import DiagnosticsSubmission, PlanSubmission
from hfcache.api.host_authorization import (
    authorize_request,
    require_admission,
    required_actions,
)
from hfcache.api.runner import OperationRunner
from hfcache.errors import AuthorizationError, HostAdministrationUnavailableError, OperationError
from hfcache.host_models import HOST_ACTIONS, HOST_UNITS, unavailable_host_status
from hfcache.host_protocol import HostProtocolError
from hfcache.server_config import InstalledPolicy
from hfcache.services.context import ExecutionContext, ServiceResult
from tests.fixtures import examples
from tests.intent_fixtures import OperationStore

BASIC = Principal(
    CredentialClass.REST_WRITER,
    authentication_method=AuthenticationMethod.BASIC,
    subject="host-boundary-administrator",
)
BEARER = Principal(CredentialClass.REST_WRITER)


def status(*, denied=(), deployment="a" * 64, policy="b" * 64):
    grants = {name: name not in denied for name in HOST_ACTIONS}
    return {
        "schema_version": 1,
        "state": "supported",
        "reason": None,
        "profile": "native",
        "binding": {
            "deployment_sha256": deployment,
            "policy_sha256": policy,
            "release_version": "0.2.2",
            "source_commit": "c" * 40,
            "source_snapshot_sha256": "d" * 64,
            "source_dirty": True,
            "archive_id": examples.ARCHIVE_ID,
            "archive_root": "/srv/hfcache",
        },
        "permissions": grants,
        "permission_reasons": {
            name: "granted" if grant else "policy-denied" for name, grant in grants.items()
        },
        "facts": {
            "guard": "inactive",
            "archive_mount": "nfs-rw",
            "units": {
                name: {"load": "loaded", "active": "inactive", "unit_file": "disabled"}
                for name in HOST_UNITS
            },
            "sync_schedule": {
                "state": "unavailable",
                "reason": "facts-unavailable",
                "revision": None,
                "source": None,
                "on_calendar": None,
                "randomized_delay_sec": None,
            },
        },
    }


class StatusClient:
    """Unit-only status source; no transport/peer proof is simulated as real."""

    def __init__(self, value=None):
        self.value: Any
        self.value = status() if value is None else value
        self.async_calls = 0
        self.sync_calls = 0

    def status(self):
        self.sync_calls += 1
        if isinstance(self.value, BaseException):
            raise self.value
        return copy.deepcopy(self.value)

    async def async_status(self):
        self.async_calls += 1
        if isinstance(self.value, BaseException):
            raise self.value
        return copy.deepcopy(self.value)


@pytest.fixture
def configured(tmp_path):
    path = tmp_path / "archive.toml"
    path.write_text(
        'schema_version=1\n[storage]\narchive_root="/srv/hfcache"\n'
        f'archive_id="{examples.ARCHIVE_ID}"\n[sync]\nlock_wait_seconds=100\n'
    )
    return InstalledPolicy(path, Path("/srv/hfcache"), examples.ARCHIVE_ID)


def request(policy, client=None, principal=BASIC):
    app = SimpleNamespace(state=SimpleNamespace(policy=policy, host_helper=client))
    return Request({"type": "http", "app": app, "state": {"principal": principal}})


@pytest.mark.parametrize(
    ("route", "expected"),
    [
        ("plans", {"hub"}),
        ("syncs", {"archive"}),
        ("verifications", {"archive"}),
        ("repairs", {"archive"}),
        ("prune-plans", {"control"}),
        ("purge-plans", {"control"}),
        ("recovery-plans", {"control"}),
        ("quarantine-plans", {"control"}),
        ("prunes", {"archive"}),
        ("purges", {"archive"}),
        ("recoveries", {"archive"}),
        ("quarantine-cleanups", {"archive"}),
        ("catalog/refreshes", {"archive"}),
        ("archive/initializations", None),
        ("future-effect", None),
        ("config/validate", None),
    ],
)
def test_closed_registered_action_map(route, expected):
    assert required_actions("/api/v1/" + route, PlanSubmission()) == expected


@pytest.mark.parametrize("read_only", [True, False])
def test_doctor_requires_both_categories_for_probing(read_only):
    assert required_actions("/api/v1/diagnostics", DiagnosticsSubmission(read_only=read_only)) == (
        {"hub"} if read_only else {"hub", "archive"}
    )
    assert required_actions("/api/v1/diagnostics", PlanSubmission()) is None


def test_bearer_has_no_helper_dependency_even_for_unmapped_work(configured):
    client = StatusClient(RuntimeError("must never be called"))
    assert asyncio.run(authorize_request(request(configured, client, BEARER), None)) is None
    require_admission(request(configured, client, BEARER), "/future", PlanSubmission(), None)
    assert client.async_calls == client.sync_calls == 0


@pytest.mark.parametrize("actions", [None, frozenset(), frozenset({"arbitrary"})])
def test_basic_unmapped_effect_refuses_without_helper_call(configured, actions):
    client = StatusClient()
    with pytest.raises(AuthorizationError):
        asyncio.run(authorize_request(request(configured, client), actions))
    assert client.async_calls == 0


@pytest.mark.parametrize(
    "value",
    [
        None,
        unavailable_host_status().model_dump(mode="json"),
        {"schema_version": True},
        {"unexpected": "never echo this"},
        HostProtocolError("timeout"),
        OSError("private OS detail"),
    ],
)
def test_missing_unknown_malformed_or_transport_failure_is_unavailable(configured, value):
    client = None if value is None else StatusClient(value)
    with pytest.raises(HostAdministrationUnavailableError) as caught:
        asyncio.run(authorize_request(request(configured, client), frozenset({"hub"})))
    assert caught.value.status_code == 503
    assert caught.value.problems[0].code == "HFAPI022"
    assert "private" not in str(caught.value)
    assert "echo" not in str(caught.value)


def test_known_denial_requires_all_doctor_grants(configured):
    client = StatusClient(status(denied={"archive"}))
    with pytest.raises(AuthorizationError):
        asyncio.run(authorize_request(request(configured, client), frozenset({"hub", "archive"})))
    assert client.async_calls == 1


def test_admission_matches_startup_archive_even_when_duplicate_skips_snapshot(configured):
    client = StatusClient()
    wrong = InstalledPolicy(configured.path, Path("/different"), examples.ARCHIVE_ID)
    with pytest.raises(HostAdministrationUnavailableError):
        asyncio.run(authorize_request(request(wrong, client), frozenset({"hub"})))


def test_proof_is_frozen_and_checks_snapshot_without_new_helper_io(configured):
    client = StatusClient()
    proof = asyncio.run(authorize_request(request(configured, client), frozenset({"hub"})))
    assert proof is not None
    client.value["permissions"]["hub"] = False
    proof.check_snapshot(configured.snapshot())
    assert proof.actions == frozenset({"hub"})
    assert client.sync_calls == 0
    with pytest.raises(AttributeError):
        setattr(proof, "actions", frozenset({"archive"}))  # noqa: B010 - frozen mutation refusal
    with pytest.raises(AuthorizationError):
        require_admission(request(configured, client), "/api/v1/plans", PlanSubmission(), None)
    with pytest.raises(AuthorizationError):
        require_admission(request(configured, client), "/api/v1/syncs", PlanSubmission(), proof)


@pytest.mark.parametrize("change", ["revoked", "unavailable", "deployment", "transport"])
def test_dispatch_reads_fresh_authority_not_admission_permissions(configured, change):
    client = StatusClient()
    proof = asyncio.run(authorize_request(request(configured, client), frozenset({"hub"})))
    assert proof is not None
    client.value = {
        "revoked": status(denied={"hub"}),
        "unavailable": unavailable_host_status().model_dump(mode="json"),
        "deployment": status(deployment="e" * 64),
        "transport": HostProtocolError("timeout"),
    }[change]
    with pytest.raises(
        AuthorizationError if change == "revoked" else HostAdministrationUnavailableError
    ):
        proof.recheck(configured.snapshot())
    assert client.async_calls == client.sync_calls == 1


def test_fresh_policy_hash_change_can_retain_an_explicit_grant(configured):
    client = StatusClient()
    proof = asyncio.run(authorize_request(request(configured, client), frozenset({"hub"})))
    assert proof is not None
    client.value = status(policy="e" * 64)
    proof.recheck(configured.snapshot())
    assert client.sync_calls == 1


def test_basic_duplicate_post_checks_again_but_original_lookup_stays_available(
    configured, tmp_path
):
    client = StatusClient()
    req = request(configured, client)
    with (
        OperationStore(tmp_path / "operations") as store,
        OperationRunner(store, configured) as runner,
    ):
        proof = asyncio.run(authorize_request(req, frozenset({"hub"})))
        assert proof is not None
        first = runner.submit(
            BASIC,
            "same-key",
            "/api/v1/plans",
            {},
            command="plan",
            execute=lambda *_: ServiceResult("plan", {}),
            wait_seconds=10,
            requires_lock=False,
            authorize=proof.recheck,
        )
        runner.wait(first.receipt.operation_id, timeout=3)
        client.value = status(denied={"hub"})
        with pytest.raises(AuthorizationError):
            asyncio.run(authorize_request(req, frozenset({"hub"})))
        assert store.lookup(BASIC, "same-key").operation_id == first.receipt.operation_id
        assert len(store.list()) == 1
        assert client.async_calls == 2


def test_queued_revocation_fails_original_receipt_without_verifier_or_reconcile(
    configured, tmp_path
):
    entered, release = threading.Event(), threading.Event()
    executed, reconciled = [], []
    client = StatusClient()
    proof = asyncio.run(authorize_request(request(configured, client), frozenset({"archive"})))
    assert proof is not None
    with OperationStore(tmp_path / "operations") as store:
        runner = OperationRunner(store, configured, check_verification_available=lambda: None)
        runner.start(reconcile=lambda receipt: reconciled.append(receipt.operation_id))
        try:

            def forbidden_execute(*_):
                executed.append(True)
                return ServiceResult("verify", {})

            def hold(*_):
                entered.set()
                assert release.wait(3)
                return ServiceResult("hold", {})

            first = runner.submit(
                BEARER,
                "hold",
                "/api/v1/plans",
                {},
                command="hold",
                execute=hold,
                wait_seconds=10,
                requires_lock=False,
            )
            assert entered.wait(3)
            second = runner.submit(
                BASIC,
                "verify",
                "/api/v1/verifications",
                {},
                command="verify",
                execute=forbidden_execute,
                wait_seconds=10,
                delegated=True,
                authorize=proof.recheck,
            )
            client.value = status(denied={"archive"})
            release.set()
            runner.wait(first.receipt.operation_id, timeout=3)
            outcome = runner.wait(second.receipt.operation_id, timeout=3)
            assert outcome.exit_code == 10
            assert outcome.errors[0].code == "HFAPI002"
            assert store.get(second.receipt.operation_id).state == "failed"
            assert executed == reconciled == []
            assert client.sync_calls == 1
        finally:
            release.set()
            runner.close()


def test_dispatch_helper_holds_no_condition_store_or_domain_lock(configured, tmp_path, monkeypatch):
    monkeypatch.setattr(locking, "LOCK_DIRECTORY", tmp_path / "locks")
    entered, release = threading.Event(), threading.Event()
    completed = []

    def authorize(_):
        entered.set()
        assert release.wait(3)

    with (
        OperationStore(tmp_path / "operations") as store,
        OperationRunner(store, configured) as runner,
    ):
        admitted = runner.submit(
            BASIC,
            "blocked",
            "/api/v1/plans",
            {},
            command="plan",
            execute=lambda *_: ServiceResult("plan", {}),
            wait_seconds=10,
            requires_lock=False,
            authorize=authorize,
        )
        try:
            assert entered.wait(3)

            def inspect():
                store.get(admitted.receipt.operation_id)
                assert runner.pending == 0
                with locking.exclusive_lock(
                    locking.lock_path(), command="independent", wait_seconds=0
                ):
                    completed.append(True)

            observer = threading.Thread(target=inspect)
            observer.start()
            observer.join(timeout=1)
            assert not observer.is_alive()
            assert completed == [True]
        finally:
            release.set()
        assert runner.wait(admitted.receipt.operation_id, timeout=3).exit_code == 0


def test_helper_time_consumes_original_queue_budget_without_dispatch(configured, tmp_path):
    clock = [0.0]
    executed = []

    def authorize(_):
        clock[0] = 2.0

    def forbidden_execute(*_):
        executed.append(True)
        return ServiceResult("plan", {})

    with (
        OperationStore(tmp_path / "operations") as store,
        OperationRunner(store, configured, monotonic=lambda: clock[0]) as runner,
    ):
        admitted = runner.submit(
            BASIC,
            "deadline",
            "/api/v1/plans",
            {},
            command="plan",
            execute=forbidden_execute,
            wait_seconds=1,
            requires_lock=False,
            authorize=authorize,
        )
        outcome = runner.wait(admitted.receipt.operation_id, timeout=3)
        assert outcome.exit_code == 20
        assert outcome.errors[0].code == "HFAPI015"
        assert store.get(admitted.receipt.operation_id).state == "failed"
        assert executed == []


def test_possible_verifier_handoff_keeps_original_reconciliation(configured, tmp_path):
    client = StatusClient()
    proof = asyncio.run(authorize_request(request(configured, client), frozenset({"archive"})))
    assert proof is not None
    outcomes, reconciled = [], []

    def execute(_, context):
        outcomes.append(ServiceResult("verify", {"original_worker": True}).envelope(context))
        client.value = status(denied={"archive"})
        raise OperationError

    def reconcile(receipt):
        reconciled.append(receipt.operation_id)
        return outcomes[0]

    with OperationStore(tmp_path / "operations") as store:
        runner = OperationRunner(store, configured, check_verification_available=lambda: None)
        runner.start(reconcile=reconcile)
        try:
            admitted = runner.submit(
                BASIC,
                "handoff",
                "/api/v1/verifications",
                {},
                command="verify",
                execute=execute,
                wait_seconds=10,
                delegated=True,
                authorize=proof.recheck,
            )
            outcome = runner.wait(admitted.receipt.operation_id, timeout=3)
            assert outcome.data == {"original_worker": True}
            assert reconciled == [admitted.receipt.operation_id]
            assert client.sync_calls == 1
            assert store.get(admitted.receipt.operation_id).state == "succeeded"
        finally:
            runner.close()


def test_recovered_basic_verifier_monitor_never_needs_new_action_authority(configured, tmp_path):
    with OperationStore(tmp_path / "operations") as store:
        old = store.admit(BASIC, "old", "/api/v1/verifications", {}, configured.snapshot).receipt
        context = ExecutionContext.create(operation_id=old.operation_id)
        original = ServiceResult("verify", {"recovered": True}).envelope(context)
        observed = []

        def monitor():
            observed.append(True)
            return original

        runner = OperationRunner(store, configured)
        runner.start(reconcile=lambda _: monitor)
        try:
            assert runner.wait(old.operation_id, timeout=3) == original
            assert observed == [True]
        finally:
            runner.close()


def test_policy_drift_during_helper_wait_is_known_before_verifier_handoff(configured, tmp_path):
    class DriftingStatus(StatusClient):
        def status(self):
            configured.path.write_text(configured.path.read_text() + "max_workers=7\n")
            return super().status()

    client = DriftingStatus()
    proof = asyncio.run(authorize_request(request(configured, client), frozenset({"archive"})))
    assert proof is not None
    executed, reconciled = [], []

    def forbidden(*_):
        executed.append(True)
        return ServiceResult("verify", {})

    with OperationStore(tmp_path / "operations") as store:
        runner = OperationRunner(store, configured, check_verification_available=lambda: None)
        runner.start(reconcile=lambda receipt: reconciled.append(receipt.operation_id))
        try:
            admitted = runner.submit(
                BASIC,
                "drift",
                "/api/v1/verifications",
                {},
                command="verify",
                execute=forbidden,
                wait_seconds=10,
                delegated=True,
                authorize=proof.recheck,
            )
            outcome = runner.wait(admitted.receipt.operation_id, timeout=3)
            assert outcome.errors[0].code == "HFAPI007"
            assert store.get(admitted.receipt.operation_id).state == "failed"
            assert executed == reconciled == []
        finally:
            runner.close()
