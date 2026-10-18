#!/usr/bin/env python3
"""Build decision 129's UBI-only Caddy stages from fixed public byte donors.

Run rootless with explicitly prefetched images. No server, network, host mount,
credential, publication or cleanup of an earlier context is authorized here.
"""

import argparse
import importlib.util
import json
import os
import re
import secrets
import shutil
import subprocess
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location(
    "hfcache_container_build_helpers", REPOSITORY / "scripts/build-container.py"
)
if _SPEC is None or _SPEC.loader is None:
    message = "fixed container build helpers are unavailable"
    raise RuntimeError(message)
_HELPERS = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_HELPERS)
local_path = _HELPERS.local_path
digest = _HELPERS.digest
refuse = _HELPERS.refuse
executable = _HELPERS.executable

_HEX = re.compile(r"[0-9a-f]{64}\Z")
_IMAGE = re.compile(r"localhost/hfcache:[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}\Z")
_INPUT_FIELDS = {
    "platform",
    "python",
    "caddy",
    "build",
    "ca_bundle_image",
    "ca_bundle_sha256",
    "uv_binary_image",
    "caddy_binary_image",
    "caddy_binary_sha256",
    "python_distribution",
}
_VERSION = "v2.11.7"
_MAX_INPUT_BYTES = 16384
_MAX_PROOF_BYTES = 4096
_PROOF_LINES = 3
_PROBE = """set -eu
test "$(id -u)" = 981
test "$(id -g)" = 981
capabilities=$(/usr/sbin/getcap /usr/bin/caddy)
test -z "$capabilities"
sha256sum /usr/bin/caddy /etc/ssl/cert.pem
/usr/bin/caddy version
"""


def _unique_pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            refuse("duplicate public image input field")
        result[key] = value
    return result


def foundation(path: Path) -> dict[str, str]:
    """Only pinned micro stages and the reviewed binary/Red Hat PEM donors."""
    with local_path(path).open("rb") as source:
        body = source.read(_MAX_INPUT_BYTES + 1)
    if not 0 < len(body) <= _MAX_INPUT_BYTES:
        refuse("public image inputs are empty or oversized")
    data = json.loads(body, object_pairs_hook=_unique_pairs)
    if not isinstance(data, dict) or set(data) != _INPUT_FIELDS:
        refuse("public image input fields are invalid")
    prefixes = {
        "caddy": "registry.access.redhat.com/ubi10/ubi-micro@sha256:",
        "build": "registry.access.redhat.com/ubi10/ubi-micro@sha256:",
        "ca_bundle_image": "registry.access.redhat.com/ubi10/ubi-minimal@sha256:",
        "caddy_binary_image": "docker.io/library/caddy@sha256:",
    }
    if data["platform"] != "linux/amd64":
        refuse("Caddy build platform must be linux/amd64")
    for field, prefix in prefixes.items():
        value = data[field]
        if not isinstance(value, str) or not value.startswith(prefix):
            refuse("public image donor or micro stage is invalid")
        if not _HEX.fullmatch(value.removeprefix(prefix)):
            refuse("public image inputs must use exact SHA256 identities")
    for field in ("caddy_binary_sha256", "ca_bundle_sha256"):
        if not isinstance(data[field], str) or not _HEX.fullmatch(data[field]):
            refuse("public byte donor hash is invalid")
    return {key: data[key] for key in (*prefixes, "caddy_binary_sha256", "ca_bundle_sha256")}


def validate_containerfile(body: bytes, inputs: dict[str, str]) -> None:
    """Refuse source/pin drift before invoking the local image builder."""
    text = body.decode("utf-8")
    stages = re.findall(r"^FROM (\S+)(?: AS \w+)?$", text, re.MULTILINE)
    donors = re.findall(r"^COPY --from=(\S+) ", text, re.MULTILINE)
    if stages != [inputs["build"], inputs["caddy"]] or donors != [
        inputs["caddy_binary_image"],
        inputs["ca_bundle_image"],
        "prepare",
    ]:
        refuse("Caddy Containerfile differs from its pinned UBI inputs")
    if any(inputs[key] not in text for key in ("caddy_binary_sha256", "ca_bundle_sha256")):
        refuse("Caddy Containerfile omits a byte donor hash")


def probe_image(image: str, inputs: dict[str, str], context: Path) -> dict[str, object]:
    """Run fixed finite hash/capability/version checks, never Caddy's server."""
    name = "hfcache-caddy-proof-" + secrets.token_hex(8)
    marker = "caddy-build-" + secrets.token_hex(16)
    cidfile = context / "probe-container.id"
    result = subprocess.run(  # noqa: S603 - fixed command and locally built immutable image
        [
            executable("podman"),
            "--remote=false",
            "run",
            "--name",
            name,
            "--label=io.hfcache.proof=" + marker,
            "--cidfile",
            str(cidfile),
            "--pull=never",
            "--http-proxy=false",
            "--network=none",
            "--read-only",
            "--read-only-tmpfs=false",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges",
            "--userns=keep-id:uid=981,gid=981",
            "--user=981:981",
            "--pids-limit=64",
            "--entrypoint=/usr/bin/bash",
            image,
            "-ec",
            _PROBE,
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    container_id = cidfile.read_text().strip()
    if not _HEX.fullmatch(container_id):
        refuse("Caddy probe did not retain an exact container identity")
    inspection = subprocess.run(  # noqa: S603 - exact retained probe ID, no mutation
        [executable("podman"), "--remote=false", "container", "inspect", container_id],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    records = json.loads(inspection.stdout)
    if not isinstance(records, list) or len(records) != 1 or not isinstance(records[0], dict):
        refuse("Caddy probe container identity is unavailable; preserve evidence")
    record = records[0]
    config, state = record.get("Config"), record.get("State")
    labels = config.get("Labels") if isinstance(config, dict) else None
    actual_image = record.get("Image")
    if isinstance(actual_image, str) and _HEX.fullmatch(actual_image):
        actual_image = "sha256:" + actual_image
    if (
        record.get("Id") != container_id
        or actual_image != image
        or not isinstance(labels, dict)
        or labels.get("io.hfcache.proof") != marker
        or not isinstance(state, dict)
        or state.get("Running") is not False
        or type(state.get("Pid")) is not int
        or state["Pid"] != 0
        or type(state.get("ExitCode")) is not int
        or state["ExitCode"] != 0
    ):
        refuse("Caddy probe container state is unknown; preserve evidence")
    lines = result.stdout.splitlines()
    if (
        len(result.stdout) > _MAX_PROOF_BYTES
        or len(lines) != _PROOF_LINES
        or lines[0] != f"{inputs['caddy_binary_sha256']}  /usr/bin/caddy"
        or lines[1] != f"{inputs['ca_bundle_sha256']}  /etc/ssl/cert.pem"
        or not (lines[2] == _VERSION or lines[2].startswith(_VERSION + " "))
    ):
        refuse("built Caddy binary, CA or version proof does not match")
    return {
        "caddy_version": lines[2],
        "file_capabilities": "",
        "probe_container_id": container_id,
        "probe_container_name": name,
        "probe_exit_code": 0,
    }


def build(context: Path, image: str) -> dict[str, object]:
    if os.geteuid() == 0:
        refuse("build as the rootless login/service account, never root")
    if not _IMAGE.fullmatch(image):
        refuse("image tag must be local localhost/hfcache:<tag>")
    context = local_path(context)
    inputs = foundation(REPOSITORY / "packaging/containers/images.json")
    containerfile = local_path(REPOSITORY / "packaging/containers/Containerfile.caddy")
    body = containerfile.read_bytes()
    validate_containerfile(body, inputs)
    # A new private context preserves every earlier or unexplained artifact.
    context.mkdir(mode=0o700)
    shutil.copyfile(containerfile, context / "Containerfile")
    commit = subprocess.run(  # noqa: S603 - fixed local source identity command
        [executable("git"), "rev-parse", "HEAD"],
        cwd=REPOSITORY,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        refuse("source commit identity is invalid")
    dirty = bool(
        subprocess.run(  # noqa: S603 - fixed local source status command
            [executable("git"), "status", "--porcelain"],
            cwd=REPOSITORY,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    )
    evidence: dict[str, object] = {
        "schema_version": 1,
        "source_commit": commit,
        "source_dirty": dirty,
        "platform": "linux/amd64",
        "caddy_base": inputs["caddy"],
        "build_base": inputs["build"],
        "ca_bundle_image": inputs["ca_bundle_image"],
        "caddy_binary_image": inputs["caddy_binary_image"],
        "caddy_binary_sha256": inputs["caddy_binary_sha256"],
        "ca_bundle_sha256": inputs["ca_bundle_sha256"],
        "containerfile_sha256": digest(body),
        "image_tag": image,
    }
    (context / "inputs.json").write_text(json.dumps(evidence, sort_keys=True, indent=2) + "\n")
    subprocess.run(  # noqa: S603 - exact local image builder, no network or publication
        [
            executable("podman"),
            "--remote=false",
            "build",
            "--pull=never",
            "--http-proxy=false",
            "--network=none",
            "--platform=linux/amd64",
            "--tag",
            image,
            "--iidfile",
            str(context / "image.id"),
            str(context),
        ],
        check=True,
    )
    identity = (context / "image.id").read_text().strip()
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", identity):
        refuse("builder did not return an exact image identity")
    evidence["image_id"] = identity
    evidence.update(probe_image(identity, inputs, context))
    (context / "build.json").write_text(json.dumps(evidence, sort_keys=True, indent=2) + "\n")
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--context", type=Path, required=True, help="new local directory; retained")
    parser.add_argument("--tag", required=True, help="localhost/hfcache:<tag>")
    options = parser.parse_args()
    try:
        evidence = build(options.context, options.tag)
    except OSError, ValueError, subprocess.SubprocessError:
        print(
            "Caddy container build refused or failed; retained context contains available evidence"
        )
        return 1
    print(json.dumps(evidence, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
