"""ADR150: optional captured build input, original release/runtime schemas."""

import hashlib
import json
import tomllib
from pathlib import Path

import pytest

from hfcache.server_config import validate_server_config_mapping
from tests.unit.test_container_release_installer import (
    deployment as deployment,  # noqa: PLC0414 - original hermetic staged-release fixture
)
from tests.unit.test_container_release_installer import installer, staged

HELPER_SOURCES = {
    "host-helper/host-helper.py": "scripts/host-helper.py",
    "host-helper/hfcache-host-helper.service": "packaging/systemd/hfcache-host-helper.service",
    "host-helper/host_policy.py": "src/hfcache/host_policy.py",
    "host-helper/host_protocol.py": "src/hfcache/host_protocol.py",
    "host-helper/host_peer.py": "src/hfcache/host_peer.py",
    "host-helper/hfcache-host-helper.cil": "packaging/selinux/hfcache-host-helper.cil",
}


def capture_helpers(deployment):
    for name, original in HELPER_SOURCES.items():
        body = (Path(__file__).parents[2] / original).read_bytes()
        path = deployment.source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
        deployment.release["files"][name] = hashlib.sha256(body).hexdigest()


def input_file(deployment, body, *, listed=True, capture=True):
    path = deployment.source / installer._HOST_HELPER_INPUT
    path.write_bytes(body)
    if listed:
        deployment.release["files"][installer._HOST_HELPER_INPUT] = hashlib.sha256(body).hexdigest()
        if capture:
            capture_helpers(deployment)
    return path


def rendered(deployment):
    return installer._rendered(
        deployment.source, deployment.release, deployment.default.read_bytes()
    )


def test_explicit_true_input_stages_indexes_and_recomputes_exact_helper_optin(deployment):
    body = b"schema_version = 1\nenabled = true\n"
    input_file(deployment, body)
    selected = staged(deployment)
    assert installer._verify_stage(selected) == deployment.release
    configuration = tomllib.loads((selected / "rendered/server.toml").read_text())
    assert configuration["host_helper"] == {
        "enabled": True,
        "profile": "rootless",
        "api_host_gid": deployment.release["service_gid"],
    }
    assert "deployment_sha256" not in configuration["host_helper"]
    assert validate_server_config_mapping(configuration).host_helper.enabled is True
    index = json.loads((selected / "artifact-index.json").read_bytes())
    assert index["files"][installer._HOST_HELPER_INPUT] == hashlib.sha256(body).hexdigest()
    assert (selected / installer._HOST_HELPER_INPUT).read_bytes() == body
    assert set(installer._HOST_HELPER_COPIES) == set(HELPER_SOURCES)
    for name in HELPER_SOURCES:
        assert (selected / name).read_bytes() == (deployment.source / name).read_bytes()
        assert index["files"][name] == deployment.release["files"][name]
    assert set(json.loads((selected / "rendered/runtime.json").read_bytes())) == {
        "schema_version",
        "service_uid",
        "service_gid",
        "app_image",
        "caddy_image",
    }
    assert set(json.loads((selected / "container-release.json").read_bytes())) == {
        "schema_version",
        "version",
        "hostname",
        "service_uid",
        "service_gid",
        "app_image",
        "caddy_image",
        "source_commit",
        "wheel_sha256",
        "files",
    }


def test_false_and_unlisted_inputs_preserve_all_original_rendered_bytes(deployment):
    original = rendered(deployment)
    input_file(deployment, b"schema_version = 1\nenabled = true\n", listed=False)
    assert rendered(deployment) == original
    input_file(deployment, b"schema_version = 1\nenabled = false\n", capture=False)
    assert rendered(deployment) == original
    selected = staged(deployment)
    assert installer._verify_stage(selected) == deployment.release
    assert not (selected / "host-helper").exists()


@pytest.mark.parametrize("missing", sorted(HELPER_SOURCES))
def test_enabled_stage_requires_every_captured_helper_before_creating_staging(deployment, missing):
    input_file(deployment, b"schema_version=1\nenabled=true\n")
    del deployment.release["files"][missing]
    # The unlisted source still exists, so a directory scan must not fill the
    # manifest's missing authority or produce a partly staged release.
    assert (deployment.source / missing).is_file()
    with pytest.raises(ValueError, match="incomplete captured host helper closure"):
        staged(deployment)
    assert not (deployment.prefix / "releases/.container-stage-0.2.0").exists()
    assert not (deployment.prefix / "releases/0.2.0").exists()
    assert deployment.calls == []


def test_changed_captured_selinux_policy_refuses_original_source_hash_check(deployment):
    input_file(deployment, b"schema_version=1\nenabled=true\n")
    policy = deployment.source / "host-helper/hfcache-host-helper.cil"
    policy.write_bytes(policy.read_bytes() + b"\n; changed after capture\n")
    with pytest.raises(ValueError, match="source artifact changed"):
        staged(deployment)
    assert not (deployment.prefix / "releases/0.2.0").exists()


def test_rehashed_staged_selinux_policy_cannot_override_captured_manifest_digest(deployment):
    input_file(deployment, b"schema_version=1\nenabled=true\n")
    selected = staged(deployment)
    name = "host-helper/hfcache-host-helper.cil"
    path = selected / name
    path.write_bytes(path.read_bytes() + b"\n; changed after staging\n")
    index_path = selected / "artifact-index.json"
    index = json.loads(index_path.read_bytes())
    index["files"][name] = hashlib.sha256(path.read_bytes()).hexdigest()
    index_path.write_bytes(installer.encoded(index))
    with pytest.raises(ValueError, match="staged release artifact changed"):
        installer._verify_stage(selected)


@pytest.mark.parametrize(
    "body",
    [
        b"enabled=true\n",
        b"schema_version=true\nenabled=true\n",
        b"schema_version=2\nenabled=true\n",
        b'schema_version=1\nenabled="true"\n',
        b"schema_version=1\nenabled=1\n",
        b"schema_version=1\nenabled=true\nextra=1\n",
        b"schema_version=1\nenabled=true\nenabled=false\n",
        b"schema_version=1\nenabled=true\n" + b"#" * 4096,
    ],
)
def test_unknown_ambiguous_wrong_type_or_oversize_build_inputs_refuse(deployment, body):
    input_file(deployment, body)
    with pytest.raises(ValueError, match=r"."):
        rendered(deployment)


def test_original_stage_hash_check_refuses_changed_input_and_keeps_source(deployment):
    path = input_file(deployment, b"schema_version=1\nenabled=true\n")
    path.write_bytes(b"schema_version=1\nenabled=false\n")
    with pytest.raises(ValueError, match="source artifact changed"):
        staged(deployment)
    assert path.read_bytes() == b"schema_version=1\nenabled=false\n"


def test_existing_helper_table_cannot_be_ambiguously_overridden(deployment):
    path = deployment.source / "packaging/containers/server.toml.in"
    path.write_bytes(path.read_bytes() + b"\n[host_helper]\nenabled=false\n")
    deployment.release["files"]["packaging/containers/server.toml.in"] = hashlib.sha256(
        path.read_bytes()
    ).hexdigest()
    input_file(deployment, b"schema_version=1\nenabled=true\n")
    with pytest.raises(ValueError, match="ambiguous host helper"):
        rendered(deployment)


def test_rendered_config_edit_cannot_bypass_original_stage_verifier(deployment):
    input_file(deployment, b"schema_version=1\nenabled=true\n")
    selected = staged(deployment)
    path = selected / "rendered/server.toml"
    path.write_bytes(path.read_bytes().replace(b"enabled = true", b"enabled = false"))
    # Rehashing the edited output is insufficient: original recomputation still
    # binds the optional input and refuses a different rendered configuration.
    index_path = selected / "artifact-index.json"
    index = json.loads(index_path.read_bytes())
    index["files"]["rendered/server.toml"] = hashlib.sha256(path.read_bytes()).hexdigest()
    index_path.write_bytes(installer.encoded(index))
    with pytest.raises(ValueError, match="rendered policy or provenance changed"):
        installer._verify_stage(selected)
