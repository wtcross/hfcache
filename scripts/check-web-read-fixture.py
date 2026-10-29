#!/usr/bin/env python3
"""Check built React reads against an owned local API fixture.

Only argument parsing occurs before the workspace guard. No ambient application
configuration, credential, manager, archive or container is discovered.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import re
import secrets
import shutil
import signal
import socket
import stat
import subprocess
import sys
import tempfile
import uuid
from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from starlette.types import ASGIApp, Message, Receive, Scope, Send

ROOT = Path(__file__).absolute().parents[1]
ARCHIVE_ID = "3f2a1c88-7b40-4a2e-9c1d-0e5b6a7f8d90"
MAX_MEMBERS = 4096
EXPECTED_DELAYED_COMPLETIONS = 6
LOCAL_FILESYSTEMS = frozenset({"btrfs", "ext2", "ext3", "ext4", "xfs", "zfs", "tmpfs", "overlay"})


def prove_local_path(path: Path, mountinfo: str | None = None) -> None:
    """Use mount metadata only; never traverse a target to discover its backing."""
    if mountinfo is None:
        with Path("/proc/self/mountinfo").open("rb") as stream:
            raw = stream.read(4 * 1024 * 1024 + 1)
        if len(raw) > 4 * 1024 * 1024:
            message = "local filesystem mount metadata exceeds its finite bound"
            raise ValueError(message)
        mountinfo = raw.decode("utf-8", errors="strict")
    matches = []
    for line in mountinfo.splitlines():
        before, separator, after = line.partition(" - ")
        fields, tail = before.split(), after.split()
        if not separator or len(fields) < 6 or len(tail) < 3:  # noqa: PLR2004 - kernel grammar
            message = "local filesystem mount metadata is malformed"
            raise ValueError(message)
        point = Path(re.sub(r"\\([0-7]{3})", lambda item: chr(int(item[1], 8)), fields[4]))
        if not point.is_absolute():
            message = "local filesystem mount metadata is not absolute"
            raise ValueError(message)
        if point == path or point in path.parents:
            matches.append((len(point.parts), tail[0]))
    depth = max((level for level, _ in matches), default=-1)
    if not matches or any(
        kind not in LOCAL_FILESYSTEMS for level, kind in matches if level == depth
    ):
        message = "fixture path is not proven to use an approved local filesystem"
        raise ValueError(message)


def prepare_workspace(  # noqa: PLR0912 - each rejection precedes the sole owned-leaf mutation
    value: str | None, *, root: Path = ROOT
) -> Path:
    """Refuse unknown paths before creating one positively owned local leaf."""
    base = root / ".scratch"
    if value is not None:
        if any(part in {".", ".."} for part in value.split("/")):
            msg = "workspace must not contain traversal components"
            raise ValueError(msg)
        candidate = Path(value)
        if not candidate.is_absolute():
            candidate = root / candidate
        if not candidate.is_relative_to(base) or candidate == base:
            msg = "workspace must be a new repository .scratch descendant"
            raise ValueError(msg)
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,95}", candidate.name):
            msg = "workspace leaf has unsupported grammar"
            raise ValueError(msg)
        parent = candidate.parent
    else:
        parent = base
        candidate = None
    prove_local_path(root)
    prove_local_path(parent)
    # Lexical rejection above precedes lstat of any supplied target. Never
    # resolve a symlink that could point into a deployed archive (FS-19).
    current = root
    for part in ("", *parent.relative_to(root).parts):
        if part:
            current = current / part
        try:
            facts = current.lstat()
        except FileNotFoundError:
            if current != base or parent != base:
                message = "workspace parents must already exist as owned directories"
                raise ValueError(message) from None
            current.mkdir(mode=0o700)
            facts = current.lstat()
        if not stat.S_ISDIR(facts.st_mode) or facts.st_uid != os.getuid():
            msg = "workspace ancestors must be owned ordinary directories"
            raise ValueError(msg)
        if facts.st_dev != root.stat().st_dev:
            msg = "workspace must remain on the repository local filesystem"
            raise ValueError(msg)
    if candidate is None:
        candidate = Path(tempfile.mkdtemp(prefix="web-read-fixture-", dir=base))
    else:
        candidate.mkdir(mode=0o700, exist_ok=False)
    marker = candidate / "fixture.json"
    with marker.open("x", encoding="utf-8") as stream:
        json.dump(
            {"schema_version": 1, "purpose": "WEB-003-owned-read-fixture", "id": uuid.uuid4().hex},
            stream,
            sort_keys=True,
        )
        stream.write("\n")
    marker.chmod(0o600)
    return candidate


def environment(workspace: Path) -> dict[str, str]:
    """Carry tool discovery, never ambient application or credential settings."""
    result = {key: os.environ[key] for key in ("PATH", "HOME", "PNPM_HOME") if key in os.environ}
    temporary = workspace / "tmp"
    temporary.mkdir(mode=0o700)
    result |= {
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "TMPDIR": str(temporary),
        "PLAYWRIGHT_BROWSERS_PATH": str(ROOT / "web/.cache/ms-playwright"),
    }
    return result


def build(workspace: Path, env: dict[str, str]) -> dict[str, str]:
    pnpm = shutil.which("pnpm", path=env.get("PATH"))
    node = shutil.which("node", path=env.get("PATH"))
    if pnpm is None or node is None:
        msg = "pinned Node and pnpm are required; see docs/development.md"
        raise ValueError(msg)
    output = workspace / "built-ui"
    with (workspace / "build.log").open("xb") as log:
        child = subprocess.Popen(  # noqa: S603 - direct fixed Vite argv and owned process group
            [
                node,
                str(ROOT / "web/node_modules/vite/bin/vite.js"),
                "build",
                "--config",
                "test/read-api/vite.config.ts",
                "--outDir",
                str(output),
            ],
            cwd=ROOT / "web",
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        try:
            status = child.wait(timeout=120)
        except subprocess.TimeoutExpired:
            # This new session contains only our direct Vite build and its
            # compiler children. Never signal an ambient tool/service group.
            os.killpg(child.pid, signal.SIGTERM)
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait(timeout=5)
            msg = "owned read fixture build exceeded its deadline"
            raise ValueError(msg) from None
    if status:
        msg = "read fixture build failed; retained build.log"
        raise ValueError(msg)
    members = {}
    total = 0
    for path in sorted(output.rglob("*")):
        if path.is_symlink() or (not path.is_dir() and not path.is_file()):
            msg = "fixture build contains an unsupported member"
            raise ValueError(msg)
        if path.is_file():
            raw = path.read_bytes()
            total += len(raw)
            if len(raw) > 8 * 1024 * 1024 or path.suffix not in {".html", ".js", ".css"}:
                msg = "fixture build member exceeds the allowed static closure"
                raise ValueError(msg)
            members[str(path.relative_to(output))] = hashlib.sha256(raw).hexdigest()
    if not members or len(members) > MAX_MEMBERS or total > 64 * 1024 * 1024:
        msg = "fixture build exceeds its finite collection budget"
        raise ValueError(msg)
    return members


def model_corpus() -> dict[str, Any]:
    """Serialize original models, never derive expected fixtures from generated IR."""
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from pydantic import ValidationError

    from hfcache.catalog_models import ModelVariant
    from hfcache.catalog_query_models import CatalogEntry, CatalogSearchPayload
    from hfcache.client_models import Capabilities, ClientRead
    from hfcache.errors import HfcacheError
    from hfcache.models import Reference
    from tests.web_wire_corpus import serialized_corpus

    authorities = {
        "ClientRead": ClientRead,
        "Capabilities": Capabilities,
        "CatalogSearchPayload": CatalogSearchPayload,
        "CatalogEntry": CatalogEntry,
        "ModelVariant": ModelVariant,
        "Reference": Reference,
    }
    literals = json.loads((ROOT / "tests/fixtures/web_wire/goldens.json").read_text())
    originals = []
    for fixture in literals:
        original = authorities[fixture["definition"]].model_validate(fixture["value"])
        originals.append(fixture | {"value": original.model_dump(mode="json")})
    originals.extend(serialized_corpus())
    incorrect = []
    for index, field, value in (
        (0, "schema_version", 2),
        (1, "maintenance_enabled", 0),
        (4, "total_bytes", 1),
        (5, "commit_sha", "not-an-exact-commit"),
    ):
        fixture = json.loads(json.dumps(literals[index]))
        fixture["case_id"] = "incorrect-" + fixture["case_id"]
        fixture["value"][field] = value
        try:
            authorities[fixture["definition"]].model_validate(fixture["value"])
        except ValidationError, HfcacheError:
            incorrect.append(fixture)
        else:
            message = "independent incorrect wire is no longer rejected by its original authority"
            raise ValueError(message)
    return {"originals": originals, "incorrect": incorrect}


def fault_body(fault: str, raw: bytes) -> bytes:
    """Change transport only after real auth/service completion; never positive facts."""
    if fault == "delay":
        return raw
    if fault == "response-limit":
        # Valid JSON plus whitespace crosses the session's 8 MiB read bound.
        return raw + b" " * (8 * 1024 * 1024)
    payload = json.loads(raw)
    if fault == "schema-version":
        payload["schema_version"] = 2
    else:
        payload["envelope"]["data"]["max_page_size"] = 9007199254740993
    return json.dumps(payload, ensure_ascii=False).encode()


class FixtureRoutes:
    """Test-only indexed assets/control and an explicitly labelled wire fault.

    Every API call still enters the actual authentication and service boundary.
    The corruption mode changes a completed real version response downstream;
    it never substitutes a fake service result for positive acceptance.
    """

    def __init__(  # noqa: PLR0913 - explicit closed test-fixture bindings
        self,
        app: ASGIApp,
        *,
        owner: Any,
        built: Path,
        prefix: str,
        token: str,
        config: Path,
        original_config: bytes,
        observations: list[dict[str, Any]],
    ) -> None:
        self.app, self.owner, self.prefix = app, owner, prefix
        self.token, self.config, self.original_config = token, config, original_config
        self.observations = observations
        self.corpus = json.dumps(model_corpus(), ensure_ascii=False).encode("utf-8")
        if len(self.corpus) > 1024 * 1024:
            message = "original model roundtrip fixture exceeds its independent byte budget"
            raise ValueError(message)
        self.index = (built / "index.html").read_text()
        self.assets = {}
        for path in built.rglob("*"):
            if path.is_file() and path.name != "index.html":
                self.assets[prefix + "/ui/" + str(path.relative_to(built))] = (
                    path.read_bytes(),
                    "text/javascript" if path.suffix == ".js" else "text/css",
                )

    async def __call__(  # noqa: PLR0915 - closed fixture routes plus actual-response fault capture
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        from starlette.responses import JSONResponse, Response

        if scope["type"] != "http":

            async def lifecycle_send(message: Message) -> None:
                if message["type"] == "lifespan.startup.failed":
                    (self.config.parent / "startup-failure.log").write_text(
                        message.get("message", "")
                    )
                await send(message)

            await self.app(scope, receive, lifecycle_send)
            return
        path, method = scope["path"], scope["method"]
        if path == self.prefix + "/__fixture__/original-models.json" and method == "GET":
            authorized = secrets.compare_digest(
                dict(scope["headers"]).get(b"authorization", b""), ("Bearer " + self.token).encode()
            )
            response = (
                Response(
                    self.corpus,
                    media_type="application/json",
                    headers={"Cache-Control": "no-store"},
                )
                if authorized
                else JSONResponse({"fixture_models": "refused"}, status_code=401)
            )
            await response(scope, receive, send)
            return
        if path == self.prefix + "/ui/" and method == "GET":
            import html

            rendered = self.index
            for key, value in {
                "API_BASE": self.prefix,
                "INSTANCE_ID": self.owner.state.instance_id,
                "ARCHIVE_ID": ARCHIVE_ID,
            }.items():
                rendered = rendered.replace(
                    "__HFCACHE_TEST_" + key + "__", html.escape(value, quote=True)
                )
            await Response(
                rendered,
                media_type="text/html",
                headers={
                    "Cache-Control": "no-store",
                    "Content-Security-Policy": (
                        "default-src 'none'; script-src 'self'; style-src 'self'; "
                        "connect-src 'self'; base-uri 'none'; frame-ancestors 'none'; "
                        "form-action 'none'"
                    ),
                    "X-Content-Type-Options": "nosniff",
                },
            )(scope, receive, send)
            return
        if path in self.assets and method == "GET":
            body, mime = self.assets[path]
            await Response(
                body,
                media_type=mime,
                headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
            )(scope, receive, send)
            return
        controls = {
            self.prefix + "/__fixture__/policy-invalid",
            self.prefix + "/__fixture__/policy-restore",
        }
        if path in controls:
            headers = dict(scope["headers"])
            authorized = secrets.compare_digest(
                headers.get(b"authorization", b""), ("Bearer " + self.token).encode()
            )
            if method != "POST" or not authorized or headers.get(b"x-hfcache-fixture") != b"1":
                await JSONResponse({"fixture_control": "refused"}, status_code=403)(
                    scope, receive, send
                )
                return
            self.config.write_bytes(
                b"broken = [\n" if path.endswith("policy-invalid") else self.original_config
            )
            await JSONResponse({"fixture_control": "changed"})(scope, receive, send)
            return
        fault = dict(scope["headers"]).get(b"x-hfcache-fixture-fault", b"").decode("ascii")
        forwarded = scope | {
            "headers": [
                (key, value)
                for key, value in scope["headers"]
                if key.lower() != b"x-hfcache-fixture-fault"
            ]
        }
        corrupt = method == "GET" and (
            (
                fault in {"schema-version", "response-limit"}
                and path == self.prefix + "/api/v1/version"
            )
            or (fault == "unsafe-integer" and path == self.prefix + "/api/v1/capabilities")
            or (
                fault == "delay"
                and path
                in {
                    self.prefix + "/api/v1/" + leaf
                    for leaf in ("version", "capabilities", "status")
                }
            )
        )
        messages: list[Message] = []

        async def capture(message: Message) -> None:
            if corrupt:
                messages.append(message)
            else:
                if message["type"] == "http.response.start":
                    self.observations.append(
                        {
                            "method": method,
                            "path": path,
                            "status": message["status"],
                            "post_service_schema_fault": False,
                        }
                    )
                await send(message)

        await self.app(forwarded, receive, capture)
        if corrupt:
            start = next(
                message for message in messages if message["type"] == "http.response.start"
            )
            raw = b"".join(
                message.get("body", b"")
                for message in messages
                if message["type"] == "http.response.body"
            )
            if start["status"] != HTTPStatus.OK or len(raw) > 1024 * 1024:
                msg = "post-service fault did not receive the bounded real response"
                raise ValueError(msg)
            body = fault_body(fault, raw)
            headers = [
                (key, value) for key, value in start["headers"] if key.lower() != b"content-length"
            ]
            headers.append((b"content-length", str(len(body)).encode()))
            self.observations.append(
                {
                    "method": method,
                    "path": path,
                    "status": start["status"],
                    "post_service_schema_fault": fault == "schema-version",
                    "post_service_transport_fault": fault,
                    "completed_service_bytes": len(raw),
                    "transport_body_bytes": len(body),
                }
            )
            await send(start | {"headers": headers})
            if fault == "delay":
                # Headers prove actual auth/service completion while the body remains pending.
                await asyncio.sleep(0.25)
            await send({"type": "http.response.body", "body": body})


async def exercise(  # noqa: PLR0915 - one actual fixture lifecycle retains drain evidence
    workspace: Path, built: Path, env: dict[str, str], prefix: str
) -> dict[str, Any]:
    from hfcache.api.app import create_app
    from hfcache.server import build_server
    from hfcache.server_config import validate_server_config_mapping

    profile = workspace / ("prefixed" if prefix else "root")
    profile.mkdir(mode=0o700)
    config = profile / "archive.toml"
    config.write_text(
        "schema_version=1\n[storage]\narchive_root="
        + json.dumps(str(profile / "absent-archive"))
        + '\narchive_id="'
        + ARCHIVE_ID
        + '"\n'
    )
    config.chmod(0o600)
    original = config.read_bytes()
    tokens = {}
    for name in ("writer", "reader"):
        token = secrets.token_urlsafe(48)
        path = profile / (name + ".token")
        path.write_text(token)
        path.chmod(0o600)
        tokens[name] = (token, path)
    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp.bind(("127.0.0.1", 0))
    port = tcp.getsockname()[1]
    settings = validate_server_config_mapping(
        {
            "schema_version": 1,
            "archive_config": str(config),
            "state_directory": str(profile / "api-state"),
            "credentials": {name: {"file": str(path)} for name, (_, path) in tokens.items()},
            "listener": {
                "unix_enabled": False,
                "unix_socket": str(profile / "api.sock"),
                "tcp_host": "127.0.0.1",
                "tcp_port": port,
                "root_path": prefix,
            },
        }
    )
    app = create_app(settings, instance_lock_path=profile / "instance.lock")
    observations: list[dict[str, Any]] = []
    app.add_middleware(
        FixtureRoutes,
        owner=app,
        built=built,
        prefix=prefix,
        token=tokens["reader"][0],
        config=config,
        original_config=original,
        observations=observations,
    )
    app.middleware_stack = app.build_middleware_stack()
    server = build_server(app, settings)
    task = asyncio.create_task(server.serve(sockets=[tcp]))
    child = None
    outcome: dict[str, Any] = {"prefix": prefix, "api_process_id": os.getpid()}
    try:
        async with asyncio.timeout(15):
            while not server.started:
                if task.done():
                    await task
                    startup_error = server.startup_errors.error
                    msg = "owned API exited before readiness"
                    if startup_error is not None:
                        msg += ": " + str(startup_error)
                    raise ValueError(msg)
                await asyncio.sleep(0.01)
        origin = f"http://127.0.0.1:{port}"
        node = shutil.which("node", path=env.get("PATH"))
        if node is None:
            msg = "pinned Node is required"
            raise ValueError(msg)
        browser_env = env | {
            "HFCACHE_READ_FIXTURE_ORIGIN": origin,
            "HFCACHE_READ_FIXTURE_PREFIX": prefix,
            "HFCACHE_READ_FIXTURE_TOKEN_FILE": str(tokens["reader"][1]),
            "HFCACHE_READ_FIXTURE_WORKSPACE": str(profile),
        }
        with (profile / "browser.log").open("xb") as log:
            child = await asyncio.create_subprocess_exec(
                node,
                str(ROOT / "web/test/read-api/run.ts"),
                cwd=ROOT / "web",
                env=browser_env,
                stdout=log,
                stderr=subprocess.STDOUT,
            )
            try:
                status = await asyncio.wait_for(child.wait(), timeout=150)
            except TimeoutError:
                child.terminate()
                try:
                    await asyncio.wait_for(child.wait(), timeout=15)
                except TimeoutError as error:
                    msg = "owned browser wrapper drain is unknown; preserve workspace and PID"
                    raise ValueError(msg) from error
                msg = "owned browser fixture exceeded its deadline"
                raise ValueError(msg) from None
        outcome["browser_wrapper_pid"], outcome["browser_exit"] = child.pid, status
        if status:
            msg = "real API read browser check failed; retained browser.log"
            raise ValueError(msg)
        required = {
            (prefix + "/api/v1/" + path, 200)
            for path in ("version", "capabilities", "status", "archive/inspection")
        }
        seen = {(item["path"], item["status"]) for item in observations}
        if (
            not required <= seen
            or (prefix + "/api/v1/status", 503) not in seen
            or not any(item["post_service_schema_fault"] for item in observations)
            or not {"delay", "response-limit", "unsafe-integer"}
            <= {item.get("post_service_transport_fault") for item in observations}
            or sum(item.get("post_service_transport_fault") == "delay" for item in observations)
            != EXPECTED_DELAYED_COMPLETIONS
        ):
            msg = "required actual service success/failure/fault reads did not execute"
            raise ValueError(msg)
        if config.read_bytes() != original or (profile / "absent-archive").exists():
            msg = "fixture policy was not restored or an archive was unexpectedly created"
            raise ValueError(msg)
    finally:
        server.should_exit = True
        await asyncio.wait_for(task, timeout=15)
        tcp.close()
        pool = getattr(app.state, "pool", None)
        outcome["api_lifespan_drained"] = task.done() and (pool is None or pool.inflight == 0)
        outcome["api_started"] = server.started
        outcome["api_listener_closed"] = tcp.fileno() == -1
        outcome["observations"] = observations
        (profile / "api-evidence.json").write_text(
            json.dumps(outcome, sort_keys=True, indent=2) + "\n"
        )
    if not outcome["api_lifespan_drained"] or not outcome["api_listener_closed"]:
        msg = "owned API lifecycle did not drain"
        raise ValueError(msg)
    return outcome


def run(workspace: Path) -> dict[str, Any]:
    env = environment(workspace)
    members = build(workspace, env)
    profiles = [
        asyncio.run(exercise(workspace, workspace / "built-ui", env, prefix))
        for prefix in ("", "/management")
    ]
    return {
        "schema_version": 1,
        "scope": (
            "WEB-003 source-built real HTTP/API React read fixture; "
            "no Caddy, Basic, installed or platform acceptance"
        ),
        "workspace": str(workspace),
        "built_members": members,
        "profiles": profiles,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument(
        "--workspace",
        help="new owned repository .scratch directory; default creates a unique retained directory",
    )
    args = parser.parse_args()
    workspace = None
    try:
        workspace = prepare_workspace(args.workspace)
        print(f"Retaining owned read-fixture evidence in {workspace}", flush=True)
        summary = run(workspace)
        (workspace / "SUMMARY.json").write_text(
            json.dumps(summary, sort_keys=True, indent=2) + "\n"
        )
    except (OSError, ValueError, TimeoutError, subprocess.SubprocessError) as error:
        message = (
            str(error)
            if isinstance(error, ValueError)
            else "owned read-fixture prerequisite or process failure"
        )
        if workspace is not None:
            (workspace / "BLOCKED.json").write_text(
                json.dumps(
                    {"schema_version": 1, "scope": "owned WEB-003 fixture only", "reason": message},
                    sort_keys=True,
                    indent=2,
                )
                + "\n"
            )
        print(message, file=sys.stderr)
        return 1
    print(
        "Real HTTP/API React read fixture passed; "
        "Caddy/Basic/installed acceptance remains separate."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
