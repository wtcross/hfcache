#!/usr/bin/env python3
"""Opt-in, NAS-free proof of one exact local UBI Python image.

The one-shot receives no host binds, secrets, engine socket or network. Retain
its named container and all local evidence. This is foundation acceptance, not
worker/domain/production acceptance and never a substitute for those proofs.
"""

import argparse
import importlib.util
import json
import os
import re
import secrets
import subprocess
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "foundation_build", Path(__file__).with_name("build-container.py")
)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError
_BUILD = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_BUILD)
_ENGINE = ["/usr/bin/podman", "--remote=false"]
_PYTHON = "/opt/hfcache/.venv/bin/python"
_LIMIT = 1024 * 1024
_MASKS = (
    "/run/credentials",
    "/run/secrets",
    "/etc/credstore",
    "/etc/credstore.encrypted",
    "/etc/hfcache/credentials",
)
_FLAGS = (
    "pid1",
    "read_only_root",
    "capabilities_empty",
    "no_new_privileges",
    "seccomp",
    "offline",
    "credential_masks",
    "ambient_sources_absent",
    "package_managers_absent",
    "nss_localhost",
)
_MODULES = (
    "hf_xet",
    "pydantic_core._pydantic_core",
    "cryptography.hazmat.bindings._rust",
    "_cffi_backend",
    "caio",
    "caio.linux_aio",
    "caio.thread_aio",
    "fastapi",
    "uvicorn",
    "fastmcp",
    "hfcache",
)
_PAYLOAD = r"""
import hashlib,importlib,importlib.util,ipaddress,json,os,platform,pwd,grp
import shutil,signal,socket,ssl,sys
signal.signal(signal.SIGTERM,lambda *_:sys.exit(20))
assert os.getpid()==1 and os.geteuid()==os.getegid()==981
assert pwd.getpwuid(981).pw_name==grp.getgrgid(981).gr_name=='hfcache'
assert platform.python_version()==sys.argv[2] and platform.machine()=='x86_64'
assert all(ipaddress.ip_address(row[4][0]).is_loopback
 for row in socket.getaddrinfo('localhost',0,type=socket.SOCK_STREAM))
release={key:value.strip().strip('"') for line in open('/etc/os-release')
 for key,separator,value in [line.strip().partition('=')] if separator}
assert release['ID']=='rhel' and release['VERSION_ID'].split('.')[0]=='10'
assert os.statvfs('/').f_flag & os.ST_RDONLY
status=dict(line.split(':',1) for line in open('/proc/self/status') if ':' in line)
assert int(status['CapEff'].strip(),16)==0 and status['NoNewPrivs'].strip()=='1'
assert status['Seccomp'].strip()=='2'
assert os.environ['HF_HUB_OFFLINE']=='1'
assert os.environ.get('SSL_CERT_FILE')=='/etc/ssl/cert.pem'
assert os.environ.get('HF_XET_LOG_DEST')=='/dev/null'
assert not any(name in os.environ for name in (
 'HF_TOKEN','HUGGING_FACE_HUB_TOKEN','HUGGINGFACE_HUB_TOKEN','HUGGINGFACEHUB_API_TOKEN',
 'HF_TOKEN_PATH','HFCACHE_API_TOKEN','HFCACHE_MCP_TOKEN','CREDENTIALS_DIRECTORY',
 'HTTP_PROXY','HTTPS_PROXY','ALL_PROXY','http_proxy','https_proxy','all_proxy',
 'SSL_CERT_DIR','CAIO_IMPL'))
for path in ('/run/credentials','/run/secrets','/etc/credstore',
 '/etc/credstore.encrypted','/etc/hfcache/credentials'):
 try: os.listdir(path)
 except PermissionError: pass
 else: raise AssertionError
assert not any(shutil.which(name) for name in ('uv','pip','pip3','dnf','microdnf','yum','rpm'))
assert all(importlib.util.find_spec(name) is None for name in ('pip','ensurepip','uv'))
ca='/etc/ssl/cert.pem'
with open(ca,'rb') as stream: body=stream.read(1024*1024)
assert hashlib.sha256(body).hexdigest()==sys.argv[1]
context=ssl.create_default_context()
assert context.verify_mode==ssl.CERT_REQUIRED and context.check_hostname
assert context.cert_store_stats()['x509_ca']>0
assert ssl.get_default_verify_paths().cafile==ca
modules=('hf_xet','pydantic_core._pydantic_core','cryptography.hazmat.bindings._rust',
 '_cffi_backend','caio','caio.linux_aio','caio.thread_aio',
 'fastapi','uvicorn','fastmcp','hfcache')
for name in modules: importlib.import_module(name)
import caio
assert caio.linux_uring is None
assert caio.linux_aio is not None and caio.thread_aio is not None
assert caio.preferred in (caio.linux_aio,caio.thread_aio)
glibc=os.confstr('CS_GNU_LIBC_VERSION')
assert glibc.startswith('glibc ')
result={'schema_version':1,'python_version':platform.python_version(),
 'os_id':release['ID'],'os_version':release['VERSION_ID'],'architecture':platform.machine(),
 'uid':981,'gid':981,'account':'hfcache','nss_localhost':True,'pid1':True,'read_only_root':True,
 'capabilities_empty':True,'no_new_privileges':True,'seccomp':True,'offline':True,
 'credential_masks':True,'ambient_sources_absent':True,'package_managers_absent':True,
 'ca_sha256':hashlib.sha256(body).hexdigest(),'trusted_ca_count':context.cert_store_stats()['x509_ca'],
 'openssl':ssl.OPENSSL_VERSION,'glibc':glibc,'imported':list(modules),
 'caio':{'linux_aio_available':True,'thread_aio_available':True,
 'linux_uring_available':False,'preferred':caio.preferred.__name__}}
print(json.dumps(result,sort_keys=True))
"""


def engine(*arguments):
    return subprocess.run(  # noqa: S603 - fixed local engine, no shell or remote context
        [*_ENGINE, *arguments], check=True, capture_output=True, text=True, timeout=90
    )


def image_identity(value):
    value = value.removeprefix("sha256:")
    if not re.fullmatch(r"[0-9a-f]{64}", value):
        _BUILD.refuse("invalid exact image identity")
    return "sha256:" + value


def inspect_image(name):
    result = json.loads(engine("image", "inspect", name).stdout)
    if not isinstance(result, list) or len(result) != 1:
        _BUILD.refuse("image inspection is ambiguous")
    return result[0]


def foundation_identity(base, actual):
    """An os-release claim cannot establish ancestry; prove ordered diffIDs."""
    image_identity(base["Id"])
    image_identity(actual["Id"])
    before, after = base["RootFS"]["Layers"], actual["RootFS"]["Layers"]
    if (
        not isinstance(before, list)
        or not before
        or not isinstance(after, list)
        or len(after) < len(before)
        or before != after[: len(before)]
        or any(
            not isinstance(item, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", item)
            for item in [*before, *after]
        )
    ):
        _BUILD.refuse("actual image does not retain selected UBI base diffID prefix")
    return {
        "base_config_id": image_identity(base["Id"]),
        "base_diff_ids": before,
        "image_config_id": image_identity(actual["Id"]),
        "diff_id_prefix_verified": True,
    }


def run_arguments(image, name, marker, pins):
    return [
        *_ENGINE,
        "run",
        "--name",
        name,
        "--pull=never",
        "--http-proxy=false",
        "--userns=keep-id:uid=981,gid=981",
        "--user=981:981",
        "--network=none",
        "--pid=private",
        "--ipc=private",
        "--read-only",
        "--read-only-tmpfs=false",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges",
        "--no-healthcheck",
        "--memory=512m",
        "--pids-limit=128",
        "--cpus=1",
        "--tmpfs=/tmp:rw,size=16m,mode=1777,nodev,nosuid,noexec",
        *[f"--tmpfs={path}:ro,size=4096,mode=000,nodev,nosuid,noexec" for path in _MASKS],
        "--env=HF_HUB_OFFLINE=1",
        "--env=HF_DATASETS_OFFLINE=1",
        "--env=HF_XET_LOG_DEST=/dev/null",
        "--label=io.hfcache.foundation=" + marker,
        "--entrypoint=" + _PYTHON,
        image,
        "-I",
        "-B",
        "-c",
        _PAYLOAD,
        pins["ca_bundle_sha256"],
        pins["python_distribution"]["version"],
    ]


def validate_result(result, pins):
    backend = result.get("caio", {})
    if (
        backend.get("linux_aio_available") is not True
        or backend.get("thread_aio_available") is not True
        or backend.get("linux_uring_available") is not False
        or backend.get("preferred") not in ("caio.linux_aio", "caio.thread_aio")
    ):
        _BUILD.refuse("actual caio native fallback proof is incomplete")
    if (
        type(result.get("schema_version")) is not int
        or result["schema_version"] != 1
        or result.get("python_version") != pins["python_distribution"]["version"]
        or result.get("ca_sha256") != pins["ca_bundle_sha256"]
        or any(result.get(name) is not True for name in _FLAGS)
        or result.get("os_id") != "rhel"
        or result.get("architecture") != "x86_64"
        or not re.fullmatch(r"10(?:\.[0-9]+)?", result.get("os_version", ""))
        or type(result.get("uid")) is not int
        or result["uid"] != 981  # noqa: PLR2004
        or type(result.get("gid")) is not int
        or result["gid"] != 981  # noqa: PLR2004
        or result.get("account") != "hfcache"
        or result.get("imported") != list(_MODULES)
        or type(result.get("trusted_ca_count")) is not int
        or result["trusted_ca_count"] <= 0
        or not re.fullmatch(r"glibc [0-9]+\.[0-9]+", result.get("glibc", ""))
        or not re.fullmatch(
            r"OpenSSL [0-9]+\.[0-9]+\.[0-9]+ [A-Za-z0-9 ]{1,40}", result.get("openssl", "")
        )
    ):
        _BUILD.refuse("actual foundation output does not establish pinned runtime proof")


def prove(image, workspace, images, *, build_record=None):
    if os.geteuid() == 0:
        _BUILD.refuse("run foundation proof as a rootless login/service account")
    image = image_identity(image)
    workspace, images = _BUILD.local_path(workspace), _BUILD.local_path(images)
    if images.stat().st_size > _LIMIT:
        _BUILD.refuse("foundation manifest is oversized")
    pins = json.loads(images.read_text())
    if (
        pins["platform"] != "linux/amd64"
        or not re.fullmatch(
            r"registry\.access\.redhat\.com/ubi10/ubi-micro@sha256:[0-9a-f]{64}", pins["python"]
        )
        or not re.fullmatch(r"[0-9a-f]{64}", pins["ca_bundle_sha256"])
    ):
        _BUILD.refuse("foundation pins are invalid")
    info = json.loads(engine("info", "--format=json").stdout)
    if info["host"]["security"]["rootless"] is not True:
        _BUILD.refuse("actual rootless local engine required")
    graph = _BUILD.local_path(Path(info["store"]["graphRoot"]))
    identity = foundation_identity(inspect_image(pins["python"]), inspect_image(image))
    if identity["image_config_id"] != image:
        _BUILD.refuse("requested exact image changed")
    source = None
    if build_record is not None:
        record = _BUILD.local_path(build_record)
        if record.stat().st_size > _LIMIT:
            _BUILD.refuse("build record is oversized")
        body = record.read_bytes()
        value = json.loads(body)
        if (
            value["image_id"] != image
            or type(value["source_dirty"]) is not bool
            or not re.fullmatch(r"[0-9a-f]{40}", value["source_commit"])
        ):
            _BUILD.refuse("build source is for a different image")
        source = {
            "source_commit": value["source_commit"],
            "source_dirty": value["source_dirty"],
            "build_record_sha256": _BUILD.digest(body),
        }
    workspace.mkdir(mode=0o700)
    marker = secrets.token_hex(8)
    name = "hfcache-foundation-" + marker
    arguments = run_arguments(image, name, marker, pins)
    (workspace / "command.json").write_text(json.dumps(arguments, indent=2) + "\n")
    # A timeout refuses acceptance and retains the named container for review;
    # it never deletes/replaces or force-stops an uncertain surviving process.
    with (
        (workspace / "stdout.log").open("xb") as stdout,
        (workspace / "stderr.log").open("xb") as stderr,
    ):
        subprocess.run(arguments, check=True, stdout=stdout, stderr=stderr, timeout=90)  # noqa: S603
    with (workspace / "stdout.log").open("rb") as stream:
        body = stream.read(_LIMIT + 1)
    if len(body) > _LIMIT:
        _BUILD.refuse("foundation output is oversized")
    result = json.loads(body)
    validate_result(result, pins)
    container = json.loads(engine("inspect", "--type=container", name).stdout)[0]
    if (
        container["Config"]["Labels"].get("io.hfcache.foundation") != marker
        or image_identity(container["Image"]) != image
        or container["State"]["Running"]
        or container["State"]["ExitCode"] != 0
        or container["HostConfig"]["NetworkMode"] != "none"
        or any(item.get("Type") == "bind" for item in container["Mounts"])
    ):
        _BUILD.refuse("actual one-shot identity, lifecycle or mount boundary changed")
    evidence = {
        "schema_version": 1,
        "image_id": image,
        "base_manifest": pins["python"],
        **identity,
        "graph_root": str(graph),
        "container_name": name,
        "container_id": container["Id"],
        "container_retained_stopped": True,
        "host_binds": False,
        "nas_access": False,
        "network": "none",
        "foundation_pins": {
            key: pins[key]
            for key in (
                "platform",
                "python",
                "build",
                "ca_bundle_image",
                "ca_bundle_sha256",
                "uv_binary_image",
                "python_distribution",
            )
        },
        "build_provenance": source,
        "result": result,
    }
    (workspace / "proof.json").write_text(json.dumps(evidence, sort_keys=True, indent=2) + "\n")
    return evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--images-json", type=Path, required=True)
    parser.add_argument("--build-record", type=Path)
    options = parser.parse_args()
    try:
        result = prove(
            options.image, options.workspace, options.images_json, build_record=options.build_record
        )
    except OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError:
        print("container foundation proof refused; retain fixture/container evidence")
        return 1
    print(
        json.dumps({"proof": str(options.workspace / "proof.json"), "image_id": result["image_id"]})
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
