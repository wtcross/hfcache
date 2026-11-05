"""ADR164: fixed child metadata crosses DAC without changing daemon credentials.

The owned USER-namespace test uses actual IDs and capability syscalls; SELinux
contexts are modeled. Installed Enforcing proof remains a separate acceptance.
"""

import copy
import fcntl
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from hfcache import host_policy as policy
from tests.unit.test_host_guard import guard_credentials
from tests.unit.test_host_policy import native as native  # noqa: PLC0414 - protected fixture


@pytest.fixture
def lock_proof(native, monkeypatch):
    snapshot = policy.inspect_authority()
    companion = native.lock.with_name(native.lock.name + ".intent")
    companion.touch(mode=0o600)
    _unit, identifiers, changes = guard_credentials(native, monkeypatch)

    def forbidden(*_args, **_kwargs):
        pytest.fail("intent metadata child asserted an active guard")

    monkeypatch.setattr(policy, "_guard_unit", forbidden)
    monkeypatch.setattr(
        os,
        "getxattr",
        lambda *_args, **_kwargs: b"system_u:object_r:hfcache_host_helper_archive_lock_t:s0",
    )
    proof = policy.observe_intent_locks(bootstrap_work={"files": 4, "bytes": 100})
    assert identifiers == {"uid": (0, 0, 0), "gid": (0, 0, 0)}
    assert changes[-1] == ("groups", [0])
    assert proof["work"]["files"] > 4
    assert proof["work"]["bytes"] > 100
    monkeypatch.setattr(policy, "LOCKS", Path("/proc/locks"))

    def child(_budget, *, intent_locks):
        assert intent_locks is True
        return proof

    monkeypatch.setattr(policy, "_guard_child", child)
    return snapshot, companion, proof


def test_parent_requires_actual_exclusive_api_flock_and_keeps_credentials(lock_proof, monkeypatch):
    snapshot, companion, proof = lock_proof

    def forbidden(*_args, **_kwargs):
        pytest.fail("threaded daemon changed credentials or traversed runtime")

    monkeypatch.setattr(os, "setresuid", forbidden)
    monkeypatch.setattr(os, "setresgid", forbidden)
    monkeypatch.setattr(os, "setgroups", forbidden)
    monkeypatch.setattr(policy._Capture, "parent", forbidden)
    before = snapshot.budget.files
    with companion.open("rb") as stream:
        fcntl.flock(stream, fcntl.LOCK_SH)
        with pytest.raises(policy.InspectionError):
            policy.review_intent_locks(snapshot, os.getpid())
        fcntl.flock(stream, fcntl.LOCK_EX)
        result = policy.review_intent_locks(snapshot, os.getpid())
        assert result["intent_lock"]["inode"] == companion.stat().st_ino
        assert result["archive_lock"]["inode"] == proof["locks"]["archive_lock"]["identity"][1]
        assert policy.review_intent_locks(snapshot, os.getpid()) == result
        with pytest.raises(policy.InspectionError):
            policy.review_intent_locks(snapshot, os.getpid() + 1)
    with pytest.raises(policy.InspectionError):
        policy.review_intent_locks(snapshot, os.getpid())
    assert snapshot.budget.files >= before + proof["work"]["files"]


@pytest.mark.parametrize(
    "change",
    [
        "extra",
        "schema-bool",
        "digest",
        "work-bool",
        "work-negative",
        "lock-extra",
        "identity-bool",
        "identity-short",
        "mode",
        "uid",
        "gid",
        "nlink",
        "context",
        "parent-mode",
        "parent-owner",
        "parent-bool",
        "parent-extra",
    ],
)
def test_parent_refuses_untyped_or_unjoined_child_reply(lock_proof, change):  # noqa: PLR0912 - closed failure matrix
    snapshot, companion, proof = lock_proof
    identity = proof["locks"]["intent_lock"]["identity"]
    if change == "extra":
        proof["extra"] = 1
    elif change == "schema-bool":
        proof["schema_version"] = True
    elif change == "digest":
        proof["deployment_sha256"] = "f" * 64
    elif change == "work-bool":
        proof["work"]["files"] = True
    elif change == "work-negative":
        proof["work"]["bytes"] = -1
    elif change == "lock-extra":
        proof["locks"]["intent_lock"]["extra"] = 1
    elif change == "identity-bool":
        identity[0] = True
    elif change == "identity-short":
        identity.pop()
    elif change in {"mode", "uid", "gid", "nlink"}:
        identity[{"mode": 2, "uid": 3, "gid": 4, "nlink": 5}[change]] += 1
    elif change == "context":
        proof["locks"]["intent_lock"]["context"] += ":c1"
    elif change == "parent-mode":
        proof["runtime_parent"][2] |= 0o002
    elif change == "parent-owner":
        proof["runtime_parent"][3] += 1
    elif change == "parent-bool":
        proof["runtime_parent"][0] = True
    else:
        proof["runtime_parent"].append(1)
    with companion.open("rb") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        with pytest.raises(policy.InspectionError):
            policy.review_intent_locks(snapshot, os.getpid())


@pytest.mark.parametrize("change", ["inode", "context", "timestamps", "parent"])
def test_full_metadata_is_pinned_across_review(lock_proof, monkeypatch, change):
    snapshot, companion, proof = lock_proof
    with companion.open("rb") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        policy.review_intent_locks(snapshot, os.getpid())
        changed = copy.deepcopy(proof)
        record = changed["locks"]["archive_lock"]
        if change == "context":
            record["context"] = record["context"].replace("system_u", "unconfined_u")
        elif change == "parent":
            changed["runtime_parent"][1] += 1
        else:
            record["identity"][1 if change == "inode" else 8] += 1

        def child(_budget, *, intent_locks):
            assert intent_locks is True
            return changed

        monkeypatch.setattr(policy, "_guard_child", child)
        with pytest.raises(policy.InspectionError):
            policy.review_intent_locks(snapshot, os.getpid())


@pytest.mark.parametrize("change", ["missing", "mode", "hardlink", "symlink", "changed-inode"])
def test_child_refuses_unsafe_or_replaced_companion_without_opening_bodies(
    lock_proof, native, monkeypatch, change
):
    _snapshot, companion, _proof = lock_proof
    _unit, identifiers, changes = guard_credentials(native, monkeypatch)
    original = policy._archive_lock_context
    calls = 0
    retained = companion.with_suffix(".retained")
    replacement = companion.with_suffix(".replacement")
    if change == "changed-inode":
        replacement.touch(mode=0o600)

    def checked(capture, uid, gid, *, path):
        nonlocal calls
        calls += 1
        if change == "changed-inode" and calls == 4:
            companion.rename(retained)
            replacement.rename(companion)
        return original(capture, uid, gid, path=path)

    monkeypatch.setattr(policy, "_archive_lock_context", checked)
    if change == "missing":
        companion.rename(retained)
    elif change == "mode":
        companion.chmod(0o640)
    elif change == "hardlink":
        os.link(companion, retained)
    elif change == "symlink":
        companion.rename(retained)
        companion.symlink_to(retained)
    opened = os.open

    def parent_only(path, *args, **kwargs):
        assert path not in {native.lock, companion, native.lock.name, companion.name}
        return opened(path, *args, **kwargs)

    monkeypatch.setattr(os, "open", parent_only)
    with pytest.raises((policy.InspectionError, FileNotFoundError)):
        policy.observe_intent_locks()
    assert identifiers == {"uid": (0, 0, 0), "gid": (0, 0, 0)}
    assert changes[-1] == ("groups", [0])


def test_actual_capability_bounded_child_crosses_service_owned_0700(tmp_path):
    """No host root: chroot and IDs exist only in an owned USER namespace."""
    unshare = shutil.which("unshare")
    if unshare is None:
        pytest.skip("owned USER namespace requires util-linux unshare")
    probe = subprocess.run(
        [unshare, "--user", "--map-auto", "--map-root-user", "true"],
        capture_output=True,
        timeout=10,
        check=False,
    )
    if probe.returncode:
        pytest.skip("owned multiple-ID USER namespace unavailable")
    program = r"""import ctypes,json,os,sys
from pathlib import Path
from hfcache import host_policy as p
libc=ctypes.CDLL(None,use_errno=True)
class Header(ctypes.Structure):_fields_=[('version',ctypes.c_uint32),('pid',ctypes.c_int)]
class Data(ctypes.Structure):
 _fields_=[('effective',ctypes.c_uint32),('permitted',ctypes.c_uint32),('inheritable',ctypes.c_uint32)]
root=Path(sys.argv[1]);root.chmod(0o755)
runtime=root/'runtime';runtime.mkdir(mode=0o700)
for name in ('hfcache.lock','hfcache.lock.intent'):
 path=runtime/name;path.touch(mode=0o600);os.chown(path,983,983)
os.chown(runtime,983,983)
try:
 os.chroot(root);os.chdir('/')
 p.LOCK=Path('/runtime/hfcache.lock')
 p.os.getxattr=lambda *a,**k:b'system_u:object_r:hfcache_host_helper_archive_lock_t:s0'
 def capture():
  c=p._Capture(p.InspectionBudget());c.mounts=[(Path('/'),'tmpfs',set(),set())];return c
 read,write=os.pipe();pid=os.fork()
 if pid==0:
  os.close(read)
  try:
   os.setgroups([])
   for cap in range(64):
    present=libc.prctl(23,cap,0,0,0)
    if present==-1:break
    if cap not in {6,7}:assert libc.prctl(24,cap,0,0,0)==0
   assert libc.prctl(38,1,0,0,0)==0
   header=Header(0x20080522,0);data=(Data*2)();data[0].effective=data[0].permitted=0xc0
   assert libc.capset(ctypes.byref(header),data)==0
   assert os.getresuid()==(0,0,0)
   try:p._archive_lock_context(capture(),983,983)
   except PermissionError:pass
   else:raise AssertionError('capability-bounded root bypassed service DAC')
   os.setresgid(0,983,0);os.setresuid(0,983,0)
   actual=(Data*2)();assert libc.capget(ctypes.byref(header),actual)==0
   assert actual[0].effective==actual[1].effective==0 and actual[0].permitted==0xc0
   def audit(event,args):
    names={'hfcache.lock','hfcache.lock.intent'}
    if event=='open' and isinstance(args[0],str) and Path(args[0]).name in names:
     raise AssertionError('metadata child opened lock body')
   sys.addaudithook(audit)
   c=capture()
   for path in (p.LOCK,p.LOCK.with_name('hfcache.lock.intent')):
    identity,context=p._archive_lock_context(c,983,983,path=path)
    assert identity[3:6]==(983,983,1)
   c.revalidate()
   os.setresuid(0,0,0);os.setresgid(0,0,0)
   os.write(write,b'ok');os._exit(0)
  except BaseException:
   import traceback;traceback.print_exc();os._exit(1)
 os.close(write);assert os.read(read,16)==b'ok';os.close(read)
 assert os.waitpid(pid,0)[1]==0 and os.getresuid()==(0,0,0)
 print('actual DAC refusal and metadata-only mixed-ID child pass')
finally:
 for path in Path('/runtime').iterdir():os.chown(path,0,0)
 os.chown('/runtime',0,0)
"""
    result = subprocess.run(
        [
            unshare,
            "--user",
            "--map-auto",
            "--map-root-user",
            sys.executable,
            "-c",
            program,
            str(tmp_path),
        ],
        capture_output=True,
        timeout=15,
        check=False,
    )
    assert result.returncode == 0, result.stderr.decode()
    assert b"actual DAC refusal and metadata-only mixed-ID child pass" in result.stdout
