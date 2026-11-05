"""ADR164: the notify worker has distinct conmon, foreground and payload PIDs."""

import copy
import json
import os
import stat
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from hfcache import host_peer as module
from tests.unit.test_host_peer import budget


@pytest.fixture
def executors(monkeypatch):
    uid = 983
    image = "a" * 64
    cid = "b" * 64
    groups = {role: "/user/" + role for role in ("api", "verification", "caddy")}
    expected = {
        role: ["/usr/bin/podman", "--remote=false", "run", "sha256:" + image, *tail]
        for role, tail in {
            "api": ["api"],
            "caddy": ["caddy"],
            "worker": ["/opt/hfcache/.venv/bin/python", "-m", "hfcache.verification_worker"],
        }.items()
    }
    units = {}
    for role, pid in (("api", 100), ("verification", 200), ("caddy", 300)):
        unit = "hfcache-" + role + ".service"
        units[unit] = {
            "Id": unit,
            "LoadState": "loaded",
            "ActiveState": "active",
            "SubState": "running",
            "MainPID": str(pid),
            "ControlPID": "0",
            "ControlGroup": groups[role],
            "InvocationID": "c" * 32,
            "FragmentPath": "/etc/systemd/user/" + unit,
            "DropInPaths": "",
            "Type": "notify" if role == "verification" else "exec",
            "NotifyAccess": "all" if role == "verification" else "none",
        }

    def process(pid, group, argv) -> dict[str, Any]:
        return {
            "pid": pid,
            "start_ticks": pid + 1000,
            "cgroup": group,
            "argv": argv,
            "credentials": {"Uid": [uid] * 4, "Gid": [uid] * 4, "NSpid": [pid]},
            "security": {
                "NoNewPrivs": "1",
                "Seccomp": "2",
                "CapEff": "0",
                "CapPrm": "0",
                "CapBnd": "0",
                "CapAmb": "0",
            },
            "uid_map": [[981, uid, 1]],
            "gid_map": [[981, uid, 1]],
            "namespaces": {},
        }

    processes = {
        100: process(100, groups["api"], expected["api"]),
        200: process(
            200,
            groups["verification"],
            [
                "/usr/bin/conmon",
                "--api-version",
                "1",
                "-c",
                cid,
                "-u",
                cid,
                "-n",
                "hfcache-verification",
            ],
        ),
        201: process(201, groups["verification"], expected["worker"]),
        202: process(
            202,
            "/user.slice/user-983.slice/user@983.service/user.slice/libpod-"
            + cid
            + ".scope/container",
            expected["worker"][4:],
        ),
        300: process(300, groups["caddy"], expected["caddy"]),
    }
    processes[202]["credentials"]["NSpid"] = [202, 1]
    worker = {
        "Id": cid,
        "Name": "hfcache-verification",
        "Image": image,
        "State": {
            "Pid": 202,
            "ConmonPid": 200,
            "Running": True,
            "Paused": False,
            "Status": "running",
        },
        "Config": {
            "Labels": {"io.hfcache.role": "worker", "io.hfcache.stack": "rootless"},
            "CreateCommand": expected["worker"],
        },
    }
    running = [
        {
            "Id": cid if role == "worker" else str(index) * 64,
            "Names": ["hfcache-verification" if role == "worker" else "hfcache-" + role],
            "State": "running",
            "Labels": {"io.hfcache.stack": "rootless", "io.hfcache.role": role},
            "ImageID": image,
            "Command": command[4:],
        }
        for index, (role, command) in enumerate(expected.items(), 1)
    ]
    original_iterdir = Path.iterdir
    monkeypatch.setattr(
        Path,
        "iterdir",
        lambda path: (
            iter(Path("/proc") / str(pid) for pid in processes)
            if path == Path("/proc")
            else original_iterdir(path)
        ),
    )
    monkeypatch.setattr(module, "_engine_prepare", lambda *_: {"keeper": {}})
    monkeypatch.setattr(module, "_intent_auxiliary", lambda *_: {})
    monkeypatch.setattr(module, "_indexed", lambda *_: b"indexed")
    monkeypatch.setattr(module, "_selected", lambda *_: Path("/opt/hfcache/releases/0.3.1"))
    monkeypatch.setattr(module, "_account_home", lambda *_: "/var/lib/hfcache")
    monkeypatch.setattr(
        module, "_expected_container", lambda *_args, role="api": copy.deepcopy(expected[role])
    )
    calls = []

    def command(argv, *_args, **_kwargs):
        unit = argv[3]
        calls.append(unit)
        requested = set(argv[-1].removeprefix("--property=").split(","))
        return "\n".join(
            key + "=" + value for key, value in units[unit].items() if key in requested
        ).encode()

    monkeypatch.setattr(module, "_command", command)

    def inspect(*_args, review=False, worker=False):
        assert review is not worker
        return json.dumps([worker_info] if worker else running).encode()

    monkeypatch.setattr(module, "_engine_inspect", inspect)
    worker_info = worker
    monkeypatch.setattr(
        module, "_process", lambda pid, *_args, **_kwargs: copy.deepcopy(processes[pid])
    )
    monkeypatch.setattr(module.os, "readlink", lambda _path: "/usr/bin/conmon")
    parents = {202: 200}

    def read(path, *_args, **_kwargs):
        if path == Path("/usr/bin/conmon"):
            return b"protected conmon"
        pid = int(path.parts[2])
        process = processes[pid]
        if path.name == "status":
            return ("Uid: " + " ".join(map(str, process["credentials"]["Uid"])) + "\n").encode()
        if path.name == "cgroup":
            return ("0::" + process["cgroup"] + "\n").encode()
        assert path.name == "stat"
        return (
            str(pid)
            + " (owned) S "
            + str(parents.get(pid, 1))
            + " "
            + "0 " * 17
            + str(process["start_ticks"])
        ).encode()

    monkeypatch.setattr(module, "_read", read)
    deployment = {
        "profile": "rootless",
        "api_principal": {"host_uid": uid, "host_gid": uid},
        "profile_evidence": {"app_image_sha256": image, "caddy_image_sha256": image},
    }
    return deployment, units, processes, worker, running, parents, calls


def test_actual_notify_shape_retains_distinct_monitor_foreground_and_payload(executors):
    deployment, *_ = executors
    facts = module._intent_executors(deployment, budget())
    worker = facts["roles"]["verification"]
    assert worker["pid"] == 200
    assert worker["foreground"]["pid"] == 201
    assert worker["payload"]["pid"] == 202


@pytest.mark.parametrize(
    "change",
    [
        "type",
        "notify",
        "monitor",
        "payload",
        "parent",
        "cid",
        "image",
        "name",
        "command",
        "monitor_cid",
        "uid",
        "gid",
        "group",
        "missing",
        "duplicate",
        "unknown",
        "unknown_process",
    ],
)
def test_notify_worker_independent_identity_joins_refuse(executors, change):  # noqa: PLR0912 - independent adversarial joins
    deployment, units, processes, worker, running, parents, _ = executors
    if change == "type":
        units["hfcache-verification.service"]["Type"] = "exec"
    elif change == "notify":
        units["hfcache-verification.service"]["NotifyAccess"] = "main"
    elif change == "monitor":
        worker["State"]["ConmonPid"] = 201
    elif change == "payload":
        worker["State"]["Pid"] = 200
    elif change == "parent":
        parents[202] = 201
    elif change == "cid":
        worker["Id"] = "d" * 64
    elif change == "image":
        worker["Image"] = "d" * 64
    elif change == "name":
        worker["Name"] = "other"
    elif change == "command":
        worker["Config"]["CreateCommand"] = ["wrong"]
    elif change == "monitor_cid":
        processes[200]["argv"][4] = "d" * 64
    elif change == "uid":
        processes[201]["credentials"]["Uid"][2] = 0
    elif change == "gid":
        processes[200]["credentials"]["Gid"][1] = 0
    elif change == "group":
        processes[201]["cgroup"] += "/child"
    elif change == "missing":
        del processes[201]
    elif change == "duplicate":
        processes[203] = processes[201] | {"pid": 203, "start_ticks": 1203}
    elif change == "unknown":
        running.append(running[0] | {"Id": "d" * 64})
    elif change == "unknown_process":
        processes[203] = processes[201] | {"pid": 203, "argv": ["unknown"]}
    with pytest.raises(module.PeerError):
        module._intent_executors(deployment, budget())


@pytest.mark.parametrize(
    "change",
    ["monitor_birth", "foreground_birth", "payload_birth", "invocation", "vanished", "unreadable"],
)
def test_notify_worker_revalidates_processes_and_manager_after_inspection(
    monkeypatch, executors, change
):
    deployment, units, processes, worker, *_ = executors
    original_inspect = module._engine_inspect
    original_process = module._process
    captured = {}

    def inspect(*args, **kwargs):
        result = original_inspect(*args, **kwargs)
        if kwargs.get("worker"):
            if change == "invocation":
                units["hfcache-verification.service"]["InvocationID"] = "e" * 32
            elif change in {"monitor_birth", "foreground_birth"}:
                processes[200 if change == "monitor_birth" else 201]["start_ticks"] += 1
            elif change in {"vanished", "unreadable"}:
                captured["failure"] = True
        return result

    def process(pid, *args, **kwargs):
        if pid == 201 and captured.get("failure"):
            raise FileNotFoundError if change == "vanished" else PermissionError
        result = original_process(pid, *args, **kwargs)
        if pid == worker["State"]["Pid"] and change == "payload_birth":
            processes[pid]["start_ticks"] += 1
        return result

    monkeypatch.setattr(module, "_engine_inspect", inspect)
    monkeypatch.setattr(module, "_process", process)
    with pytest.raises((module.PeerError, FileNotFoundError, PermissionError)):
        module._intent_executors(deployment, budget())


def test_notify_join_preserves_independent_manual_writer_payload_domain(monkeypatch, executors):
    deployment, *_ = executors
    deployment["profile_evidence"]["archive_mode"] = "manual-writer"
    context = "system_u:system_r:hfcache_archive_writer_t:s0:c1,c2"

    def writer(item, *_args):
        return {
            "pid": 202,
            "start_ticks": 1202,
            "cgroup": "/user.slice/user-983.slice/user@983.service/user.slice/libpod-"
            + item["Id"]
            + ".scope/container",
            "domain": context,
        }

    monkeypatch.setattr(module, "_intent_writer_payload", writer)
    facts = module._intent_executors(deployment, budget())
    assert facts["roles"]["verification"]["payload"]["domain"] == context


def test_monitor_executable_name_alone_cannot_substitute_inspected_identity(monkeypatch, executors):
    deployment, *_ = executors
    monkeypatch.setattr(module.os, "readlink", lambda _path: "/tmp/conmon")
    with pytest.raises(module.PeerError):
        module._intent_executors(deployment, budget())


@pytest.mark.parametrize("kind", ["manager", "keeper", "broker-launch", "broker"])
@pytest.mark.parametrize(
    "drift", [None, "metadata", "process", "link", "parent", "kernel_before", "kernel_after"]
)
def test_inert_actual_role_shapes_do_not_read_unused_executable_bodies(  # noqa: PLR0915 - fixed inert roles and independent revalidation
    monkeypatch, executors, kind, drift
):
    deployment, _, processes, _, _, parents, _ = executors
    manager = {"pid": 400, "start_ticks": 1400, "group": "/user/manager"}
    broker = {"pid": 403, "start_ticks": 1403, "group": "/user/broker"}
    keeper_maps = [[0, 983, 1], [1, 165536, 65536]]
    keeper = {
        "pid": 402,
        "start_ticks": 1402,
        "uid": 983,
        "gid": 983,
        "uid_map": copy.deepcopy(keeper_maps),
        "gid_map": copy.deepcopy(keeper_maps),
    }
    machine = "f" * 32
    executable, pid, parent, group, context, argv = {
        "manager": (
            "/usr/lib/systemd/systemd",
            400,
            1,
            "/user/manager/init.scope",
            "unconfined_t",
            ["/usr/lib/systemd/systemd", "--user"],
        ),
        "pam": (
            "/usr/lib/systemd/systemd-executor",
            401,
            400,
            "/user/manager/init.scope",
            "init_t",
            ["(sd-pam)"],
        ),
        "keeper": (
            "/usr/libexec/catatonit/catatonit",
            402,
            400,
            "/user/keeper",
            "container_runtime_t",
            ["catatonit", "-P"],
        ),
        "broker-launch": (
            "/usr/bin/dbus-broker-launch",
            403,
            400,
            "/user/broker",
            "unconfined_dbusd_t",
            ["/usr/bin/dbus-broker-launch", "--scope", "user"],
        ),
        "broker": (
            "/usr/bin/dbus-broker",
            404,
            403,
            "/user/broker",
            "unconfined_dbusd_t",
            [
                "dbus-broker",
                "--log",
                "1",
                "--controller",
                "2",
                "--machine-id",
                machine,
                "--max-bytes",
                "3",
                "--max-fds",
                "4",
                "--max-matches",
                "5",
            ],
        ),
    }[kind]
    processes[pid] = copy.deepcopy(processes[201]) | {
        "pid": pid,
        "start_ticks": pid + 1000,
        "cgroup": group,
        "argv": argv,
    }
    parents[pid] = parent
    if kind == "keeper":
        processes[pid]["uid_map"] = copy.deepcopy(keeper_maps)
        processes[pid]["gid_map"] = copy.deepcopy(keeper_maps)
    monkeypatch.setattr(module, "_engine_prepare", lambda *_: {"keeper": keeper})
    monkeypatch.setattr(
        module,
        "_intent_auxiliary",
        lambda *_: {"manager": manager, "broker": broker, "machine_id": machine},
    )
    links = []

    def readlink(path):
        if str(path) != f"/proc/{pid}/exe":
            return "/usr/bin/conmon"
        links.append(path)
        return "/tmp/substitution" if drift == "link" and len(links) == 2 else executable

    monkeypatch.setattr(module.os, "readlink", readlink)
    original_kind = module._intent_auxiliary_kind

    def classify(*args):
        result = original_kind(*args)
        if drift == "process":
            processes[pid]["argv"] = ["unknown"]
        elif drift == "parent":
            parents[pid] += 1
        return result

    monkeypatch.setattr(module, "_intent_auxiliary_kind", classify)
    original_read = module._read
    body_attempts = []

    def read(path, *args, **kwargs):
        if path == Path(executable):
            body_attempts.append(path)
            raise PermissionError
        if path == Path(f"/proc/{pid}/attr/current"):
            return ("system_u:system_r:" + context + ":s0").encode()
        return original_read(path, *args, **kwargs)

    metadata_calls = []
    kernel_identity = {
        "st_dev": 1,
        "st_ino": 20,
        "st_mode": stat.S_IFREG | 0o755,
        "st_uid": 0,
        "st_gid": 0,
        "st_nlink": 1,
        "st_size": 10,
        "st_mtime_ns": 1,
        "st_ctime_ns": 1,
    }
    original_stat = module.os.stat
    kernel_stats = []

    def kernel_stat(path, *args, **kwargs):
        if str(path) == f"/proc/{pid}/exe":
            kernel_stats.append(path)
            wrong = drift == "kernel_before" or (drift == "kernel_after" and len(kernel_stats) == 2)
            return SimpleNamespace(**(kernel_identity | ({"st_ino": 21} if wrong else {})))
        return original_stat(path, *args, **kwargs)

    monkeypatch.setattr(module.os, "stat", kernel_stat)

    def metadata(path, work):
        assert path == Path(executable)
        work.consume()
        metadata_calls.append(path)
        identity = kernel_identity | (
            {"st_ino": 21} if drift == "metadata" and len(metadata_calls) == 2 else {}
        )
        return {
            executable: module._engine_storage_identity(
                cast("os.stat_result", SimpleNamespace(**identity))
            )
        }

    monkeypatch.setattr(module, "_read", read)
    monkeypatch.setattr(module, "_intent_executable", metadata, raising=False)
    if drift is None:
        facts = module._intent_executors(deployment, budget())
        assert facts["inert_counts"] == {kind: 1}
        assert metadata_calls == [Path(executable), Path(executable)]
    else:
        with pytest.raises(module.PeerError):
            module._intent_executors(deployment, budget())
    assert body_attempts == []


@pytest.mark.parametrize(
    "change",
    [
        None,
        "owner",
        "writable",
        "not_executable",
        "not_regular",
        "hardlink",
        "actual_systemd_executor_size",
        "ancestor",
        "rejoin",
        "fstat_failure",
    ],
)
def test_real_opath_executable_metadata_rejoins_and_closes_without_body_read(monkeypatch, change):
    path = Path("/usr/bin/true")
    monkeypatch.setattr(module, "_INTENT_EXECUTABLES", frozenset({str(path)}))
    leaf = path.stat()
    ancestor = Path("/usr").stat()
    original_open, original_fstat, original_stat, original_close = (
        os.open,
        os.fstat,
        os.stat,
        os.close,
    )
    opened = set()
    fields = (
        "st_dev",
        "st_ino",
        "st_mode",
        "st_uid",
        "st_gid",
        "st_nlink",
        "st_size",
        "st_mtime_ns",
        "st_ctime_ns",
    )

    def patched(info, **changes):
        return SimpleNamespace(**({name: getattr(info, name) for name in fields} | changes))

    def opening(*args, **kwargs):
        assert args[1] & os.O_PATH
        assert args[1] & os.O_CLOEXEC
        if args[0] != "/":
            assert args[1] & os.O_NOFOLLOW
        descriptor = original_open(*args, **kwargs)
        opened.add(descriptor)
        return descriptor

    def closing(descriptor):
        opened.remove(descriptor)
        original_close(descriptor)

    def fstat(descriptor):
        info = original_fstat(descriptor)
        if (info.st_dev, info.st_ino) == (leaf.st_dev, leaf.st_ino):
            if change == "fstat_failure":
                raise PermissionError
            changes = {
                "owner": {"st_uid": 1000},
                "writable": {"st_mode": info.st_mode | 0o020},
                "not_executable": {"st_mode": stat.S_IFREG | 0o644},
                "not_regular": {"st_mode": stat.S_IFLNK | 0o777},
                "hardlink": {"st_nlink": 2},
                "actual_systemd_executor_size": {"st_size": 1_413_592},
            }.get(change, {})
            return patched(info, **changes)
        if change == "ancestor" and (info.st_dev, info.st_ino) == (
            ancestor.st_dev,
            ancestor.st_ino,
        ):
            return patched(info, st_mode=info.st_mode | 0o020)
        return info

    def rejoin(*args, **kwargs):
        info = original_stat(*args, **kwargs)
        if change == "actual_systemd_executor_size" and info.st_ino == leaf.st_ino:
            return patched(info, st_size=1_413_592)
        return (
            patched(info, st_ino=info.st_ino + 1)
            if change == "rejoin" and args[0] == path.name
            else info
        )

    monkeypatch.setattr(module.os, "open", opening)
    monkeypatch.setattr(module.os, "close", closing)
    monkeypatch.setattr(module.os, "fstat", fstat)
    monkeypatch.setattr(module.os, "stat", rejoin)
    monkeypatch.setattr(module.os, "read", lambda *_: pytest.fail("executable body was read"))
    work = budget()
    if change in {None, "actual_systemd_executor_size"}:
        expected = module._engine_storage_identity(leaf)
        if change == "actual_systemd_executor_size":
            expected["bytes"] = 1_413_592  # actual CentOS systemd-executor; no body read
        assert module._intent_executable(path, work)[str(path)] == expected
        assert work.files > 0
        assert work.bytes == 0
    else:
        with pytest.raises((module.PeerError, PermissionError)):
            module._intent_executable(path, work)
    assert opened == set()


def test_inert_executable_unknown_path_refuses_before_any_open(monkeypatch):
    monkeypatch.setattr(
        module.os, "open", lambda *_args, **_kwargs: pytest.fail("unknown path opened")
    )
    with pytest.raises(module.PeerError):
        module._intent_executable(Path("/tmp/arbitrary-executable"), budget())


@pytest.fixture
def pam_executor(monkeypatch, executors):
    deployment, _, processes, _, _, parents, _ = executors
    pid, manager_pid = 401, 400
    group = "/user.slice/user-983.slice/user@983.service"
    unit = {
        "Id": "user@983.service",
        "Type": "notify-reload",
        "User": "983",
        "PAMName": "systemd-user",
        "MainPID": str(manager_pid),
        "InvocationID": "e" * 32,
        "ControlGroup": group,
    }
    auxiliary = {
        "manager": {
            "pid": manager_pid,
            "start_ticks": 1400,
            "group": group,
            "unit": unit,
            "files": {"/usr/lib/systemd/system/user@.service": "public vendor digest"},
        },
        "broker": {"pid": 403, "start_ticks": 1403, "group": "/broker"},
        "machine_id": "f" * 32,
    }
    process = copy.deepcopy(processes[201]) | {
        "pid": pid,
        "start_ticks": 1401,
        "cgroup": group + "/init.scope",
        "argv": ["(sd-pam)"],
    }
    process["credentials"]["NSpid"] = [pid]
    process["uid_map"] = process["gid_map"] = [[0, 0, 4294967295]]
    process["security"].update({"NoNewPrivs": "0", "Seccomp": "0", "CapBnd": "000001ffffffffff"})
    processes[pid] = process
    parents[pid] = manager_pid
    context = ["system_u:system_r:init_t:s0"]
    status = {
        "Name": "(sd-pam)",
        "Pid": str(pid),
        "Tgid": str(pid),
        "NSpid": str(pid),
        "PPid": str(manager_pid),
        "TracerPid": "0",
        "Groups": "",
        "Uid": "983 983 983 983",
        "Gid": "983 983 983 983",
        "State": "S (sleeping)",
        "CapInh": "0000000000000000",
        "SigPnd": "0000000000000000",
        "ShdPnd": "0000000000000000",
    }
    metadata = {"directory": {"uid": 983, "inode": 50}, "exe_link": {"uid": 0, "inode": 51}}
    monkeypatch.setattr(module, "_intent_auxiliary", lambda *_: copy.deepcopy(auxiliary))
    original_read, original_readlink = module._read, module.os.readlink

    def read(path, *args, **kwargs):
        if str(path) in {f"/proc/{candidate}/status" for candidate in (401, 402)}:
            candidate = path.parts[2]
            actual_status = status | (
                {"Pid": candidate, "Tgid": candidate, "NSpid": candidate}
                if candidate != str(pid)
                else {}
            )
            return "\n".join(key + ": " + value for key, value in actual_status.items()).encode()
        if str(path) in {f"/proc/{candidate}/attr/current" for candidate in (401, 402)}:
            return context[0].encode()
        return original_read(path, *args, **kwargs)

    def readlink(path):
        if path == Path(f"/proc/{pid}/exe"):
            raise PermissionError
        return original_readlink(path)

    def pam_metadata(actual_pid, principal, work):
        assert actual_pid in {401, 402}
        assert principal == (983, 983)
        work.consume(files=6)
        return copy.deepcopy(metadata)

    monkeypatch.setattr(module, "_read", read)
    monkeypatch.setattr(module.os, "readlink", readlink)
    monkeypatch.setattr(module, "_intent_pam_metadata", pam_metadata, raising=False)
    return deployment, process, auxiliary, status, metadata, context, processes, parents


def test_actual_nondumpable_pam_shape_has_closed_lineage_without_image_read(pam_executor):
    deployment, *_ = pam_executor
    assert module._intent_executors(deployment, budget())["inert_counts"] == {"pam": 1}


@pytest.mark.parametrize(
    "change",
    [
        "type",
        "user",
        "pam_name",
        "invocation",
        "manager_pid",
        "older_birth",
        "parent",
        "group",
        "context",
        "uid",
        "gid",
        "nspid",
        "maps",
        "effective_cap",
        "permitted_cap",
        "ambient_cap",
        "name",
        "tgid",
        "tracer",
        "groups",
        "inherited_cap",
        "awake",
        "pending",
        "shared_pending",
        "duplicate",
        "unknown_argv",
    ],
)
def test_pam_lineage_independent_constraints_refuse(pam_executor, change):  # noqa: PLR0912 - closed independent PAM constraints
    deployment, process, auxiliary, status, _, context, processes, parents = pam_executor
    unit = auxiliary["manager"]["unit"]
    if change in {"type", "user", "pam_name", "invocation", "manager_pid"}:
        key, value = {
            "type": ("Type", "exec"),
            "user": ("User", "0"),
            "pam_name": ("PAMName", "other"),
            "invocation": ("InvocationID", "bad"),
            "manager_pid": ("MainPID", "999"),
        }[change]
        unit[key] = value
    elif change == "older_birth":
        process["start_ticks"] = 1399
    elif change == "parent":
        parents[401] = 999
    elif change == "group":
        process["cgroup"] += "/child"
    elif change == "context":
        context[0] = "system_u:system_r:unconfined_t:s0"
    elif change == "uid":
        process["credentials"]["Uid"][2] = 0
    elif change == "gid":
        process["credentials"]["Gid"][1] = 0
    elif change == "nspid":
        process["credentials"]["NSpid"] = [401, 1]
    elif change == "maps":
        process["uid_map"] = [[0, 983, 1]]
    elif change in {"effective_cap", "permitted_cap", "ambient_cap"}:
        process["security"][
            {"effective_cap": "CapEff", "permitted_cap": "CapPrm", "ambient_cap": "CapAmb"}[change]
        ] = "1"
    elif change in {
        "name",
        "tgid",
        "tracer",
        "groups",
        "inherited_cap",
        "awake",
        "pending",
        "shared_pending",
    }:
        key, value = {
            "name": ("Name", "other"),
            "tgid": ("Tgid", "999"),
            "tracer": ("TracerPid", "1"),
            "groups": ("Groups", "983"),
            "inherited_cap": ("CapInh", "1"),
            "awake": ("State", "R (running)"),
            "pending": ("SigPnd", "1"),
            "shared_pending": ("ShdPnd", "1"),
        }[change]
        status[key] = value
    elif change == "duplicate":
        processes[402] = copy.deepcopy(process) | {"pid": 402, "start_ticks": 1402}
        processes[402]["credentials"]["NSpid"] = [402]
        parents[402] = 400
    elif change == "unknown_argv":
        process["argv"] = ["unknown"]
    with pytest.raises((module.PeerError, PermissionError)):
        module._intent_executors(deployment, budget())


@pytest.mark.parametrize(
    "change",
    ["metadata", "status", "context", "parent", "birth", "manager_invocation", "manager_file"],
)
def test_pam_coherent_revalidation_refuses_drift(monkeypatch, pam_executor, change):
    deployment, process, auxiliary, status, metadata, context, _, parents = pam_executor
    original = module._intent_pam
    calls = []

    def capture(*args, **kwargs):
        result = original(*args, **kwargs)
        calls.append(result)
        if len(calls) == 1:
            if change == "metadata":
                metadata["exe_link"]["inode"] += 1
            elif change == "status":
                status["TracerPid"] = "1"
            elif change == "context":
                context[0] = "system_u:system_r:unconfined_t:s0"
            elif change == "parent":
                parents[401] = 999
            elif change == "birth":
                process["start_ticks"] += 1
            elif change == "manager_invocation":
                auxiliary["manager"]["unit"]["InvocationID"] = "d" * 32
            elif change == "manager_file":
                auxiliary["manager"]["files"]["/usr/lib/systemd/system/user@.service"] = "changed"
        return result

    monkeypatch.setattr(module, "_intent_pam", capture)
    with pytest.raises(module.PeerError):
        module._intent_executors(deployment, budget())


def test_actual_nondumpable_child_proc_objects_need_no_exe_readlink(monkeypatch):
    if os.geteuid() == 0:
        pytest.skip("actual same-UID ptrace read refusal requires an unprivileged test owner")
    program = (
        "import ctypes,sys;assert ctypes.CDLL(None).prctl(4,0)==0;"
        "print('ready',flush=True);sys.stdin.read(1)"
    )
    with subprocess.Popen(
        [sys.executable, "-I", "-c", program],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
    ) as child:
        try:
            assert child.stdout is not None
            assert child.stdout.readline() == "ready\n"
            with pytest.raises(PermissionError):
                Path(f"/proc/{child.pid}/exe").readlink()
            monkeypatch.setattr(
                module.os, "readlink", lambda *_: pytest.fail("PAM exe link was read")
            )
            captured = module._intent_pam_metadata(child.pid, (os.getuid(), os.getgid()), budget())
            assert captured["directory"]["uid"] == os.getuid()
            assert captured["exe_link"]["uid"] == captured["exe_link"]["gid"] == 0
            assert stat.S_ISLNK(captured["exe_link"]["mode"])
            assert (
                module._intent_pam_metadata(child.pid, (os.getuid(), os.getgid()), budget())
                == captured
            )
            child.communicate(input="x", timeout=5)
            assert child.returncode == 0
        finally:
            if child.poll() is None:
                child.kill()
                child.wait()


@pytest.mark.parametrize("bad", [None, "Type", "User", "PAMName", "InvocationID", "ControlGroup"])
def test_fixed_auxiliary_manager_requires_loaded_vendor_pam_authority(monkeypatch, bad):
    deployment = {"api_principal": {"host_uid": 983}}
    monkeypatch.setattr(module, "_account_home", lambda *_: "/var/lib/hfcache")
    monkeypatch.setattr(
        module, "_process", lambda pid, *_args, **_kwargs: {"start_ticks": pid + 1000}
    )
    queries = []

    def command(argv, *_args, **kwargs):
        assert kwargs["uid"] == 983
        name = argv[3]
        user = name == "dbus-broker.service"
        queries.append(name)
        rows = {
            "Id": name,
            "LoadState": "loaded",
            "ActiveState": "active",
            "SubState": "running",
            "MainPID": "403" if user else "400",
            "ControlPID": "0",
            "ControlGroup": "/broker" if user else "/user.slice/user-983.slice/user@983.service",
            "FragmentPath": "/usr/lib/systemd/user/dbus-broker.service"
            if user
            else "/usr/lib/systemd/system/user@.service",
            "DropInPaths": "",
        }
        if not user:
            rows.update(
                {
                    "Type": "notify-reload",
                    "User": "983",
                    "PAMName": "systemd-user",
                    "InvocationID": "e" * 32,
                }
            )
            if bad:
                rows[bad] = "wrong"
        assert set(rows) == set(argv[-1].removeprefix("--property=").split(","))
        return "\n".join(key + "=" + value for key, value in rows.items()).encode()

    def read(path, *_args, **kwargs):
        assert kwargs["protected"] is True
        return b"f" * 32 if path == Path("/etc/machine-id") else b"protected vendor unit"

    monkeypatch.setattr(module, "_command", command)
    monkeypatch.setattr(module, "_read", read)
    if bad:
        with pytest.raises(module.PeerError):
            module._intent_auxiliary(deployment, budget())
        assert queries == ["user@983.service"]
    else:
        proof = module._intent_auxiliary(deployment, budget())
        assert proof["manager"]["unit"]["PAMName"] == "systemd-user"
        assert proof["manager"]["files"]["/usr/lib/systemd/system/user@.service"]
        assert queries == ["user@983.service", "dbus-broker.service"]


@pytest.fixture
def detached_keeper():
    mappings = [[0, 983, 1], [1, 165536, 65536]]
    keeper = {
        "pid": 21279,
        "start_ticks": 2712684,
        "uid": 983,
        "gid": 983,
        "user_inode": 4026532303,
        "uid_map": copy.deepcopy(mappings),
        "gid_map": copy.deepcopy(mappings),
    }
    process = {
        "pid": 21279,
        "start_ticks": 2712684,
        "argv": ["catatonit", "-P"],
        "cgroup": (
            "/user.slice/user-983.slice/user@983.service/user.slice/podman-pause-4dc47458.scope"
        ),
        "credentials": {"Uid": [983] * 4, "Gid": [983] * 4},
        "uid_map": copy.deepcopy(mappings),
        "gid_map": copy.deepcopy(mappings),
    }
    auxiliary = {
        "manager": {"pid": 21205, "start_ticks": 2687095},
        "broker": {"pid": 21288, "start_ticks": 2712693},
    }
    return process, keeper, auxiliary


@pytest.mark.parametrize("parent", [1, 21205])
def test_actual_authenticated_keeper_accepts_init_adoption_or_manager_only(detached_keeper, parent):
    process, keeper, auxiliary = detached_keeper
    assert (
        module._intent_auxiliary_kind(
            process,
            "/usr/libexec/catatonit/catatonit",
            "unconfined_u:unconfined_r:container_runtime_t:s0-s0:c0.c1023",
            parent,
            keeper,
            auxiliary,
        )
        == "keeper"
    )


@pytest.mark.parametrize(
    "change",
    [
        "parent",
        "pid",
        "birth",
        "exe",
        "argv",
        "domain",
        "uid",
        "gid",
        "uid_map",
        "gid_map",
        "prepared_owner",
        "prepared_map",
    ],
)
def test_detached_keeper_requires_all_existing_prepared_identity_joins(detached_keeper, change):
    process, keeper, auxiliary = detached_keeper
    executable = "/usr/libexec/catatonit/catatonit"
    context = "unconfined_u:unconfined_r:container_runtime_t:s0-s0:c0.c1023"
    parent = 1
    if change == "parent":
        parent = 2
    elif change == "pid":
        process["pid"] += 1
    elif change == "birth":
        process["start_ticks"] += 1
    elif change == "exe":
        executable = "/tmp/catatonit"
    elif change == "argv":
        process["argv"].append("unknown")
    elif change == "domain":
        context = "unconfined_u:unconfined_r:unconfined_t:s0"
    elif change == "uid":
        process["credentials"]["Uid"][2] = 0
    elif change == "gid":
        process["credentials"]["Gid"][1] = 0
    elif change == "uid_map":
        process["uid_map"][1][1] += 1
    elif change == "gid_map":
        process["gid_map"][1][1] += 1
    elif change == "prepared_owner":
        keeper["uid"] = 984
    elif change == "prepared_map":
        keeper["gid_map"][1][1] += 1
    assert (
        module._intent_auxiliary_kind(process, executable, context, parent, keeper, auxiliary)
        is None
    )
