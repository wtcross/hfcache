#!/usr/bin/env python3
"""Opt-in decisions 127/128 proof using local fixtures and an exact image.

This never binds or opens the NAS, submits verification, removes containers, or
kills a surviving executor. Run as the rootless account. Retain the workspace
and stopped containers for inspection; cleanup is a separate reviewed action.
"""

import argparse
import fcntl
import importlib.util
import json
import os
import re
import secrets
import subprocess
import time
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "hfcache_container_build", Path(__file__).with_name("build-container.py")
)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError
_BUILD = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_BUILD)

_PYTHON = "/opt/hfcache/.venv/bin/python"
_ARCHIVE_ID = "9e478d8e-d508-4f2c-ae79-aaf5bb26b207"
_SOCKET_PATH_LIMIT = 100
_MASKS = (
    "/run/credentials",
    "/etc/credstore",
    "/etc/credstore.encrypted",
    "/etc/hfcache/credentials",
)
_UNIT_FIELDS = (
    "Type",
    "NotifyAccess",
    "ActiveState",
    "SubState",
    "MainPID",
    "ControlGroup",
    "ExecMainStartTimestampMonotonic",
    "ActiveEnterTimestampMonotonic",
)
_PEER_PROBE = """
import json,os,sys
from pathlib import Path
from hfcache.verification_protocol import VerificationClient
assert os.geteuid()==os.getegid()==981
VerificationClient(Path(sys.argv[1]),expected_uid=981,timeout_seconds=5).check_available()
print(json.dumps({'api_container_peer':True,'uid':981,'expected_worker_uid':981}))
"""
_WORKER_METADATA = """
import json,os
command=open('/proc/1/cmdline','rb').read().split(b'\\0')
assert b'hfcache.verification_worker' in command and b'--container-listener' in command
assert os.readlink('/proc/1/fd/3').startswith('socket:[')
status=dict(line.split(':',1) for line in open('/proc/1/status') if ':' in line)
assert int(status['CapEff'].strip(),16)==0 and status['NoNewPrivs'].strip()=='1'
assert status['Seccomp'].strip()=='2' and int(status['Seccomp_filters'].strip())>=1
print(json.dumps({'worker_pid1':True,'internal_fd3':True,'capabilities_empty':True,
 'no_new_privileges':True,'seccomp_filter':True}))
"""
_ISOLATION = """
import errno,fcntl,json,os,socket,sys
check='identity'
socket_errno={}
try:
 assert os.geteuid()==os.getegid()==981
 check='offline_environment'
 assert os.environ['HF_HUB_OFFLINE']=='1'
 check='credential_environment'
 assert all(name not in os.environ for name in (
  'HF_TOKEN','HUGGING_FACE_HUB_TOKEN','HUGGINGFACE_HUB_TOKEN','HUGGINGFACEHUB_API_TOKEN',
  'HF_TOKEN_PATH','HFCACHE_API_TOKEN','HFCACHE_MCP_TOKEN','CREDENTIALS_DIRECTORY',
  'LISTEN_PIDFDID','HTTP_PROXY','HTTPS_PROXY','ALL_PROXY','http_proxy','https_proxy','all_proxy'))
 for family,label in ((socket.AF_INET,'ip4_socket'),(socket.AF_INET6,'ip6_socket')):
  check=label
  try: channel=socket.socket(family,socket.SOCK_STREAM)
  except OSError as error:
   assert error.errno in (errno.EPERM,errno.EACCES,errno.ENOSYS)
   socket_errno[label]=error.errno
  else: channel.close(); raise AssertionError
 for path,label in (('/etc/hfcache/credentials/synthetic','masked_credential'),
                    (sys.argv[1],'unmounted_credential')):
  check=label
  try: descriptor=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
  except (PermissionError,FileNotFoundError): pass
  else: os.close(descriptor); raise AssertionError
 check='private_network'
 assert os.stat('/proc/1/ns/net').st_ino!=int(sys.argv[2])
 check='private_pid'
 assert os.stat('/proc/1/ns/pid').st_ino!=int(sys.argv[3])
 check='read_only_root'
 assert os.statvfs('/').f_flag & os.ST_RDONLY
 check='pid1_entrypoint'
 assert os.getpid()==1
 check='lock_identity'
 assert os.stat('/run/hfcache/hfcache.lock').st_ino==int(sys.argv[4])
 check='lock_contention'
 with open('/run/hfcache/hfcache.lock','r+b') as lock:
  try: fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError: pass
  else: raise AssertionError
except Exception as error:
 allowed={'AssertionError','PermissionError','FileNotFoundError','OSError','KeyError','ValueError'}
 kind=type(error).__name__
 print(json.dumps({'failed_check':check,'error_class':kind if kind in allowed else 'Exception'}))
 sys.exit(1)
print(json.dumps({'uid':981,'gid':981,'ip_sockets_denied':True,'credentials_denied':True,
 'offline':True,'read_only_root':True,'private_pid_network':True,'shared_lock_inode':True,
 'shared_lock_contends':True,'ip_socket_errno':socket_errno}))
"""
_CHECK_NAMES = frozenset(
    {
        "identity",
        "offline_environment",
        "credential_environment",
        "ip4_socket",
        "ip6_socket",
        "masked_credential",
        "unmounted_credential",
        "private_network",
        "private_pid",
        "read_only_root",
        "pid1_entrypoint",
        "lock_identity",
        "lock_contention",
    }
)

_PROTECTED_READER = """
import json,os
from pathlib import Path
from hfcache.api.auth import read_protected_token
assert os.geteuid()==981
value=read_protected_token(Path('/run/secrets/proof-api'))
assert len(value)==48
print(json.dumps({'protected_token_file':True,'uid':981}))
"""


def engine(*arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603 - fixed local Podman, no shell
        ["/usr/bin/podman", "--remote=false", *arguments],
        check=check,
        capture_output=True,
        text=True,
    )


def manager(*arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603 - fixed caller's user manager, never the system manager
        ["/usr/bin/systemctl", "--user", *arguments],
        check=check,
        capture_output=True,
        text=True,
    )


def transient_command(unit: str, worker_name: str, run: list[str]) -> list[str]:
    """Exercise actual readiness attribution; no conmon-only startup shortcut."""
    if (
        not re.fullmatch(r"hfcache-proof-[a-z0-9-]+\.service", unit)
        or not re.fullmatch(r"hfcache-proof-[a-z0-9-]+", worker_name)
        or unit != worker_name + ".service"
    ):
        _BUILD.refuse("invalid disposable user unit")
    properties = (
        "Type=notify",
        "NotifyAccess=all",
        "TimeoutStartSec=45",
        "TimeoutStopSec=infinity",
        "SendSIGKILL=no",
        "Restart=no",
        "UMask=0077",
    )
    return [
        "/usr/bin/systemd-run",
        "--user",
        "--unit=" + unit,
        "--pipe",
        "--wait",
        "--quiet",
        *["--property=" + value for value in properties],
        *run,
    ]


def ready_state(body: str) -> dict[str, str] | None:
    state = dict(line.split("=", 1) for line in body.splitlines() if "=" in line)
    if state.get("ActiveState") != "active":
        return None
    if (
        set(state) != set(_UNIT_FIELDS)
        or state["Type"] != "notify"
        or state["NotifyAccess"] != "all"
        or state["SubState"] != "running"
        or not state["MainPID"].isdigit()
        or int(state["MainPID"]) <= 0
        or not state["ControlGroup"].startswith("/user.slice/")
        or not state["ExecMainStartTimestampMonotonic"].isdigit()
        or not state["ActiveEnterTimestampMonotonic"].isdigit()
        or not 0
        < int(state["ExecMainStartTimestampMonotonic"])
        <= int(state["ActiveEnterTimestampMonotonic"])
    ):
        _BUILD.refuse("user manager did not establish worker readiness")
    return state


def wait_ready(unit: str, process: subprocess.Popen, *, seconds: float = 45) -> dict[str, str]:
    deadline = time.monotonic() + seconds
    while True:
        result = manager("show", unit, "--property=" + ",".join(_UNIT_FIELDS), check=False)
        if result.returncode == 0 and (state := ready_state(result.stdout)) is not None:
            return state
        if process.poll() is not None or time.monotonic() >= deadline:
            _BUILD.refuse("actual user unit did not receive worker readiness")
        time.sleep(0.05)


def rootless_storage() -> str:
    info = json.loads(engine("info", "--format=json").stdout)
    if os.geteuid() == 0 or info["host"]["security"]["rootless"] is not True:
        _BUILD.refuse("proof requires a rootless local engine")
    if (
        info["host"]["security"].get("selinuxEnabled") is not True
        or Path("/sys/fs/selinux/enforce").read_text().strip() != "1"
    ):
        _BUILD.refuse("container peer proof requires SELinux enforcing")
    graph = _BUILD.local_path(Path(info["store"]["graphRoot"]))
    return str(graph)


def base_arguments(image: str, name: str, profile: Path, marker: str) -> list[str]:
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", image):
        _BUILD.refuse("proof requires an exact local image ID")
    if not re.fullmatch(r"hfcache-proof-[a-z0-9-]+", name):
        _BUILD.refuse("invalid disposable container name")
    return [
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
        "--cap-drop=all",
        "--security-opt=no-new-privileges",
        f"--security-opt=seccomp={profile}",
        "--no-healthcheck",
        "--tmpfs=/tmp:rw,size=16m,mode=1777,nodev,nosuid,noexec",
        *[f"--tmpfs={path}:ro,size=4096,mode=000,nodev,nosuid,noexec" for path in _MASKS],
        "--env=HF_HUB_OFFLINE=1",
        "--env=HF_DATASETS_OFFLINE=1",
        f"--label=io.hfcache.proof={marker}",
        "--entrypoint",
        _PYTHON,
    ]


def inspect_owned(name: str, marker: str, image: str) -> dict:
    data = json.loads(engine("inspect", "--type=container", name).stdout)[0]
    actual = data["Image"]
    if isinstance(actual, str) and re.fullmatch(r"[0-9a-f]{64}", actual):
        actual = "sha256:" + actual
    state = data.get("State")
    if (
        data["Config"]["Labels"].get("io.hfcache.proof") != marker
        or actual != image
        or not isinstance(data.get("Id"), str)
        or not re.fullmatch(r"[0-9a-f]{64}", data["Id"])
        or not isinstance(state, dict)
        or type(state.get("Running")) is not bool
        or type(state.get("Pid")) is not int
        or state["Pid"] < 0
        or (state["Running"] and state["Pid"] == 0)
    ):
        _BUILD.refuse("container identity changed; preserve it for investigation")
    return data


def _prove(  # noqa: PLR0912, PLR0915 - one explicit owned lifecycle, never hidden cleanup
    image: str, workspace: Path, profile: Path, trace: dict[str, str]
) -> dict[str, object]:
    """The only host writes are inside the new local workspace/Podman storage."""
    # Validate all inputs before starting or creating any proof state.
    if os.geteuid() == 0:
        _BUILD.refuse("run the proof as the rootless login/service account")
    workspace = _BUILD.local_path(workspace)
    profile = _BUILD.local_path(profile)
    profile_hash = _BUILD.digest(profile.read_bytes())
    marker = secrets.token_hex(8)
    worker_name, client_name, peer_name, isolation_name = (
        f"hfcache-proof-{marker}-{role}" for role in ("worker", "client", "api", "isolation")
    )
    unit = worker_name + ".service"
    common = base_arguments(image, worker_name, profile, marker)
    trace["stage"] = "rootless_engine"
    graph = rootless_storage()
    for name in (worker_name, client_name, peer_name, isolation_name):
        if engine("container", "exists", name, check=False).returncode != 1:
            _BUILD.refuse("disposable name is not proven absent")
    if (
        manager("show", unit, "--property=LoadState", "--value", check=False).stdout.strip()
        != "not-found"
    ):
        _BUILD.refuse("disposable user unit is not proven absent")
    workspace.mkdir(mode=0o700)
    trace.update({"workspace": str(workspace), "stage": "local_fixture"})
    policy, runtime, states = (workspace / item for item in ("policy", "runtime", "states"))
    for directory in (policy, runtime, states, policy / "credentials"):
        directory.mkdir(mode=0o700)
    token = secrets.token_hex(24)
    source = workspace / "synthetic-api-token"
    source.write_text(token)
    source.chmod(0o400)
    masked_source = policy / "credentials/synthetic"
    masked_source.write_text(token)
    masked_source.chmod(0o400)
    archive = workspace / "archive-not-mounted"
    (policy / "config.toml").write_text(
        f'schema_version=1\n[storage]\narchive_root="{archive}"\narchive_id="{_ARCHIVE_ID}"\n'
    )
    lock = workspace / "hfcache.lock"
    lock.touch(mode=0o600)
    address = runtime / "verification.sock"
    if len(os.fsencode(address)) > _SOCKET_PATH_LIMIT:
        _BUILD.refuse("use a shorter local workspace for the Unix socket")
    evidence: dict[str, object] = {
        "schema_version": 1,
        "image_id": image,
        "graph_root": graph,
        "seccomp_sha256": profile_hash,
        "worker_container": worker_name,
        "client_container": client_name,
        "api_peer_container": peer_name,
        "isolation_container": isolation_name,
        "user_unit": unit,
        "host_uid": os.geteuid(),
        "container_uid": 981,
        "nas_mounted": False,
        "verification_submitted": False,
    }
    run = [
        "/usr/bin/podman",
        "--remote=false",
        "run",
        *common,
        "--sdnotify=container",
        "--volume",
        f"{policy}:/etc/hfcache:ro,z",
        "--volume",
        f"{runtime}:{runtime}:rw,z",
        "--volume",
        f"{states}:/var/lib/hfcache:rw,z",
        "--volume",
        f"{lock}:/run/hfcache/hfcache.lock:rw,z",
        image,
        "-m",
        "hfcache.verification_worker",
        "--container-listener",
        "--config",
        "/etc/hfcache/config.toml",
        "--state-directory",
        "/var/lib/hfcache/verification",
        "--socket",
        str(address),
    ]
    with (workspace / "worker.log").open("xb") as log:
        trace["stage"] = "user_notify"
        process = subprocess.Popen(  # noqa: S603 - fixed disposable user unit and exact local image
            transient_command(unit, worker_name, run),
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=log,
        )
        try:
            state = wait_ready(unit, process)
            evidence["notify"] = state
            trace["stage"] = "worker_identity"
            owned = inspect_owned(worker_name, marker, image)
            if (
                owned["HostConfig"]["NetworkMode"] != "none"
                or ":container_t:" not in owned.get("ProcessLabel", "")
                or type(owned["State"].get("ConmonPid")) is not int
                or owned["State"]["ConmonPid"] != int(state["MainPID"])
            ):
                _BUILD.refuse("actual notify worker identity changed")
            inode = address.lstat().st_ino
            evidence["worker_metadata"] = json.loads(
                engine("exec", worker_name, _PYTHON, "-c", _WORKER_METADATA).stdout
            )
            trace["stage"] = "api_container_peer"
            result = engine(
                "run",
                *base_arguments(image, peer_name, profile, marker),
                "--label=io.hfcache.role=api",
                "--volume",
                f"{runtime}:{runtime}:ro,z",
                image,
                "-c",
                _PEER_PROBE,
                str(address),
            )
            peer = inspect_owned(peer_name, marker, image)
            if ":container_t:" not in peer.get("ProcessLabel", ""):
                _BUILD.refuse("API peer is not under ordinary container confinement")
            evidence["private_probe"] = json.loads(result.stdout)
            evidence["selinux_enforcing_container_peer"] = True
            trace["stage"] = "pid1_isolation_companion"
            with lock.open("r+b") as held:
                fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
                proof = engine(
                    "run",
                    *base_arguments(image, isolation_name, profile, marker),
                    "--volume",
                    f"{policy}:/etc/hfcache:ro,z",
                    "--volume",
                    f"{lock}:/run/hfcache/hfcache.lock:rw,z",
                    image,
                    "-c",
                    _ISOLATION,
                    str(source),
                    str(Path("/proc/self/ns/net").stat().st_ino),
                    str(Path("/proc/self/ns/pid").stat().st_ino),
                    str(lock.stat().st_ino),
                    check=False,
                )
            inspect_owned(isolation_name, marker, image)
            if proof.returncode:
                detail = json.loads(proof.stdout)
                check = detail.get("failed_check")
                trace["failed_check"] = check if check in _CHECK_NAMES else "unknown"
                _BUILD.refuse("PID1 companion isolation proof failed")
            evidence["pid1_isolation_companion"] = json.loads(proof.stdout)
            trace["stage"] = "protected_reader"
            result = engine(
                "run",
                *base_arguments(image, client_name, profile, marker),
                "--volume",
                f"{source}:/run/secrets/proof-api:ro,z",
                image,
                "-c",
                _PROTECTED_READER,
            )
            evidence["protected_reader"] = json.loads(result.stdout)
            inspect_owned(client_name, marker, image)
            trace["stage"] = "drain"
        finally:
            exists = engine("container", "exists", worker_name, check=False)
            if exists.returncode == 0:
                owned = inspect_owned(worker_name, marker, image)
                # Validate exact ownership, stop the ID, then let the user unit
                # finish naturally. Never stop an unknown replacement by name.
                engine("stop", "--time", "-1", owned["Id"])
                process.wait()  # no timeout/kill of an unexplained surviving executor
            elif process.poll() is None:
                _BUILD.refuse("worker state is uncertain; preserve user unit and fixture")
    trace["stage"] = "retained_state"
    stopped = inspect_owned(worker_name, marker, image)
    if stopped["State"]["Running"] or stopped["State"]["ExitCode"] != 0 or process.returncode != 0:
        _BUILD.refuse("actual worker did not drain cleanly")
    try:
        address.lstat()
    except FileNotFoundError:
        pass
    else:
        _BUILD.refuse("owned listener was not removed after joined drain")
    if sorted(path.name for path in (states / "verification").iterdir()) != [".lock"]:
        _BUILD.refuse("probe unexpectedly created operation history")
    if archive.exists() or token.encode() in (workspace / "worker.log").read_bytes():
        _BUILD.refuse(
            "proof unexpectedly touched archive state or disclosed its synthetic credential"
        )
    evidence.update(
        {"clean_stop": True, "removed_owned_socket_inode": inode, "empty_operations": True}
    )
    (workspace / "proof.json").write_text(json.dumps(evidence, sort_keys=True, indent=2) + "\n")
    return evidence


def prove(image: str, workspace: Path, profile: Path) -> dict[str, object]:
    trace = {"stage": "input_validation"}
    try:
        return _prove(image, workspace, profile, trace)
    except BaseException as error:
        # Only a successfully created, owned local workspace is eligible. No
        # raw exception/message/argv, credential or SDK response enters evidence.
        if (owned := trace.get("workspace")) is not None:
            evidence = {
                "schema_version": 1,
                "stage": trace["stage"],
                "error_class": type(error).__name__,
                "status": "failed",
            }
            if "failed_check" in trace:
                evidence["failed_check"] = trace["failed_check"]
            try:
                with (Path(owned) / "failure.json").open("x") as target:
                    target.write(json.dumps(evidence, sort_keys=True) + "\n")
            except OSError:
                pass  # Preserve prior evidence; failure reporting cannot justify replacing it.
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True, help="exact locally built sha256 image ID")
    parser.add_argument(
        "--workspace", type=Path, required=True, help="new short local fixture path"
    )
    parser.add_argument("--seccomp-profile", type=Path, required=True)
    options = parser.parse_args()
    try:
        evidence = prove(options.image, options.workspace, options.seccomp_profile)
    except Exception:  # noqa: BLE001 - no raw engine/SDK data is suitable for proof diagnostics
        print("container worker proof failed; preserve the local fixture and container evidence")
        return 1
    print(json.dumps(evidence, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
