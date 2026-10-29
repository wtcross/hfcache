"""ADR150 fixed guard proof; credential syscalls are stubbed in unprivileged tests.

The original predicate consumes real owned flock/proc-lock metadata. Actual
mixed-UID anti-ptrace and installed system-manager conformance remain separate.
"""

import fcntl
import hashlib
import io
import json
import os
import subprocess
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from hfcache import host_policy as policy
from tests.unit.test_host_policy import (
    deployment as deployment,  # noqa: PLC0414 - original indexed-stage dependency
)
from tests.unit.test_host_policy import (
    native as native,  # noqa: PLC0414 - ordinary protected temporary authority tree
)
from tests.unit.test_host_policy import (
    rootless as rootless,  # noqa: PLC0414 - original indexed-stage authority tree
)


def unit(native):
    native.units[policy.GUARD].update(
        LoadState="loaded",
        ActiveState="active",
        SubState="running",
        UnitFileState="enabled",
        MainPID=str(os.getpid()),
    )
    return native.units[policy.GUARD] | {"InvocationID": "e" * 32}


def result(native):
    current = unit(native)
    info = native.lock.stat()
    return {
        "schema_version": 1,
        "deployment_sha256": hashlib.sha256(native.deployment.read_bytes()).hexdigest(),
        "guard": "held",
        "unit": current,
        "start_ticks": policy._process_start(os.getpid(), policy.InspectionBudget()),
        "lock": {
            "device": info.st_dev,
            "inode": info.st_ino,
            "uid": native.index["api_principal"]["host_uid"],
            "gid": native.index["api_principal"]["host_gid"],
            "mode": 0o600,
        },
        "work": {"files": 4, "bytes": 100},
    }


def test_absent_guard_does_not_create_an_observer_or_access_private_lock(native, monkeypatch):
    def forbidden(*_args):
        pytest.fail("known absent guard reached child/process proof")

    monkeypatch.setattr(policy, "_guard_child", forbidden)
    monkeypatch.setattr(policy, "_process_start", forbidden)
    assert policy.inspect_authority().status()["facts"]["guard"] == "absent"


@pytest.mark.parametrize(
    "change",
    [
        "extra",
        "schema-bool",
        "digest",
        "guard",
        "unit",
        "start",
        "lock-uid",
        "lock-mode",
        "lock-inode-bool",
        "work-negative",
        "work-bool",
    ],
)
def test_parent_refuses_every_unknown_or_unjoined_child_shape(native, monkeypatch, change):
    proof = result(native)
    if change == "extra":
        proof["extra"] = 1
    elif change == "schema-bool":
        proof["schema_version"] = True
    elif change == "digest":
        proof["deployment_sha256"] = "0" * 64
    elif change == "guard":
        proof["guard"] = "inactive"
    elif change == "unit":
        proof["unit"]["InvocationID"] = "f" * 32
    elif change == "start":
        proof["start_ticks"] += 1
    elif change == "lock-uid":
        proof["lock"]["uid"] += 1
    elif change == "lock-mode":
        proof["lock"]["mode"] = 0o644
    elif change == "lock-inode-bool":
        proof["lock"]["inode"] = True
    elif change == "work-negative":
        proof["work"]["bytes"] = -1
    else:
        proof["work"]["files"] = True
    monkeypatch.setattr(policy, "_guard_child", lambda _budget: proof)
    with pytest.raises(policy.InspectionError):
        policy.inspect_authority()


def test_parent_brackets_guard_generation_and_charges_child_work(native, monkeypatch):
    proof = result(native)
    monkeypatch.setattr(policy, "_guard_child", lambda _budget: proof)
    snapshot = policy.inspect_authority()
    assert snapshot.status()["facts"]["guard"] == "held"
    assert snapshot.status()["permissions"]["archive"] is False
    assert snapshot.budget.files >= 8

    def changed(_budget):
        native.units[policy.GUARD]["MainPID"] = str(os.getpid() + 1)
        return proof

    monkeypatch.setattr(policy, "_guard_child", changed)
    with pytest.raises(policy.InspectionError):
        policy.revalidate(snapshot)


def guard_credentials(native, monkeypatch):
    current = unit(native)
    uid = native.index["api_principal"]["host_uid"]
    gid = native.index["api_principal"]["host_gid"]
    identifiers = {"uid": (0, 0, 0), "gid": (0, 0, 0)}
    changes = []

    def setuid(*values):
        identifiers["uid"] = values
        changes.append(("uid", values))

    def setgid(*values):
        identifiers["gid"] = values
        changes.append(("gid", values))

    monkeypatch.setattr(os, "getresuid", lambda: identifiers["uid"])
    monkeypatch.setattr(os, "getresgid", lambda: identifiers["gid"])
    monkeypatch.setattr(os, "setresuid", setuid)
    monkeypatch.setattr(os, "setresgid", setgid)
    monkeypatch.setattr(os, "getgroups", lambda: [0])
    monkeypatch.setattr(os, "setgroups", lambda groups: changes.append(("groups", groups)))
    monkeypatch.setattr(
        policy.pwd,
        "getpwnam",
        lambda name: (
            SimpleNamespace(pw_uid=uid, pw_gid=gid, pw_dir="/var/lib/hfcache")
            if name == "hfcache"
            else None
        ),
    )
    monkeypatch.setattr(policy, "LOCKS", Path("/proc/locks"))
    body = json.dumps(
        {
            "schema_version": 1,
            "remaining_seconds": 5.0,
            "maximum_files": 1024,
            "maximum_bytes": 64 * 1024 * 1024,
        }
    ).encode()
    monkeypatch.setattr(policy.sys, "stdin", SimpleNamespace(buffer=io.BytesIO(body)))
    return current, identifiers, changes


def test_child_runs_original_predicate_with_real_flock_and_mixed_id_call_sequence(
    native, monkeypatch
):
    current, identifiers, changes = guard_credentials(native, monkeypatch)
    uid = native.index["api_principal"]["host_uid"]
    gid = native.index["api_principal"]["host_gid"]

    def forbidden(*_args, **_kwargs):
        pytest.fail("native guard read the rootless archive-lock context")

    monkeypatch.setattr(os, "getxattr", forbidden)
    with native.lock.open("rb") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        proof = policy.observe_guard(
            bootstrap_work={"files": 4, "bytes": 100}, started_at=time.monotonic()
        )
    assert proof["guard"] == "held"
    assert proof["unit"] == current
    assert proof["lock"]["inode"] == native.lock.stat().st_ino
    assert proof["work"]["files"] > 4
    assert proof["work"]["bytes"] > 100
    assert ("uid", (0, uid, 0)) in changes
    assert ("gid", (0, gid, 0)) in changes
    assert identifiers == {"uid": (0, 0, 0), "gid": (0, 0, 0)}
    assert changes[-1] == ("groups", [0])


def test_rootless_child_brackets_original_flock_with_metadata_only_context_proof(
    rootless, monkeypatch
):
    current, identifiers, changes = guard_credentials(rootless, monkeypatch)
    uid = rootless.index["api_principal"]["host_uid"]
    gid = rootless.index["api_principal"]["host_gid"]
    contexts = []
    original = os.open

    def getxattr(path, name, *, follow_symlinks):
        assert path == rootless.lock
        assert name == "security.selinux"
        assert follow_symlinks is False
        assert identifiers == {"uid": (0, uid, 0), "gid": (0, gid, 0)}
        contexts.append(path)
        return b"system_u:object_r:hfcache_host_helper_archive_lock_t:s0"

    def open_parent(path, *args, **kwargs):
        assert path not in {rootless.lock, rootless.lock.name}
        return original(path, *args, **kwargs)

    monkeypatch.setattr(os, "getxattr", getxattr)
    with rootless.lock.open("rb") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        monkeypatch.setattr(os, "open", open_parent)
        proof = policy.observe_guard()
    assert proof["guard"] == "held"
    assert proof["unit"] == current
    assert contexts == [rootless.lock, rootless.lock]
    assert identifiers == {"uid": (0, 0, 0), "gid": (0, 0, 0)}
    assert changes[-1] == ("groups", [0])
    assert set(proof["lock"]) == {"device", "inode", "uid", "gid", "mode"}


@pytest.mark.parametrize("change", ["initial-type", "changed-context", "changed-inode"])
def test_rootless_guard_refusal_restores_credentials_and_retains_original_lock(
    rootless, monkeypatch, change
):
    _current, identifiers, changes = guard_credentials(rootless, monkeypatch)
    context = b"system_u:object_r:hfcache_host_helper_archive_lock_t:s0"
    original = policy._archive_lock_context
    calls = 0
    retained = rootless.lock.with_suffix(".original")

    def checked(capture, uid, gid):
        nonlocal calls
        calls += 1
        if change == "changed-inode" and calls == 2:
            rootless.lock.rename(retained)
            rootless.lock.write_bytes(b"replacement lock")
            rootless.lock.chmod(0o600)
            if os.geteuid() == 0:
                os.chown(rootless.lock, uid, gid)
        return original(capture, uid, gid)

    def getxattr(*_args, **_kwargs):
        if change == "initial-type":
            return b"system_u:object_r:container_file_t:s0"
        if change == "changed-context" and calls == 2:
            return context.replace(b"system_u", b"unconfined_u")
        return context

    monkeypatch.setattr(policy, "_archive_lock_context", checked)
    monkeypatch.setattr(os, "getxattr", getxattr)
    before = rootless.lock.stat()
    with rootless.lock.open("rb") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(policy.InspectionError) as refused:
            policy.observe_guard()
        assert refused.value.reason == "facts-unavailable"
        assert os.fstat(stream.fileno()).st_ino == before.st_ino
    assert calls == (1 if change == "initial-type" else 2)
    assert identifiers == {"uid": (0, 0, 0), "gid": (0, 0, 0)}
    assert changes[-1] == ("groups", [0])
    assert (retained if change == "changed-inode" else rootless.lock).stat().st_ino == before.st_ino


@pytest.mark.parametrize(
    "context",
    [
        b"",
        b"system_u:system_r:hfcache_host_helper_archive_lock_t:s0",
        b"system_u:object_r:hfcache_host_helper_archive_lock_t:s0:c1",
        b"system_u:object_r:hfcache_host_helper_archive_lock_t:s0\n",
        b"system_u:object_r:hfcache_host_helper_archive_lock_t:s0\0\0",
        b"\xff:object_r:hfcache_host_helper_archive_lock_t:s0",
        b"x" * 4097,
    ],
)
def test_fixed_guard_lock_context_refuses_unknown_full_sid(native, monkeypatch, context):
    capture = policy._Capture(policy.InspectionBudget())
    capture.mounts = capture.mount_rows()
    monkeypatch.setattr(os, "getxattr", lambda *_args, **_kwargs: context)
    principal = native.index["api_principal"]
    with pytest.raises(policy.InspectionError) as refused:
        policy._archive_lock_context(capture, principal["host_uid"], principal["host_gid"])
    assert refused.value.reason == "facts-unavailable"


@pytest.mark.parametrize("change", ["symlink", "hardlink", "mode", "uid", "gid"])
def test_fixed_guard_lock_context_refuses_unsafe_inode_before_xattr(native, monkeypatch, change):
    principal = native.index["api_principal"].copy()
    if change == "symlink":
        retained = native.lock.with_suffix(".original")
        native.lock.rename(retained)
        native.lock.symlink_to(retained)
    elif change == "hardlink":
        os.link(native.lock, native.lock.with_suffix(".alias"))
    elif change == "mode":
        native.lock.chmod(0o640)
    else:
        principal["host_" + change] += 1

    def forbidden(*_args, **_kwargs):
        pytest.fail("unsafe original lock reached context read")

    monkeypatch.setattr(os, "getxattr", forbidden)
    capture = policy._Capture(policy.InspectionBudget())
    capture.mounts = capture.mount_rows()
    with pytest.raises(policy.InspectionError) as refused:
        policy._archive_lock_context(capture, principal["host_uid"], principal["host_gid"])
    assert refused.value.reason == "facts-unavailable"


def test_non_root_guard_role_refuses_before_any_metadata(native, monkeypatch):
    monkeypatch.setattr(os, "getresuid", lambda: (983, 983, 983))
    with pytest.raises(policy.InspectionError):
        policy.observe_guard()
    assert native.calls == []


def test_parent_timeout_retains_exact_read_child_until_natural_exit(monkeypatch):
    original = subprocess.Popen
    owned = []
    arguments = []

    def popen(argv, **kwargs):
        arguments.append(argv)
        child = original(
            [
                os.sys.executable,
                "-c",
                "import sys,time;sys.stdin.buffer.read();time.sleep(.15);print('{}')",
            ],
            **kwargs,
        )
        owned.append(child)
        return child

    monkeypatch.setattr(policy.subprocess, "Popen", popen)
    started = time.monotonic()
    budget = policy.InspectionBudget(deadline_ns=time.monotonic_ns() + 50_000_000)
    with pytest.raises(TimeoutError):
        policy._guard_child(budget)
    assert time.monotonic() - started >= 0.15
    assert arguments == [["/usr/local/libexec/hfcache-host-helper", "observe-guard"]]
    assert owned[0].returncode == 0


def test_process_start_parser_reads_only_fixed_positive_pid():
    assert policy._process_start(os.getpid(), policy.InspectionBudget()) > 0
    with pytest.raises(policy.InspectionError):
        policy._process_start(pid=True, budget=policy.InspectionBudget())


@pytest.mark.parametrize(
    "change",
    ["extra", "seconds-int", "seconds-long", "bytes-large", "files-bool", "elapsed-bootstrap"],
)
def test_guard_child_closed_budget_and_original_clock_fail_before_metadata(
    native, monkeypatch, change
):
    request = {
        "schema_version": 1,
        "remaining_seconds": 5.0,
        "maximum_files": 1024,
        "maximum_bytes": 64 * 1024 * 1024,
    }
    if change == "extra":
        request["uid"] = 983
    elif change == "seconds-int":
        request["remaining_seconds"] = 5
    elif change == "seconds-long":
        request["remaining_seconds"] = 5.001
    elif change == "bytes-large":
        request["maximum_bytes"] += 1
    elif change == "files-bool":
        request["maximum_files"] = True
    monkeypatch.setattr(os, "getresuid", lambda: (0, 0, 0))
    monkeypatch.setattr(os, "getresgid", lambda: (0, 0, 0))
    monkeypatch.setattr(
        policy.sys, "stdin", SimpleNamespace(buffer=io.BytesIO(json.dumps(request).encode()))
    )
    started = time.monotonic() - 10 if change == "elapsed-bootstrap" else time.monotonic()
    with pytest.raises((policy.InspectionError, TimeoutError)):
        policy.observe_guard(bootstrap_work={"files": 4, "bytes": 100}, started_at=started)
    assert native.calls == []
