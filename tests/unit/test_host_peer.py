"""Decision150 fixed-role metadata adversaries and real owned process evidence."""

import ast
import copy
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from hfcache import host_peer as module
from hfcache.host_policy import AuthoritySnapshot, InspectionBudget
from hfcache.host_protocol import LivePeer


def budget(seconds=2):
    return module._Budget(time.monotonic() + seconds, 1024, 64 * 1024 * 1024)


def test_real_process_capture_has_original_start_namespace_and_maps():
    process = module._process(os.getpid(), budget())
    assert process["pid"] == os.getpid()
    assert process["start_ticks"] > 0
    assert process["credentials"]["Uid"] == [os.getuid()] * 4
    assert process["credentials"]["Gid"] == [os.getgid()] * 4
    assert process["credentials"]["NSpid"][-1] == os.getpid()
    assert module._mapped(process["uid_map"], os.getuid()) == os.getuid()
    assert set(process["namespaces"]) == set(module._NAMESPACES)
    assert all(value > 0 for value in process["namespaces"].values())


def test_real_process_start_race_refuses(monkeypatch):
    original_read = module._read
    seen = 0

    def changed_stat(path, work, **kwargs):
        nonlocal seen
        data = original_read(path, work, **kwargs)
        if path.name == "stat":
            seen += 1
            if seen == 2:
                prefix, separator, fields = data.rpartition(b") ")
                values = fields.split()
                values[19] = str(int(values[19]) + 1).encode()
                return prefix + separator + b" ".join(values)
        return data

    monkeypatch.setattr(module, "_read", changed_stat)
    with pytest.raises(module.PeerError):
        module._process(os.getpid(), budget())
    assert seen == 2


def test_native_root_capture_does_not_require_other_uid_namespace_links(monkeypatch):
    def hidden_namespace(*_args, **_kwargs):
        raise PermissionError

    monkeypatch.setattr(module.os, "readlink", hidden_namespace)
    captured = module._process(os.getpid(), budget(), namespaces=False)
    assert captured["pid"] == os.getpid()
    assert captured["start_ticks"] > 0
    assert captured["namespaces"] == {}
    assert captured["credentials"]["Uid"] == [os.getuid()] * 4
    assert captured["argv"]
    assert captured["cgroup"].startswith("/")
    with pytest.raises(PermissionError):
        module._process(os.getpid(), budget())


@pytest.mark.parametrize(
    "body",
    [b"", b"0 0 0", b"0 0 3\n2 9 2", b"0 0 3\n4 2 2", b"0 0 -1", b"0 0 4294967297"],
)
def test_namespace_map_rejects_aliases_overlaps_and_empty_ranges(body):
    with pytest.raises(module.PeerError):
        module._maps(body)


def test_real_owned_inspection_cli_timeout_reaps_only_its_child(monkeypatch):
    original = subprocess.Popen
    children = []

    def capture(*args, **kwargs):
        child = original(*args, **kwargs)
        children.append(child)
        return child

    monkeypatch.setattr(module.subprocess, "Popen", capture)
    with pytest.raises(module.PeerError):
        module._command(
            [sys.executable, "-I", "-c", "import time;time.sleep(10)"],
            budget(0.04),
            uid=os.getuid(),
        )
    assert len(children) == 1
    assert children[0].returncode is not None
    assert children[0].poll() is not None


def manager(profile="native") -> dict[str, str]:
    properties = module._NATIVE_HARDENING if profile == "native" else module._ROOTLESS_MANAGER
    result = dict(properties) | {
        "Id": "hfcache-api.service",
        "LoadState": "loaded",
        "ActiveState": "active",
        "SubState": "running",
        "MainPID": "100",
        "InvocationID": "a" * 32,
        "ControlGroup": "/system.slice/hfcache-api.service",
        "FragmentPath": "/etc/systemd/system/hfcache-api.service",
        "DropInPaths": "",
        "ExecStart": "known",
        "User": "hfcache",
        "Group": "hfcache",
    }
    if profile == "native":
        result.update(
            SystemCallArchitectures="native",
            RestrictAddressFamilies="AF_UNIX AF_INET AF_INET6",
            ReadWritePaths="/srv/hfcache",
        )
    return result


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("Id", "hfcache-verification.service"),
        ("LoadState", "not-found"),
        ("ActiveState", "inactive"),
        ("MainPID", "0"),
        ("InvocationID", ""),
        ("DropInPaths", "/etc/systemd/system/hfcache-api.service.d/override.conf"),
        ("NoNewPrivileges", "no"),
        ("CapabilityBoundingSet", "cap_sys_ptrace"),
        ("ProtectProc", "default"),
        ("ProcSubset", "all"),
        ("ProtectSystem", "no"),
        ("RestrictAddressFamilies", "AF_UNIX AF_INET AF_INET6 AF_PACKET"),
        ("ReadWritePaths", "/srv/hfcache /etc"),
        ("RootDirectory", "/elsewhere"),
    ],
)
def test_loaded_native_manager_must_match_closed_indexed_security(monkeypatch, key, value):
    observed = manager() | {key: value}
    monkeypatch.setattr(
        module,
        "_command",
        lambda *_args, **_kwargs: "\n".join(f"{k}={v}" for k, v in observed.items()).encode(),
    )
    with pytest.raises(module.PeerError):
        module._show("native", os.getuid(), budget())


@pytest.mark.parametrize("observer_uid", [0, 983])
def test_real_manager_cli_child_uses_closed_profile_transport_environment(
    monkeypatch, observer_uid
):
    # Model only the validated observer identity; the owned child retains the
    # test runner's real credentials and performs no manager or network action.
    monkeypatch.setattr(module.os, "getuid", lambda: observer_uid)
    monkeypatch.setattr(module.os, "geteuid", lambda: observer_uid)
    monkeypatch.setenv("SYSTEMCTL_FORCE_BUS", "0")
    monkeypatch.setenv("DBUS_SESSION_BUS_ADDRESS", "unix:path=/untrusted/session")
    monkeypatch.setenv("DBUS_SYSTEM_BUS_ADDRESS", "unix:path=/untrusted/system")
    monkeypatch.setenv("XDG_RUNTIME_DIR", "/untrusted/runtime")
    monkeypatch.setenv("HFCACHE_BUS_TEST_POISON", "must-not-reach-child")
    script = (
        "import json,os;print(json.dumps({key:os.environ.get(key)for key in "
        "['SYSTEMCTL_FORCE_BUS','DBUS_SESSION_BUS_ADDRESS','DBUS_SYSTEM_BUS_ADDRESS',"
        "'XDG_RUNTIME_DIR','HFCACHE_BUS_TEST_POISON']}))"
    )
    body = module._command([sys.executable, "-I", "-c", script], budget(), uid=observer_uid)
    assert json.loads(body) == {
        "SYSTEMCTL_FORCE_BUS": "1" if observer_uid else None,
        "DBUS_SESSION_BUS_ADDRESS": f"unix:path=/run/user/{observer_uid}/bus",
        "DBUS_SYSTEM_BUS_ADDRESS": None,
        "XDG_RUNTIME_DIR": f"/run/user/{observer_uid}",
        "HFCACHE_BUS_TEST_POISON": None,
    }


def test_manager_command_is_fixed_and_selected_by_profile_only(monkeypatch):
    calls = []

    def show(argv, _work, **_kwargs):
        calls.append(argv)
        return "\n".join(f"{key}={value}" for key, value in manager().items()).encode()

    monkeypatch.setattr(module, "_command", show)
    assert module._show("native", os.getuid(), budget()) == manager()
    assert calls[0][:5] == [
        "/usr/bin/systemctl",
        "--system",
        "show",
        "hfcache-api.service",
        "--no-pager",
    ]


def rootless_fixture():
    uid, gid = os.getuid(), os.getgid()
    image, cid = "b" * 64, "c" * 64
    expected = [
        "/usr/bin/podman",
        "--remote=false",
        "run",
        "--userns=keep-id:uid=981,gid=981",
        "--user=981:981",
        "--cap-drop=ALL",
        "--env=INVOCATION_ID=" + "a" * 32,
        "--volume",
        module.HELPER_PARENT + ":" + module.HELPER_PARENT + ":ro",
        "sha256:" + image,
        "/opt/hfcache/.venv/bin/hfcache",
        "serve",
        "--server-config",
        "/etc/hfcache/containers/server.toml",
    ]
    info = {
        "Id": cid,
        "Name": "hfcache-api",
        "Image": image,
        "State": {"Running": True, "Status": "running", "Paused": False, "Pid": 200},
        "Config": {
            "Labels": {"io.hfcache.stack": "rootless", "io.hfcache.role": "api"},
            "User": "981:981",
            "CreateCommand": expected,
            "Env": ["INVOCATION_ID=" + "a" * 32],
        },
        "HostConfig": {
            "ReadonlyRootfs": True,
            "Privileged": False,
            "CapAdd": [],
            "CapDrop": sorted(module._EXPANDED_CAP_DROP),
            "NetworkMode": "pasta",
            "PortBindings": {},
            "UsernsMode": "private",
            "SecurityOpt": ["no-new-privileges"],
        },
        "Mounts": [
            {
                "Type": "bind",
                "Source": module.HELPER_PARENT,
                "Destination": module.HELPER_PARENT,
                "RW": False,
            }
        ],
    }
    process = {
        "pid": 200,
        "start_ticks": 1234,
        "credentials": {"Uid": [uid] * 4, "Gid": [gid] * 4, "NSpid": [200, 1]},
        "security": {
            "NoNewPrivs": "1",
            "Seccomp": "2",
            "CapEff": "0",
            "CapBnd": "0",
            "CapPrm": "0",
            "CapAmb": "0",
        },
        "namespaces": dict.fromkeys(module._NAMESPACES, 10),
        "cgroup": "/user.slice/libpod-" + cid + ".scope",
        "argv": ["/opt/hfcache/.venv/bin/python", *expected[-4:]],
        "uid_map": [[0, 100000, 981], [981, uid, 1], [982, 100981, 64554]],
        "gid_map": [[0, 200000, 981], [981, gid, 1], [982, 200981, 64554]],
    }
    # The complete original command after the image is the only accepted API argv.
    process["argv"] = [
        "/opt/hfcache/.venv/bin/python",
        *expected[expected.index("sha256:" + image) + 1 :],
    ]
    state = manager("rootless")
    state["ExecStart"] = (
        "{ path=/usr/local/libexec/hfcache-container-service ; "
        "argv[]=/usr/local/libexec/hfcache-container-service api ; ignore_errors=no ; pid=100 ; }"
    )
    manager_process = copy.deepcopy(process) | {
        "pid": 100,
        "argv": expected,
        "cgroup": state["ControlGroup"],
    }
    deployment = {
        "api_principal": {"host_uid": uid, "host_gid": gid},
        "profile_evidence": {"app_image_sha256": image},
    }
    return state, deployment, info, expected, process, manager_process


def install_rootless_fixture(monkeypatch, fixture):
    state, deployment, info, expected, process, manager_process = fixture
    monkeypatch.setattr(
        module, "_engine_inspect", lambda *_args, **_kwargs: json.dumps([info]).encode()
    )
    monkeypatch.setattr(module, "_expected_container", lambda *_: expected)
    monkeypatch.setattr(
        module,
        "_process",
        lambda pid, _work: copy.deepcopy(manager_process if pid == 100 else process),
    )
    monkeypatch.setattr(module, "_helper_mount", lambda *_: {"parent_gid": os.getgid()})
    return state, deployment


@pytest.mark.parametrize("payload_leaf", ["", "/container"])
def test_rootless_container_requires_actual_api_init_and_host_mapping(monkeypatch, payload_leaf):
    fixture = rootless_fixture()
    fixture[4]["cgroup"] += payload_leaf
    state, deployment = install_rootless_fixture(monkeypatch, fixture)
    process, container = module._container(state, deployment, budget())
    assert process["credentials"]["NSpid"] == [200, 1]
    assert container["cid"] == "c" * 64
    assert (
        container["userns_mode"] == "private"
    )  # Raw encoding is not a substitute for kernel maps.
    assert process["cgroup"] == fixture[4]["cgroup"]


@pytest.mark.parametrize(
    "scope_suffix",
    [
        "libpod-" + "d" * 64 + ".scope/container",
        "libpod-" + "c" * 63 + ".scope/container",
        "notlibpod-" + "c" * 64 + ".scope/container",
        "libpod-" + "c" * 64 + ".scopex/container",
        "libpod-" + "c" * 64 + ".scope/containerx",
        "libpod-" + "c" * 64 + ".scope/container/nested",
        "libpod-" + "c" * 64 + ".scope/arbitrary",
        "libpod-" + "c" * 64 + ".scope/",
    ],
)
def test_rootless_api_cgroup_refuses_foreign_or_unrecognized_payload_paths(
    monkeypatch, scope_suffix
):
    fixture = rootless_fixture()
    fixture[4]["cgroup"] = "/user.slice/" + scope_suffix
    state, deployment = install_rootless_fixture(monkeypatch, fixture)
    with pytest.raises(module.PeerError):
        module._container(state, deployment, budget())


@pytest.mark.parametrize("payload_leaf", ["", "/container"])
@pytest.mark.parametrize(
    "change",
    [
        "wrong-role",
        "wrong-image",
        "paused",
        "not-running",
        "privileged",
        "rw-root",
        "cap-added",
        "cap-missing",
        "cap-duplicate",
        "host-network",
        "published-api",
        "wrong-user",
        "unknown-security",
        "helper-rw",
        "helper-source",
        "create-drift",
        "wrong-env",
        "inside-not-init",
        "wrong-host-uid",
        "wrong-map",
        "wrong-program",
    ],
)
def test_rootless_peer_metadata_refuses_each_independent_boundary(  # noqa: PLR0912 - independent named security mutations
    monkeypatch, change, payload_leaf
):
    fixture = rootless_fixture()
    _state, _deployment, info, _expected, process, _manager = fixture
    process["cgroup"] += payload_leaf
    config, host = info["Config"], info["HostConfig"]
    if change == "wrong-role":
        config["Labels"]["io.hfcache.role"] = "worker"
    elif change == "wrong-image":
        info["Image"] = "d" * 64
    elif change == "paused":
        info["State"]["Paused"] = True
    elif change == "not-running":
        info["State"]["Running"] = False
    elif change == "privileged":
        host["Privileged"] = True
    elif change == "rw-root":
        host["ReadonlyRootfs"] = False
    elif change == "cap-added":
        host["CapAdd"] = ["CAP_SYS_PTRACE"]
    elif change == "cap-missing":
        host["CapDrop"].pop()
    elif change == "cap-duplicate":
        host["CapDrop"][-1] = host["CapDrop"][0]
    elif change == "host-network":
        host["NetworkMode"] = "host"
    elif change == "published-api":
        host["PortBindings"] = {"123/tcp": [{}]}
    elif change == "wrong-user":
        config["User"] = "0:0"
    elif change == "unknown-security":
        host["SecurityOpt"] = ["unconfined"]
    elif change == "helper-rw":
        info["Mounts"][0]["RW"] = True
    elif change == "helper-source":
        info["Mounts"][0]["Source"] = "/fake"
    elif change == "create-drift":
        config["CreateCommand"] = ["untrusted"]
    elif change == "wrong-env":
        config["Env"] = ["INVOCATION_ID=" + "b" * 32]
    elif change == "inside-not-init":
        process["credentials"]["NSpid"] = [200, 2]
    elif change == "wrong-host-uid":
        process["credentials"]["Uid"] = [os.getuid() + 1] * 4
    elif change == "wrong-map":
        process["uid_map"][1][1] += 1
    elif change == "wrong-program":
        process["argv"] = ["worker"]
    state, deployment = install_rootless_fixture(monkeypatch, fixture)
    with pytest.raises(module.PeerError):
        module._container(state, deployment, budget())


def test_late_owned_observer_waits_for_actual_exit_without_parent_signals(tmp_path, monkeypatch):
    observer = tmp_path / "observer"
    observer.write_text(
        f"#!{sys.executable}\nimport sys,time\nsys.stdin.buffer.read()\n"
        "time.sleep(.10)\nprint('{}')\n"
    )
    observer.chmod(0o700)
    monkeypatch.setattr(module, "OBSERVER", str(observer))
    original = subprocess.Popen
    children = []

    def same_uid_child(*args, **kwargs):
        for key in ("user", "group", "extra_groups"):
            kwargs.pop(key)
        child = original(*args, **kwargs)
        children.append(child)
        return child

    monkeypatch.setattr(module.subprocess, "Popen", same_uid_child)
    started = time.monotonic()
    with pytest.raises(module.PeerError):
        module._observe_as_account(
            {"remaining_seconds": 0.03}, os.getuid(), os.getgid(), profile="rootless"
        )
    assert time.monotonic() - started >= 0.10
    assert len(children) == 1
    assert children[0].returncode == 0


def test_failed_owned_observer_retains_operator_diagnostic_without_logging_stdout(
    tmp_path, monkeypatch, capfd
):
    observer = tmp_path / "observer"
    observer.write_text(
        f"#!{sys.executable}\nimport sys\nsys.stdin.buffer.read()\n"
        "print('private observer stdout')\n"
        "sys.stderr.write('protected observer refused: phase=container-validation\\n')\n"
        "raise SystemExit(20)\n"
    )
    observer.chmod(0o700)
    monkeypatch.setattr(module, "OBSERVER", str(observer))
    original = subprocess.Popen
    children = []

    def same_uid_child(*args, **kwargs):
        for key in ("user", "group", "extra_groups"):
            kwargs.pop(key)
        child = original(*args, **kwargs)
        children.append(child)
        return child

    monkeypatch.setattr(module.subprocess, "Popen", same_uid_child)
    with pytest.raises(module.PeerError):
        module._observe_as_account(
            {"remaining_seconds": 2.0}, os.getuid(), os.getgid(), profile="rootless"
        )
    out, error = capfd.readouterr()
    assert out == ""
    assert error == "protected observer refused: phase=container-validation\n"
    assert len(children) == 1
    assert children[0].returncode == 20


def test_peer_proof_matches_live_original_pid_and_same_generation(monkeypatch):
    work = InspectionBudget()
    snapshot = cast(
        "AuthoritySnapshot",
        SimpleNamespace(
            api_principal=(os.getuid(), os.getgid()),
            budget=work,
            deployment_sha256="a" * 64,
            profile="native",
        ),
    )
    monkeypatch.setattr(
        module.pwd,
        "getpwnam",
        lambda _: SimpleNamespace(
            pw_uid=os.getuid(), pw_gid=os.getgid(), pw_dir="/var/lib/hfcache"
        ),
    )
    value: dict[str, Any] = {
        "schema_version": 1,
        "deployment_sha256": "a" * 64,
        "profile": "native",
        "process": {
            "pid": os.getpid(),
            "start_ticks": 12345,
            "credentials": {"Uid": [os.getuid()] * 4, "Gid": [os.getgid()] * 4},
            "security": {
                "NoNewPrivs": "1",
                "Seccomp": "2",
                "CapEff": "0",
                "CapBnd": "0",
                "CapPrm": "0",
                "CapAmb": "0",
            },
        },
        "manager": {"InvocationID": "b" * 32},
        "container": None,
        "work": {"files": 1, "bytes": 64},
    }
    monkeypatch.setattr(module, "_observe_as_account", lambda *_, **__: json.dumps(value).encode())
    first, second = socket.socketpair()
    try:
        peer = LivePeer(first)
        try:
            proof = module.authenticate(snapshot, peer, remaining_seconds=1)
            module.revalidate(proof, snapshot, peer, remaining_seconds=1)
            value["manager"]["InvocationID"] = "c" * 32
            with pytest.raises(module.PeerError):
                module.revalidate(proof, snapshot, peer, remaining_seconds=1)
            value["process"]["pid"] += 1
            with pytest.raises(module.PeerError):
                module.authenticate(snapshot, peer, remaining_seconds=1)
        finally:
            peer.close()
    finally:
        first.close()
        second.close()


def test_peer_bootstrap_syntax_is_python312_and_runtime_imports_stdlib_only():
    tree = ast.parse(Path(module.__file__).read_text(), feature_version=(3, 12))
    direct_imports = [node for node in tree.body if isinstance(node, ast.ImportFrom)]
    assert all(not (node.module or "").startswith("hfcache") for node in direct_imports)


def test_bootstrap_loading_consumes_same_clock_files_and_bytes(monkeypatch):
    monkeypatch.setattr(module.time, "monotonic", lambda: 105.0)
    request = {
        "schema_version": 1,
        "remaining_seconds": 10.0,
        "maximum_files": 20,
        "maximum_bytes": 1000,
    }
    result = module._observer_budget(request, {"files": 4, "bytes": 500}, 100.0)
    assert result.remaining() == 5.0
    assert result.files == 4
    assert result.bytes == 500
    with pytest.raises(module.PeerError):
        result.consume(size=501)


@pytest.mark.parametrize(
    "work",
    [
        {"files": 21, "bytes": 0},
        {"files": 0, "bytes": 1001},
        {"files": True, "bytes": 1},
        {"files": 1, "bytes": 0, "extra": 1},
    ],
)
def test_bootstrap_over_budget_or_invalid_counts_refuse_before_facts(work):
    request = {
        "schema_version": 1,
        "remaining_seconds": 10.0,
        "maximum_files": 20,
        "maximum_bytes": 1000,
    }
    with pytest.raises(module.PeerError):
        module._observer_budget(request, work, None)


def test_elapsed_bootstrap_cannot_start_a_fresh_observer_deadline(monkeypatch):
    monkeypatch.setattr(module.time, "monotonic", lambda: 111.0)
    request = {
        "schema_version": 1,
        "remaining_seconds": 10.0,
        "maximum_files": 20,
        "maximum_bytes": 1000,
    }
    with pytest.raises(module.PeerError):
        module._observer_budget(request, {"files": 4, "bytes": 100}, 100.0)


@pytest.mark.parametrize("profile", ["native", "rootless"])
def test_real_owned_observer_launch_uses_trusted_profile_identity(tmp_path, monkeypatch, profile):
    observer = tmp_path / "observer"
    observer.write_text(f"#!{sys.executable}\nimport sys\nsys.stdin.buffer.read()\nprint('{{}}')\n")
    observer.chmod(0o700)
    monkeypatch.setattr(module, "OBSERVER", str(observer))
    original = subprocess.Popen
    selected = []

    def launch(*args, **kwargs):
        selected.append({key: kwargs.pop(key) for key in ("user", "group", "extra_groups")})
        return original(*args, **kwargs)

    monkeypatch.setattr(module.subprocess, "Popen", launch)
    result = module._observe_as_account({"remaining_seconds": 2.0}, 983, 983, profile=profile)
    assert json.loads(result) == {}
    uid = 0 if profile == "native" else 983
    assert selected == [{"user": uid, "group": uid, "extra_groups": ()}]


def test_unrecognized_profile_cannot_launch_observer(monkeypatch):
    def no_child(*_args, **_kwargs):
        pytest.fail("invalid profile launched an observer")

    monkeypatch.setattr(module.subprocess, "Popen", no_child)
    with pytest.raises(module.PeerError):
        module._observe_as_account({"remaining_seconds": 2.0}, 983, 983, profile="other")


def native_uv_fixture(monkeypatch, interpreter):
    deployment = {
        "api_principal": {"host_uid": 983, "host_gid": 983},
        "release": {"version": "0.2.2", "selector_target": "releases/0.2.2"},
        "profile_evidence": {"python_target_relative": "cpython-3.14.6/bin/python3.14"},
    }
    entry = "/opt/hfcache/releases/0.2.2/.venv/bin/hfcache"
    argv = [interpreter, entry, "serve", "--server-config", "/etc/hfcache/server.toml"]
    observed = {
        "pid": 100,
        "start_ticks": 1000,
        "credentials": {"Uid": [983] * 4, "Gid": [983] * 4, "NSpid": [100]},
        "security": {
            "NoNewPrivs": "1",
            "Seccomp": "2",
            "CapEff": "0",
            "CapBnd": "0",
            "CapPrm": "0",
            "CapAmb": "0",
        },
        "namespaces": {},
        "cgroup": "/system.slice/hfcache-api.service",
        "argv": argv,
        "uid_map": [[0, 0, 4294967295]],
        "gid_map": [[0, 0, 4294967295]],
    }
    state = manager() | {
        "ExecStart": "{ path="
        + entry
        + " ; argv[]="
        + " ".join(argv[1:])
        + " ; ignore_errors=no ; pid=100 ; }"
    }

    def process(_pid, _budget, *, namespaces):
        assert namespaces is False
        return copy.deepcopy(observed)

    monkeypatch.setattr(module, "_process", process)
    monkeypatch.setattr(module, "_indexed", lambda *_: ("#!" + interpreter + "\n").encode())
    return state, deployment, observed


@pytest.mark.parametrize("alias", ["python", "python3", "python3.14"])
@pytest.mark.parametrize("selection", ["releases/0.2.2", "current"])
def test_native_console_script_actual_uv_alias_shape_matches_authenticated_snapshot(
    monkeypatch, alias, selection
):
    interpreter = "/opt/hfcache/" + selection + "/.venv/bin/" + alias
    state, deployment, expected = native_uv_fixture(monkeypatch, interpreter)
    assert module._native_process(state, deployment, budget()) == expected


@pytest.mark.parametrize(
    "interpreter",
    ["/usr/bin/python3", "/tmp/python3", "/opt/hfcache/releases/0.2.2/.venv/bin/python3.13"],
)
def test_native_console_script_swapped_or_unverified_alias_refuses(monkeypatch, interpreter):
    state, deployment, _ = native_uv_fixture(monkeypatch, interpreter)
    with pytest.raises(module.PeerError):
        module._native_process(state, deployment, budget())


def test_intent_review_rejects_unclassified_init_scope_processes():
    keeper = {"pid": 20, "start_ticks": 30}
    manager = {"pid": 21, "start_ticks": 31, "argv": ["/usr/lib/systemd/systemd", "--user"]}
    assert module._intent_inert(manager, "/usr/lib/systemd/systemd", keeper)
    assert module._intent_inert(
        {"pid": 20, "start_ticks": 30, "argv": ["catatonit", "-P"]},
        "/usr/libexec/catatonit/catatonit",
        keeper,
    )
    assert not module._intent_inert(
        manager | {"argv": ["python", "unknown.py"]}, "/usr/bin/python", keeper
    )
    assert not module._intent_inert(
        {"pid": 99, "start_ticks": 30, "argv": ["catatonit", "-P"]},
        "/usr/libexec/catatonit/catatonit",
        keeper,
    )
    assert not module._intent_inert(
        manager | {"argv": ["/usr/lib/systemd/systemd", "--user", "--unclassified"]},
        "/usr/lib/systemd/systemd",
        keeper,
    )
