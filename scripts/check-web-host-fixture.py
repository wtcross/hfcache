#!/usr/bin/env python3
"""Check WEB006 through an owned fixed installation, real Caddy and built UI.

Help is inert. Execution requires protected provisioning in the explicitly owned
disposable guest. This runner never selects a unit, executable, archive or peer.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import importlib.util
import itertools
import json
import os
import re
import secrets
import stat
import sys
import time
import uuid
from pathlib import Path
from typing import Any, NoReturn

ROOT = Path(__file__).absolute().parents[1]
PROFILES = {"native", "rootless"}
MODES = ("baseline", "helper-down", "restarted", "timeout")
ACTIONS = {
    "start",
    "inspect",
    "helper-stop",
    "helper-start",
    "timeout-arm",
    "timeout-release",
    "stop",
}
ROLES = {"api", "worker", "caddy", "helper"}
CATEGORIES = {"archive", "hub", "control", "schedule", "configuration", "observer"}
HEX32 = re.compile(r"[0-9a-f]{32}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
MAX_JSON = 2 * 1024 * 1024
MAX_RESOURCES = 256
MAX_CGROUPS = 64
MAX_CONTAINERS = 16
MAX_PATH_BYTES = 1024
MAX_MAP_ROWS = 8
MAP_FIELDS = 3
MIN_ROLE_PROCESSES = 4
PARENT_MODE = 0o750
CONTAINER_ACCOUNT = 981
ROOTLESS_CONTAINERS = 3
MIN_ENDPOINTS = 3
MAX_ENDPOINTS = 8
MIN_TIMEOUT_SECONDS = 21.0
MAX_TIMEOUT_SECONDS = 28.0
REQUIRED_CASES = {
    "baseline": {
        "host-status-observed",
        "host-denial-ui-reasons",
        "basic-hub-denied",
        "basic-archive-denied",
        "basic-control-denied",
        "forged-admin-header-denied",
        "old-writer-no-host-admin",
    },
    "helper-down": {"host-unavailable-visible", "basic-unavailable-denied"},
    "restarted": {"host-restart-same-parent"},
    "timeout": {"actual-timeout-visible"},
}


class FixtureError(ValueError):
    """Fixed safe diagnostic; raw dependency errors are never persisted."""


def need(value: object) -> None:
    if not value:
        refuse()


def refuse() -> NoReturn:
    message = "owned host fixture prerequisite or evidence refused"
    raise FixtureError(message)


def exact(value: object, keys: set[str]) -> dict[str, Any]:
    need(type(value) is dict and set(value) == keys)
    return value  # type: ignore[return-value]


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def serving_tools() -> Any:
    """Reuse unchanged WEB005 provenance/process validators, never its runner."""
    spec = importlib.util.spec_from_file_location(
        "_host_fixture_serving", ROOT / "scripts/check-web-functional.py"
    )
    if spec is None or spec.loader is None:
        refuse()
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def persist(path: Path, value: object) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(canonical(value))
        stream.flush()
        os.fsync(stream.fileno())


def pair(value: object) -> tuple[int, int]:
    item = exact(value, {"pid", "start_ticks"})
    need(all(type(x) is int for x in item.values()) and item["pid"] > 1 and item["start_ticks"] > 0)
    return item["pid"], item["start_ticks"]


def group(value: object) -> str:
    need(
        type(value) is str
        and value.startswith("/")
        and value != "/"
        and ".." not in value.split("/")
        and len(value) <= MAX_PATH_BYTES
    )
    return value  # type: ignore[return-value]


def resource_lists(value: dict[str, Any]) -> tuple[set[tuple[int, int]], set[str], set[str]]:
    processes, groups, containers = (
        value["owned_processes"],
        value["owned_cgroups"],
        value["owned_containers"],
    )
    need(type(processes) is list and MIN_ROLE_PROCESSES <= len(processes) <= MAX_RESOURCES)
    identities = {pair(item) for item in processes}
    need(len(identities) == len(processes))
    need(type(groups) is list and 1 <= len(groups) <= MAX_CGROUPS)
    cgroups = {group(item) for item in groups}
    need(len(cgroups) == len(groups))
    need(type(containers) is list and len(containers) <= MAX_CONTAINERS)
    need(all(type(item) is str and HEX64.fullmatch(item) for item in containers))
    need(len(set(containers)) == len(containers))
    return identities, cgroups, set(containers)


def source_identity(value: object, tools: Any) -> dict[str, str]:
    item = exact(value, {"parent_commit", "snapshot_sha256", "label", "input_manifest"})
    need(
        item["label"] == "WEB-006, this commit"
        and type(item["parent_commit"]) is str
        and tools.COMMIT.fullmatch(item["parent_commit"])
    )
    need(type(item["snapshot_sha256"]) is str and HEX64.fullmatch(item["snapshot_sha256"]))
    inventory = tools.json_bytes(tools.bounded(tools.file_record(item["input_manifest"])))
    need(
        inventory["parent_commit"] == item["parent_commit"]
        and inventory["snapshot_sha256"] == item["snapshot_sha256"]
    )
    files, modes = inventory["files"], inventory["modes"]
    need(type(files) is dict and 0 < len(files) <= tools.MAXIMUM_SOURCE_FILES)
    need(type(modes) is dict and set(modes) == set(files))
    for name, digest in files.items():
        need(
            type(name) is str
            and not name.startswith("/")
            and all(part not in {"", ".", ".."} for part in name.split("/"))
        )
        path = ROOT
        for part in name.split("/"):
            path /= part
            facts = path.lstat()
            need(
                stat.S_ISREG(facts.st_mode) if path == ROOT / name else stat.S_ISDIR(facts.st_mode)
            )
        need(type(modes[name]) is int and stat.S_IMODE(facts.st_mode) == modes[name])
        tools.digest_file(path, digest, tools.MAXIMUM_MEMBER_BYTES)
    observed = hashlib.sha256(
        json.dumps(files, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    need(observed == item["snapshot_sha256"])
    return files


def guest_identity(value: object) -> bool:
    """Accept only named disposable WEB fixtures; the protected marker binds the boot."""
    return type(value) is str and (
        value == "web-004-83a4380d0c82465fa225c00bba53359c"
        or re.fullmatch(r"web-006-source[1-9][0-9]*-[0-9a-f]{32}", value) is not None
    )


def parent(value: object, gid: int) -> dict[str, int]:
    item = exact(value, {"device", "inode", "uid", "gid", "mode"})
    need(all(type(x) is int for x in item.values()))
    need(
        item["device"] > 0
        and item["inode"] > 0
        and item["uid"] == 0
        and item["gid"] == gid
        and item["mode"] == PARENT_MODE
    )
    return item


def process(value: object, *, api: bool = False) -> dict[str, Any]:
    keys = {"pid", "start_ticks", "uid", "gid", "cgroup", "namespaces"}
    if api:
        keys |= {"inner_pid", "inner_uid", "inner_gid", "uid_map", "gid_map"}
    item = exact(value, keys)
    pair({key: item[key] for key in ("pid", "start_ticks")})
    need(
        type(item["uid"]) is int
        and item["uid"] >= 0
        and type(item["gid"]) is int
        and item["gid"] >= 0
    )
    group(item["cgroup"])
    namespaces = exact(item["namespaces"], {"mnt", "pid", "user", "net"})
    need(all(type(x) is int and x > 0 for x in namespaces.values()))
    if api:
        need(
            all(
                type(item[key]) is int and item[key] > 0
                for key in ("inner_pid", "inner_uid", "inner_gid")
            )
        )
        for key, inside, outside in (
            ("uid_map", item["inner_uid"], item["uid"]),
            ("gid_map", item["inner_gid"], item["gid"]),
        ):
            rows = item[key]
            need(type(rows) is list and 1 <= len(rows) <= MAX_MAP_ROWS)
            need(
                all(
                    type(row) is list
                    and len(row) == MAP_FIELDS
                    and all(type(x) is int and x >= 0 for x in row)
                    and row[2] > 0
                    and row[0] + row[2] <= 2**32
                    and row[1] + row[2] <= 2**32
                    for row in rows
                )
            )
            for offset in (0, 1):
                ordered = sorted(rows, key=lambda row: row[offset])
                need(
                    all(
                        first[offset] + first[2] <= second[offset]
                        for first, second in itertools.pairwise(ordered)
                    )
                )
            matches = [
                host + inside - inner
                for inner, host, count in rows
                if inner <= inside < inner + count
            ]
            need(matches == [outside])
    return item


def ready_evidence(value: object, manifest: dict[str, Any], profile: str) -> dict[str, Any]:
    item = exact(
        value,
        {
            "state",
            "deployment_sha256",
            "policy_sha256",
            "asset_manifest_sha256",
            "instance_id",
            *ROLES,
            "api_manager",
            "helper_parent",
            "isolation",
            "owned_processes",
            "owned_cgroups",
            "owned_containers",
            "owned_endpoints",
        },
    )
    selected = manifest["profiles"][profile]
    need(
        item["state"] == "ready"
        and item["deployment_sha256"] == selected["deployment"]["sha256"]
        and item["policy_sha256"] == selected["policy"]["sha256"]
        and item["asset_manifest_sha256"] == manifest["assets"]["manifest_sha256"]
    )
    need(type(item["instance_id"]) is str and HEX32.fullmatch(item["instance_id"]))
    for role in ROLES:
        process(item[role], api=role == "api")
    need(len({(item[role]["pid"], item[role]["start_ticks"]) for role in ROLES}) == len(ROLES))
    api, helper = item["api"], item["helper"]
    need(api["uid"] > 0 and api["gid"] > 0 and helper["uid"] == helper["gid"] == 0)
    manager = exact(
        item["api_manager"], {"scope", "name", "main_pid", "main_start_ticks", "invocation_id"}
    )
    pair({"pid": manager["main_pid"], "start_ticks": manager["main_start_ticks"]})
    need(
        manager["name"] == "hfcache-api.service"
        and type(manager["invocation_id"]) is str
        and HEX32.fullmatch(manager["invocation_id"])
    )
    need(manager["scope"] == ("system" if profile == "native" else "user"))
    if profile == "native":
        need((manager["main_pid"], manager["main_start_ticks"]) == (api["pid"], api["start_ticks"]))
        need(
            (api["inner_pid"], api["inner_uid"], api["inner_gid"])
            == (api["pid"], api["uid"], api["gid"])
        )
    else:
        need(
            manager["main_pid"] != api["pid"]
            and api["inner_pid"] == 1
            and api["inner_uid"] == api["inner_gid"] == CONTAINER_ACCOUNT
        )
    parent(item["helper_parent"], api["gid"])
    isolation = exact(
        item["isolation"],
        {
            "caddy_helper_mount",
            "worker_helper_mount",
            "same_uid_peer_refused",
            "other_tgid_peer_refused",
            "helper_af_unix_only",
            "helper_archive_masked",
            "helper_hub_secrets_masked",
        },
    )
    need(all(type(x) is bool for x in isolation.values()))
    need(
        not isolation["caddy_helper_mount"]
        and not isolation["worker_helper_mount"]
        and all(isolation[key] for key in isolation if not key.endswith("_mount"))
    )
    identities, cgroups, containers = resource_lists(item)
    need(
        all(
            (item[role]["pid"], item[role]["start_ticks"]) in identities
            and item[role]["cgroup"] in cgroups
            for role in ROLES
        )
    )
    need((manager["main_pid"], manager["main_start_ticks"]) in identities)
    need(profile != "rootless" or len(containers) >= ROOTLESS_CONTAINERS)
    endpoints = item["owned_endpoints"]
    need(type(endpoints) is list and MIN_ENDPOINTS <= len(endpoints) <= MAX_ENDPOINTS)
    need(all(type(address) is str and 0 < len(address) <= MAX_PATH_BYTES for address in endpoints))
    need(len(set(endpoints)) == len(endpoints))
    need(
        "/run/hfcache-host-helper/api/helper.sock" in endpoints and selected["origin"] in endpoints
    )
    return item


def same_application(before: dict[str, Any], after: dict[str, Any]) -> None:
    for key in (
        "instance_id",
        "deployment_sha256",
        "policy_sha256",
        "asset_manifest_sha256",
        "api",
        "worker",
        "caddy",
        "api_manager",
        "helper_parent",
        "isolation",
        "owned_endpoints",
    ):
        need(before[key] == after[key])


def action_evidence(value: object, ready: dict[str, Any], action: str) -> dict[str, Any]:
    keys = {"state", "api", "helper", "helper_parent", "observed"}
    if action.startswith("timeout-"):
        keys.add("paused")
    item = exact(value, keys)
    need(item["state"] == action and item["observed"] is True)
    need(pair(item["api"]) == (ready["api"]["pid"], ready["api"]["start_ticks"]))
    need(pair(item["helper"]) == (ready["helper"]["pid"], ready["helper"]["start_ticks"]))
    need(item["helper_parent"] == ready["helper_parent"])
    parent(item["helper_parent"], ready["api"]["gid"])
    if action.startswith("timeout-"):
        need(item["paused"] is (action == "timeout-arm"))
    return item


def stopped_evidence(value: object, retained: list[dict[str, Any]]) -> dict[str, Any]:
    item = exact(
        value, {"state", "processes", "cgroups", "containers", "endpoints", "inputs_unchanged"}
    )
    need(item["state"] == "stopped" and item["inputs_unchanged"] is True)
    need(type(item["processes"]) is list and len(item["processes"]) <= MAX_RESOURCES)
    closed = set()
    for row in item["processes"]:
        exact(row, {"pid", "start_ticks", "gone"})
        need(row["gone"] is True)
        closed.add(pair({key: row[key] for key in ("pid", "start_ticks")}))
    need(len(closed) == len(item["processes"]))
    need(type(item["cgroups"]) is list and len(item["cgroups"]) <= MAX_CGROUPS)
    groups = set()
    for row in item["cgroups"]:
        exact(row, {"path", "empty"})
        need(row["empty"] is True)
        groups.add(group(row["path"]))
    need(len(groups) == len(item["cgroups"]))
    need(type(item["containers"]) is list and len(item["containers"]) <= MAX_CONTAINERS)
    containers = set()
    for row in item["containers"]:
        exact(row, {"id", "status", "pid", "exit_code"})
        need(type(row["id"]) is str and HEX64.fullmatch(row["id"]))
        need(
            row["status"] == "exited"
            and type(row["pid"]) is int
            and row["pid"] == 0
            and type(row["exit_code"]) is int
            and row["exit_code"] == 0
        )
        containers.add(row["id"])
    need(len(containers) == len(item["containers"]))
    need(
        type(item["endpoints"]) is list and MIN_ENDPOINTS <= len(item["endpoints"]) <= MAX_ENDPOINTS
    )
    for endpoint in item["endpoints"]:
        exact(endpoint, {"address", "refused"})
        need(
            type(endpoint["address"]) is str
            and len(endpoint["address"]) <= MAX_PATH_BYTES
            and endpoint["refused"] is True
        )
    endpoints = {row["address"] for row in item["endpoints"]}
    need(len(endpoints) == len(item["endpoints"]))
    for ready in retained:
        owned, paths, cids = resource_lists(ready)
        need(owned <= closed and paths <= groups and cids <= containers)
        need(set(ready["owned_endpoints"]) <= endpoints)
    return item


def validate_manifest(filename: str, *, tools: Any | None = None) -> dict[str, Any]:
    tools = serving_tools() if tools is None else tools
    path = tools.path_input(filename)
    tools.local_backing(ROOT)
    manifest = tools.json_bytes(tools.bounded(path))
    exact(
        manifest,
        {
            "schema_version",
            "kind",
            "fixture_id",
            "marker",
            "guest",
            "source",
            "installed",
            "assets",
            "browser",
            "profiles",
        },
    )
    need(
        type(manifest["schema_version"]) is int
        and manifest["schema_version"] == 1
        and manifest["kind"] == "hfcache_web_host_fixture"
    )
    need(
        type(manifest["fixture_id"]) is str
        and str(uuid.UUID(manifest["fixture_id"])) == manifest["fixture_id"]
    )
    guest = exact(manifest["guest"], {"identity", "boot_id"})
    need(guest_identity(guest["identity"]))
    need(type(guest["boot_id"]) is str and str(uuid.UUID(guest["boot_id"])) == guest["boot_id"])
    marker = tools.file_record(manifest["marker"])
    need(marker.stat().st_uid == 0)
    need(
        tools.json_bytes(tools.bounded(marker))
        == {
            "schema_version": 1,
            "fixture_id": manifest["fixture_id"],
            "repository_root": str(ROOT),
            "guest": guest,
            "scope": "owned isolated WEB006 only",
            "production": False,
            "external_nas": False,
        }
    )
    files = source_identity(manifest["source"], tools)
    tools.installed_identity(manifest["installed"], files)
    tools.asset_identity(manifest["assets"])
    browser = exact(
        manifest["browser"],
        {
            "launcher",
            "ca",
            "playwright_module",
            "node_binary",
            "toolchain_inventory",
            "seccomp",
            "trusted_image_sha256",
            "node_version",
            "playwright_version",
        },
    )
    for key in (
        "launcher",
        "ca",
        "playwright_module",
        "node_binary",
        "toolchain_inventory",
        "seccomp",
    ):
        tools.file_record(browser[key], maximum=tools.MAXIMUM_TOOL_BYTES)
    need(browser["node_version"] == "24.18.1" and browser["playwright_version"] == "1.64.1")
    need(
        type(browser["trusted_image_sha256"]) is str
        and HEX64.fullmatch(browser["trusted_image_sha256"])
    )
    profiles = exact(manifest["profiles"], PROFILES)
    for profile, binding in profiles.items():
        exact(binding, {"launcher", "origin", "prefix", "deployment", "policy"})
        tools.origin(binding["origin"])
        need(binding["prefix"] in {"", "/management"})
        tools.file_record(binding["launcher"])
        deployment = tools.json_bytes(tools.bounded(tools.file_record(binding["deployment"])))
        need(deployment["profile"] == profile)
        policy = tools.json_bytes(tools.bounded(tools.file_record(binding["policy"])))
        exact(policy, {"schema_version", "deployment_sha256", "permissions"})
        need(
            type(policy["schema_version"]) is int
            and policy["schema_version"] == 1
            and policy["deployment_sha256"] == binding["deployment"]["sha256"]
        )
        permissions = exact(policy["permissions"], CATEGORIES)
        need(
            all(
                type(value) is bool and value == (name == "configuration")
                for name, value in permissions.items()
            )
        )
    return manifest


async def command(path: str, body: dict[str, Any], *, timeout: float) -> dict[str, Any]:
    """No signals: late owned launchers stay owned until their actual reap."""
    child = await asyncio.create_subprocess_exec(
        path,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
        env={"PATH": os.defpath, "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "PYTHONNOUSERSITE": "1"},
    )

    async def exchange() -> bytes:
        sink, source = child.stdin, child.stdout
        if sink is None or source is None:
            await child.wait()
            refuse()

        async def read_output(source: asyncio.StreamReader) -> bytes:
            output = bytearray()
            overflow = False
            while chunk := await source.read(65536):
                overflow |= len(output) + len(chunk) > MAX_JSON
                if not overflow:
                    output.extend(chunk)
            need(not overflow)
            return bytes(output)

        reader = asyncio.create_task(read_output(source))
        try:
            sink.write(canonical(body))
            await sink.drain()
            sink.close()
            return await reader
        finally:
            sink.close()
            try:
                await reader
            finally:
                await child.wait()
                need(child.returncode == 0)

    task = asyncio.create_task(exchange())
    interrupted = False
    late = False
    deadline = time.monotonic() + timeout
    while not task.done():
        try:
            left = max(0.001, deadline - time.monotonic())
            done, _ = await asyncio.wait({task}, timeout=left if not late else 1)
            late |= not done and time.monotonic() >= deadline
        except asyncio.CancelledError:
            interrupted = True
    output = task.result()
    need(not late and not interrupted and time.monotonic() < deadline)
    return serving_tools().json_bytes(output)


def response(value: object, request: dict[str, Any]) -> dict[str, Any]:
    item = exact(
        value, {"schema_version", "fixture_id", "generation_id", "profile", "action", "evidence"}
    )
    need(
        all(
            item[key] == request[key] and type(item[key]) is type(request[key])
            for key in item
            if key != "evidence"
        )
    )
    need(type(item["evidence"]) is dict)
    return item["evidence"]


def browser_evidence(
    value: object, *, manifest: dict[str, Any], runtime: dict[str, Any], mode: str
) -> dict[str, Any]:
    from hfcache.host_models import HostStatus

    report = exact(
        value,
        {
            "schema_version",
            "fixture_id",
            "generation_id",
            "profile",
            "prefix",
            "mode",
            "asset_manifest_sha256",
            "instance_id",
            "engines",
        },
    )
    need(type(report["schema_version"]) is int and report["schema_version"] == 1)
    for key in ("fixture_id", "generation_id", "profile", "prefix", "instance_id"):
        need(report[key] == runtime[key])
    need(
        report["asset_manifest_sha256"] == manifest["assets"]["manifest_sha256"]
        and report["mode"] == mode
    )
    engines = exact(report["engines"], {"chromium", "firefox", "webkit"})
    tools = serving_tools()
    for name, item in engines.items():
        tools.browser_process_evidence(item, name)
        need(
            item["browser_closed"] is True
            and item["descendants_closed"] is True
            and item.get("forced_close") is False
            and item.get("infrastructure_failed") is not True
            and item.get("descendant_inventory_unknown") is not True
            and item.get("browser_drain_unknown") is not True
        )
        need(item["browser_exit"] == {"code": 0, "signal": None})
        status = HostStatus.model_validate(item["host_status"])
        if mode in {"baseline", "restarted"}:
            need(status.state == "supported" and status.profile == runtime["profile"])
            if status.binding is None or status.facts is None:
                refuse()
            need(
                status.binding.deployment_sha256
                == manifest["profiles"][runtime["profile"]]["deployment"]["sha256"]
                and status.binding.policy_sha256
                == manifest["profiles"][runtime["profile"]]["policy"]["sha256"]
                and status.facts.guard in {"absent", "inactive"}
            )
            need(
                all(
                    getattr(status.permissions, key) == (key == "configuration")
                    for key in CATEGORIES
                )
            )
        else:
            need(status.state == "unavailable")
            need(
                status.reason == "helper-timeout"
                if mode == "timeout"
                else status.reason in {"helper-refused", "helper-unavailable"}
            )
        cases = item["cases"]
        need(
            type(cases) is list
            and {row["id"] for row in cases} == REQUIRED_CASES[mode]
            and len(cases) == len(REQUIRED_CASES[mode])
        )
        for row in cases:
            need(row["passed"] is True and type(row["attempts"]) is int and row["attempts"] == 1)
        if mode == "timeout":
            need(
                type(item.get("timeout_elapsed_seconds")) in {int, float}
                and MIN_TIMEOUT_SECONDS <= item["timeout_elapsed_seconds"] < MAX_TIMEOUT_SECONDS
            )
    return report


def browser_receipt(
    value: object, manifest: dict[str, Any], runtime: dict[str, Any], mode: str
) -> dict[str, Any]:
    item = exact(
        value,
        {"schema_version", "fixture_id", "generation_id", "profile", "mode", "report", "container"},
    )
    need(type(item["schema_version"]) is int and item["schema_version"] == 1)
    need(
        all(item[key] == runtime[key] for key in ("fixture_id", "generation_id", "profile"))
        and item["mode"] == mode
    )
    container = exact(
        item["container"],
        {
            "image_sha256",
            "container_id",
            "init_identity",
            "exit_code",
            "container_drained",
            "init_closed",
            "inputs_unchanged",
            "trust_mode",
        },
    )
    need(container["image_sha256"] == manifest["browser"]["trusted_image_sha256"])
    need(type(container["container_id"]) is str and HEX64.fullmatch(container["container_id"]))
    pair(container["init_identity"])
    need(type(container["exit_code"]) is int and container["exit_code"] == 0)
    need(
        all(
            container[key] is True
            for key in ("container_drained", "init_closed", "inputs_unchanged")
        )
    )
    need(container["trust_mode"] == "private-ca")
    return item


async def run_profile(manifest: dict[str, Any], workspace: Path, profile: str) -> dict[str, Any]:  # noqa: PLR0915 - one visible owned lifecycle and unconditional stop boundary
    generation = uuid.uuid4().hex
    target = workspace / (profile + "-" + generation)
    target.mkdir(mode=0o700)
    request = {
        "schema_version": 1,
        "fixture_id": manifest["fixture_id"],
        "generation_id": generation,
        "profile": profile,
        "action": "start",
        "workspace": str(target),
    }
    auth = {
        "schema_version": 1,
        "username": "web006-administrator",
        "password": secrets.token_urlsafe(48),
        "tokens": {
            name: secrets.token_urlsafe(48) for name in ("hub", "mcp_reader", "reader", "writer")
        },
    }
    result: dict[str, Any] = {
        "schema_version": 1,
        "fixture_id": manifest["fixture_id"],
        "generation_id": generation,
        "profile": profile,
        "cleanup_unknown": True,
        "modes": {},
    }
    retained = []
    attempts: dict[str, int] = {}
    browser_containers = set()
    timeout_armed = False
    timeout_released = False
    launcher = manifest["profiles"][profile]["launcher"]["path"]

    async def control(action: str) -> dict[str, Any]:
        attempts[action] = attempts.get(action, 0) + 1
        request["action"] = action
        sent = request | ({"auth": auth} if action == "start" else {})
        raw = await command(launcher, sent, timeout=180)
        suffix = "" if attempts[action] == 1 else "-attempt" + str(attempts[action])
        persist(target / (action + "-response" + suffix + ".json"), raw)
        return response(raw, request)

    try:
        ready = ready_evidence(await control("start"), manifest, profile)
        current = ready
        retained.append(ready)
        result["ready"] = ready
        runtime = {
            "schema_version": 1,
            "fixture_id": manifest["fixture_id"],
            "generation_id": generation,
            "profile": profile,
            "prefix": manifest["profiles"][profile]["prefix"],
            "origin": manifest["profiles"][profile]["origin"],
            "instance_id": ready["instance_id"],
            "asset_manifest_sha256": manifest["assets"]["manifest_sha256"],
        }
        persist(target / "runtime.json", runtime)
        for mode in MODES:
            if mode == "helper-down":
                result["helper-stop"] = action_evidence(
                    await control("helper-stop"), current, "helper-stop"
                )
            elif mode == "restarted":
                restarted = ready_evidence(await control("helper-start"), manifest, profile)
                same_application(ready, restarted)
                need(
                    (ready["helper"]["pid"], ready["helper"]["start_ticks"])
                    != (restarted["helper"]["pid"], restarted["helper"]["start_ticks"])
                )
                retained.append(restarted)
                current = restarted
                result["helper-start"] = restarted
            elif mode == "timeout":
                timeout_armed = True
                result["timeout-arm"] = action_evidence(
                    await control("timeout-arm"), current, "timeout-arm"
                )
            browser_request = request | {"action": "browser", "mode": mode, "auth": auth}
            receipt = await command(
                manifest["browser"]["launcher"]["path"], browser_request, timeout=240
            )
            browser_receipt(receipt, manifest, runtime, mode)
            cid = receipt["container"]["container_id"]
            need(cid not in browser_containers)
            browser_containers.add(cid)
            persist(target / ("browser-" + mode + "-receipt.json"), receipt)
            tools = serving_tools()
            report_path = tools.file_record(receipt["report"], maximum=tools.MAXIMUM_REPORT_BYTES)
            need(report_path == target / ("browser-" + mode + "-report.json"))
            result["modes"][mode] = browser_evidence(
                tools.json_bytes(tools.bounded(report_path, tools.MAXIMUM_REPORT_BYTES)),
                manifest=manifest,
                runtime=runtime,
                mode=mode,
            )
            if mode == "timeout":
                result["timeout-release"] = action_evidence(
                    await control("timeout-release"), current, "timeout-release"
                )
                timeout_released = True
        inspected = ready_evidence(await control("inspect"), manifest, profile)
        same_application(ready, inspected)
        retained.append(inspected)
        result["inspected"] = inspected
    finally:
        try:
            try:
                if timeout_armed and not timeout_released:
                    result["timeout-release"] = action_evidence(
                        await control("timeout-release"), current, "timeout-release"
                    )
            finally:
                stopped = await control("stop")
                result["stopped"] = stopped_evidence(stopped, retained)
                need(bool(retained))
                result["cleanup_unknown"] = False
        finally:
            persist(target / "RESULT.json", result)
    return result


async def run(manifest: dict[str, Any], workspace: Path, profile: str) -> dict[str, Any]:
    results = []
    for selected in sorted(PROFILES) if profile == "all" else (profile,):
        results.append(await run_profile(manifest, workspace, selected))  # noqa: PERF401 - actual fixed installation must stop before profile switch
    summary = {
        "schema_version": 1,
        "scope": "owned WEB006 fixed installation only; no production or held-NFS-guard claim",
        "fixture_id": manifest["fixture_id"],
        "profile": profile,
        "source": manifest["source"],
        "results": results,
        "case_ids": ["AUTH-08", "HOST-01", "HOST-02", "HOST-03"],
        "required_case_skips": 0,
        "required_case_retries": 0,
    }
    persist(workspace / "SUMMARY.json", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--profile", choices=("native", "rootless", "all"), required=True)
    parser.add_argument(
        "--workspace",
        required=True,
        help="fresh direct private .scratch/web-host-fixture-* descendant",
    )
    args = parser.parse_args()
    workspace = None
    try:
        manifest = validate_manifest(args.manifest)
        import hfcache

        need(Path(hfcache.__file__).parent == Path(manifest["installed"]["package_root"]))
        need(
            Path("/proc/sys/kernel/random/boot_id").read_text().strip()
            == manifest["guest"]["boot_id"]
        )
        base = ROOT / ".scratch"
        facts = base.lstat()
        need(
            stat.S_ISDIR(facts.st_mode)
            and facts.st_uid == os.getuid()
            and not facts.st_mode & 0o077
        )
        candidate = Path(args.workspace)
        need(
            candidate.is_absolute()
            and candidate.parent == base
            and candidate.name.startswith("web-host-fixture-")
            and not candidate.exists()
        )
        candidate.mkdir(mode=0o700)
        workspace = candidate
        asyncio.run(run(manifest, workspace, args.profile))
        validate_manifest(args.manifest)
    except Exception:  # noqa: BLE001 - no raw credential-bearing exception is public evidence
        if workspace is not None:
            persist(
                workspace / "BLOCKED.json",
                {
                    "schema_version": 1,
                    "reason": "required fixed installation, execution, evidence or drain refused",
                },
            )
        print("Owned WEB006 fixture refused; preserve its original evidence.", file=sys.stderr)
        return 1
    print("Owned WEB006 cases passed; inspect original SUMMARY.json and drain evidence.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
