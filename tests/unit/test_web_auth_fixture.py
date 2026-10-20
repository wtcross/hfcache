"""Disposable native-browser fixture refuses unsafe authority before any effect."""

import asyncio
import hashlib
import json
import os
import runpy
import socket
import ssl
import stat
import subprocess
import sys
import zipfile
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import httpx
import pytest

import hfcache
from hfcache import server as server_module
from hfcache import server_config
from hfcache.api import app as application_module
from hfcache.services.bootstrap import query_version
from tests.unit.test_script_help import (
    test_every_approved_python_help_precedes_runtime_access as assert_safe_help,
)
from tests.unit.test_server_bootstrap import isolate_logging  # noqa: F401 - autouse isolation
from tests.unit.test_web_basic_sockets import (
    tls_identity as auth_fixture_tls,  # noqa: F401 - owned TLS identity
)

ROOT = Path(__file__).absolute().parents[2]
HELPER = ROOT / "scripts/check-web-auth-fixture.py"
FIXTURE_ID = "830b4146-e3c3-4d55-8d13-45fb98767c72"
IMAGE = "bdfda2a8fdf48707c5e50a49bd3e06d8d0c759153dc8ee057d8a81c3450bb3e9"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, sort_keys=True) + "\n")
    path.chmod(0o600)
    return path


@pytest.fixture
def helper():
    return runpy.run_path(str(HELPER))


@pytest.fixture
def provisioned(tmp_path):
    """Owned metadata only; no fake prerequisite establishes browser acceptance."""
    root = tmp_path / "repository"
    root.mkdir(mode=0o700)
    scratch = root / ".scratch"
    scratch.mkdir(mode=0o700)
    bundle = scratch / "bundle"
    bundle.mkdir(mode=0o700)
    source = root / "src/hfcache"
    source.mkdir(parents=True)
    package_files = ("__init__.py", "api/__init__.py", "services/__init__.py")
    for name in package_files:
        member = source / name
        member.parent.mkdir(exist_ok=True)
        member.write_bytes(b'"""Independent source identity."""\n')
    files = {"src/hfcache/" + name: sha(source / name) for name in package_files}
    inputs = write_json(bundle / "source-inputs.json", {"schema_version": 1, "files": files})
    installed = bundle / "installed/hfcache"
    installed.mkdir(parents=True)
    for name in package_files:
        member = installed / name
        member.parent.mkdir(exist_ok=True)
        member.write_bytes((source / name).read_bytes())
    wheel = bundle / "fixture.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        for name in ("", "api", "services"):
            archive.write(source / name, "hfcache/" + name)
        for name in package_files:
            archive.write(source / name, "hfcache/" + name)
    marker = write_json(
        bundle / "provisioned.json",
        {"schema_version": 1, "fixture_id": FIXTURE_ID, "repository_root": str(root)},
    )
    launcher = bundle / "launcher"
    launcher.write_text("#!/bin/sh\nexit 99\n")
    launcher.chmod(0o700)
    playwright = bundle / "playwright.mjs"
    playwright.write_text("export const fixtureOnly = true;\n")
    evidence = bundle / "evidence"
    evidence.mkdir(mode=0o700)
    tls = {}
    tls_hashes = {}
    for name in (
        "ca_certificate",
        "certificate",
        "private_key",
        "untrusted_certificate",
        "untrusted_private_key",
    ):
        path = bundle / (name + ".pem")
        path.write_text("not a certificate; metadata guard tests only\n")
        path.chmod(0o600)
        tls[name] = str(path)
        tls_hashes[name] = sha(path)
    manifest = {
        "schema_version": 1,
        "fixture_id": FIXTURE_ID,
        "marker_path": str(marker),
        "source": {
            "parent_commit": "a" * 40,
            "snapshot_sha256": hashlib.sha256(
                json.dumps(files, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest(),
            "input_manifest_path": str(inputs),
            "input_manifest_sha256": sha(inputs),
            "label": "WEB-004, this commit",
        },
        "wheel": {"path": str(wheel), "sha256": sha(wheel)},
        "installed": {
            "module_root": str(installed),
            "files": {name: files["src/hfcache/" + name] for name in package_files},
        },
        "toolchain": {
            "node_version": "24.18.1",
            "playwright_version": "1.64.1",
            "image_manifest_sha256": IMAGE,
            "playwright_module": str(playwright),
            "playwright_module_sha256": sha(playwright),
        },
        "launcher": {"path": str(launcher), "sha256": sha(launcher)},
        "tls": tls | {"hashes": tls_hashes},
        "origins": {
            "trusted": "https://127.0.0.1:20101",
            "foreign": "https://127.0.0.1:20102",
            "untrusted": "https://127.0.0.1:20103",
        },
        "evidence_root": str(evidence),
    }
    path = write_json(bundle / "manifest.json", manifest)
    return root, path, manifest


def test_public_help_has_no_runtime_access(monkeypatch, capsys):
    assert_safe_help(monkeypatch, capsys, "check-web-auth-fixture.py")


def test_protected_metadata_validates_without_starting_a_service(helper, provisioned, monkeypatch):
    root, path, manifest = provisioned

    def forbidden(*args, **kwargs):
        pytest.fail("metadata validation attempted a runtime effect")

    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    result = helper["validate_manifest"](str(path), root=root)
    assert result["fixture_id"] == manifest["fixture_id"]
    assert list(Path(manifest["evidence_root"]).iterdir()) == []


def test_normal_wheel_directories_are_only_parent_metadata_not_installed_files(helper, provisioned):
    root, path, manifest = provisioned
    with zipfile.ZipFile(manifest["wheel"]["path"]) as archive:
        directories = [item.filename for item in archive.infolist() if item.is_dir()]
    assert set(directories) == {"hfcache/", "hfcache/api/", "hfcache/services/"}
    result = helper["validate_manifest"](str(path), root=root)
    assert set(result["installed"]["files"]) == {
        "__init__.py",
        "api/__init__.py",
        "services/__init__.py",
    }


@pytest.mark.parametrize(
    "kind",
    [
        "extra-empty-directory",
        "directory-traversal",
        "directory-alias",
        "duplicate-directory",
        "file-directory-collision",
        "symlink",
        "special",
        "directory-mode",
        "file-mode",
        "nonempty-directory",
        "oversized",
        "duplicate-file",
    ],
)
def test_wheel_directory_support_keeps_all_adversarial_member_refusals(helper, provisioned, kind):
    root, path, manifest = provisioned
    wheel = Path(manifest["wheel"]["path"])
    if kind in {"directory-mode", "file-mode", "nonempty-directory"}:
        with zipfile.ZipFile(wheel) as archive:
            contents = [(item, archive.read(item)) for item in archive.infolist()]
        with zipfile.ZipFile(wheel, "w") as archive:
            for item, payload in contents:
                content = payload
                if kind == "directory-mode" and item.filename == "hfcache/api/":
                    item.external_attr = (stat.S_IFREG | 0o755) << 16
                elif kind == "file-mode" and item.filename == "hfcache/__init__.py":
                    item.external_attr = (stat.S_IFREG | 0o666) << 16
                elif kind == "nonempty-directory" and item.filename == "hfcache/api/":
                    content = b"invalid directory data"
                archive.writestr(item, content)
    else:
        names = {
            "extra-empty-directory": "hfcache/unused/",
            "directory-traversal": "hfcache/../escape/",
            "directory-alias": "hfcache//api/",
            "duplicate-directory": "hfcache/api/",
            "file-directory-collision": "hfcache/__init__.py/",
            "symlink": "hfcache/link",
            "special": "hfcache/device",
            "oversized": "hfcache/large.py",
            "duplicate-file": "hfcache/__init__.py",
        }
        item = zipfile.ZipInfo(names[kind])
        item.create_system = 3
        mode = stat.S_IFDIR | 0o755 if item.is_dir() else stat.S_IFREG | 0o644
        if kind == "symlink":
            mode = stat.S_IFLNK | 0o777
        elif kind == "special":
            mode = stat.S_IFCHR | 0o600
        item.external_attr = mode << 16
        payload = b"x" * (8 * 1024 * 1024 + 1) if kind == "oversized" else b""
        with zipfile.ZipFile(wheel, "a") as archive:
            if kind in {"duplicate-directory", "duplicate-file"}:
                with pytest.warns(UserWarning, match="Duplicate name"):
                    archive.writestr(item, payload)
            else:
                archive.writestr(item, payload)
    manifest["wheel"]["sha256"] = sha(wheel)
    write_json(path, manifest)
    with pytest.raises(ValueError, match="wheel"):
        helper["validate_manifest"](str(path), root=root)
    assert list(Path(manifest["evidence_root"]).iterdir()) == []


@pytest.mark.parametrize(
    "value", ["relative.json", "/srv/hfcache/unowned.json", "/tmp/../fixture", ""]
)
def test_unsafe_paths_refuse_before_any_lstat(helper, monkeypatch, value):
    def forbidden(*args, **kwargs):
        pytest.fail("unsafe fixture path reached filesystem discovery")

    monkeypatch.setattr(Path, "lstat", forbidden)
    with pytest.raises(ValueError, match="fixture"):
        helper["owned_path"](value)


@pytest.mark.parametrize(
    "kind",
    ["leaf-symlink", "ancestor-symlink", "hardlink", "writable", "private-key", "scratch-mode"],
)
def test_unsafe_owned_metadata_refuses(helper, provisioned, kind):
    root, path, manifest = provisioned
    if kind == "leaf-symlink":
        copied = path.with_name("original.json")
        path.rename(copied)
        path.symlink_to(copied)
    elif kind == "ancestor-symlink":
        actual = path.parent.with_name("actual")
        path.parent.rename(actual)
        path.parent.symlink_to(actual, target_is_directory=True)
    elif kind == "hardlink":
        os.link(path, path.with_name("alias.json"))
    elif kind == "writable":
        path.chmod(0o620)
    elif kind == "private-key":
        Path(manifest["tls"]["private_key"]).chmod(0o644)
    else:
        (root / ".scratch").chmod(0o755)
    with pytest.raises(ValueError, match="fixture"):
        helper["validate_manifest"](str(path), root=root)


@pytest.mark.parametrize(
    "kind",
    [
        "schema",
        "marker",
        "snapshot",
        "source-bytes",
        "wheel-hash",
        "installed-bytes",
        "installed-extra",
        "installed-untracked",
        "node",
        "playwright",
        "image",
        "launcher",
        "origin-http",
        "origin-host",
        "origin-userinfo",
        "origin-path",
        "origin-zero-port",
        "origin-duplicate",
    ],
)
def test_drift_or_ambient_authority_refuses(  # noqa: PLR0912 - independent prerequisite refusal inventory
    helper, provisioned, kind
):
    root, path, manifest = provisioned
    if kind == "schema":
        manifest["schema_version"] = True
    elif kind == "marker":
        write_json(Path(manifest["marker_path"]), {"schema_version": 1})
    elif kind == "snapshot":
        manifest["source"]["snapshot_sha256"] = "b" * 64
    elif kind == "source-bytes":
        (root / "src/hfcache/__init__.py").write_text("changed\n")
    elif kind == "wheel-hash":
        manifest["wheel"]["sha256"] = "b" * 64
    elif kind == "installed-bytes":
        (Path(manifest["installed"]["module_root"]) / "__init__.py").write_text("changed\n")
    elif kind == "installed-extra":
        manifest["installed"]["files"]["not-in-wheel.py"] = "b" * 64
    elif kind == "installed-untracked":
        (Path(manifest["installed"]["module_root"]) / "not-in-wheel.py").write_text("changed\n")
    elif kind in {"node", "playwright"}:
        manifest["toolchain"][kind + "_version"] = "0.0.0"
    elif kind == "image":
        manifest["toolchain"]["image_manifest_sha256"] = "b" * 64
    elif kind == "launcher":
        manifest["launcher"]["sha256"] = "b" * 64
    elif kind == "origin-duplicate":
        manifest["origins"]["foreign"] = manifest["origins"]["trusted"]
    else:
        manifest["origins"]["trusted"] = {
            "origin-http": "http://127.0.0.1:20101",
            "origin-host": "https://production.invalid:20101",
            "origin-userinfo": "https://user@127.0.0.1:20101",
            "origin-path": "https://127.0.0.1:20101/path",
            "origin-zero-port": "https://127.0.0.1:0",
        }[kind]
    write_json(path, manifest)
    with pytest.raises(ValueError, match=r"fixture|source|wheel|installed"):
        helper["validate_manifest"](str(path), root=root)
    assert list(Path(manifest["evidence_root"]).iterdir()) == []


@pytest.mark.parametrize("filesystem", ["nfs", "nfs4", "cifs", "fuse.sshfs", "unknown"])
def test_network_or_unknown_backing_refuses_from_mount_metadata(helper, filesystem):
    metadata = f"1 0 0:1 / / rw - xfs root rw\n2 1 0:2 / /repo rw - {filesystem} remote rw\n"
    with pytest.raises(ValueError, match="approved local filesystem"):
        helper["prove_local_path"](Path("/repo/.scratch/fixture"), metadata)


def test_source_snapshot_cannot_claim_unrelated_old_wheel(helper, provisioned):
    root, path, manifest = provisioned
    source = root / "src/hfcache/__init__.py"
    source.write_text("source was changed without rebuilding the wheel\n")
    files = {"src/hfcache/__init__.py": sha(source)}
    inputs = Path(manifest["source"]["input_manifest_path"])
    write_json(inputs, {"schema_version": 1, "files": files})
    manifest["source"]["input_manifest_sha256"] = sha(inputs)
    manifest["source"]["snapshot_sha256"] = hashlib.sha256(
        json.dumps(files, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    write_json(path, manifest)
    with pytest.raises(ValueError, match="reviewed source snapshot"):
        helper["validate_manifest"](str(path), root=root)


def test_actual_two_listener_generations_reuse_the_provisioned_port_after_active_close(helper):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    origin = f"https://127.0.0.1:{port}"
    for _ in range(2):
        with helper["bind_listener"](origin) as listener:
            listener.settimeout(2)
            listener.listen(1)
            with socket.create_connection(("127.0.0.1", port), timeout=2) as client:
                accepted, _peer = listener.accept()
                with accepted:
                    # The fixture server actively closes its accepted stream,
                    # so the next generation must tolerate server TIME_WAIT.
                    accepted.shutdown(socket.SHUT_WR)
                    assert client.recv(1) == b""


def test_unowned_listener_origin_refuses_before_socket_creation(helper, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("unowned origin reached listener creation")

    monkeypatch.setattr(socket, "socket", forbidden)
    with pytest.raises(ValueError, match="provisioned canonical loopback"):
        helper["bind_listener"]("https://production.invalid:443")


@pytest.fixture
def reported():
    """Synthetic evidence-parser fixture only; never used as functional acceptance."""
    cases = [
        "native-challenge-version",
        "same-origin-capabilities",
        "same-origin-json-post",
        "foreign-text",
        "foreign-multipart",
        "foreign-form",
        "foreign-preflight",
        "untrusted-ca-refused",
    ]
    report: dict[str, Any] = {"schema_version": 1, "fixture_id": FIXTURE_ID, "engines": {}}
    observations = []
    trusted, foreign = "https://127.0.0.1:20101", "https://127.0.0.1:20102"
    origins = {"trusted": trusted, "foreign": foreign, "untrusted": "https://127.0.0.1:20103"}
    for number, engine in enumerate(("chromium", "firefox", "webkit")):
        report["engines"][engine] = {
            "passed": 8,
            "failed": 0,
            "skipped": 0,
            "browser_closed": True,
            "descendants_closed": True,
            "untrusted_certificate_rejected": True,
            "browser_pid": 100 + number,
            "process": {
                "kind": "live",
                "pid": 100 + number,
                "status": {"uids": [1000] * 4, "cap_eff": "0000000000000000", "no_new_privs": 1},
                "command": {"disabling_flags_absent": True, "representation": "nul-separated-argv"},
            },
            "cases": [{"case_id": case, "status": "passed"} for case in cases],
            "network_observation": {
                "mode": "passive-origin-observer",
                "request_interception": False,
                "limit": 256,
                "request_count": 3,
                "expected_origins": origins,
                "invalid": False,
                "overflow": False,
                "observations": [
                    {
                        "category": category,
                        "scheme": "https:",
                        "host": "127.0.0.1",
                        "port": 20101 + index,
                    }
                    for index, category in enumerate(("trusted", "foreign", "untrusted"))
                ],
            },
        }
        if engine == "chromium":
            report["engines"][engine]["sandbox"] = {
                "verified": True,
                "evaluation": "You are adequately sandboxed.",
                "diagnostics": {
                    "Layer 1 Sandbox": "Namespace",
                    "PID namespaces": "Yes",
                    "Network namespaces": "Yes",
                    "Seccomp-BPF sandbox": "Yes",
                },
                "renderers": [{"pid": 200}],
            }
        base = {
            "profile": "trusted",
            "engine": engine,
            "method": "GET",
            "path": "/api/v1/version",
            "origin": "",
            "authentication": "absent-or-other",
            "content_type": "",
            "basic_challenge": False,
        }
        observations.extend(
            [
                base | {"status": 401, "basic_challenge": True},
                base | {"status": 200, "authentication": "basic"},
                base
                | {
                    "method": "POST",
                    "status": 200,
                    "authentication": "basic",
                    "origin": trusted,
                    "path": "/api/v1/config/validate",
                    "content_type": "application/json",
                },
                *[
                    base
                    | {
                        "method": "POST",
                        "status": 403,
                        "authentication": "basic",
                        "origin": foreign,
                        "content_type": content_type,
                    }
                    for content_type in (
                        "text/plain",
                        "multipart/form-data",
                        "application/x-www-form-urlencoded",
                    )
                ],
                base | {"method": "OPTIONS", "origin": foreign, "status": 401},
            ]
        )
        observations.extend(
            [
                base | {"profile": "foreign", "status": 401, "basic_challenge": True},
                base | {"profile": "foreign", "status": 200, "authentication": "basic"},
            ]
        )
    return (
        report,
        {"fixture_id": FIXTURE_ID, "origins": origins},
        observations,
    )


def test_evidence_parser_accepts_complete_per_engine_evidence(helper, reported):
    helper["accept_evidence"](*reported, "")


@pytest.mark.parametrize(
    "kind",
    [
        "zero-count",
        "skip",
        "bool-count",
        "missing-case",
        "duplicate-case",
        "missing-engine",
        "unknown-id",
        "undrained",
        "infrastructure",
        "no-observations",
        "no-engine-label",
        "no-challenge",
        "preemptive",
        "no-origin-write",
        "unauthenticated-form",
        "missing-preflight",
        "successful-foreign",
        "privileged-browser",
        "zombie-browser",
        "missing-sandbox",
        "live-descendant",
        "network-error-negative",
        "untrusted-http",
        "observer-missing",
        "observer-invalid",
        "observer-overflow",
        "observer-interception",
        "observer-unsafe-metadata",
        "foreign-no-challenge",
    ],
)
def test_positive_report_alone_never_hides_missing_cases_or_real_http(  # noqa: PLR0912, PLR0915 - explicit refusal inventory
    helper, reported, kind
):
    report, manifest, observations = reported
    item = report["engines"]["firefox"]
    if kind == "zero-count":
        item["passed"] = 0
    elif kind == "observer-missing":
        del item["network_observation"]
    elif kind == "observer-invalid":
        item["network_observation"]["invalid"] = True
    elif kind == "observer-overflow":
        item["network_observation"]["overflow"] = True
    elif kind == "observer-interception":
        item["network_observation"]["request_interception"] = True
    elif kind == "observer-unsafe-metadata":
        item["network_observation"]["observations"][0]["query"] = "never-retain-query"
    elif kind == "foreign-no-challenge":
        observations[:] = [
            row
            for row in observations
            if not (
                row["engine"] == "firefox" and row["profile"] == "foreign" and row["status"] == 401
            )
        ]
    elif kind == "skip":
        item["skipped"] = 1
    elif kind == "bool-count":
        item["skipped"] = False
    elif kind == "missing-case":
        item["cases"].pop()
    elif kind == "duplicate-case":
        item["cases"][-1] = item["cases"][0]
    elif kind == "missing-engine":
        del report["engines"]["firefox"]
    elif kind == "unknown-id":
        report["fixture_id"] = "different"
    elif kind == "undrained":
        item["browser_closed"] = False
    elif kind == "infrastructure":
        item["infrastructure_failed"] = True
    elif kind == "no-observations":
        observations.clear()
    elif kind == "privileged-browser":
        item["process"]["status"]["uids"] = [0] * 4
    elif kind == "zombie-browser":
        item["process"]["kind"] = "zombie"
    elif kind == "missing-sandbox":
        del report["engines"]["chromium"]["sandbox"]
    elif kind == "live-descendant":
        item["descendants_closed"] = False
    elif kind == "network-error-negative":
        item["untrusted_certificate_rejected"] = False
    elif kind == "untrusted-http":
        observations.append(observations[0] | {"profile": "untrusted", "engine": "firefox"})
    else:
        firefox = [row for row in observations if row["engine"] == "firefox"]
        if kind == "no-engine-label":
            for row in firefox:
                row["engine"] = "unclassified"
        elif kind == "no-challenge":
            firefox[0]["basic_challenge"] = False
        elif kind == "preemptive":
            firefox[0]["authentication"] = "basic"
        elif kind == "no-origin-write":
            firefox[2]["origin"] = ""
        elif kind == "unauthenticated-form":
            firefox[5]["authentication"] = "absent-or-other"
        elif kind == "missing-preflight":
            firefox[6]["method"] = "GET"
        else:
            firefox[3]["status"] = 200
    with pytest.raises(ValueError, match=r"native-browser|engine"):
        helper["accept_evidence"](report, manifest, observations, "")


@pytest.mark.parametrize(
    "mode",
    [
        "success",
        "launcher-failure",
        "partial-setup",
        "tls-startup",
        "lifespan-failure",
        "cancel-active",
    ],
)
def test_real_api_lifecycle_drains_before_raw_sockets_close(  # noqa: PLR0915 - actual process/listener lifecycle matrix
    helper,
    monkeypatch,
    tmp_path,
    auth_fixture_tls,  # noqa: F811 - imported shared fixture
    mode,
):
    """Actual TLS/Argon/app cleanup; a fake launcher is NOT browser acceptance.

    This source-app regression tests the same orchestrator installed by the guest.
    Native browser/installed-wheel acceptance remains a separate real guest run.
    """
    manifest_path = tmp_path / "lifecycle-manifest.json"
    origins = {}
    sockets = []
    for name in ("trusted", "foreign", "untrusted"):
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.bind(("127.0.0.1", 0))
        sockets.append(listener)
        origins[name] = f"https://127.0.0.1:{listener.getsockname()[1]}"
    for listener in sockets:
        listener.close()
    launcher = tmp_path / "lifecycle-launcher"
    launcher.write_text(
        f"#!{sys.executable}\n"
        "import base64,http.client,json,ssl,sys,time\n"
        "from pathlib import Path\n"
        "from urllib.parse import urlsplit\n"
        "credentials=json.load(sys.stdin)\n"
        "manifest=json.loads(Path(sys.argv[2]).read_text())\n"
        "endpoint=urlsplit(manifest['origins']['trusted'])\n"
        "context=ssl.create_default_context(cafile=manifest['tls']['certificate'])\n"
        "connection=http.client.HTTPSConnection('localhost',endpoint.port,context=context,timeout=10)\n"
        "pair=(credentials['username']+':'+credentials['password']).encode()\n"
        "authorization='Basic '+base64.b64encode(pair).decode()\n"
        "connection.request('GET','/api/v1/version',headers={'Host':endpoint.netloc,'Authorization':authorization})\n"
        "response=connection.getresponse()\n"
        "assert response.status==200\n"
        "response.read();connection.close()\n"
        "workspace=Path(sys.argv[4]);(workspace/'browser-report.json').write_text('{}')\n"
        + ("time.sleep(60)\n" if mode == "cancel-active" else "")
        + ("raise SystemExit(1)\n" if mode == "launcher-failure" else "")
    )
    launcher.chmod(0o700)
    manifest = {
        "fixture_id": FIXTURE_ID,
        "installed": {"module_root": str(Path(hfcache.__file__).absolute().parent)},
        "source": {"label": "source-only actual lifecycle regression"},
        "wheel": {},
        "origins": origins,
        "launcher": {"path": str(launcher)},
        "_manifest_path": str(manifest_path),
        "tls": {
            "certificate": str(auth_fixture_tls[0]),
            "private_key": str(auth_fixture_tls[1]),
            "untrusted_certificate": str(auth_fixture_tls[0]),
            "untrusted_private_key": str(auth_fixture_tls[1]),
        },
    }
    write_json(manifest_path, manifest)
    # Only the browser-evidence seam is replaced. All actual application,
    # configuration, TLS, hash workers and Uvicorn lifespans remain unchanged.
    helper["run"].__globals__["accept_evidence"] = lambda *_: None
    apps = []
    actual_create_app = application_module.create_app

    def capture_app(*args, **kwargs):
        app = actual_create_app(*args, **kwargs)
        apps.append(app)
        if mode == "lifespan-failure" and len(apps) == 1:
            actual_lifespan = app.router.lifespan_context

            @asynccontextmanager
            async def failing_shutdown(application):
                async with actual_lifespan(application):
                    yield
                message = "injected shutdown failure after actual worker closure"
                raise RuntimeError(message)

            app.router.lifespan_context = failing_shutdown
        return app

    monkeypatch.setattr(application_module, "create_app", capture_app)
    actual_validate = server_config.validate_server_config_mapping
    calls = 0

    def partial_validate(value):
        nonlocal calls
        calls += 1
        if mode == "partial-setup" and calls == 2:
            message = "injected partial setup refusal"
            raise ValueError(message)
        return actual_validate(value)

    monkeypatch.setattr(server_config, "validate_server_config_mapping", partial_validate)
    actual_build = server_module.build_server
    built = []

    def broken_tls_build(*args, **kwargs):
        server = actual_build(*args, **kwargs)
        built.append(server)
        if mode == "tls-startup" and len(built) == 2:
            invalid_public_certificate = tmp_path / "invalid-public-certificate.pem"
            invalid_public_certificate.write_text("not a PEM certificate\n")
            server.config.ssl_certfile = str(invalid_public_certificate)
            actual_serve = server.serve

            async def serve_after_real_hash(*args, **kwargs):
                endpoint = urlsplit(origins["trusted"])
                # The first real listener is already ready. A deliberate wrong
                # password performs real Argon work without acquiring the
                # helper's in-memory generated password or reading its PHC file.
                context = ssl.create_default_context(cafile=auth_fixture_tls[0])
                async with httpx.AsyncClient(verify=context, trust_env=False) as client:
                    response = await client.get(
                        f"https://localhost:{endpoint.port}/api/v1/version",
                        headers={"Host": endpoint.netloc},
                        auth=("owned-native-operator", "deliberately-wrong-fixture-password"),
                    )
                assert response.status_code == 401
                assert apps[0].state.basic_provider.stats.failures == 1
                await actual_serve(*args, **kwargs)

            monkeypatch.setattr(server, "serve", serve_after_real_hash)
        return server

    monkeypatch.setattr(server_module, "build_server", broken_tls_build)
    workspace = tmp_path / "workspace"
    workspace.mkdir(mode=0o700)

    async def exercise():
        task = asyncio.create_task(helper["run"](manifest, workspace))
        if mode == "cancel-active":
            async with asyncio.timeout(20):
                while not any(
                    getattr(app.state, "basic_provider", None) is not None
                    and app.state.basic_provider.stats.active > 0
                    for app in apps
                ):
                    if task.done():
                        await task
                        pytest.fail("real hash was not observed active")
                    await asyncio.sleep(0.001)
            task.cancel()
            await asyncio.sleep(0.01)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
        elif mode == "launcher-failure":
            with pytest.raises(ValueError, match="native-browser authentication checks failed"):
                await task
        elif mode == "partial-setup":
            with pytest.raises(ValueError, match="injected partial setup"):
                await task
        elif mode == "tls-startup":
            with pytest.raises(ssl.SSLError):
                await task
        elif mode == "lifespan-failure":
            with pytest.raises(ValueError, match="complete worker/listener drain"):
                await task
        else:
            await task

    asyncio.run(exercise())
    evidence = json.loads((workspace / "api-evidence.json").read_text())
    assert len(evidence["profiles"]) == ({"partial-setup": 1, "tls-startup": 2}.get(mode, 3))
    assert evidence["auth_workers_joined"] is True
    if mode == "tls-startup":
        assert evidence["auth_worker_ids"]
    assert not evidence.get("launcher_drain_unknown")
    assert not evidence.get("lifespan_drain_unknown")
    for profile in evidence["profiles"]:
        assert profile["listener_closed"] is True
        assert profile["api_task_done"] is True
        if mode == "tls-startup" and profile["name"] == "foreign":
            assert profile["api_exit_clean"] is False
            assert profile["lifespan_started"] is False
            assert profile["lifespan_shutdown"] is False
            assert profile["auth_active"] is None
            continue
        failed_shutdown = mode == "lifespan-failure" and profile["name"] == "trusted"
        assert profile["api_exit_clean"] is not failed_shutdown
        assert profile["lifespan_failed"] is failed_shutdown
        assert profile["lifespan_shutdown"] is True
        assert profile["auth_accepting"] is False
        assert (
            profile["auth_active"] == profile["auth_waiting"] == profile["auth_reservations"] == 0
        )
        assert profile["archive_absent"] is True
    assert all(getattr(app.state, "basic_provider", None) is None for app in apps)
    if mode == "success":
        runtime = json.loads((workspace / "runtime.json").read_text())
        assert set(runtime) == {"fixture_id", "prefix", "expected_application"}
        assert runtime["expected_application"] == query_version().data["application"]
