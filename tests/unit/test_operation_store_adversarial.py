"""Durable bindings survive races without deleting ambiguous history (INV-014)."""

import fcntl
import json
import multiprocessing
import os
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Barrier, Lock

import pytest

from hfcache.api import operations
from hfcache.api.auth import CredentialClass, Principal
from hfcache.api.operations import OperationLimits, OperationStore
from hfcache.config import ApplicationConfig
from hfcache.errors import HfcacheError
from hfcache.redaction import register_secret
from hfcache.server_config import PolicySnapshot
from hfcache.services.context import ExecutionContext, ServiceResult
from hfcache.storage import atomic_write_bytes

ARCHIVE_ID = "3f2a1c88-7b40-4a2e-9c1d-0e5b6a7f8d90"
KEY = "adversarial-key-0123456789abcdef0123456789abcdef"
WRITER = Principal(CredentialClass.REST_WRITER)
READER = Principal(CredentialClass.REST_READER)
ROUTE = "/api/v1/syncs"
NOW = datetime(2026, 10, 17, 12, 0, tzinfo=UTC)


@pytest.fixture
def snapshot(tmp_path):
    config = ApplicationConfig.model_validate(
        {
            "schema_version": 1,
            "storage": {"archive_root": str(tmp_path / "archive"), "archive_id": ARCHIVE_ID},
        }
    )
    return PolicySnapshot(config, config.fingerprint())


def _admit(store, snapshot, *, route=ROUTE, request=None, principal=WRITER):
    return store.admit(
        principal,
        KEY,
        route,
        {"selectors": ["model:org/repo"]} if request is None else request,
        snapshot=lambda: snapshot,
    )


def _receipt_file(root, operation_id):
    files = list(root.rglob(operation_id + ".json"))
    assert len(files) == 1
    return files[0]


def test_raw_key_and_candidate_request_never_enter_control_files(tmp_path, snapshot):
    root = tmp_path / "state"
    request_secret = "unregistered-opaque-candidate-value-that-must-never-be-written"
    with OperationStore(root) as store:
        admitted = _admit(store, snapshot, request={"candidate_toml": request_secret})
        assert admitted.created
        assert store.lookup(WRITER, KEY).operation_id == admitted.receipt.operation_id

    for path in root.rglob("*"):
        if path.is_file():
            assert KEY.encode() not in path.read_bytes()
            assert request_secret.encode() not in path.read_bytes()
        assert KEY not in path.name
    assert not snapshot.config.storage.archive_root.exists()


def test_reopened_receipt_is_authoritative_before_fresh_policy_resolution(tmp_path, snapshot):
    root = tmp_path / "state"
    with OperationStore(root) as store:
        original = _admit(store, snapshot)

    def unavailable_policy():
        pytest.fail("matching retry resolved new policy before consulting the durable binding")

    with OperationStore(root) as reopened:
        retried = reopened.admit(
            WRITER, KEY, ROUTE, {"selectors": ["model:org/repo"]}, snapshot=unavailable_policy
        )
        assert not retried.created
        assert retried.receipt.operation_id == original.receipt.operation_id
        assert reopened.lookup(WRITER, KEY).operation_id == original.receipt.operation_id


@pytest.mark.parametrize(
    ("route", "payload"),
    [
        ("/api/v1/prunes", {"selectors": ["model:org/repo"]}),
        (ROUTE, {"selectors": ["model:org/other"]}),
    ],
)
def test_reusing_key_for_a_different_route_or_request_is_a_durable_conflict(
    tmp_path, snapshot, route, payload
):
    with OperationStore(tmp_path / "state") as store:
        original = _admit(store, snapshot)
        with pytest.raises(HfcacheError) as failure:
            _admit(store, snapshot, route=route, request=payload)
        assert failure.value.problems[0].code == "HFAPI012"
        assert store.lookup(WRITER, KEY).operation_id == original.receipt.operation_id


def test_identical_raw_keys_are_independent_in_the_caller_class_namespace(tmp_path, snapshot):
    with OperationStore(tmp_path / "state") as store:
        writer = _admit(store, snapshot)
        reader = _admit(store, snapshot, principal=READER)

        assert writer.receipt.operation_id != reader.receipt.operation_id
        assert store.lookup(WRITER, KEY).operation_id == writer.receipt.operation_id
        assert store.lookup(READER, KEY).operation_id == reader.receipt.operation_id


def test_distinct_store_handles_serialize_simultaneous_duplicate_admission(tmp_path, snapshot):
    root = tmp_path / "state"
    barrier = Barrier(8)
    counter_lock = Lock()
    snapshots = 0

    def once():
        nonlocal snapshots
        with counter_lock:
            snapshots += 1
        return snapshot

    with OperationStore(root) as first, OperationStore(root) as second:

        def submit(index):
            barrier.wait(timeout=10)
            return (first if index % 2 else second).admit(
                WRITER, KEY, ROUTE, {"selectors": ["model:org/repo"]}, snapshot=once
            )

        with ThreadPoolExecutor(max_workers=8) as executor:
            admissions = list(executor.map(submit, range(8)))

        assert sum(admission.created for admission in admissions) == 1
        assert len({admission.receipt.operation_id for admission in admissions}) == 1
        assert snapshots == 1
        receipt = admissions[0].receipt
        payload = json.loads(_receipt_file(root, receipt.operation_id).read_text())
        assert payload["operation_id"] == receipt.operation_id


@pytest.mark.parametrize(
    "stage",
    [
        "before_write",
        "before_file_fsync",
        "after_file_fsync",
        "before_rename",
        "after_rename",
        "before_directory_fsync",
        "after_directory_fsync",
    ],
)
def test_lost_admission_acknowledgement_keeps_durable_key_binding(tmp_path, snapshot, stage):
    root = tmp_path / "state"

    class InjectedCrash(BaseException):
        pass

    def crash(name):
        if name == stage:
            raise InjectedCrash

    with OperationStore(root, checkpoint=crash) as store, pytest.raises(InjectedCrash):
        _admit(store, snapshot)

    recorded = [path for path in root.iterdir() if re.fullmatch(r"[0-9a-f]{32}\.json", path.name)]
    if stage in {"after_rename", "before_directory_fsync", "after_directory_fsync"}:
        assert len(recorded) == 1
        original = json.loads(recorded[0].read_text())

        def unavailable_policy():
            pytest.fail("durable lost-acknowledgement retry requested a new policy")

        with OperationStore(root) as reopened:
            retried = reopened.admit(
                WRITER, KEY, ROUTE, {"selectors": ["model:org/repo"]}, snapshot=unavailable_policy
            )
            assert not retried.created
            assert retried.receipt.operation_id == original["operation_id"]
    else:
        assert recorded == []
        before = {path.name: path.read_bytes() for path in root.iterdir() if path.is_file()}
        with OperationStore(root) as reopened, pytest.raises(HfcacheError):
            reopened.lookup(WRITER, KEY)
        assert before == {path.name: path.read_bytes() for path in root.iterdir() if path.is_file()}


@pytest.mark.parametrize(
    "damage",
    [
        "new-version",
        "missing-version",
        "boolean-version",
        "duplicate-field",
        "mcp-principal",
        "malformed",
        "wrong-id",
        "symlink",
        "fifo",
        "directory",
        "hardlink",
        "public-mode",
    ],
)
def test_unsafe_or_unexplained_receipt_is_preserved_and_blocks_new_admission(
    tmp_path, snapshot, damage
):
    root = tmp_path / "state"
    with OperationStore(root) as store:
        receipt = _admit(store, snapshot).receipt
    path = _receipt_file(root, receipt.operation_id)
    body = json.loads(path.read_text())
    changes = {
        "new-version": {"schema_version": 99},
        "boolean-version": {"schema_version": True},
        "mcp-principal": {"principal": "mcp-reader"},
        "wrong-id": {"operation_id": "f" * 32 if receipt.operation_id != "f" * 32 else "e" * 32},
    }
    if damage in changes:
        path.write_text(json.dumps(body | changes[damage]))
    elif damage == "missing-version":
        body.pop("schema_version")
        path.write_text(json.dumps(body))
    elif damage == "duplicate-field":
        path.write_text('{"schema_version":1,' + json.dumps(body)[1:])
    elif damage == "malformed":
        path.write_bytes(b"{malformed-private-receipt")
    elif damage == "symlink":
        outside = tmp_path / "outside"
        path.rename(outside)
        path.symlink_to(outside)
    elif damage == "fifo":
        path.unlink()
        os.mkfifo(path, mode=0o600)
    elif damage == "directory":
        path.unlink()
        path.mkdir(mode=0o700)
    elif damage == "hardlink":
        (tmp_path / "linked-receipt").hardlink_to(path)
    else:
        path.chmod(0o644)
    original = path.lstat()
    raw = path.read_bytes() if damage not in {"fifo", "directory"} else None

    with OperationStore(root) as reopened:
        with pytest.raises(HfcacheError) as failure:
            reopened.get(receipt.operation_id)
        assert failure.value.problems[0].code == "HFAPI014"
        with pytest.raises(HfcacheError):
            reopened.admit(WRITER, KEY + "-other", ROUTE, {}, snapshot=lambda: snapshot)
        with pytest.raises(HfcacheError):
            reopened.expire()

    after = path.lstat()
    assert (after.st_dev, after.st_ino, after.st_mode) == (
        original.st_dev,
        original.st_ino,
        original.st_mode,
    )
    if raw is not None:
        assert path.read_bytes() == raw


def test_unknown_files_never_become_capacity_or_retention_cleanup_targets(tmp_path, snapshot):
    root = tmp_path / "state"
    with OperationStore(root) as store:
        receipt = _admit(store, snapshot).receipt
        unknown = root / "unexplained.tmp-0123456789abcdef"
        unknown.write_bytes(b"operator-evidence-that-must-survive")
        unknown.chmod(0o600)
        before = unknown.read_bytes()
        with pytest.raises(HfcacheError):
            store.expire()
        with pytest.raises(HfcacheError):
            store.admit(WRITER, KEY + "-other", ROUTE, {}, snapshot=lambda: snapshot)
        assert store.get(receipt.operation_id).state == "queued"
        assert unknown.read_bytes() == before


def _complete(store, receipt):
    store.transition(receipt.operation_id, "running")
    envelope = ServiceResult("sync", {"repositories": []}).envelope(ExecutionContext.create())
    return store.transition(receipt.operation_id, "succeeded", envelope=envelope)


def test_expiry_holds_the_common_lock_through_result_validation_and_deletion(
    tmp_path, snapshot, monkeypatch
):
    root = tmp_path / "state"
    now = [NOW]
    with OperationStore(root, clock=lambda: now[0]) as store:
        receipt = _complete(store, _admit(store, snapshot).receipt)
        now[0] += timedelta(days=31)
        original = operations.os.unlink
        checked = []

        def locked_unlink(name, *args, **kwargs):
            if str(name).startswith(receipt.operation_id):
                probe = os.open(root / ".lock", os.O_RDWR)
                try:
                    try:
                        fcntl.flock(probe, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    except BlockingIOError:
                        checked.append(str(name))
                    else:
                        pytest.fail("expiry released its common lock before deleting evidence")
                finally:
                    os.close(probe)
            return original(name, *args, **kwargs)

        monkeypatch.setattr(operations.os, "unlink", locked_unlink)
        assert store.expire() == (receipt.operation_id,)
        assert len(checked) == 2


@pytest.mark.parametrize("state", ["queued", "running", "interrupted", "unexpired-terminal"])
def test_capacity_never_evicts_unexpired_or_ambiguous_history(tmp_path, snapshot, state):
    root = tmp_path / "state"
    now = [NOW]
    with OperationStore(root, limits=OperationLimits(max_records=1), clock=lambda: now[0]) as store:
        receipt = _admit(store, snapshot).receipt
        if state == "unexpired-terminal":
            _complete(store, receipt)
        elif state != "queued":
            store.transition(receipt.operation_id, state)
        before = _receipt_file(root, receipt.operation_id).read_bytes()
        if state != "unexpired-terminal":
            now[0] += timedelta(days=400)
        assert store.expire() == ()
        with pytest.raises(HfcacheError) as failure:
            store.admit(WRITER, KEY + "-new", ROUTE, {}, snapshot=lambda: snapshot)
        assert int(failure.value.exit_code) == 20
        assert _receipt_file(root, receipt.operation_id).read_bytes() == before


@pytest.mark.parametrize("damage", ["missing", "changed", "symlink"])
def test_expired_terminal_with_unavailable_result_is_preserved(tmp_path, snapshot, damage):
    root = tmp_path / "state"
    now = [NOW]
    with OperationStore(root, clock=lambda: now[0]) as store:
        receipt = _complete(store, _admit(store, snapshot).receipt)
        authority = _receipt_file(root, receipt.operation_id)
        original = authority.read_bytes()
        result = root / (receipt.operation_id + ".result.json")
        if damage == "missing":
            result.unlink()
        elif damage == "changed":
            result.write_bytes(b"changed-result-evidence")
        else:
            outside = tmp_path / "outside-result"
            result.rename(outside)
            result.symlink_to(outside)
        now[0] += timedelta(days=31)
        with pytest.raises(HfcacheError):
            store.result(receipt.operation_id)
        with pytest.raises(HfcacheError):
            store.expire()
        assert authority.read_bytes() == original


def test_bounded_events_keep_explicit_gap_and_never_persist_registered_secrets(tmp_path, snapshot):
    root = tmp_path / "state"
    secret = "operation-private-opaque-value-0123456789abcdef"
    register_secret(secret)
    with OperationStore(root, limits=OperationLimits(max_events=2)) as store:
        receipt = _admit(store, snapshot).receipt
        for index in range(3):
            store.append_event(receipt.operation_id, "progress", f"phase {index}: {secret}")
        before = _receipt_file(root, receipt.operation_id).read_bytes()
        page = store.events(receipt.operation_id, after=0, limit=2)
        assert tuple(event.sequence for event in page.events) == (2, 3)
        assert page.oldest_sequence == 2
        assert page.next_cursor == 3
        assert page.truncated
        assert secret.encode() not in before
        assert _receipt_file(root, receipt.operation_id).read_bytes() == before
        assert store.get(receipt.operation_id).state == "queued"


@pytest.mark.parametrize("mode", [0o750, 0o755, 0o770, 0o777])
def test_existing_nonprivate_state_directory_is_refused_without_chmod(tmp_path, mode):
    root = tmp_path / "state"
    root.mkdir()
    root.chmod(mode)
    evidence = root / "operator-evidence"
    evidence.write_bytes(b"preserve-existing-state")

    with pytest.raises(HfcacheError):
        OperationStore(root)

    assert root.stat().st_mode & 0o777 == mode
    assert evidence.read_bytes() == b"preserve-existing-state"


def test_state_parent_symlink_cannot_redirect_or_create_control_files(tmp_path):
    target = tmp_path / "target"
    target.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(target, target_is_directory=True)

    with pytest.raises(HfcacheError):
        OperationStore(alias / "state")

    assert list(target.iterdir()) == []


def test_replaced_lock_name_cannot_create_independent_admission_authorities(tmp_path, snapshot):
    root = tmp_path / "state"
    with OperationStore(root) as store:
        receipt = _admit(store, snapshot).receipt
        original = (root / ".lock").stat()
        (root / ".lock").rename(root / "retained-original-lock")
        replacement = root / ".lock"
        replacement.touch(mode=0o600)
        with pytest.raises(HfcacheError):
            _admit(store, snapshot)
        assert (root / "retained-original-lock").stat().st_ino == original.st_ino
        assert _receipt_file(root, receipt.operation_id).exists()


def _process_admission(root, config_payload, barrier, results):
    config = ApplicationConfig.model_validate(config_payload)
    snapshot = PolicySnapshot(config, config.fingerprint())
    with OperationStore(Path(root)) as store:
        barrier.wait(timeout=20)
        admitted = _admit(store, snapshot)
        results.put((admitted.receipt.operation_id, admitted.created))


def test_spawned_processes_share_one_durable_idempotent_admission(tmp_path, snapshot, monkeypatch):
    # Spawn must be able to import this pytest importlib-mode module by name.
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2]))
    context = multiprocessing.get_context("spawn")
    barrier = context.Barrier(3)
    results = context.Queue()
    root = tmp_path / "state"
    processes = [
        context.Process(
            target=_process_admission,
            args=(str(root), snapshot.config.model_dump(mode="json"), barrier, results),
        )
        for _ in range(3)
    ]
    try:
        for process in processes:
            process.start()
        admitted = [results.get(timeout=30) for _ in processes]
        for process in processes:
            process.join(timeout=10)
            assert process.exitcode == 0
        assert len({operation_id for operation_id, _ in admitted}) == 1
        assert sum(created for _, created in admitted) == 1
        with OperationStore(root) as store:
            assert store.lookup(WRITER, KEY).operation_id == admitted[0][0]
    finally:
        for process in processes:
            if process.is_alive():
                process.terminate()
            process.join(timeout=10)
        results.close()
        results.join_thread()


def test_atomic_write_collision_preserves_the_unexplained_existing_inode(tmp_path, monkeypatch):
    root = tmp_path / "state"
    root.mkdir(mode=0o700)
    temporary = root / "receipt.json.tmp-0123456789abcdef"
    temporary.write_bytes(b"pre-existing-operator-evidence")
    before = temporary.stat()
    monkeypatch.setattr("hfcache.storage.temporary_sibling", lambda _: Path(temporary.name))
    descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
    try:
        with pytest.raises(FileExistsError):
            atomic_write_bytes(Path("receipt.json"), b"new-receipt", mode=0o600, dir_fd=descriptor)
    finally:
        os.close(descriptor)

    assert temporary.read_bytes() == b"pre-existing-operator-evidence"
    assert temporary.stat().st_ino == before.st_ino
    assert not (root / "receipt.json").exists()


def test_atomic_failure_cleanup_preserves_a_replacement_temp_inode(tmp_path, monkeypatch):
    root = tmp_path / "state"
    root.mkdir(mode=0o700)
    temporary = root / "receipt.json.tmp-0123456789abcdef"
    retained = root / "retained-original-temp"
    monkeypatch.setattr("hfcache.storage.temporary_sibling", lambda _: Path(temporary.name))

    def replace(name):
        if name == "before_file_fsync":
            temporary.rename(retained)
            temporary.write_bytes(b"replacement-operator-evidence")
            message = "injected write failure after pathname replacement"
            raise OSError(message)

    descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
    try:
        with pytest.raises(OSError, match="injected write failure"):
            atomic_write_bytes(
                Path("receipt.json"),
                b"new-receipt",
                mode=0o600,
                dir_fd=descriptor,
                checkpoint=replace,
            )
    finally:
        os.close(descriptor)

    assert temporary.read_bytes() == b"replacement-operator-evidence"
    assert retained.read_bytes() == b"new-receipt"
    assert not (root / "receipt.json").exists()
