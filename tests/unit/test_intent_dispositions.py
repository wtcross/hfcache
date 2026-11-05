"""INV-023: durable key closure, exact observation and independent lease ownership."""

import errno
import json
import os
import subprocess
import sys
import threading
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from pydantic import ValidationError

from hfcache.api import intent_activation as activation
from hfcache.api.auth import AuthenticationMethod, CredentialClass, Principal
from hfcache.api.intent_activation import prepare_intent_state
from hfcache.api.intents import INTENT_NAME, IntentInterlock, IntentState
from hfcache.api.operations import OperationStore as UnactivatedStore
from hfcache.api.operations import request_digest
from hfcache.errors import OperationError, RequestError
from hfcache.server_config import validate_server_config_mapping
from tests.fixtures import examples
from tests.intent_fixtures import OperationStore
from tests.unit.test_operations import ROUTE, WRITER, envelope
from tests.unit.test_operations import (
    snapshot as snapshot,  # noqa: PLC0414 - register shared fixture
)

BASIC = Principal(
    CredentialClass.REST_WRITER,
    authentication_method=AuthenticationMethod.BASIC,
    subject="administrator",
)
FOREIGN = Principal(
    CredentialClass.REST_WRITER,
    authentication_method=AuthenticationMethod.BASIC,
    subject="different-administrator",
)


def refused(store, key="original", principal=BASIC):
    return store.refuse(
        principal, key, ROUTE, {"selectors": []}, examples.ARCHIVE_ID, "permission_denied"
    )


@pytest.mark.parametrize("version", [True, 1.0, "1", 0, 2])
def test_versions_are_strict_before_literal_equality(version):
    with pytest.raises(ValidationError):
        IntentState.model_validate(
            {"schema_version": version, "archive_id": examples.ARCHIVE_ID, "entries": []}
        )


def test_fence_is_permanent_key_wide_namespaced_and_secret_free(tmp_path, snapshot):
    with OperationStore(tmp_path / "api") as store:
        assert store.intent(BASIC, "original", examples.ARCHIVE_ID) == (None, None)
        record, closed = refused(store)
        assert record is None
        assert closed is not None
        assert closed.request_digest == request_digest(ROUTE, {"selectors": []})
        assert closed == refused(store)[1]
        with pytest.raises(OperationError):
            store.admit(BASIC, "original", "/api/v1/another", {}, snapshot)
        assert store.admit(FOREIGN, "original", ROUTE, {}, snapshot).created
        assert store.admit(WRITER, "original", ROUTE, {}, snapshot).created
        raw = (store.root / INTENT_NAME).read_bytes()
        assert b'"original"' not in raw
        assert b"administrator" not in raw
        assert "key_digest" not in closed.projection(examples.ARCHIVE_ID)
        store.expire()
    with UnactivatedStore(tmp_path / "api") as store:
        assert store.intent(BASIC, "original", examples.ARCHIVE_ID)[1] == closed
        with pytest.raises(OperationError):
            store.admit(BASIC, "original", ROUTE, {}, snapshot)


def test_existing_admission_wins_denial_and_conflicts_stay_conflicts(tmp_path, snapshot):
    with OperationStore(tmp_path / "api") as store:
        admitted = store.admit(BASIC, "original", ROUTE, {"selectors": []}, snapshot)
        assert refused(store) == (admitted.receipt, None)
        with pytest.raises(RequestError):
            store.refuse(
                BASIC, "original", "/api/v1/changed", {}, examples.ARCHIVE_ID, "permission_denied"
            )
        assert (
            IntentState.model_validate_json((store.root / INTENT_NAME).read_bytes()).entries == ()
        )


def test_cross_handle_admission_rechecks_after_fresh_refusal(tmp_path, snapshot):
    with OperationStore(tmp_path / "api") as first, UnactivatedStore(tmp_path / "api") as second:
        ready, proceed = threading.Event(), threading.Event()
        errors = []

        def slow_snapshot():
            ready.set()
            assert proceed.wait(5)
            return snapshot()

        def admit():
            try:
                first.admit(BASIC, "original", ROUTE, {"selectors": []}, slow_snapshot)
            except OperationError as error:
                errors.append(error)

        thread = threading.Thread(target=admit)
        thread.start()
        assert ready.wait(5)
        closed = refused(second)[1]
        proceed.set()
        thread.join(5)
        assert not thread.is_alive()
        assert len(errors) == 1
        assert first.intent(BASIC, "original", examples.ARCHIVE_ID) == (None, closed)
        assert first.list() == ()


def test_admission_wins_concurrent_denial_after_fresh_check(tmp_path, snapshot):
    with OperationStore(tmp_path / "api") as first, UnactivatedStore(tmp_path / "api") as second:
        admission = second.admit(BASIC, "original", ROUTE, {"selectors": []}, snapshot)
        assert refused(first) == (admission.receipt, None)


@pytest.mark.parametrize("problem", ["missing", "corrupt", "future", "duplicate", "symlink"])
def test_degraded_authority_keeps_exact_receipt_result_and_never_recreates(
    tmp_path, snapshot, problem
):
    with OperationStore(tmp_path / "api") as store:
        receipt = store.admit(BASIC, "accepted", ROUTE, {}, snapshot).receipt
        result = envelope()
        store.transition(receipt.operation_id, "running")
        store.transition(receipt.operation_id, "succeeded", envelope=result)
        marker = store.root / INTENT_NAME
        if problem in {"missing", "symlink"}:
            marker.unlink()
            if problem == "symlink":
                marker.symlink_to(tmp_path / "absent")
        elif problem == "future":
            marker.write_bytes(
                b'{"schema_version":2,"archive_id":"'
                + examples.ARCHIVE_ID.encode()
                + b'","entries":[]}'
            )
        elif problem == "duplicate":
            marker.write_bytes(b'{"schema_version":1,"schema_version":1}')
        else:
            marker.write_bytes(b"{bad")
        before = (
            marker.readlink()
            if marker.is_symlink()
            else marker.read_bytes()
            if marker.exists()
            else None
        )
        assert store.get(receipt.operation_id).state == "succeeded"
        assert store.result(receipt.operation_id) == result
        for action in (
            lambda: store.admit(BASIC, "new", ROUTE, {}, snapshot),
            lambda: refused(store),
            lambda: store.intent(BASIC, "missing", examples.ARCHIVE_ID),
        ):
            with pytest.raises(OperationError):
                action()
        after = (
            marker.readlink()
            if marker.is_symlink()
            else marker.read_bytes()
            if marker.exists()
            else None
        )
        assert after == before


def test_missing_activation_never_silently_initializes(tmp_path, snapshot):
    with UnactivatedStore(tmp_path / "api") as store:
        with pytest.raises(OperationError):
            store.admit(BASIC, "new", ROUTE, {}, snapshot)
        assert not (store.root / INTENT_NAME).exists()


def test_rename_before_directory_fsync_failure_is_uncertain_then_get_recovers(
    tmp_path, monkeypatch
):
    with OperationStore(tmp_path / "api") as store:
        sync = os.fsync

        def fail_parent(descriptor):
            if descriptor == store._fd:
                raise OSError(errno.ENOSPC, "injected")
            return sync(descriptor)

        with monkeypatch.context() as patch:
            patch.setattr(os, "fsync", fail_parent)
            with pytest.raises(OperationError):
                refused(store)
            with pytest.raises(OperationError):
                store.intent(BASIC, "original", examples.ARCHIVE_ID)
            with pytest.raises(OperationError):
                refused(store)
        record, disposition = store.intent(BASIC, "original", examples.ARCHIVE_ID)
        assert record is None
        assert disposition is not None
        assert store.list() == ()


def test_full_permanent_state_refuses_new_work_but_keeps_observations(
    tmp_path, snapshot, monkeypatch
):
    from hfcache.api import operations  # noqa: PLC0415 - local capacity seam

    with OperationStore(tmp_path / "api") as store:
        accepted = store.admit(BASIC, "accepted", ROUTE, {}, snapshot).receipt
        closed = refused(store)[1]
        monkeypatch.setattr(operations, "MAX_INTENTS", 1)
        with pytest.raises(OperationError):
            store.admit(BASIC, "new", ROUTE, {}, snapshot)
        with pytest.raises(OperationError):
            refused(store, "new")
        assert store.intent(BASIC, "original", examples.ARCHIVE_ID) == (None, closed)
        assert store.intent(BASIC, "accepted", examples.ARCHIVE_ID) == (accepted, None)


def test_lease_independent_descriptions_and_replacement_refusal(tmp_path):
    path = tmp_path / "intent.lock"
    path.touch(mode=0o600)
    interlock = IntentInterlock(path)
    first, second = interlock.acquire(), interlock.acquire()
    first.close()
    with pytest.raises(OperationError):
        interlock.acquire(exclusive=True)
    second.close()
    with interlock.acquire(exclusive=True), pytest.raises(OperationError):
        interlock.acquire()
    with interlock.acquire() as original:
        path.rename(tmp_path / "old.lock")
        path.touch(mode=0o600)
        with pytest.raises(OperationError):
            interlock.acquire(exclusive=True)
        assert original.fd >= 0


def test_cross_process_shared_lease_blocks_review_after_parent_lease_closes(tmp_path):
    path = tmp_path / "intent.lock"
    path.touch(mode=0o600)
    interlock = IntentInterlock(path)
    code = (
        "from pathlib import Path; import sys; "
        "from hfcache.api.intents import IntentInterlock; "
        "lease=IntentInterlock(Path(sys.argv[1])).acquire(); "
        "print('ready',flush=True);sys.stdin.readline();lease.close()"
    )
    with subprocess.Popen(
        [sys.executable, "-c", code, str(path)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
    ) as process:
        assert process.stdout is not None
        assert process.stdin is not None
        assert process.stdout.readline().strip() == "ready"
        lease = interlock.acquire()
        lease.close()
        with pytest.raises(OperationError):
            interlock.acquire(exclusive=True)
        process.stdin.write("done\n")
        process.stdin.flush()
        assert process.wait(timeout=5) == 0
    with interlock.acquire(exclusive=True):
        pass


def test_offline_activation_backs_up_both_predecessor_stores_and_refuses_reactivation(tmp_path):
    api, worker = tmp_path / "api", tmp_path / "worker"
    for root in (api, worker):
        with UnactivatedStore(root, private=True):
            pass
    backup, companion = tmp_path / "backup", tmp_path / "companion"
    prepare_intent_state(
        examples.ARCHIVE_ID, backup, public=api, private=worker, companion=companion
    )
    assert json.loads((api / INTENT_NAME).read_bytes())["entries"] == []
    assert set(json.loads((backup / "manifest.json").read_bytes())) == {
        "schema_version",
        "archive_id",
        "api",
        "worker",
    }
    before = (api / INTENT_NAME).read_bytes(), companion.stat().st_ino
    with pytest.raises(OperationError):
        prepare_intent_state(
            examples.ARCHIVE_ID,
            tmp_path / "another-backup",
            public=api,
            private=worker,
            companion=companion,
        )
    assert before == ((api / INTENT_NAME).read_bytes(), companion.stat().st_ino)


def review_for(store):
    import hashlib  # noqa: PLC0415

    from hfcache.api.intents import IntentReview  # noqa: PLC0415 - fixture for trusted proof
    from hfcache.models import serialize  # noqa: PLC0415

    data = {
        "schema_version": 1,
        "review_id": "a" * 32,
        "observed_at": "2026-11-03T12:00:00.000000Z",
        "deployment_sha256": "a" * 64,
        "policy_sha256": "b" * 64,
        "receipt_set_sha256": store.receipt_set_digest(tuple(reversed(store.list()))),
        "worker_state_sha256": "c" * 64,
        "helper_effects_sha256": "d" * 64,
        "instances_sha256": "e" * 64,
        "intent_lock": {"device": 1, "inode": 2},
        "archive_lock": {"device": 1, "inode": 3},
    }
    return IntentReview.model_validate(
        data | {"sha256": hashlib.sha256(serialize(data).encode()).hexdigest()}
    )


def test_review_monotonically_enriches_later_refusal_preserving_every_original_field(tmp_path):
    with OperationStore(tmp_path / "api") as store:
        original = refused(store)[1]
        review = review_for(store)
        record, enriched = store.retire(
            BASIC,
            "original",
            examples.ARCHIVE_ID,
            review,
            receipt_set_sha256=review.receipt_set_sha256,
        )
        assert record is None
        assert enriched is not None
        assert original is not None
        assert enriched.model_dump(exclude={"review"}) == original.model_dump(exclude={"review"})
        assert original.projection(examples.ARCHIVE_ID)["state"] == "not_admitted"
        assert enriched.projection(examples.ARCHIVE_ID)["state"] == "retired_unknown"
        assert enriched.projection(examples.ARCHIVE_ID)["disposition_id"] == review.review_id
        assert enriched.projection(examples.ARCHIVE_ID)["reason"] is None
        assert store.retire(
            BASIC,
            "original",
            examples.ARCHIVE_ID,
            review,
            receipt_set_sha256=review.receipt_set_sha256,
        ) == (None, enriched)


def test_review_failure_preserves_original_fence_and_cannot_revive_it(
    tmp_path, monkeypatch, snapshot
):
    with OperationStore(tmp_path / "api") as store:
        original = refused(store)[1]
        review = review_for(store)
        before = (store.root / INTENT_NAME).read_bytes()
        with monkeypatch.context() as patch:
            patch.setattr(store, "_write", lambda *_: (_ for _ in ()).throw(OperationError()))
            with pytest.raises(OperationError):
                store.retire(
                    BASIC,
                    "original",
                    examples.ARCHIVE_ID,
                    review,
                    receipt_set_sha256=review.receipt_set_sha256,
                )
        assert (store.root / INTENT_NAME).read_bytes() == before
        assert store.intent(BASIC, "original", examples.ARCHIVE_ID)[1] == original
        with pytest.raises(OperationError):
            store.admit(BASIC, "original", ROUTE, {}, snapshot)


def test_exact_previous_reader_refuses_marker_even_empty_and_preserves_exact_reads(
    tmp_path, snapshot
):
    import io  # noqa: PLC0415 - exact predecessor source drill
    import tarfile  # noqa: PLC0415
    import zipfile  # noqa: PLC0415

    old_root = tmp_path / "previous"
    old_root.mkdir()
    archive = subprocess.check_output(
        [
            "git",
            "archive",
            "c23abba45f8967d058983043b96843bef62e899a",
            "src/hfcache",
            "pyproject.toml",
            "uv.lock",
            ".python-version",
            "README.md",
            "LICENSE",
        ]
    )
    with tarfile.open(fileobj=io.BytesIO(archive)) as bundle:
        bundle.extractall(old_root, filter="data")
    # Source imports alone would resolve the current environment's distribution
    # metadata. Build/extract the exact predecessor wheel so its version and
    # reader implementation come from the same immutable release.
    subprocess.run(
        ["uv", "build", "--wheel", "--offline", "--out-dir", str(old_root / "dist")],
        cwd=old_root,
        check=True,
        capture_output=True,
    )
    installed = old_root / "installed"
    with zipfile.ZipFile(old_root / "dist/hfcache-0.3.1-py3-none-any.whl") as wheel:
        wheel.extractall(installed)
    root = tmp_path / "api"
    with OperationStore(root) as store:
        receipt = store.admit(BASIC, "accepted", ROUTE, {}, snapshot).receipt
        result = envelope()
        store.transition(receipt.operation_id, "running")
        store.transition(receipt.operation_id, "succeeded", envelope=result)
    code = """
import sys
sys.path.insert(0,sys.argv[1])
from pathlib import Path
from hfcache import __version__
from hfcache.api.operations import OperationStore
from hfcache.api.auth import CredentialClass,Principal
from hfcache.errors import OperationError
assert __version__=='0.3.1'
with OperationStore(Path(sys.argv[2])) as store:
    if sys.argv[4]=='present':
        assert store.get(sys.argv[3]).state=='succeeded'
        assert store.result(sys.argv[3]).exit_code==0
    actions = [store.list, store.expire]
    principal = Principal(CredentialClass.REST_WRITER)
    actions += [lambda:store.lookup(principal,'unknown')]
    actions += [lambda:store.admit(principal,'unknown','/api/v1/syncs',{},lambda:None)]
    for action in actions:
        try: action()
        except OperationError: pass
        else: raise AssertionError('predecessor accepted new authority')
"""

    def previous(mode):
        subprocess.run(
            [
                sys.executable,
                "-c",
                code,
                str(installed),
                str(root),
                receipt.operation_id,
                mode,
            ],
            check=True,
            capture_output=True,
        )

    previous("present")
    with UnactivatedStore(root) as store:
        refused(store)
    previous("present")
    # Exact terminal retention removes receipt/result only; old scans still
    # reject the retained permanent authority with no expirable records left.
    from datetime import timedelta  # noqa: PLC0415

    with UnactivatedStore(root) as store:
        store.clock = lambda: receipt.created_at + timedelta(days=100)
        assert store.expire() == (receipt.operation_id,)
    previous("gone")


def test_missing_original_store_lock_refuses_open_and_preserves_evidence(tmp_path):
    root = tmp_path / "api"
    with OperationStore(root) as store:
        refused(store)
    before = (root / INTENT_NAME).read_bytes()
    (root / ".lock").rename(root / "original-lock-preserved")
    with pytest.raises(OperationError):
        UnactivatedStore(root)
    assert not (root / ".lock").exists()
    assert (root / INTENT_NAME).read_bytes() == before


def test_nested_review_requires_explicit_version_and_rejects_ambiguous_versions(tmp_path):
    with OperationStore(tmp_path / "api") as store:
        review = review_for(store).model_dump(mode="json")
        from hfcache.api.intents import IntentReview  # noqa: PLC0415

        with pytest.raises(ValidationError):
            IntentReview.model_validate(
                {key: value for key, value in review.items() if key != "schema_version"}
            )
        for version in (True, 1.0, "1", 2):
            with pytest.raises(ValidationError):
                IntentReview.model_validate(review | {"schema_version": version})


def test_store_budget_counts_actual_disposition_bytes_with_valid_whitespace(tmp_path, snapshot):
    from hfcache.api.operations import OperationLimits  # noqa: PLC0415 - narrow quota fixture

    root = tmp_path / "api"
    with OperationStore(root) as store:
        receipt = store.admit(BASIC, "accepted", ROUTE, {}, snapshot).receipt
        marker = root / INTENT_NAME
        marker.write_bytes(b" " * 2048 + marker.read_bytes())
    with UnactivatedStore(root, limits=OperationLimits(max_store_bytes=2048)) as narrow:
        with pytest.raises(OperationError):
            narrow.list()
        assert narrow.get(receipt.operation_id) == receipt


@pytest.mark.parametrize("missing", ["directory", "lock"])
def test_offline_existing_store_refuses_missing_original_without_creation(tmp_path, missing):
    root = tmp_path / "api"
    if missing == "lock":
        root.mkdir(mode=0o700)
    with pytest.raises(OperationError):
        OperationStore(root, private=True, existing=True)
    assert not (root / ".lock").exists()
    assert root.exists() == (missing == "lock")


def test_activation_preserves_original_store_lock_inodes(tmp_path):
    api, worker = tmp_path / "api", tmp_path / "worker"
    for root in (api, worker):
        with UnactivatedStore(root, private=True):
            pass
    before = [(root / ".lock").stat().st_ino for root in (api, worker)]
    prepare_intent_state(
        examples.ARCHIVE_ID,
        tmp_path / "backup",
        public=api,
        private=worker,
        companion=tmp_path / "companion",
    )
    assert before == [(root / ".lock").stat().st_ino for root in (api, worker)]


@pytest.mark.parametrize("kind", ["writer", "reader", "mcp_reader", "basic", "tls"])
def test_native_custom_credential_sources_require_actual_model_and_covered_masks(kind):
    data: dict[str, Any] = {
        "schema_version": 1,
        "credentials": {"writer": {"systemd_name": "rest-writer"}},
    }
    if kind in {"writer", "reader", "mcp_reader"}:
        data["credentials"][kind] = {"file": "/private-activation-source/token"}
    elif kind == "basic":
        data["basic"] = {
            "origin": "https://localhost",
            "administrator": {"file": "/private-activation-source/administrator.json"},
        }
        data["listener"] = {"allowed_origins": ["https://localhost"]}
    else:
        data["listener"] = {
            "tls": {
                "certificate": "/public/certificate.pem",
                "private_key": "/private-activation-source/key.pem",
            }
        }
    server = validate_server_config_mapping(data)
    with pytest.raises(OperationError):
        activation.validate_native_sources(server, (Path("/etc/credstore"),))
    activation.validate_native_sources(server, (Path("/private-activation-source"),))


@pytest.fixture
def native_activation_policy(tmp_path, monkeypatch):
    selected = tmp_path / "selected"
    packaged = selected / "packaging/systemd/hfcache-api.service"
    packaged.parent.mkdir(parents=True)
    packaged.write_bytes(
        (Path(__file__).parents[2] / "packaging/systemd/hfcache-api.service").read_bytes()
    )
    script = selected / "scripts/hardening-probe.py"
    script.parent.mkdir()
    script.write_bytes((Path(__file__).parents[2] / "scripts/hardening-probe.py").read_bytes())
    server = tmp_path / "server.toml"
    server.write_text(
        'schema_version=1\n[credentials.writer]\nfile="/private-activation-source/token"\n'
    )
    archive = tmp_path / "config.toml"
    archive.write_text(
        'schema_version=1\n[storage]\narchive_root="/srv/hfcache"\narchive_id="'
        + examples.ARCHIVE_ID
        + '"\n'
    )
    monkeypatch.setattr(activation, "NATIVE_SERVER", server)
    monkeypatch.setattr(activation, "NATIVE_ARCHIVE_CONFIG", archive)
    monkeypatch.setattr(
        activation.pwd,
        "getpwnam",
        lambda _: SimpleNamespace(pw_uid=981, pw_gid=981, pw_dir="/var/lib/hfcache"),
    )
    entry = "/opt/hfcache/current/.venv/bin/hfcache"
    api = {
        "FragmentPath": str(packaged),
        "DropInPaths": "",
        "ImportCredential": "hf-token",
        "ExecStart": "{ path="
        + entry
        + " ; argv[]="
        + entry
        + " serve --server-config /etc/hfcache/server.toml ; ignore_errors=no ; pid=0 ; }",
    }
    worker = {"LoadState": "loaded", "InaccessiblePaths": "-/private-activation-source"}
    monkeypatch.setattr(
        activation,
        "_native_show",
        lambda unit, _properties: api.copy() if unit == "hfcache-api.service" else worker.copy(),
    )
    credentials = {
        "LoadCredential": [],
        "LoadCredentialEncrypted": [["hfcache.api", "/etc/credstore.encrypted/hfcache.api"]],
    }
    monkeypatch.setattr(
        activation.subprocess,
        "run",
        lambda argv, **_kwargs: SimpleNamespace(
            stdout=json.dumps({"type": "a(ss)", "data": credentials[argv[-1]]})
        ),
    )
    return SimpleNamespace(
        selected=selected,
        api=api,
        worker=worker,
        server=server,
        archive=archive,
        credentials=credentials,
    )


def test_native_masks_preserve_reviewed_sources_and_optional_absent_standard_stores(
    native_activation_policy,
):
    host = native_activation_policy
    masks, revision = activation.native_mask_policy(host.selected)
    assert "-/private-activation-source" in masks.split()
    for path in activation._NATIVE_MASKS:
        assert "-" + path in masks.split()
    assert len(revision) == 64
    before = masks, revision
    host.server.write_text(host.server.read_text() + "# changed exact bytes\n")
    assert activation.native_mask_policy(host.selected) != before
    host.worker["InaccessiblePaths"] = ""
    with pytest.raises(OperationError):
        activation.native_mask_policy(host.selected)


@pytest.mark.parametrize(
    "change",
    ["dropin", "hub-file", "missing-worker", "escaped-mask", "custom-archive", "cached-credential"],
)
def test_native_policy_refuses_unsupported_or_unmodelled_sources(native_activation_policy, change):
    host = native_activation_policy
    if change == "dropin":
        host.api["DropInPaths"] = "/etc/systemd/system/hfcache-api.service.d/custom.conf"
    elif change == "hub-file":
        host.api["ExecStart"] = host.api["ExecStart"].replace(
            " ; ignore_errors", " --hub-token-file /custom/source ; ignore_errors"
        )
    elif change == "missing-worker":
        host.worker["LoadState"] = "not-found"
    elif change == "cached-credential":
        host.credentials["LoadCredential"] = [["hf-token", "/private-unmodelled-source/token"]]
    elif change == "custom-archive":
        host.archive.write_text(
            host.archive.read_text().replace("/srv/hfcache", "/mnt/custom-native-archive")
        )
    else:
        host.worker["InaccessiblePaths"] = "-/private-activation-source /custom%masked"
    with pytest.raises((OperationError, ValueError)):
        activation.native_mask_policy(host.selected)


def test_native_credentials_use_fixed_typed_system_bus_metadata(monkeypatch):
    calls = []
    expected = {
        "LoadCredential": [],
        "LoadCredentialEncrypted": [["hfcache.api", "/etc/credstore.encrypted/hfcache.api"]],
    }

    def run(argv, **kwargs):
        calls.append((argv, kwargs))
        return SimpleNamespace(stdout=json.dumps({"type": "a(ss)", "data": expected[argv[-1]]}))

    monkeypatch.setattr(activation.subprocess, "run", run)
    assert activation._native_credentials() == expected
    assert len(calls) == 2
    for (argv, kwargs), property_name in zip(calls, expected, strict=True):
        assert argv == [
            "/usr/bin/busctl",
            "--system",
            "--json=short",
            "--timeout=5",
            "get-property",
            "org.freedesktop.systemd1",
            "/org/freedesktop/systemd1/unit/hfcache_2dapi_2eservice",
            "org.freedesktop.systemd1.Service",
            property_name,
        ]
        assert kwargs == {
            "check": True,
            "stdin": subprocess.DEVNULL,
            "capture_output": True,
            "text": True,
            "timeout": 5,
            "env": {"PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C"},
        }


@pytest.mark.parametrize(
    "body",
    [
        "[unprintable]",
        '{"type":"a(ss)","type":"a(ss)","data":[]}',
        '{"type":"a(ss)","data":[],"data":[]}',
        '{"type":"as","data":[]}',
        '{"type":"a(ss)","data":[],"extra":false}',
        '{"type":"a(ss)","data":[["hf-token","/custom/token"]]}',
        '{"type":"a(ss)","data":[["hfcache.api","/etc/credstore.encrypted/hfcache.api"]]}',
        '{"type":"a(ss)","data":null}',
        " " * (activation._MAX_NATIVE_METADATA + 1),
    ],
)
def test_native_credential_metadata_refuses_unexplained_or_unsupported_arrays(monkeypatch, body):
    monkeypatch.setattr(
        activation.subprocess, "run", lambda *_args, **_kwargs: SimpleNamespace(stdout=body)
    )
    with pytest.raises(OperationError):
        activation._native_credentials()


@pytest.mark.parametrize(
    "entries",
    [
        [],
        [["hfcache.api", "/custom/token"]],
        [["other", "/etc/credstore.encrypted/hfcache.api"]],
        [["hfcache.api", "/etc/credstore.encrypted/hfcache.api"], ["extra", "/extra"]],
    ],
)
def test_native_encrypted_credential_delivery_requires_exact_original_pair(
    native_activation_policy, entries
):
    host = native_activation_policy
    host.credentials["LoadCredentialEncrypted"] = entries
    with pytest.raises(OperationError):
        activation.native_mask_policy(host.selected)


@pytest.mark.parametrize("stale", [False, True])
def test_native_revision_rechecks_before_state_effects(tmp_path, monkeypatch, snapshot, stale):
    current = snapshot()
    masks = "-/etc/credstore"
    revision = "a" * 64
    monkeypatch.setattr(activation, "load_config", lambda _: current.config)
    monkeypatch.setattr(
        activation, "native_mask_policy", lambda _: (masks, "b" * 64 if stale else revision)
    )
    calls = []
    monkeypatch.setattr(activation, "prepare_intent_state", lambda *args: calls.append(args))
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "intent_activation",
            "--archive-id",
            str(current.config.storage.archive_id),
            "--backup-directory",
            str(tmp_path / "initial"),
            "--native-masks=" + masks,
            "--native-revision",
            revision,
        ],
    )
    if stale:
        with pytest.raises(OperationError):
            activation.main()
        assert calls == []
    else:
        activation.main()
        assert calls == [(str(current.config.storage.archive_id), tmp_path / "initial")]


def test_offline_partial_activation_preserves_companion_backup_and_original_inodes(
    tmp_path, monkeypatch
):
    api, worker = tmp_path / "api", tmp_path / "worker"
    for root in (api, worker):
        with UnactivatedStore(root, private=True):
            pass
    inodes = [(root / ".lock").stat().st_ino for root in (api, worker)]
    runtime = tmp_path / "isolated-runtime"
    runtime.mkdir(mode=0o700)
    companion = runtime / "hfcache.lock.intent"
    backup = tmp_path / "initial-backup"

    def interrupted(*_args, **_kwargs):
        raise OperationError

    monkeypatch.setattr(UnactivatedStore, "_write", interrupted)
    with pytest.raises(OperationError):
        prepare_intent_state(
            examples.ARCHIVE_ID, backup, public=api, private=worker, companion=companion
        )
    assert companion.is_file()
    companion_inode = companion.stat().st_ino
    assert (backup / "manifest.json").is_file()
    assert not (api / INTENT_NAME).exists()
    assert inodes == [(root / ".lock").stat().st_ino for root in (api, worker)]
    with pytest.raises(OperationError):
        prepare_intent_state(
            examples.ARCHIVE_ID,
            tmp_path / "unexplained-retry",
            public=api,
            private=worker,
            companion=companion,
        )
    assert not (tmp_path / "unexplained-retry").exists()
    assert companion.stat().st_ino == companion_inode
