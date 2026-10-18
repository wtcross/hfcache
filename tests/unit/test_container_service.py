"""Decision127: closed runtime authority and preservation of unknown executors."""

import importlib.machinery
import importlib.util
import json
import os
import re
from pathlib import Path
from types import SimpleNamespace

import pytest

SCRIPT = Path(__file__).parents[2] / "scripts/container-service.py"
SPEC = importlib.util.spec_from_file_location("container_service", SCRIPT)
assert SPEC is not None
assert SPEC.loader is not None
runtime = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runtime)
PROFILE = {
    "schema_version": 1,
    "service_uid": 981,
    "service_gid": 981,
    "app_image": "sha256:" + "a" * 64,
    "caddy_image": "sha256:" + "b" * 64,
}


def info(*, running=False, pid=0):
    return {
        "Id": "c" * 64,
        "Image": PROFILE["app_image"],
        "Config": {"Labels": {"io.hfcache.role": "worker", "io.hfcache.stack": "rootless"}},
        "State": {"Running": running, "Pid": pid},
    }


def test_privilege_and_secret_boundaries_apply_to_every_actual_payload():
    for role in ("api", "worker", "caddy", "client"):
        argv = runtime.command(PROFILE, role)
        assert argv[:4] == ["/usr/bin/podman", "--remote=false", "run", "--pull=never"]
        assert {
            "--http-proxy=false",
            "--userns=keep-id:uid=981,gid=981",
            "--user=981:981",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges",
            "--read-only",
            "--read-only-tmpfs=false",
        } <= set(argv)
        assert not any(
            part
            in {"--privileged", "--replace", "--init", "--network=host", "--pid=host", "--env-host"}
            or "label=disable" in part
            or "podman.sock" in part
            for part in argv
        )
        if role != "client":
            assert "--rm" not in argv
        secrets = [
            argv[i + 1].split(",", 1)[0] for i, part in enumerate(argv) if part == "--secret"
        ]
        expected = {
            "api": {"hfcache.api", "hfcache.api-reader", "hfcache.mcp-reader", "hf-token"},
            "worker": set(),
            "caddy": {"hfcache.tls-cert", "hfcache.tls-key"},
            "client": {"hfcache.api"},
        }
        assert set(secrets) == expected[role]


def test_human_role_matrix_matches_actual_runtime_network_secrets_and_executable():
    guide = (SCRIPT.parents[1] / "docs/containers.md").read_text()
    section = guide.split("### Role profile matrix", 1)[1].split("System hfcache.target", 1)[0]
    rows = {}
    for line in section.splitlines():
        if re.match(r"\| `(api|worker|caddy|client)` \|", line):
            cells = [cell.strip() for cell in line.split("|")[1:-1]]
            rows[cells[0].strip("`")] = cells
    assert set(rows) == {"api", "worker", "caddy", "client"}
    for role, cells in rows.items():
        argv = runtime.command(PROFILE, role)
        assert len(cells) == 5
        assert f"--network={cells[1].strip('`')}" in argv
        secret_names = {
            argv[index + 1].split(",", 1)[0]
            for index, item in enumerate(argv)
            if item == "--secret"
        }
        assert set(re.findall(r"`([^`]+)`", cells[2])) == secret_names
        executable = re.findall(r"`([^`]+)`", cells[3])
        assert len(executable) == 1
        assert any(
            item == executable[0] or item == f"--entrypoint={executable[0]}" for item in argv
        )
        archive = [item for item in argv if item.startswith("/srv/hfcache:")]
        if role in {"api", "worker"}:
            assert archive == ["/srv/hfcache:/srv/hfcache:ro"]
            assert "archive read-only" in cells[4]
        else:
            assert archive == []
            assert "no archive" in cells[4] or "no server stores/archive" in cells[4]


def test_nas_and_private_peer_paths_are_exposed_only_to_executors():
    commands = {
        role: runtime.command(PROFILE, role) for role in ("api", "worker", "caddy", "client")
    }
    for role in ("api", "worker"):
        assert "/srv/hfcache:/srv/hfcache:ro" in commands[role]
        assert "/run/hfcache/hfcache.lock:/run/hfcache/hfcache.lock:rw,z" in commands[role]
        assert "/etc/hfcache:/etc/hfcache:ro" in commands[role]
    for role in ("client", "caddy"):
        assert not any(
            "/srv/hfcache" in part or "/verification" in part or "hfcache.lock" in part
            for part in commands[role]
        )
    assert "--network=none" in commands["worker"]
    assert "--network=none" in commands["client"]
    assert "/run/hfcache/verification:/run/hfcache/verification:rw,z" in commands["worker"]
    assert "/run/hfcache/verification:/run/hfcache/verification:ro,z" in commands["api"]
    assert "--sdnotify=container" in commands["worker"]
    assert "--container-listener" in commands["worker"]
    assert not any(
        "--sdnotify" in item or item == "--container-listener" for item in commands["api"]
    )
    assert (
        f"--security-opt=seccomp={runtime.PROFILE_DIRECTORY}/worker-seccomp.json"
        in commands["worker"]
    )
    for role in ("worker", "client"):
        for hidden in (
            "/run/credentials",
            "/etc/credstore",
            "/etc/credstore.encrypted",
            "/etc/hfcache/credentials",
        ):
            assert f"--tmpfs={hidden}:ro,nosuid,nodev,noexec,mode=000" in commands[role]


def test_every_release_profile_is_pinned_to_the_executing_physical_tree():
    for role in ("api", "worker", "client"):
        argv = runtime.command(PROFILE, role)
        assert f"{runtime.PROFILE_DIRECTORY}:/etc/hfcache/containers:ro" in argv
        assert argv.index("/etc/hfcache:/etc/hfcache:ro") < argv.index(
            f"{runtime.PROFILE_DIRECTORY}:/etc/hfcache/containers:ro"
        )
    assert (
        f"{runtime.PROFILE_DIRECTORY}/client.toml:/etc/hfcache/client.toml:ro"
        in runtime.command(PROFILE, "client")
    )
    assert f"{runtime.PROFILE_DIRECTORY}/Caddyfile:/etc/caddy/Caddyfile:ro" in runtime.command(
        PROFILE, "caddy"
    )
    assert runtime.PROFILE == runtime.PROFILE_DIRECTORY / "runtime.json"


def test_current_switch_selects_new_profiles_without_retargeting_running_helper(tmp_path):
    prefix = tmp_path / "deployment"
    for version in ("0.2.0", "0.2.1"):
        script = prefix / "releases" / version / "scripts/container-service.py"
        script.parent.mkdir(parents=True)
        script.write_bytes(SCRIPT.read_bytes())
    current = prefix / "current"
    current.symlink_to("releases/0.2.0")
    launcher = tmp_path / "hfcache-container-service"
    launcher.symlink_to(current / "scripts/container-service.py")

    def selected():
        loader = importlib.machinery.SourceFileLoader("selected_runtime", str(launcher))
        spec = importlib.util.spec_from_loader("selected_runtime", loader)
        assert spec is not None
        assert spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    previous = selected()
    current.unlink()
    current.symlink_to("releases/0.2.1")
    following = selected()
    for module, version in ((previous, "0.2.0"), (following, "0.2.1")):
        physical = prefix / "releases" / version / "rendered"
        assert physical / "runtime.json" == module.PROFILE
        assert f"{physical}:/etc/hfcache/containers:ro" in module.command(PROFILE, "api")


def test_option_shaped_cli_data_cannot_become_engine_authority():
    data = [
        "--client-config",
        "/etc/hfcache/client.toml",
        "--json",
        "operations",
        "lookup",
        "--",
        "--privileged",
    ]
    argv = runtime.command(PROFILE, "client", data)
    boundary = argv.index(PROFILE["app_image"])
    assert argv[boundary + 1 :] == ["/opt/hfcache/.venv/bin/hfcache", *data]
    assert "--privileged" not in argv[:boundary]
    with pytest.raises(ValueError, match="unknown fixed"):
        runtime.command(PROFILE, "worker", data)
    with pytest.raises(ValueError, match="unknown fixed"):
        runtime.command(PROFILE, "anything")


def test_only_actual_valid_unit_identity_reaches_executor_environment(monkeypatch):
    monkeypatch.setenv("INVOCATION_ID", "e" * 32)
    for role in ("api", "worker"):
        assert "--env=INVOCATION_ID=" + "e" * 32 in runtime.command(PROFILE, role)
    for role in ("client", "caddy"):
        assert not any("INVOCATION_ID" in part for part in runtime.command(PROFILE, role))
    monkeypatch.setenv("INVOCATION_ID", "untrusted caller declaration")
    assert not any("INVOCATION_ID" in part for part in runtime.command(PROFILE, "api"))


@pytest.mark.parametrize(
    "change",
    [
        {"State": {}},
        {"State": {"Running": False}},
        {"State": {"Running": True, "Pid": 0}},
        {"State": {"Running": False, "Pid": "0"}},
        {"State": []},
        {"Config": []},
        {"Id": "unknown"},
        {"Image": "sha256:" + "d" * 64},
    ],
)
def test_unknown_inspect_metadata_never_authorizes_cleanup(monkeypatch, change):
    observed = info() | change
    monkeypatch.setattr(runtime, "inspect_container", lambda _: observed)
    calls = []
    monkeypatch.setattr(runtime.subprocess, "run", lambda *args, **_kwargs: calls.append(args))
    with pytest.raises((RuntimeError, TypeError)):
        runtime.prepare_start(PROFILE, "worker")
    assert calls == []


def test_running_executor_start_is_refused_without_replacement(monkeypatch):
    monkeypatch.setattr(runtime, "inspect_container", lambda _: info(running=True, pid=123))
    calls = []
    monkeypatch.setattr(runtime.subprocess, "run", lambda *args, **_kwargs: calls.append(args))
    with pytest.raises(RuntimeError, match="existing executor"):
        runtime.prepare_start(PROFILE, "worker")
    assert calls == []


def test_stop_waits_without_deadline_then_removes_only_confirmed_stopped_id(monkeypatch):
    states = iter([info(running=True, pid=123), info()])
    monkeypatch.setattr(runtime, "inspect_container", lambda _: next(states))
    calls = []
    monkeypatch.setattr(runtime.subprocess, "run", lambda argv, **_kwargs: calls.append(argv))
    runtime.drain(PROFILE, "worker")
    assert calls == [
        ["/usr/bin/podman", "--remote=false", "stop", "--time", "-1", "c" * 64],
        ["/usr/bin/podman", "--remote=false", "rm", "c" * 64],
    ]


def test_uncertain_drain_preserves_container_without_removal(monkeypatch):
    monkeypatch.setattr(runtime, "inspect_container", lambda _: info(running=True, pid=123))
    calls = []
    monkeypatch.setattr(runtime.subprocess, "run", lambda argv, **_kwargs: calls.append(argv))
    with pytest.raises(RuntimeError, match="not drained"):
        runtime.drain(PROFILE, "worker")
    assert len(calls) == 1
    assert "rm" not in calls[0]


def test_name_reuse_during_drain_preserves_replacement_container(monkeypatch):
    replacement = info() | {"Id": "d" * 64}
    states = iter([info(running=True, pid=123), replacement])
    monkeypatch.setattr(runtime, "inspect_container", lambda _: next(states))
    calls = []
    monkeypatch.setattr(runtime.subprocess, "run", lambda argv, **_kwargs: calls.append(argv))
    with pytest.raises(RuntimeError, match="identity changed"):
        runtime.drain(PROFILE, "worker")
    assert calls == [["/usr/bin/podman", "--remote=false", "stop", "--time", "-1", "c" * 64]]


@pytest.mark.parametrize("error", [KeyError("Id"), TypeError("State"), OSError("engine")])
def test_unknown_stop_errors_remain_blocked_instead_of_falling_through(monkeypatch, capsys, error):
    monkeypatch.setattr(runtime.sys, "argv", ["helper", "stop", "worker"])
    monkeypatch.setattr(runtime, "load_profile", lambda: PROFILE)

    def fail(*args):
        raise error

    monkeypatch.setattr(runtime, "drain", fail)

    class Blocked(BaseException):
        pass

    def held(*args):
        raise Blocked

    monkeypatch.setattr(runtime.time, "sleep", held)
    with pytest.raises(Blocked):
        runtime.main()
    assert "retained state requires inspection" in capsys.readouterr().err


def test_profile_rejects_symlink_and_unprotected_source(tmp_path):
    path = tmp_path / "runtime.json"
    path.write_text(json.dumps(PROFILE))
    path.chmod(0o666)
    with pytest.raises(ValueError, match="unsafe"):
        runtime.load_profile(path)
    link = tmp_path / "link"
    link.symlink_to(path)
    with pytest.raises(OSError, match="Too many levels"):
        runtime.load_profile(link)


def test_documented_bare_image_inspect_spelling_keeps_exact_identity(monkeypatch):
    observed = info()
    observed["Image"] = PROFILE["app_image"].removeprefix("sha256:")
    monkeypatch.setattr(runtime, "inspect_container", lambda _: observed)
    assert runtime.owned_container(PROFILE, "worker")["Id"] == "c" * 64


@pytest.mark.parametrize("options", ["rw,nosuid,nodev", "rw,ro", "nosuid,nodev"])
def test_executor_requires_actual_read_only_nfs_mount_before_start(options):
    table = f"100 90 0:90 / /srv/hfcache {options} - nfs4 nas:/archive rw,vers=4.2\n"
    with pytest.raises(RuntimeError, match="read-only NAS"):
        runtime.archive_readonly(table)


def test_mount_barrier_uses_kernel_metadata_without_opening_archive(monkeypatch):
    table = "100 90 0:90 / /srv/hfcache ro,nosuid,nodev - nfs4 nas:/archive rw,vers=4.2\n"
    assert runtime.archive_readonly(table) is None
    with pytest.raises(RuntimeError, match="read-only NAS"):
        runtime.archive_readonly("")


def test_fixed_profile_supplies_missing_service_runtime_but_refuses_wrong_one(
    tmp_path, monkeypatch
):
    path = tmp_path / "runtime.json"
    path.write_text(json.dumps(PROFILE))
    path.chmod(0o640)
    original = os.fstat

    def root_metadata(fd):
        observed = original(fd)
        return SimpleNamespace(
            **{
                name: 0 if name == "st_uid" else getattr(observed, name)
                for name in (
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
            }
        )

    monkeypatch.setattr(runtime.os, "fstat", root_metadata)
    monkeypatch.setattr(runtime.os, "geteuid", lambda: 981)
    monkeypatch.setattr(runtime.os, "getegid", lambda: 981)
    monkeypatch.delenv("XDG_RUNTIME_DIR", raising=False)
    assert runtime.load_profile(path) == PROFILE
    assert os.environ["XDG_RUNTIME_DIR"] == "/run/user/981"
    path.write_text(json.dumps(PROFILE)[:-1] + ', "service_uid":1000}')
    with pytest.raises(ValueError, match="duplicate"):
        runtime.load_profile(path)
    path.write_text(json.dumps(PROFILE))
    monkeypatch.setenv("XDG_RUNTIME_DIR", "/run/user/1000")
    with pytest.raises(ValueError, match="identity"):
        runtime.load_profile(path)
