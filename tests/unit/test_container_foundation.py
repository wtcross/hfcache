"""Decision 129: actual UBI ancestry and isolated native runtime proof contract."""

import ast
import importlib.util
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
IMAGE = "sha256:" + "a" * 64
BASE = "sha256:" + "b" * 64
LAYER = "sha256:" + "c" * 64


@pytest.fixture
def proof():
    spec = importlib.util.spec_from_file_location(
        "foundation", ROOT / "scripts/check-container-foundation.py"
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def pins():
    return json.loads((ROOT / "packaging/containers/images.json").read_text())


def valid_result(proof, pins):
    return {
        "schema_version": 1,
        "python_version": pins["python_distribution"]["version"],
        "ca_sha256": pins["ca_bundle_sha256"],
        **dict.fromkeys(proof._FLAGS, True),
        "os_id": "rhel",
        "os_version": "10.2",
        "architecture": "x86_64",
        "uid": 981,
        "gid": 981,
        "account": "hfcache",
        "imported": list(proof._MODULES),
        "trusted_ca_count": 140,
        "glibc": "glibc 2.39",
        "openssl": "OpenSSL 3.5.7 9 Jun 2026",
        "caio": {
            "linux_aio_available": True,
            "thread_aio_available": True,
            "linux_uring_available": False,
            "preferred": "caio.linux_aio",
        },
    }


def test_actual_ordered_base_diff_ids_are_required_not_labels(proof):
    base = {"Id": BASE, "RootFS": {"Layers": [LAYER]}}
    actual = {"Id": IMAGE, "RootFS": {"Layers": [LAYER, IMAGE]}}
    result = proof.foundation_identity(base, actual)
    assert result == {
        "base_config_id": BASE,
        "base_diff_ids": [LAYER],
        "image_config_id": IMAGE,
        "diff_id_prefix_verified": True,
    }


@pytest.mark.parametrize(
    ("base_layers", "layers"),
    [
        ([], [LAYER]),
        ([LAYER], []),
        ([LAYER], [BASE, LAYER]),
        ([LAYER, BASE], [LAYER]),
        (["untrusted"], ["untrusted", LAYER]),
    ],
)
def test_missing_reordered_or_malformed_base_prefix_cannot_pass(proof, base_layers, layers):
    with pytest.raises(ValueError, match="diffID prefix"):
        proof.foundation_identity(
            {"Id": BASE, "RootFS": {"Layers": base_layers}},
            {"Id": IMAGE, "RootFS": {"Layers": layers}},
        )


def test_payload_and_arguments_prove_native_ca_nss_without_host_mounts_or_jobs(proof, pins):
    ast.parse(proof._PAYLOAD)
    arguments = proof.run_arguments(IMAGE, "hfcache-foundation-fixture", "marker", pins)
    assert arguments[:3] == ["/usr/bin/podman", "--remote=false", "run"]
    for required in (
        "--pull=never",
        "--http-proxy=false",
        "--network=none",
        "--read-only",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges",
        "--user=981:981",
    ):
        assert required in arguments
    for forbidden in (
        "--volume",
        "--mount",
        "--secret",
        "--replace",
        "--rm",
        "--init",
        "--privileged",
    ):
        assert forbidden not in arguments
    assert not any("/srv" in item or "label=disable" in item for item in arguments)
    assert arguments[-2:] == [pins["ca_bundle_sha256"], "3.14.6"]
    for name in proof._MODULES:
        assert name in proof._PAYLOAD
    assert "getaddrinfo('localhost'" in proof._PAYLOAD
    assert "CERT_REQUIRED" in proof._PAYLOAD
    assert "ssl.create_default_context()" in proof._PAYLOAD
    assert "verify_targets" not in proof._PAYLOAD


@pytest.mark.parametrize(
    "change",
    [
        None,
        {"SSL_CERT_FILE": "/untrusted"},
        {"SSL_CERT_DIR": "/untrusted"},
        {"HF_TOKEN": "private"},
    ],
)
def test_payload_retains_only_the_fixed_image_ca_environment(proof, pins, change):
    tree = ast.parse(proof._PAYLOAD)
    checks: list[ast.stmt] = [
        node
        for node in tree.body
        if isinstance(node, ast.Assert) and "os.environ" in ast.unparse(node)
    ]
    program = compile(ast.Module(body=checks, type_ignores=[]), "fixture-env", "exec")
    environment = {
        "HF_HUB_OFFLINE": "1",
        "SSL_CERT_FILE": "/etc/ssl/cert.pem",
        "HF_XET_LOG_DEST": "/dev/null",
    }
    if change is None:
        exec(program, {"os": SimpleNamespace(environ=environment)})
    else:
        with pytest.raises(AssertionError):
            exec(program, {"os": SimpleNamespace(environ=environment | change)})
    arguments = proof.run_arguments(IMAGE, "hfcache-foundation-fixture", "marker", pins)
    assert not any(item.startswith(("--env=SSL_CERT", "--unsetenv=SSL_CERT")) for item in arguments)
    assert "--env=HF_XET_LOG_DEST=/dev/null" in arguments


@pytest.mark.parametrize(
    "change",
    [
        {"preferred": "unregistered-backend"},
        {"preferred": "caio.python_aio"},
        {"linux_aio_available": False},
        {"thread_aio_available": False},
        {"linux_uring_available": True},
    ],
)
def test_supported_caio_fallback_is_proved_without_enabling_uring(proof, pins, change):
    result = valid_result(proof, pins)
    result["caio"].update(change)
    with pytest.raises(ValueError, match="fallback proof"):
        proof.validate_result(result, pins)


@pytest.mark.parametrize("installed", [None, "pip", "ensurepip", "uv"])
def test_module_installers_are_refused_even_without_path_entrypoints(proof, installed):
    checks: list[ast.stmt] = [
        node
        for node in ast.parse(proof._PAYLOAD).body
        if isinstance(node, ast.Assert) and "find_spec" in ast.unparse(node)
    ]
    assert len(checks) == 1
    program = compile(ast.Module(body=checks, type_ignores=[]), "fixture-module-installers", "exec")
    context = {
        "importlib": SimpleNamespace(
            util=SimpleNamespace(find_spec=lambda name: object() if name == installed else None)
        )
    }
    if installed is None:
        exec(program, context)
    else:
        with pytest.raises(AssertionError):
            exec(program, context)


@pytest.mark.parametrize(
    "change",
    [
        {"schema_version": True},
        {"python_version": "3.14.8"},
        {"ca_sha256": "0" * 64},
        {"read_only_root": False},
        {"credential_masks": False},
        {"uid": True},
        {"trusted_ca_count": 0},
        {"trusted_ca_count": True},
        {"imported": []},
        {"os_id": "debian"},
        {"glibc": "unregistered private input"},
    ],
)
def test_partial_or_contradictory_output_cannot_be_accepted(proof, pins, change):
    with pytest.raises(ValueError, match="does not establish"):
        proof.validate_result(valid_result(proof, pins) | change, pins)


def fake_runtime(proof, monkeypatch, pins, workspace, *, bad_container=False):
    calls = []
    result = valid_result(proof, pins)
    marker = "fixture"
    monkeypatch.setattr(proof.secrets, "token_hex", lambda _: marker)
    original_run = subprocess.run

    def run(arguments, **kwargs):
        calls.append(arguments)
        assert arguments[:2] == ["/usr/bin/podman", "--remote=false"]
        if arguments[2] == "run":
            assert kwargs["timeout"] == 90
            kwargs["stdout"].write(json.dumps(result).encode())
            return subprocess.CompletedProcess(arguments, 0)
        if arguments[2] == "info":
            body = {
                "host": {"security": {"rootless": True}},
                "store": {"graphRoot": str(workspace.parent)},
            }
        elif arguments[2:4] == ["image", "inspect"]:
            body = [
                {
                    "Id": BASE if arguments[-1] == pins["python"] else IMAGE,
                    "RootFS": {
                        "Layers": [LAYER] if arguments[-1] == pins["python"] else [LAYER, IMAGE]
                    },
                }
            ]
        elif arguments[2] == "inspect":
            body = [
                {
                    "Id": "d" * 64,
                    "Config": {"Labels": {"io.hfcache.foundation": marker}},
                    "Image": IMAGE,
                    "State": {"Running": bad_container, "ExitCode": 0},
                    "HostConfig": {"NetworkMode": "none"},
                    "Mounts": [],
                }
            ]
        else:
            return original_run(arguments, **kwargs)
        return subprocess.CompletedProcess(arguments, 0, stdout=json.dumps(body))

    monkeypatch.setattr(proof.subprocess, "run", run)
    return calls


def test_exact_one_shot_proof_retains_identity_ancestry_and_source_without_unknown_fields(
    proof, monkeypatch, pins, tmp_path
):
    source = tmp_path / "images.json"
    source.write_text(json.dumps(pins | {"unknown": "DO_NOT_ECHO"}))
    record = tmp_path / "build.json"
    record.write_text(
        json.dumps(
            {
                "image_id": IMAGE,
                "source_commit": "e" * 40,
                "source_dirty": True,
                "unknown": "DO_NOT_ECHO",
            }
        )
    )
    workspace = tmp_path / "proof"
    calls = fake_runtime(proof, monkeypatch, pins, workspace)
    result = proof.prove(IMAGE, workspace, source, build_record=record)
    assert result["base_manifest"] == pins["python"]
    assert result["base_config_id"] == BASE
    assert result["base_diff_ids"] == [LAYER]
    assert result["container_retained_stopped"] is True
    assert result["build_provenance"]["source_dirty"] is True
    assert "DO_NOT_ECHO" not in (workspace / "proof.json").read_text()
    assert len(calls) == 5
    assert all("stop" not in call and "rm" not in call for call in calls)


def test_running_or_unexplained_container_refuses_and_preserves_logs(
    proof, monkeypatch, pins, tmp_path
):
    source = tmp_path / "images.json"
    source.write_text(json.dumps(pins))
    workspace = tmp_path / "proof"
    fake_runtime(proof, monkeypatch, pins, workspace, bad_container=True)
    with pytest.raises(ValueError, match="lifecycle or mount boundary"):
        proof.prove(IMAGE, workspace, source)
    assert (workspace / "stdout.log").exists()
    assert not (workspace / "proof.json").exists()


def test_root_refuses_before_any_engine_or_fixture_access(proof, monkeypatch, tmp_path):
    monkeypatch.setattr(proof.os, "geteuid", lambda: 0)
    monkeypatch.setattr(proof, "engine", lambda *_: pytest.fail("engine called"))
    with pytest.raises(ValueError, match="rootless"):
        proof.prove(IMAGE, tmp_path / "proof", tmp_path / "missing")


def test_existing_evidence_directory_is_never_merged_or_removed(proof, monkeypatch, pins, tmp_path):
    source = tmp_path / "images.json"
    source.write_text(json.dumps(pins))
    workspace = tmp_path / "proof"
    workspace.mkdir()
    (workspace / "unknown").write_bytes(b"preserve")
    calls = fake_runtime(proof, monkeypatch, pins, workspace)
    with pytest.raises(FileExistsError):
        proof.prove(IMAGE, workspace, source)
    assert (workspace / "unknown").read_bytes() == b"preserve"
    assert all(call[2] != "run" for call in calls)
