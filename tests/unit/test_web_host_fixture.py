"""Owned WEB006 metadata adversaries and real launcher lifetime checks.

Metadata fixtures do not establish installed peer, Caddy, namespace or UI proof.
"""

import asyncio
import copy
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from hfcache.host_models import unavailable_host_status

ROOT = Path(__file__).absolute().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "web_host_fixture", ROOT / "scripts/check-web-host-fixture.py"
)
assert SPEC is not None
assert SPEC.loader is not None
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


@pytest.mark.parametrize(
    "identity",
    [
        "web-004-83a4380d0c82465fa225c00bba53359c",
        "web-006-source26-a4df9de51e0f477c90da6980b5653076",
    ],
)
def test_explicit_disposable_guest_names(identity):
    assert module.guest_identity(identity)


@pytest.mark.parametrize(
    "identity", [None, "", "production", "web-006-source26", "web-006-source0-" + "a" * 32]
)
def test_other_guest_names_remain_refused(identity):
    assert not module.guest_identity(identity)


def fixture(profile="native") -> tuple[dict[str, Any], dict[str, Any]]:
    manifest = {
        "assets": {"manifest_sha256": "a" * 64},
        "profiles": {
            profile: {
                "deployment": {"sha256": "d" * 64},
                "policy": {"sha256": "e" * 64},
                "origin": "https://127.0.0.1:33333",
            }
        },
    }
    ready: dict[str, Any] = {
        "state": "ready",
        "deployment_sha256": "d" * 64,
        "policy_sha256": "e" * 64,
        "asset_manifest_sha256": "a" * 64,
        "instance_id": "b" * 32,
        "api_manager": {
            "scope": "system" if profile == "native" else "user",
            "name": "hfcache-api.service",
            "main_pid": 101 if profile == "native" else 106,
            "main_start_ticks": 1001 if profile == "native" else 1006,
            "invocation_id": "c" * 32,
        },
        "helper_parent": {"device": 7, "inode": 100, "uid": 0, "gid": 983, "mode": 0o750},
        "isolation": {
            "caddy_helper_mount": False,
            "worker_helper_mount": False,
            "same_uid_peer_refused": True,
            "other_tgid_peer_refused": True,
            "helper_af_unix_only": True,
            "helper_archive_masked": True,
            "helper_hub_secrets_masked": True,
        },
        "owned_processes": [],
        "owned_cgroups": [],
        "owned_containers": [str(number) * 64 for number in (1, 2, 3)]
        if profile == "rootless"
        else [],
        "owned_endpoints": [
            "https://127.0.0.1:33333",
            "/run/hfcache/api.sock",
            "/run/hfcache-host-helper/api/helper.sock",
        ],
    }
    for index, role in enumerate(("api", "worker", "caddy", "helper"), 1):
        ready[role] = {
            "pid": 100 + index,
            "start_ticks": 1000 + index,
            "uid": 0 if role == "helper" else 983,
            "gid": 0 if role == "helper" else 983,
            "cgroup": "/system.slice/owned-" + role + ".service",
            "namespaces": {"mnt": index, "pid": index, "user": index, "net": index},
        }
        ready["owned_processes"].append({"pid": 100 + index, "start_ticks": 1000 + index})
        ready["owned_cgroups"].append(ready[role]["cgroup"])
    api = ready["api"]
    api.update(
        inner_pid=101 if profile == "native" else 1,
        inner_uid=983 if profile == "native" else 981,
        inner_gid=983 if profile == "native" else 981,
        uid_map=[[0, 0, 4294967295]]
        if profile == "native"
        else [[0, 100000, 981], [981, 983, 1], [982, 100981, 64554]],
        gid_map=[[0, 0, 4294967295]]
        if profile == "native"
        else [[0, 100000, 981], [981, 983, 1], [982, 100981, 64554]],
    )
    if profile == "rootless":
        ready["owned_processes"].append({"pid": 106, "start_ticks": 1006})
    return manifest, ready


def stopped(ready):
    return {
        "state": "stopped",
        "processes": [value | {"gone": True} for value in ready["owned_processes"]],
        "cgroups": [{"path": path, "empty": True} for path in ready["owned_cgroups"]],
        "containers": [
            {"id": cid, "status": "exited", "pid": 0, "exit_code": 0}
            for cid in ready["owned_containers"]
        ],
        "endpoints": [
            {"address": address, "refused": True} for address in ready["owned_endpoints"]
        ],
        "inputs_unchanged": True,
    }


@pytest.mark.parametrize("profile", ["native", "rootless"])
def test_closed_ready_and_exact_owned_drain_metadata(profile):
    manifest, ready = fixture(profile)
    assert module.ready_evidence(ready, manifest, profile) is ready
    assert module.stopped_evidence(stopped(ready), [ready])["state"] == "stopped"


@pytest.mark.parametrize(
    "change",
    [
        "wrong-manager",
        "wrong-inner",
        "wrong-map",
        "overlapping-map",
        "same-role-process",
        "bool-pid",
        "socket-group",
        "caddy-mount",
        "worker-mount",
        "peer-not-refused",
        "helper-ip",
        "missing-owner",
        "missing-group",
        "same-endpoint",
        "missing-helper-endpoint",
        "wrong-policy",
        "extra",
    ],
)
def test_ready_metadata_cannot_substitute_authority_or_omit_resources(change):  # noqa: PLR0912 - independent authority/resource substitutions
    manifest, ready = fixture("rootless")
    if change == "wrong-manager":
        ready["api_manager"]["main_pid"] = ready["api"]["pid"]
    elif change == "wrong-inner":
        ready["api"]["inner_pid"] = ready["api"]["pid"]
    elif change == "wrong-map":
        ready["api"]["uid_map"][1][1] += 1
    elif change == "overlapping-map":
        ready["api"]["uid_map"].append([0, 999999, 1])
    elif change == "same-role-process":
        ready["worker"] = {key: ready["api"][key] for key in ready["worker"]}
    elif change == "bool-pid":
        ready["api"]["pid"] = True
    elif change == "socket-group":
        ready["helper_parent"]["gid"] += 1
    elif change == "caddy-mount":
        ready["isolation"]["caddy_helper_mount"] = True
    elif change == "worker-mount":
        ready["isolation"]["worker_helper_mount"] = True
    elif change == "peer-not-refused":
        ready["isolation"]["same_uid_peer_refused"] = False
    elif change == "helper-ip":
        ready["isolation"]["helper_af_unix_only"] = False
    elif change == "missing-owner":
        ready["owned_processes"].pop(0)
    elif change == "missing-group":
        ready["owned_cgroups"].pop(0)
    elif change == "same-endpoint":
        ready["owned_endpoints"][-1] = ready["owned_endpoints"][0]
    elif change == "missing-helper-endpoint":
        ready["owned_endpoints"][-1] = "/run/unknown.sock"
    elif change == "wrong-policy":
        ready["policy_sha256"] = "f" * 64
    else:
        ready["extra"] = "unaccounted"
    with pytest.raises(module.FixtureError):
        module.ready_evidence(ready, manifest, "rootless")


@pytest.mark.parametrize(
    "change", ["process", "group", "container", "exit", "endpoint", "inputs", "duplicate"]
)
def test_stop_metadata_never_promotes_partial_or_unknown_cleanup(change):
    _, ready = fixture("rootless")
    proof = stopped(ready)
    if change == "process":
        proof["processes"].pop()
    elif change == "group":
        proof["cgroups"][0]["empty"] = False
    elif change == "container":
        proof["containers"].pop()
    elif change == "exit":
        proof["containers"][0]["exit_code"] = 1
    elif change == "endpoint":
        proof["endpoints"][0]["address"] = "https://127.0.0.1:1"
    elif change == "inputs":
        proof["inputs_unchanged"] = False
    else:
        proof["processes"].append(proof["processes"][0])
    with pytest.raises(module.FixtureError):
        module.stopped_evidence(proof, [ready])


def test_restart_preserves_original_api_instance_and_parent_and_drain_keeps_old_helper():
    _, before = fixture()
    after = copy.deepcopy(before)
    after["helper"]["pid"] += 100
    after["helper"]["start_ticks"] += 100
    after["owned_processes"][-1] = {
        "pid": after["helper"]["pid"],
        "start_ticks": after["helper"]["start_ticks"],
    }
    module.same_application(before, after)
    with pytest.raises(module.FixtureError):
        module.stopped_evidence(stopped(after), [before, after])
    proof = stopped(after)
    proof["processes"].append(before["owned_processes"][-1] | {"gone": True})
    module.stopped_evidence(proof, [before, after])
    after["instance_id"] = "e" * 32
    with pytest.raises(module.FixtureError):
        module.same_application(before, after)


def test_timeout_action_requires_exact_current_helper_and_positive_pause_observation():
    _, ready = fixture()
    action = {
        "state": "timeout-arm",
        "api": {key: ready["api"][key] for key in ("pid", "start_ticks")},
        "helper": {key: ready["helper"][key] for key in ("pid", "start_ticks")},
        "helper_parent": ready["helper_parent"],
        "observed": True,
        "paused": True,
    }
    module.action_evidence(action, ready, "timeout-arm")
    for key, value in (
        ("observed", False),
        ("paused", False),
        ("helper", {"pid": 1, "start_ticks": 1000}),
    ):
        with pytest.raises(module.FixtureError):
            module.action_evidence(action | {key: value}, ready, "timeout-arm")


def test_real_late_launcher_is_reaped_and_refused_without_signalling(tmp_path):
    program = tmp_path / "owned-read"
    proof = tmp_path / "closed"
    program.write_text(
        f"#!{sys.executable}\nimport pathlib,sys,time\nsys.stdin.buffer.read()\n"
        f"time.sleep(.10)\npathlib.Path({str(proof)!r}).write_text('normal')\nprint('{{}}')\n"
    )
    program.chmod(0o700)
    started = time.monotonic()
    with pytest.raises(module.FixtureError):
        asyncio.run(module.command(str(program), {"operation": "test"}, timeout=0.03))
    assert time.monotonic() - started >= 0.10
    assert proof.read_text() == "normal"


@pytest.mark.parametrize("boundary", ["spawn", "exchange"])
def test_real_cancelled_launcher_keeps_child_owned_until_actual_normal_close(
    tmp_path, monkeypatch, boundary
):
    program = tmp_path / "owned-read"
    proof = tmp_path / "closed"
    ready = tmp_path / "received"
    release = tmp_path / "release"
    program.write_text(
        f"#!{sys.executable}\nimport pathlib,sys,time\nsys.stdin.buffer.read()\n"
        f"pathlib.Path({str(ready)!r}).touch()\n"
        f"while not pathlib.Path({str(release)!r}).exists(): time.sleep(.001)\n"
        f"pathlib.Path({str(proof)!r}).write_text('normal')\nprint('{{}}')\n"
    )
    program.chmod(0o700)

    async def exercise():
        spawned = asyncio.Event()
        return_child = asyncio.Event()
        children = []
        actual_spawn = asyncio.create_subprocess_exec

        async def delayed_spawn(*args, **kwargs):
            child = await actual_spawn(*args, **kwargs)
            children.append(child)
            spawned.set()
            if boundary == "spawn":
                try:
                    await return_child.wait()
                except asyncio.CancelledError:
                    # A regression must fail without leaking the test's child.
                    assert child.stdin is not None
                    child.stdin.close()
                    await child.wait()
                    raise
            return child

        async def received_request():
            while not ready.exists():
                await asyncio.sleep(0.001)

        monkeypatch.setattr(asyncio, "create_subprocess_exec", delayed_spawn)
        task = asyncio.create_task(module.command(str(program), {}, timeout=30))
        try:
            await asyncio.wait_for(spawned.wait(), timeout=30)
            if boundary == "exchange":
                await asyncio.wait_for(received_request(), timeout=30)
            task.cancel()
            await asyncio.sleep(0)
            assert not task.done()
            return_child.set()
            release.touch()
            with pytest.raises(module.FixtureError):
                await task
            assert len(children) == 1
            assert children[0].returncode == 0
        finally:
            return_child.set()
            release.touch()
            if not task.done():
                task.cancel()
            await asyncio.gather(task, return_exceptions=True)

    asyncio.run(exercise())
    assert proof.read_text() == "normal"


def test_help_is_inert_without_manifest_or_credentials(tmp_path):
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/check-web-host-fixture.py"), "--help"],
        cwd=tmp_path,
        env={"PATH": os.defpath},
        capture_output=True,
        check=False,
        timeout=5,
    )
    assert result.returncode == 0
    assert b"--manifest" in result.stdout
    assert list(tmp_path.iterdir()) == []


def test_host_browser_metadata_adversaries_execute_without_browser_or_credentials():
    result = subprocess.run(
        ["node", "--test", str(ROOT / "web/test/host-api/driver.test.mjs")],
        cwd=ROOT,
        capture_output=True,
        check=False,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout.decode() + result.stderr.decode()


def source_fixture(tmp_path, monkeypatch):
    source = tmp_path / "one.py"
    source.write_bytes(b"# original source\n")
    source.chmod(0o644)
    files = {source.name: hashlib.sha256(source.read_bytes()).hexdigest()}
    snapshot = hashlib.sha256(
        json.dumps(files, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    value = {
        "label": "WEB-006, this commit",
        "parent_commit": "f" * 40,
        "snapshot_sha256": snapshot,
        "input_manifest": {"path": str(tmp_path / "inventory.json"), "sha256": "0" * 64},
    }
    inventory = {
        "parent_commit": "f" * 40,
        "snapshot_sha256": snapshot,
        "files": files,
        "modes": {source.name: 0o644},
    }
    path = tmp_path / "inventory.json"
    path.write_text(json.dumps(inventory))
    real = module.serving_tools()
    monkeypatch.setattr(module, "ROOT", tmp_path)
    tools = SimpleNamespace(
        COMMIT=re.compile("[0-9a-f]{40}"),
        MAXIMUM_SOURCE_FILES=4096,
        MAXIMUM_MEMBER_BYTES=8388608,
        file_record=lambda _: path,
        bounded=real.bounded,
        json_bytes=real.json_bytes,
        digest_file=real.digest_file,
    )
    return value, inventory, source, path, tools


def test_source_label_is_web006_and_measured_source_bytes_and_modes_are_bound(
    tmp_path, monkeypatch
):
    value, inventory, source, _, tools = source_fixture(tmp_path, monkeypatch)
    assert module.source_identity(value, tools) == inventory["files"]
    with pytest.raises(module.FixtureError):
        module.source_identity(value | {"label": "WEB-005, this commit"}, tools)
    source.chmod(0o600)
    with pytest.raises(module.FixtureError):
        module.source_identity(value, tools)


def test_source_inventory_drift_is_refused_against_original_bytes(tmp_path, monkeypatch):
    value, _, source, _, tools = source_fixture(tmp_path, monkeypatch)
    source.write_bytes(b"# replaced source\n")
    with pytest.raises(ValueError, match="digest differs"):
        module.source_identity(value, tools)


def browser_container_receipt() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "fixture_id": "fixture",
        "generation_id": "a" * 32,
        "profile": "native",
        "mode": "baseline",
        "report": {"path": "/retained", "sha256": "b" * 64},
        "container": {
            "image_sha256": "c" * 64,
            "container_id": "d" * 64,
            "init_identity": {"pid": 444, "start_ticks": 555},
            "exit_code": 0,
            "container_drained": True,
            "init_closed": True,
            "inputs_unchanged": True,
            "trust_mode": "private-ca",
        },
    }


@pytest.mark.parametrize("change", [None, "image", "running", "init", "exit", "inputs", "trust"])
def test_browser_receipt_requires_actual_owned_container_and_init_close(change):
    value = browser_container_receipt()
    runtime = {key: value[key] for key in ("fixture_id", "generation_id", "profile")}
    manifest = {"browser": {"trusted_image_sha256": "c" * 64}}
    field = {
        "image": ("image_sha256", "e" * 64),
        "running": ("container_drained", False),
        "init": ("init_closed", False),
        "exit": ("exit_code", -15),
        "inputs": ("inputs_unchanged", False),
        "trust": ("trust_mode", "absent"),
    }
    if change is None:
        assert module.browser_receipt(value, manifest, runtime, "baseline") is value
    else:
        key, replacement = field[change]
        value["container"][key] = replacement
        with pytest.raises(module.FixtureError):
            module.browser_receipt(value, manifest, runtime, "baseline")


@pytest.mark.parametrize("flag", ["browser_drain_unknown", "descendant_inventory_unknown"])
def test_browser_report_explicit_unknown_never_becomes_normal_cleanup(monkeypatch, flag):
    runtime = {
        "fixture_id": "fixture",
        "generation_id": "a" * 32,
        "profile": "native",
        "prefix": "",
        "instance_id": "b" * 32,
    }
    manifest = {"assets": {"manifest_sha256": "c" * 64}}
    report = {
        "schema_version": 1,
        **runtime,
        "mode": "helper-down",
        "asset_manifest_sha256": "c" * 64,
        "engines": {},
    }
    for name in ("chromium", "firefox", "webkit"):
        report["engines"][name] = {
            "browser_closed": True,
            "descendants_closed": True,
            "forced_close": False,
            "browser_exit": {"code": 0, "signal": None},
            "host_status": unavailable_host_status().model_dump(mode="json"),
            "cases": [
                {"id": identity, "passed": True, "attempts": 1}
                for identity in module.REQUIRED_CASES["helper-down"]
            ],
        }
    tools = SimpleNamespace(browser_process_evidence=lambda *_: None)
    monkeypatch.setattr(module, "serving_tools", lambda: tools)
    module.browser_evidence(report, manifest=manifest, runtime=runtime, mode="helper-down")
    report["engines"]["chromium"][flag] = True
    with pytest.raises(module.FixtureError):
        module.browser_evidence(report, manifest=manifest, runtime=runtime, mode="helper-down")


@pytest.mark.parametrize("failure", ["release-response", "browser-timeout", "arm-command"])
def test_injected_timeout_failures_always_release_owned_helper_then_stop(  # noqa: PLR0915 - one full failure-injected owned lifecycle
    tmp_path, monkeypatch, failure
):
    manifest, before = fixture()
    after = copy.deepcopy(before)
    after["helper"]["pid"] += 100
    after["helper"]["start_ticks"] += 100
    after["owned_processes"][-1] = {key: after["helper"][key] for key in ("pid", "start_ticks")}
    manifest.update(
        fixture_id="fixture",
        browser={"launcher": {"path": "browser"}, "trusted_image_sha256": "c" * 64},
    )
    manifest["profiles"]["native"].update(launcher={"path": "controller"}, prefix="")
    calls = []
    release_count = 0

    def action(ready, name):
        result = {
            "state": name,
            "api": {key: ready["api"][key] for key in ("pid", "start_ticks")},
            "helper": {key: ready["helper"][key] for key in ("pid", "start_ticks")},
            "helper_parent": ready["helper_parent"],
            "observed": True,
        }
        if name.startswith("timeout-"):
            result["paused"] = name == "timeout-arm"
        return result

    async def command(_path, request, **_kwargs):
        nonlocal release_count
        name = request["action"]
        calls.append(name)
        if name == "browser":
            if request["mode"] == "timeout" and failure == "browser-timeout":
                raise module.FixtureError
            receipt = browser_container_receipt()
            receipt.update(generation_id=request["generation_id"], mode=request["mode"])
            receipt["container"]["container_id"] = str(module.MODES.index(request["mode"]) + 1) * 64
            report = Path(request["workspace"]) / ("browser-" + request["mode"] + "-report.json")
            report.write_text("{}")
            receipt["report"]["path"] = str(report)
            return receipt
        if name == "start":
            evidence = before
        elif name == "helper-start":
            evidence = after
        elif name == "stop":
            evidence = stopped(after)
            evidence["processes"].append(before["owned_processes"][-1] | {"gone": True})
        elif name == "timeout-arm" and failure == "arm-command":
            raise module.FixtureError
        else:
            evidence = action(before if name == "helper-stop" else after, name)
            if name == "timeout-release":
                release_count += 1
                if failure == "release-response" and release_count == 1:
                    evidence["observed"] = False
        return {
            key: request[key]
            for key in ("schema_version", "fixture_id", "generation_id", "profile", "action")
        } | {"evidence": evidence}

    monkeypatch.setattr(module, "command", command)
    monkeypatch.setattr(module, "browser_evidence", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(
        module,
        "serving_tools",
        lambda: SimpleNamespace(
            file_record=lambda value, **_: Path(value["path"]),
            bounded=lambda path, *_: path.read_bytes(),
            json_bytes=json.loads,
            MAXIMUM_REPORT_BYTES=4194304,
        ),
    )
    with pytest.raises(module.FixtureError):
        asyncio.run(module.run_profile(manifest, tmp_path, "native"))
    assert calls[-2:] == ["timeout-release", "stop"]
    assert release_count == (2 if failure == "release-response" else 1)
    generation = next(tmp_path.iterdir())
    result = json.loads((generation / "RESULT.json").read_bytes())
    assert result["stopped"]["state"] == "stopped"
    assert not (tmp_path / "SUMMARY.json").exists()
    if failure == "release-response":
        assert (generation / "timeout-release-response.json").is_file()
        assert (generation / "timeout-release-response-attempt2.json").is_file()
