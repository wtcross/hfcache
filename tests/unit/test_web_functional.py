"""Independent functional-runner guards; metadata fixtures prove no real browser acceptance."""

import asyncio
import copy
import hashlib
import json
import os
import runpy
import stat
import struct
import sys
from pathlib import Path
from typing import Any

import httpx2
import pytest
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport
from fastmcp.utilities.asgi_transport import StreamingASGITransport, run_asgi_lifespan

from hfcache.api.app import create_app
from hfcache.config import load_config
from hfcache.reporting import RunReport, VerificationReport
from hfcache.server_config import validate_server_config_mapping
from hfcache.services.queries import LocalQueries
from tests.unit.test_web_auth_fixture import provisioned as auth_provisioned  # noqa: F401
from tests.web_functional_fixture import seed_archive, snapshot

ROOT = Path(__file__).absolute().parents[2]
HELPER = ROOT / "scripts/check-web-functional.py"
TOOLS = {
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
CASES = {
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
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record(path):
    return {"path": str(path), "sha256": sha(path)}


def write(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n")
    path.chmod(0o600)
    return path


@pytest.fixture
def helper():
    return runpy.run_path(str(HELPER))


@pytest.fixture
def provisioned(request):
    """Explicit metadata-only placeholders are never executed."""
    root, path, old = request.getfixturevalue("auth_provisioned")
    bundle = path.parent
    guest = {
        "identity": "web-004-83a4380d0c82465fa225c00bba53359c",
        "boot_id": "0d281f8b-de29-44c1-b5e5-57fb27aef707",
    }
    marker = write(
        bundle / "functional-marker.json",
        {
            "schema_version": 1,
            "fixture_id": old["fixture_id"],
            "repository_root": str(root),
            "guest": guest,
        },
    )
    assets = bundle / "assets"
    assets.mkdir(mode=0o700)
    members = []
    for name, body, mime in (
        ("index.html", b"<html></html>\n", "text/html"),
        ("licenses.json", b"{}\n", "application/json"),
        ("THIRD_PARTY_NOTICES.txt", b"fixture notice\n", "text/plain"),
    ):
        (assets / name).write_bytes(body)
        members.append(
            {"path": name, "bytes": len(body), "sha256": sha(assets / name), "mime": mime}
        )
    artifact = {
        "schema_version": 1,
        "kind": "hfcache_web_assets",
        "entrypoint": "index.html",
        "meta_identity": {},
        "build": {"application_version": "unit-only"},
        "members": sorted(members, key=lambda item: item["path"]),
    }
    artifact_path = write(assets / "manifest.json", artifact)
    tooling = old["launcher"]
    binding = {
        "launcher": tooling,
        "origin": old["origins"]["trusted"],
        "caddy_config": tooling,
        "caddy_binary_sha256": "a" * 64,
        "api_image_sha256": None,
        "caddy_image_sha256": None,
        "worker_image_sha256": None,
    }
    source = old["source"]
    value: dict[str, Any] = {
        "schema_version": 1,
        "kind": "hfcache_web_functional_fixture",
        "fixture_id": old["fixture_id"],
        "marker": record(marker),
        "guest": guest,
        "source": {
            "parent_commit": source["parent_commit"],
            "snapshot_sha256": source["snapshot_sha256"],
            "label": "WEB-005, this commit",
            "input_manifest": {
                "path": source["input_manifest_path"],
                "sha256": source["input_manifest_sha256"],
            },
        },
        "installed": {"wheel": old["wheel"], "package_root": old["installed"]["module_root"]},
        "assets": {"root": str(assets), "manifest_sha256": sha(artifact_path)},
        "browser": {
            **dict.fromkeys(
                (
                    "launcher",
                    "ca",
                    "toolchain_inventory",
                    "playwright_module",
                    "node_binary",
                    "seccomp",
                ),
                tooling,
            ),
            "playwright_version": "1.64.1",
            "node_version": "24.18.1",
            "trusted_image_sha256": "a" * 64,
            "untrusted_image_sha256": "b" * 64,
        },
        "profiles": {
            name: copy.deepcopy(binding) for name in ("application", "native", "rootless")
        },
        "mcp_arguments": {name: {} for name in TOOLS},
    }
    for key in ("api_image_sha256", "caddy_image_sha256", "worker_image_sha256"):
        value["profiles"]["rootless"][key] = "c" * 64
    write(path, value)
    return root, path, value


def test_metadata_guard_has_no_runtime_effect(helper, provisioned, monkeypatch):
    root, path, value = provisioned

    def forbidden(*args, **kwargs):
        pytest.fail("metadata guard attempted a runtime effect")

    monkeypatch.setattr(asyncio, "create_subprocess_exec", forbidden)
    assert helper["validate_manifest"](str(path), root=root) == value


@pytest.mark.parametrize(
    "unsafe",
    [
        "/srv/hfcache/secrets",
        "relative.json",
        "/tmp/manifest.json",
        "/home/tyler/Projects/hfcache/.scratch/../manifest.json",
    ],
)
def test_unsafe_manifest_refuses_before_mount_or_runtime_access(helper, monkeypatch, unsafe):
    def forbidden(*args, **kwargs):
        pytest.fail("unsafe lexical path reached mount/runtime discovery")

    monkeypatch.setitem(helper["validate_manifest"].__globals__, "local_backing", forbidden)
    with pytest.raises(ValueError, match=r"fixture|functional"):
        helper["validate_manifest"](unsafe)


@pytest.mark.parametrize(
    "kind",
    [
        "schema",
        "bool-schema",
        "extra-field",
        "marker",
        "source",
        "installed",
        "extra-installed",
        "same-trust-images",
        "profile",
        "mcp-tool",
        "version",
        "foreign-origin",
        "origin-query",
        "asset-bytes",
        "asset-extra",
        "asset-symlink",
        "asset-size",
        "asset-mime",
        "launcher-symlink",
        "mode",
    ],
)
def test_unsafe_prerequisite_cannot_become_functional_acceptance(  # noqa: PLR0912 - explicit independent refusal mutations
    helper, provisioned, kind
):
    root, path, value = provisioned
    assets = Path(value["assets"]["root"])
    if kind == "schema":
        value["schema_version"] = 2
    elif kind == "bool-schema":
        value["schema_version"] = True
    elif kind == "extra-field":
        value["ambient_credentials"] = "forbidden"
    elif kind == "marker":
        value["fixture_id"] = "00000000-0000-0000-0000-000000000001"
    elif kind == "source":
        (root / "src/hfcache/__init__.py").write_text("changed\n")
    elif kind == "installed":
        (Path(value["installed"]["package_root"]) / "__init__.py").write_text("changed\n")
    elif kind == "extra-installed":
        (Path(value["installed"]["package_root"]) / "unknown.py").write_text("changed\n")
    elif kind == "same-trust-images":
        value["browser"]["untrusted_image_sha256"] = value["browser"]["trusted_image_sha256"]
    elif kind == "profile":
        value["profiles"]["ambient"] = value["profiles"]["native"]
    elif kind == "mcp-tool":
        value["mcp_arguments"].pop("get_archive_status")
    elif kind == "version":
        value["browser"]["playwright_version"] = "future"
    elif kind in {"foreign-origin", "origin-query"}:
        value["profiles"]["application"]["origin"] = (
            "https://example.invalid:48209"
            if kind == "foreign-origin"
            else "https://127.0.0.1:48209?unsafe"
        )
    elif kind == "asset-bytes":
        (assets / "index.html").write_text("changed\n")
    elif kind == "asset-extra":
        (assets / "unindexed.html").write_text("unknown\n")
    elif kind == "asset-symlink":
        (assets / "alias.html").symlink_to(assets / "index.html")
    elif kind in {"asset-size", "asset-mime"}:
        artifact = json.loads((assets / "manifest.json").read_text())
        artifact["members"][0]["bytes" if kind == "asset-size" else "mime"] = (
            999 if kind == "asset-size" else "image/svg+xml"
        )
        write(assets / "manifest.json", artifact)
        value["assets"]["manifest_sha256"] = sha(assets / "manifest.json")
    elif kind == "launcher-symlink":
        link = path.parent / "alias-launcher"
        link.symlink_to(value["browser"]["launcher"]["path"])
        value["browser"]["launcher"]["path"] = str(link)
    elif kind == "mode":
        path.chmod(0o666)
    if kind != "mode":
        write(path, value)
    with pytest.raises((ValueError, OSError)):
        helper["validate_manifest"](str(path), root=root)


def test_duplicate_json_is_not_last_value_wins(helper):
    with pytest.raises(ValueError, match="duplicate"):
        helper["json_bytes"](b'{"schema_version":1,"schema_version":2}')


def test_input_leaf_swap_to_symlink_refuses_before_reading_replacement(
    helper, tmp_path, monkeypatch
):
    leaf = tmp_path / "input.json"
    leaf.write_bytes(b'{"original":true}\n')
    replacement = tmp_path / "replacement.json"
    replacement.write_bytes(b'{"replacement":"must not be read"}\n')
    original_open = os.open
    attempted = []

    def replace_before_open(path, flags, *args, **kwargs):
        if Path(path) == leaf:
            assert flags & os.O_NOFOLLOW
            leaf.rename(leaf.with_suffix(".original"))
            leaf.symlink_to(replacement)
            attempted.append("symlink swap before protected open")
        return original_open(path, flags, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(os, "open", replace_before_open)
        with pytest.raises(OSError, match="Too many levels"):
            helper["bounded"](leaf)
    assert attempted == ["symlink swap before protected open"]
    assert leaf.with_suffix(".original").read_bytes() == b'{"original":true}\n'


def test_input_leaf_swap_to_fifo_refuses_without_waiting_for_a_writer(
    helper, tmp_path, monkeypatch
):
    leaf = tmp_path / "input.json"
    leaf.write_bytes(b"{}\n")
    original_open = os.open

    def replace_before_open(path, flags, *args, **kwargs):
        if Path(path) == leaf:
            assert flags & os.O_NONBLOCK
            leaf.rename(leaf.with_suffix(".original"))
            os.mkfifo(leaf)
        return original_open(path, flags, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(os, "open", replace_before_open)
        with pytest.raises(ValueError, match="leaf changed"):
            helper["bounded"](leaf)


@pytest.mark.parametrize("kind", ["nfs4", "cifs", "fuse", "unknown"])
def test_mount_metadata_rejects_network_unknown_without_archive_traversal(helper, kind):
    with pytest.raises(ValueError, match="local filesystem"):
        helper["local_backing"](Path("/owned/repo"), f"1 0 0:1 / / rw - {kind} source rw\n")


def test_workspace_is_fresh_private_and_preserves_prior_failures(helper, provisioned):
    root, _, _ = provisioned
    target = root / ".scratch/web-functional-unit-owned"
    assert helper["prepare_workspace"](str(target), root=root) == target
    assert stat.S_IMODE(target.stat().st_mode) == 0o700
    (target / "failure.json").write_text('{"preserve":true}\n')
    before = sha(target / "failure.json")
    with pytest.raises(ValueError, match="fresh"):
        helper["prepare_workspace"](str(target), root=root)
    assert sha(target / "failure.json") == before


def test_profiles_and_pending_final_refusal_are_explicit(helper):
    assert helper["selected_profiles"]("application") == ("application",)
    assert helper["selected_profiles"]("platform") == ("native", "rootless")
    assert helper["selected_profiles"]("all") == ("application", "native", "rootless")
    rows = helper["case_summary"](
        ["ROUTE-01", "CONFIG-01"], [{"case_ids": ["ROUTE-01"], "profile": "application"}]
    )
    assert [row["status"] for row in rows] == ["passed", "pending"]
    with pytest.raises(ValueError, match="all95"):
        helper["require_final"](rows, "all")
    with pytest.raises(ValueError, match="actual evidence"):
        helper["require_final"]([{"status": "passed", "executions": []}] * 95, "all")


def test_real_child_timeout_refuses_positive_json_even_when_sigterm_exits_zero(helper, tmp_path):
    pid_file = tmp_path / "owned.pid"
    program = (
        "import json,os,signal,sys\n"
        "signal.signal(signal.SIGTERM,lambda *_:sys.exit(0))\n"
        f"open({str(pid_file)!r},'w').write(str(os.getpid()))\n"
        "print(json.dumps({'passed':True}),flush=True)\n"
        "signal.pause()\n"
    )

    async def exercise():
        with pytest.raises(TimeoutError):
            await helper["command"]([sys.executable, "-c", program], body=None, timeout=0.5)

    asyncio.run(exercise())
    assert pid_file.exists()
    assert not Path("/proc", pid_file.read_text()).exists()


def test_real_child_output_is_bounded_and_drained(helper):
    program = "import sys\nsys.stdout.write('x'*2097152)\nsys.stdout.flush()\n"

    async def exercise():
        with pytest.raises(ValueError, match="output exceeded"):
            await helper["command"]([sys.executable, "-c", program], body=None, timeout=5)

    asyncio.run(exercise())


def test_original_serializers_seed_real_read_only_publications(tmp_path):
    target = tmp_path / "owned-seed"
    target.mkdir(mode=0o700)
    fixture = seed_archive(target, fixture_root=tmp_path)
    queries = LocalQueries(load_config(Path(fixture["archive_config"])))
    before = snapshot(Path(fixture["archive_root"]), fixture_root=tmp_path)
    assert set(fixture["mcp_arguments"]) == TOOLS
    assert queries.archive_status().data["archive"]["archive_id"] == fixture["archive_id"]
    assert queries.list_repositories().data["repositories"]
    run_id = fixture["mcp_arguments"]["get_run_report"]["run_id"]
    verification_id = fixture["mcp_arguments"]["get_verification_report"]["run_id"]
    assert run_id != verification_id
    assert isinstance(queries.read_report(run_id), RunReport)
    assert isinstance(queries.read_report(verification_id), VerificationReport)
    assert snapshot(Path(fixture["archive_root"]), fixture_root=tmp_path) == before


def test_seed_all_fourteen_tools_through_real_source_services(tmp_path):
    """Real ASGI/SDK integration; this is explicitly not Caddy/installed acceptance."""

    target = tmp_path / "mcp-source-seed"
    target.mkdir(mode=0o700)
    fixture = seed_archive(target, fixture_root=tmp_path)
    token = tmp_path / "mcp.token"
    token.write_text("source-mcp-fixture-" + "M" * 48)
    token.chmod(0o600)
    writer = tmp_path / "writer.token"
    writer.write_text("source-writer-fixture-" + "W" * 48)
    writer.chmod(0o600)
    settings = validate_server_config_mapping(
        {
            "schema_version": 1,
            "archive_config": fixture["archive_config"],
            "state_directory": str(tmp_path / "source-api-state"),
            "credentials": {"writer": {"file": str(writer)}, "mcp_reader": {"file": str(token)}},
            "listener": {"unix_socket": str(tmp_path / "source-api.sock"), "tcp_enabled": False},
            "mcp_enabled": True,
        }
    )
    app = create_app(settings, instance_lock_path=tmp_path / "source-instance.lock")

    def factory(headers=None, timeout=None, auth=None, **options):
        return httpx2.AsyncClient(
            transport=StreamingASGITransport(app),
            trust_env=False,
            headers=headers,
            timeout=timeout or httpx2.Timeout(3),
            auth=auth,
            **options,
        )

    async def exercise():
        transport = StreamableHttpTransport(
            "http://localhost/mcp/", auth=token.read_text(), httpx_client_factory=factory
        )
        async with run_asgi_lifespan(app), Client(transport, timeout=5, init_timeout=5) as client:
            before = snapshot(Path(fixture["archive_root"]), fixture_root=tmp_path)
            assert {item.name for item in await client.list_tools()} == TOOLS
            for name in sorted(TOOLS):
                response = await client.call_tool(
                    name, fixture["mcp_arguments"][name], raise_on_error=False
                )
                assert not response.is_error, name
                body = response.structured_content
                assert isinstance(body, dict)
                assert body["envelope"]["outcome"] in {"success", "success_with_warnings"}, name
                assert body["envelope"]["exit_code"] == 0, name
            assert app.state.operations.list() == ()
            assert snapshot(Path(fixture["archive_root"]), fixture_root=tmp_path) == before

    asyncio.run(exercise())


def metadata_process(role="worker"):
    """Hand metadata validates refusal logic, never process/functional acceptance."""
    pid = {"api": 101, "worker": 102, "caddy": 103}[role]
    uid = 982 if role == "caddy" else 981
    return {
        "schema_version": 1,
        "role": role,
        "identity": {"pid": pid, "parent_pid": 1, "state": "S", "start_ticks": "12345"},
        "status": {
            "Pid": pid,
            "PPid": 1,
            "Uid": [uid] * 4,
            "Gid": [uid] * 4,
            "NSpid": [pid],
            "CapEff": "0" * 16,
            "CapBnd": "0" * 16,
            "NoNewPrivs": 1,
            "Seccomp": 2,
        },
        "namespaces": {
            name: name + ":[123]" for name in ("pid", "user", "mnt", "net", "ipc", "uts", "cgroup")
        },
        "cgroup": "0::/system.slice/owned.service\n",
        "mountinfo": "1 0 0:1 / / ro - ext4 /dev/test ro\n",
        "uid_map": "0 0 4294967295\n",
        "gid_map": "0 0 4294967295\n",
        "selinux_context": "system_u:system_r:init_t:s0",
        "executable": {"bytes": 100, "sha256": "a" * 64, "device": 1, "inode": 1},
        "argv_sha256": "b" * 64,
        "argv_count": 3,
        "fixed_argv_matched": True,
    }


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("Uid", [0] * 4),
        ("Uid", [981, 0, 981, 981]),
        ("NoNewPrivs", 0),
        ("Seccomp", 0),
        ("CapEff", "0000000000000001"),
        ("CapBnd", "0000000000000001"),
        ("NSpid", []),
    ],
)
def test_role_kernel_facts_refuse_summary_true_with_unsafe_actual_state(helper, field, value):
    process = metadata_process()
    helper["role_process"](process, "worker", "native")
    process["status"][field] = value
    with pytest.raises(ValueError, match=r"actual|functional|role"):
        helper["role_process"](process, "worker", "native")


def test_empty_state_is_not_an_actual_live_role_process(helper):
    process = metadata_process()
    process["identity"]["state"] = ""
    with pytest.raises(ValueError, match="process privilege"):
        helper["role_process"](process, "worker", "native")


@pytest.mark.parametrize(
    "mutation", ["other-pid", "other-start", "refused-connection", "missing-ipv6", "readable-token"]
)
def test_origin_probe_requires_same_worker_and_actual_policy_errno(helper, mutation):
    process = metadata_process()
    probe: dict[str, Any] = {
        "schema_version": 1,
        "role": "worker",
        "profile": "native",
        "passed": True,
        "identity": copy.deepcopy(process["identity"]),
        "status": process["status"],
        "authority_probes": {
            key: {"attempted": True, "errno": 13, "denied": True}
            for key in ("basic", "writer", "reader", "mcp_reader", "hub")
        },
        "network_probes": {
            key: {"attempted": True, "operation": "connect", "errno": 1, "denied": True}
            for key in ("inet", "inet6")
        },
    }
    helper["origin_probe"](probe, process, "worker", "native")
    if mutation == "other-pid":
        probe["identity"]["pid"] += 1
    elif mutation == "other-start":
        probe["identity"]["start_ticks"] = "98765"
    elif mutation == "refused-connection":
        probe["network_probes"]["inet"]["errno"] = 111
    elif mutation == "missing-ipv6":
        del probe["network_probes"]["inet6"]
    else:
        probe["authority_probes"]["hub"] = {"attempted": True, "errno": None, "denied": False}
    with pytest.raises(ValueError, match=r"actual|functional|role"):
        helper["origin_probe"](probe, process, "worker", "native")


def packet_instruction(code, dst=0, src=0, offset=0, immediate=0):
    return struct.pack("<BBhi", code, dst | src << 4, offset, immediate)


def packet_deny_program():
    # Hand authored from the original systemd v257 deny-any/no-accounting path.
    # Metadata fixtures exercise parser refusal, not actual kernel attachment.
    body = b"".join(
        [
            packet_instruction(0xBF, 6, 1),
            packet_instruction(0x61, 7, 6, 16),
            packet_instruction(0xB4, 8),
            packet_instruction(0x44, 8, immediate=2),
            packet_instruction(0xB7, immediate=1),
            packet_instruction(0x55, 8, offset=1, immediate=2),
            packet_instruction(0xB7),
            packet_instruction(0x95),
        ]
    )
    return {
        "type": 8,
        "id": 417,
        "tag": "b" * 16,
        "name": "sd_fw_ingress",
        "created_by_uid": 0,
        "map_ids": [],
        "translated_bytes": len(body),
        "translated_hex": body.hex(),
        "translated_sha256": hashlib.sha256(body).hexdigest(),
        "semantics": {"verified_deny_all": True, "instructions": 8, "states": 8, "exits": 1},
    }


def test_actual_packet_program_is_independently_interpreted(helper):
    value = packet_deny_program()
    assert helper["bpf_deny_program"](value, 417, "sd_fw_ingress") == value


@pytest.mark.parametrize(
    "mutation",
    [
        "allows",
        "unknown",
        "unknown-branch",
        "helper-call",
        "map-load",
        "store",
        "loop",
        "fallthrough",
        "bad-jump",
        "bad-register",
        "bad-hash",
        "maps",
        "owner",
        "bool-type",
        "bool-id",
        "bool-owner",
        "bool-count",
        "extra",
    ],
)
def test_packet_program_cannot_substitute_name_or_asserted_success(helper, mutation):
    value = packet_deny_program()
    bodies = {
        "allows": packet_instruction(0xB7, immediate=1) + packet_instruction(0x95),
        "unknown": packet_instruction(0xBF, 0, 1) + packet_instruction(0x95),
        "unknown-branch": packet_instruction(0x15, 1, offset=1)
        + packet_instruction(0xB7, immediate=1)
        + packet_instruction(0x95),
        "helper-call": packet_instruction(0x85),
        "map-load": packet_instruction(0x18),
        "store": packet_instruction(0x63),
        "loop": packet_instruction(0x05, offset=-1),
        "fallthrough": packet_instruction(0xB7),
        "bad-jump": packet_instruction(0x05, offset=1) + packet_instruction(0x95),
        "bad-register": packet_instruction(0xB7, 11) + packet_instruction(0x95),
    }
    if mutation in bodies:
        body = bodies[mutation]
        value.update(
            translated_bytes=len(body),
            translated_hex=body.hex(),
            translated_sha256=hashlib.sha256(body).hexdigest(),
        )
    elif mutation == "bad-hash":
        value["translated_sha256"] = "0" * 64
    elif mutation == "maps":
        value["map_ids"] = [123]
    elif mutation == "owner":
        value["created_by_uid"] = 981
    elif mutation.startswith("bool-"):
        key = {"bool-type": "type", "bool-id": "id", "bool-owner": "created_by_uid"}.get(mutation)
        if key:
            value[key] = bool(value[key])
        else:
            value["semantics"]["exits"] = True
    else:
        value["unexpected"] = True
    with pytest.raises(ValueError, match="BPF"):
        helper["bpf_deny_program"](value, 417, "sd_fw_ingress")


def metadata_browser() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    manifest = {
        "fixture_id": "71348794-30fb-4e1a-a609-c87cb4772429",
        "assets": {"manifest_sha256": "a" * 64},
        "profiles": {"application": {"origin": "https://127.0.0.1:48209"}},
    }
    runtime = {
        "profile": "application",
        "prefix": "",
        "instance_id": "a" * 32,
        "origin": "https://127.0.0.1:48209",
        "asset_manifest": {
            "members": [
                {
                    "path": "assets/main-12345678.js",
                    "bytes": 200000,
                    "sha256": "c" * 64,
                    "mime": "text/javascript",
                }
            ]
        },
    }
    engines = {}
    for name, version in {"chromium": "156.0.8078.4", "firefox": "157.0", "webkit": "27.2"}.items():
        process = {
            "kind": "live",
            "pid": 100,
            "status": {"uids": [1000] * 4, "cap_eff": "0" * 16, "no_new_privs": 1, "seccomp": 2},
            "command": {"representation": "nul-separated-argv", "disabling_flags_absent": True},
        }
        engine: dict[str, Any] = {
            "version": version,
            "instance_id": "a" * 32,
            "process": process,
            "browser_closed": True,
            "descendants_closed": True,
            "cases": [{"id": case, "passed": True, "attempts": 1} for case in sorted(CASES)],
            "network_observation": {
                "mode": "passive-origin-observer",
                "request_interception": False,
                "invalid": False,
                "overflow": False,
                "request_count": 1,
                "expected_origins": {"trusted": "https://127.0.0.1:48209"},
                "observations": [
                    {"category": "trusted", "scheme": "https:", "host": "127.0.0.1", "port": 48209}
                ],
            },
            "mcp_tools": {
                tool: {
                    "passed": True,
                    "browser_active": True,
                    "origin": "https://127.0.0.1:48209",
                    "request_id": "f" * 32,
                    "outcome": "success",
                }
                for tool in TOOLS
            },
        }
        engine["static_abort"] = metadata_static_abort(runtime, len(engines) * 100)
        if name == "chromium":
            engine["sandbox"] = {
                "verified": True,
                "evaluation": "You are adequately sandboxed.",
                "diagnostics": {
                    "Layer 1 Sandbox": "Namespace",
                    "PID namespaces": "Yes",
                    "Network namespaces": "Yes",
                    "Seccomp-BPF sandbox": "Yes",
                },
                "renderers": [
                    {"kind": "live", "command": {"renderer": True}, "status": process["status"]}
                ],
            }
        negative = copy.deepcopy(engine)
        negative.update(
            certificate_refused=True,
            cases=[{"id": "untrusted-certificate-refused", "passed": True, "attempts": 1}],
        )
        engine["untrusted_phase"] = negative
        engines[name] = engine
    report = {
        "schema_version": 1,
        "fixture_id": manifest["fixture_id"],
        "profile": "application",
        "prefix": "",
        "asset_manifest_sha256": "a" * 64,
        "engines": engines,
    }
    return report, manifest, runtime


def metadata_static_abort(runtime, offset):
    def original(number):
        return f"{offset + number + 1:032x}"

    member = runtime["asset_manifest"]["members"][0]
    item: dict[str, Any] = {
        "member": {key: member[key] for key in ("path", "bytes", "sha256")},
        "head": {"status": 200, "request_id": original(0), "bytes": 0, "headers": {}},
        "browser_cancels": [
            {
                "status": 200,
                "request_id": original(number + 1),
                "read_bytes": 1024,
                "first_read_done": False,
                "reader_cancelled": True,
                "controller_aborted": True,
            }
            for number in range(8)
        ],
        "concurrent_bearer": {
            "status": 200,
            "request_id": original(11),
            "instance_id": runtime["instance_id"],
            "browser_active": True,
        },
    }
    for number, mode in enumerate(("cancel", "deadline")):
        item[mode] = {
            "mode": mode,
            "origin": runtime["origin"],
            "path": "/ui/" + member["path"],
            "initial_window_size": 0,
            "push_enabled": False,
            "settings_acknowledged": True,
            "received_bytes": 0,
            "client_cancel_after_ms": 2000 if mode == "cancel" else 35000,
            "observed_ms": 2000 if mode == "cancel" else 35000,
            "remote_closed": False,
            "stream_closed": True,
            "session_closed": True,
            "request_id": original(9 + number),
            "status": 200,
        }
    return item


@pytest.mark.parametrize(
    "mutation",
    [
        "zero",
        "skip",
        "retry",
        "missing-mcp",
        "closed-page",
        "interception",
        "foreign-origin",
        "missing-cert",
        "missing-renderer",
        "root-browser",
        "no-sandbox",
    ],
)
def test_browser_report_refuses_missing_or_unsafe_actual_evidence(helper, mutation):
    report, manifest, runtime = metadata_browser()
    helper["browser_evidence"](report, manifest=manifest, runtime=runtime)
    engine = report["engines"]["chromium"]
    if mutation == "zero":
        engine["cases"] = []
    elif mutation == "skip":
        engine["cases"][0]["passed"] = False
    elif mutation == "retry":
        engine["cases"][0]["attempts"] = 2
    elif mutation == "missing-mcp":
        del engine["mcp_tools"]["get_run_report"]
    elif mutation == "closed-page":
        engine["mcp_tools"]["get_run_report"]["browser_active"] = False
    elif mutation == "interception":
        engine["network_observation"]["request_interception"] = True
    elif mutation == "foreign-origin":
        engine["network_observation"]["observations"][0]["host"] = "attacker.invalid"
    elif mutation == "missing-cert":
        engine["untrusted_phase"]["certificate_refused"] = False
    elif mutation == "missing-renderer":
        engine["sandbox"]["renderers"] = []
    elif mutation == "root-browser":
        engine["process"]["status"]["uids"] = [0] * 4
    else:
        engine["process"]["command"]["disabling_flags_absent"] = False
    with pytest.raises(ValueError, match=r"actual|functional|role"):
        helper["browser_evidence"](report, manifest=manifest, runtime=runtime)


def test_repeated_parent_cancellation_waits_for_exact_real_child_drain(helper, tmp_path):
    child_file = tmp_path / "owned-child.pid"
    program = (
        f"import os,time\nopen({str(child_file)!r},'w').write(str(os.getpid()))\ntime.sleep(.15)\n"
    )

    async def exercise():
        child = await asyncio.create_subprocess_exec(sys.executable, "-c", program)
        task = asyncio.create_task(helper["protected_cleanup"](child.wait()))
        for _ in range(3):
            await asyncio.sleep(0.025)
            task.cancel()
        result, cancelled = await task
        assert cancelled
        assert result == 0
        assert child.returncode == 0

    asyncio.run(exercise())
    assert not Path("/proc", child_file.read_text()).exists()


@pytest.mark.parametrize(
    "mutation", ["capture", "stream", "hash-worker", "pool-worker", "operation", "objects"]
)
def test_final_resource_proof_refuses_summary_drain_when_actual_resources_remain(helper, mutation):
    ready = {
        "schema_version": 1,
        "fixture_id": "fixture",
        "generation_id": "b" * 32,
        "instance_id": "a" * 32,
        "identity": {"pid": 101, "start_ticks": "12345"},
        "object_ids": {
            "store": 100,
            "pool": 101,
            "runner": 102,
            "verifier": 103,
            "capture": 104,
            "streams": 105,
        },
    }
    final: dict[str, Any] = {
        "schema_version": 1,
        "fixture_id": "fixture",
        "generation_id": "b" * 32,
        **copy.deepcopy(ready),
        "lifespan_count": 1,
        "worker_probes": [],
        "async_tasks": [],
        "capture": {
            "root_descriptor": -1,
            "matching_descriptors": [],
            "members_remaining": 0,
            "shells_remaining": 0,
            "manifest_bytes_remaining": 0,
        },
        "streams": {"active": 0, "accepting": False, "owned_tasks": []},
        "metadata": {"inflight": 0, "closed": True, "threads": [{"ident": 10, "alive": False}]},
        "authentication": {
            "stats": {"active": 0, "waiting": 0, "reservations": 0, "accepting": False},
            "threads": [{"ident": 20, "alive": False}],
        },
        "runner": {
            "pending": 0,
            "active_operation_id": None,
            "accepting": False,
            "closing": True,
            "thread": [{"ident": 30, "alive": False}],
        },
    }
    helper["api_final"](final, ready)
    if mutation == "capture":
        final["capture"]["root_descriptor"] = 4
    elif mutation == "stream":
        final["streams"]["owned_tasks"] = [{"name": "sender", "done": False}]
    elif mutation == "hash-worker":
        final["authentication"]["threads"][0]["alive"] = True
    elif mutation == "pool-worker":
        final["metadata"]["threads"][0]["alive"] = True
    elif mutation == "operation":
        final["runner"]["pending"] = 1
    else:
        final["object_ids"]["pool"] = 900
    with pytest.raises(ValueError, match=r"actual|owned"):
        helper["api_final"](final, ready)


def test_native_listener_does_not_relabel_manager_creator_as_worker(helper):
    process = metadata_process()
    listener = {
        "path": "/owned/verification.sock",
        "device": 1,
        "inode": 1,
        "uid": 981,
        "gid": 981,
        "mode": 384,
        "kernel_creator_peer": {"pid": 1, "uid": 0, "gid": 0, "start_ticks": "1"},
        "acceptor": {
            "pid": 102,
            "start_ticks": "12345",
            "process_path": "/owned/verification.sock",
            "kernel_inode": 7,
            "listener_fds": [3],
            "activation_fd": 3,
        },
    }
    helper["unix_listener"](listener, process, worker=True, profile="native")
    listener["kernel_creator_peer"]["pid"] = 102
    with pytest.raises(ValueError, match="manager-created FD3"):
        helper["unix_listener"](listener, process, worker=True, profile="native")


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("privileged", True),
        ("read_only_rootfs", False),
        ("network_mode", "host"),
        ("image_sha256", "b" * 64),
        ("userns", "host"),
        ("cap_drop", []),
    ],
)
def test_rootless_container_refuses_privilege_or_image_substitution(helper, field, value):
    process = metadata_process()
    process["status"].update(Uid=[1000] * 4, Gid=[1000] * 4, NSpid=[102, 1])
    process["uid_map"] = process["gid_map"] = "0 524288 981\n981 1000 1\n982 525269 64555\n"
    name = "web005-" + "d" * 32 + "-rootless-worker"
    group = "/user.slice/user-1000.slice/user@1000.service/app.slice/" + name + ".service"
    manifest = {
        "profiles": {
            "rootless": {"worker_image_sha256": "a" * 64, "origin": "https://127.0.0.1:33333"}
        }
    }
    container: dict[str, Any] = {
        "schema_version": 1,
        "engine": "podman-rootless-vfs",
        "id": "c" * 64,
        "name": name,
        "image_sha256": "a" * 64,
        "init_identity": {"pid": 102, "start_ticks": "12345"},
        "running": True,
        "exit_code": None,
        "user": "981:981",
        "userns": "keep-id:uid=981,gid=981",
        "network_mode": "none",
        "read_only_rootfs": True,
        "privileged": False,
        "cap_drop": ["ALL"],
        "security_opt": ["no-new-privileges"],
        "mounts": [{"source": "/owned/archive", "destination": "/archive", "read_only": True}],
        "published_ports": [],
        "manager_unit": {
            "Id": name + ".service",
            "MainPID": "202",
            "InvocationID": "e" * 32,
            "ControlGroup": group,
            "ActiveState": "active",
            "SubState": "running",
            "ExecMainCode": "0",
            "ExecMainStatus": "0",
            "Type": "notify",
            "KillMode": "mixed",
            "SendSIGKILL": "no",
            "TimeoutStopUSec": "infinity",
            "StandardOutput": "journal",
            "StandardError": "journal",
        },
        "cgroup": {},
        "owned_processes": [
            {"pid": pid, "start_ticks": "12345", "gone": False} for pid in (102, 202)
        ],
        "owned_cgroups": [
            {"path": "/user.slice/owned.scope", "pids": [102]},
            {"path": group, "pids": [202]},
        ],
    }
    helper["role_container"](container, process, manifest, "worker", stage="ready")
    container[field] = value
    with pytest.raises(ValueError, match="actual rootless"):
        helper["role_container"](container, process, manifest, "worker", stage="ready")


@pytest.mark.parametrize("role", ["api", "worker", "caddy"])
@pytest.mark.parametrize("mutation", ["host-uid", "host-gid", "uid-map", "gid-map", "inner-pid"])
def test_every_rootless_role_requires_actual_host_and_namespace_mapping(helper, role, mutation):
    process = metadata_process(role)
    pid = process["identity"]["pid"]
    process["status"].update(Uid=[1000] * 4, Gid=[1000] * 4, NSpid=[pid, 1])
    process["uid_map"] = process["gid_map"] = "0 524288 981\n981 1000 1\n982 525269 64555\n"
    helper["uid_mapping"](process)
    if mutation == "host-uid":
        process["status"]["Uid"] = [981] * 4
    elif mutation == "host-gid":
        process["status"]["Gid"] = [981] * 4
    elif mutation in {"uid-map", "gid-map"}:
        process[mutation.replace("-", "_")] = "0 0 4294967295\n"
    else:
        process["status"]["NSpid"] = [pid, 2]
    # Full closed record, deliberately no successful container facts: the
    # actual role mapping must refuse before downstream summary assertions.
    container = dict.fromkeys(
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
        }
    )
    with pytest.raises(ValueError, match=r"mapped identity|identity mapping"):
        helper["role_container"](container, process, {}, role, stage="ready")


def metadata_manager(role="worker", *, stopped=False) -> dict[str, Any]:
    name = "web005-" + "a" * 32 + "-rootless-" + role
    group = "/user.slice/user-1000.slice/user@1000.service/app.slice/" + name + ".service"
    before = {
        "Id": name + ".service",
        "MainPID": "202",
        "InvocationID": "e" * 32,
        "ControlGroup": group,
        "ActiveState": "active",
        "SubState": "running",
        "ExecMainCode": "0",
        "ExecMainStatus": "0",
        "Type": "notify" if role == "worker" else "exec",
        "KillMode": "mixed",
        "SendSIGKILL": "no",
        "TimeoutStopUSec": "infinity",
        "StandardOutput": "journal",
        "StandardError": "journal",
    }
    manager = (
        {
            "before_stop": before,
            "after_stop": {
                "Id": name + ".service",
                "LoadState": "not-found",
                "ActiveState": "inactive",
                "SubState": "dead",
                "MainPID": "0",
                "ControlGroup": "",
                "Result": "",
            },
        }
        if stopped
        else before
    )
    return {
        "name": name,
        "manager_unit": manager,
        "owned_processes": [{"pid": 202, "start_ticks": "12345", "gone": stopped}],
        "owned_cgroups": [{"path": group, "pids": [] if stopped else [202]}],
    }


EXPANDED_CAP_DROP = [
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
]


def metadata_rootless_container(role="worker", *, stage="ready"):
    """Independent metadata only; no container, kernel capability or platform proof."""
    stopped = stage == "stopped"
    process = metadata_process(role)
    pid = process["identity"]["pid"]
    process["status"].update(Uid=[1000] * 4, Gid=[1000] * 4, NSpid=[pid, 1])
    process["uid_map"] = process["gid_map"] = "0 524288 981\n981 1000 1\n982 525269 64555\n"
    manager = metadata_manager(role, stopped=stopped)
    container = {
        "schema_version": 1,
        "engine": "podman-rootless-vfs",
        "id": "c" * 64,
        "name": manager["name"],
        "image_sha256": "a" * 64,
        "init_identity": {"pid": pid, "start_ticks": "12345"},
        "running": not stopped,
        "exit_code": 0 if stopped else None,
        "user": "981:981",
        "userns": "keep-id:uid=981,gid=981",
        "network_mode": "none" if role == "worker" else "pasta",
        "read_only_rootfs": True,
        "privileged": False,
        "cap_drop": ["ALL"],
        "security_opt": ["no-new-privileges"],
        "mounts": [{"source": "/owned/archive", "destination": "/archive", "read_only": True}],
        "published_ports": (
            [
                {
                    "host_ip": "127.0.0.1",
                    "host_port": 33333,
                    "container_port": 8443,
                    "protocol": "tcp",
                }
            ]
            if role == "caddy"
            else []
        ),
        "manager_unit": manager["manager_unit"],
        "cgroup": {},
        "owned_processes": [
            {"pid": owned_pid, "start_ticks": "12345", "gone": stopped} for owned_pid in (pid, 202)
        ],
        "owned_cgroups": [
            {"path": "/user.slice/owned.scope", "pids": [] if stopped else [pid]},
            *manager["owned_cgroups"],
        ],
    }
    manifest = {
        "profiles": {
            "rootless": {
                "api_image_sha256": "a" * 64,
                "worker_image_sha256": "a" * 64,
                "caddy_image_sha256": "a" * 64,
                "origin": "https://127.0.0.1:33333",
            }
        }
    }
    return container, process, manifest


@pytest.mark.parametrize("role", ["api", "worker", "caddy"])
@pytest.mark.parametrize("stage", ["ready", "stopped"])
@pytest.mark.parametrize(
    "observed",
    [["ALL"], EXPANDED_CAP_DROP, list(reversed(EXPANDED_CAP_DROP))],
    ids=["literal-all", "actual-expanded-eleven", "reordered-expanded-eleven"],
)
def test_rootless_cap_drop_encodings_keep_raw_order_and_require_other_proofs(
    helper, role, stage, observed
):
    container, process, manifest = metadata_rootless_container(role, stage=stage)
    container["cap_drop"] = copy.deepcopy(observed)
    original = copy.deepcopy(container)
    raw = container["cap_drop"]
    helper["role_container"](container, process, manifest, role, stage=stage)
    assert container == original
    assert container["cap_drop"] is raw


CAP_DROP_REFUSALS = (
    [
        pytest.param(
            EXPANDED_CAP_DROP[:index] + EXPANDED_CAP_DROP[index + 1 :], id="missing-" + name
        )
        for index, name in enumerate(EXPANDED_CAP_DROP)
    ]
    + [
        pytest.param(
            [
                *EXPANDED_CAP_DROP[:index],
                EXPANDED_CAP_DROP[(index + 1) % len(EXPANDED_CAP_DROP)],
                *EXPANDED_CAP_DROP[index + 1 :],
            ],
            id="same-length-duplicate-" + name,
        )
        for index, name in enumerate(EXPANDED_CAP_DROP)
    ]
    + [
        pytest.param(value, id=label)
        for label, value in [
            ("extra-capability", [*EXPANDED_CAP_DROP, "CAP_SYS_ADMIN"]),
            ("unknown-replaces-capability", [*EXPANDED_CAP_DROP[:-1], "CAP_SYS_ADMIN"]),
            ("mixed-same-length", ["ALL", *EXPANDED_CAP_DROP[:-1]]),
            ("mixed-expanded", ["ALL", *EXPANDED_CAP_DROP]),
            ("mixed-literal", ["ALL", "CAP_CHOWN"]),
            ("duplicate-literal", ["ALL", "ALL"]),
            ("lowercase-capability", [*EXPANDED_CAP_DROP[:-1], "cap_sys_chroot"]),
            ("lowercase-all", ["all"]),
            ("empty-list", []),
            ("boolean", True),
            ("null", None),
            ("integer", 1),
            ("string", "ALL"),
            ("tuple", ("ALL",)),
            ("set", {"ALL"}),
            ("mapping", {"ALL": True}),
            ("boolean-item", [True]),
            ("integer-item", [1]),
            ("null-item", [None]),
            ("nested-list", [["ALL"]]),
            ("unhashable-same-length", [*EXPANDED_CAP_DROP[:-1], {}]),
            ("byte-string-item", [*EXPANDED_CAP_DROP[:-1], b"CAP_SYS_CHROOT"]),
        ]
    ]
)


@pytest.mark.parametrize("observed", CAP_DROP_REFUSALS)
def test_rootless_cap_drop_rejects_missing_duplicate_extra_or_unrecognized_metadata(
    helper, observed
):
    container, process, manifest = metadata_rootless_container()
    container["cap_drop"] = observed
    with pytest.raises(ValueError, match="actual rootless"):
        helper["role_container"](container, process, manifest, "worker", stage="ready")


@pytest.mark.parametrize("role", ["api", "worker", "caddy"])
@pytest.mark.parametrize("stage", ["ready", "stopped"])
@pytest.mark.parametrize("observed", [["ALL"], EXPANDED_CAP_DROP], ids=["literal", "expanded"])
@pytest.mark.parametrize("field", ["CapEff", "CapBnd"])
def test_rootless_cap_drop_cannot_substitute_for_actual_zero_process_capabilities(
    helper, role, stage, observed, field
):
    container, process, manifest = metadata_rootless_container(role, stage=stage)
    container["cap_drop"] = copy.deepcopy(observed)
    helper["role_container"](container, process, manifest, role, stage=stage)
    process["status"][field] = "0000000000000001"
    with pytest.raises(ValueError, match="actual rootless"):
        helper["role_container"](container, process, manifest, role, stage=stage)


def caddy_kernel_rows(*, ipv6=False, port=8443) -> list[dict[str, Any]]:
    # Saved successful TLS3 control rows; no listener rows survived failed common19.
    return [
        {
            "protocol": "tcp6" if ipv6 else "tcp",
            "address": "::" if ipv6 else "0.0.0.0",
            "port": port,
            "kernel_inode": 241109,
        },
        {
            "protocol": "udp6" if ipv6 else "udp",
            "address": "::" if ipv6 else "0.0.0.0",
            "port": port,
            "kernel_inode": 241113,
        },
    ]


@pytest.mark.parametrize("profile", ["application", "native", "rootless"])
@pytest.mark.parametrize("with_udp", [False, True])
@pytest.mark.parametrize("reverse", [False, True])
def test_caddy_kernel_rows_preserve_original_family_order_and_values(
    helper, profile, with_udp, reverse
):
    rows = caddy_kernel_rows(port=8443 if profile == "rootless" else 55235)
    if profile != "rootless":
        for row in rows:
            row["address"] = "127.0.0.1"
    rows = rows if with_udp else rows[:1]
    if reverse:
        rows.reverse()
    before = copy.deepcopy(rows)
    identities = [id(row) for row in rows]
    helper["caddy_listeners"](rows, profile=profile, origin="https://127.0.0.1:55235")
    assert rows == before
    assert [id(row) for row in rows] == identities


@pytest.mark.parametrize("with_udp", [False, True])
@pytest.mark.parametrize("reverse", [False, True])
def test_rootless_caddy_accepts_measured_raw_ipv6_wildcard_without_normalization(
    helper, with_udp, reverse
):
    rows = caddy_kernel_rows(ipv6=True)
    rows = rows if with_udp else rows[:1]
    if reverse:
        rows.reverse()
    before = copy.deepcopy(rows)
    helper["caddy_listeners"](rows, profile="rootless", origin="https://127.0.0.1:33333")
    assert rows == before


@pytest.mark.parametrize("ipv6", [False, True])
@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("protocol", None),
        ("protocol", "TCP"),
        ("protocol", "sctp"),
        ("address", None),
        ("address", "127.0.0.1"),
        ("address", "::1"),
        ("address", "::ffff:0.0.0.0"),
        ("address", "0:0:0:0:0:0:0:0"),
        ("address", "::%eth0"),
        ("port", 8444),
        ("port", "8443"),
        ("port", 8443.0),
        ("port", True),
        ("kernel_inode", 0),
        ("kernel_inode", -1),
        ("kernel_inode", "241109"),
        ("kernel_inode", True),
        ("kernel_inode", 241109.0),
    ],
)
def test_rootless_caddy_refuses_unproved_or_reinterpreted_kernel_row(helper, ipv6, field, value):
    rows = caddy_kernel_rows(ipv6=ipv6)
    helper["caddy_listeners"](rows, profile="rootless", origin="https://127.0.0.1:33333")
    rows[0][field] = value
    with pytest.raises(ValueError, match="actual Caddy"):
        helper["caddy_listeners"](rows, profile="rootless", origin="https://127.0.0.1:33333")


@pytest.mark.parametrize("ipv6", [False, True])
@pytest.mark.parametrize(
    "mutation",
    [
        "missing-key",
        "extra-key",
        "duplicate-protocol",
        "duplicate-inode",
        "mixed-family",
        "udp-only",
        "extra-socket",
        "empty",
        "not-list",
        "not-row",
    ],
)
def test_rootless_caddy_requires_one_closed_family_and_unique_owned_sockets(helper, ipv6, mutation):
    rows: Any = caddy_kernel_rows(ipv6=ipv6)
    helper["caddy_listeners"](rows, profile="rootless", origin="https://127.0.0.1:33333")
    if mutation == "missing-key":
        del rows[0]["kernel_inode"]
    elif mutation == "extra-key":
        rows[0]["claimed_owner"] = 1
    elif mutation == "duplicate-protocol":
        rows[1]["protocol"] = rows[0]["protocol"]
    elif mutation == "duplicate-inode":
        rows[1]["kernel_inode"] = rows[0]["kernel_inode"]
    elif mutation == "mixed-family":
        rows[1] = caddy_kernel_rows(ipv6=not ipv6)[1]
    elif mutation == "udp-only":
        rows = rows[1:]
    elif mutation == "extra-socket":
        rows.append({**rows[0], "kernel_inode": 241114})
    elif mutation == "empty":
        rows = []
    elif mutation == "not-list":
        rows = tuple(rows)
    else:
        rows[0] = None
    with pytest.raises(ValueError, match="actual Caddy"):
        helper["caddy_listeners"](rows, profile="rootless", origin="https://127.0.0.1:33333")


@pytest.mark.parametrize("profile", ["application", "native"])
@pytest.mark.parametrize("ipv6", [False, True])
def test_native_caddy_cannot_borrow_container_wildcard_acceptance(helper, profile, ipv6):
    with pytest.raises(ValueError, match="actual Caddy"):
        helper["caddy_listeners"](
            caddy_kernel_rows(ipv6=ipv6, port=55235),
            profile=profile,
            origin="https://127.0.0.1:55235",
        )


@pytest.mark.parametrize("profile", ["application", "native"])
def test_native_caddy_port_boolean_cannot_equal_the_trusted_origin_port(helper, profile):
    rows = caddy_kernel_rows(port=1)[:1]
    rows[0]["address"] = "127.0.0.1"
    helper["caddy_listeners"](rows, profile=profile, origin="https://127.0.0.1:1")
    rows[0]["port"] = True
    with pytest.raises(ValueError, match="actual Caddy"):
        helper["caddy_listeners"](rows, profile=profile, origin="https://127.0.0.1:1")


@pytest.mark.parametrize("host_ip", ["0.0.0.0", "::", "::1", "127.0.0.2"])
def test_rootless_ipv6_listener_does_not_relax_exact_ipv4_host_publication(helper, host_ip):
    container, process, manifest = metadata_rootless_container("caddy", stage="ready")
    helper["caddy_listeners"](
        caddy_kernel_rows(ipv6=True),
        profile="rootless",
        origin=manifest["profiles"]["rootless"]["origin"],
    )
    helper["role_container"](container, process, manifest, "caddy", stage="ready")
    container["published_ports"][0]["host_ip"] = host_ip
    with pytest.raises(ValueError, match="rootless publication"):
        helper["role_container"](container, process, manifest, "caddy", stage="ready")


@pytest.mark.parametrize("role", ["api", "worker", "caddy"])
@pytest.mark.parametrize("stage", ["ready", "stopped"])
def test_rootless_manager_binds_applied_policy_before_gc_safe_final_state(helper, role, stage):
    helper["rootless_manager"](
        metadata_manager(role, stopped=stage == "stopped"), role, stage=stage
    )


@pytest.mark.parametrize(
    "mutation",
    [
        "missing-killmode",
        "force-kill",
        "killmode",
        "finite-stop",
        "wrong-manager",
        "unknown-pid",
        "unknown-cgroup",
        "inactive-before",
        "wrong-type",
        "missing-before",
        "missing-after",
        "live-after",
        "failed-after",
        "different-after",
        "wrong-shape",
        "unowned-group",
    ],
)
def test_rootless_manager_policy_or_drain_cannot_be_replaced_by_summary(  # noqa: PLR0912 - explicit policy/drain refusal matrix
    helper, mutation
):
    item = metadata_manager(stopped=True)
    before, after = item["manager_unit"]["before_stop"], item["manager_unit"]["after_stop"]
    if mutation == "missing-killmode":
        del before["KillMode"]
    elif mutation == "force-kill":
        before["SendSIGKILL"] = "yes"
    elif mutation == "killmode":
        before["KillMode"] = "control-group"
    elif mutation == "finite-stop":
        before["TimeoutStopUSec"] = "30s"
    elif mutation == "wrong-manager":
        before["Id"] = "unrelated.service"
    elif mutation == "unknown-pid":
        before["MainPID"] = "999"
    elif mutation == "unknown-cgroup":
        before["ControlGroup"] += "/other"
    elif mutation == "inactive-before":
        before["ActiveState"] = "inactive"
    elif mutation == "wrong-type":
        before["Type"] = "oneshot"
    elif mutation == "missing-before":
        del item["manager_unit"]["before_stop"]
    elif mutation == "missing-after":
        del item["manager_unit"]["after_stop"]
    elif mutation == "live-after":
        after["MainPID"] = "202"
    elif mutation == "failed-after":
        after["Result"] = "exit-code"
    elif mutation == "different-after":
        after["Id"] = "different.service"
    elif mutation == "wrong-shape":
        item["manager_unit"] = before
    else:
        item["owned_cgroups"] = []
    with pytest.raises(ValueError, match=r"rootless manager"):
        helper["rootless_manager"](item, "worker", stage="stopped")


@pytest.mark.parametrize(
    "mutation", ["same-container", "wrong-image", "missing-drain", "wrong-trust", "changed-report"]
)
def test_browser_launcher_receipt_requires_distinct_observed_phase_drains(
    helper, tmp_path, mutation
):
    report, manifest, runtime = metadata_browser()
    manifest["browser"] = {"trusted_image_sha256": "a" * 64, "untrusted_image_sha256": "b" * 64}
    filename = write(tmp_path / "browser-report.json", report)
    phases = {
        name: {
            "image_sha256": manifest["browser"][name + "_image_sha256"],
            "container_id": ("c" if name == "trusted" else "d") * 64,
            "init_identity": {"pid": 101, "start_ticks": "12345"},
            "exit_code": 0,
            "container_drained": True,
            "init_closed": True,
            "inputs_unchanged": True,
            "trust_mode": "private-ca" if name == "trusted" else "absent",
        }
        for name in ("trusted", "untrusted")
    }
    receipt = {
        "schema_version": 1,
        "fixture_id": manifest["fixture_id"],
        "profile": "application",
        "prefix": "",
        "workspace": str(tmp_path),
        "phases": phases,
        "report": record(filename),
    }
    helper["browser_launcher_receipt"](
        receipt, manifest=manifest, runtime=runtime, workspace=tmp_path
    )
    if mutation == "same-container":
        phases["trusted"]["container_id"] = phases["untrusted"]["container_id"]
    elif mutation == "wrong-image":
        phases["untrusted"]["image_sha256"] = "a" * 64
    elif mutation == "missing-drain":
        phases["untrusted"]["init_closed"] = False
    elif mutation == "wrong-trust":
        phases["untrusted"]["trust_mode"] = "private-ca"
    else:
        filename.write_bytes(b"{}\n")
    with pytest.raises(ValueError, match=r"functional|fixture"):
        helper["browser_launcher_receipt"](
            receipt, manifest=manifest, runtime=runtime, workspace=tmp_path
        )


@pytest.mark.parametrize(
    "mutation", ["untrusted-http", "missing-challenge", "missing-tools", "secret-field"]
)
def test_api_observations_require_native_challenge_and_no_untrusted_http(
    helper, tmp_path, mutation
):
    identity = {"fixture_id": "f", "generation_id": "a" * 32, "prefix": "/management"}
    ready = {"instance_id": "b" * 32, "identity": {"pid": 101, "start_ticks": "12345"}}
    base = {"schema_version": 1, **{key: identity[key] for key in ("fixture_id", "generation_id")}}
    events = []
    for phase in ("started", "draining", "stopped"):
        events.append(  # noqa: PERF401 - explicit lifecycle order is the independent expected fixture
            {
                **base,
                "event": "lifecycle",
                "phase": phase,
                **ready["identity"],
                "instance_id": ready["instance_id"],
                "capture_fingerprint": "c" * 64,
                "capture_descriptor_open": phase != "stopped",
                "streams_active": 0,
                "streams_accepting": phase != "stopped",
                "metadata_inflight": 0,
                "metadata_closed": phase == "stopped",
                "auth_active": 0,
                "auth_waiting": 0,
                "auth_reservations": 0,
                "auth_accepting": phase != "stopped",
                "auth_workers": [20],
                "auth_workers_joined": phase == "stopped",
                "operations_active": 0,
                "worker_available": True,
            }
        )
    for engine in ("chromium", "firefox", "webkit"):
        for endpoint, status, authentication, actor, method in [
            ("/ui", 401, "none", "browser", "GET"),
            ("/ui", 307, "basic", "browser", "GET"),
            ("/ui/", 200, "basic", "browser", "GET"),
            ("/api/v1/config/validate", 200, "basic", "browser", "POST"),
            ("/api/v1/capabilities", 200, "rest-reader", "node", "GET"),
            *[("/mcp/", 200, "mcp-reader", "node", "POST")] * 14,
        ]:
            events.insert(
                -2,
                {
                    **base,
                    "event": "http",
                    "phase": "trusted",
                    "engine": engine,
                    "actor": actor,
                    "method": method,
                    "path": "/management" + endpoint,
                    "status": status,
                    "authentication": authentication,
                    "instance_id": ready["instance_id"],
                    "request_id": "d" * 32,
                },
            )
    filename = tmp_path / "events.jsonl"

    def retain():
        filename.write_text("".join(json.dumps(row) + "\n" for row in events))

    retain()
    helper["api_events"](filename, identity, ready, stage="stopped")
    if mutation == "untrusted-http":
        events[1]["phase"] = "untrusted"
    elif mutation == "missing-challenge":
        events[:] = [row for row in events if row.get("status") != 401]
    elif mutation == "missing-tools":
        events[:] = [row for row in events if row.get("path") != "/management/mcp/"]
    else:
        events[1]["authorization"] = "supplemental test sentinel, never a credential"
    retain()
    with pytest.raises(ValueError, match=r"actual|HTTP|native|bearer|unsafe|untrusted"):
        helper["api_events"](filename, identity, ready, stage="stopped")


def metadata_protocol_snapshot(protocol, **changes):
    return {
        "cycle_id": protocol["cycle_id"],
        "transport_id": protocol["transport_id"],
        "disconnected": False,
        "response_started": True,
        "response_complete": False,
        "write_paused": False,
        "transport_closing": False,
        "write_buffer_bytes": 0,
        **changes,
    }


def metadata_transfer_facts(pid=1):
    """Independent private schema2 metadata; this is no runtime acceptance."""
    browser, manifest, _runtime = metadata_browser()
    ready = {
        "identity": {"pid": pid, "start_ticks": "999"},
        "instance_id": "a" * 32,
        "object_ids": {
            key: number + 10
            for number, key in enumerate(
                ("store", "pool", "runner", "verifier", "capture", "streams")
            )
        },
    }
    identity = {
        "schema_version": 1,
        "fixture_id": manifest["fixture_id"],
        "generation_id": "b" * 32,
        "prefix": "",
    }
    rows = []
    for engine, record in browser["engines"].items():
        for mode in ("cancel", "deadline"):
            started = 100_000_000_000
            duration = 2_000_000_000 if mode == "cancel" else 30_000_000_000
            protocol = {
                "identity": copy.deepcopy(ready["identity"]),
                "cycle_id": 101,
                "scope_id": 102,
                "protocol_id": 103,
                "transport_id": 104,
                "send": {
                    "module": "uvicorn.protocols.http.h11_impl",
                    "qualname": "RequestResponseCycle.send",
                    "source_sha256": (
                        "a3154a6c2cfaaaebe19ac7aa255dfe9b6b7b490de1da95274c033aa093e8c322"
                    ),
                },
                "protocol_class": {
                    "module": "__main__",
                    "qualname": "install_accepted_buffer_pressure.<locals>.AcceptedBufferProtocol",
                    "source_sha256": "c" * 64,
                },
                "socket": {
                    "descriptor": 8,
                    "device": 9,
                    "kernel_inode": 10101,
                    "family": "unix",
                    "type": "stream",
                    "send_buffer": 8192,
                },
            }
            initial = metadata_protocol_snapshot(protocol)
            paused = metadata_protocol_snapshot(
                protocol, write_paused=True, write_buffer_bytes=65536
            )
            disconnected = metadata_protocol_snapshot(
                protocol, disconnected=True, transport_closing=True
            )
            sends: list[dict[str, Any]] = [
                {
                    "sequence": 0,
                    "bytes": 65536,
                    "more_body": True,
                    "started_ns": started,
                    "finished_ns": started + 10,
                    "error_kind": None,
                    "protocol_before": initial,
                    "protocol_after": copy.deepcopy(paused),
                    "protocol_result": "submitted",
                },
                {
                    "sequence": 1,
                    "bytes": 65536,
                    "more_body": True,
                    "started_ns": started + 10,
                    "finished_ns": started + 10 + duration,
                    "error_kind": None if mode == "cancel" else "cancelled",
                    "protocol_before": paused,
                    "protocol_after": disconnected if mode == "cancel" else copy.deepcopy(paused),
                    "protocol_result": "disconnected_noop" if mode == "cancel" else "raised",
                },
            ]
            if mode == "cancel":
                # Original H11 returns normally for the remaining body/final
                # after disconnect. Preserve these literal raw ASGI facts.
                for size, more in ((65536, True), (3392, True), (0, False)):
                    number = len(sends)
                    sends.append(
                        {
                            "sequence": number,
                            "bytes": size,
                            "more_body": more,
                            "started_ns": sends[-1]["finished_ns"],
                            "finished_ns": sends[-1]["finished_ns"] + 10,
                            "error_kind": None,
                            "protocol_before": copy.deepcopy(disconnected),
                            "protocol_after": copy.deepcopy(disconnected),
                            "protocol_result": "disconnected_noop",
                        }
                    )
            rows.append(
                {
                    "schema_version": 2,
                    "fixture_id": identity["fixture_id"],
                    "generation_id": identity["generation_id"],
                    "phase": "trusted",
                    "engine": engine,
                    "actor": "node",
                    "request_id": record["static_abort"][mode]["request_id"],
                    "instance_id": ready["instance_id"],
                    "object_ids": copy.deepcopy(ready["object_ids"]),
                    "method": "GET",
                    "path": record["static_abort"][mode]["path"],
                    "status": 200,
                    "selected_body_bytes": 200000,
                    "started_ns": started,
                    "finished_ns": sends[-1]["finished_ns"] + 1000,
                    "disconnect_received": mode == "cancel",
                    "disconnect_ns": started + duration if mode == "cancel" else None,
                    "error_kind": None if mode == "cancel" else "cancelled",
                    "streams_before": {"active": 0, "tasks": []},
                    "streams_after": {"active": 0, "tasks": []},
                    "body_sends": sends,
                    "protocol": protocol,
                }
            )
            recount_transfer(rows[-1])
    return browser, ready, identity, rows


def recount_transfer(row):
    sends = row["body_sends"]
    completed = [item for item in sends if item["error_kind"] is None]
    submitted = [item for item in sends if item["protocol_result"] == "submitted"]
    row.update(
        body_send_started=len(sends),
        body_send_completed=len(completed),
        body_bytes_started=sum(item["bytes"] for item in sends),
        body_bytes_completed=sum(item["bytes"] for item in completed),
        final_send_started=any(not item["more_body"] for item in sends),
        final_send_completed=any(not item["more_body"] for item in completed),
        protocol_body_send_submitted=len(submitted),
        protocol_body_bytes_submitted=sum(item["bytes"] for item in submitted),
        protocol_final_send_submitted=any(not item["more_body"] for item in submitted),
    )


@pytest.mark.parametrize("pid", [1, 1234])
def test_transfer_proof_preserves_asgi_noops_and_inner_process_identity(helper, tmp_path, pid):
    browser, ready, identity, rows = metadata_transfer_facts(pid)
    first = rows[0]
    assert first["body_bytes_completed"] == first["selected_body_bytes"]
    assert first["final_send_completed"] is True
    assert first["error_kind"] is None
    assert first["protocol_body_bytes_submitted"] == 65536
    assert first["protocol_final_send_submitted"] is False
    filename = tmp_path / "transfers.jsonl"
    filename.write_text("".join(json.dumps(row) + "\n" for row in rows))
    helper["transfer_evidence"](filename, ready, identity, browser)


def test_transfer_cancel_can_raise_original_paused_drain_cancellation(helper, tmp_path):
    browser, ready, identity, rows = metadata_transfer_facts()
    row = rows[0]
    row["body_sends"] = row["body_sends"][:2]
    interrupted = row["body_sends"][-1]
    interrupted["error_kind"] = "cancelled"
    interrupted["protocol_result"] = "raised"
    row["error_kind"] = "cancelled"
    row["finished_ns"] = interrupted["finished_ns"] + 1000
    recount_transfer(row)
    assert row["body_bytes_completed"] == 65536
    assert row["final_send_completed"] is False
    filename = tmp_path / "transfers.jsonl"
    filename.write_text("".join(json.dumps(item) + "\n" for item in rows))
    helper["transfer_evidence"](filename, ready, identity, browser)


@pytest.mark.parametrize(
    "mutation",
    [
        "completion-won",
        "whole-body-submitted",
        "outer-generic-error",
        "early-deadline",
        "no-disconnect",
        "wrong-body",
        "wrong-objects",
        "missing-probe",
        "leaked-task",
        "unclassified-send-error",
        "false-counter",
        "schema1",
        "missing-protocol",
        "extra-protocol",
        "wrong-send-function",
        "wrong-source",
        "changed-entry-source",
        "wrong-class",
        "outer-pid",
        "boolean-pid",
        "zero-pid",
        "aliased-ticks",
        "wrong-family",
        "wrong-socket-type",
        "negative-fd",
        "boolean-pressure",
        "unmeasured-pressure",
        "wrong-cycle",
        "wrong-transport",
        "integer-flag",
        "boolean-buffer",
        "oversized-buffer",
        "false-result",
        "generic-error-beside-good-witness",
        "timeout-deadline",
        "unpaused-raised",
        "instant-noop",
        "already-disconnected",
        "resumed-submission",
        "invented-reconnection",
        "within-send-reconnection",
        "false-submission-count",
        "false-final-submission",
        "false-asgi-final",
        "complete-before",
        "missing-snapshot",
        "extra-snapshot",
    ],
)
def test_actual_transfer_facts_refuse_unproved_backpressure(helper, tmp_path, mutation):  # noqa: PLR0912, PLR0915 - independent finite proof corruptions
    browser, ready, identity, rows = metadata_transfer_facts()
    row = rows[0]
    send = row["body_sends"][1]
    if mutation == "completion-won":
        row["body_sends"][-1]["protocol_after"]["response_complete"] = True
    elif mutation == "whole-body-submitted":
        for item in row["body_sends"][:-1]:
            item["protocol_result"] = "submitted"
            item["protocol_before"]["disconnected"] = False
            item["protocol_after"]["disconnected"] = False
        recount_transfer(row)
    elif mutation == "outer-generic-error":
        row["error_kind"] = "send_error"
    elif mutation == "early-deadline":
        rows[1]["finished_ns"] = rows[1]["started_ns"] + 2_000_000_000
        rows[1]["body_sends"][-1]["finished_ns"] = rows[1]["finished_ns"]
    elif mutation == "no-disconnect":
        row["disconnect_received"] = False
    elif mutation == "wrong-body":
        row["selected_body_bytes"] = 1
    elif mutation == "wrong-objects":
        row["object_ids"]["pool"] = 999
    elif mutation == "missing-probe":
        rows.pop()
    elif mutation == "leaked-task":
        row["streams_after"] = {
            "active": 1,
            "tasks": [{"id": 991, "name": "hfcache-ui-send", "done": False}],
        }
    elif mutation in {"unclassified-send-error", "timeout-deadline"}:
        rows[1]["body_sends"][-1]["error_kind"] = (
            "other" if mutation == "unclassified-send-error" else "timeout"
        )
    elif mutation == "false-counter":
        row["body_send_completed"] = True
    elif mutation == "schema1":
        row["schema_version"] = 1
    elif mutation == "missing-protocol":
        del row["protocol"]
    elif mutation == "extra-protocol":
        row["protocol"]["claimed_uid"] = 981
    elif mutation == "wrong-send-function":
        row["protocol"]["send"]["qualname"] = "custom.send"
    elif mutation == "wrong-source":
        row["protocol"]["send"]["source_sha256"] = "d" * 64
    elif mutation == "changed-entry-source":
        row["protocol"]["protocol_class"]["source_sha256"] = "d" * 64
    elif mutation == "wrong-class":
        row["protocol"]["protocol_class"]["qualname"] = "custom.Protocol"
    elif mutation in {"outer-pid", "boolean-pid", "zero-pid"}:
        row["protocol"]["identity"]["pid"] = {
            "outer-pid": 22222,
            "boolean-pid": True,
            "zero-pid": 0,
        }[mutation]
    elif mutation == "aliased-ticks":
        row["protocol"]["identity"]["start_ticks"] = "0999"
    elif mutation == "wrong-family":
        row["protocol"]["socket"]["family"] = "inet"
    elif mutation == "wrong-socket-type":
        row["protocol"]["socket"]["type"] = "datagram"
    elif mutation == "negative-fd":
        row["protocol"]["socket"]["descriptor"] = -1
    elif mutation in {"boolean-pressure", "unmeasured-pressure"}:
        row["protocol"]["socket"]["send_buffer"] = (
            True if mutation == "boolean-pressure" else 212992
        )
    elif mutation in {"wrong-cycle", "wrong-transport"}:
        send["protocol_after"]["cycle_id" if mutation == "wrong-cycle" else "transport_id"] = 999
    elif mutation == "integer-flag":
        send["protocol_after"]["disconnected"] = 1
    elif mutation == "boolean-buffer":
        send["protocol_after"]["write_buffer_bytes"] = False
    elif mutation == "oversized-buffer":
        send["protocol_after"]["write_buffer_bytes"] = 1048577
    elif mutation == "false-result":
        send["protocol_result"] = "submitted"
    elif mutation == "generic-error-beside-good-witness":
        other = row["body_sends"][2]
        other["error_kind"] = "send_error"
        other["protocol_result"] = "raised"
        other["protocol_before"]["disconnected"] = False
        other["protocol_before"]["write_paused"] = True
        recount_transfer(row)
    elif mutation == "unpaused-raised":
        rows[1]["body_sends"][-1]["protocol_before"]["write_paused"] = False
    elif mutation == "instant-noop":
        send["started_ns"] = send["finished_ns"] - 100
    elif mutation == "already-disconnected":
        send["protocol_before"]["disconnected"] = True
        send["protocol_before"]["write_paused"] = False
    elif mutation == "resumed-submission":
        send["protocol_after"]["disconnected"] = False
        send["protocol_result"] = "submitted"
        recount_transfer(row)
    elif mutation in {"invented-reconnection", "within-send-reconnection"}:
        other = row["body_sends"][2]
        other["protocol_before"]["disconnected"] = mutation == "within-send-reconnection"
        other["protocol_after"]["disconnected"] = False
        other["protocol_result"] = "submitted"
        recount_transfer(row)
    elif mutation == "false-submission-count":
        row["protocol_body_send_submitted"] = True
    elif mutation == "false-final-submission":
        row["protocol_final_send_submitted"] = True
    elif mutation == "false-asgi-final":
        row["final_send_completed"] = False
    elif mutation == "complete-before":
        send["protocol_before"]["response_complete"] = True
    elif mutation == "missing-snapshot":
        del send["protocol_before"]
    else:
        send["protocol_before"]["request_headers"] = "supplemental sentinel, never a credential"
    filename = tmp_path / "transfers.jsonl"
    filename.write_text("".join(json.dumps(item) + "\n" for item in rows))
    with pytest.raises(ValueError, match=r"actual|original|completion"):
        helper["transfer_evidence"](filename, ready, identity, browser)


def metadata_origin(process, profile) -> dict[str, Any]:
    return {
        "schema_version": 2,
        "role": "worker",
        "profile": profile,
        "passed": True,
        "identity": {
            "pid": process["status"]["NSpid"][-1],
            "start_ticks": process["identity"]["start_ticks"],
        },
        "status": {
            "Pid": process["status"]["NSpid"][-1],
            "PPid": 0 if profile == "rootless" else process["identity"]["parent_pid"],
            "Uid": [981] * 4,
            "Gid": [981] * 4,
            "NSpid": [process["status"]["NSpid"][-1]],
            "NoNewPrivs": 1,
            "Seccomp": 2,
            "CapEff": "0" * 16,
            "CapBnd": "0" * 16,
        },
        "authority_probes": {
            name: {"attempted": True, "errno": 13, "denied": True}
            for name in ("basic", "writer", "reader", "mcp_reader", "hub")
        },
        "network_probes": {},
    }


def metadata_network_copy(value):
    if type(value) is not dict or set(value) != {"record", "body"}:
        message = "network evidence copy is incomplete"
        raise ValueError(message)
    return value["record"], value["body"]


def metadata_rootless_network(helper, monkeypatch) -> tuple[dict[str, Any], ...]:
    """Hand-authored proof fixtures exercise guards, never real confinement acceptance."""
    namespace = helper["rootless_origin_network"].__globals__
    stock = {
        "defaultAction": "SCMP_ACT_ERRNO",
        "defaultErrnoRet": 38,
        "syscalls": [{"names": ["socket", "socketcall", "read"], "action": "SCMP_ACT_ALLOW"}],
    }
    installer = runpy.run_path(str(ROOT / "scripts/install-container-release.py"))
    policy = installer["worker_seccomp"](stock)
    stock_hash = hashlib.sha256(helper["canonical"](stock)).hexdigest()
    policy_hash = hashlib.sha256(helper["canonical"](policy)).hexdigest()
    monkeypatch.setitem(namespace, "STOCK_POLICY_SHA256", stock_hash)
    monkeypatch.setitem(namespace, "WORKER_POLICY_SHA256", policy_hash)
    monkeypatch.setitem(namespace, "copied_evidence", metadata_network_copy)
    process = metadata_process()
    process["status"].update(Uid=[1000] * 4, Gid=[1000] * 4, NSpid=[102, 1])
    process["uid_map"] = process["gid_map"] = "0 524288 981\n981 1000 1\n982 525269 64555\n"
    cid = "c" * 64
    process["cgroup"] = "0::/user.slice/libpod-" + cid + ".scope/container\n"
    image = "a" * 64
    guest = {"identity": "owned-guest", "boot_id": "owned-boot"}
    receipt = {
        "schema_version": 1,
        "scope": "socket-family availability only; not worker confinement or feature acceptance",
        "guest_identity": guest["identity"],
        "boot_id": guest["boot_id"],
        "image_sha256": image,
        "stock_policy": {"path": namespace["STOCK_POLICY_PATH"], "sha256": stock_hash},
        "container_id": cid,
        "kernel_release": "6.12.0-test.x86_64",
        "machine": "x86_64",
        "container": {
            "image_sha256": image,
            "network_mode": "none",
            "readonly_rootfs": True,
            "user": "981:981",
            "security_options": ["no-new-privileges", "seccomp=" + namespace["STOCK_POLICY_PATH"]],
        },
        "host_process": copy.deepcopy(process),
        "controller_namespaces": {name: name + ":[456]" for name in process["namespaces"]},
        "probe_sha256": namespace["SOCKET_CONTROL_SHA256"],
        "outcome": {
            "schema_version": 1,
            "scope": "socket-family availability only; no bind/listen/connect",
            "identity": {"pid": 1, "start_ticks": "12345"},
            "status": {
                "Uid": "981 981 981 981",
                "Gid": "981 981 981 981",
                "NoNewPrivs": "1",
                "Seccomp": "2",
                "CapEff": "0" * 16,
                "CapBnd": "0" * 16,
                "NSpid": "1",
            },
            "families": {
                name: {"operation": "socket", "created": True, "closed": True, "errno": None}
                for name in ("unix", "inet", "inet6")
            },
        },
        "drain": {
            "container_id": cid,
            "running": False,
            "exit_code": 0,
            "attachment_waited": True,
            "attachment_exit_code": 0,
            "gate_identity_unchanged": True,
            "processes": [
                {"pid": pid, "start_ticks": "12345", "gone": True} for pid in (102, 200, 201)
            ],
            "cgroups": [
                {"path": "/user.slice/libpod-" + cid + suffix, "pids": []}
                for suffix in (".scope/container", ".conmon.scope")
            ],
        },
    }
    receipt_hash = hashlib.sha256(helper["canonical"](receipt)).hexdigest()
    probe = metadata_origin(process, "rootless")
    probe["network_probes"] = {
        name: {
            "attempted": True,
            "operation": "socket",
            "outcome": "denied",
            "error_class": "OSError",
            "errno": 38,
            "elapsed_ns": 1000,
            "denied": True,
        }
        for name in ("inet", "inet6")
    }
    probe["unix_socket"] = {"operation": "socket", "created": True, "closed": True, "errno": None}
    probe["seccomp_context"] = {
        "image_sha256": image,
        "policy": {
            "path": namespace["WORKER_POLICY_PATH"],
            "sha256": policy_hash,
            "default_action": "SCMP_ACT_ERRNO",
            "default_errno": 38,
            "native_arch": "SCMP_ARCH_X86_64",
            "allowed_socket_families": [1],
        },
        "availability": {"path": namespace["SOCKET_RECEIPT_PATH"], "sha256": receipt_hash},
    }
    generation = "b" * 32
    public = "/opt/hfcache-web005/rootless-generations-v8/" + generation + "/public/"
    worker = {
        "generation_id": generation,
        "container": {
            "image_sha256": image,
            "security_opt": ["no-new-privileges", "seccomp=" + namespace["WORKER_POLICY_PATH"]],
            "mounts": [
                {"source": public + leaf, "destination": path, "read_only": True}
                for leaf, path in (
                    ("worker-policy.json", namespace["WORKER_POLICY_PATH"]),
                    ("worker-availability.json", namespace["SOCKET_RECEIPT_PATH"]),
                )
            ],
        },
    }
    network = {
        name: {"record": {"path": "metadata-only", "sha256": checksum}, "body": body}
        for name, checksum, body in (
            ("worker_network", receipt_hash, receipt),
            ("worker_policy", policy_hash, policy),
            ("stock_policy", stock_hash, stock),
        )
    }
    manifest = {"guest": guest, "profiles": {"rootless": {"worker_image_sha256": image}}}
    return probe, process, network, worker, manifest


def test_rootless_denial_requires_derived_policy_and_independent_stock_control(helper, monkeypatch):
    probe, process, network, worker, manifest = metadata_rootless_network(helper, monkeypatch)
    helper["origin_probe"](
        probe,
        process,
        "worker",
        "rootless",
        network=network,
        worker=worker,
        manifest=manifest,
        invocation={},
    )


@pytest.mark.parametrize(
    "mutation",
    [
        "errno",
        "timeout",
        "connect",
        "unix",
        "image",
        "applied-policy",
        "writable-policy",
        "wrong-source",
        "stock-policy",
        "worker-policy",
        "stock-family",
        "probe-source",
        "boot",
        "uid-map",
        "same-netns",
        "control-init",
        "control-live",
        "control-cgroup",
        "bool-exit",
        "bool-schema",
        "missing-context",
        "missing-family",
        "inner-status",
        "inner-capabilities",
        "inner-bool",
        "bool-errno",
        "bool-elapsed",
        "extra-status",
        "control-no-init",
        "control-gate",
        "multiple-policies",
        "receipt-checksum",
    ],
)
def test_unbound_enosys_or_incomplete_rootless_control_refuses(  # noqa: PLR0912, PLR0915 - explicit adversarial evidence mutations
    helper, monkeypatch, mutation
):
    probe, process, network, worker, manifest = metadata_rootless_network(helper, monkeypatch)
    receipt = network["worker_network"]["body"]
    if mutation == "errno":
        probe["network_probes"]["inet"]["errno"] = 13
    elif mutation == "timeout":
        probe["network_probes"]["inet"].update(
            outcome="timeout", error_class="TimeoutError", errno=None
        )
    elif mutation == "connect":
        probe["network_probes"]["inet"]["operation"] = "connect"
    elif mutation == "unix":
        probe["unix_socket"]["created"] = False
    elif mutation == "image":
        worker["container"]["image_sha256"] = "e" * 64
    elif mutation == "applied-policy":
        worker["container"]["security_opt"] = ["no-new-privileges"]
    elif mutation == "writable-policy":
        worker["container"]["mounts"][0]["read_only"] = False
    elif mutation == "wrong-source":
        worker["container"]["mounts"][0]["source"] = "/opt/unrelated/worker-policy.json"
    elif mutation in {"stock-policy", "worker-policy"}:
        network[mutation.replace("-", "_")]["body"]["defaultErrnoRet"] = 1
    elif mutation == "stock-family":
        receipt["outcome"]["families"]["inet6"]["created"] = False
    elif mutation == "probe-source":
        receipt["probe_sha256"] = "e" * 64
    elif mutation == "boot":
        receipt["boot_id"] = "other"
    elif mutation == "uid-map":
        receipt["host_process"]["uid_map"] = "0 0 4294967295\n"
    elif mutation == "same-netns":
        receipt["controller_namespaces"]["net"] = receipt["host_process"]["namespaces"]["net"]
    elif mutation == "control-init":
        receipt["outcome"]["identity"]["start_ticks"] = "99999"
    elif mutation == "control-live":
        receipt["drain"]["processes"][0]["gone"] = False
    elif mutation == "control-cgroup":
        receipt["drain"]["cgroups"][0]["pids"] = [102]
    elif mutation == "bool-exit":
        receipt["drain"]["exit_code"] = False
    elif mutation == "bool-schema":
        probe["schema_version"] = True
    elif mutation == "missing-context":
        del probe["seccomp_context"]
    elif mutation == "missing-family":
        del probe["network_probes"]["inet6"]
    elif mutation == "inner-status":
        del probe["status"]["Gid"]
    elif mutation == "inner-capabilities":
        probe["status"]["CapEff"] = "0000000000000001"
    elif mutation == "inner-bool":
        probe["status"]["NoNewPrivs"] = True
    elif mutation == "bool-errno":
        probe["network_probes"]["inet"]["errno"] = True
    elif mutation == "bool-elapsed":
        probe["network_probes"]["inet"]["elapsed_ns"] = False
    elif mutation == "extra-status":
        probe["status"]["untrusted"] = True
    elif mutation == "control-no-init":
        receipt["drain"]["processes"][0]["pid"] = 999
    elif mutation == "control-gate":
        receipt["drain"]["gate_identity_unchanged"] = False
    elif mutation == "multiple-policies":
        worker["container"]["security_opt"].append("seccomp=/unrelated.json")
    else:
        probe["seccomp_context"]["availability"]["sha256"] = "0" * 64
    with pytest.raises(ValueError, match=r"rootless|stock|socket|origin|actual|control|policy"):
        helper["origin_probe"](
            probe,
            process,
            "worker",
            "rootless",
            network=network,
            worker=worker,
            manifest=manifest,
            invocation={},
        )


def metadata_queries(group, *, filtered):
    values = []
    for kind in (0, 1):
        for flags in (0, 1):
            identity = {
                "pid": 300 + kind * 2 + flags,
                "start_ticks": "10000",
                "cgroup": "0::/owned-controller\n",
            }
            ids = [417 if kind == 0 else 416] if filtered else []
            values.append(
                {
                    "attach_type": kind,
                    "query_flags": flags,
                    "rc": 0,
                    "errno": 0,
                    "attach_flags": 2 if flags == 0 and filtered else 0,
                    "reported_prog_count": len(ids),
                    "ids": ids,
                    "ids_buffer": ids + [0] * (64 - len(ids)),
                    "complete": True,
                    "truncated": False,
                    "backing_bytes": 256,
                    "semantic_prefix_bytes": 64,
                    "revision": 2 if flags == 0 and filtered else 0,
                    "tail_before_hex": "a5" * 192,
                    "tail_after_hex": "a5" * 192,
                    "tail_changed": False,
                    "query_process_exit": 0,
                    "timed_out": False,
                    "stderr_sha256": hashlib.sha256(b"").hexdigest(),
                    "entered": {
                        "identity": identity,
                        "fd_device": group["device"],
                        "fd_inode": group["inode"],
                        "attach_type": kind,
                        "query_flags": flags,
                    },
                    "query_process_gone": True,
                    "identity": identity,
                }
            )
    return values


def test_copied_network_evidence_reopens_and_hashes_actual_protected_bytes(
    helper, provisioned, monkeypatch
):
    root, _, _ = provisioned
    path = write(
        root / ".scratch/bundle/network-proof.json", {"schema_version": 2, "measured": True}
    )
    original = helper["file_record"]
    monkeypatch.setitem(
        helper["copied_evidence"].__globals__,
        "file_record",
        lambda value: original(value, root=root),
    )
    copied = {"record": record(path), "body": {"schema_version": 2, "measured": True}}
    assert helper["copied_evidence"](copied)[1] == copied["body"]
    copied["body"]["measured"] = False
    with pytest.raises(ValueError, match="retained original bytes"):
        helper["copied_evidence"](copied)
    copied["body"]["measured"] = True
    write(path, {"schema_version": 2, "measured": False})
    with pytest.raises(ValueError, match="digest"):
        helper["copied_evidence"](copied)


def metadata_native_network(helper, monkeypatch) -> tuple[dict[str, Any], ...]:
    """Independent hand fixtures represent no actual BPF, process or network acceptance."""
    namespace = helper["native_origin_network"].__globals__
    monkeypatch.setitem(namespace, "copied_evidence", metadata_network_copy)
    generation = "b" * 32
    invocation = {"fixture_id": "unit-only", "generation_id": generation, "profile": "native"}
    group = "/system.slice/web005-" + generation + "-worker.service"
    process = metadata_process()
    process["cgroup"] = "0::" + group + "\n"
    identity = {"pid": 102, "start_ticks": "12345"}
    probe = metadata_origin(process, "native")
    endpoints = {"inet": ["127.0.0.1", 45001], "inet6": ["::1", 45002]}
    for index, family in enumerate(("inet", "inet6")):
        probe["network_probes"][family] = {
            "attempted": True,
            "operation": "connect",
            "outcome": "timeout",
            "error_class": "TimeoutError",
            "errno": None,
            "started_ns": (10 + index * 3) * 10**9,
            "finished_ns": (12 + index * 3) * 10**9,
            "local_tuple": [endpoints[family][0], 46000 + index],
            "remote_tuple": endpoints[family],
            "nonce_sha256": str(index + 1) * 64,
        }
    programs = [packet_deny_program(), {**packet_deny_program(), "id": 416, "name": "sd_fw_egress"}]
    inode = {"device": 1, "inode": 2}

    def filters(captured):
        return {
            "captured_ns": captured * 10**9,
            "cgroup": group,
            "cgroup_identity": inode,
            "queries": metadata_queries(inode, filtered=True),
            "program_audit": {
                "schema_version": 1,
                "identity": {"pid": 500 + captured, "start_ticks": "10000", "state": "R"},
                "programs": copy.deepcopy(programs),
                "verified": True,
            },
        }

    control_process = copy.deepcopy(process)
    control_process["identity"]["pid"] = control_process["status"]["Pid"] = 200
    control_process["status"]["NSpid"] = [200]
    control_group = "/system.slice/web005-" + generation + "-network-control.service"
    control_process["cgroup"] = "0::" + control_group + "\n"
    control_inode = {"device": 1, "inode": 3}

    def control(phase, timestamp) -> dict[str, Any]:
        return {
            "phase": phase,
            "identity": {"pid": 200, "start_ticks": "12345"},
            "cgroup": control_group,
            "cgroup_identity": control_inode,
            "netns": process["namespaces"]["net"],
            "process": copy.deepcopy(control_process),
            "queries": metadata_queries(control_inode, filtered=False),
            "round_trips": {
                family: {
                    "started_ns": timestamp * 10**9,
                    "finished_ns": (timestamp + 1) * 10**9,
                    "local_tuple": [endpoints[family][0], 47000 + index + timestamp],
                    "remote_tuple": endpoints[family],
                    "nonce_sha256": hashlib.sha256((phase + family).encode()).hexdigest(),
                    "acknowledged": True,
                }
                for index, family in enumerate(("inet", "inet6"))
            },
        }

    before, after = control("before", 6), control("after", 21)
    fds = {
        family: {
            "descriptor": index + 4,
            "device": 1,
            "inode": index + 10,
            "local_tuple": endpoints[family],
        }
        for index, family in enumerate(("inet", "inet6"))
    }
    accepts = [
        {
            "family": family,
            "phase": row["phase"],
            "accepted_ns": trip["started_ns"] + 1000,
            "local_tuple": trip["remote_tuple"],
            "peer_tuple": trip["local_tuple"],
            "nonce_sha256": trip["nonce_sha256"],
            "acknowledged": True,
        }
        for row in (before, after)
        for family, trip in row["round_trips"].items()
    ]
    ready = {
        "schema_version": 2,
        "fixture_id": invocation["fixture_id"],
        "generation_id": generation,
        "identity": identity,
        "cgroup": group,
        "netns": process["namespaces"]["net"],
    }
    attempts = {**ready, "network_probes": probe["network_probes"]}
    verdict = {
        "schema_version": 2,
        "kind": "native-cgroup-packet-filter",
        "guest_identity": "owned-guest",
        "boot_id": "owned-boot",
        "fixture_id": invocation["fixture_id"],
        "generation_id": generation,
        "worker": {
            "identity": identity,
            "cgroup": group,
            "netns": process["namespaces"]["net"],
            "process_before": copy.deepcopy(process),
            "process_after": copy.deepcopy(process),
            "ready": ready,
            "attempts": attempts,
            "ready_sha256": hashlib.sha256(helper["canonical"](ready)).hexdigest(),
            "attempts_sha256": hashlib.sha256(helper["canonical"](attempts)).hexdigest(),
            "unit": {
                "name": group.rsplit("/", 1)[-1],
                "main_pid": 102,
                "invocation_id": "c" * 32,
                "cgroup": group,
                "ip_deny": ["0.0.0.0/0", "::/0"],
                "ip_allow": [],
                "private_network": False,
                "network_namespace_path": "",
                "address_families": ["AF_UNIX", "AF_INET", "AF_INET6"],
                "source_sha256": "d" * 64,
                "hardening": copy.deepcopy(namespace["NATIVE_HARDENING"]),
            },
        },
        "filters_before": filters(5),
        "filters_after": filters(20),
        "control_before": before,
        "control_after": after,
        "control_drain": {
            "identity": before["identity"],
            "unit_name": control_group.rsplit("/", 1)[-1],
            "process_gone": True,
            "cgroup_empty": True,
            "unit_exited": {
                "MainPID": "0",
                "ExecMainCode": "1",
                "ExecMainStatus": "0",
                "ActiveState": "active",
                "SubState": "exited",
                "InvocationID": "d" * 32,
            },
            "unit_final": {
                "MainPID": "0",
                "ExecMainCode": "0",
                "ExecMainStatus": "0",
                "ActiveState": "inactive",
                "SubState": "dead",
                "InvocationID": "",
            },
        },
        "listeners": {
            "owner": {"pid": 900, "start_ticks": "10000"},
            "netns": process["namespaces"]["net"],
            "endpoints": endpoints,
            "fds_before": fds,
            "fds_after": copy.deepcopy(fds),
            "started_ns": 10**9,
            "finished_ns": 25 * 10**9,
            "accepts": accepts,
            "threads": [
                {"id": index + 1000, "name": "control-listener-" + str(index), "alive": False}
                for index in (0, 1)
            ],
            "closed_descriptors": [4, 5],
        },
        "sources": dict.fromkeys(
            (
                "native_helper_sha256",
                "collector_sha256",
                "entrypoints_sha256",
                "network_helper_sha256",
                "query_source_sha256",
                "program_auditor_sha256",
                "control_source_sha256",
            ),
            "e" * 64,
        ),
        "completed_ns": 26 * 10**9,
        "packet_filter_denial_verified": True,
    }
    verdict["sources"]["program_auditor_sha256"] = namespace["PROGRAM_AUDITOR_SHA256"]
    probe["network_evidence_sha256"] = "f" * 64
    network = {
        "worker_network": {"record": {"path": "metadata-only", "sha256": "f" * 64}, "body": verdict}
    }
    worker = {"unit": {"InvocationID": "c" * 32}}
    manifest = {"guest": {"identity": "owned-guest", "boot_id": "owned-boot"}}
    return probe, process, network, worker, manifest, invocation


def test_packet_timeout_requires_complete_measured_conjunction(helper, monkeypatch):
    probe, process, network, worker, manifest, invocation = metadata_native_network(
        helper, monkeypatch
    )
    helper["origin_probe"](
        probe,
        process,
        "worker",
        "native",
        network=network,
        worker=worker,
        manifest=manifest,
        invocation=invocation,
    )


@pytest.mark.parametrize(
    "mutation",
    [
        "bare-timeout",
        "connected",
        "connection-refused",
        "unknown-error",
        "old-hash",
        "other-worker",
        "other-program",
        "program-allows",
        "query-fault",
        "query-bool",
        "query-empty",
        "query-revision",
        "query-canary",
        "query-32bytes",
        "query-fd",
        "control-filtered",
        "control-other-netns",
        "control-other-uid",
        "control-no-ack",
        "missing-accept",
        "worker-accepted",
        "control-after-too-early",
        "listener-rebound",
        "listener-open",
        "control-live",
        "control-no-positive-exit",
        "changed-hardening",
        "private-network",
        "wrong-auditor",
    ],
)
def test_native_packet_filter_conjunction_refuses_partial_or_coerced_proof(  # noqa: PLR0912, PLR0915 - explicit independent refusal matrix
    helper, monkeypatch, mutation
):
    probe, process, network, worker, manifest, invocation = metadata_native_network(
        helper, monkeypatch
    )
    verdict = network["worker_network"]["body"]
    query = verdict["filters_after"]["queries"][0]
    if mutation == "bare-timeout":
        del network["worker_network"]
    elif mutation == "connected":
        probe["network_probes"]["inet"].update(outcome="connected", error_class=None)
    elif mutation == "connection-refused":
        probe["network_probes"]["inet"].update(
            outcome="os_error", error_class="ConnectionRefusedError", errno=111
        )
    elif mutation == "unknown-error":
        probe["network_probes"]["inet"]["error_class"] = "OSError"
    elif mutation == "old-hash":
        probe["network_evidence_sha256"] = "0" * 64
    elif mutation == "other-worker":
        verdict["worker"]["process_after"]["identity"]["start_ticks"] = "99999"
    elif mutation == "other-program":
        verdict["filters_after"]["program_audit"]["programs"][0]["id"] = 999
    elif mutation == "program-allows":
        program = verdict["filters_after"]["program_audit"]["programs"][0]
        body = packet_instruction(0xB7, immediate=1) + packet_instruction(0x95)
        program.update(
            translated_hex=body.hex(),
            translated_bytes=len(body),
            translated_sha256=hashlib.sha256(body).hexdigest(),
        )
    elif mutation == "query-fault":
        query["query_process_exit"] = -11
    elif mutation == "query-bool":
        query["rc"] = False
    elif mutation == "query-empty":
        query.update(ids=[], ids_buffer=[0] * 64, reported_prog_count=0)
    elif mutation == "query-revision":
        query["revision"] += 1
    elif mutation == "query-canary":
        query["tail_after_hex"] = "00" * 192
    elif mutation == "query-32bytes":
        query["semantic_prefix_bytes"] = 32
    elif mutation == "query-fd":
        query["entered"]["fd_inode"] = 999
    elif mutation == "control-filtered":
        verdict["control_before"]["queries"] = verdict["filters_before"]["queries"]
    elif mutation == "control-other-netns":
        verdict["control_before"]["netns"] = "net:[999]"
    elif mutation == "control-other-uid":
        verdict["control_before"]["process"]["status"]["Uid"] = [982] * 4
    elif mutation == "control-no-ack":
        verdict["control_before"]["round_trips"]["inet"]["acknowledged"] = False
    elif mutation == "missing-accept":
        verdict["listeners"]["accepts"].pop()
    elif mutation == "worker-accepted":
        verdict["listeners"]["accepts"][0]["peer_tuple"] = probe["network_probes"]["inet"][
            "local_tuple"
        ]
    elif mutation == "control-after-too-early":
        verdict["control_after"]["round_trips"]["inet"]["started_ns"] = 9 * 10**9
    elif mutation == "listener-rebound":
        verdict["listeners"]["fds_after"]["inet"]["inode"] += 1
    elif mutation == "listener-open":
        verdict["listeners"]["threads"][0]["alive"] = True
    elif mutation == "control-live":
        verdict["control_drain"]["process_gone"] = False
    elif mutation == "control-no-positive-exit":
        verdict["control_drain"]["unit_exited"]["ExecMainCode"] = "0"
    elif mutation == "changed-hardening":
        verdict["worker"]["unit"]["hardening"]["ProcSubset"] = "all"
    elif mutation == "private-network":
        verdict["worker"]["unit"]["private_network"] = True
    else:
        verdict["sources"]["program_auditor_sha256"] = "0" * 64
    verdict["worker"]["attempts_sha256"] = hashlib.sha256(
        helper["canonical"](verdict["worker"]["attempts"])
    ).hexdigest()
    with pytest.raises(
        ValueError, match=r"packet|network|native|worker|actual|positive|functional"
    ):
        helper["origin_probe"](
            probe,
            process,
            "worker",
            "native",
            network=network,
            worker=worker,
            manifest=manifest,
            invocation=invocation,
        )
