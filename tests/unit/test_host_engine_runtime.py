"""Decision150 exact owned child channel tests; no namespace/capability changes."""

from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pytest

from hfcache import host_peer as module
from hfcache.host_policy import InspectionBudget, InspectionError


def budget() -> module._Budget:
    return module._Budget(time.monotonic() + 2, module._MAX_WORK_FILES, 64 * 1024 * 1024)


def child_fixture(tmp_path, monkeypatch, *, change="", exit_code=0, delay=0):
    """A real disposable child exercises framing/ownership, not platform proof."""
    deployment = {"profile": "rootless", "api_principal": {"host_uid": os.getuid()}}
    deployment_body = json.dumps(deployment).encode()
    prepared: dict[str, Any] = {
        "schema_version": 1,
        "account_home": "/var/lib/hfcache",
        "keeper": {"pid": os.getpid(), "user_inode": 100},
        "namespaces": dict.fromkeys(module._NAMESPACES, 1),
        "storage": {"original_options": ["overlay.mountopt=nodev"]},
        "seccomp_filters": 1,
    }
    entered = {
        "namespaces": prepared["namespaces"] | {"user": 100},
        "capabilities": {
            "CapEff": 0x200004,
            "CapPrm": 0x200004,
            "CapBnd": 0x200004,
            "CapInh": 0,
            "CapAmb": 0,
            "NoNewPrivs": 1,
            "Seccomp": 2,
            "Seccomp_filters": 1,
        },
        "securebits": 0xCE,
        "mount_transitions_denied": True,
    }
    source = (
        f"#!{sys.executable}\n"
        "import sys,os,json,hashlib,time\n"
        "request=json.loads(sys.stdin.buffer.read())\n"
        "fields=open('/proc/self/stat').read().rpartition(') ')[2].split()\n"
        f"prepared={prepared!r}\nentered={entered!r}\n"
        "value={'schema_version':1,'deployment_sha256':"
        f"hashlib.sha256({deployment_body!r}).hexdigest(),"
        "'process':{'pid':os.getpid(),'start_ticks':int(fields[19])},"
        "'prepared':prepared,'entered':entered,'work':{'files':2,'bytes':17}}\n"
        f"{change}\n"
        f"time.sleep({delay!r})\n"
        "sys.stdout.buffer.write(json.dumps(value,separators=(',',':')).encode()+b'\\n'+b'[{\"raw\":true}]')\n"
        f"sys.exit({exit_code!r})\n"
    )
    child = tmp_path / "owned-observer"
    child.write_text(source)
    child.chmod(0o700)
    monkeypatch.setattr(module, "OBSERVER", str(child))
    monkeypatch.setattr(module, "_engine_prepare", lambda *_: copy.deepcopy(prepared))
    original_read = module._read

    def read(path, work, **kwargs):
        if path == module.DEPLOYMENT:
            work.consume(size=len(deployment_body))
            return deployment_body
        return original_read(path, work, **kwargs)

    monkeypatch.setattr(module, "_read", read)
    children = []
    original_popen = subprocess.Popen

    def popen(*args, **kwargs):
        result = original_popen(*args, **kwargs)
        children.append(result)
        return result

    monkeypatch.setattr(module.subprocess, "Popen", popen)
    return deployment, prepared, children


def test_original_raw_json_survives_real_child_preamble_and_work_is_charged(tmp_path, monkeypatch):
    deployment, _, children = child_fixture(tmp_path, monkeypatch)
    work = budget()
    assert module._engine_inspect(deployment, work) == b'[{"raw":true}]'
    assert len(children) == 1
    assert children[0].returncode == 0
    assert work.files >= 3
    assert work.bytes > 17
    assert not Path(f"/proc/{children[0].pid}").exists()


@pytest.mark.parametrize("maximum_files", [1024, 4096])
def test_repeated_preparation_and_child_reads_share_one_cumulative_budget(
    tmp_path, monkeypatch, maximum_files
):
    leaf = tmp_path / "owned-metadata"
    leaf.write_bytes(b"bounded metadata\n")
    change = (
        "work={'files':0,'bytes':0}\n"
        "for _ in range(1200):\n"
        f" with open({str(leaf)!r},'rb') as stream: data=stream.read()\n"
        " work['files']+=1;work['bytes']+=len(data)\n"
        "value['work']=work\n"
    )
    deployment, prepared, children = child_fixture(tmp_path, monkeypatch, change=change)
    preparations = []

    def prepare(_deployment, work):
        for _ in range(500):
            module._read(leaf, work, maximum=64)
        preparations.append(work.files)
        return copy.deepcopy(prepared)

    monkeypatch.setattr(module, "_engine_prepare", prepare)
    shared = InspectionBudget(maximum_files=maximum_files)
    work = module._observer_budget(
        {
            "schema_version": 1,
            "remaining_seconds": 5.0,
            "maximum_files": shared.maximum_files,
            "maximum_bytes": shared.maximum_bytes,
        },
        None,
        None,
    )
    if maximum_files == 1024:
        with pytest.raises(module.PeerError):
            module._engine_inspect(deployment, work)
        assert len(preparations) == 1
    else:
        assert module._engine_inspect(deployment, work) == b'[{"raw":true}]'
        assert len(preparations) == 2
        assert 2200 <= work.files <= maximum_files
        shared.consume(files=work.files, size=work.bytes)
        shared.consume(files=shared.maximum_files - shared.files)
        with pytest.raises(InspectionError):
            shared.consume(files=1)
    assert len(children) == 1
    assert children[0].returncode == 0
    assert not Path(f"/proc/{children[0].pid}").exists()


@pytest.mark.parametrize(
    "change",
    [
        "value['schema_version']=True",
        "value['extra']=0",
        "value['deployment_sha256']='0'*64",
        "value['process']['pid']+=1",
        "value['process']['pid']=float(value['process']['pid'])",
        "value['prepared']['schema_version']=True",
        "value['prepared']['seccomp_filters']=1.0",
        "value['process']['start_ticks']+=1",
        "value['prepared']['keeper']['user_inode']+=1",
        "value['prepared']['storage']['original_options']=[]",
        "value['prepared']['account_home']='/var/lib/hfcache/container-home'",
        "value['prepared'].pop('account_home')",
        "value['entered']['namespaces']['mnt']+=1",
        "value['entered']['namespaces']['mnt']=True",
        "value['entered']['namespaces']['user']+=1",
        "value['entered']['capabilities']['CapEff']=0",
        "value['entered']['capabilities']['CapBnd']=2**64-1",
        "value['entered']['capabilities']['CapAmb']=1",
        "value['entered']['capabilities']['Seccomp_filters']+=1",
        "value['entered']['capabilities']['NoNewPrivs']=True",
        "value['entered']['securebits']=0",
        "value['entered']['securebits']=float(0xCE)",
        "value['entered']['mount_transitions_denied']=False",
        "value['work']['bytes']=-1",
        "value['work']['files']=4097",
    ],
)
def test_independent_preamble_mutations_refuse_after_actual_child_reap(
    tmp_path, monkeypatch, change
):
    deployment, _, children = child_fixture(tmp_path, monkeypatch, change=change)
    with pytest.raises(module.PeerError):
        module._engine_inspect(deployment, budget())
    assert len(children) == 1
    assert children[0].returncode == 0


def test_nonzero_engine_cannot_publish_valid_preamble(tmp_path, monkeypatch):
    deployment, _, children = child_fixture(tmp_path, monkeypatch, exit_code=9)
    with pytest.raises(module.PeerError):
        module._engine_inspect(deployment, budget())
    assert children[0].returncode == 9


def test_exact_owned_read_child_timeout_reaps_and_refuses(tmp_path, monkeypatch):
    deployment, _, children = child_fixture(tmp_path, monkeypatch, delay=10)
    monkeypatch.setattr(module, "_ENGINE_SECONDS", 0.08)
    with pytest.raises(module.PeerError):
        module._engine_inspect(deployment, budget())
    assert len(children) == 1
    assert children[0].returncode is not None
    assert not Path(f"/proc/{children[0].pid}").exists()


def test_parent_storage_drift_after_child_refuses(tmp_path, monkeypatch):
    deployment, prepared, children = child_fixture(tmp_path, monkeypatch)
    calls = 0

    def prepare(*_):
        nonlocal calls
        calls += 1
        result = copy.deepcopy(prepared)
        if calls > 1:
            result["storage"]["original_options"] = []
        return result

    monkeypatch.setattr(module, "_engine_prepare", prepare)
    with pytest.raises(module.PeerError):
        module._engine_inspect(deployment, budget())
    assert children[0].returncode == 0


def test_pidfd_setter_failure_closes_the_actual_owned_descriptor(monkeypatch):
    original = module.os.pidfd_open
    descriptors = []

    def capture(pid, flags):
        result = original(pid, flags)
        descriptors.append(result)
        return result

    def fail(*_):
        raise PermissionError

    monkeypatch.setattr(module.os, "pidfd_open", capture)
    monkeypatch.setattr(module.os, "set_inheritable", fail)
    with pytest.raises(PermissionError):
        module._engine_pidfd(os.getpid())
    with pytest.raises(OSError, match="Bad file descriptor"):
        os.fstat(descriptors[0])


def test_no_arbitrary_engine_command_or_info_mode():
    assert module._engine_argv() == [
        "/usr/bin/podman",
        "--remote=false",
        "--storage-opt=overlay.mountopt=nodev",
        "--storage-opt=overlay.skip_mount_home=true",
        "container",
        "inspect",
        "hfcache-api",
    ]


def test_real_owned_process_executes_the_retained_root_owned_elf_fd():
    """Supplemental FD-exec mechanism; no guest USER/Podman acceptance claim."""
    program = """import os,sys,time
sys.path.insert(0,sys.argv[1])
from hfcache import host_peer as m
from pathlib import Path
m._ENGINE=Path('/usr/bin/true')
work=m._Budget(time.monotonic()+3,30,4096)
fd,identity=m._engine_binary(work)
assert os.fstat(fd).st_ino==identity['inode']
assert not os.get_inheritable(fd)
os.execve(fd,['/usr/bin/true'],{'PATH':'/usr/bin:/bin','LANG':'C'})
raise AssertionError('exec returned')
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", program, str(Path(module.__file__).parents[1])],
        capture_output=True,
        timeout=5,
        check=False,
    )
    assert result.returncode == 0, result.stderr.decode()
    assert result.stdout == b""


@pytest.mark.parametrize("field", ["CapEff", "CapPrm", "CapBnd"])
@pytest.mark.parametrize("wrong", [0, 4, 1 << 21, 0x200005, 0xC0, True, float(0x200004)])
def test_parent_refuses_forged_two_capability_masks_after_owned_child_reap(
    tmp_path, monkeypatch, field, wrong
):
    change = f"value['entered']['capabilities'][{field!r}]={wrong!r}"
    deployment, _, children = child_fixture(tmp_path, monkeypatch, change=change)
    with pytest.raises(module.PeerError):
        module._engine_inspect(deployment, budget())
    assert len(children) == 1
    assert children[0].returncode == 0
    assert not Path(f"/proc/{children[0].pid}").exists()
