#!/usr/bin/env python3
"""Check native browser authentication inside an explicitly provisioned disposable guest.

The manifest binds a private fixture, installed wheel, CA and fixed browser launcher.
Argument parsing and help perform no runtime discovery or service access.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import re
import secrets
import socket
import stat
import subprocess
import sys
import tempfile
import threading
import uuid
import zipfile
from contextlib import AsyncExitStack, suppress
from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING, Any, NoReturn
from urllib.parse import urlsplit

if TYPE_CHECKING:
    from starlette.types import ASGIApp, Message, Receive, Scope, Send

ROOT = Path(__file__).absolute().parents[1]
MAXIMUM_JSON = 1024 * 1024
MAXIMUM_MEMBERS = 4096
MAXIMUM_OBSERVATIONS = 4096
MAXIMUM_BROWSER_REQUESTS = 256
CASE_COUNT = 8
PROFILE_COUNT = 3
ENGINES = {"chromium", "firefox", "webkit"}
CASE_IDS = {
    "native-challenge-version",
    "same-origin-capabilities",
    "same-origin-json-post",
    "foreign-text",
    "foreign-multipart",
    "foreign-form",
    "foreign-preflight",
    "untrusted-ca-refused",
}
ARCHIVE_ID = "3f2a1c88-7b40-4a2e-9c1d-0e5b6a7f8d90"
IMAGE = "bdfda2a8fdf48707c5e50a49bd3e06d8d0c759153dc8ee057d8a81c3450bb3e9"
SHA256 = re.compile(r"[a-f0-9]{64}")
LOCAL_FILESYSTEMS = frozenset({"btrfs", "ext2", "ext3", "ext4", "xfs", "zfs", "tmpfs", "overlay"})


class FixtureRefusalError(ValueError):
    """Only constant nonsecret diagnostics cross the public fixture boundary."""


def reject(message: str) -> NoReturn:
    raise FixtureRefusalError(message)


def prove_local_path(path: Path, mountinfo: str | None = None) -> None:
    """Read mount metadata without traversing any storage/archive destination."""
    if mountinfo is None:
        with Path("/proc/self/mountinfo").open("rb") as stream:
            raw = stream.read(4 * 1024 * 1024 + 1)
        if len(raw) > 4 * 1024 * 1024:
            reject("local mount metadata exceeds its finite byte budget")
        mountinfo = raw.decode("utf-8", errors="strict")
    matches = []
    for line in mountinfo.splitlines():
        before, separator, after = line.partition(" - ")
        fields, tail = before.split(), after.split()
        if not separator or len(fields) < 6 or len(tail) < 3:  # noqa: PLR2004 - kernel grammar
            reject("local mount metadata is malformed")
        point = Path(re.sub(r"\\([0-7]{3})", lambda item: chr(int(item[1], 8)), fields[4]))
        if point == path or point in path.parents:
            matches.append((len(point.parts), tail[0]))
    depth = max((level for level, _ in matches), default=-1)
    if not matches or any(
        kind not in LOCAL_FILESYSTEMS for level, kind in matches if level == depth
    ):
        reject("fixture inputs are not proven to use an approved local filesystem")


def digest(path: Path, maximum: int = 64 * 1024 * 1024) -> str:
    size = path.stat().st_size
    if size > maximum:
        reject("fixture input exceeds its finite byte budget")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            reject("fixture JSON has duplicate fields")
        result[key] = value
    return result


def json_file(path: Path) -> dict[str, Any]:
    if path.stat().st_size > MAXIMUM_JSON:
        reject("fixture JSON exceeds its finite byte budget")
    payload = json.loads(path.read_bytes(), object_pairs_hook=unique_object)
    if not isinstance(payload, dict):
        reject("fixture JSON must be an object")
    return payload


def owned_path(
    value: Any, *, root: Path = ROOT, directory: bool = False, private: bool = False
) -> Path:
    """Validate lexically before lstat; never follow an unowned/symlinked ancestor."""
    if not isinstance(value, str) or any(part in {".", ".."} for part in value.split("/")):
        reject("fixture paths must be absolute without traversal")
    path = Path(value)
    base = root / ".scratch"
    if not path.is_absolute() or not path.is_relative_to(base) or path == base:
        reject("fixture inputs must be repository .scratch descendants")
    current = root
    for part in ("", *path.relative_to(root).parts):
        if part:
            current /= part
        facts = current.lstat()
        leaf = current == path
        if facts.st_uid not in {0, os.getuid()} or facts.st_mode & 0o022:
            reject("fixture inputs and ancestors must be protected and root/current-user owned")
        if not (
            stat.S_ISREG(facts.st_mode) if leaf and not directory else stat.S_ISDIR(facts.st_mode)
        ):
            reject("fixture input has a symlink or unsupported file kind")
        if current == base and (facts.st_uid != os.getuid() or facts.st_mode & 0o077):
            reject("fixture .scratch must be a private current-user directory")
        if leaf and not directory and facts.st_nlink != 1:
            reject("fixture input must have exactly one hard link")
        if (
            leaf
            and private
            and (facts.st_uid != os.getuid() or stat.S_IMODE(facts.st_mode) not in {0o400, 0o600})
        ):
            reject("fixture private key must be current-user owned with mode0400 or0600")
    return path


def checked_file(value: Any, expected: Any, *, root: Path, private: bool = False) -> Path:
    path = owned_path(value, root=root, private=private)
    if not isinstance(expected, str) or not SHA256.fullmatch(expected) or digest(path) != expected:
        reject("fixture input digest does not match its provisioned identity")
    return path


def validate_manifest(value: str, *, root: Path = ROOT) -> dict[str, Any]:  # noqa: PLR0912, PLR0915 - closed provisioning inventory
    """All acquisition/runtime authority is explicit, immutable and owned."""
    # Lexical path refusal must precede even the mount metadata read.
    manifest_path = owned_path(value, root=root)
    prove_local_path(root)
    prove_local_path(manifest_path)
    manifest = json_file(manifest_path)
    if type(manifest.get("schema_version")) is not int or manifest["schema_version"] != 1:
        reject("fixture manifest schema is unsupported")
    fixture_id = manifest.get("fixture_id")
    if not isinstance(fixture_id, str) or str(uuid.UUID(fixture_id)) != fixture_id:
        reject("fixture ID must be a canonical UUID")
    marker_path = owned_path(manifest["marker_path"], root=root)
    marker = json_file(marker_path)
    if marker != {"schema_version": 1, "fixture_id": fixture_id, "repository_root": str(root)}:
        reject("fixture provisioning marker does not bind this repository and UUID")
    source = manifest["source"]
    if (
        source["label"] != "WEB-004, this commit"
        or not re.fullmatch(r"[a-f0-9]{40}", source["parent_commit"])
        or not SHA256.fullmatch(source["snapshot_sha256"])
    ):
        reject("fixture source provenance is unsupported")
    inputs = checked_file(source["input_manifest_path"], source["input_manifest_sha256"], root=root)
    input_manifest = json_file(inputs)
    files = input_manifest.get("files")
    if (
        input_manifest.get("schema_version") != 1
        or not isinstance(files, dict)
        or not files
        or len(files) > MAXIMUM_MEMBERS
    ):
        reject("source input manifest is missing its bounded file inventory")
    canonical = json.dumps(files, sort_keys=True, separators=(",", ":")).encode()
    if hashlib.sha256(canonical).hexdigest() != source["snapshot_sha256"]:
        reject("source snapshot identity differs from the input inventory")
    for name, expected in files.items():
        relative = Path(name)
        if relative.is_absolute() or any(part in {".", ".."} for part in name.split("/")):
            reject("source inventory contains an unsafe path")
        current = root
        for part in relative.parts:
            current /= part
            facts = current.lstat()
            if (
                stat.S_ISLNK(facts.st_mode)
                or facts.st_uid not in {0, os.getuid()}
                or facts.st_mode & 0o022
            ):
                reject("source inventory has an unowned or symlinked member")
        if not current.is_file() or digest(current) != expected:
            reject("source inventory bytes differ from this checkout")
    wheel = checked_file(manifest["wheel"]["path"], manifest["wheel"]["sha256"], root=root)
    module_root = owned_path(manifest["installed"]["module_root"], root=root, directory=True)
    installed_files = manifest["installed"]["files"]
    with zipfile.ZipFile(wheel) as archive:
        members = archive.infolist()
        if len(members) > MAXIMUM_MEMBERS:
            reject("wheel package inventory exceeds its finite member budget")
        expected_files = {}
        seen = set()
        directories = set()
        regular_files = set()
        total = 0
        for item in members:
            name = item.filename
            member = Path(name.removesuffix("/"))
            canonical = str(member) + ("/" if item.is_dir() else "")
            mode = item.external_attr >> 16
            if (
                not name
                or name != item.orig_filename
                or canonical != name
                or member.is_absolute()
                or "\\" in name
                or any(part in {".", ".."} for part in name.removesuffix("/").split("/"))
                or str(member) in seen
                or item.file_size > 8 * 1024 * 1024
                or mode & 0o7022
                or item.flag_bits & 1
                or not (stat.S_ISDIR(mode) if item.is_dir() else stat.S_ISREG(mode))
            ):
                reject("wheel package inventory has unsupported members, aliases, modes or size")
            seen.add(str(member))
            total += item.file_size
            if total > 64 * 1024 * 1024:
                reject("wheel package closure exceeds its finite byte budget")
            if item.is_dir():
                if item.file_size != 0 or archive.read(item) != b"":
                    reject("wheel directory entries must contain zero bytes")
                directories.add(member)
                continue
            regular_files.add(member)
            if not name.startswith("hfcache/"):
                continue
            relative = member.relative_to("hfcache")
            expected = hashlib.sha256(archive.read(item)).hexdigest()
            name = str(relative)
            if name in expected_files or files.get("src/hfcache/" + name) != expected:
                reject("wheel package bytes do not exactly match the reviewed source snapshot")
            checked_file(str(module_root / relative), expected, root=root)
            expected_files[name] = expected
        parents = {
            parent for member in regular_files for parent in member.parents if str(parent) != "."
        }
        if not directories <= parents:
            reject("wheel has an empty directory outside validated regular-file parents")
    if not expected_files or installed_files != expected_files:
        reject("installed byte inventory does not exactly match the supplied wheel")
    actual_files = set()
    for index, path in enumerate(module_root.rglob("*")):
        if index >= MAXIMUM_MEMBERS:
            reject("installed package exceeds its finite member budget")
        facts = path.lstat()
        relative = path.relative_to(module_root)
        if stat.S_ISLNK(facts.st_mode) or not (
            stat.S_ISREG(facts.st_mode) or stat.S_ISDIR(facts.st_mode)
        ):
            reject("installed package contains a symlink or unsupported member")
        if path.is_file() and "__pycache__" not in relative.parts:
            actual_files.add(str(relative))
    if actual_files != set(expected_files):
        reject("installed package contains bytes outside the supplied wheel inventory")
    toolchain = manifest["toolchain"]
    if (
        toolchain["node_version"] != "24.18.1"
        or toolchain["playwright_version"] != "1.64.1"
        or toolchain["image_manifest_sha256"] != IMAGE
    ):
        reject("fixture browser toolchain differs from its pinned platform")
    checked_file(toolchain["playwright_module"], toolchain["playwright_module_sha256"], root=root)
    launcher = checked_file(manifest["launcher"]["path"], manifest["launcher"]["sha256"], root=root)
    if not os.access(launcher, os.X_OK):
        reject("fixture launcher must be an executable protected regular file")
    for name in (
        "ca_certificate",
        "certificate",
        "private_key",
        "untrusted_certificate",
        "untrusted_private_key",
    ):
        checked_file(
            manifest["tls"][name],
            manifest["tls"]["hashes"][name],
            root=root,
            private=name.endswith("private_key"),
        )
    origins = manifest["origins"]
    if (
        set(origins) != {"trusted", "foreign", "untrusted"}
        or len(set(origins.values())) != PROFILE_COUNT
    ):
        reject("fixture requires three distinct provisioned loopback origins")
    for origin in origins.values():
        parsed = urlsplit(origin)
        if (
            parsed.scheme != "https"
            or parsed.hostname != "127.0.0.1"
            or parsed.port is None
            or parsed.port == 0
            or origin != f"https://127.0.0.1:{parsed.port}"
        ):
            reject("fixture origins must be canonical numeric loopback HTTPS authorities")
    evidence = owned_path(manifest["evidence_root"], root=root, directory=True)
    if evidence.stat().st_uid != os.getuid() or evidence.stat().st_mode & 0o077:
        reject("fixture evidence root must be private and current-user owned")
    manifest["_manifest_path"] = str(manifest_path)
    return manifest


class Observe:
    """Record status/credential PRESENCE only; raw headers/passwords never enter evidence."""

    def __init__(self, app: ASGIApp, *, observations: list[dict[str, Any]], profile: str) -> None:
        self.app, self.observations, self.profile = app, observations, profile

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        headers = dict(scope["headers"])
        authorization = headers.get(b"authorization", b"")
        scheme = "basic" if authorization.lower().startswith(b"basic ") else "absent-or-other"
        agent = headers.get(b"user-agent", b"").decode("ascii", "replace")
        engine = agent.removeprefix("hfcache-owned-native-auth/")
        if engine not in {"chromium", "firefox", "webkit"}:
            engine = "unclassified"

        async def capture(message: Message) -> None:
            if message["type"] == "http.response.start":
                if len(self.observations) >= MAXIMUM_OBSERVATIONS:
                    self.observations[-1]["observation_overflow"] = True
                    await send(message)
                    return
                self.observations.append(
                    {
                        "profile": self.profile,
                        "engine": engine,
                        "method": scope["method"],
                        "path": scope["path"][:512],
                        "origin": headers.get(b"origin", b"").decode("ascii", "replace")[:512],
                        "content_type": headers.get(b"content-type", b"")
                        .decode("ascii", "replace")
                        .split(";", 1)[0][:256],
                        "authentication": scheme,
                        "status": message["status"],
                        "basic_challenge": any(
                            key.lower() == b"www-authenticate" and b"Basic " in value
                            for key, value in message["headers"]
                        ),
                    }
                )
            await send(message)

        await self.app(scope, receive, capture)


def _native_challenge_retry(rows: list[dict[str, Any]], prefix: str) -> bool:
    challenge = next(
        (
            index
            for index, row in enumerate(rows)
            if row["method"] == "GET"
            and row["status"] == HTTPStatus.UNAUTHORIZED
            and row["basic_challenge"]
            and row["authentication"] == "absent-or-other"
            and row["path"] == prefix + "/api/v1/version"
        ),
        None,
    )
    retry = next(
        (
            index
            for index, row in enumerate(rows)
            if row["method"] == "GET"
            and row["status"] == HTTPStatus.OK
            and row["authentication"] == "basic"
            and row["path"] == prefix + "/api/v1/version"
        ),
        None,
    )
    return challenge is not None and retry is not None and retry > challenge


def _passive_network_observation(item: dict[str, Any], manifest: dict[str, Any]) -> None:
    state = item.get("network_observation", {})
    if (
        state.get("mode") != "passive-origin-observer"
        or state.get("request_interception") is not False
        or state.get("limit") != MAXIMUM_BROWSER_REQUESTS
        or type(state.get("request_count")) is not int
        or not 0 < state["request_count"] <= MAXIMUM_BROWSER_REQUESTS
        or state.get("invalid") is not False
        or state.get("overflow") is not False
        or state.get("expected_origins") != manifest["origins"]
        or len(state.get("observations", [])) != state["request_count"]
    ):
        reject("native-browser passive origin observation is missing or unsafe")
    for row in state["observations"]:
        category = row.get("category")
        if category not in {"trusted", "foreign", "untrusted"}:
            reject("native-browser passive origin observation contains an unexpected target")
        target = urlsplit(manifest["origins"][category])
        if (
            set(row) != {"category", "scheme", "host", "port"}
            or row["scheme"] != "https:"
            or row["host"] != "127.0.0.1"
            or type(row["port"]) is not int
            or row["port"] != target.port
        ):
            reject("native-browser passive origin observation contains unsafe metadata")


def accept_evidence(  # noqa: PLR0912 - independent per-engine HTTP/TLS/process obligations
    report: dict[str, Any],
    manifest: dict[str, Any],
    observations: list[dict[str, Any]],
    prefix: str,
) -> None:
    if (
        type(report.get("schema_version")) is not int
        or report["schema_version"] != 1
        or report.get("fixture_id") != manifest["fixture_id"]
        or set(report.get("engines", {})) != ENGINES
    ):
        reject("native-browser report lacks its exact fixture/engine identity")
    if any(row.get("observation_overflow") for row in observations):
        reject("native-browser HTTP evidence exceeded its finite observation budget")
    for engine in ENGINES:
        item = report["engines"][engine]
        if (
            any(type(item.get(field)) is not int for field in ("passed", "failed", "skipped"))
            or item["passed"] != CASE_COUNT
            or item["failed"] != 0
            or item["skipped"] != 0
            or item.get("browser_closed") is not True
            or item.get("descendants_closed") is not True
            or item.get("descendant_inventory_unknown")
            or item.get("untrusted_certificate_rejected") is not True
            or item.get("browser_drain_unknown")
            or item.get("infrastructure_failed")
            or type(item.get("browser_pid")) is not int
            or item["browser_pid"] <= 1
            or len(item.get("cases", [])) != CASE_COUNT
            or {case.get("case_id") for case in item["cases"]} != CASE_IDS
            or any(case.get("status") != "passed" for case in item["cases"])
        ):
            reject("native-browser report lacks all required real cases/counts/drain")
        _passive_network_observation(item, manifest)
        process = item.get("process", {})
        status = process.get("status", {})
        uids = status.get("uids", [])
        if (
            process.get("pid") != item["browser_pid"]
            or process.get("kind") != "live"
            or len(uids) != 4  # noqa: PLR2004 - Linux real/effective/saved/filesystem UID tuple
            or any(type(uid) is not int or uid <= 0 for uid in uids)
            or status.get("cap_eff") != "0000000000000000"
            or status.get("no_new_privs") != 1
            or process.get("command", {}).get("disabling_flags_absent") is not True
            or process.get("command", {}).get("representation") != "nul-separated-argv"
        ):
            reject("native-browser process privilege/sandbox evidence is missing or unsafe")
        if engine == "chromium":
            sandbox = item.get("sandbox", {})
            diagnostics = sandbox.get("diagnostics", {})
            if (
                sandbox.get("verified") is not True
                or sandbox.get("evaluation") != "You are adequately sandboxed."
                or diagnostics.get("Layer 1 Sandbox") != "Namespace"
                or any(
                    diagnostics.get(key) != "Yes"
                    for key in ("PID namespaces", "Network namespaces", "Seccomp-BPF sandbox")
                )
                or not sandbox.get("renderers")
            ):
                reject("native-browser Chromium namespace/seccomp sandbox is unproven")
        trusted = [
            row for row in observations if row["profile"] == "trusted" and row["engine"] == engine
        ]
        if any(row["profile"] == "untrusted" and row["engine"] == engine for row in observations):
            reject("native-browser untrusted CA reached HTTP instead of refusing TLS")
        for profile_name in ("trusted", "foreign"):
            rows = [
                row
                for row in observations
                if row["profile"] == profile_name and row["engine"] == engine
            ]
            if not _native_challenge_retry(rows, prefix):
                reject("engine did not produce both actual initial401 then native Basic200 retries")
        if not any(
            row["status"] == HTTPStatus.OK
            and row["authentication"] == "basic"
            and row["method"] == "POST"
            and row["path"] == prefix + "/api/v1/config/validate"
            and row["origin"] == manifest["origins"]["trusted"]
            for row in trusted
        ):
            reject("engine did not produce an actual native same-origin JSON validation")
        foreign = manifest["origins"]["foreign"]
        types = {
            row["content_type"]
            for row in trusted
            if row["method"] == "POST"
            and row["origin"] == foreign
            and row["status"] == HTTPStatus.FORBIDDEN
            and row["authentication"] == "basic"
        }
        if not {"text/plain", "multipart/form-data", "application/x-www-form-urlencoded"} <= types:
            reject("engine did not produce real authenticated foreign simple/form refusals")
        if not any(
            row["method"] == "OPTIONS"
            and row["origin"] == foreign
            and row["status"] in {HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN}
            for row in trusted
        ):
            reject("engine did not produce a real foreign preflight refusal")
        if any(
            row["status"] < HTTPStatus.BAD_REQUEST
            and row["origin"] == foreign
            and row["method"] not in {"GET", "HEAD"}
            for row in trusted
        ):
            reject("engine produced a successful unsafe foreign request")


def bind_listener(origin: str) -> socket.socket:
    """Reuse only the explicitly provisioned loopback port across closed profiles."""
    parsed = urlsplit(origin)
    if (
        parsed.scheme != "https"
        or parsed.hostname != "127.0.0.1"
        or parsed.port is None
        or parsed.port == 0
        or origin != f"https://127.0.0.1:{parsed.port}"
    ):
        reject("fixture listener must use a provisioned canonical loopback HTTPS origin")
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind(("127.0.0.1", parsed.port))
    except BaseException:
        listener.close()
        raise
    return listener


async def run(  # noqa: PLR0912, PLR0915 - closed actual API/browser/drain lifecycle
    manifest: dict[str, Any], workspace: Path, prefix: str = ""
) -> dict[str, Any]:
    if os.getuid() == 0 or os.geteuid() == 0:
        reject("native-browser fixture API must run as the provisioned unprivileged guest user")
    # Import only after manifest/byte verification. The guest Python environment
    # must actually import the supplied installed wheel, never this checkout.
    import hfcache
    from hfcache.api.app import create_app
    from hfcache.api.basic import create_administrator_record
    from hfcache.reporting import RuntimeVersions
    from hfcache.server import build_server
    from hfcache.server_config import validate_server_config_mapping

    if Path(hfcache.__file__).absolute().parent != Path(manifest["installed"]["module_root"]):
        reject("fixture Python did not import the verified installed wheel")
    expected_application = RuntimeVersions.measured().application
    if (
        not isinstance(expected_application, str)
        or re.fullmatch(r"[\x20-\x7e]{1,128}", expected_application) is None
    ):
        reject("installed application version lacks a bounded printable identity")
    password = secrets.token_urlsafe(48)
    username = "owned-native-operator"
    record = create_administrator_record("owned-native-subject", username, password.encode())
    observations: list[dict[str, Any]] = []
    servers = []
    before = set(threading.enumerate())
    auth_threads: set[threading.Thread] = set()
    browser = None
    outcome: dict[str, Any] = {
        "schema_version": 1,
        "scope": (
            "WEB-004 installed-wheel direct API TLS native-browser authentication; "
            "no Caddy/UI/platform rollout acceptance"
        ),
        "fixture_id": manifest["fixture_id"],
        "source": manifest["source"],
        "wheel": manifest["wheel"],
        "api_owner_pid": os.getpid(),
        "api_uid": os.getuid(),
        "api_effective_uid": os.geteuid(),
        "prefix": prefix,
        "profiles": [],
    }
    stack = AsyncExitStack()
    try:
        for name in ("trusted", "foreign", "untrusted"):
            profile = workspace / name
            profile.mkdir(mode=0o700)
            policy = profile / "archive.toml"
            policy.write_text(
                "schema_version=1\n[storage]\narchive_root="
                + json.dumps(str(profile / "absent-archive"))
                + '\narchive_id="'
                + ARCHIVE_ID
                + '"\n'
            )
            administrator = profile / "administrator.json"
            administrator.write_text(record.model_dump_json())
            administrator.chmod(0o600)
            # Existing REST token remains required; it is ephemeral and is
            # never used to turn browser native authentication into a fake.
            token = profile / "rest.token"
            token.write_text(secrets.token_urlsafe(48))
            token.chmod(0o600)
            origin = manifest["origins"][name]
            port = urlsplit(origin).port
            tcp = bind_listener(origin)
            stack.callback(tcp.close)
            certificate = "untrusted_certificate" if name == "untrusted" else "certificate"
            private_key = "untrusted_private_key" if name == "untrusted" else "private_key"
            settings = validate_server_config_mapping(
                {
                    "schema_version": 1,
                    "archive_config": str(policy),
                    "state_directory": str(profile / "state"),
                    "credentials": {"writer": {"file": str(token)}},
                    "basic": {"origin": origin, "administrator": {"file": str(administrator)}},
                    "listener": {
                        "unix_enabled": False,
                        "unix_socket": str(profile / "api.sock"),
                        "tcp_host": "127.0.0.1",
                        "tcp_port": port,
                        "root_path": prefix,
                        "allowed_origins": [origin],
                        "tls": {
                            "certificate": manifest["tls"][certificate],
                            "private_key": manifest["tls"][private_key],
                        },
                    },
                }
            )
            from hfcache import locking
            from hfcache.api.operations import OperationStore

            # Explicit offline activation of this new owned fixture before any API starts.
            # Keep real product startup noncreating and all original browser/API assertions.
            locking.LOCK_DIRECTORY = profile.parent / "intent-runtime"
            locking.LOCK_DIRECTORY.mkdir(mode=0o700, exist_ok=True)
            companion = locking.lock_path().with_name(locking.lock_path().name + ".intent")
            if not companion.exists():
                companion.touch(mode=0o600, exist_ok=False)
            with OperationStore(settings.state_directory) as fixture_store:
                fixture_store.prepare_intent_state(ARCHIVE_ID)
            app = create_app(settings, instance_lock_path=profile / "instance.lock")
            app.add_middleware(Observe, observations=observations, profile=name)
            server = build_server(app, settings)
            task = asyncio.create_task(server.serve(sockets=[tcp]))
            servers.append((name, server, task, tcp, app, profile))
            async with asyncio.timeout(20):
                while not server.started:
                    if task.done():
                        await task
                        reject("owned installed API exited before readiness")
                    await asyncio.sleep(0.01)
        (workspace / "runtime.json").write_text(
            json.dumps(
                {
                    "fixture_id": manifest["fixture_id"],
                    "prefix": prefix,
                    "expected_application": expected_application,
                }
            )
            + "\n"
        )
        launcher = manifest["launcher"]["path"]
        with (workspace / "browser.log").open("xb") as log:
            browser = await asyncio.create_subprocess_exec(
                launcher,
                "--manifest",
                manifest["_manifest_path"],
                "--workspace",
                str(workspace),
                cwd=ROOT,
                env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"},
                stdin=asyncio.subprocess.PIPE,
                stdout=log,
                stderr=subprocess.STDOUT,
            )
            outcome["launcher_pid"] = browser.pid
            assert browser.stdin is not None
            message = json.dumps({"username": username, "password": password}).encode() + b"\n"
            browser.stdin.write(message)
            await browser.stdin.drain()
            browser.stdin.close()
            del message, password
            try:
                status = await asyncio.wait_for(browser.wait(), timeout=240)
            except TimeoutError:
                browser.terminate()
                await asyncio.wait_for(browser.wait(), timeout=45)
                reject("owned native-browser deadline expired; retained exact launcher evidence")
            outcome["launcher_exit"] = status
            if status:
                reject("native-browser authentication checks failed; retained browser.log")
        report_path = workspace / "browser-report.json"
        report = json_file(report_path)
        accept_evidence(report, manifest, observations, prefix)
        outcome["browser_report_sha256"] = digest(report_path)
        outcome["browser_report"] = report
    finally:

        async def cleanup() -> None:  # noqa: PLR0912 - drain all exact owned resources
            for thread in threading.enumerate():
                if thread.name.startswith("hfcache-auth") and thread not in before:
                    auth_threads.add(thread)
            if browser is not None and browser.returncode is None:
                with suppress(ProcessLookupError):
                    browser.terminate()
                try:
                    await asyncio.wait_for(browser.wait(), timeout=45)
                except TimeoutError:
                    outcome["launcher_drain_unknown"] = True
            for name, server, task, tcp, app, profile in reversed(servers):
                provider = getattr(app.state, "basic_provider", None)
                lifespan = getattr(server, "lifespan", None)
                server.should_exit = True
                graceful = True
                try:
                    await asyncio.wait_for(asyncio.shield(task), timeout=20)
                except Exception, asyncio.CancelledError:  # noqa: BLE001 - drain every owned listener
                    graceful = False
                    # A failed serve task or force_exit omits Uvicorn lifespan
                    # shutdown. Drain it explicitly before considering raw sockets
                    # or task cancellation; abnormal cleanup still refuses acceptance.
                    if lifespan is not None and not lifespan.shutdown_event.is_set():
                        try:
                            await asyncio.wait_for(lifespan.shutdown(), timeout=20)
                        except Exception, asyncio.CancelledError:  # noqa: BLE001
                            outcome["lifespan_drain_unknown"] = True
                    if provider is not None:
                        provider.stop_admission()
                        await provider.aclose()
                    server.force_exit = True
                    if not task.done():
                        try:
                            await asyncio.wait_for(asyncio.shield(task), timeout=5)
                        except Exception, asyncio.CancelledError:  # noqa: BLE001
                            task.cancel()
                            with suppress(Exception, asyncio.CancelledError):
                                await task
                finally:
                    # asyncio's Server owns this same socket object. Closing it
                    # earlier can raise in Server.close before lifespan.shutdown.
                    tcp.close()
                if provider is not None:
                    # CPython's owned executor retains its exact Thread objects
                    # after shutdown, including workers started during the drain.
                    auth_threads.update(provider._executor._threads)  # noqa: SLF001 - exact owned thread proof
                lifespan_failed = lifespan is not None and any(
                    getattr(lifespan, flag, False)
                    for flag in ("startup_failed", "shutdown_failed", "error_occurred")
                )
                outcome["profiles"].append(
                    {
                        "name": name,
                        "listener_closed": tcp.fileno() == -1,
                        "api_task_done": task.done(),
                        "api_exit_clean": graceful
                        and not task.cancelled()
                        and task.exception() is None
                        and not lifespan_failed,
                        "lifespan_failed": lifespan_failed,
                        "lifespan_started": lifespan is not None,
                        "lifespan_shutdown": lifespan is not None
                        and lifespan.shutdown_event.is_set(),
                        "auth_active": None if provider is None else provider.stats.active,
                        "auth_waiting": None if provider is None else provider.stats.waiting,
                        "auth_reservations": None
                        if provider is None
                        else provider.stats.reservations,
                        "auth_accepting": None if provider is None else provider.stats.accepting,
                        "archive_absent": not (profile / "absent-archive").exists(),
                    }
                )
            # Also close a bound socket whose later application construction failed.
            await stack.aclose()
            for thread in threading.enumerate():
                if thread.name.startswith("hfcache-auth") and thread not in before:
                    auth_threads.add(thread)
            outcome["auth_worker_ids"] = sorted(
                thread.ident for thread in auth_threads if thread.ident is not None
            )
            outcome["auth_workers_joined"] = all(not thread.is_alive() for thread in auth_threads)
            outcome["observations"] = observations
            (workspace / "api-evidence.json").write_text(
                json.dumps(outcome, sort_keys=True, indent=2) + "\n"
            )

        # Defer repeated cancellation until every owned lifespan, worker and socket
        # has drained and the bounded evidence has been retained.
        joining = asyncio.create_task(cleanup())
        cancelled = False
        while not joining.done():
            try:
                await asyncio.shield(joining)
            except asyncio.CancelledError:
                cancelled = True
        joining.result()
        if cancelled:
            raise asyncio.CancelledError
    if (
        not outcome["auth_workers_joined"]
        or outcome.get("launcher_drain_unknown")
        or outcome.get("lifespan_drain_unknown")
        or not all(
            row["listener_closed"]
            and row["api_task_done"]
            and row["api_exit_clean"]
            and row["lifespan_shutdown"]
            and row["archive_absent"]
            and row["auth_active"] == row["auth_waiting"] == row["auth_reservations"] == 0
            and not row["auth_accepting"]
            for row in outcome["profiles"]
        )
    ):
        reject("owned authentication fixture did not prove complete worker/listener drain")
    return outcome


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument(
        "--manifest", required=True, help="owned disposable-guest provisioning manifest"
    )
    args = parser.parse_args()
    workspace = None
    try:
        manifest = validate_manifest(args.manifest)
        workspace = Path(tempfile.mkdtemp(prefix="web-auth-", dir=manifest["evidence_root"]))
        workspace.chmod(0o700)
        print(f"Retaining native authentication evidence in {workspace}", flush=True)
        profiles = []
        for name, prefix in (("root", ""), ("prefixed", "/management")):
            profile = workspace / name
            profile.mkdir(mode=0o700)
            profiles.append(asyncio.run(run(manifest, profile, prefix)))
        result = {"schema_version": 1, "profiles": profiles}
        (workspace / "SUMMARY.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        TimeoutError,
        subprocess.SubprocessError,
    ) as error:
        # Exception text may come from a browser/network dependency. Never print
        # it alongside native credential material or persist an uncontrolled trace.
        message = (
            str(error)
            if isinstance(error, FixtureRefusalError)
            else (
                "owned native authentication fixture refused or failed; "
                "inspect retained bounded evidence"
            )
        )
        if workspace is not None:
            (workspace / "BLOCKED.json").write_text(
                json.dumps({"schema_version": 1, "reason": message}) + "\n"
            )
        print(message, file=sys.stderr)
        return 1
    print("Native Chromium, Firefox and WebKit authentication passed against the installed API.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
