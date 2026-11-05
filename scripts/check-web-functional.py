#!/usr/bin/env python3
"""Check built web interfaces in an explicitly owned disposable test deployment.

Application and platform profiles require protected, digest-bound provisioning.
Help performs no environment discovery, credential access or runtime action.
"""

from __future__ import annotations

import argparse
import asyncio
import errno
import hashlib
import importlib.metadata
import itertools
import json
import os
import pwd
import re
import secrets
import ssl
import stat
import struct
import sys
import tempfile
import tomllib
import uuid
import zipfile
from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING, Any, NoReturn
from urllib.parse import urlsplit

if TYPE_CHECKING:
    from collections.abc import Callable

ROOT = Path(__file__).absolute().parents[1]
NATIVE_PREFIX = Path("/opt/hfcache")
NATIVE_OWNER = 0
MAXIMUM_JSON = 2 * 1024 * 1024
MAXIMUM_SOURCE_FILES = 4096
MAXIMUM_MEMBER_BYTES = 8 * 1024 * 1024
MAXIMUM_ASSET_BYTES = 64 * 1024 * 1024
MAXIMUM_REPORT_BYTES = 4 * 1024 * 1024
MAXIMUM_COMMAND_BYTES = 1024 * 1024
MAXIMUM_TOOL_BYTES = 256 * 1024 * 1024
MAXIMUM_BROWSER_REQUESTS = 256
MAXIMUM_PATH_BYTES = 1024
MAXIMUM_PATH_DEPTH = 8
MAXIMUM_COMPONENT_BYTES = 255
MAXIMUM_ASSET_ENTRIES = 8193
REQUIRED_CASE_COUNT = 95
UID_FIELDS = 4
SECCOMP_FILTER = 2
MAXIMUM_ARGUMENTS = 256
MINIMUM_MOUNT_FIELDS = 6
MINIMUM_MOUNT_TRAILING_FIELDS = 3
CADDY_AUTHORITY_PATHS = {"/srv/hfcache", "/etc/hfcache", "/run/hfcache-host-helper"}
NATIVE_ACTIVATION_FD = 3
MAXIMUM_THREADS = 64
MAXIMUM_EVENTS = 4096
MAXIMUM_HTTP_STATUS = 599
MAXIMUM_TRANSFER_EVENTS = 256
MAXIMUM_BODY_SENDS = 130
TRANSFER_EVIDENCE_VERSION = 2
MAXIMUM_PROTOCOL_BUFFER_BYTES = 1048576
H11_PROTOCOL_SOURCE_SHA256 = "a3154a6c2cfaaaebe19ac7aa255dfe9b6b7b490de1da95274c033aa093e8c322"
STATIC_BROWSER_CANCELS = 8
FIXTURE_SEND_BUFFER_REQUESTED = 4096
FIXTURE_SEND_BUFFER_OBSERVED = 8192
MAXIMUM_UI_CHUNK_BYTES = 65536
MAXIMUM_UI_STREAMS = 16
MAXIMUM_UI_TASKS = 32
MAXIMUM_PROBE_MS = 45000
MAXIMUM_BPF_INSTRUCTIONS = 512
MAXIMUM_BPF_STATES = 4096
BPF_CGROUP_SKB_TYPE = 8
BPF_MAXIMUM_REGISTER = 10
BPF_MAXIMUM_CONTEXT_OFFSET = 4096
BPF_EXIT = 0x95
BPF_JUMP_ALWAYS = 0x05
BPF_JUMP_NOT_EQUAL = 0x55
BPF_MOVE64_IMMEDIATE = 0xB7
BPF_MOVE32_REGISTER = 0xBC
BPF_OR32_IMMEDIATE = 0x44
ORIGIN_EVIDENCE_VERSION = 2
UID_MAPPING_FIELDS = 3
MINIMUM_CONTROL_PROCESSES = 3
MINIMUM_CONTROL_CGROUPS = 2
BPF_QUERY_COUNT = 4
BPF_QUERY_BACKING_BYTES = 256
BPF_QUERY_PREFIX_BYTES = 64
BPF_QUERY_IDS = 64
MAXIMUM_BPF_PROGRAMS = 8
SOCKET_TUPLE_FIELDS = 2
CONTROL_ACCEPT_COUNT = 4
NETWORK_NONCE_COUNT = 6
CONTROL_LISTENER_COUNT = 2
MAXIMUM_SAFE_LABEL = 128
MAXIMUM_NETWORK_ATTEMPT_NS = 5_000_000_000
WORKER_POLICY_SHA256 = "08f97ffb4a6e9b48dcf95ec19fd41432b766b2a69c42fcc4e5991dd1d571c221"
STOCK_POLICY_SHA256 = "ffba5b06a9343516f61d46b0e86c95448bbe2a94f26d5cb04f9c79c52382b1bc"
SOCKET_CONTROL_SHA256 = "909000ef7d5abc91edfcf28e583d6a42e1c95183a58d0d899d9446faf87c09ce"
PROGRAM_AUDITOR_SHA256 = "1cd191295ae57143e2de3c2c3da6519e034c3610e517b4150c5f8b24f1eaa1e2"
WORKER_POLICY_PATH = "/opt/hfcache-web005/worker-seccomp-v1.json"
STOCK_POLICY_PATH = "/usr/share/containers/seccomp.json"
SOCKET_RECEIPT_PATH = "/opt/hfcache-web005/rootless-socket-availability-v1/receipt.json"
NATIVE_HARDENING = {
    **dict.fromkeys(
        (
            "NoNewPrivileges",
            "PrivateTmp",
            "PrivateDevices",
            "ProtectHome",
            "ProtectKernelTunables",
            "ProtectKernelModules",
            "ProtectKernelLogs",
            "ProtectControlGroups",
            "ProtectClock",
            "ProtectHostname",
            "RestrictNamespaces",
            "LockPersonality",
        ),
        "true",
    ),
    "ProtectSystem": "strict",
    "ProtectProc": "invisible",
    "ProcSubset": "pid",
    "CapabilityBoundingSet": "",
    "AmbientCapabilities": "",
    "SystemCallArchitectures": "native",
    "RestrictAddressFamilies": "AF_UNIX AF_INET AF_INET6",
}
MINIMUM_REMOTE_DEADLINE_MS = 28000
MINIMUM_CLIENT_DEADLINE_MS = 34900
NANOSECONDS_PER_MILLISECOND = 1_000_000
MINIMUM_CANCEL_NS = 1_500_000_000
MAXIMUM_CANCEL_NS = 10_000_000_000
MINIMUM_DEADLINE_NS = 29_000_000_000
MAXIMUM_DEADLINE_NS = 36_000_000_000
BROWSER_VERSIONS = {"chromium": "156.0.8078.4", "firefox": "157.0", "webkit": "27.2"}
ENGINES = {"chromium", "firefox", "webkit"}
DEPLOYMENTS = {"application", "native", "rootless"}
PREFIXES = ("", "/management")
SHA256 = re.compile(r"[a-f0-9]{64}")
IDENTIFIER = re.compile(r"[a-f0-9]{32}")
COMMIT = re.compile(r"[a-f0-9]{40}")
MCP_TOOLS = {
    "get_archive_status",
    "list_repositories",
    "list_revisions",
    "get_current_reference",
    "get_revision_manifest",
    "list_run_reports",
    "get_run_report",
    "get_verification_report",
    "estimate_verification",
    "search_models",
    "search_datasets",
    "get_catalog_entry",
    "list_model_variants",
    "get_catalog_facets",
}
# Each acceptance row is derived from this engine's actual assertion records.
# Role/trust/network/transfer/drain evidence remains mandatory before extraction.
CASE_ASSERTIONS = {
    "AUTH-01": {"native-ui-challenge", "validated-bootstrap", "same-origin-json-validation"},
    "AUTH-04": {
        "credential-class-isolation",
        "bearer-rest-with-browser",
        "all-mcp-tools-with-browser",
    },
    "AUTH-06": {"bearer-rest-with-browser"},
    "AUTH-09": {"native-ui-challenge", "plaintext-refused", "untrusted-certificate-refused"},
    "ROUTE-01": {"native-ui-challenge", "bearer-rest-with-browser", "all-mcp-tools-with-browser"},
    "ROUTE-02": {
        "native-ui-challenge",
        "native-prefix-projection",
        "same-origin-security-headers",
        "api-pagination",
        "all-mcp-tools-with-browser",
    },
    "ROUTE-03": {
        "workspaces-deep-refresh",
        "history-back-forward",
        "exact-publication-refresh-history",
        "publication-files-locators-and-history",
    },
    "ROUTE-04": {"missing-assets-isolated", "api-mcp-errors-not-html", "unsafe-method-no-fallback"},
    "ROUTE-06": {"same-origin-security-headers", "missing-assets-isolated"},
    "ROUTE-07": {"same-origin-network", "all-mcp-tools-with-browser"},
    "CONFIG-03": {
        "config-two-sessions-same-full-byte-base",
        "config-session-a-tag-only-validate",
        "config-session-a-reviewed-empty-preview",
        "config-session-b-tag-only-validate",
        "config-session-b-reviewed-empty-preview",
        "config-session-a-one-reviewed-apply",
        "config-session-a-confirm-original-host-outcome",
        "config-session-b-stale-apply-refusal",
        "config-session-b-compare-retains-original-intent",
        "config-session-a-original-preview-after-reload",
        "config-session-a-original-apply-after-reload",
        "config-session-a-original-host-outcome-after-reload",
        "config-session-b-original-preview-after-reload",
    },
    "CATALOG-01": {
        "library-type-and-repository-scopes",
        "library-literal-id-tag-not-readme",
        "library-current-and-retained-publications",
    },
    "CATALOG-02": {
        "library-tags-default-corpus",
        "library-tags-canonical-all",
        "library-tags-all-and-missing",
        "library-tags-clear-after-all",
        "library-tags-any",
        "library-tags-groups-combine-with-and",
        "library-tags-clear-before-observed",
        "library-tags-last-observed",
        "library-tags-current-only-withholds-old",
        "library-tags-clear-before-unpublished",
        "library-tags-disabled-unpublished",
        "library-tags-clear-before-count-bound",
        "library-tags-64-accepted",
        "library-tags-65-refused",
        "library-tags-restore-valid-count",
        "library-tags-64-canonical-128-raw",
        "library-tags-65-canonical-refused",
        "library-tags-129-raw-refused",
        "library-tags-restore-default",
    },
    "CATALOG-03": {
        "publication-model-dataset-static-evidence",
        "library-technical-primary-GGUF-all-predicates",
        "library-technical-one-byte-below-excludes-GGUF",
        "library-technical-primary-GPTQ-same-variant",
        "library-technical-cross-variant-format-method-bits",
        "library-technical-cross-variant-scheme-bits",
        "library-technical-adapter-excluded",
        "library-technical-projector-excluded",
        "library-technical-unknown-role-excluded",
        "library-technical-incomplete-members-excluded",
    },
    "CATALOG-04": {"library-total-page-coverage-and-zero"},
    "CATALOG-07": {"publication-model-dataset-static-evidence"},
    "CARD-11": {
        "readme-active-corpus-fails-closed",
        "readme-blocked-resources-and-pinned-links",
        "same-origin-network",
    },
    "RELEASE-03": {
        "same-origin-network",
        "native-ui-challenge",
        "bearer-rest-with-browser",
        "all-mcp-tools-with-browser",
    },
}
BASELINE_BROWSER_CASES = {
    "static-abort-drain",
    "native-ui-challenge",
    "validated-bootstrap",
    "workspaces-deep-refresh",
    "history-back-forward",
    "same-origin-security-headers",
    "missing-assets-isolated",
    "api-mcp-errors-not-html",
    "unsafe-method-no-fallback",
    "bearer-rest-with-browser",
    "all-mcp-tools-with-browser",
    "native-prefix-projection",
    "plaintext-refused",
    "untrusted-certificate-refused",
    "private-browser-storage",
    "same-origin-network",
    "same-origin-json-validation",
    "exact-publication-refresh-history",
    "api-pagination",
    "credential-class-isolation",
    "denied-basic-read-auth",
    "denied-basic-csrf",
    "no-browser-errors",
    "library-type-and-repository-scopes",
    "library-literal-id-tag-not-readme",
    "library-current-and-retained-publications",
    "library-tags-default-corpus",
    "library-tags-canonical-all",
    "library-tags-all-and-missing",
    "library-tags-clear-after-all",
    "library-tags-any",
    "library-tags-groups-combine-with-and",
    "library-tags-clear-before-observed",
    "library-tags-last-observed",
    "library-tags-current-only-withholds-old",
    "library-tags-clear-before-unpublished",
    "library-tags-disabled-unpublished",
    "library-tags-clear-before-count-bound",
    "library-tags-64-accepted",
    "library-tags-65-refused",
    "library-tags-restore-valid-count",
    "library-tags-64-canonical-128-raw",
    "library-tags-65-canonical-refused",
    "library-tags-129-raw-refused",
    "library-tags-restore-default",
    "library-technical-primary-GGUF-all-predicates",
    "library-technical-one-byte-below-excludes-GGUF",
    "library-technical-primary-GPTQ-same-variant",
    "library-technical-cross-variant-format-method-bits",
    "library-technical-cross-variant-scheme-bits",
    "library-technical-adapter-excluded",
    "library-technical-projector-excluded",
    "library-technical-unknown-role-excluded",
    "library-technical-incomplete-members-excluded",
    "library-total-page-coverage-and-zero",
    "publication-files-locators-and-history",
    "publication-model-dataset-static-evidence",
    "readme-active-corpus-fails-closed",
    "readme-blocked-resources-and-pinned-links",
    "readme-sanitized-source-secret-and-format-bounds",
    "ordinary-config-read-projection",
    "ordinary-tag-draft-first-validation",
    "ordinary-explicit-second-validation",
    "ordinary-discard-fresh-UI-read",
    "config-numeric-lexical-leading-zero",
    "config-numeric-lexical-exponent",
    "config-numeric-lexical-fraction",
    "config-numeric-lexical-unsafe-integer",
    "config-numeric-range-free-gib-upper",
    "config-numeric-range-free-percent-upper",
    "config-numeric-range-workers-upper",
    "config-numeric-range-sync-wait-upper",
    "config-numeric-range-staging-lower",
    "config-numeric-range-verification-wait-upper",
    "config-numeric-range-repair-grace-lower",
    "config-tag-refusal-raw-count-before-deduplication",
    "config-tag-refusal-raw-length-before-trim",
    "config-tag-refusal-nonascii",
    "config-tag-refusal-empty-line",
    "config-json-refusal-malformed",
    "config-json-refusal-mixed-managed-and-candidate",
    "config-json-refusal-json-pointer",
    "config-json-refusal-protected-root",
    "config-json-refusal-coercive-integer",
    "config-json-refusal-coercive-boolean",
    "config-json-refusal-noninteger-lexeme",
    "config-json-refusal-duplicate-identity",
    "config-json-refusal-reordered-existing",
    "config-two-sessions-same-full-byte-base",
    "config-session-a-tag-only-validate",
    "config-session-a-reviewed-empty-preview",
    "config-session-b-tag-only-validate",
    "config-session-b-reviewed-empty-preview",
    "config-session-a-one-reviewed-apply",
    "config-session-a-confirm-original-host-outcome",
    "config-session-b-stale-apply-refusal",
    "config-session-b-compare-retains-original-intent",
    "config-session-a-original-preview-after-reload",
    "config-session-a-original-apply-after-reload",
    "config-session-a-original-host-outcome-after-reload",
    "config-session-b-original-preview-after-reload",
}
BROWSER_CASES = BASELINE_BROWSER_CASES | {"rich-card-dom-and-pinned-files"}
COMMON_ASSERTIONS = {
    "validated-bootstrap",
    "private-browser-storage",
    "same-origin-network",
    "no-browser-errors",
}
BASIC_READ_REFUSALS = {
    "missing": 0,
    "wrong-user": 1,
    "wrong-password": 1,
    "malformed-base64": 1,
    "missing-colon": 1,
    "noncanonical-base64": 1,
    "invalid-utf8-user": 1,
    "invalid-utf8-password": 1,
    "duplicate-headers": 2,
    "duplicate-schemes": 1,
    "oversized-user": 1,
    "oversized-password": 1,
    "oversized-authorization": 1,
}
MAXIMUM_BASIC_REFUSAL_BYTES = 4096
ROLE_CHECKS = {
    "api_unprivileged",
    "api_unix_only",
    "single_api_lifespan",
    "single_caddy",
    "worker_peer_verified",
    "worker_ip_denied",
    "worker_credentials_denied",
    "caddy_archive_denied",
    "caddy_policy_denied",
    "caddy_credentials_denied",
    "caddy_helper_denied",
    "selinux_enforcing",
    "no_privilege_weakening",
}
ROLE_DRAINS = {
    "api_lifespan",
    "api_listener",
    "api_streams",
    "api_metadata_pool",
    "api_auth_workers",
    "worker_executor",
    "worker_listener",
    "caddy",
    "browser_containers",
    "owned_descendants",
}
HELPER_BOOTSTRAP = {
    "/usr/local/libexec/hfcache-host-helper": ("host-helper.py", "helper_daemon", 0o755),
    "/etc/systemd/system/hfcache-host-helper.service": (
        "hfcache-host-helper.service",
        "helper_unit",
        0o644,
    ),
    "/usr/local/lib/hfcache-host-helper/hfcache-host-helper.cil": (
        "hfcache-host-helper.cil",
        "helper_selinux_policy",
        0o644,
    ),
    **{
        "/usr/local/lib/hfcache-host-helper/" + name + ".py": (name + ".py", role, 0o644)
        for name, role in (
            ("host_policy", "helper_policy_module"),
            ("host_protocol", "helper_protocol_module"),
            ("host_configuration", "helper_configuration_module"),
            ("host_actions", "helper_actions_module"),
            ("host_selinux", "helper_selinux_module"),
            ("host_peer", "helper_peer_module"),
        )
    },
}
MIME = {
    ".html": "text/html",
    ".css": "text/css",
    ".js": "text/javascript",
    ".json": "application/json",
    ".png": "image/png",
    ".webp": "image/webp",
    ".woff2": "font/woff2",
}


class FunctionalRefusalError(ValueError):
    """Only fixed nonsecret diagnostics cross the runner boundary."""


def reject(message: str) -> NoReturn:
    raise FunctionalRefusalError(message)


def require(condition: object, message: str) -> None:
    if not condition:
        reject(message)


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode()


def persist_bytes(path: Path, body: bytes) -> None:
    """Retain an exclusive durable copy without replacing earlier evidence."""
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(body)
        stream.flush()
        os.fsync(stream.fileno())
    directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def persist_json(path: Path, value: object) -> None:
    """Retain intent before effects without replacing earlier evidence."""
    persist_bytes(path, canonical(value))


def duplicate_refusal(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value = {}
    for key, item in pairs:
        require(key not in value, "fixture JSON contains duplicate fields")
        value[key] = item
    return value


def json_bytes(body: bytes) -> dict[str, Any]:
    require(len(body) <= MAXIMUM_JSON, "fixture JSON exceeds its finite byte budget")
    value = json.loads(
        body,
        object_pairs_hook=duplicate_refusal,
        parse_constant=lambda _: reject("fixture JSON contains a nonfinite numeric constant"),
    )
    require(type(value) is dict, "fixture JSON must be an object")
    return value


def exact(value: Any, keys: set[str], message: str) -> dict[str, Any]:
    require(type(value) is dict and set(value) == keys, message)
    return value


def path_input(value: object, *, root: Path = ROOT, directory: bool = False) -> Path:
    """Refuse lexically before accessing a filesystem or runtime (INV-019)."""
    if not isinstance(value, str):
        reject("fixture paths must be absolute without traversal")
    require(
        isinstance(value, str)
        and value.startswith("/")
        and not any(part in {".", ".."} for part in value.split("/")),
        "fixture paths must be absolute without traversal",
    )
    path = Path(value)
    base = root / ".scratch"
    require(
        path.is_relative_to(base) and path != base,
        "functional fixture inputs must be repository .scratch descendants",
    )
    current = root
    for part in ("", *path.relative_to(root).parts):
        if part:
            current /= part
        facts = current.lstat()
        leaf = current == path
        require(
            facts.st_uid in {0, os.getuid()} and not facts.st_mode & 0o022,
            "functional fixture ancestors must be protected root/current-user owned",
        )
        require(
            stat.S_ISREG(facts.st_mode) if leaf and not directory else stat.S_ISDIR(facts.st_mode),
            "functional fixture input contains a symlink or unsupported file kind",
        )
        if current == base:
            require(
                facts.st_uid == os.getuid() and not facts.st_mode & 0o077,
                "functional .scratch must be private and current-user owned",
            )
        if leaf and not directory:
            require(facts.st_nlink == 1, "functional fixture file must have one hard link")
    return path


def bounded(path: Path, maximum: int = MAXIMUM_JSON) -> bytes:
    facts = path.lstat()
    require(
        stat.S_ISREG(facts.st_mode) and facts.st_size <= maximum,
        "functional fixture file is not a bounded ordinary file",
    )
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
    expected = tuple(getattr(facts, key) for key in fields)
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK)
    with os.fdopen(descriptor, "rb") as stream:
        opened = os.fstat(stream.fileno())
        require(
            tuple(getattr(opened, key) for key in fields) == expected,
            "functional fixture leaf changed before its protected read",
        )
        body = stream.read(maximum + 1)
        after_descriptor = os.fstat(stream.fileno())
        require(
            tuple(getattr(after_descriptor, key) for key in fields) == expected,
            "functional fixture descriptor changed while read",
        )
    require(len(body) <= maximum, "functional fixture file grew beyond its bound")
    after = path.lstat()
    require(
        tuple(getattr(after, key) for key in fields) == expected,
        "functional fixture input changed while read",
    )
    return body


def digest_file(path: Path, expected: object, maximum: int = MAXIMUM_JSON) -> str:
    require(
        isinstance(expected, str) and SHA256.fullmatch(expected),
        "functional fixture digest must be a lowercase SHA256",
    )
    observed = hashlib.sha256(bounded(path, maximum)).hexdigest()
    require(observed == expected, "functional fixture input digest differs")
    return observed


def file_record(value: object, *, root: Path = ROOT, maximum: int = MAXIMUM_JSON) -> Path:
    item = exact(value, {"path", "sha256"}, "fixture file identity is malformed")
    path = path_input(item["path"], root=root)
    digest_file(path, item["sha256"], maximum)
    return path


def local_backing(path: Path, mountinfo: str | None = None) -> None:
    """Only mount metadata is read; never traverse archive or production paths."""
    if mountinfo is None:
        with Path("/proc/self/mountinfo").open("rb") as stream:
            body = stream.read(MAXIMUM_JSON + 1)
        require(len(body) <= MAXIMUM_JSON, "mount metadata exceeds its finite byte budget")
        mountinfo = body.decode()
    candidates = []
    for line in mountinfo.splitlines():
        left, separator, right = line.partition(" - ")
        fields, tail = left.split(), right.split()
        require(separator and len(fields) >= 6 and len(tail) >= 3, "mount metadata is malformed")  # noqa: PLR2004 - fixed kernel grammar
        point = Path(re.sub(r"\\([0-7]{3})", lambda match: chr(int(match[1], 8)), fields[4]))
        if path == point or point in path.parents:
            candidates.append((len(point.parts), tail[0]))
    deepest = max((depth for depth, _ in candidates), default=-1)
    require(
        candidates
        and all(
            kind in {"ext4", "xfs", "btrfs", "tmpfs", "overlay"}
            for depth, kind in candidates
            if depth == deepest
        ),
        "functional inputs are not proven to use an approved local filesystem",
    )


def current_release(manifest: dict[str, Any]) -> bool:
    return isinstance(manifest.get("installed"), dict) and "release" in manifest["installed"]


def native_principal(role: str, *, caddy_account: str | None = None) -> int:
    name = caddy_account if role == "caddy" else "hfcache"
    if not isinstance(name, str):
        reject("fixed functional service account is malformed")
    require(
        re.fullmatch(r"[a-z_][a-z0-9_-]{0,31}", name),
        "fixed functional service account is malformed",
    )
    account = pwd.getpwnam(name)
    require(
        account.pw_name == name
        and type(account.pw_uid) is int
        and account.pw_uid > 0
        and account.pw_uid == account.pw_gid,
        "fixed functional service principal is unsupported",
    )
    return account.pw_uid


def application_index(manifest: dict[str, Any]) -> tuple[Path, dict[str, Any]]:
    path = file_record(manifest["installed"]["release"], root=ROOT)
    index = json_bytes(bounded(path))
    require(
        canonical(index) == bounded(path) and index.get("kind") == "hfcache_web_release",
        "original application index changed",
    )
    return path.parent, index


def container_principal(manifest: dict[str, Any], role: str) -> int:
    release, index = application_index(manifest)
    name = "packaging/containers/Containerfile" + (".caddy" if role == "caddy" else "")
    path = path_input(str(release / "source" / name), root=ROOT)
    digest_file(path, index["source_files"][name])
    users = re.findall(r"^USER ([0-9]+):([0-9]+)$", bounded(path).decode(), flags=re.MULTILINE)
    require(
        len(users) == 1 and int(users[0][0]) > 0 and users[0][0] == users[0][1],
        "indexed container role principal is unsupported",
    )
    return int(users[0][0])


def fixture_unit(manifest: dict[str, Any], generation: object, suffix: str) -> str:
    if not isinstance(generation, str):
        reject("functional unit generation is malformed")
    require(
        IDENTIFIER.fullmatch(generation),
        "functional unit generation is malformed",
    )
    fixture = str(uuid.UUID(manifest["fixture_id"]))
    require(fixture == manifest["fixture_id"], "functional unit fixture is malformed")
    return "web-functional-" + fixture.replace("-", "") + "-" + generation + "-" + suffix


def captured_tool(name: str, expected: object) -> dict[str, Any]:
    """Execute only captured, inventory-bound validation code, never candidate code."""
    require(
        name in {"web-release.py", "release-profile.py", "container-service.py"},
        "unknown validation tool",
    )
    path = ROOT / "scripts" / name
    body = bounded(path)
    require(hashlib.sha256(body).hexdigest() == expected, "validation tool source differs")
    namespace: dict[str, Any] = {"__name__": "functional_validation", "__file__": str(path)}
    exec(compile(body, str(path), "exec"), namespace)  # noqa: S102 - captured fixed inventory-bound validator
    return namespace


def source_identity(value: object, *, root: Path = ROOT, legacy: bool = True) -> dict[str, Any]:
    item = exact(
        value,
        {"parent_commit", "snapshot_sha256", "label", "input_manifest"},
        "functional source identity is malformed",
    )
    require(
        isinstance(item["label"], str)
        and (
            item["label"] == "WEB-005, this commit"
            if legacy
            else item["label"] != "WEB-005, this commit"
            and re.fullmatch(r"WEB-[0-9]{3}, this commit", item["label"]) is not None
        )
        and isinstance(item["parent_commit"], str)
        and COMMIT.fullmatch(item["parent_commit"]),
        "functional source provenance is unsupported",
    )
    inventory_path = file_record(item["input_manifest"], root=root)
    inventory = json_bytes(bounded(inventory_path))
    files = inventory.get("files")
    if not isinstance(files, dict) or not 0 < len(files) <= MAXIMUM_SOURCE_FILES:
        reject("functional source inventory is empty or exceeds its bound")
    for name, expected in files.items():
        require(
            isinstance(name, str)
            and not name.startswith("/")
            and all(part not in {"", ".", ".."} for part in name.split("/")),
            "functional source inventory contains an unsafe name",
        )
        path = root / name
        current = root
        for part in Path(name).parts:
            current /= part
            facts = current.lstat()
            require(
                stat.S_ISREG(facts.st_mode) if current == path else stat.S_ISDIR(facts.st_mode),
                "functional source inventory contains an unsafe file",
            )
            require(
                facts.st_uid in {0, os.getuid()} and not facts.st_mode & 0o022,
                "functional source inventory is not protected",
            )
        digest_file(path, expected, MAXIMUM_MEMBER_BYTES)
    observed = hashlib.sha256(
        json.dumps(files, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    require(observed == item["snapshot_sha256"], "functional source snapshot differs")
    if not legacy:
        require(
            {
                "scripts/check-web-functional.py",
                "scripts/web-release.py",
                "scripts/release-profile.py",
                "web/test/functional-api/driver.mjs",
                "web/test/auth-api/sandbox.mjs",
                "tests/fixtures/web-acceptance/requirements.json",
                "tests/fixtures/web-acceptance/coverage-groups.json",
            }
            <= files.keys(),
            "functional tooling inventory is incomplete",
        )
    return files


def native_path(
    value: object, *, directory: bool = False, anchor: Path = Path("/"), owner: int = 0
) -> Path:
    """Read-only fixed-prefix exception; writable fixture inputs never use this."""
    if not isinstance(value, str):
        reject("native installed path is unsafe")
    require(
        value.startswith("/") and not any(part in {".", ".."} for part in value.split("/")),
        "native installed path is unsafe",
    )
    path = Path(value)
    require(path.is_relative_to(NATIVE_PREFIX), "native installed path escaped its fixed prefix")
    local_backing(path)
    current = anchor
    require(path.is_relative_to(anchor), "native installed path escaped its root")
    for part in ("", *path.relative_to(anchor).parts):
        if part:
            current /= part
        facts = current.lstat()
        leaf = current == path
        require(
            facts.st_uid == owner and not facts.st_mode & 0o022,
            "native installed ancestry is not protected root-owned storage",
        )
        require(
            stat.S_ISREG(facts.st_mode) if leaf and not directory else stat.S_ISDIR(facts.st_mode),
            "native installed path contains a link or unsupported file kind",
        )
        require(not leaf or directory or facts.st_nlink == 1, "native installed file is linked")
    return path


def native_package(
    value: object, index: dict[str, Any], files: dict[str, str], verifier: dict[str, Any]
) -> Path:
    native_path(str(NATIVE_PREFIX), directory=True)
    selector = NATIVE_PREFIX / "current"
    before = selector.lstat()
    require(
        stat.S_ISLNK(before.st_mode) and before.st_uid == NATIVE_OWNER and before.st_nlink == 1,
        "native current selector is not a protected link",
    )
    selected = os.readlink(selector)  # noqa: PTH115 - raw selector spelling is authority
    require(selected == "releases/" + index["version"], "native current selects another release")
    target = native_path(str(NATIVE_PREFIX / selected), directory=True)
    expected_index = hashlib.sha256(canonical(index)).hexdigest()
    digest_file(native_path(str(target / "web-release.json")), expected_index)
    for name in index["source_files"]:
        if name in verifier["SHIPPED_FILES"] or Path(name).parts[0] in verifier["SHIPPED_TREES"]:
            native_path(str(target / name))
    for name in index["files"]:
        if name.startswith(("ui/", "host-helper/")):
            native_path(str(target / name))
    classifier = captured_tool("release-profile.py", files.get("scripts/release-profile.py"))
    require(
        classifier["native_selection"](NATIVE_PREFIX) == target,
        "selected installed native layout differs",
    )
    verifier["verify_shipped_source"](target, index["source_files"])
    pin = bounded(native_path(str(target / ".python-version"))).decode().strip()
    require(re.fullmatch(r"3\.[0-9]+(?:\.[0-9]+)?", pin), "native Python pin is unsupported")
    expected = (
        target / ".venv/lib" / ("python" + ".".join(pin.split(".")[:2])) / "site-packages/hfcache"
    )
    require(value == str(expected), "installed package is not the selected native package")
    package = native_path(value, directory=True)
    after = selector.lstat()
    require(
        all(
            getattr(before, field) == getattr(after, field)
            for field in ("st_dev", "st_ino", "st_uid", "st_nlink", "st_mtime_ns", "st_ctime_ns")
        )
        and os.readlink(selector) == selected,  # noqa: PTH115 - retain raw spelling
        "native current selector changed during validation",
    )
    return package


def application_release(
    item: dict[str, Any], files: dict[str, str], *, root: Path = ROOT
) -> tuple[dict[str, Any], dict[str, Any]]:
    release_index = file_record(item["release"], root=root)
    require(release_index.name == "web-release.json", "explicit application release index required")
    release = release_index.parent
    source = path_input(str(release / "source"), root=root, directory=True)
    verifier = captured_tool("web-release.py", files.get("scripts/web-release.py"))
    index = verifier["verify_native"](release, item["release"]["sha256"], source)

    def application_input(name: str) -> bool:
        return (
            name.startswith(("src/", "packaging/"))
            or (name.startswith("web/") and not name.startswith("web/test/"))
            or name
            in {".python-version", "pyproject.toml", "uv.lock", *verifier["HELPER"].values()}
        )

    runtime_inputs = {
        name: expected
        for name, expected in index["source_files"].items()
        if application_input(name)
    }
    require(
        runtime_inputs
        and {name: expected for name, expected in files.items() if application_input(name)}
        == runtime_inputs,
        "tooling checkout differs from original application inputs",
    )
    wheel_name = "wheels/hfcache-" + index["version"] + "-py3-none-any.whl"
    require(
        item["wheel"]["sha256"] == index["files"][wheel_name],
        "functional wheel is not the original application release",
    )
    return index, verifier


def rootless_tooling_package(
    item: dict[str, Any], index: dict[str, Any], *, root: Path = ROOT
) -> Path:
    """Verify only an immutable same-wheel SDK; live actor images are proved separately."""
    tooling = exact(
        item["tooling"], {"prefix", "python"}, "rootless SDK tooling identity is incomplete"
    )
    prefix = native_path(tooling["prefix"], directory=True)
    require(
        prefix.is_relative_to(NATIVE_PREFIX / "functional-sdk")
        and prefix != NATIVE_PREFIX / "functional-sdk",
        "rootless SDK must use its explicit immutable tooling prefix, never selected actor layout",
    )
    interpreter = exact(
        tooling["python"], {"path", "sha256"}, "rootless SDK interpreter identity is incomplete"
    )
    binary = native_path(interpreter["path"])
    digest_file(binary, interpreter["sha256"], MAXIMUM_TOOL_BYTES)
    require(
        Path(sys.executable).resolve() == binary and Path(sys.prefix) == prefix,
        "functional SDK process is not its pinned immutable interpreter and prefix",
    )
    pin = index["source_files"].get(".python-version")
    require(isinstance(pin, str), "indexed interpreter pin is missing")
    # The canonical application source supplies the Python version; the running
    # tooling interpreter remains a separately pinned artifact, never actor evidence.
    release = file_record(item["release"], root=root).parent
    version_file = path_input(str(release / "source/.python-version"), root=root)
    digest_file(version_file, pin)
    version = bounded(version_file).decode().strip()
    require(
        re.fullmatch(r"3\.[0-9]+(?:\.[0-9]+)?", version)
        and tuple(map(int, version.split("."))) == sys.version_info[: len(version.split("."))],
        "rootless SDK interpreter differs from the indexed Python version",
    )
    expected = (
        prefix / "lib" / ("python" + ".".join(version.split(".")[:2])) / "site-packages/hfcache"
    )
    require(
        item["package_root"] == str(expected), "rootless SDK package escaped its tooling prefix"
    )
    return native_path(item["package_root"], directory=True)


def installed_identity(
    value: object, files: dict[str, str], *, root: Path = ROOT, profile: str = "all"
) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        reject("functional installed authority is malformed")
    modern = "release" in value
    rootless_sdk = modern and profile == "rootless"
    item = exact(
        value,
        {"wheel", "package_root"}
        | ({"release"} if modern else set())
        | ({"tooling"} if rootless_sdk else set()),
        "functional installed authority is malformed",
    )
    index, verifier = application_release(item, files, root=root) if modern else (None, None)
    wheel = file_record(item["wheel"], root=root, maximum=MAXIMUM_ASSET_BYTES)
    installed = (
        rootless_tooling_package(item, index, root=root)
        if rootless_sdk and index is not None
        else native_package(item["package_root"], index, files, verifier)
        if index is not None and verifier is not None
        else path_input(item["package_root"], root=root, directory=True)
    )
    require(
        installed.name == "hfcache", "installed package root must be the actual hfcache package"
    )
    regular = {}
    directories = set()
    with zipfile.ZipFile(wheel) as archive:
        members = archive.infolist()
        require(len(members) <= MAXIMUM_SOURCE_FILES, "functional wheel member budget exceeded")
        seen = set()
        for member in members:
            require(member.filename not in seen, "functional wheel contains duplicate members")
            seen.add(member.filename)
            if not member.filename.startswith("hfcache/"):
                continue
            name = member.filename.removeprefix("hfcache/")
            mode = member.external_attr >> 16
            require(
                not member.flag_bits & 1 and member.file_size <= MAXIMUM_MEMBER_BYTES,
                "functional wheel contains an encrypted or oversized member",
            )
            if member.is_dir():
                require(
                    member.file_size == 0 and stat.S_IFMT(mode) in {0, stat.S_IFDIR},
                    "functional wheel directory is malformed",
                )
                directories.add(member.filename)
                continue
            require(
                name
                and not name.startswith("/")
                and all(part not in {"", ".", ".."} for part in name.split("/"))
                and stat.S_IFMT(mode) in {0, stat.S_IFREG},
                "functional wheel contains an unsafe package member",
            )
            content = archive.read(member)
            expected = hashlib.sha256(content).hexdigest()
            require(
                (index["source_files"] if index is not None else files).get("src/hfcache/" + name)
                == expected,
                "functional wheel differs from the frozen source package",
            )
            target = (
                native_path(str(installed / name))
                if index is not None
                else path_input(str(installed / name), root=root)
            )
            digest_file(target, expected, MAXIMUM_MEMBER_BYTES)
            regular[name] = expected
    expected_directories = {"hfcache/"}
    for name in regular:
        expected_directories.update(
            "hfcache/" + str(parent) + "/" for parent in Path(name).parents if str(parent) != "."
        )
    require(
        regular and directories <= expected_directories,
        "functional wheel has unexplained empty directories",
    )
    observed = set()
    for number, path in enumerate(installed.rglob("*"), start=1):
        require(number <= MAXIMUM_ASSET_ENTRIES, "installed package entry bound exceeded")
        require(not path.is_symlink(), "installed package contains a symlink")
        if "__pycache__" in path.parts:
            continue
        if index is not None:
            native_path(str(path), directory=path.is_dir())
        if path.is_file():
            observed.add(path.relative_to(installed).as_posix())
    require(observed == set(regular), "installed package differs from its complete wheel inventory")
    if index is not None and verifier is not None:
        require(
            (
                rootless_tooling_package(item, index, root=root)
                if rootless_sdk
                else native_package(item["package_root"], index, files, verifier)
            )
            == installed,
            "installed SDK tooling or native selection changed",
        )
    return index


def asset_identity(value: object, *, root: Path = ROOT) -> dict[str, Any]:
    item = exact(value, {"root", "manifest_sha256"}, "functional asset identity is malformed")
    assets = path_input(item["root"], root=root, directory=True)
    manifest_path = path_input(str(assets / "manifest.json"), root=root)
    digest_file(manifest_path, item["manifest_sha256"])
    body = bounded(manifest_path)
    manifest = json_bytes(body)
    require(
        canonical(manifest) == body
        and manifest.get("kind") == "hfcache_web_assets"
        and type(manifest.get("schema_version")) is int
        and manifest["schema_version"] == 1,
        "functional assets lack their canonical independent schema",
    )
    members = manifest.get("members")
    if not isinstance(members, list) or not 0 < len(members) <= MAXIMUM_SOURCE_FILES:
        reject("functional asset member budget is invalid")
    names = []
    total = 0
    for record in members:
        member = exact(
            record, {"path", "bytes", "sha256", "mime"}, "functional asset record is malformed"
        )
        name = member["path"]
        require(
            isinstance(name, str)
            and len(name) <= MAXIMUM_PATH_BYTES
            and 1 <= len(name.split("/")) <= MAXIMUM_PATH_DEPTH
            and all(
                1 <= len(part) <= MAXIMUM_COMPONENT_BYTES
                and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", part)
                and part not in {".", ".."}
                for part in name.split("/")
            ),
            "functional assets contain an unsafe member path",
        )
        require(
            type(member["bytes"]) is int and 0 <= member["bytes"] <= MAXIMUM_MEMBER_BYTES,
            "functional asset size is outside its bound",
        )
        expected_mime = (
            "text/plain" if name == "THIRD_PARTY_NOTICES.txt" else MIME.get(Path(name).suffix)
        )
        require(
            member["mime"] == expected_mime and expected_mime is not None,
            "functional asset MIME differs from its fixed path",
        )
        require(
            name in {"index.html", "licenses.json", "THIRD_PARTY_NOTICES.txt"}
            or name.startswith("assets/"),
            "functional asset shadows a reserved UI route",
        )
        target = path_input(str(assets / name), root=root)
        require(target.stat().st_size == member["bytes"], "functional asset byte count differs")
        digest_file(target, member["sha256"], MAXIMUM_MEMBER_BYTES)
        total += member["bytes"]
        require(total <= MAXIMUM_ASSET_BYTES, "functional asset total byte budget exceeded")
        names.append(name)
    require(
        names == sorted(set(names))
        and {"index.html", "licenses.json", "THIRD_PARTY_NOTICES.txt"} <= set(names),
        "functional asset inventory lacks exact sorted required members",
    )
    actual = set()
    for number, path in enumerate(assets.rglob("*"), 1):
        require(
            number <= MAXIMUM_ASSET_ENTRIES and not path.is_symlink(),
            "functional asset tree is unsafe or oversized",
        )
        if path.is_file():
            actual.add(path.relative_to(assets).as_posix())
        else:
            require(path.is_dir(), "functional asset tree contains a special entry")
    require(actual == {*names, "manifest.json"}, "functional asset tree has unindexed content")
    return manifest


def origin(value: object) -> str:
    if not isinstance(value, str):
        reject("functional origin must be an explicit HTTPS loopback origin")
    parsed = urlsplit(value)
    require(
        parsed.scheme == "https"
        and parsed.hostname == "127.0.0.1"
        and parsed.port
        and value == f"https://127.0.0.1:{parsed.port}",
        "functional origin must be an explicit HTTPS loopback origin",
    )
    return value


def validate_manifest(
    value: str, *, root: Path = ROOT, profile: str = "all", common_only: bool = False
) -> dict[str, Any]:
    path = path_input(value, root=root)
    local_backing(root)
    manifest = json_bytes(bounded(path))
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
            "mcp_arguments",
        },
        "functional manifest has unsupported fields",
    )
    require(
        type(manifest["schema_version"]) is int
        and manifest["schema_version"] == 1
        and manifest["kind"] == "hfcache_web_functional_fixture",
        "functional manifest schema is unsupported",
    )
    fixture = manifest["fixture_id"]
    require(
        isinstance(fixture, str) and str(uuid.UUID(fixture)) == fixture,
        "functional fixture ID must be a canonical UUID",
    )
    modern = current_release(manifest)
    if not common_only:
        marker = json_bytes(bounded(file_record(manifest["marker"], root=root)))
        guest = exact(
            manifest["guest"], {"identity", "boot_id"}, "functional guest identity is malformed"
        )
        require(
            isinstance(guest["identity"], str)
            and (
                re.fullmatch(r"[a-z][a-z0-9-]{0,127}", guest["identity"]) is not None
                if modern
                else guest["identity"] == "web-004-83a4380d0c82465fa225c00bba53359c"
            )
            and isinstance(guest["boot_id"], str)
            and str(uuid.UUID(guest["boot_id"])) == guest["boot_id"],
            "functional runtime is not the explicitly owned disposable guest",
        )
        require(
            marker
            == {
                "schema_version": 1,
                "fixture_id": fixture,
                "repository_root": str(root),
                "guest": guest,
            },
            "functional marker does not bind this repository and guest",
        )
        if modern:
            require(
                Path("/proc/sys/kernel/random/boot_id").read_text().strip() == guest["boot_id"],
                "functional installed reads require the explicitly owned guest boot",
            )
    files = source_identity(manifest["source"], root=root, legacy=not modern)
    if common_only:
        require(modern, "offline joining requires original canonical release artifacts")
        application, _ = application_release(manifest["installed"], files, root=root)
        file_record(manifest["installed"]["wheel"], root=root, maximum=MAXIMUM_ASSET_BYTES)
    else:
        application = installed_identity(manifest["installed"], files, root=root, profile=profile)
    assets = asset_identity(manifest["assets"], root=root)
    if application is not None:
        require(
            manifest["assets"]["manifest_sha256"] == application["ui_manifest_sha256"]
            and assets["build"]["source_commit"] == application["source_commit"]
            and assets["build"]["application_version"] == application["version"]
            and assets["build"]["source_dirty"] is False,
            "functional UI is not the original clean application release",
        )
    browser = exact(
        manifest["browser"],
        {
            "launcher",
            "ca",
            "playwright_version",
            "node_version",
            "toolchain_inventory",
            "playwright_module",
            "node_binary",
            "trusted_image_sha256",
            "untrusted_image_sha256",
            "seccomp",
        },
        "functional browser binding is malformed",
    )
    for key in (
        "launcher",
        "ca",
        "toolchain_inventory",
        "playwright_module",
        "node_binary",
        "seccomp",
    ):
        file_record(browser[key], root=root, maximum=MAXIMUM_TOOL_BYTES)
    for key in ("trusted_image_sha256", "untrusted_image_sha256"):
        require(
            isinstance(browser[key], str) and SHA256.fullmatch(browser[key]),
            "functional browser image digest is invalid",
        )
    require(
        browser["trusted_image_sha256"] != browser["untrusted_image_sha256"],
        "functional untrusted browser binding must omit the test CA",
    )
    require(
        browser["playwright_version"] == "1.64.1" and browser["node_version"] == "24.18.1",
        "functional browser toolchain is not the pinned closure",
    )
    profiles = exact(
        manifest["profiles"],
        DEPLOYMENTS,
        "functional profiles must include application/native/rootless",
    )
    for deployment in () if common_only else selected_profiles(profile):
        binding = profiles[deployment]
        current_rootless = modern and deployment == "rootless"
        exact(
            binding,
            {
                "launcher",
                "origin",
                "caddy_config",
                "caddy_binary_sha256",
                "api_image_sha256",
                "caddy_image_sha256",
                "worker_image_sha256",
            }
            | (
                {"network", "storage_driver"}
                if current_rootless
                else {"caddy_account"}
                if modern
                else set()
            ),
            "functional runtime binding is malformed",
        )
        file_record(binding["launcher"], root=root)
        file_record(binding["caddy_config"], root=root)
        origin(binding["origin"])
        require(
            isinstance(binding["caddy_binary_sha256"], str)
            and SHA256.fullmatch(binding["caddy_binary_sha256"]),
            "functional Caddy digest is invalid",
        )
        for key in ("api_image_sha256", "caddy_image_sha256", "worker_image_sha256"):
            require(
                binding[key] is None
                or (isinstance(binding[key], str) and SHA256.fullmatch(binding[key])),
                "functional role image digest is invalid",
            )
            require(
                deployment != "rootless" or binding[key] is not None,
                "rootless functional roles require exact installed image identities",
            )
        if current_rootless:
            network = exact(
                binding["network"],
                {"worker_policy", "stock_control"},
                "rootless network authority is incomplete",
            )
            for record in network.values():
                file_record(record, root=root)
            require(
                network["worker_policy"]["sha256"] == WORKER_POLICY_SHA256
                and network["worker_policy"]["path"] != network["stock_control"]["path"]
                and binding["storage_driver"] in {"overlay", "vfs"},
                "rootless policy, control or storage authority differs",
            )
        elif modern and deployment != "rootless":
            native_principal("caddy", caddy_account=binding["caddy_account"])
    require(
        type(manifest["mcp_arguments"]) is dict
        and set(manifest["mcp_arguments"]) == MCP_TOOLS
        and all(type(item) is dict for item in manifest["mcp_arguments"].values()),
        "functional MCP fixtures must name all fourteen real tool calls",
    )
    return manifest


def prepare_workspace(value: str | None, *, root: Path = ROOT) -> Path:
    base = root / ".scratch"
    facts = base.lstat()
    require(
        stat.S_ISDIR(facts.st_mode) and facts.st_uid == os.getuid() and not facts.st_mode & 0o077,
        "functional .scratch must be private before creating state",
    )
    local_backing(base)
    if value is None:
        return Path(tempfile.mkdtemp(prefix="web-functional-", dir=base))
    require(
        isinstance(value, str) and value.startswith("/"), "functional workspace must be absolute"
    )
    path = Path(value)
    require(
        path.parent == base and path.name.startswith("web-functional-") and not path.exists(),
        "functional workspace must be a fresh direct owned .scratch descendant",
    )
    path.mkdir(mode=0o700)
    return path


def safe_environment() -> dict[str, str]:
    return {"PATH": os.defpath, "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "PYTHONNOUSERSITE": "1"}


async def command(argv: list[str], *, body: bytes | None, timeout: float) -> dict[str, Any]:
    """No shell, ambient credentials, unsafe output persistence or unbounded child."""
    child = await asyncio.create_subprocess_exec(
        *argv,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
        env=safe_environment(),
    )

    async def exchange() -> bytes:
        sink, source = child.stdin, child.stdout
        if sink is None or source is None:
            reject("owned functional launcher pipes are unavailable")
        if body is not None:
            require(
                len(body) <= MAXIMUM_COMMAND_BYTES,
                "owned functional launcher input exceeded its bound",
            )
            sink.write(body)
            await sink.drain()
        sink.close()
        chunks = []
        size = 0
        while chunk := await source.read(65536):
            size += len(chunk)
            require(
                size <= MAXIMUM_COMMAND_BYTES, "owned functional launcher output exceeded its bound"
            )
            chunks.append(chunk)
        await child.wait()
        return b"".join(chunks)

    try:
        async with asyncio.timeout(timeout):
            output = await exchange()
    except BaseException:

        async def drain() -> None:
            if child.stdin is not None:
                child.stdin.close()
            if child.returncode is None:
                child.terminate()

            async def discard() -> None:
                size = 0
                if child.stdout is not None:
                    while chunk := await child.stdout.read(65536):
                        size += len(chunk)
                        require(
                            size <= MAXIMUM_COMMAND_BYTES,
                            "owned launcher pipe drain exceeded its bound",
                        )

            try:
                await asyncio.wait_for(asyncio.gather(child.wait(), discard()), 45)
            except TimeoutError:
                if child.returncode is None:
                    child.kill()
                await asyncio.wait_for(asyncio.gather(child.wait(), discard()), 5)

        await protected_cleanup(drain())
        raise
    require(child.returncode == 0, "owned functional launcher exited unsuccessfully")
    return json_bytes(output)


async def protected_cleanup(operation: Any) -> tuple[Any, bool]:
    """Repeated request cancellation cannot strand exact owned resources."""
    task = asyncio.create_task(operation)
    cancelled = False
    while True:
        try:
            return await asyncio.shield(task), cancelled
        except asyncio.CancelledError:
            if task.done():
                raise
            cancelled = True


async def python_mcp_compatibility(
    manifest: dict[str, Any], runtime: dict[str, Any], tokens: dict[str, str]
) -> dict[str, Any]:
    """Use the actual installed SDK against real Caddy TLS, never ASGI transport."""
    import httpx2
    from fastmcp import Client
    from fastmcp.client.transports import StreamableHttpTransport

    from hfcache.client_models import ClientRead

    context = ssl.create_default_context(cafile=manifest["browser"]["ca"]["path"])

    def factory(headers=None, timeout=None, auth=None, **options):
        options.pop("follow_redirects", None)
        headers = dict(headers or {})
        headers["User-Agent"] = "hfcache-functional-python-sdk"
        return httpx2.AsyncClient(
            headers=headers,
            timeout=timeout or httpx2.Timeout(10),
            auth=auth,
            trust_env=False,
            verify=context,
            follow_redirects=False,
            **options,
        )

    endpoint = runtime["origin"] + runtime["prefix"] + "/mcp/"
    transport = StreamableHttpTransport(
        endpoint, auth=tokens["mcp_reader"], httpx_client_factory=factory
    )
    tools = {}
    async with Client(transport, timeout=10, init_timeout=10) as client:
        require(
            {item.name for item in await client.list_tools()} == MCP_TOOLS,
            "installed Python MCP SDK observed a changed fourteen-tool allowlist",
        )
        require(
            await client.list_resources() == [] and await client.list_prompts() == [],
            "installed Python MCP SDK observed an unexpected resource or prompt surface",
        )
        for name in sorted(MCP_TOOLS):
            result = await client.call_tool(
                name, runtime["mcp_arguments"][name], raise_on_error=False
            )
            require(
                not result.is_error, "installed Python MCP SDK tool returned a protocol failure"
            )
            wire = ClientRead.model_validate(result.structured_content)
            require(
                wire.envelope.outcome in {"success", "success_with_warnings"}
                and wire.envelope.exit_code == 0,
                "installed Python MCP SDK tool did not succeed",
            )
            tools[name] = {
                "passed": True,
                "request_id": wire.request_id,
                "outcome": wire.envelope.outcome,
            }
    return {
        "schema_version": 1,
        "origin": runtime["origin"],
        "prefix": runtime["prefix"],
        "transport": "real_caddy_tls",
        "tools": tools,
        "versions": {
            name: importlib.metadata.version(name) for name in ("fastmcp", "mcp", "httpx2")
        },
    }


def role_process(
    value: object, role: str, profile: str, *, expected_uid: int | None = None
) -> dict[str, Any]:
    """Inspect retained kernel facts independently of the launcher's summary flags."""
    item = exact(
        value,
        {
            "schema_version",
            "role",
            "identity",
            "status",
            "namespaces",
            "cgroup",
            "mountinfo",
            "uid_map",
            "gid_map",
            "selinux_context",
            "executable",
            "argv_sha256",
            "argv_count",
            "fixed_argv_matched",
        },
        "functional role process inspection is incomplete",
    )
    identity = exact(
        item["identity"],
        {"pid", "parent_pid", "state", "start_ticks"},
        "functional role process identity is incomplete",
    )
    status = item["status"]
    require(
        type(identity["pid"]) is int
        and identity["pid"] > 1
        and positive_integer(identity["parent_pid"], zero=True)
        and isinstance(identity["start_ticks"], str)
        and re.fullmatch(r"[0-9]+", identity["start_ticks"])
        and identity["state"] in set("RSDTWtIKP")
        and type(item["schema_version"]) is int
        and item["schema_version"] == 1
        and item["role"] == role
        and type(status) is dict
        and set(status)
        == {"Pid", "PPid", "Uid", "Gid", "NSpid", "CapEff", "CapBnd", "NoNewPrivs", "Seccomp"}
        and type(status.get("Pid")) is int
        and type(status.get("PPid")) is int
        and status.get("Pid") == identity["pid"]
        and status.get("PPid") == identity["parent_pid"]
        and type(status.get("Uid")) is list
        and len(status["Uid"]) == UID_FIELDS
        and all(type(uid) is int and uid > 0 for uid in status["Uid"])
        and len(set(status["Uid"])) == 1
        and status.get("Gid") == status["Uid"]
        and all(type(gid) is int for gid in status["Gid"])
        and status.get("CapEff") == status.get("CapBnd") == "0000000000000000"
        and type(status.get("NoNewPrivs")) is int
        and status.get("NoNewPrivs") == 1
        and type(status.get("Seccomp")) is int
        and status.get("Seccomp") == SECCOMP_FILTER
        and type(status.get("NSpid")) is list
        and status["NSpid"]
        and status["NSpid"][0] == identity["pid"]
        and all(type(pid) is int and pid > 0 for pid in status["NSpid"])
        and item["fixed_argv_matched"] is True
        and type(item["argv_count"]) is int
        and 0 < item["argv_count"] < MAXIMUM_ARGUMENTS
        and isinstance(item["argv_sha256"], str)
        and SHA256.fullmatch(item["argv_sha256"]),
        "functional role process privilege or exact invocation is unproved",
    )
    if profile != "rootless":
        require(
            status["Uid"]
            == [expected_uid if expected_uid is not None else 982 if role == "caddy" else 981] * 4,
            "native functional role uses an unexpected identity",
        )
    namespaces = exact(
        item["namespaces"],
        {"pid", "user", "mnt", "net", "ipc", "uts", "cgroup"},
        "functional role namespaces are incomplete",
    )
    require(
        all(
            isinstance(value, str) and re.fullmatch(name + r":\[[0-9]+\]", value)
            for name, value in namespaces.items()
        ),
        "functional namespace identity is invalid",
    )
    require(
        all(
            isinstance(item[key], str) and 0 < len(item[key].encode()) <= MAXIMUM_JSON
            for key in ("cgroup", "mountinfo", "uid_map", "gid_map", "selinux_context")
        )
        and "unconfined_t" not in item["selinux_context"],
        "functional role confinement metadata is missing or unconfined",
    )
    executable = exact(
        item["executable"],
        {"bytes", "sha256", "device", "inode"},
        "functional role executable identity is missing",
    )
    require(
        type(executable["bytes"]) is int
        and 0 < executable["bytes"] <= MAXIMUM_TOOL_BYTES
        and isinstance(executable["sha256"], str)
        and SHA256.fullmatch(executable["sha256"])
        and all(
            type(executable[key]) is int and executable[key] > 0 for key in ("device", "inode")
        ),
        "functional role executable identity is malformed",
    )
    return item


def helper_process(value: object) -> dict[str, Any]:
    """The fixed privileged helper is never an exception to online role checks."""
    item = exact(
        value,
        {
            "schema_version",
            "role",
            "identity",
            "status",
            "namespaces",
            "cgroup",
            "mountinfo",
            "uid_map",
            "gid_map",
            "selinux_context",
            "executable",
            "argv_sha256",
            "argv_count",
            "fixed_argv_matched",
            "expected_executable",
        },
        "actual helper process capture is incomplete",
    )
    identity = exact(
        item["identity"],
        {"pid", "parent_pid", "state", "start_ticks"},
        "actual helper process tuple is incomplete",
    )
    process_identity({key: identity[key] for key in ("pid", "start_ticks")})
    status = exact(
        item["status"],
        {
            "Pid",
            "PPid",
            "Uid",
            "Gid",
            "NSpid",
            "CapEff",
            "CapBnd",
            "NoNewPrivs",
            "Seccomp",
            "CapPrm",
            "CapInh",
            "CapAmb",
            "Seccomp_filters",
        },
        "actual helper status is incomplete",
    )
    require(
        item["schema_version"] == 1
        and type(item["schema_version"]) is int
        and item["role"] == "helper"
        and status["Pid"] == identity["pid"]
        and type(status["Pid"]) is int
        and status["PPid"] == identity["parent_pid"]
        and positive_integer(status["PPid"], zero=True)
        and identity["state"] in set("RSDTWtIKP")
        and type(status["NSpid"]) is list
        and status["NSpid"]
        and status["NSpid"][0] == identity["pid"]
        and all(positive_integer(pid) for pid in status["NSpid"])
        and status["Uid"] == status["Gid"] == [0] * UID_FIELDS
        and all(type(uid) is int for uid in status["Uid"] + status["Gid"])
        and status["CapEff"] == status["CapPrm"] == status["CapBnd"] == "00000000000000c0"
        and status["CapInh"] == status["CapAmb"] == "0000000000000000"
        and status["NoNewPrivs"] == 1
        and type(status["NoNewPrivs"]) is int
        and status["Seccomp"] == SECCOMP_FILTER
        and type(status["Seccomp"]) is int
        and positive_integer(status["Seccomp_filters"])
        and item["selinux_context"] == "system_u:system_r:hfcache_host_helper_t:s0"
        and item["cgroup"] == "0::/system.slice/hfcache-host-helper.service\n"
        and item["fixed_argv_matched"] is True
        and digest(item["argv_sha256"])
        and positive_integer(item["argv_count"])
        and item["argv_count"] < MAXIMUM_ARGUMENTS,
        "actual helper privilege, invocation or confinement differs",
    )
    namespaces = exact(
        item["namespaces"],
        {"pid", "user", "mnt", "net", "ipc", "uts", "cgroup"},
        "actual helper namespace inventory is incomplete",
    )
    require(
        all(
            type(value) is str and re.fullmatch(name + r":\[[0-9]+\]", value)
            for name, value in namespaces.items()
        )
        and all(
            type(item[key]) is str and 0 < len(item[key].encode()) <= MAXIMUM_JSON
            for key in ("mountinfo", "uid_map", "gid_map")
        ),
        "actual helper namespace or mount identity is malformed",
    )
    executable = exact(
        item["executable"],
        {"bytes", "sha256", "device", "inode"},
        "actual helper executable identity is incomplete",
    )
    require(
        executable == item["expected_executable"]
        and digest(executable["sha256"])
        and all(positive_integer(executable[key]) for key in ("bytes", "device", "inode")),
        "actual helper does not execute its protected fixed interpreter",
    )
    return item


def effective_mask_evidence(value: object, process: dict[str, Any]) -> None:
    """A hidden lower NFS row is valid only behind an identity-proven mask."""
    require(
        type(value) is list and len(CADDY_AUTHORITY_PATHS) <= len(value) <= MAXIMUM_THREADS,
        "effective Caddy authority mounts are incomplete",
    )
    paths = set()
    for row in value:
        item = exact(row, {"effective", "mask"}, "effective authority mount is malformed")
        effective, mask = item["effective"], item["mask"]
        for capture in (effective,) if mask is None else (effective, mask):
            exact(
                capture,
                {"pid", "path", "mount_id", "mountinfo", "stat"},
                "effective path lacks its held descriptor observation",
            )
            facts = exact(
                capture["stat"],
                {"device", "inode", "mode", "uid", "gid"},
                "effective path identity is incomplete",
            )
            require(
                positive_integer(capture["pid"])
                and positive_integer(capture["mount_id"])
                and type(capture["path"]) is str
                and capture["path"].startswith("/")
                and ".." not in Path(capture["path"]).parts
                and all(type(number) is int for number in facts.values())
                and positive_integer(facts["device"])
                and positive_integer(facts["inode"]),
                "effective path identity is invalid",
            )
            fields, separator, trailing = capture["mountinfo"].partition(" - ")
            columns, tail = fields.split(), trailing.split()
            require(
                separator
                and len(columns) >= MINIMUM_MOUNT_FIELDS
                and len(tail) >= MINIMUM_MOUNT_TRAILING_FIELDS
                and columns[0] == str(capture["mount_id"]),
                "effective mount ID and raw row differ",
            )
        require(
            effective["pid"] == process["identity"]["pid"]
            and effective["mountinfo"] in process["mountinfo"].splitlines()
            and effective["path"] not in paths,
            "effective authority path changed its actual process or raw mount row",
        )
        fields, _, trailing = effective["mountinfo"].partition(" - ")
        columns, tail = fields.split(), trailing.split()
        if mask is None:
            # An inherited local root filesystem is not a dedicated authority
            # bind. The separate origin-probe denial remains mandatory.
            require(
                columns[3] == "/"
                and columns[4] != effective["path"]
                and Path(columns[4]) in Path(effective["path"]).parents
                and tail[0] in {"ext4", "xfs", "tmpfs"},
                "Caddy has a real effective protected-source or network bind",
            )
            paths.add(effective["path"])
            continue
        require(
            mask["path"] in {"/run/systemd/inaccessible/dir", "/run/systemd/inaccessible/reg"}
            and effective["stat"] == mask["stat"]
            and mask["stat"]["uid"] == mask["stat"]["gid"] == 0
            and stat.S_IMODE(mask["stat"]["mode"]) == 0
            and (
                stat.S_ISDIR(mask["stat"]["mode"])
                if mask["path"].endswith("/dir")
                else stat.S_ISREG(mask["stat"]["mode"])
            )
            and "ro" in effective["mountinfo"].partition(" - ")[0].split()[5].split(",")
            and tail[0] not in {"nfs", "nfs4"},
            "Caddy authority is exposed or its inaccessible mask is unproved",
        )
        paths.add(effective["path"])
    require(
        paths >= CADDY_AUTHORITY_PATHS,
        "effective Caddy authority scope omits fixed protected paths",
    )


def installed_role_evidence(proofs: dict[str, Any], manifest: dict[str, Any]) -> None:
    """Join actual role captures to original selected artifacts, never acceptance labels."""
    _, index = application_index(manifest)
    require(
        proofs["network"].get("selinux_enforce") == "1",
        "raw installed SELinux enforcing observation is absent",
    )
    helper = proofs["helper"]
    process = helper_process(helper.get("process"))
    manager = helper.get("unit", {})
    require(
        manager.get("MainPID") == str(process["identity"]["pid"])
        and type(manager.get("InvocationID")) is str
        and IDENTIFIER.fullmatch(manager["InvocationID"])
        and manager.get("ControlGroup") == "/system.slice/hfcache-host-helper.service"
        and manager.get("NoNewPrivileges") == "yes",
        "actual helper manager identity differs",
    )
    bootstrap = exact(
        helper.get("bootstrap"),
        set(HELPER_BOOTSTRAP),
        "selected helper bootstrap capture is incomplete",
    )
    deployment = helper.get("deployment", {})
    require(
        deployment.get("release")
        == {"version": index["version"], "selector_target": "releases/" + index["version"]}
        and deployment.get("source", {}).get("parent_commit") == index["source_commit"]
        and deployment.get("source", {}).get("dirty") is False,
        "helper deployment selects another original release",
    )
    authority = exact(
        helper.get("authority"),
        {
            "deployment_sha256",
            "policy_deployment_sha256",
            "receipt_sha256",
            "kernel_policy_sha256",
            "receipt_kernel_policy_sha256",
            "cil_sha256",
            "receipt_cil_sha256",
            "key_parent",
        },
        "helper protected authority join is incomplete",
    )
    require(
        all(digest(authority[name]) for name in authority if name != "key_parent")
        and authority["deployment_sha256"] == authority["policy_deployment_sha256"]
        and authority["kernel_policy_sha256"] == authority["receipt_kernel_policy_sha256"]
        and authority["cil_sha256"]
        == authority["receipt_cil_sha256"]
        == index["files"]["host-helper/hfcache-host-helper.cil"]
        and deployment.get("selinux_installation_sha256") == authority["receipt_sha256"],
        "helper deployment, policy, loaded CIL or installation receipt changed",
    )
    parent = authority["key_parent"]
    require(
        type(parent) is dict
        and parent.get("st_uid") == parent.get("st_gid") == 0
        and stat.S_ISDIR(parent.get("st_mode", 0))
        and not parent["st_mode"] & 0o022
        and positive_integer(parent.get("st_dev"))
        and positive_integer(parent.get("st_ino")),
        "helper credential parent is not protected metadata",
    )
    for path, (name, binding, mode) in HELPER_BOOTSTRAP.items():
        row = exact(
            bootstrap[path],
            {"metadata", "sha256", "selected_sha256"},
            "helper bootstrap identity is incomplete",
        )
        facts = row["metadata"]
        require(
            row["sha256"]
            == row["selected_sha256"]
            == index["files"]["host-helper/" + name]
            == deployment["bindings"][binding]
            and facts.get("st_uid") == facts.get("st_gid") == 0
            and stat.S_ISREG(facts.get("st_mode", 0))
            and stat.S_IMODE(facts["st_mode"]) == mode
            and facts.get("st_nlink") == 1,
            "helper bootstrap changed selected bytes or protected metadata",
        )
    for role in ("api", "worker", "caddy"):
        proof = proofs[role]
        installation = exact(
            proof.get("installation"),
            {"release_index_sha256", "source_commit", "expected_executable", "package_root"},
            "actual role installation join is incomplete",
        )
        require(
            installation["release_index_sha256"] == manifest["installed"]["release"]["sha256"]
            and installation["source_commit"] == index["source_commit"]
            and installation["expected_executable"] == proof["process"]["executable"],
            "actual role executable differs from its selected installed input",
        )
        if role == "caddy":
            require(
                proof["process"]["executable"]["sha256"]
                == manifest["profiles"][proof["profile"]]["caddy_binary_sha256"]
                and installation["package_root"] is None,
                "live Caddy binary differs from its canonical binary pin",
            )
        else:
            expected = (
                "/opt/hfcache/.venv/lib/python3.14/site-packages/hfcache"
                if proof["profile"] == "rootless"
                else manifest["installed"]["package_root"]
            )
            require(
                installation["package_root"] == expected,
                "actual role imported another installed package",
            )
    if helper["profile"] != "rootless":
        effective_mask_evidence(proofs["caddy"].get("authority_mounts"), proofs["caddy"]["process"])
    else:
        selected_image_evidence(proofs, manifest, index)


def selected_image_evidence(
    proofs: dict[str, Any], manifest: dict[str, Any], index: dict[str, Any]
) -> None:
    """Join live images to selected canonical indexes and original constructor records."""
    artifacts = exact(
        proofs["network"].get("selected_artifacts"),
        {"release", "stage_index", "api_build", "caddy_build"},
        "selected container artifact capture is incomplete",
    )
    selected = NATIVE_PREFIX / "releases" / index["version"]

    def selected_record(name: str, record: object) -> dict[str, Any]:
        item = exact(record, {"path", "sha256"}, "selected artifact record is malformed")
        require(item["path"] == str(selected / name), "container artifact is not selected")
        path = native_path(item["path"])
        digest_file(path, item["sha256"])
        return json_bytes(bounded(path))

    release = selected_record("container-release.json", artifacts["release"])
    stage = selected_record("artifact-index.json", artifacts["stage_index"])
    require(
        release.get("source_commit") == index["source_commit"]
        and release.get("version") == index["version"]
        and release.get("wheel_sha256")
        == index["files"]["wheels/hfcache-" + index["version"] + "-py3-none-any.whl"]
        and release.get("files", {}).get("web-release.json")
        == manifest["installed"]["release"]["sha256"]
        and release["files"].get("ui/manifest.json") == index["ui_manifest_sha256"]
        and stage.get("schema_version") == 1
        and type(stage.get("files")) is dict,
        "selected container index differs from the original application release",
    )
    for name, expected in release["files"].items():
        require(
            type(name) is str
            and not name.startswith("/")
            and all(part not in {"", ".", ".."} for part in name.split("/"))
            and stage["files"].get(name) == expected,
            "selected container stage omitted or changed an indexed artifact",
        )
        digest_file(native_path(str(selected / name)), expected, MAXIMUM_MEMBER_BYTES)
    api = json_bytes(bounded(file_record(artifacts["api_build"], root=ROOT)))
    caddy = json_bytes(bounded(file_record(artifacts["caddy_build"], root=ROOT)))
    require(
        api.get("source_commit") == index["source_commit"]
        and api.get("source_dirty") is False
        and api.get("version") == index["version"]
        and api.get("wheel_sha256") == release["wheel_sha256"]
        and api.get("web_manifest_sha256") == index["ui_manifest_sha256"]
        and api.get("containerfile_sha256")
        == release["files"]["packaging/containers/Containerfile"]
        and api.get("image_id") == release.get("app_image")
        and caddy.get("image_id") == release.get("caddy_image")
        and caddy.get("containerfile_sha256")
        == release["files"]["packaging/containers/Containerfile.caddy"]
        and caddy.get("caddy_binary_sha256")
        == manifest["profiles"]["rootless"]["caddy_binary_sha256"],
        "live image authority does not join canonical build and selected artifact bytes",
    )
    for role in ("api", "worker", "caddy"):
        container = proofs[role]["container"]
        image = release["caddy_image" if role == "caddy" else "app_image"]
        require(
            image == "sha256:" + container["image_sha256"],
            "actual role image is not the selected canonical image",
        )
        projection = exact(
            proofs[role].get("mount_projection"),
            {"source_sha256", "binds"},
            "canonical rootless bind projection is missing",
        )
        constructor = captured_tool(
            "container-service.py", index["source_files"].get("scripts/container-service.py")
        )
        constructor["PROFILE_DIRECTORY"] = selected / "rendered"
        runtime = json_bytes(bounded(native_path(str(selected / "rendered/runtime.json"))))
        argv = constructor["command"](
            runtime, role, invocation_id="", preserve_archive_lock=role in {"api", "worker"}
        )
        expected_binds = []
        for position, argument in enumerate(argv):
            if argument == "--volume":
                source, destination, options = argv[position + 1].split(":")
                expected_binds.append(
                    {
                        "source": source,
                        "destination": destination,
                        "read_only": options.split(",")[0] == "ro",
                    }
                )
        server = tomllib.loads(
            bounded(native_path(str(selected / "rendered/server.toml"))).decode()
        )
        if role == "api" and server.get("host_helper", {}).get("enabled") is True:
            expected_binds.append(
                {
                    "source": "/run/hfcache-host-helper/api",
                    "destination": "/run/hfcache-host-helper/api",
                    "read_only": True,
                }
            )
        require(
            projection["source_sha256"] == release["files"]["scripts/container-service.py"]
            and type(projection["binds"]) is list
            and sorted(projection["binds"], key=lambda row: row["destination"])
            == sorted(expected_binds, key=lambda row: row["destination"])
            and sorted(projection["binds"], key=lambda row: row["destination"])
            == sorted(container["mounts"], key=lambda row: row["destination"]),
            "actual rootless binds differ from the selected finite create projection",
        )


def bpf_deny_program(value: object, identifier: int, name: str) -> dict[str, Any]:  # noqa: PLR0912, PLR0915 - finite instruction proof stays together
    """Independently verify actual translated deny-all bytes; perform no BPF calls."""
    item = exact(
        value,
        {
            "type",
            "id",
            "tag",
            "name",
            "created_by_uid",
            "map_ids",
            "translated_bytes",
            "translated_hex",
            "translated_sha256",
            "semantics",
        },
        "actual BPF program metadata is incomplete",
    )
    require(
        type(item["type"]) is int
        and item["type"] == BPF_CGROUP_SKB_TYPE
        and type(item["id"]) is int
        and item["id"] == identifier
        and type(item["created_by_uid"]) is int
        and item["created_by_uid"] == 0
        and item["name"] == name
        and item["map_ids"] == []
        and isinstance(item["tag"], str)
        and re.fullmatch(r"[a-f0-9]{16}", item["tag"])
        and type(item["translated_bytes"]) is int
        and 0 < item["translated_bytes"] <= MAXIMUM_BPF_INSTRUCTIONS * 8
        and item["translated_bytes"] % 8 == 0
        and isinstance(item["translated_hex"], str)
        and len(item["translated_hex"]) == item["translated_bytes"] * 2
        and re.fullmatch(r"[a-f0-9]+", item["translated_hex"]),
        "actual BPF program is not the bounded root-created map-free profile",
    )
    body = bytes.fromhex(item["translated_hex"])
    require(
        hashlib.sha256(body).hexdigest() == item["translated_sha256"],
        "actual BPF bytecode hash differs",
    )
    instructions = []
    allowed = {
        0xB7,
        0xB4,
        0xBF,
        0xBC,
        0x44,
        0x61,
        0x69,
        0x71,
        0x79,
        0xDC,
        0xD4,
        0x05,
        0x15,
        0x55,
        0x95,
    }
    branches = {0x05, 0x15, 0x55}
    for code, registers, offset, immediate in struct.iter_unpack("<BBhi", body):
        dst, src = registers & 15, registers >> 4
        require(
            code in allowed and dst <= BPF_MAXIMUM_REGISTER and src <= BPF_MAXIMUM_REGISTER,
            "actual BPF instruction is unsupported",
        )
        if code in branches:
            require(offset >= 0, "actual BPF backward jump is unsupported")
        elif code in {0x61, 0x69, 0x71, 0x79}:
            require(
                0 <= offset <= BPF_MAXIMUM_CONTEXT_OFFSET and immediate == 0,
                "actual BPF context load is malformed",
            )
        else:
            require(offset == 0, "actual BPF instruction offset is malformed")
        if code in {0xB7, 0xB4, 0x44, 0x15, 0x55, 0xDC, 0xD4}:
            require(src == 0, "actual BPF instruction source is malformed")
        if code in {0xBF, 0xBC}:
            require(immediate == 0, "actual BPF register move is malformed")
        if code in {0xDC, 0xD4}:
            require(immediate in {16, 32, 64}, "actual BPF endian conversion is malformed")
        if code in {0x05, 0x95}:
            require(dst == src == immediate == 0, "actual BPF branch or exit is malformed")
        instructions.append((code, dst, src, offset, immediate))
    for pc, (code, _, _, offset, _) in enumerate(instructions):
        require(
            code not in branches or pc + offset + 1 < len(instructions),
            "actual BPF branch escapes the program",
        )
    pending: list[tuple[int, tuple[int | None, ...]]] = [(0, (None,) * 11)]
    seen: set[tuple[int, tuple[int | None, ...]]] = set()
    exits = 0
    while pending:
        pc, registers = pending.pop()
        state = (pc, registers)
        if state in seen:
            continue
        seen.add(state)
        require(
            len(seen) <= MAXIMUM_BPF_STATES and 0 <= pc < len(instructions),
            "actual BPF proof exhausted its bound or fell through",
        )
        code, dst, src, offset, immediate = instructions[pc]
        values = list(registers)
        if code == BPF_EXIT:
            require(
                values[0] == 0, "actual BPF program can allow a packet or return an unknown value"
            )
            exits += 1
            continue
        if code in branches:
            target = pc + offset + 1
            if code == BPF_JUMP_ALWAYS:
                pending.append((target, registers))
            else:
                current = values[dst]
                take = None if current is None else current == (immediate & ((1 << 64) - 1))
                if code == BPF_JUMP_NOT_EQUAL and take is not None:
                    take = not take
                if take is not False:
                    pending.append((target, registers))
                if take is not True:
                    pending.append((pc + 1, registers))
            continue
        if code in {0xB7, 0xB4}:
            values[dst] = immediate & ((1 << (64 if code == BPF_MOVE64_IMMEDIATE else 32)) - 1)
        elif code in {0xBF, 0xBC}:
            values[dst] = values[src]
            current = values[dst]
            if code == BPF_MOVE32_REGISTER and current is not None:
                values[dst] = current & ((1 << 32) - 1)
        elif code == BPF_OR32_IMMEDIATE:
            current = values[dst]
            if current is not None:
                values[dst] = (current | immediate) & ((1 << 32) - 1)
        else:
            values[dst] = None  # Context loads/endian conversions are unknown.
        pending.append((pc + 1, tuple(values)))
    semantics = exact(
        item["semantics"],
        {"verified_deny_all", "instructions", "states", "exits"},
        "actual BPF proof summary is malformed",
    )
    require(
        exits > 0
        and semantics["verified_deny_all"] is True
        and all(type(semantics[key]) is int for key in ("instructions", "states", "exits"))
        and semantics["instructions"] == len(instructions)
        and semantics["states"] == len(seen)
        and semantics["exits"] == exits,
        "actual BPF proof summary differs from independent bytecode analysis",
    )
    return item


def positive_integer(value: object, *, maximum: int = (1 << 63) - 1, zero: bool = False) -> bool:
    return type(value) is int and (0 if zero else 1) <= value <= maximum


def digest(value: object) -> bool:
    return isinstance(value, str) and SHA256.fullmatch(value) is not None


def process_identity(value: object) -> dict[str, Any]:
    item = exact(value, {"pid", "start_ticks"}, "network evidence process identity is incomplete")
    require(
        positive_integer(item["pid"])
        and item["pid"] > 1
        and isinstance(item["start_ticks"], str)
        and re.fullmatch(r"[0-9]+", item["start_ticks"]),
        "network evidence process identity is malformed",
    )
    return item


def device_identity(value: object) -> dict[str, Any]:
    item = exact(value, {"device", "inode"}, "network evidence kernel identity is incomplete")
    require(
        all(positive_integer(item[key]) for key in item),
        "network evidence kernel identity is malformed",
    )
    return item


def copied_evidence(value: object) -> tuple[dict[str, Any], dict[str, Any]]:
    copied = exact(value, {"record", "body"}, "network evidence public copy is missing")
    body = json_bytes(bounded(file_record(copied["record"])))
    require(body == copied["body"], "network evidence differs from retained original bytes")
    return copied["record"], body


def uid_mapping(process: dict[str, Any], *, host_uid: int = 1000, container_uid: int = 981) -> None:
    require(
        process["status"]["Uid"] == process["status"].get("Gid") == [host_uid] * 4
        and process["status"]["NSpid"] == [process["identity"]["pid"], 1],
        "stock control must use the actual rootless mapped identity",
    )
    for key in ("uid_map", "gid_map"):
        rows = [line.split() for line in process[key].splitlines()]
        require(
            all(
                len(row) == UID_MAPPING_FIELDS
                and all(re.fullmatch(r"[0-9]+", part) for part in row)
                for row in rows
            )
            and [container_uid, host_uid, 1] in [[int(part) for part in row] for row in rows],
            "stock control lacks the exact container-to-host identity mapping",
        )


def socket_success(value: object) -> None:
    row = exact(
        value, {"operation", "created", "closed", "errno"}, "actual socket control is incomplete"
    )
    require(
        row == {"operation": "socket", "created": True, "closed": True, "errno": None}
        and row["created"] is True
        and row["closed"] is True,
        "actual AF_UNIX or stock socket control failed",
    )


def derived_worker_policy(stock: dict[str, Any]) -> dict[str, Any]:
    """Independently reproduce the shipped installer narrowing, never execute it."""
    require(
        stock.get("defaultAction") == "SCMP_ACT_ERRNO" and type(stock.get("syscalls")) is list,
        "stock seccomp policy is not the source authority",
    )
    result = json.loads(json.dumps(stock))
    result.pop("architectures", None)
    result["archMap"] = [{"architecture": "SCMP_ARCH_X86_64", "subArchitectures": []}]
    rules, native = [], False
    for row in result["syscalls"]:
        require(
            type(row) is dict
            and type(row.get("names")) is list
            and row["names"]
            and all(isinstance(name, str) for name in row["names"])
            and isinstance(row.get("action"), str),
            "stock seccomp syscall rule is malformed",
        )
        if row["action"] == "SCMP_ACT_ALLOW":
            if "socket" in row["names"] and not any(
                row.get(key) for key in ("args", "includes", "excludes")
            ):
                native = True
            row["names"] = [name for name in row["names"] if name not in {"socket", "socketcall"}]
        if row["names"]:
            rules.append(row)
    require(native, "stock native socket availability is not permitted by its actual policy")
    rules.append(
        {
            "names": ["socket"],
            "action": "SCMP_ACT_ALLOW",
            "args": [{"index": 0, "value": 1, "op": "SCMP_CMP_EQ"}],
        }
    )
    result["syscalls"] = rules
    return result


def stock_socket_receipt(value: object, manifest: dict[str, Any]) -> dict[str, Any]:
    item = exact(
        value,
        {
            "schema_version",
            "scope",
            "guest_identity",
            "boot_id",
            "image_sha256",
            "stock_policy",
            "container_id",
            "kernel_release",
            "machine",
            "container",
            "host_process",
            "controller_namespaces",
            "probe_sha256",
            "outcome",
            "drain",
        },
        "stock socket control receipt is incomplete",
    )
    image = manifest["profiles"]["rootless"]["worker_image_sha256"]
    require(
        type(item["schema_version"]) is int
        and item["schema_version"] == 1
        and item["scope"]
        == "socket-family availability only; not worker confinement or feature acceptance"
        and item["guest_identity"] == manifest["guest"]["identity"]
        and item["boot_id"] == manifest["guest"]["boot_id"]
        and item["image_sha256"] == image
        and item["stock_policy"] == {"path": STOCK_POLICY_PATH, "sha256": STOCK_POLICY_SHA256}
        and digest(item["container_id"])
        and item["probe_sha256"] == SOCKET_CONTROL_SHA256
        and item["machine"] == "x86_64"
        and isinstance(item["kernel_release"], str)
        and re.fullmatch(r"[A-Za-z0-9._+-]{1,128}", item["kernel_release"]),
        "stock socket control is not the exact owned image, kernel and reviewed probe",
    )
    inner_uid = container_principal(manifest, "worker") if current_release(manifest) else 981
    host_uid = native_principal("api") if current_release(manifest) else 1000
    container = exact(
        item["container"],
        {"image_sha256", "user", "readonly_rootfs", "network_mode", "security_options"},
        "stock socket control container is incomplete",
    )
    require(
        container
        == {
            "image_sha256": image,
            "user": f"{inner_uid}:{inner_uid}",
            "readonly_rootfs": True,
            "network_mode": "none",
            "security_options": ["no-new-privileges", "seccomp=" + STOCK_POLICY_PATH],
        }
        and container["readonly_rootfs"] is True,
        "stock socket control changed confinement",
    )
    process = role_process(item["host_process"], "worker", "rootless")
    uid_mapping(process, host_uid=host_uid, container_uid=inner_uid)
    namespaces = exact(
        item["controller_namespaces"],
        set(process["namespaces"]),
        "stock control observer namespaces are incomplete",
    )
    require(
        all(
            isinstance(value, str) and re.fullmatch(name + r":\[[0-9]+\]", value)
            for name, value in namespaces.items()
        )
        and all(
            namespaces[name] != process["namespaces"][name]
            for name in ("pid", "user", "mnt", "net")
        ),
        "stock control was not observed in distinct actual namespaces",
    )
    outcome = exact(
        item["outcome"],
        {"schema_version", "scope", "identity", "status", "families"},
        "stock socket outcomes are incomplete",
    )
    require(
        type(outcome["schema_version"]) is int
        and outcome["schema_version"] == 1
        and outcome["scope"] == "socket-family availability only; no bind/listen/connect"
        and outcome["identity"] == {"pid": 1, "start_ticks": process["identity"]["start_ticks"]}
        and type(outcome["identity"]["pid"]) is int,
        "stock socket outcomes are not from the observed container init",
    )
    status = exact(
        outcome["status"],
        {"Uid", "Gid", "NoNewPrivs", "Seccomp", "CapEff", "CapBnd", "NSpid"},
        "stock socket status is incomplete",
    )
    require(
        all(isinstance(value, str) for value in status.values())
        and all(status[key].split() == ["981"] * 4 for key in ("Uid", "Gid"))
        and status["NoNewPrivs"] == "1"
        and status["Seccomp"] == "2"
        and status["NSpid"] == "1"
        and status["CapEff"] == status["CapBnd"] == "0" * 16,
        "stock socket outcome privilege is unproved",
    )
    for row in exact(
        outcome["families"],
        {"unix", "inet", "inet6"},
        "stock socket family controls are incomplete",
    ).values():
        socket_success(row)
    drain = exact(
        item["drain"],
        {
            "container_id",
            "running",
            "exit_code",
            "attachment_waited",
            "attachment_exit_code",
            "processes",
            "cgroups",
            "gate_identity_unchanged",
        },
        "stock socket control drain is incomplete",
    )
    require(
        drain["container_id"] == item["container_id"]
        and drain["running"] is False
        and type(drain["exit_code"]) is int
        and drain["exit_code"] == 0
        and drain["attachment_waited"] is True
        and type(drain["attachment_exit_code"]) is int
        and drain["attachment_exit_code"] == 0
        and drain["gate_identity_unchanged"] is True
        and type(drain["processes"]) is list
        and MINIMUM_CONTROL_PROCESSES <= len(drain["processes"]) <= MAXIMUM_THREADS
        and type(drain["cgroups"]) is list
        and MINIMUM_CONTROL_CGROUPS <= len(drain["cgroups"]) <= MAXIMUM_THREADS,
        "stock socket control exact resources did not drain",
    )
    identities = set()
    for row in drain["processes"]:
        exact(
            row, {"pid", "start_ticks", "gone"}, "stock socket control process drain is malformed"
        )
        identity = process_identity({key: row[key] for key in ("pid", "start_ticks")})
        require(row["gone"] is True, "stock socket control process remains live or unknown")
        identities.add((identity["pid"], identity["start_ticks"]))
    require(
        len(identities) == len(drain["processes"])
        and (process["identity"]["pid"], process["identity"]["start_ticks"]) in identities,
        "stock socket control omitted its observed init",
    )
    for row in drain["cgroups"]:
        exact(row, {"path", "pids"}, "stock socket control cgroup drain is malformed")
        require(
            isinstance(row["path"], str)
            and row["path"].startswith("/user.slice/")
            and item["container_id"] in row["path"]
            and row["pids"] == [],
            "stock socket control cgroup is not empty or owned",
        )
    return item


def guarded_bpf_queries(
    value: object, group: object, *, filtered: bool
) -> dict[tuple[int, int], dict[str, Any]]:
    target = device_identity(group)
    require(
        type(value) is list and len(value) == BPF_QUERY_COUNT,
        "actual packet filter queries are incomplete",
    )
    if not isinstance(value, list):
        reject("actual packet filter queries are unavailable")
    rows = {}
    for raw in value:
        row = exact(
            raw,
            {
                "attach_type",
                "query_flags",
                "rc",
                "errno",
                "attach_flags",
                "reported_prog_count",
                "ids",
                "ids_buffer",
                "complete",
                "truncated",
                "backing_bytes",
                "semantic_prefix_bytes",
                "revision",
                "tail_before_hex",
                "tail_after_hex",
                "tail_changed",
                "query_process_exit",
                "timed_out",
                "stderr_sha256",
                "entered",
                "query_process_gone",
                "identity",
            },
            "actual guarded packet filter query is incomplete",
        )
        require(
            all(
                type(row[key]) is int
                for key in (
                    "attach_type",
                    "query_flags",
                    "rc",
                    "errno",
                    "attach_flags",
                    "reported_prog_count",
                    "backing_bytes",
                    "semantic_prefix_bytes",
                    "revision",
                    "query_process_exit",
                )
            ),
            "packet filter query numeric metadata is coerced or absent",
        )
        key = row["attach_type"], row["query_flags"]
        require(
            key in {(0, 0), (0, 1), (1, 0), (1, 1)}
            and key not in rows
            and row["rc"] == row["errno"] == row["query_process_exit"] == 0
            and 0 <= row["attach_flags"] < 1 << 32
            and 0 <= row["revision"] < 1 << 64
            and (row["attach_flags"] == 0 if key[1] == 1 else True)
            and row["backing_bytes"] == BPF_QUERY_BACKING_BYTES
            and row["semantic_prefix_bytes"] == BPF_QUERY_PREFIX_BYTES
            and row["tail_before_hex"] == row["tail_after_hex"] == "a5" * 192
            and row["tail_changed"] is False
            and row["complete"] is True
            and row["truncated"] is False
            and row["timed_out"] is False
            and row["query_process_gone"] is True
            and row["stderr_sha256"] == hashlib.sha256(b"").hexdigest(),
            "actual packet filter query failed or violated its full UAPI bounds",
        )
        ids, buffer = row["ids"], row["ids_buffer"]
        require(
            type(ids) is list
            and (0 < len(ids) <= BPF_QUERY_IDS if filtered else ids == [])
            and all(positive_integer(identifier, maximum=(1 << 32) - 1) for identifier in ids)
            and len(set(ids)) == len(ids)
            and row["reported_prog_count"] == len(ids)
            and type(buffer) is list
            and len(buffer) == BPF_QUERY_IDS
            and all(
                positive_integer(identifier, maximum=(1 << 32) - 1, zero=True)
                for identifier in buffer
            )
            and buffer == ids + [0] * (64 - len(ids)),
            "actual packet filter ID inventory is unknown or truncated",
        )
        entered = exact(
            row["entered"],
            {"identity", "fd_device", "fd_inode", "attach_type", "query_flags"},
            "packet filter query entry is incomplete",
        )
        identity = exact(
            row["identity"],
            {"pid", "start_ticks", "cgroup"},
            "packet filter query child identity is incomplete",
        )
        process_identity({name: identity[name] for name in ("pid", "start_ticks")})
        require(
            entered["identity"] == identity
            and isinstance(identity["cgroup"], str)
            and identity["cgroup"].startswith("0::/")
            and type(entered["attach_type"]) is int
            and entered["attach_type"] == key[0]
            and type(entered["query_flags"]) is int
            and entered["query_flags"] == key[1]
            and all(
                type(entered["fd_" + name]) is int and entered["fd_" + name] == target[name]
                for name in target
            ),
            "packet filter query was not bound to the observed live cgroup",
        )
        rows[key] = row
    for kind in (0, 1):
        require(
            set(rows[(kind, 0)]["ids"]) <= set(rows[(kind, 1)]["ids"]),
            "direct packet filter IDs are absent from effective filtering",
        )
    return rows


def packet_filter_snapshot(value: object, group: str) -> dict[str, Any]:
    item = exact(
        value,
        {"captured_ns", "cgroup", "cgroup_identity", "queries", "program_audit"},
        "actual packet filter snapshot is incomplete",
    )
    require(
        positive_integer(item["captured_ns"]) and item["cgroup"] == group,
        "packet filter snapshot changed target cgroup",
    )
    rows = guarded_bpf_queries(item["queries"], item["cgroup_identity"], filtered=True)
    expected = {}
    for kind in (0, 1):
        for identifier in rows[(kind, 1)]["ids"]:
            require(
                identifier not in expected,
                "ingress and egress packet filter identities are ambiguous",
            )
            expected[identifier] = "sd_fw_ingress" if kind == 0 else "sd_fw_egress"
    require(
        len(expected) <= MAXIMUM_BPF_PROGRAMS,
        "packet filter program inventory exceeds the reviewed bound",
    )
    audit = exact(
        item["program_audit"],
        {"schema_version", "identity", "programs", "verified"},
        "actual translated packet filter audit is incomplete",
    )
    identity = exact(
        audit["identity"],
        {"pid", "start_ticks", "state"},
        "packet filter audit child identity is incomplete",
    )
    process_identity({name: identity[name] for name in ("pid", "start_ticks")})
    require(
        type(audit["schema_version"]) is int
        and audit["schema_version"] == 1
        and audit["verified"] is True
        and identity["state"] in set("RSDTWtIKP")
        and type(audit["programs"]) is list
        and len(audit["programs"]) == len(expected),
        "actual translated packet filter audit failed or is unknown",
    )
    programs = {}
    for program in audit["programs"]:
        require(
            type(program) is dict
            and type(program.get("id")) is int
            and program["id"] in expected
            and program["id"] not in programs,
            "packet filter audit omitted or substituted a queried program",
        )
        programs[program["id"]] = bpf_deny_program(program, program["id"], expected[program["id"]])
    return {
        "captured_ns": item["captured_ns"],
        "cgroup_identity": item["cgroup_identity"],
        "programs": programs,
        "queries": {
            key: {name: row[name] for name in ("ids", "attach_flags", "revision")}
            for key, row in rows.items()
        },
    }


def loopback_tuple(value: object, family: str) -> list[Any]:
    if not isinstance(value, list):
        reject("packet filter endpoint tuple is unavailable")
    require(
        type(value) is list
        and len(value) == SOCKET_TUPLE_FIELDS
        and value[0] == ("127.0.0.1" if family == "inet" else "::1")
        and positive_integer(value[1], maximum=65535),
        "packet filter endpoint is not an exact owned loopback tuple",
    )
    return value


def native_control_snapshot(
    value: object,
    phase: str,
    worker: dict[str, Any],
    *,
    expected_group: str | None = None,
    expected_uid: int | None = None,
) -> dict[str, Any]:
    item = exact(
        value,
        {
            "phase",
            "identity",
            "cgroup",
            "cgroup_identity",
            "netns",
            "process",
            "queries",
            "round_trips",
        },
        "same-UID unfiltered control is incomplete",
    )
    process = role_process(item["process"], "worker", "native", expected_uid=expected_uid)
    identity = process_identity(item["identity"])
    require(
        item["phase"] == phase
        and identity == {key: process["identity"][key] for key in identity}
        and identity["pid"] != worker["identity"]["pid"]
        and item["netns"] == worker["netns"] == process["namespaces"]["net"]
        and isinstance(item["cgroup"], str)
        and (
            item["cgroup"] == expected_group
            if expected_group is not None
            else re.fullmatch(
                r"/system.slice/web005-[a-f0-9]{32}-network-control\.service", item["cgroup"]
            )
        )
        and item["cgroup"] != worker["cgroup"]
        and process["cgroup"] == "0::" + item["cgroup"] + "\n",
        "positive packet filter control is not the same-UID same-netns independent live process",
    )
    guarded_bpf_queries(item["queries"], item["cgroup_identity"], filtered=False)
    for family, row in exact(
        item["round_trips"], {"inet", "inet6"}, "positive packet filter control lacks both families"
    ).items():
        exact(
            row,
            {
                "started_ns",
                "finished_ns",
                "local_tuple",
                "remote_tuple",
                "nonce_sha256",
                "acknowledged",
            },
            "positive packet filter round trip is incomplete",
        )
        require(
            positive_integer(row["started_ns"])
            and positive_integer(row["finished_ns"])
            and 0 < row["finished_ns"] - row["started_ns"] <= MAXIMUM_NETWORK_ATTEMPT_NS
            and digest(row["nonce_sha256"])
            and row["acknowledged"] is True,
            "positive packet filter round trip failed",
        )
        loopback_tuple(row["local_tuple"], family)
        loopback_tuple(row["remote_tuple"], family)
    return item


def native_listener_evidence(
    value: object, worker: dict[str, Any], before: dict[str, Any], after: dict[str, Any]
) -> dict[str, Any]:
    item = exact(
        value,
        {
            "owner",
            "netns",
            "endpoints",
            "fds_before",
            "fds_after",
            "started_ns",
            "finished_ns",
            "accepts",
            "threads",
            "closed_descriptors",
        },
        "continuous packet filter listener evidence is incomplete",
    )
    process_identity(item["owner"])
    require(
        item["netns"] == worker["netns"]
        and positive_integer(item["started_ns"])
        and positive_integer(item["finished_ns"])
        and item["started_ns"] < item["finished_ns"]
        and item["fds_before"] == item["fds_after"],
        "packet filter listeners changed identity or observation interval",
    )
    endpoints = exact(
        item["endpoints"], {"inet", "inet6"}, "packet filter listener endpoints are incomplete"
    )
    fds = exact(
        item["fds_before"], {"inet", "inet6"}, "packet filter listener descriptors are incomplete"
    )
    for family, row in fds.items():
        exact(
            row,
            {"descriptor", "device", "inode", "local_tuple"},
            "packet filter listener kernel facts are incomplete",
        )
        require(
            positive_integer(row["descriptor"], zero=True)
            and all(positive_integer(row[key]) for key in ("device", "inode"))
            and row["local_tuple"] == endpoints[family],
            "packet filter listener kernel facts changed",
        )
        loopback_tuple(endpoints[family], family)
    require(
        fds["inet"]["descriptor"] != fds["inet6"]["descriptor"]
        and type(item["accepts"]) is list
        and len(item["accepts"]) == CONTROL_ACCEPT_COUNT,
        "packet filter listener accepted an unknown connection or omitted a control",
    )
    expected = {}
    for control in (before, after):
        for family, trip in control["round_trips"].items():
            require(
                trip["remote_tuple"] == endpoints[family]
                and item["started_ns"]
                <= trip["started_ns"]
                < trip["finished_ns"]
                <= item["finished_ns"],
                "packet filter control escaped continuous listener interval",
            )
            expected[(control["phase"], family)] = trip
    require(
        len({trip["nonce_sha256"] for trip in expected.values()}) == CONTROL_ACCEPT_COUNT,
        "packet filter positive-control nonces are not distinct",
    )
    seen = set()
    for row in item["accepts"]:
        exact(
            row,
            {
                "family",
                "phase",
                "accepted_ns",
                "local_tuple",
                "peer_tuple",
                "nonce_sha256",
                "acknowledged",
            },
            "packet filter listener accept evidence is incomplete",
        )
        key = row["phase"], row["family"]
        require(
            key in expected and key not in seen,
            "packet filter listener accepted an unknown or duplicate connection",
        )
        trip = expected[key]
        require(
            positive_integer(row["accepted_ns"])
            and trip["started_ns"] <= row["accepted_ns"] <= trip["finished_ns"]
            and row["local_tuple"] == trip["remote_tuple"]
            and row["peer_tuple"] == trip["local_tuple"]
            and row["nonce_sha256"] == trip["nonce_sha256"]
            and row["acknowledged"] is True,
            "packet filter control lacks actual accept-side nonce acknowledgement",
        )
        seen.add(key)
    require(
        type(item["threads"]) is list
        and len(item["threads"]) == CONTROL_LISTENER_COUNT
        and len({row.get("id") for row in item["threads"] if type(row) is dict})
        == CONTROL_LISTENER_COUNT
        and all(
            type(row) is dict
            and set(row) == {"id", "name", "alive"}
            and positive_integer(row["id"])
            and isinstance(row["name"], str)
            and 0 < len(row["name"]) <= MAXIMUM_SAFE_LABEL
            and row["alive"] is False
            for row in item["threads"]
        )
        and item["closed_descriptors"] == sorted(row["descriptor"] for row in fds.values())
        and all(type(fd) is int for fd in item["closed_descriptors"]),
        "packet filter listener threads or descriptors did not drain",
    )
    return item


def native_control_drain(value: object, control: dict[str, Any]) -> None:
    item = exact(
        value,
        {"identity", "unit_name", "unit_exited", "unit_final", "process_gone", "cgroup_empty"},
        "packet filter positive control drain is incomplete",
    )
    require(
        item["identity"] == control["identity"]
        and item["unit_name"] == control["cgroup"].rsplit("/", 1)[-1]
        and item["process_gone"] is True
        and item["cgroup_empty"] is True,
        "packet filter control process did not drain",
    )
    keys = {"MainPID", "ExecMainCode", "ExecMainStatus", "ActiveState", "SubState", "InvocationID"}
    exited = exact(item["unit_exited"], keys, "packet filter control positive exit is incomplete")
    final = exact(item["unit_final"], keys, "packet filter control final state is incomplete")
    require(
        all(isinstance(value, str) for row in (exited, final) for value in row.values())
        and [
            exited[key]
            for key in ("MainPID", "ExecMainCode", "ExecMainStatus", "ActiveState", "SubState")
        ]
        == ["0", "1", "0", "active", "exited"]
        and IDENTIFIER.fullmatch(exited["InvocationID"])
        and [final[key] for key in ("MainPID", "ExecMainStatus", "ActiveState", "SubState")]
        == ["0", "0", "inactive", "dead"]
        and final["ExecMainCode"] in {"0", "1"}
        and final["InvocationID"] in {"", exited["InvocationID"]},
        "packet filter positive control never exited successfully or remains active",
    )


def native_origin_network(  # noqa: PLR0913, PLR0917 - independent identity contexts
    item: dict[str, Any],
    process: dict[str, Any],
    network: dict[str, Any],
    role: dict[str, Any],
    manifest: dict[str, Any],
    invocation: dict[str, Any],
) -> None:
    record, verdict = copied_evidence(network.get("worker_network"))
    exact(
        verdict,
        {
            "schema_version",
            "kind",
            "guest_identity",
            "boot_id",
            "fixture_id",
            "generation_id",
            "worker",
            "filters_before",
            "filters_after",
            "control_before",
            "control_after",
            "control_drain",
            "listeners",
            "sources",
            "completed_ns",
            "packet_filter_denial_verified",
        },
        "native packet filter verdict is incomplete",
    )
    require(
        type(verdict["schema_version"]) is int
        and verdict["schema_version"] == ORIGIN_EVIDENCE_VERSION
        and verdict["kind"] == "native-cgroup-packet-filter"
        and verdict["guest_identity"] == manifest["guest"]["identity"]
        and verdict["boot_id"] == manifest["guest"]["boot_id"]
        and all(verdict[key] == invocation[key] for key in ("fixture_id", "generation_id"))
        and verdict["packet_filter_denial_verified"] is True
        and positive_integer(verdict["completed_ns"])
        and item["network_evidence_sha256"] == record["sha256"],
        "native packet filter verdict changed ownership or original bytes",
    )
    worker = exact(
        verdict["worker"],
        {
            "identity",
            "unit",
            "cgroup",
            "netns",
            "process_before",
            "process_after",
            "ready_sha256",
            "attempts_sha256",
            "ready",
            "attempts",
        },
        "native packet filter worker binding is incomplete",
    )
    identity = process_identity(worker["identity"])
    modern = current_release(manifest)
    group = (
        "/system.slice/hfcache-verification.service"
        if modern
        else "/system.slice/web005-" + invocation["generation_id"] + "-worker.service"
    )
    require(
        identity == {key: process["identity"][key] for key in identity}
        and worker["cgroup"] == group
        and worker["netns"] == process["namespaces"]["net"]
        and process["cgroup"] == "0::" + group + "\n",
        "packet filter target is not the original actual worker",
    )
    for key in ("process_before", "process_after"):
        observed = role_process(
            worker[key],
            "worker",
            invocation["profile"],
            expected_uid=native_principal("worker") if modern else None,
        )
        require(
            all(
                observed[name] == process[name]
                for name in (
                    "executable",
                    "argv_sha256",
                    "argv_count",
                    "namespaces",
                    "uid_map",
                    "gid_map",
                    "cgroup",
                )
            )
            and all(observed["identity"][name] == identity[name] for name in identity),
            "packet filter worker source or live identity changed",
        )
    unit = exact(
        worker["unit"],
        {
            "name",
            "main_pid",
            "invocation_id",
            "cgroup",
            "ip_deny",
            "ip_allow",
            "private_network",
            "network_namespace_path",
            "address_families",
            "source_sha256",
            "hardening",
        },
        "packet filter original worker unit is incomplete",
    )
    require(
        unit["name"] == group.rsplit("/", 1)[-1]
        and type(unit["main_pid"]) is int
        and unit["main_pid"] == identity["pid"]
        and isinstance(unit["invocation_id"], str)
        and IDENTIFIER.fullmatch(unit["invocation_id"])
        and unit["invocation_id"] == role["unit"]["InvocationID"]
        and unit["cgroup"] == group
        and unit["ip_deny"] == ["0.0.0.0/0", "::/0"]
        and unit["ip_allow"] == []
        and unit["private_network"] is False
        and unit["network_namespace_path"] == ""
        and unit["address_families"] == ["AF_UNIX", "AF_INET", "AF_INET6"]
        and digest(unit["source_sha256"])
        and unit["hardening"] == NATIVE_HARDENING,
        "native packet filter proof substituted original worker isolation",
    )
    for key in ("ready", "attempts"):
        record_body = exact(
            worker[key],
            {"schema_version", "fixture_id", "generation_id", "identity", "cgroup", "netns"}
            | ({"network_probes"} if key == "attempts" else set()),
            "native worker handshake record is incomplete",
        )
        require(
            type(record_body["schema_version"]) is int
            and record_body["schema_version"] == ORIGIN_EVIDENCE_VERSION
            and all(record_body[name] == verdict[name] for name in ("fixture_id", "generation_id"))
            and all(record_body[name] == worker[name] for name in ("identity", "cgroup", "netns"))
            and hashlib.sha256(canonical(record_body)).hexdigest() == worker[key + "_sha256"],
            "native worker handshake record digest or identity changed",
        )
    require(
        worker["attempts"]["network_probes"] == item["network_probes"],
        "native packet filter verdict changed original raw attempts",
    )
    before = packet_filter_snapshot(verdict["filters_before"], group)
    after = packet_filter_snapshot(verdict["filters_after"], group)
    require(
        all(before[key] == after[key] for key in ("cgroup_identity", "programs", "queries"))
        and before["captured_ns"] < after["captured_ns"] <= verdict["completed_ns"],
        "actual packet filter IDs, revisions or bytecode changed across attempts",
    )
    control_group = (
        "/system.slice/"
        + fixture_unit(manifest, invocation["generation_id"], "network-control.service")
        if modern
        else None
    )
    controls = {
        phase: native_control_snapshot(
            verdict["control_" + phase],
            phase,
            worker,
            expected_group=control_group,
            expected_uid=native_principal("worker") if modern else None,
        )
        for phase in ("before", "after")
    }
    first, last = controls["before"], controls["after"]
    require(
        all(first[key] == last[key] for key in ("identity", "cgroup", "cgroup_identity", "netns")),
        "positive packet filter control changed live identity",
    )
    listeners = native_listener_evidence(verdict["listeners"], worker, first, last)
    native_control_drain(verdict["control_drain"], last)
    for family, row in item["network_probes"].items():
        exact(
            row,
            {
                "attempted",
                "operation",
                "outcome",
                "error_class",
                "errno",
                "started_ns",
                "finished_ns",
                "local_tuple",
                "remote_tuple",
                "nonce_sha256",
            },
            "native raw packet filter attempt is incomplete",
        )
        require(
            row["attempted"] is True
            and row["operation"] == "connect"
            and row["outcome"] == "timeout"
            and row["error_class"] == "TimeoutError"
            and row["errno"] is None
            and positive_integer(row["started_ns"])
            and positive_integer(row["finished_ns"])
            and MINIMUM_CANCEL_NS
            <= row["finished_ns"] - row["started_ns"]
            <= MAXIMUM_NETWORK_ATTEMPT_NS
            and before["captured_ns"]
            < row["started_ns"]
            < row["finished_ns"]
            < after["captured_ns"]
            and first["round_trips"][family]["finished_ns"] < row["started_ns"]
            and row["finished_ns"] < last["round_trips"][family]["started_ns"]
            and listeners["started_ns"]
            <= row["started_ns"]
            < row["finished_ns"]
            <= listeners["finished_ns"]
            and row["remote_tuple"] == listeners["endpoints"][family]
            and digest(row["nonce_sha256"]),
            "native timeout lacks the complete live packet filter and positive-control conjunction",
        )
        loopback_tuple(row["local_tuple"], family)
        require(
            not any(
                accepted["family"] == family and accepted["peer_tuple"] == row["local_tuple"]
                for accepted in listeners["accepts"]
            ),
            "packet filter listener accepted the worker connection",
        )
    nonces = [row["nonce_sha256"] for row in item["network_probes"].values()]
    nonces.extend(
        row["nonce_sha256"] for control in (first, last) for row in control["round_trips"].values()
    )
    require(
        len(set(nonces)) == NETWORK_NONCE_COUNT,
        "packet filter attempts and controls reused a nonce identity",
    )
    sources = exact(
        verdict["sources"],
        {
            "native_helper_sha256",
            "collector_sha256",
            "entrypoints_sha256",
            "network_helper_sha256",
            "query_source_sha256",
            "program_auditor_sha256",
            "control_source_sha256",
        },
        "packet filter source inventory is incomplete",
    )
    require(
        all(digest(value) for value in sources.values())
        and sources["program_auditor_sha256"] == PROGRAM_AUDITOR_SHA256
        and listeners["finished_ns"] <= verdict["completed_ns"],
        "packet filter proof did not bind reviewed program auditing or finite listener completion",
    )


def rootless_origin_network(
    item: dict[str, Any], network: dict[str, Any], worker: dict[str, Any], manifest: dict[str, Any]
) -> None:
    modern = current_release(manifest)
    bindings = manifest["profiles"]["rootless"].get("network") if modern else None
    if modern:
        bindings = exact(
            bindings,
            {"worker_policy", "stock_control"},
            "rootless network authority is incomplete",
        )
        for binding in bindings.values():
            file_record(binding, root=ROOT)
    policy_path = bindings["worker_policy"]["path"] if bindings is not None else WORKER_POLICY_PATH
    receipt_path = (
        bindings["stock_control"]["path"] if bindings is not None else SOCKET_RECEIPT_PATH
    )
    context = exact(
        item["seccomp_context"],
        {"image_sha256", "policy", "availability"},
        "rootless origin policy context is incomplete",
    )
    expected_policy = {
        "path": policy_path,
        "sha256": WORKER_POLICY_SHA256,
        "default_action": "SCMP_ACT_ERRNO",
        "default_errno": 38,
        "native_arch": "SCMP_ARCH_X86_64",
        "allowed_socket_families": [1],
    }
    require(
        context["policy"] == expected_policy
        and type(context["policy"]["default_errno"]) is int
        and all(type(value) is int for value in context["policy"]["allowed_socket_families"])
        and context["image_sha256"] == manifest["profiles"]["rootless"]["worker_image_sha256"],
        "rootless origin is not bound to the exact profile-derived socket policy",
    )
    availability = exact(
        context["availability"], {"path", "sha256"}, "rootless stock control linkage is incomplete"
    )
    record, receipt = copied_evidence(network.get("worker_network"))
    policy_record, policy = copied_evidence(network.get("worker_policy"))
    stock_record, stock = copied_evidence(network.get("stock_policy"))
    require(
        availability == {"path": receipt_path, "sha256": record["sha256"]}
        and policy_record["sha256"] == WORKER_POLICY_SHA256
        and stock_record["sha256"] == STOCK_POLICY_SHA256
        and policy == derived_worker_policy(stock)
        and type(policy.get("defaultErrnoRet")) is int
        and policy["defaultErrnoRet"] == context["policy"]["default_errno"],
        "rootless denial policy does not derive from the exact available stock authority",
    )
    stock_socket_receipt(receipt, manifest)
    if bindings is not None:
        require(
            bindings["worker_policy"]["sha256"] == policy_record["sha256"]
            and bindings["stock_control"]["sha256"] == record["sha256"],
            "rootless applied network records differ from their explicit authority",
        )
    container = worker["container"]
    generation = worker.get("generation_id")
    if not isinstance(generation, str) or not IDENTIFIER.fullmatch(generation):
        reject("rootless policy mount generation is unknown")
    if bindings is None:
        public = "/opt/hfcache-web005/rootless-generations-v8/" + generation + "/public/"
        mounted = {
            policy_path: public + "worker-policy.json",
            receipt_path: public + "worker-availability.json",
        }
    else:
        mounted = {policy_path: policy_path, receipt_path: receipt_path}
    require(
        container["image_sha256"] == context["image_sha256"]
        and "seccomp=" + policy_path in container["security_opt"]
        and sum(option.startswith("seccomp=") for option in container["security_opt"]) == 1
        and all(
            any(
                mount["source"] == mounted[path]
                and mount["destination"] == path
                and mount["read_only"] is True
                for mount in container["mounts"]
            )
            for path in (policy_path, receipt_path)
        ),
        "rootless worker did not apply and readonly-bind the measured policy and stock control",
    )
    socket_success(item["unix_socket"])
    for row in item["network_probes"].values():
        exact(
            row,
            {"attempted", "operation", "outcome", "error_class", "errno", "elapsed_ns", "denied"},
            "rootless socket denial is incomplete",
        )
        require(
            row["attempted"] is True
            and row["operation"] == "socket"
            and row["outcome"] == "denied"
            and row["error_class"] == "OSError"
            and type(row["errno"]) is int
            and row["errno"] == policy["defaultErrnoRet"]
            and row["denied"] is True
            and positive_integer(row["elapsed_ns"], maximum=5_000_000_000, zero=True),
            "rootless socket refusal is not the measured applied-policy outcome",
        )


def origin_probe(  # noqa: PLR0913 - contexts independently bind retained network evidence
    value: object,
    process: dict[str, Any],
    role: str,
    profile: str,
    *,
    network: dict[str, Any] | None = None,
    worker: dict[str, Any] | None = None,
    manifest: dict[str, Any] | None = None,
    invocation: dict[str, Any] | None = None,
) -> None:
    version = value.get("schema_version") if type(value) is dict else None
    extra = (
        (
            {"unix_socket", "seccomp_context"}
            if profile == "rootless"
            else {"network_evidence_sha256"}
        )
        if version == ORIGIN_EVIDENCE_VERSION and role == "worker"
        else set()
    )
    item = exact(
        value,
        {
            "schema_version",
            "role",
            "profile",
            "identity",
            "status",
            "authority_probes",
            "network_probes",
            "passed",
        }
        | extra,
        "actual role origin probe is incomplete",
    )
    identity = item["identity"]
    require(
        item["schema_version"] in ({1, 2} if role == "worker" else {1})
        and type(item["schema_version"]) is int
        and item["role"] == role
        and item["profile"] == profile
        and item["passed"] is True
        and identity["pid"] == process["status"]["NSpid"][-1]
        and identity["start_ticks"] == process["identity"]["start_ticks"],
        "role origin probe was not executed in the actual role process",
    )
    authorities = {"basic", "writer", "reader", "mcp_reader", "hub"}
    if role == "caddy":
        authorities |= {"archive", "policy", "helper"}
    probes = exact(
        item["authority_probes"], authorities, "actual role authority probes are incomplete"
    )
    for row in probes.values():
        exact(row, {"attempted", "errno", "denied"}, "actual authority probe is malformed")
        require(
            row["attempted"] is True
            and row["denied"] is True
            and type(row["errno"]) is int
            and row["errno"] in {errno.EACCES, errno.EPERM, errno.ENOENT, errno.ENOTDIR},
            "actual role could read a protected authority or its result is unknown",
        )
    probe_network = exact(
        item["network_probes"],
        {"inet", "inet6"} if role == "worker" else set(),
        "actual role network probes are incomplete",
    )
    if version == ORIGIN_EVIDENCE_VERSION:
        inner_identity = exact(
            item["identity"],
            {"pid", "start_ticks"},
            "version2 origin process identity is incomplete",
        )
        inner_status = exact(
            item["status"],
            {"Pid", "PPid", "Uid", "Gid", "NSpid", "CapEff", "CapBnd", "NoNewPrivs", "Seccomp"},
            "version2 origin inner process status is incomplete",
        )
        require(
            type(inner_identity["pid"]) is int
            and type(inner_status["Pid"]) is int
            and inner_status["Pid"] == inner_identity["pid"]
            and positive_integer(inner_status["PPid"], zero=True)
            and inner_status["Uid"] == inner_status["Gid"] == [981] * 4
            and all(type(uid) is int for name in ("Uid", "Gid") for uid in inner_status[name])
            and inner_status["NSpid"] == [inner_identity["pid"]]
            and all(type(pid) is int for pid in inner_status["NSpid"])
            and inner_status["CapEff"] == inner_status["CapBnd"] == "0" * 16
            and type(inner_status["NoNewPrivs"]) is int
            and inner_status["NoNewPrivs"] == 1
            and type(inner_status["Seccomp"]) is int
            and inner_status["Seccomp"] == SECCOMP_FILTER
            and (
                inner_status["PPid"] == 0
                if profile == "rootless"
                else inner_status["PPid"] == process["identity"]["parent_pid"]
            ),
            "version2 origin inner worker identity or hardening differs",
        )
        require(
            network is not None
            and worker is not None
            and manifest is not None
            and invocation is not None,
            "version2 origin lacks independent applied network evidence",
        )
        if network is None or worker is None or manifest is None or invocation is None:
            reject("version2 network context is unavailable")
        if profile == "rootless":
            rootless_origin_network(item, network, worker, manifest)
        else:
            native_origin_network(item, process, network, worker, manifest, invocation)
        return
    for row in probe_network.values():
        exact(row, {"attempted", "operation", "errno", "denied"}, "actual no-IP probe is malformed")
        allowed = {errno.EACCES, errno.EPERM}
        if profile == "rootless" and row["operation"] == "socket":
            allowed |= {errno.EAFNOSUPPORT, errno.EPROTONOSUPPORT}
        require(
            row["attempted"] is True
            and row["denied"] is True
            and row["operation"] in {"socket", "connect"}
            and type(row["errno"]) is int
            and row["errno"] in allowed,
            "actual worker IP refusal lacks a policy denial from its own process",
        )


def unix_listener(value: object, process: dict[str, Any], *, worker: bool, profile: str) -> None:
    keys = {"path", "device", "inode", "uid", "gid", "mode", "kernel_creator_peer", "acceptor"}
    if profile == "rootless" and type(value) is dict and "source_path" in value:
        keys.add("source_path")
    item = exact(
        value,
        keys,
        "actual Unix listener inspection is incomplete",
    )
    acceptor = exact(
        item["acceptor"],
        {"pid", "start_ticks", "process_path", "kernel_inode", "listener_fds", "activation_fd"},
        "actual Unix acceptor inspection is incomplete",
    )
    require(
        isinstance(item["path"], str)
        and item["path"].startswith("/")
        and all(type(item[key]) is int and item[key] > 0 for key in ("device", "inode"))
        and acceptor["pid"] == process["identity"]["pid"]
        and acceptor["start_ticks"] == process["identity"]["start_ticks"]
        and type(acceptor["kernel_inode"]) is int
        and acceptor["kernel_inode"] > 0
        and type(acceptor["listener_fds"]) is list
        and acceptor["listener_fds"]
        and all(type(fd) is int and fd >= 0 for fd in acceptor["listener_fds"]),
        "Unix listener is not bound to the actual role acceptor",
    )
    creator = exact(
        item["kernel_creator_peer"],
        {"pid", "uid", "gid", "start_ticks"},
        "Unix listener creator inspection is incomplete",
    )
    if worker and profile != "rootless":
        require(
            creator["pid"] == 1
            and creator["uid"] == 0
            and acceptor["activation_fd"] == NATIVE_ACTIVATION_FD
            and acceptor["listener_fds"] == [3],
            "native worker must corroborate manager-created FD3 and the actual acceptor",
        )
    else:
        require(
            creator["pid"] == process["identity"]["pid"]
            and creator["start_ticks"] == process["identity"]["start_ticks"]
            and creator["uid"] == process["status"]["Uid"][0],
            "Unix listener creator differs from the actual foreground role",
        )


def api_final(value: object, ready: dict[str, Any]) -> None:
    value = exact(
        value,
        {
            "schema_version",
            "fixture_id",
            "generation_id",
            "identity",
            "lifespan_count",
            "instance_id",
            "object_ids",
            "worker_probes",
            "capture",
            "streams",
            "metadata",
            "authentication",
            "runner",
            "async_tasks",
        },
        "actual API final inspection is incomplete",
    )
    require(
        type(value) is dict
        and value.get("lifespan_count") == 1
        and all(
            value.get(key) == ready[key]
            for key in (
                "schema_version",
                "fixture_id",
                "generation_id",
                "instance_id",
                "object_ids",
                "identity",
            )
        ),
        "actual API shutdown changed its lifespan or shared object identity",
    )
    capture, streams = value.get("capture", {}), value.get("streams", {})
    require(
        capture.get("root_descriptor") == -1
        and capture.get("matching_descriptors") == []
        and all(
            type(capture.get(key)) is int and capture[key] == 0
            for key in ("members_remaining", "shells_remaining", "manifest_bytes_remaining")
        )
        and streams.get("active") == 0
        and streams.get("accepting") is False
        and streams.get("owned_tasks") == [],
        "actual captured bytes or stream tasks did not drain",
    )
    metadata, authentication = value.get("metadata", {}), value.get("authentication", {})
    stats = authentication.get("stats", {})
    require(
        metadata.get("inflight") == 0
        and metadata.get("closed") is True
        and all(
            type(stats.get(key)) is int and stats[key] == 0
            for key in ("active", "waiting", "reservations")
        )
        and stats.get("accepting") is False,
        "actual API metadata/authentication admission did not drain",
    )
    runner = value.get("runner", {})
    require(
        runner.get("pending") == 0
        and runner.get("active_operation_id") is None
        and runner.get("accepting") is False
        and runner.get("closing") is True,
        "actual operation runner did not drain",
    )
    for rows, required in (
        (metadata.get("threads"), False),
        (authentication.get("threads"), True),
        (runner.get("thread"), True),
    ):
        require(
            type(rows) is list and len(rows) <= MAXIMUM_THREADS and (bool(rows) or not required),
            "actual executor thread inventory is absent or oversized",
        )
        require(
            all(
                type(row) is dict
                and row.get("alive") is False
                and type(row.get("ident")) is int
                and row["ident"] > 0
                for row in rows
            ),
            "an actual owned executor thread remains alive or unknown",
        )


def selected_browser_engines(runtime: dict[str, Any]) -> tuple[str, ...]:
    if "browser_engine" not in runtime:
        return ("chromium", "firefox", "webkit")
    selected = runtime["browser_engine"]
    require(
        type(selected) is str and selected in ENGINES,
        "functional selected browser engine is invalid",
    )
    return (selected,)


def api_events(
    path: Path,
    identity: dict[str, Any],
    ready: dict[str, Any],
    *,
    stage: str,
    runtime: dict[str, Any] | None = None,
) -> None:
    engines = selected_browser_engines({} if runtime is None else runtime)
    lines = bounded(path).splitlines()
    require(0 < len(lines) <= MAXIMUM_EVENTS, "actual API event inventory is empty or oversized")
    events = [json_bytes(line) for line in lines]
    require(
        all(
            row.get("schema_version") == 1
            and type(row.get("schema_version")) is int
            and row.get("fixture_id") == identity["fixture_id"]
            and row.get("generation_id") == identity["generation_id"]
            for row in events
        ),
        "actual API event invocation identity differs",
    )
    http, lifecycle = [], []
    for row in events:
        if row.get("event") == "http":
            exact(
                row,
                {
                    "schema_version",
                    "fixture_id",
                    "generation_id",
                    "event",
                    "phase",
                    "engine",
                    "actor",
                    "method",
                    "path",
                    "status",
                    "authentication",
                    "instance_id",
                    "request_id",
                },
                "actual HTTP observations contain unsafe or unknown fields",
            )
            require(
                row["phase"] == "trusted"
                and row["instance_id"] == ready["instance_id"]
                and row["actor"] in {"browser", "node", "python-sdk", "unix-client", "readiness"}
                and row["engine"] in {*engines, None}
                and type(row["status"]) is int
                and HTTPStatus.CONTINUE <= row["status"] <= MAXIMUM_HTTP_STATUS
                and isinstance(row["path"], str)
                and row["path"].startswith("/")
                and "?" not in row["path"]
                and len(row["path"].encode()) <= MAXIMUM_EVENTS,
                "untrusted browser reached HTTP or actual API observation is invalid",
            )
            http.append(row)
        elif row.get("event") == "lifecycle":
            exact(
                row,
                {
                    "schema_version",
                    "fixture_id",
                    "generation_id",
                    "event",
                    "phase",
                    "pid",
                    "start_ticks",
                    "instance_id",
                    "capture_fingerprint",
                    "capture_descriptor_open",
                    "streams_active",
                    "streams_accepting",
                    "metadata_inflight",
                    "metadata_closed",
                    "auth_active",
                    "auth_waiting",
                    "auth_reservations",
                    "auth_accepting",
                    "auth_workers",
                    "auth_workers_joined",
                    "operations_active",
                    "worker_available",
                },
                "actual lifecycle observation contains unsafe or unknown fields",
            )
            require(
                row.get("phase") in {"started", "draining", "stopped"}
                and row.get("instance_id") == ready["instance_id"]
                and all(row.get(key) == ready["identity"][key] for key in ("pid", "start_ticks")),
                "actual API lifecycle observation is invalid",
            )
            lifecycle.append(row)
        else:
            reject("actual API observation kind is unsupported")
    require(
        [row["phase"] for row in lifecycle]
        == (["started", "draining", "stopped"] if stage == "stopped" else ["started"]),
        "actual API lifespan did not enter and drain exactly once",
    )
    if stage != "stopped":
        return
    final = lifecycle[-1]
    require(
        final["capture_descriptor_open"] is False
        and final["streams_accepting"] is False
        and final["metadata_closed"] is True
        and final["auth_accepting"] is False
        and final["auth_workers_joined"] is True
        and all(
            type(final[key]) is int and final[key] == 0
            for key in (
                "streams_active",
                "metadata_inflight",
                "auth_active",
                "auth_waiting",
                "auth_reservations",
                "operations_active",
            )
        ),
        "actual API stopped event did not prove resource drain",
    )
    for engine in engines:
        rows = [
            {**row, "path": row["path"].removeprefix(identity["prefix"])}
            for row in http
            if row["engine"] == engine and row["actor"] == "browser"
        ]
        require(
            any(
                row["path"] == "/ui"
                and row["status"] == HTTPStatus.UNAUTHORIZED
                and row["authentication"] == "none"
                for row in rows
            )
            and any(
                row["path"] == "/ui"
                and row["status"] == HTTPStatus.TEMPORARY_REDIRECT
                and row["authentication"] == "basic"
                for row in rows
            )
            and any(
                row["path"] == "/ui/"
                and row["status"] == HTTPStatus.OK
                and row["authentication"] == "basic"
                for row in rows
            ),
            "actual native browser challenge and authenticated UI were not observed",
        )
        require(
            any(
                row["path"] == "/api/v1/config/validate"
                and row["method"] == "POST"
                and row["status"] == HTTPStatus.OK
                and row["authentication"] == "basic"
                for row in rows
            ),
            "actual same-origin Basic JSON validation was not observed",
        )
        node = [
            {**row, "path": row["path"].removeprefix(identity["prefix"])}
            for row in http
            if row["engine"] == engine and row["actor"] == "node"
        ]
        require(
            any(
                row["path"].startswith("/api/")
                and row["authentication"] == "rest-reader"
                and row["status"] == HTTPStatus.OK
                for row in node
            )
            and sum(
                row["path"] == "/mcp/"
                and row["method"] == "POST"
                and row["authentication"] == "mcp-reader"
                and row["status"] == HTTPStatus.OK
                for row in node
            )
            >= len(MCP_TOOLS),
            "actual simultaneous bearer REST and all MCP calls were not observed",
        )


def caddy_listeners(value: object, *, profile: str, origin: str) -> None:
    """Validate closed raw kernel rows without changing family, address or order."""
    require(
        type(profile) is str
        and profile in {"application", "native", "rootless"}
        and type(origin) is str,
        "actual Caddy listener profile or origin is unknown",
    )
    if type(value) is not list or len(value) not in {1, 2}:
        reject("actual Caddy listener inventory is incomplete or contains extra sockets")
    rows = [
        exact(
            row,
            {"protocol", "address", "port", "kernel_inode"},
            "actual Caddy listener row is not closed kernel metadata",
        )
        for row in value
    ]
    port = 8443 if profile == "rootless" else urlsplit(origin).port
    for row in rows:
        require(
            type(row["protocol"]) is str
            and type(row["address"]) is str
            and type(row["port"]) is int
            and row["port"] == port
            and type(row["kernel_inode"]) is int
            and row["kernel_inode"] > 0,
            "actual Caddy listener port, address or kernel identity is unproved",
        )
    protocols = {row["protocol"] for row in rows}
    require(
        len(protocols) == len(rows) and len({row["kernel_inode"] for row in rows}) == len(rows),
        "actual Caddy listener protocols or kernel inodes are duplicated",
    )
    ipv6 = profile == "rootless" and bool(protocols & {"tcp6", "udp6"})
    tcp, udp = ("tcp6", "udp6") if ipv6 else ("tcp", "udp")
    address = ("::" if ipv6 else "0.0.0.0") if profile == "rootless" else "127.0.0.1"  # noqa: S104 - container wildcard; host loopback publication is checked independently
    require(
        tcp in protocols
        and protocols <= {tcp, udp}
        and all(row["address"] == address for row in rows),
        "actual Caddy listener escaped its single closed address family and origin",
    )


def detailed_role_evidence(item: dict[str, Any], manifest: dict[str, Any], *, stage: str) -> None:  # noqa: PLR0915 - cross-role identity assertions stay together for audit
    proofs = {
        name: json_bytes(bounded(file_record(record))) for name, record in item["proofs"].items()
    }
    processes = {}
    for name, proof in proofs.items():
        require(
            all(
                proof.get(key) == item[key]
                for key in (
                    "schema_version",
                    "fixture_id",
                    "generation_id",
                    "profile",
                    "prefix",
                    "origin",
                    "stage",
                )
            )
            and proof.get("role") == name,
            "detailed role evidence changed invocation identity",
        )
        if name == "network":
            continue
        if name == "helper":
            helper_process(proof.get("process"))
            require(
                proof.get("process_gone") is False and proof.get("cgroup_empty") is False,
                "the original installed helper must remain a live prerequisite",
            )
            continue
        processes[name] = role_process(
            proof.get("process"),
            name,
            item["profile"],
            expected_uid=(
                native_principal(
                    name,
                    caddy_account=manifest["profiles"][item["profile"]]["caddy_account"],
                )
                if current_release(manifest) and item["profile"] != "rootless"
                else None
            ),
        )
        if item["profile"] == "rootless":
            role_container(proof.get("container"), processes[name], manifest, name, stage=stage)
        else:
            unit = proof.get("unit", {})
            require(
                unit.get("MainPID") == str(processes[name]["identity"]["pid"])
                and isinstance(unit.get("InvocationID"), str)
                and IDENTIFIER.fullmatch(unit["InvocationID"])
                and unit.get("NoNewPrivileges") == "yes"
                and unit.get("CapabilityBoundingSet") == unit.get("AmbientCapabilities") == ""
                and unit.get("ProtectSystem") == "strict",
                "actual native role systemd identity or hardening differs",
            )
            if current_release(manifest):
                require(
                    unit.get("User")
                    == unit.get("Group")
                    == (
                        manifest["profiles"][item["profile"]]["caddy_account"]
                        if name == "caddy"
                        else "hfcache"
                    ),
                    "actual native role does not use its fixed service account",
                )
        require(
            proof.get("process_gone") is (stage == "stopped")
            and proof.get("cgroup_empty") is (stage == "stopped"),
            "detailed role PID and cgroup drain is unknown",
        )
    require(
        len({process["identity"]["pid"] for process in processes.values()}) == len(DEPLOYMENTS),
        "API, Caddy and verification worker must be distinct actual processes",
    )
    if current_release(manifest):
        installed_role_evidence(proofs, manifest)
    api, worker, caddy = (proofs[name] for name in ("api", "worker", "caddy"))
    unix_listener(api.get("listener"), processes["api"], worker=False, profile=item["profile"])
    unix_listener(worker.get("listener"), processes["worker"], worker=True, profile=item["profile"])
    origin_probe(
        worker.get("origin_probe"),
        processes["worker"],
        "worker",
        item["profile"],
        network=proofs["network"],
        worker=worker,
        manifest=manifest,
        invocation=item,
    )
    origin_probe(caddy.get("origin_probe"), processes["caddy"], "caddy", item["profile"])
    require(
        caddy.get("upstream") == api["listener"] and api.get("inet_listeners") == [],
        "single Caddy upstream must bind the actual Unix-only API",
    )
    require(
        api.get("native_projection")
        == {
            "rest_status": HTTPStatus.OK,
            "mcp_alias_status": HTTPStatus.TEMPORARY_REDIRECT,
            "mcp_alias_location": "/mcp/",
        },
        "original Unix REST and MCP alias compatibility is unproved",
    )
    caddy_listeners(caddy.get("listener"), profile=item["profile"], origin=item["origin"])
    require(
        caddy.get("template") == manifest["profiles"][item["profile"]]["caddy_config"],
        "actual Caddy configuration did not use the pinned immutable input template",
    )
    rendered = bounded(file_record(caddy.get("config")))
    template = bounded(file_record(caddy["template"]))
    upstream = (
        api["listener"]["acceptor"]["process_path"]
        if item["profile"] == "rootless"
        else api["listener"]["path"]
    )
    markers = (b"__API_SOCKET__", b"__TLS_CERTIFICATE__", b"__TLS_PRIVATE_KEY__")
    pattern = re.escape(template)
    for number, marker in enumerate(markers):
        pattern = pattern.replace(
            re.escape(marker), (f"(?P<path{number}>/[A-Za-z0-9/._-]+)").encode()
        )
    applied = re.fullmatch(pattern, rendered)
    require(
        all(template.count(marker) == 1 for marker in markers)
        and applied
        and applied["path0"] == upstream.encode()
        and all(
            not any(part in {b"", b".", b".."} for part in applied[f"path{number}"].split(b"/")[1:])
            for number in range(len(markers))
        )
        and b"basic_auth" not in rendered
        and b"handle_path" not in rendered,
        "applied Caddy configuration is not the original path-preserving template",
    )
    if item["profile"] == "rootless":
        source = api["listener"].get("source_path", api["listener"]["path"])
        require(
            any(
                mount["source"] == str(Path(source).parent)
                and mount["destination"] == str(Path(upstream).parent)
                and mount["read_only"] is True
                for mount in caddy["container"]["mounts"]
            ),
            "Caddy upstream lacks the actual read-only bind of the observed API socket inode",
        )
    ready_record = exact(
        api.get("ready"), {"record", "body"}, "actual API startup proof is missing"
    )
    ready = json_bytes(bounded(file_record(ready_record["record"])))
    runtime = json_bytes(bounded(path_input(str(Path(item["workspace"]) / "runtime.json"))))
    require(
        ready == ready_record["body"]
        and ready.get("lifespan_count") == 1
        and all(
            ready.get(key) == item[key] for key in ("schema_version", "fixture_id", "generation_id")
        )
        and ready.get("capture_fingerprint") == manifest["assets"]["manifest_sha256"]
        and ready.get("phase_identity")
        == [runtime["phase_identity"]["device"], runtime["phase_identity"]["inode"]]
        and ready.get("identity")
        == {
            "pid": processes["api"]["status"]["NSpid"][-1],
            "start_ticks": processes["api"]["identity"]["start_ticks"],
        }
        and isinstance(ready.get("instance_id"), str)
        and IDENTIFIER.fullmatch(ready["instance_id"]),
        "actual API startup identity or single lifespan is unproved",
    )
    buffer = exact(
        ready.get("socket_send_buffer"),
        {"requested", "observed", "listeners"},
        "actual owned Unix backpressure injection is unproved",
    )
    require(
        buffer["requested"] == FIXTURE_SEND_BUFFER_REQUESTED
        and buffer["observed"] == FIXTURE_SEND_BUFFER_OBSERVED
        and type(buffer["listeners"]) is list
        and len(buffer["listeners"]) == 1
        and buffer["listeners"][0].get("family") == "unix"
        and type(buffer["listeners"][0].get("descriptor")) is int
        and buffer["listeners"][0]["descriptor"] >= 0
        and buffer["listeners"][0].get("requested") == FIXTURE_SEND_BUFFER_REQUESTED
        and buffer["listeners"][0].get("observed") == FIXTURE_SEND_BUFFER_OBSERVED,
        "actual fixture Unix socket send buffer differs from its controlled finite setting",
    )
    transfer_path = file_record(api.get("transfers"))
    if stage == "ready":
        require(
            bounded(transfer_path) == b"", "transfer fixture was not fresh before browser execution"
        )
    objects = exact(
        ready.get("object_ids"),
        {"store", "pool", "runner", "verifier", "capture", "streams"},
        "actual API shared-object inventory is incomplete",
    )
    require(
        all(type(value) is int and value > 0 for value in objects.values())
        and len(set(objects.values())) == len(objects),
        "actual API shared objects are invalid",
    )
    probes = ready.get("worker_probes", [])
    require(
        probes
        and probes[0].get("available") is True
        and probes[0].get("api_identity") == ready["identity"]
        and probes[0].get("verifier_object_id") == objects["verifier"]
        and worker.get("api_protocol_probe") == probes[0],
        "worker availability must come from the actual API-owned original protocol client",
    )
    api_events(file_record(api.get("events")), item, ready, stage=stage, runtime=runtime)
    require(
        proofs["network"].get("controlled_listeners_closed") is True,
        "owned IP probe endpoint listeners did not drain",
    )
    if stage == "stopped":
        final = exact(api.get("final"), {"record", "body"}, "actual API shutdown proof is missing")
        body = json_bytes(bounded(file_record(final["record"])))
        require(body == final["body"], "actual API final proof differs from its retained bytes")
        api_final(body, ready)


def cap_drop_all(value: object) -> bool:
    """Keep raw metadata; accept literal ALL or the measured expanded capability list."""
    expanded = {
        "CAP_CHOWN",
        "CAP_DAC_OVERRIDE",
        "CAP_FOWNER",
        "CAP_FSETID",
        "CAP_KILL",
        "CAP_NET_BIND_SERVICE",
        "CAP_SETFCAP",
        "CAP_SETGID",
        "CAP_SETPCAP",
        "CAP_SETUID",
        "CAP_SYS_CHROOT",
    }
    return (
        type(value) is list
        and len(value) in {1, len(expanded)}
        and all(type(item) is str for item in value)
        and (value == ["ALL"] or (len(value) == len(expanded) and set(value) == expanded))
    )


def role_container(
    value: object, process: dict[str, Any], manifest: dict[str, Any], role: str, *, stage: str
) -> None:
    item = exact(
        value,
        {
            "schema_version",
            "engine",
            "id",
            "name",
            "image_sha256",
            "init_identity",
            "running",
            "exit_code",
            "user",
            "userns",
            "network_mode",
            "read_only_rootfs",
            "privileged",
            "cap_drop",
            "security_opt",
            "mounts",
            "published_ports",
            "manager_unit",
            "cgroup",
            "owned_processes",
            "owned_cgroups",
        },
        "actual rootless container inspection is incomplete",
    )
    modern = current_release(manifest)
    host_uid = native_principal("api") if modern else 1000
    inner_uid = container_principal(manifest, role) if modern else 981
    uid_mapping(process, host_uid=host_uid, container_uid=inner_uid)
    engine = (
        "podman-rootless-" + manifest["profiles"]["rootless"]["storage_driver"]
        if modern
        else "podman-rootless-vfs"
    )
    require(
        type(item["schema_version"]) is int
        and item["schema_version"] == 1
        and item["engine"] == engine
        and isinstance(item["id"], str)
        and SHA256.fullmatch(item["id"])
        and item["image_sha256"] == manifest["profiles"]["rootless"][role + "_image_sha256"]
        and item["init_identity"]
        == {key: process["identity"][key] for key in ("pid", "start_ticks")}
        and item["user"] == f"{inner_uid}:{inner_uid}"
        and item["userns"] == f"keep-id:uid={inner_uid},gid={inner_uid}"
        and item["read_only_rootfs"] is True
        and item["privileged"] is False
        and cap_drop_all(item["cap_drop"])
        and process["status"].get("CapEff") == process["status"].get("CapBnd") == "0" * 16
        and item["running"] is (stage != "stopped")
        and (
            type(item["exit_code"]) is int and item["exit_code"] == 0
            if stage == "stopped"
            else item["exit_code"] is None
        )
        and item["network_mode"] == ("none" if role == "worker" else "pasta")
        and type(item["security_opt"]) is list
        and any(
            option in {"no-new-privileges", "no-new-privileges=true"}
            for option in item["security_opt"]
        ),
        "actual rootless container image, identity, privilege or lifecycle differs",
    )
    mounts = item["mounts"]
    require(
        type(mounts) is list and 0 < len(mounts) <= MAXIMUM_THREADS,
        "actual rootless mount inventory is absent",
    )
    for mount in mounts:
        exact(mount, {"source", "destination", "read_only"}, "actual rootless mount is malformed")
        require(
            all(
                isinstance(mount[key], str)
                and mount[key].startswith("/")
                and ".." not in mount[key].split("/")
                for key in ("source", "destination")
            )
            and type(mount["read_only"]) is bool,
            "actual rootless mount identity is unsafe",
        )
    ports = item["published_ports"]
    expected = (
        [
            {
                "host_ip": "127.0.0.1",
                "host_port": urlsplit(manifest["profiles"]["rootless"]["origin"]).port,
                "container_port": 8443,
                "protocol": "tcp",
            }
        ]
        if role == "caddy"
        else []
    )
    require(ports == expected, "actual rootless publication escaped the owned Caddy loopback port")
    identities = item["owned_processes"]
    require(
        type(identities) is list and 0 < len(identities) <= MAXIMUM_THREADS,
        "actual rootless owned process inventory is missing",
    )
    for identity in identities:
        exact(
            identity, {"pid", "start_ticks", "gone"}, "actual rootless owned identity is malformed"
        )
        require(
            type(identity["pid"]) is int
            and identity["pid"] > 1
            and isinstance(identity["start_ticks"], str)
            and identity["start_ticks"].isdigit()
            and identity["gone"] is (stage == "stopped"),
            "actual rootless owned process drain is unknown",
        )
    require(
        any(
            {key: identity[key] for key in ("pid", "start_ticks")} == item["init_identity"]
            for identity in identities
        ),
        "rootless init disappeared from its owned process inventory",
    )
    groups = item["owned_cgroups"]
    require(
        type(groups) is list and 0 < len(groups) <= MAXIMUM_THREADS,
        "actual rootless owned cgroup inventory is missing",
    )
    for group in groups:
        exact(group, {"path", "pids"}, "actual rootless owned cgroup is malformed")
        require(
            isinstance(group["path"], str)
            and group["path"].startswith("/user.slice/")
            and ".." not in group["path"].split("/")
            and type(group["pids"]) is list
            and (group["pids"] == [] if stage == "stopped" else bool(group["pids"])),
            "actual rootless owned cgroup drain is unknown",
        )
    rootless_manager(item, role, stage=stage, current=modern, host_uid=host_uid)


def rootless_manager(
    item: dict[str, Any], role: str, *, stage: str, current: bool = False, host_uid: int = 1000
) -> None:
    """Normal shutdown policy and its exact manager survive unit garbage collection."""
    manager = item["manager_unit"]
    if stage == "stopped":
        wrapper = exact(
            manager,
            {"before_stop", "after_stop"},
            "rootless manager drain snapshots are incomplete",
        )
        manager = wrapper["before_stop"]
    manager = exact(
        manager,
        {
            "Id",
            "MainPID",
            "InvocationID",
            "ControlGroup",
            "ActiveState",
            "SubState",
            "ExecMainCode",
            "ExecMainStatus",
            "Type",
            "KillMode",
            "SendSIGKILL",
            "TimeoutStopUSec",
            "StandardOutput",
            "StandardError",
        },
        "rootless manager policy inspection is incomplete",
    )
    require(
        isinstance(item["name"], str)
        and (
            item["name"]
            == {"api": "hfcache-api", "worker": "hfcache-verification", "caddy": "hfcache-caddy"}[
                role
            ]
            if current
            else re.fullmatch(r"web005-[a-f0-9]{32}-rootless-" + role, item["name"])
        )
        and all(isinstance(value, str) for value in manager.values())
        and manager["Id"] == item["name"] + ".service"
        and re.fullmatch(r"[0-9]+", manager["MainPID"])
        and int(manager["MainPID"]) > 1
        and IDENTIFIER.fullmatch(manager["InvocationID"])
        and manager["ActiveState"] == "active"
        and manager["SubState"] == "running"
        and manager["Type"] == ("notify" if role == "worker" else "exec")
        and manager["KillMode"] == "mixed"
        and manager["SendSIGKILL"] == "no"
        and manager["TimeoutStopUSec"] == "infinity"
        and manager["StandardOutput"] == manager["StandardError"] == "journal"
        and manager["ExecMainCode"] in {"0", "1"}
        and manager["ExecMainStatus"] == "0"
        and manager["ControlGroup"].startswith(f"/user.slice/user-{host_uid}.slice/")
        and manager["ControlGroup"].rsplit("/", 1)[-1] == manager["Id"]
        and any(row["pid"] == int(manager["MainPID"]) for row in item["owned_processes"])
        and any(
            row["path"] == manager["ControlGroup"]
            and (
                row["pids"] == [] if stage == "stopped" else int(manager["MainPID"]) in row["pids"]
            )
            for row in item["owned_cgroups"]
        ),
        "actual rootless manager identity or normal no-force shutdown policy differs",
    )
    if stage == "stopped":
        final = exact(
            item["manager_unit"]["after_stop"],
            {"Id", "LoadState", "ActiveState", "SubState", "MainPID", "ControlGroup", "Result"},
            "actual rootless manager final state is incomplete",
        )
        require(
            all(isinstance(value, str) for value in final.values())
            and final["Id"] == manager["Id"]
            and final["LoadState"] in {"loaded", "not-found"}
            and final["ActiveState"] == "inactive"
            and final["SubState"] == "dead"
            and final["MainPID"] == "0"
            and final["ControlGroup"] == ""
            and final["Result"] in {"", "success"},
            "actual rootless manager remains live or its stop failed",
        )


def bind_role_generation(
    ready: dict[str, Any],
    stopped: dict[str, Any],
    *,
    read_record: Callable[[object], dict[str, Any]] | None = None,
) -> None:
    def read(value: object) -> dict[str, Any]:
        return (
            json_bytes(bounded(file_record(value))) if read_record is None else read_record(value)
        )

    require(
        ready["generation_id"] == stopped["generation_id"],
        "functional role cleanup changed generation identity",
    )
    for role in ("api", "worker", "caddy"):
        before = read(ready["proofs"][role])
        after = read(stopped["proofs"][role])
        require(
            before["process"] == after["process"],
            "functional drain dropped or changed the originally observed role process",
        )
        if ready["profile"] == "rootless":
            old, new = before["container"], after["container"]
            require(
                old["id"] == new["id"]
                and old["init_identity"] == new["init_identity"]
                and {(row["pid"], row["start_ticks"]) for row in old["owned_processes"]}
                == {(row["pid"], row["start_ticks"]) for row in new["owned_processes"]}
                and {row["path"] for row in old["owned_cgroups"]}
                == {row["path"] for row in new["owned_cgroups"]},
                "rootless drain dropped an originally owned process, cgroup or container",
            )
    if "helper" in ready["proofs"] or "helper" in stopped["proofs"]:
        require(
            "helper" in ready["proofs"] and "helper" in stopped["proofs"],
            "original installed helper observation disappeared",
        )
        before = read(ready["proofs"]["helper"])
        after = read(stopped["proofs"]["helper"])
        old_process, new_process = before["process"], after["process"]
        old_authority, new_authority = before["authority"], after["authority"]
        require(
            all(old_process[key] == new_process[key] for key in old_process if key != "identity")
            and all(
                old_process["identity"][key] == new_process["identity"][key]
                for key in ("pid", "parent_pid", "start_ticks")
            )
            and all(
                before["unit"][key] == after["unit"][key]
                for key in ("MainPID", "InvocationID", "ControlGroup", "NoNewPrivileges")
            )
            and before["bootstrap"] == after["bootstrap"]
            and before["deployment"] == after["deployment"]
            and all(
                old_authority[key] == new_authority[key]
                for key in old_authority
                if key != "key_parent"
            )
            and all(
                old_authority["key_parent"][key] == new_authority["key_parent"][key]
                for key in ("st_dev", "st_ino", "st_mode", "st_uid", "st_gid")
            )
            and before["process_gone"] is after["process_gone"] is False
            and before["cgroup_empty"] is after["cgroup_empty"] is False,
            "original live helper identity, selected bytes or authority changed",
        )


def role_context(  # noqa: PLR0913 - all invocation identity fields are independent obligations
    value: object,
    *,
    manifest: dict[str, Any],
    profile: str,
    workspace: Path,
    prefix: str,
    stage: str,
) -> dict[str, Any]:
    item = exact(
        value,
        {
            "schema_version",
            "fixture_id",
            "generation_id",
            "profile",
            "workspace",
            "prefix",
            "stage",
            "origin",
            "checks",
            "drains",
            "proofs",
        },
        "functional role evidence is malformed",
    )
    require(
        type(item["schema_version"]) is int
        and item["schema_version"] == 1
        and item["fixture_id"] == manifest["fixture_id"]
        and item["profile"] == profile
        and item["workspace"] == str(workspace)
        and item["prefix"] == prefix
        and item["stage"] == stage
        and isinstance(item["generation_id"], str)
        and IDENTIFIER.fullmatch(item["generation_id"])
        and item["origin"] == manifest["profiles"][profile]["origin"],
        "functional role evidence does not bind this invocation",
    )
    checks = exact(item["checks"], ROLE_CHECKS, "functional role checks are incomplete")
    require(
        all(value is True for value in checks.values()),
        "actual native/rootless role or worker confinement is not proven",
    )
    require(
        type(item["proofs"]) is dict
        and set(item["proofs"])
        == {"api", "caddy", "worker", "network"}
        | ({"helper"} if current_release(manifest) else set()),
        "actual role inspection artifacts are incomplete",
    )
    if stage == "stopped":
        drains = exact(item["drains"], ROLE_DRAINS, "actual functional role drains are incomplete")
        require(
            all(value is True for value in drains.values()),
            "actual functional role drain is unknown",
        )
    else:
        require(item["drains"] == {}, "ready role evidence cannot claim future process drains")
    return item


def successful_browser_assertions(value: object) -> set[str]:
    require(type(value) is list, "functional browser assertion records are missing")
    assert isinstance(value, list)
    seen: set[str] = set()
    passed: set[str] = set()
    for row in value:
        require(
            type(row) is dict
            and isinstance(row.get("id"), str)
            and row["id"] in BROWSER_CASES
            and row["id"] not in seen
            and type(row.get("passed")) is bool
            and type(row.get("attempts")) is int
            and row["attempts"] == 1,
            "functional browser assertion is unknown, duplicated, malformed or retried",
        )
        seen.add(row["id"])
        if row["passed"]:
            passed.add(row["id"])
    return passed


def role_evidence(  # noqa: PLR0913 - independent original invocation fields
    value: object,
    *,
    manifest: dict[str, Any],
    profile: str,
    workspace: Path,
    prefix: str,
    stage: str,
) -> dict[str, Any]:
    item = role_context(
        value, manifest=manifest, profile=profile, workspace=workspace, prefix=prefix, stage=stage
    )
    detailed_role_evidence(item, manifest, stage=stage)
    return item


def basic_read_refusals(value: object, *, prefix: str, origin: str) -> None:
    require(
        type(value) is list and len(value) == len(BASIC_READ_REFUSALS),
        "functional Basic read refusal observations are incomplete",
    )
    assert isinstance(value, list)
    expected_problem = hashlib.sha256(
        b'{"code":"HFAPI001","message":"Not authenticated","exit_code":10}'
    ).hexdigest()
    labels, requests = set(), set()
    for item in value:
        row = exact(
            item,
            {
                "label",
                "status",
                "code",
                "request_id",
                "authorization_fields",
                "body_bytes",
                "body_sha256",
                "problem_sha256",
                "method",
                "path",
                "origin",
                "transport",
            },
            "functional Basic read refusal contains unsafe or unknown fields",
        )
        label = row["label"]
        require(
            type(label) is str
            and label in BASIC_READ_REFUSALS
            and label not in labels
            and type(row["status"]) is int
            and row["status"] == HTTPStatus.UNAUTHORIZED
            and row["code"] == "HFAPI001"
            and isinstance(row["request_id"], str)
            and IDENTIFIER.fullmatch(row["request_id"])
            and row["request_id"] not in requests
            and type(row["authorization_fields"]) is int
            and row["authorization_fields"] == BASIC_READ_REFUSALS[label]
            and type(row["body_bytes"]) is int
            and 0 < row["body_bytes"] <= MAXIMUM_BASIC_REFUSAL_BYTES
            and isinstance(row["body_sha256"], str)
            and SHA256.fullmatch(row["body_sha256"])
            and row["problem_sha256"] == expected_problem
            and row["method"] == "GET"
            and row["path"] == prefix + "/api/v1/version"
            and row["origin"] == origin
            and row["transport"] == "trusted-node-https",
            "functional Basic read refusal identity, bounds or classification differs",
        )
        labels.add(label)
        requests.add(row["request_id"])


def browser_evidence(
    value: object, *, manifest: dict[str, Any], runtime: dict[str, Any]
) -> dict[str, Any]:
    item = exact(
        value,
        {"schema_version", "fixture_id", "profile", "prefix", "asset_manifest_sha256", "engines"}
        | ({"run_id"} if "run_id" in runtime else set()),
        "functional browser report is malformed",
    )
    require(
        type(item["schema_version"]) is int
        and item["schema_version"] == 1
        and ("run_id" not in runtime or item["run_id"] == runtime["run_id"])
        and item["fixture_id"] == manifest["fixture_id"]
        and item["profile"] == runtime["profile"]
        and item["prefix"] == runtime["prefix"]
        and item["asset_manifest_sha256"] == manifest["assets"]["manifest_sha256"]
        and type(item["engines"]) is dict
        and set(item["engines"]) == set(selected_browser_engines(runtime)),
        "functional browser identity is incomplete",
    )
    for name, engine in item["engines"].items():
        require(
            type(engine) is dict and type(engine.get("cases")) is list,
            "functional browser cases are missing",
        )
        require(
            engine.get("instance_id") == runtime["instance_id"],
            "actual browser bootstrap and installed API instance differ",
        )
        passed = successful_browser_assertions(engine["cases"])
        require(
            passed >= BASELINE_BROWSER_CASES and len(passed) == len(engine["cases"]),
            "functional browser required case failed, retried or was omitted",
        )
        require(
            not passed - BASELINE_BROWSER_CASES
            or (runtime["profile"] == "native" and runtime.get("browser_engine") == name),
            "optional rich read requires its explicitly selected native engine",
        )
        require(
            engine.get("page_errors") == []
            and engine.get("failed_responses") == []
            and not engine.get("browser_error_overflow"),
            "functional browser observed application errors or failed responses",
        )
        basic_read_refusals(
            engine.get("basic_read_refusals"),
            prefix=runtime["prefix"],
            origin=manifest["profiles"][runtime["profile"]]["origin"],
        )
        require(
            engine.get("browser_closed") is True
            and engine.get("descendants_closed") is True
            and not engine.get("infrastructure_failed")
            and not engine.get("descendant_inventory_unknown"),
            "functional browser lifecycle is not proved",
        )
        network = engine.get("network_observation", {})
        require(
            network.get("mode") == "passive-origin-observer"
            and network.get("request_interception") is False
            and network.get("invalid") is False
            and network.get("overflow") is False
            and type(network.get("request_count")) is int
            and 0 < network["request_count"] <= MAXIMUM_BROWSER_REQUESTS,
            "functional browser network confinement is unproved",
        )
        require(
            set(engine.get("mcp_tools", {})) == MCP_TOOLS
            and all(
                result.get("passed") is True
                and result.get("browser_active") is True
                and result.get("origin") == manifest["profiles"][runtime["profile"]]["origin"]
                and isinstance(result.get("request_id"), str)
                and IDENTIFIER.fullmatch(result["request_id"])
                and result.get("outcome") in {"success", "success_with_warnings"}
                for result in engine["mcp_tools"].values()
            ),
            "functional browser did not exercise all fourteen actual MCP tools",
        )
        expected_origin = manifest["profiles"][runtime["profile"]]["origin"]
        require(
            network.get("expected_origins") == {"trusted": expected_origin}
            and type(network.get("observations")) is list
            and len(network["observations"]) == network["request_count"],
            "functional passive observation identities are incomplete",
        )
        for observed in network["observations"]:
            require(
                observed
                == {
                    "category": "trusted",
                    "scheme": "https:",
                    "host": "127.0.0.1",
                    "port": urlsplit(expected_origin).port,
                },
                "functional browser observed an unexpected or unsafe origin",
            )
        browser_process_evidence(engine, name)
        static_abort_evidence(engine.get("static_abort"), runtime)
        negative = engine.get("untrusted_phase", {})
        require(
            type(negative) is dict
            and negative.get("certificate_refused") is True
            and negative.get("browser_closed") is True
            and negative.get("descendants_closed") is True
            and not negative.get("infrastructure_failed")
            and not negative.get("descendant_inventory_unknown")
            and negative.get("cases")
            and len(negative["cases"]) == 1
            and negative["cases"][0].get("id") == "untrusted-certificate-refused"
            and negative["cases"][0].get("passed") is True
            and type(negative["cases"][0].get("attempts")) is int
            and negative["cases"][0]["attempts"] == 1,
            "functional untrusted phase lacks actual certificate refusal and drain",
        )
        browser_process_evidence(negative, name)
    return item


def static_abort_evidence(value: object, runtime: dict[str, Any]) -> None:
    item = exact(
        value,
        {"member", "head", "browser_cancels", "cancel", "deadline", "concurrent_bearer"},
        "actual static cancellation evidence is incomplete",
    )
    artifact = runtime["asset_manifest"]
    candidates = [
        member
        for member in artifact["members"]
        if member["mime"] == "text/javascript" and member["bytes"] > 0
    ]
    require(
        candidates, "static cancellation requires an actual nonempty production JavaScript asset"
    )
    member = max(candidates, key=lambda candidate: candidate["bytes"])
    require(
        item["member"] == {key: member[key] for key in ("path", "bytes", "sha256")},
        "static cancellation changed the production artifact member",
    )
    head = item["head"]
    require(
        type(head) is dict
        and head.get("status") == HTTPStatus.OK
        and type(head.get("bytes")) is int
        and head["bytes"] == 0
        and isinstance(head.get("request_id"), str)
        and IDENTIFIER.fullmatch(head["request_id"]),
        "actual authenticated HEAD did not preserve its original request identity or empty body",
    )
    rows = item["browser_cancels"]
    require(
        type(rows) is list and len(rows) == STATIC_BROWSER_CANCELS,
        "actual browser cancellation attempts are incomplete",
    )
    for row in rows:
        exact(
            row,
            {
                "status",
                "request_id",
                "read_bytes",
                "first_read_done",
                "reader_cancelled",
                "controller_aborted",
            },
            "actual browser cancellation record is malformed",
        )
        require(
            row["status"] == HTTPStatus.OK
            and isinstance(row["request_id"], str)
            and IDENTIFIER.fullmatch(row["request_id"])
            and type(row["read_bytes"]) is int
            and 0 < row["read_bytes"] <= member["bytes"]
            and type(row["first_read_done"]) is bool
            and row["reader_cancelled"] is True
            and row["controller_aborted"] is True,
            "actual browser read/cancel/abort was not executed",
        )
    request_ids = [head["request_id"], *(row["request_id"] for row in rows)]
    for mode in ("cancel", "deadline"):
        probe = exact(
            item[mode],
            {
                "mode",
                "origin",
                "path",
                "initial_window_size",
                "push_enabled",
                "settings_acknowledged",
                "received_bytes",
                "client_cancel_after_ms",
                "observed_ms",
                "remote_closed",
                "stream_closed",
                "session_closed",
                "request_id",
                "status",
            },
            "actual HTTP2 stall evidence is incomplete",
        )
        require(
            probe["mode"] == mode
            and probe["origin"] == runtime["origin"]
            and probe["path"] == runtime["prefix"] + "/ui/" + member["path"]
            and type(probe["initial_window_size"]) is int
            and probe["initial_window_size"] == 0
            and probe["push_enabled"] is False
            and probe["settings_acknowledged"] is True
            and type(probe["received_bytes"]) is int
            and probe["received_bytes"] == 0
            and probe["stream_closed"] is True
            and probe["session_closed"] is True
            and probe["status"] == HTTPStatus.OK
            and isinstance(probe["request_id"], str)
            and IDENTIFIER.fullmatch(probe["request_id"])
            and type(probe["observed_ms"]) in {int, float}
            and 0 <= probe["observed_ms"] < MAXIMUM_PROBE_MS,
            "actual HTTP2 settings, zero-window, identity or drain is unproved",
        )
        if mode == "cancel":
            require(
                probe["remote_closed"] is False
                and type(probe["client_cancel_after_ms"]) in {int, float}
                and MINIMUM_CANCEL_NS / NANOSECONDS_PER_MILLISECOND
                <= probe["client_cancel_after_ms"]
                < MAXIMUM_CANCEL_NS / NANOSECONDS_PER_MILLISECOND,
                "completion won the zero-window cancellation race",
            )
        else:
            require(
                (
                    probe["remote_closed"] is True
                    and probe["client_cancel_after_ms"] is None
                    and probe["observed_ms"] >= MINIMUM_REMOTE_DEADLINE_MS
                )
                or (
                    probe["remote_closed"] is False
                    and type(probe["client_cancel_after_ms"]) in {int, float}
                    and MINIMUM_CLIENT_DEADLINE_MS
                    <= probe["client_cancel_after_ms"]
                    < MAXIMUM_PROBE_MS
                ),
                "deadline probe was cancelled before the original server deadline",
            )
        request_ids.append(probe["request_id"])
    require(
        len(request_ids) == len(set(request_ids)),
        "static probes reused original request identities",
    )
    bearer = item["concurrent_bearer"]
    require(
        type(bearer) is dict
        and bearer.get("status") == HTTPStatus.OK
        and bearer.get("browser_active") is True
        and bearer.get("instance_id") == runtime["instance_id"]
        and isinstance(bearer.get("request_id"), str)
        and IDENTIFIER.fullmatch(bearer["request_id"]),
        "concurrent original bearer read was not observed",
    )


def transfer_protocol(value: object, ready: dict[str, Any]) -> dict[str, Any]:
    item = exact(
        value,
        {
            "identity",
            "cycle_id",
            "scope_id",
            "protocol_id",
            "transport_id",
            "send",
            "protocol_class",
            "socket",
        },
        "actual original protocol binding is incomplete",
    )
    process = exact(item["identity"], {"pid", "start_ticks"}, "actual protocol process is unknown")
    require(
        type(process["pid"]) is int
        and process["pid"] >= 1
        and type(process["start_ticks"]) is str
        and re.fullmatch(r"[1-9][0-9]*", process["start_ticks"])
        and process == ready.get("identity"),
        "actual protocol identity differs from the original API inner identity",
    )
    require(
        all(
            type(item[key]) is int and item[key] > 0
            for key in ("cycle_id", "scope_id", "protocol_id", "transport_id")
        ),
        "actual cached protocol object identity is invalid",
    )
    original = exact(
        item["send"], {"module", "qualname", "source_sha256"}, "actual original send is unknown"
    )
    require(
        original
        == {
            "module": "uvicorn.protocols.http.h11_impl",
            "qualname": "RequestResponseCycle.send",
            "source_sha256": H11_PROTOCOL_SOURCE_SHA256,
        },
        "actual original send changed its pinned H11 source binding",
    )
    instrumented = exact(
        item["protocol_class"],
        {"module", "qualname", "source_sha256"},
        "actual accepted protocol class is unknown",
    )
    require(
        instrumented["module"] == "__main__"
        and instrumented["qualname"]
        == "install_accepted_buffer_pressure.<locals>.AcceptedBufferProtocol"
        and type(instrumented["source_sha256"]) is str
        and SHA256.fullmatch(instrumented["source_sha256"]),
        "actual accepted protocol class binding is invalid",
    )
    channel = exact(
        item["socket"],
        {"descriptor", "device", "kernel_inode", "family", "type", "send_buffer"},
        "actual initial accepted Unix socket is unknown",
    )
    require(
        all(type(channel[key]) is int and channel[key] >= 0 for key in ("descriptor", "device"))
        and type(channel["kernel_inode"]) is int
        and channel["kernel_inode"] > 0
        and channel["family"] == "unix"
        and channel["type"] == "stream"
        and type(channel["send_buffer"]) is int
        and channel["send_buffer"] == FIXTURE_SEND_BUFFER_OBSERVED,
        "actual initial accepted Unix socket identity or measured pressure is invalid",
    )
    return item


def transfer_protocol_snapshot(value: object, protocol: dict[str, Any]) -> dict[str, Any]:
    item = exact(
        value,
        {
            "cycle_id",
            "transport_id",
            "disconnected",
            "response_started",
            "response_complete",
            "write_paused",
            "transport_closing",
            "write_buffer_bytes",
        },
        "actual original protocol snapshot is incomplete",
    )
    require(
        all(
            type(item[key]) is int and item[key] == protocol[key]
            for key in ("cycle_id", "transport_id")
        )
        and all(
            type(item[key]) is bool
            for key in (
                "disconnected",
                "response_started",
                "response_complete",
                "write_paused",
                "transport_closing",
            )
        )
        and type(item["write_buffer_bytes"]) is int
        and 0 <= item["write_buffer_bytes"] <= MAXIMUM_PROTOCOL_BUFFER_BYTES
        and item["response_started"] is True
        and item["response_complete"] is False,
        "actual protocol identity, bounded state or incomplete response is unproved",
    )
    return item


def transfer_protocol_result(send: dict[str, Any], protocol: dict[str, Any]) -> str:
    before = transfer_protocol_snapshot(send["protocol_before"], protocol)
    after = transfer_protocol_snapshot(send["protocol_after"], protocol)
    if send["error_kind"] is not None:
        require(
            send["error_kind"] == "cancelled"
            and before["write_paused"] is True
            and before["disconnected"] is False,
            "actual raised original send was not cancellation of its paused drain",
        )
        result = "raised"
    elif after["disconnected"]:
        require(
            before["disconnected"] is True or before["write_paused"] is True,
            "actual disconnected no-op lacks its original paused transition",
        )
        result = "disconnected_noop"
    else:
        require(
            before["disconnected"] is False and send["more_body"] is True,
            "actual original protocol submission is inconsistent or complete",
        )
        result = "submitted"
    require(
        send["protocol_result"] == result,
        "actual original send result contradicts its observations",
    )
    return result


def transfer_evidence(
    path: Path, ready: dict[str, Any], identity: dict[str, Any], browser: dict[str, Any]
) -> None:
    lines = bounded(path).splitlines()
    require(
        0 < len(lines) <= MAXIMUM_TRANSFER_EVENTS,
        "actual API transfer inventory is empty or oversized",
    )
    rows = [json_bytes(line) for line in lines]
    expected_ids = {
        engine["static_abort"][mode]["request_id"]
        for engine in browser["engines"].values()
        for mode in ("cancel", "deadline")
    }
    require(
        len(rows) == len(expected_ids) and {row.get("request_id") for row in rows} == expected_ids,
        "actual API transfer evidence omits or duplicates a required original probe",
    )
    protocol_digests = set()
    for row in rows:
        exact(
            row,
            {
                "schema_version",
                "fixture_id",
                "generation_id",
                "phase",
                "engine",
                "actor",
                "request_id",
                "instance_id",
                "object_ids",
                "method",
                "path",
                "status",
                "selected_body_bytes",
                "started_ns",
                "finished_ns",
                "body_send_started",
                "body_send_completed",
                "body_bytes_started",
                "body_bytes_completed",
                "final_send_started",
                "final_send_completed",
                "disconnect_received",
                "disconnect_ns",
                "error_kind",
                "streams_before",
                "streams_after",
                "body_sends",
                "protocol",
                "protocol_body_send_submitted",
                "protocol_body_bytes_submitted",
                "protocol_final_send_submitted",
            },
            "actual API transfer schema contains unsafe or unknown fields",
        )
        require(
            type(row["schema_version"]) is int
            and row["schema_version"] == TRANSFER_EVIDENCE_VERSION
            and all(row[key] == identity[key] for key in ("fixture_id", "generation_id"))
            and row["phase"] == "trusted"
            and row["engine"] in browser["engines"]
            and row["actor"] == "node"
            and row["instance_id"] == ready["instance_id"]
            and row["object_ids"] == ready["object_ids"]
            and row["method"] == "GET"
            and row["status"] == HTTPStatus.OK,
            "actual transfer changed its API process, shared objects or native request identity",
        )
        engine = browser["engines"][row["engine"]]["static_abort"]
        mode = next(
            (
                name
                for name in ("cancel", "deadline")
                if engine[name]["request_id"] == row["request_id"]
            ),
            None,
        )
        require(
            mode is not None
            and row["path"] == identity["prefix"] + "/ui/" + engine["member"]["path"]
            and row["selected_body_bytes"] == engine["member"]["bytes"],
            "actual transfer did not select the exact production artifact body",
        )
        require(
            type(row["started_ns"]) is int
            and type(row["finished_ns"]) is int
            and 0 < row["started_ns"] < row["finished_ns"],
            "actual transfer timing is unknown",
        )
        protocol = transfer_protocol(row["protocol"], ready)
        protocol_digests.add(protocol["protocol_class"]["source_sha256"])
        sends = row["body_sends"]
        require(
            type(sends) is list and 0 < len(sends) <= MAXIMUM_BODY_SENDS,
            "actual transfer send inventory is missing",
        )
        for number, send in enumerate(sends):
            exact(
                send,
                {
                    "sequence",
                    "bytes",
                    "more_body",
                    "started_ns",
                    "finished_ns",
                    "error_kind",
                    "protocol_before",
                    "protocol_after",
                    "protocol_result",
                },
                "actual awaited send record is malformed",
            )
            require(
                type(send["sequence"]) is int
                and send["sequence"] == number
                and type(send["bytes"]) is int
                and 0 <= send["bytes"] <= MAXIMUM_UI_CHUNK_BYTES
                and type(send["more_body"]) is bool
                and type(send["started_ns"]) is int
                and type(send["finished_ns"]) is int
                and row["started_ns"]
                <= send["started_ns"]
                <= send["finished_ns"]
                <= row["finished_ns"]
                and send["error_kind"] in {None, "timeout", "cancelled", "send_error"},
                "actual awaited send timing, chunk bound or error classification is unknown",
            )
        results = [transfer_protocol_result(send, protocol) for send in sends]
        states = [
            snapshot
            for send in sends
            for snapshot in (send["protocol_before"], send["protocol_after"])
        ]
        require(
            all(
                not before["disconnected"] or after["disconnected"]
                for before, after in itertools.pairwise(states)
            ),
            "actual original cycle reset its disconnected state",
        )
        completed = [send for send in sends if send["error_kind"] is None]
        submitted = [
            send for send, result in zip(sends, results, strict=True) if result == "submitted"
        ]
        require(
            all(
                type(row[key]) is int
                for key in (
                    "body_send_started",
                    "body_send_completed",
                    "body_bytes_started",
                    "body_bytes_completed",
                    "protocol_body_send_submitted",
                    "protocol_body_bytes_submitted",
                )
            )
            and row["body_send_started"] == len(sends)
            and row["body_send_completed"] == len(completed)
            and row["body_bytes_started"] == sum(send["bytes"] for send in sends)
            and row["body_bytes_completed"] == sum(send["bytes"] for send in completed)
            and 0
            <= row["body_bytes_completed"]
            <= row["body_bytes_started"]
            <= row["selected_body_bytes"]
            and type(row["final_send_started"]) is bool
            and row["final_send_started"] == any(not send["more_body"] for send in sends)
            and type(row["final_send_completed"]) is bool
            and row["final_send_completed"] == any(not send["more_body"] for send in completed)
            and row["protocol_body_send_submitted"] == len(submitted)
            and row["protocol_body_bytes_submitted"] == sum(send["bytes"] for send in submitted)
            and 0 <= row["protocol_body_bytes_submitted"] < row["selected_body_bytes"]
            and type(row["protocol_final_send_submitted"]) is bool
            and row["protocol_final_send_submitted"]
            == any(not send["more_body"] for send in submitted)
            and row["protocol_final_send_submitted"] is False,
            "actual ASGI counters or incomplete protocol submission contradict the records",
        )
        elapsed = row["finished_ns"] - row["started_ns"]
        require(
            row["error_kind"] in {None, "cancelled"} and type(row["disconnect_received"]) is bool,
            "actual transfer exit classification is invalid",
        )
        if mode == "cancel":
            witnesses = [
                send
                for send, result in zip(sends, results, strict=True)
                if result in {"disconnected_noop", "raised"}
                and send["protocol_before"]["write_paused"] is True
                and send["protocol_before"]["disconnected"] is False
                and send["protocol_after"]["disconnected"] is True
            ]
            require(
                row["disconnect_received"] is True
                and type(row["disconnect_ns"]) is int
                and row["started_ns"] <= row["disconnect_ns"] <= row["finished_ns"]
                and MINIMUM_CANCEL_NS <= elapsed < MAXIMUM_CANCEL_NS
                and any(
                    send["finished_ns"] - send["started_ns"] >= MINIMUM_CANCEL_NS
                    for send in witnesses
                ),
                "actual client cancellation did not reach the API's incomplete paused send",
            )
        else:
            witnesses = [
                send for send, result in zip(sends, results, strict=True) if result == "raised"
            ]
            require(
                MINIMUM_DEADLINE_NS <= elapsed < MAXIMUM_DEADLINE_NS
                and any(
                    send["finished_ns"] - send["started_ns"] >= MINIMUM_DEADLINE_NS
                    for send in witnesses
                )
                and (
                    row["disconnect_ns"] is None
                    or (
                        type(row["disconnect_ns"]) is int
                        and row["disconnect_ns"] >= row["started_ns"] + MINIMUM_DEADLINE_NS
                    )
                ),
                "actual incomplete paused send did not reach the original cancellation deadline",
            )
        for snapshot in (row["streams_before"], row["streams_after"]):
            exact(snapshot, {"active", "tasks"}, "actual transfer stream snapshot is incomplete")
            require(
                type(snapshot["active"]) is int
                and 0 <= snapshot["active"] <= MAXIMUM_UI_STREAMS
                and type(snapshot["tasks"]) is list
                and len(snapshot["tasks"]) <= MAXIMUM_UI_TASKS,
                "actual transfer exceeded its original stream/task bounds",
            )
            require(
                snapshot["active"] == 0 and snapshot["tasks"] == [],
                "actual transfer retained a lease or owned task after return",
            )
            for task in snapshot["tasks"]:
                exact(
                    task, {"id", "name", "done"}, "actual owned stream task identity is incomplete"
                )
                require(
                    type(task["id"]) is int
                    and task["id"] > 0
                    and task["name"] in {"hfcache-ui-send", "hfcache-ui-disconnect"}
                    and type(task["done"]) is bool,
                    "actual owned stream task identity is unknown",
                )

    require(
        len(protocol_digests) == 1,
        "actual accepted protocol source changed between original probes",
    )


def browser_process_evidence(item: dict[str, Any], name: str) -> None:
    process = item.get("process", {})
    status = process.get("status", {})
    uids = status.get("uids", [])
    require(
        item.get("version") == BROWSER_VERSIONS[name]
        and process.get("kind") == "live"
        and type(process.get("pid")) is int
        and process["pid"] > 1
        and len(uids) == UID_FIELDS
        and all(type(uid) is int and uid > 0 for uid in uids)
        and status.get("cap_eff") == "0000000000000000"
        and status.get("no_new_privs") == 1
        and status.get("seccomp") == SECCOMP_FILTER
        and process.get("command", {}).get("representation") == "nul-separated-argv"
        and process.get("command", {}).get("disabling_flags_absent") is True,
        "functional browser exact process/privilege evidence is missing",
    )
    if name == "chromium":
        sandbox = item.get("sandbox", {})
        diagnostics = sandbox.get("diagnostics", {})
        require(
            sandbox.get("verified") is True
            and sandbox.get("evaluation") == "You are adequately sandboxed."
            and diagnostics.get("Layer 1 Sandbox") == "Namespace"
            and all(
                diagnostics.get(key) == "Yes"
                for key in ("PID namespaces", "Network namespaces", "Seccomp-BPF sandbox")
            )
            and sandbox.get("renderers"),
            "functional Chromium sandbox is not proven",
        )
        for renderer in sandbox["renderers"]:
            require(
                renderer.get("kind") == "live"
                and renderer.get("command", {}).get("renderer") is True
                and renderer.get("status", {}).get("cap_eff") == "0000000000000000"
                and renderer.get("status", {}).get("no_new_privs") == 1
                and renderer.get("status", {}).get("seccomp") == SECCOMP_FILTER,
                "functional Chromium renderer is not a live sandboxed process",
            )


def browser_launcher_receipt(
    value: object,
    *,
    manifest: dict[str, Any],
    runtime: dict[str, Any],
    workspace: Path,
    report_copy: Path | None = None,
) -> dict[str, Any]:
    item = exact(
        value,
        {"schema_version", "fixture_id", "profile", "prefix", "workspace", "phases", "report"}
        | ({"run_id"} if "run_id" in runtime else set()),
        "functional browser launcher receipt is malformed",
    )
    require(
        type(item["schema_version"]) is int
        and item["schema_version"] == 1
        and ("run_id" not in runtime or item["run_id"] == runtime["run_id"])
        and item["fixture_id"] == manifest["fixture_id"]
        and item["profile"] == runtime["profile"]
        and item["prefix"] == runtime["prefix"]
        and item["workspace"] == str(workspace),
        "functional browser launcher receipt changed invocation",
    )
    phases = exact(
        item["phases"], {"trusted", "untrusted"}, "functional browser phase receipts are incomplete"
    )
    for name, phase in phases.items():
        exact(
            phase,
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
            "functional browser phase receipt is malformed",
        )
        identity = exact(
            phase["init_identity"],
            {"pid", "start_ticks"},
            "functional browser init identity is missing",
        )
        require(
            phase["image_sha256"] == manifest["browser"][name + "_image_sha256"]
            and isinstance(phase["container_id"], str)
            and SHA256.fullmatch(phase["container_id"])
            and type(identity["pid"]) is int
            and identity["pid"] > 1
            and isinstance(identity["start_ticks"], str)
            and identity["start_ticks"].isdigit()
            and type(phase["exit_code"]) is int
            and phase["exit_code"] == 0
            and all(
                phase[key] is True
                for key in ("container_drained", "init_closed", "inputs_unchanged")
            )
            and phase["trust_mode"] == ("private-ca" if name == "trusted" else "absent"),
            "functional browser exact container/trust/drain proof is unsafe",
        )
    require(
        phases["trusted"]["container_id"] != phases["untrusted"]["container_id"],
        "functional trusted and untrusted phases reused one container identity",
    )
    report = exact(
        item["report"], {"path", "sha256"}, "functional browser report identity is missing"
    )
    require(
        report["path"] == str(workspace / "browser-report.json"),
        "functional browser report escaped its owned generation",
    )
    digest_file(
        workspace / "browser-report.json" if report_copy is None else report_copy,
        report["sha256"],
        MAXIMUM_REPORT_BYTES,
    )
    return item


def selected_profiles(profile: str) -> tuple[str, ...]:
    require(
        profile in {"application", "native", "rootless", "platform", "all"},
        "functional profile selector is unsupported",
    )
    return (
        (profile,)
        if profile in DEPLOYMENTS
        else ("native", "rootless")
        if profile == "platform"
        else ("application", "native", "rootless")
    )


def case_summary(case_ids: list[str], executions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for identifier in case_ids:
        matching = [item for item in executions if identifier in item["case_ids"]]
        rows.append(
            {
                "case_id": identifier,
                "layer": "functional",
                "status": "passed" if matching else "pending",
                "executions": matching,
            }
        )
    return rows


def acceptance_executions(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Project only passed assertions from the same actual engine and role lifecycle."""
    executions = []
    for result in results:
        require(
            result.get("profile") in DEPLOYMENTS and result.get("prefix") in PREFIXES,
            "functional execution cell identity is invalid",
        )
        browser = result["browser"]
        require(
            browser["profile"] == result["profile"]
            and browser["prefix"] == result["prefix"]
            and set(browser["engines"]) == set(selected_browser_engines(result)),
            "functional browser execution cell does not match its role lifecycle",
        )
        for name, engine in sorted(browser["engines"].items()):
            passed = successful_browser_assertions(engine["cases"])
            for identifier, specific in sorted(CASE_ASSERTIONS.items()):
                assertions = specific | COMMON_ASSERTIONS
                if assertions <= passed:
                    executions.append(
                        {
                            "case_ids": [identifier],
                            "profile": result["profile"],
                            "browser": name,
                            "prefix": result["prefix"],
                            "exit_code": 0,
                            "attempts": 1,
                            "assertion_ids": sorted(assertions),
                            "evidence": result["browser_report"],
                            "role_evidence": result["role_report"],
                        }
                    )
    return executions


def requirement_ids(
    through: str | None = None, *, root: Path = ROOT
) -> tuple[list[str], list[str]]:
    requirements = json_bytes(bounded(root / "tests/fixtures/web-acceptance/requirements.json"))
    task_index = json_bytes(bounded(root / "tests/fixtures/web-acceptance/coverage-groups.json"))
    return select_requirement_ids(requirements, task_index, through)


def select_requirement_ids(
    requirements: dict[str, Any], task_index: dict[str, Any], through: str | None
) -> tuple[list[str], list[str]]:
    require(
        type(requirements.get("schema_version")) is int
        and requirements["schema_version"] == 1
        and type(task_index.get("schema_version")) is int
        and task_index["schema_version"] == 1
        and isinstance(requirements.get("cases"), list)
        and isinstance(task_index.get("tasks"), list),
        "functional requirements or task index is malformed",
    )
    tasks = task_index["tasks"]
    task_ids: list[str] = []
    for task in tasks:
        if not isinstance(task, dict) or not isinstance(task.get("id"), str):
            reject("functional task order is invalid")
        task_ids.append(task["id"])
    require(
        len(task_ids) == len(tasks)
        and all(isinstance(task, str) and re.fullmatch(r"WEB-[0-9]{3}", task) for task in task_ids)
        and task_ids == sorted(set(task_ids)),
        "functional task order is invalid",
    )
    for position, task in enumerate(tasks):
        dependencies = task.get("depends_on")
        require(
            isinstance(dependencies, list)
            and all(dependency in task_ids[:position] for dependency in dependencies),
            "functional task dependency order is invalid",
        )
    cases = requirements["cases"]
    require(
        len(cases) == REQUIRED_CASE_COUNT
        and all(
            isinstance(case, dict)
            and isinstance(case.get("id"), str)
            and re.fullmatch(r"[A-Z]+-[0-9]{2}", case["id"])
            and case.get("owner") in task_ids
            for case in cases
        ),
        "functional case ownership inventory is invalid",
    )
    all_ids = [case["id"] for case in cases]
    require(len(set(all_ids)) == len(all_ids), "functional case inventory has duplicate IDs")
    if through is None:
        return all_ids, all_ids
    require(
        through in {"WEB-022", "WEB-023", "WEB-024", "WEB-025"} and through in task_ids,
        "functional through-task selection is unsupported",
    )
    owners = set(task_ids[: task_ids.index(through) + 1])
    required = [case["id"] for case in cases if case["owner"] in owners]
    require(required, "functional through-task selection has no required cases")
    return all_ids, required


def require_cells(
    rows: list[dict[str, Any]], profile: str, case_ids: list[str], required: list[str], label: str
) -> None:
    expected = {
        (deployment, prefix, browser)
        for deployment in DEPLOYMENTS
        for prefix in PREFIXES
        for browser in ENGINES
    }
    require(
        profile == "all"
        and len(rows) == len(case_ids)
        and all(isinstance(row, dict) and isinstance(row.get("case_id"), str) for row in rows)
        and {row["case_id"] for row in rows} == set(case_ids),
        label + " requires actual evidence for the complete, unique case inventory",
    )
    selected = [row for row in rows if row["case_id"] in required]
    require(
        len(selected) == len(required) and all(row.get("status") == "passed" for row in selected),
        label + " requires every owned case to pass; pending cases refuse acceptance",
    )
    require(
        all(
            isinstance(row.get("executions"), list)
            and len(row["executions"]) == len(expected)
            and all(
                isinstance(execution, dict)
                and type(execution.get("exit_code")) is int
                and execution["exit_code"] == 0
                and type(execution.get("attempts")) is int
                and execution["attempts"] == 1
                for execution in row["executions"]
            )
            and {
                (execution.get("profile"), execution.get("prefix"), execution.get("browser"))
                for execution in row["executions"]
            }
            == expected
            for row in selected
        ),
        label + " requires actual evidence for every profile/prefix/browser exactly once",
    )


def require_final(rows: list[dict[str, Any]], profile: str) -> None:
    require(
        profile == "all"
        and len(rows) == REQUIRED_CASE_COUNT
        and all(row.get("status") == "passed" for row in rows),
        "final functional acceptance requires all95 actual cases and both completed profiles",
    )
    case_ids, required = requirement_ids()
    require_cells(rows, profile, case_ids, required, "final functional acceptance")


def require_through(rows: list[dict[str, Any]], profile: str, through: str) -> None:
    case_ids, required = requirement_ids(through)
    require_cells(rows, profile, case_ids, required, "functional acceptance through " + through)


def retained_record(path: Path) -> dict[str, str]:
    return {
        "path": str(path),
        "sha256": hashlib.sha256(bounded(path, MAXIMUM_REPORT_BYTES)).hexdigest(),
    }


def retain_run_inputs(
    manifest_path: Path, manifest: dict[str, Any], workspace: Path, profile: str, run_id: str
) -> dict[str, Any]:
    require(type(run_id) is str and IDENTIFIER.fullmatch(run_id), "fresh run identity is invalid")
    raw = bounded(manifest_path)
    require(json_bytes(raw) == manifest, "functional manifest changed before intent")
    inputs = {
        "SOURCE-INPUTS.json": manifest["source"]["input_manifest"],
        "MARKER.json": manifest["marker"],
        "TOOLCHAIN.json": manifest["browser"]["toolchain_inventory"],
        "UI-MANIFEST.json": {
            "path": str(Path(manifest["assets"]["root"]) / "manifest.json"),
            "sha256": manifest["assets"]["manifest_sha256"],
        },
    }
    if current_release(manifest):
        inputs["RELEASE.json"] = manifest["installed"]["release"]
    for deployment in selected_profiles(profile):
        inputs["CADDY-" + deployment + ".conf"] = manifest["profiles"][deployment]["caddy_config"]
    persist_bytes(workspace / "MANIFEST.json", raw)
    for name, record in inputs.items():
        persist_bytes(
            workspace / name,
            bounded(file_record(record, maximum=MAXIMUM_TOOL_BYTES), MAXIMUM_TOOL_BYTES),
        )
    intent = {
        "schema_version": 1,
        "run_id": run_id,
        "profile": profile,
        "fixture_id": manifest["fixture_id"],
        "guest": manifest["guest"],
        "manifest": {"path": str(manifest_path), "sha256": hashlib.sha256(raw).hexdigest()},
        "workspace": str(workspace),
    }
    persist_json(workspace / "RUN-INTENT.json", intent)
    return intent


def workspace_record(
    value: object, original_workspace: Path, copied_workspace: Path, maximum: int = MAXIMUM_JSON
) -> Path:
    """Resolve only one original workspace prefix; original records remain untouched."""
    item = exact(value, {"path", "sha256"}, "retained workspace file identity is incomplete")
    name = item["path"]
    require(
        type(name) is str
        and name.startswith("/")
        and str(Path(name)) == name
        and not any(part in {".", ".."} for part in name.split("/")),
        "retained original path is not canonical",
    )
    original = Path(name)
    require(
        original != original_workspace and original.is_relative_to(original_workspace),
        "required public proof escaped its original workspace",
    )
    copied = path_input(str(copied_workspace / original.relative_to(original_workspace)))
    digest_file(copied, item["sha256"], maximum)
    return copied


def retained_records(value: object, original: Path, copied: Path) -> None:
    """Check embedded public copies; protected original records stay opaque provenance."""
    pending = [value]
    count = 0
    while pending:
        item = pending.pop()
        count += 1
        require(count <= MAXIMUM_SOURCE_FILES * 16, "retained proof member bound exceeded")
        if type(item) is list:
            pending.extend(item)
        elif type(item) is dict:
            if set(item) == {"record", "body"}:
                path = workspace_record(item["record"], original, copied)
                require(json_bytes(bounded(path)) == item["body"], "retained public body differs")
            elif set(item) == {"path", "sha256"}:
                name = item["path"]
                if type(name) is str and Path(name).is_relative_to(original):
                    workspace_record(item, original, copied, MAXIMUM_REPORT_BYTES)
            pending.extend(item.values())


def retained_selected_artifacts(
    network: dict[str, Any], manifest: dict[str, Any], original: Path, copied: Path
) -> None:
    names = {"release", "stage_index", "api_build", "caddy_build"}
    originals = exact(
        network.get("selected_artifacts"), names, "selected artifact originals missing"
    )
    copies = exact(
        network.get("selected_artifact_copies"), names, "selected public artifact copies missing"
    )
    bodies = {}
    for name in sorted(names):
        source = exact(originals[name], {"path", "sha256"}, "selected original record malformed")
        public = exact(copies[name], {"record", "body"}, "selected artifact copy malformed")
        record = exact(public["record"], {"path", "sha256"}, "selected public record malformed")
        require(record["sha256"] == source["sha256"], "selected artifact copy changed bytes")
        body = json_bytes(bounded(workspace_record(record, original, copied)))
        require(body == public["body"], "selected artifact body changed")
        bodies[name] = body
    release, stage = bodies["release"], bodies["stage_index"]
    require(
        release.get("files", {}).get("web-release.json")
        == manifest["installed"]["release"]["sha256"]
        and release["files"].get("ui/manifest.json") == manifest["assets"]["manifest_sha256"]
        and stage.get("schema_version") == 1
        and all(
            stage.get("files", {}).get(name) == digest for name, digest in release["files"].items()
        )
        and bodies["api_build"].get("image_id") == release.get("app_image")
        and bodies["caddy_build"].get("image_id") == release.get("caddy_image"),
        "retained selected artifact closure changed",
    )


def retained_role_proofs(
    item: dict[str, Any],
    manifest: dict[str, Any],
    original: Path,
    copied: Path,
    runtime: dict[str, Any],
) -> dict[str, Any]:
    """Inspect captured data only; do not resolve accounts, selectors or remote files."""
    proofs = {
        name: json_bytes(bounded(workspace_record(record, original, copied)))
        for name, record in item["proofs"].items()
    }
    require(proofs["network"].get("selinux_enforce") == "1", "recorded enforcing proof missing")
    for name in ("api", "worker", "caddy", "helper"):
        proof = proofs[name]
        require(
            all(
                proof.get(key) == item[key]
                for key in (
                    "schema_version",
                    "fixture_id",
                    "generation_id",
                    "profile",
                    "prefix",
                    "origin",
                    "stage",
                )
            )
            and proof.get("role") == name,
            "retained role proof changed original invocation",
        )
        if name == "helper":
            helper_process(proof.get("process"))
        else:
            process = proof.get("process", {})
            uids = process.get("status", {}).get("Uid", [])
            require(type(uids) is list and len(uids) == UID_FIELDS, "recorded principal missing")
            # Fixed account lookup was performed locally by role_evidence. The
            # copied original UID is metadata here, never a local pwd lookup.
            role_process(process, name, item["profile"], expected_uid=uids[0])
            installation = proof.get("installation", {})
            require(
                installation.get("release_index_sha256")
                == manifest["installed"]["release"]["sha256"]
                and installation.get("expected_executable") == process["executable"],
                "retained installed role identity changed",
            )
        stopped = item["stage"] == "stopped" and name != "helper"
        require(
            proof.get("process_gone") is stopped and proof.get("cgroup_empty") is stopped,
            "retained actual role drain is unknown",
        )
    if item["profile"] == "rootless":
        retained_selected_artifacts(proofs["network"], manifest, original, copied)
    config = bounded(workspace_record(proofs["caddy"]["config"], original, copied))
    template = bounded(path_input(str(copied / ("CADDY-" + item["profile"] + ".conf"))))
    require(
        proofs["caddy"]["template"] == manifest["profiles"][item["profile"]]["caddy_config"]
        and hashlib.sha256(template).hexdigest() == proofs["caddy"]["template"]["sha256"],
        "retained Caddy template changed",
    )
    pattern = re.escape(template)
    markers = (b"__API_SOCKET__", b"__TLS_CERTIFICATE__", b"__TLS_PRIVATE_KEY__")
    for number, marker in enumerate(markers):
        pattern = pattern.replace(
            re.escape(marker), f"(?P<path{number}>/[A-Za-z0-9/._-]+)".encode()
        )
    applied = re.fullmatch(pattern, config)
    upstream = (
        proofs["api"]["listener"]["acceptor"]["process_path"]
        if item["profile"] == "rootless"
        else proofs["api"]["listener"]["path"]
    )
    require(
        all(template.count(marker) == 1 for marker in markers)
        and applied is not None
        and applied["path0"] == upstream.encode()
        and b"basic_auth" not in config
        and b"handle_path" not in config,
        "retained Caddy configuration does not join its original upstream/template",
    )
    api_events(
        workspace_record(proofs["api"]["events"], original, copied),
        item,
        proofs["api"]["ready"]["body"],
        stage=item["stage"],
        runtime=runtime,
    )
    retained_records(proofs, original, copied)
    return proofs


def retained_profile_inputs(
    summary: dict[str, Any], copied: Path, common: dict[str, Any], run_id: str
) -> tuple[dict[str, Any], Path]:
    original = Path(summary["workspace"])
    require(
        str(original) == summary["workspace"]
        and original.is_absolute()
        and original.parent.name == ".scratch"
        and original.name.startswith("web-functional-")
        and not any(part in {".", ".."} for part in summary["workspace"].split("/")),
        "original normal workspace is malformed",
    )
    record = summary["run_intent"]
    require(record.get("path") == str(original / "RUN-INTENT.json"), "normal intent path changed")
    intent = json_bytes(bounded(workspace_record(record, original, copied)))
    exact(
        intent,
        {"schema_version", "run_id", "profile", "fixture_id", "guest", "manifest", "workspace"},
        "normal run intent malformed",
    )
    require(
        intent["schema_version"] == 1
        and type(intent["schema_version"]) is int
        and all(
            intent[key] == summary[key]
            for key in ("run_id", "profile", "fixture_id", "guest", "manifest", "workspace")
        )
        and intent["run_id"] == run_id,
        "normal run context changed",
    )
    source = exact(intent["manifest"], {"path", "sha256"}, "original manifest identity missing")
    require(
        type(source["path"]) is str
        and str(Path(source["path"])) == source["path"]
        and not any(part in {".", ".."} for part in source["path"].split("/"))
        and Path(source["path"]).is_relative_to(original.parent.parent)
        and not Path(source["path"]).is_relative_to(original),
        "original manifest escaped its provisioned repository",
    )
    manifest_copy = path_input(str(copied / "MANIFEST.json"))
    digest_file(manifest_copy, source["sha256"])
    manifest = json_bytes(bounded(manifest_copy))
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
            "mcp_arguments",
        },
        "retained original manifest shape changed",
    )
    exact(
        manifest["installed"],
        {"wheel", "package_root", "release"}
        | ({"tooling"} if summary["profile"] == "rootless" else set()),
        "retained original SDK/native descriptor changed",
    )
    guest = exact(summary["guest"], {"identity", "boot_id"}, "retained guest identity malformed")
    require(
        type(guest["identity"]) is str
        and re.fullmatch(r"[a-z][a-z0-9-]{0,127}", guest["identity"])
        and type(guest["boot_id"]) is str
        and str(uuid.UUID(guest["boot_id"])) == guest["boot_id"]
        and type(summary["fixture_id"]) is str
        and str(uuid.UUID(summary["fixture_id"])) == summary["fixture_id"],
        "retained original fixture or boot is malformed",
    )
    require(
        manifest.get("schema_version") == 1
        and manifest.get("kind") == "hfcache_web_functional_fixture"
        and manifest.get("fixture_id") == summary["fixture_id"]
        and manifest.get("guest") == summary["guest"]
        and current_release(manifest)
        and summary["source"] == manifest["source"]
        and summary["artifacts"]
        == {"installed": manifest["installed"], "assets": manifest["assets"]},
        "retained original manifest or artifacts changed",
    )
    for key in ("parent_commit", "snapshot_sha256", "label"):
        require(manifest["source"][key] == common["source"][key], "profile test source differs")
    inputs = {
        "SOURCE-INPUTS.json": manifest["source"]["input_manifest"]["sha256"],
        "MARKER.json": manifest["marker"]["sha256"],
        "TOOLCHAIN.json": manifest["browser"]["toolchain_inventory"]["sha256"],
        "UI-MANIFEST.json": manifest["assets"]["manifest_sha256"],
        "RELEASE.json": manifest["installed"]["release"]["sha256"],
        "CADDY-" + summary["profile"] + ".conf": manifest["profiles"][summary["profile"]][
            "caddy_config"
        ]["sha256"],
    }
    for name, expected in inputs.items():
        digest_file(path_input(str(copied / name)), expected, MAXIMUM_TOOL_BYTES)
    marker = json_bytes(bounded(path_input(str(copied / "MARKER.json"))))
    require(
        marker
        == {
            "schema_version": 1,
            "fixture_id": summary["fixture_id"],
            "repository_root": str(original.parent.parent),
            "guest": summary["guest"],
        },
        "retained original guest marker changed",
    )
    inventory = json_bytes(bounded(path_input(str(copied / "SOURCE-INPUTS.json"))))
    require(
        hashlib.sha256(
            json.dumps(inventory.get("files"), sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        == common["source"]["snapshot_sha256"],
        "retained complete tooling source differs",
    )
    for key in ("wheel", "release"):
        require(
            manifest["installed"][key]["sha256"] == common["installed"][key]["sha256"],
            "profile application artifact differs",
        )
    require(
        manifest["assets"]["manifest_sha256"] == common["assets"]["manifest_sha256"],
        "profile UI differs",
    )
    for key in (
        "playwright_version",
        "node_version",
        "trusted_image_sha256",
        "untrusted_image_sha256",
    ):
        require(
            manifest["browser"][key] == common["browser"][key], "profile browser authority differs"
        )
    for key in ("toolchain_inventory", "playwright_module", "node_binary", "seccomp"):
        require(
            manifest["browser"][key]["sha256"] == common["browser"][key]["sha256"],
            "profile browser tooling differs",
        )
    return manifest, original


def retained_profile_result(
    result: dict[str, Any], manifest: dict[str, Any], original: Path, copied: Path, run_id: str
) -> tuple[str, str, list[tuple[str, str, int, str]]]:
    profile, prefix, engine = result["profile"], result["prefix"], result["browser_engine"]
    require(
        profile in DEPLOYMENTS and prefix in PREFIXES and engine in ENGINES,
        "retained cell malformed",
    )
    cell = original / (profile + ("-prefixed" if prefix else "-root") + "-" + engine)
    require(
        result["workspace"] == str(cell) and result["run_id"] == run_id,
        "retained cell context changed",
    )

    def read(record: object) -> dict[str, Any]:
        return json_bytes(bounded(workspace_record(record, original, copied)))

    body = json_bytes(
        bounded(workspace_record(result["role_report"], original, copied, MAXIMUM_REPORT_BYTES))
    )
    require(
        body == {k: v for k, v in result.items() if k != "role_report"},
        "normal RESULT differs from summary",
    )
    require(
        result["role_report"]["path"] == str(cell / "RESULT.json"), "normal RESULT path changed"
    )
    runtime = read(result["runtime_record"])
    exact(
        runtime,
        {
            "schema_version",
            "fixture_id",
            "profile",
            "prefix",
            "origin",
            "asset_manifest_sha256",
            "asset_manifest",
            "phase_path",
            "phase_identity",
            "mcp_arguments",
            "browser_engine",
            "run_id",
        },
        "retained runtime malformed",
    )
    require(
        result["runtime_record"]["path"] == str(cell / "runtime.json")
        and runtime.get("run_id") == run_id
        and runtime.get("browser_engine") == engine
        and all(runtime.get(k) == result[k] for k in ("profile", "prefix"))
        and runtime["schema_version"] == 1
        and type(runtime["schema_version"]) is int
        and runtime["fixture_id"] == manifest["fixture_id"]
        and runtime["origin"] == manifest["profiles"][profile]["origin"]
        and runtime["asset_manifest_sha256"] == manifest["assets"]["manifest_sha256"]
        and runtime["asset_manifest"]
        == json_bytes(bounded(path_input(str(copied / "UI-MANIFEST.json"))))
        and runtime["phase_path"] == str(cell / "browser-phase.txt")
        and runtime["mcp_arguments"] == manifest["mcp_arguments"],
        "retained runtime changed",
    )
    ready_api: dict[str, Any] = {}
    actors = []
    for stage in ("ready", "stopped"):
        item = role_context(
            result[stage],
            manifest=manifest,
            profile=profile,
            workspace=cell,
            prefix=prefix,
            stage=stage,
        )
        proofs = retained_role_proofs(item, manifest, original, copied, runtime)
        if stage == "ready":
            ready_api = proofs["api"]
            actors = [
                (
                    manifest["guest"]["boot_id"],
                    role,
                    proofs[role]["process"]["identity"]["pid"],
                    proofs[role]["process"]["identity"]["start_ticks"],
                )
                for role in ("api", "worker", "caddy")
            ]
    bind_role_generation(result["ready"], result["stopped"], read_record=read)
    intent = read(result["browser_intent"])
    require(
        result["browser_intent"]["path"] == str(cell / "browser-intent.json")
        and intent
        == {
            "schema_version": 1,
            "fixture_id": manifest["fixture_id"],
            "generation_id": result["ready"]["generation_id"],
            "profile": profile,
            "prefix": prefix,
            "workspace": str(cell),
            "state": "requested",
            "run_id": run_id,
        },
        "retained browser admission intent differs",
    )
    runtime["instance_id"] = ready_api["ready"]["body"]["instance_id"]
    require(
        read(ready_api["ready"]["record"]) == ready_api["ready"]["body"],
        "retained API READY differs",
    )
    ready = ready_api["ready"]["body"]
    require(
        ready.get("fixture_id") == manifest["fixture_id"]
        and ready.get("generation_id") == result["ready"]["generation_id"]
        and ready.get("lifespan_count") == 1
        and ready.get("capture_fingerprint") == manifest["assets"]["manifest_sha256"]
        and ready.get("phase_identity")
        == [runtime["phase_identity"]["device"], runtime["phase_identity"]["inode"]]
        and ready.get("identity")
        == {
            "pid": ready_api["process"]["status"]["NSpid"][-1],
            "start_ticks": ready_api["process"]["identity"]["start_ticks"],
        },
        "retained API instance was not the original role generation",
    )
    browser_path = workspace_record(
        result["browser_report"], original, copied, MAXIMUM_REPORT_BYTES
    )
    require(
        result["browser_report"]["path"] == str(cell / "browser-report.json"),
        "browser report path changed",
    )
    browser = browser_evidence(
        json_bytes(bounded(browser_path, MAXIMUM_REPORT_BYTES)), manifest=manifest, runtime=runtime
    )
    require(browser == result["browser"], "retained browser differs from summary")
    receipt = read(result["browser_launcher_record"])
    require(
        result["browser_launcher_record"]["path"] == str(cell / "browser-launcher-receipt.json")
        and receipt == result["browser_launcher"],
        "retained browser launcher receipt differs",
    )
    browser_launcher_receipt(
        receipt, manifest=manifest, runtime=runtime, workspace=cell, report_copy=browser_path
    )
    require(
        result["python_mcp_record"]["path"] == str(cell / "python-mcp.json")
        and read(result["python_mcp_record"]) == result["installed_python_mcp"],
        "retained original SDK client report differs",
    )
    sdk = result["installed_python_mcp"]
    require(
        sdk.get("schema_version") == 1
        and sdk.get("origin") == runtime["origin"]
        and sdk.get("prefix") == prefix
        and sdk.get("transport") == "real_caddy_tls"
        and set(sdk.get("tools", {})) == MCP_TOOLS
        and all(row.get("passed") is True for row in sdk["tools"].values()),
        "retained original SDK client scope is incomplete",
    )
    require(
        result["transfer_evidence"] == proofs["api"]["transfers"],
        "original transfer closure changed",
    )
    workspace_record(result["transfer_evidence"], original, copied)
    require(not result.get("cleanup_unknown"), "original cleanup is unknown")
    retained_records(result, original, copied)
    return result["ready"]["generation_id"], runtime["instance_id"], actors


def join_profiles(  # noqa: PLR0913 - authority, fresh context, inputs and strict mode are independent
    manifest: dict[str, Any],
    workspace: Path,
    run_id: str,
    records: list[list[str]],
    *,
    final: bool,
    through: str | None,
) -> dict[str, Any]:
    require(type(run_id) is str and IDENTIFIER.fullmatch(run_id), "fresh join run identity missing")
    require(
        len(records) == len(DEPLOYMENTS) and (final or through is not None),
        "join requires three complete normal profiles and strict acceptance mode",
    )
    results, retained = [], []
    profiles, generations, instances, actors = set(), set(), set(), set()
    expected = {(prefix, engine) for prefix in PREFIXES for engine in ENGINES}
    for name, digest in records:
        summary_path = file_record({"path": name, "sha256": digest}, maximum=MAXIMUM_ASSET_BYTES)
        require(summary_path.name == "SUMMARY.json", "join requires normal SUMMARY files")
        summary = json_bytes(bounded(summary_path, MAXIMUM_ASSET_BYTES))
        exact(
            summary,
            {
                "schema_version",
                "scope",
                "fixture_id",
                "profile",
                "final",
                "require_through",
                "required_case_ids",
                "source",
                "artifacts",
                "results",
                "cases",
                "pending_case_ids",
                "run_id",
                "guest",
                "manifest",
                "workspace",
                "run_intent",
            },
            "normal profile summary malformed",
        )
        profile = summary["profile"]
        require(
            summary["schema_version"] == 1
            and type(summary["schema_version"]) is int
            and summary["scope"]
            == "owned installed shared-Caddy functional fixture; no production/NAS claim"
            and profile in DEPLOYMENTS
            and profile not in profiles
            and summary["run_id"] == run_id
            and summary["final"] is False
            and summary["require_through"] is None
            and summary["required_case_ids"] == []
            and len(summary["results"]) == len(expected),
            "join requires unique fresh normal singleton profiles",
        )
        profiles.add(profile)
        original_manifest, original = retained_profile_inputs(
            summary, summary_path.parent, manifest, run_id
        )
        cells = set()
        for result in summary["results"]:
            require(result["profile"] == profile, "normal result borrowed another profile")
            cell = (result["prefix"], result["browser_engine"])
            require(
                cell in expected and cell not in cells,
                "normal profile omitted or duplicated a cell",
            )
            cells.add(cell)
            generation, instance, identities = retained_profile_result(
                result, original_manifest, original, summary_path.parent, run_id
            )
            require(
                generation not in generations and instance not in instances,
                "fresh lifecycle reused a generation or API instance",
            )
            require(
                not actors.intersection(identities),
                "fresh lifecycle reused an original role process",
            )
            generations.add(generation)
            instances.add(instance)
            actors.update(identities)
            results.append(result)
        rows = case_summary(requirement_ids()[0], acceptance_executions(summary["results"]))
        require(
            summary["cases"] == rows
            and summary["pending_case_ids"]
            == [row["case_id"] for row in rows if row["status"] != "passed"],
            "normal summary status differs from actual assertions",
        )
        retained.append({"path": str(summary_path), "sha256": digest})
    require(
        profiles == set(DEPLOYMENTS) and len(generations) == len(DEPLOYMENTS) * len(expected),
        "complete fresh execution set missing",
    )
    case_ids, required = requirement_ids(through)
    rows = case_summary(case_ids, acceptance_executions(results))
    summary = {
        "schema_version": 1,
        "scope": (
            "fresh normal profile summaries; common manifest fixture is artifact authority, "
            "original per-profile fixtures remain in results"
        ),
        "fixture_id": manifest["fixture_id"],
        "profile": "all",
        "run_id": run_id,
        "final": final,
        "require_through": through,
        "required_case_ids": required,
        "source": manifest["source"],
        "artifacts": {"installed": manifest["installed"], "assets": manifest["assets"]},
        "joined_profile_summaries": retained,
        "results": results,
        "cases": rows,
        "pending_case_ids": [row["case_id"] for row in rows if row["status"] != "passed"],
    }
    persist_json(workspace / "SUMMARY.json", summary)
    if final:
        require_final(rows, "all")
    else:
        require(through is not None, "strict through-task mode missing")
        if through is not None:
            require_through(rows, "all", through)
    return summary


async def run_profile(  # noqa: PLR0913, PLR0915 - one owned generation binds its optional engine and drain
    manifest_path: Path,
    manifest: dict[str, Any],
    workspace: Path,
    profile: str,
    prefix: str,
    *,
    browser_engine: str | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Own one durable role generation and drain it before moving to the next."""
    selection = {} if browser_engine is None else {"browser_engine": browser_engine}
    context = {} if run_id is None else {"run_id": run_id}
    selected_browser_engines(selection)
    require(
        run_id is None or (type(run_id) is str and IDENTIFIER.fullmatch(run_id)),
        "fresh run identity is invalid",
    )
    target = workspace / (
        profile
        + ("-prefixed" if prefix else "-root")
        + ("-" + browser_engine if browser_engine else "")
    )
    target.mkdir(mode=0o700)
    phase = target / "browser-phase.txt"
    phase.write_text("trusted\n", encoding="ascii")
    phase.chmod(0o644)
    phase_facts = phase.stat()
    runtime = {
        "schema_version": 1,
        "fixture_id": manifest["fixture_id"],
        "profile": profile,
        "prefix": prefix,
        "origin": manifest["profiles"][profile]["origin"],
        "asset_manifest_sha256": manifest["assets"]["manifest_sha256"],
        "asset_manifest": asset_identity(manifest["assets"]),
        "phase_path": str(phase),
        "phase_identity": {"device": phase_facts.st_dev, "inode": phase_facts.st_ino},
        "mcp_arguments": manifest["mcp_arguments"],
        **selection,
        **context,
    }
    (target / "runtime.json").write_bytes(canonical(runtime))
    import hfcache
    from hfcache.api.basic import (
        create_administrator_record,
    )

    require(
        Path(hfcache.__file__).parent == Path(manifest["installed"]["package_root"]),
        "functional runner must use the verified installed package",
    )

    password = secrets.token_urlsafe(48)
    username = "functional-login-user"
    record = create_administrator_record("functional-subject", username, password.encode())
    tokens = {name: secrets.token_urlsafe(48) for name in ("writer", "reader", "mcp_reader", "hub")}
    authority = {
        "schema_version": 1,
        "fixture_id": manifest["fixture_id"],
        "administrator_record": record.model_dump(mode="json"),
        "tokens": tokens,
    }
    launcher = manifest["profiles"][profile]["launcher"]["path"]
    argv = [
        launcher,
        "--manifest",
        str(manifest_path),
        "--workspace",
        str(target),
        "--profile",
        profile,
        "--action",
    ]
    admitted = False
    result: dict[str, Any] = {
        "profile": profile,
        "prefix": prefix,
        "workspace": str(target),
        **selection,
        **context,
    }
    if run_id is not None:
        result["runtime_record"] = retained_record(target / "runtime.json")
    try:
        ready = await command([*argv, "start"], body=canonical(authority), timeout=180)
        result["ready"] = role_evidence(
            ready,
            manifest=manifest,
            profile=profile,
            workspace=target,
            prefix=prefix,
            stage="ready",
        )
        ready_api = json_bytes(bounded(file_record(result["ready"]["proofs"]["api"])))
        runtime["instance_id"] = ready_api["ready"]["body"]["instance_id"]
        admitted = True
        result["installed_python_mcp"] = await python_mcp_compatibility(manifest, runtime, tokens)
        (target / "python-mcp.json").write_bytes(canonical(result["installed_python_mcp"]))
        if run_id is not None:
            result["python_mcp_record"] = retained_record(target / "python-mcp.json")
        browser = manifest["browser"]["launcher"]["path"]
        persist_json(
            target / "browser-intent.json",
            {
                "schema_version": 1,
                "fixture_id": manifest["fixture_id"],
                "generation_id": ready["generation_id"],
                "profile": profile,
                "prefix": prefix,
                "workspace": str(target),
                "state": "requested",
                **context,
            },
        )
        if run_id is not None:
            result["browser_intent"] = retained_record(target / "browser-intent.json")
        receipt = await command(
            [browser, "--manifest", str(manifest_path), "--workspace", str(target)],
            body=canonical(
                {"schema_version": 1, "username": username, "password": password, "tokens": tokens}
            ),
            timeout=420,
        )
        result["browser_launcher"] = browser_launcher_receipt(
            receipt, manifest=manifest, runtime=runtime, workspace=target
        )
        receipt_path = target / "browser-launcher-receipt.json"
        require(
            json_bytes(bounded(receipt_path)) == receipt,
            "functional browser launcher retained receipt differs from stdout authority",
        )
        if run_id is not None:
            result["browser_launcher_record"] = retained_record(receipt_path)
        report_path = target / "browser-report.json"
        result["browser"] = browser_evidence(
            json_bytes(bounded(report_path, MAXIMUM_REPORT_BYTES)),
            manifest=manifest,
            runtime=runtime,
        )
        result["browser_report"] = {
            "path": str(report_path),
            "sha256": hashlib.sha256(bounded(report_path)).hexdigest(),
        }
    finally:
        # Even a startup error may have created a positively indexed generation.
        # The fixed launcher owns that exact workspace; no broad process/group kill.
        try:
            stopped, cancelled = await protected_cleanup(
                command([*argv, "stop"], body=None, timeout=90)
            )
            result["stopped"] = role_evidence(
                stopped,
                manifest=manifest,
                profile=profile,
                workspace=target,
                prefix=prefix,
                stage="stopped",
            )
            if admitted:
                bind_role_generation(result["ready"], result["stopped"])
            if "browser" in result:
                final_api = json_bytes(bounded(file_record(result["stopped"]["proofs"]["api"])))
                transfer_evidence(
                    file_record(final_api["transfers"]),
                    final_api["ready"]["body"],
                    result["stopped"],
                    result["browser"],
                )
                result["transfer_evidence"] = final_api["transfers"]
        except BaseException:
            result["cleanup_unknown"] = True
            raise
        finally:
            (target / "RESULT.json").write_bytes(canonical(result))
        if cancelled:
            raise asyncio.CancelledError
    result["role_report"] = {
        "path": str(target / "RESULT.json"),
        "sha256": hashlib.sha256(bounded(target / "RESULT.json")).hexdigest(),
    }
    return result


async def run(  # noqa: PLR0913 - artifact, profile and acceptance mode are independent inputs
    manifest_path: Path,
    manifest: dict[str, Any],
    workspace: Path,
    profile: str,
    *,
    final: bool,
    through: str | None = None,
    browser_engine: str | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    require(not (final and through is not None), "final and through-task selection are exclusive")
    selection = {} if browser_engine is None else {"browser_engine": browser_engine}
    selected_browser_engines(selection)
    require(
        browser_engine is None or not (final or through is not None),
        "selected browser evidence cannot claim complete functional acceptance",
    )
    case_ids, required_ids = requirement_ids(through)
    require(through is None or profile == "all", "through-task acceptance requires all profiles")
    require(
        Path("/proc/sys/kernel/random/boot_id").read_text().strip() == manifest["guest"]["boot_id"],
        "functional runtime does not match its provisioned disposable guest boot",
    )
    intent = (
        None
        if run_id is None
        else retain_run_inputs(manifest_path, manifest, workspace, profile, run_id)
    )
    results = []
    for deployment in selected_profiles(profile):
        for prefix in PREFIXES:
            engines = (
                selected_browser_engines(selection) if run_id is not None else (browser_engine,)
            )
            for engine in engines:
                results.append(  # noqa: PERF401 - each actual generation drains before the next
                    await run_profile(
                        manifest_path,
                        manifest,
                        workspace,
                        deployment,
                        prefix,
                        browser_engine=engine,
                        run_id=run_id,
                    )
                )
    require(
        validate_manifest(str(manifest_path), profile=profile) == manifest,
        "functional manifest changed during its actual profile lifecycles",
    )
    executions = acceptance_executions(results)
    rows = case_summary(case_ids, executions)
    summary = {
        "schema_version": 1,
        "scope": "owned installed shared-Caddy functional fixture; no production/NAS claim",
        "fixture_id": manifest["fixture_id"],
        "profile": profile,
        "final": final,
        "require_through": through,
        "required_case_ids": required_ids if final or through is not None else [],
        "source": manifest["source"],
        "artifacts": {"installed": manifest["installed"], "assets": manifest["assets"]},
        "results": results,
        "cases": rows,
        "pending_case_ids": [row["case_id"] for row in rows if row["status"] != "passed"],
        **selection,
    }
    if intent is not None:
        require(
            retained_record(manifest_path) == intent["manifest"],
            "original run manifest bytes changed",
        )
        summary.update(
            run_id=run_id,
            guest=manifest["guest"],
            workspace=str(workspace),
            manifest=intent["manifest"],
            run_intent=retained_record(workspace / "RUN-INTENT.json"),
        )
    persist_json(workspace / "SUMMARY.json", summary)
    if final:
        require_final(rows, profile)
    elif through is not None:
        require_through(rows, profile, through)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument(
        "--profile", choices=("application", "native", "rootless", "platform", "all"), required=True
    )
    parser.add_argument(
        "--manifest", required=True, help="protected, digest-bound disposable fixture manifest"
    )
    parser.add_argument("--workspace", help="fresh direct repository .scratch descendant")
    parser.add_argument(
        "--run-id", help="fresh32-hex identity shared by the three normal profile runs"
    )
    parser.add_argument(
        "--join-summary",
        action="append",
        nargs=2,
        metavar=("PATH", "SHA256"),
        help="exactly three fresh normal profile SUMMARY copies; offline strict join only",
    )
    requirement = parser.add_mutually_exclusive_group()
    requirement.add_argument(
        "--final",
        action="store_true",
        help="require all95 actual cases; pending cases refuse acceptance",
    )
    requirement.add_argument(
        "--require-through",
        metavar="TASK",
        help="require every case owned through the selected task in all profiles",
    )
    args = parser.parse_args()
    if args.final and args.profile != "all":
        parser.error("--final requires --profile all")
    if args.require_through is not None and args.profile != "all":
        parser.error("--require-through requires --profile all")
    joining = args.join_summary is not None
    if args.run_id is not None and not IDENTIFIER.fullmatch(args.run_id):
        parser.error("--run-id must be32 lower-case hexadecimal characters")
    if joining and (
        args.profile != "all" or args.run_id is None or not (args.final or args.require_through)
    ):
        parser.error(
            "--join-summary requires --profile all, explicit --run-id and --final/--require-through"
        )
    if args.run_id is None:
        args.run_id = secrets.token_hex(16)
    workspace = None
    try:
        if args.require_through is not None:
            requirement_ids(args.require_through)
        manifest = validate_manifest(args.manifest, profile=args.profile, common_only=joining)
        # This guard precedes workspace creation and any process or credential work.
        if not joining:
            require(
                Path("/proc/sys/kernel/random/boot_id").read_text().strip()
                == manifest["guest"]["boot_id"],
                "functional runtime must be its explicitly provisioned disposable guest",
            )
        workspace = prepare_workspace(args.workspace)
        print(f"Retaining owned functional evidence in {workspace}", flush=True)
        if joining:
            join_profiles(
                manifest,
                workspace,
                args.run_id,
                args.join_summary,
                final=args.final,
                through=args.require_through,
            )
        else:
            asyncio.run(
                run(
                    Path(args.manifest),
                    manifest,
                    workspace,
                    args.profile,
                    final=args.final,
                    through=args.require_through,
                    run_id=args.run_id,
                )
            )
    except Exception:  # noqa: BLE001 - never expose credential-bearing third-party exception text
        if workspace is not None:
            (workspace / "BLOCKED.json").write_bytes(
                canonical(
                    {
                        "schema_version": 1,
                        "scope": "owned functional fixture only",
                        "reason": "required provenance, execution, evidence or drain refused",
                    }
                )
            )
        print(
            "Functional fixture refused; preserve evidence and provision the required "
            "owned prerequisites.",
            file=sys.stderr,
        )
        return 1
    print(
        "Executed functional cases passed; inspect SUMMARY.json for explicit later pending cases."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
