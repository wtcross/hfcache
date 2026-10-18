#!/usr/bin/python3
"""Decision 127: fixed rootless container roles and non-killing executor drain.

This host orchestrator imports no application code. Secret values never enter
argv, environment or the protected profile; Podman supplies explicit file mounts.
"""

import json
import os
import re
import stat
import subprocess
import sys
import time
from pathlib import Path

RELEASE_ROOT = Path(__file__).resolve().parents[1]
PROFILE_DIRECTORY = RELEASE_ROOT / "rendered"
PROFILE = PROFILE_DIRECTORY / "runtime.json"
PODMAN = "/usr/bin/podman"
ENGINE = [PODMAN, "--remote=false"]
CONTAINER_UID = 981
NAMES = {"api": "hfcache-api", "worker": "hfcache-verification", "caddy": "hfcache-caddy"}
IMAGE_ID = re.compile(r"sha256:[0-9a-f]{64}")
MAX_PROFILE_BYTES = 16384
MIN_MOUNT_FIELDS = 6


def profile_pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            msg = "duplicate container profile field"
            raise ValueError(msg)
        result[key] = value
    return result


def load_profile(path=PROFILE):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        info = os.fstat(descriptor)
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_uid != 0
            or info.st_mode & 0o022
            or info.st_nlink != 1
            or not 0 < info.st_size <= MAX_PROFILE_BYTES
        ):
            msg = "unsafe container profile"
            raise ValueError(msg)
        raw = os.read(descriptor, MAX_PROFILE_BYTES + 1)
        after = os.fstat(descriptor)
        if any(
            getattr(after, key) != getattr(info, key)
            for key in (
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
        ):
            msg = "container profile changed"
            raise ValueError(msg)
    finally:
        os.close(descriptor)
    profile = json.loads(raw, object_pairs_hook=profile_pairs)
    if (
        set(profile) != {"schema_version", "service_uid", "service_gid", "app_image", "caddy_image"}
        or type(profile["schema_version"]) is not int
        or profile["schema_version"] != 1
        or any(
            type(profile[key]) is not int or profile[key] < 1
            for key in ("service_uid", "service_gid")
        )
        or any(
            not isinstance(profile[key], str) or not IMAGE_ID.fullmatch(profile[key])
            for key in ("app_image", "caddy_image")
        )
        or (os.geteuid(), os.getegid()) != (profile["service_uid"], profile["service_gid"])
        or os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{profile['service_uid']}")
        != f"/run/user/{profile['service_uid']}"
    ):
        msg = "container profile or service identity mismatch"
        raise ValueError(msg)
    os.environ["XDG_RUNTIME_DIR"] = f"/run/user/{profile['service_uid']}"
    return profile


def secret(name):
    return ["--secret", f"{name},type=mount,target={name},uid=981,gid=981,mode=0400"]


def volume(source, target=None, *, writable=False, shared=False):
    options = "rw" if writable else "ro"
    if shared:
        options += ",z"  # Only reviewed LOCAL paths; never call this for NAS.
    return ["--volume", f"{source}:{target or source}:{options}"]


def command(profile, role, arguments=()):  # noqa: PLR0912, PLR0915 - one closed role/mount allowlist
    if role not in {*NAMES, "client"} or (role != "client" and arguments):
        msg = "unknown fixed container role"
        raise ValueError(msg)
    argv = [
        *ENGINE,
        "run",
        "--pull=never",
        "--http-proxy=false",
        "--sig-proxy=false",
        "--userns=keep-id:uid=981,gid=981",
        "--user=981:981",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges",
        "--read-only",
        "--read-only-tmpfs=false",
        "--tmpfs=/tmp:rw,nosuid,nodev,noexec,mode=1777",
        "--pids-limit=512",
        "--label=io.hfcache.stack=rootless",
        f"--label=io.hfcache.role={role}",
    ]
    if role == "client":
        # An observer exiting never stops the API or cancels an admitted job.
        argv += ["--rm", "--network=none"]
    else:
        argv += ["--name", NAMES[role]]
        argv += ["--network=none" if role == "worker" else "--network=pasta"]
    argv += ["--cgroup-conf=memory.high=" + ("536870912" if role == "caddy" else "4294967296")]
    invocation = os.environ.get("INVOCATION_ID", "")
    if role in {"api", "worker"} and re.fullmatch(r"[0-9a-f]{32}", invocation):
        # Nonsecret actual-unit evidence, never a submitted caller/timer claim.
        argv += ["--env=INVOCATION_ID=" + invocation]
    if role in {"api", "worker", "client"}:
        # Directory bind intentionally observes atomic config replacement.
        argv += volume("/etc/hfcache")
        # Pin release-owned profiles to the same physical tree as this helper.
        # The host targets are regular placeholders, never external symlinks.
        argv += volume(PROFILE_DIRECTORY, "/etc/hfcache/containers")
        if role == "client":
            argv += volume(PROFILE_DIRECTORY / "client.toml", "/etc/hfcache/client.toml")
    if role in {"worker", "client"}:
        for hidden in (
            "/run/credentials",
            "/etc/credstore",
            "/etc/credstore.encrypted",
            "/etc/hfcache/credentials",
        ):
            argv += [f"--tmpfs={hidden}:ro,nosuid,nodev,noexec,mode=000"]
    if role in {"api", "worker"}:
        argv += volume("/srv/hfcache")  # No relabel/chown/copyup option, ever.
        argv += volume("/run/hfcache/hfcache.lock", writable=True, shared=True)
    if role in {"api", "client", "caddy"}:
        argv += volume("/run/hfcache/api", writable=role == "api", shared=True)
    if role in {"api", "worker"}:
        argv += volume("/run/hfcache/verification", shared=True)
    if role == "api":
        argv += volume("/run/hfcache/api.lock", writable=True, shared=True)
        argv += volume("/var/lib/hfcache/api", writable=True, shared=True)
        argv += volume("/var/lib/hfcache/hf-home", writable=True, shared=True)
        argv += volume("/var/cache/hfcache", writable=True, shared=True)
        argv += [
            "--env=HF_HOME=/var/lib/hfcache/hf-home",
            "--env=HF_XET_CACHE=/var/cache/hfcache/xet",
        ]
        for name in ("hfcache.api", "hfcache.api-reader", "hfcache.mcp-reader", "hf-token"):
            argv += secret(name)
        argv += [
            profile["app_image"],
            "/opt/hfcache/.venv/bin/hfcache",
            "serve",
            "--server-config",
            "/etc/hfcache/containers/server.toml",
            "--hub-token-file",
            "/run/secrets/hf-token",
        ]
    elif role == "worker":
        argv += [f"--security-opt=seccomp={PROFILE_DIRECTORY}/worker-seccomp.json"]
        argv += volume("/var/lib/hfcache/verification", writable=True, shared=True)
        argv += volume("/var/lib/hfcache/verification.instance.lock", writable=True, shared=True)
        argv += [
            "--env=HF_HUB_OFFLINE=1",
            "--env=HF_DATASETS_OFFLINE=1",
            "--env=HF_HUB_DISABLE_TELEMETRY=1",
            "--env=HF_HOME=/tmp/hf-home",
            "--env=HF_XET_CACHE=/tmp/xet",
        ]
        argv += [
            profile["app_image"],
            "/opt/hfcache/.venv/bin/python",
            "-m",
            "hfcache.verification_worker",
            "--config",
            "/etc/hfcache/config.toml",
            "--state-directory",
            "/var/lib/hfcache/verification",
            "--socket",
            "/run/hfcache/verification/verification.sock",
            "--api-uid",
            "981",
        ]
    elif role == "caddy":
        argv += ["--publish=0.0.0.0:8443:8443"]
        argv += volume(PROFILE_DIRECTORY / "Caddyfile", "/etc/caddy/Caddyfile")
        argv += volume("/var/lib/hfcache/caddy-data", "/data", writable=True, shared=True)
        argv += volume("/var/lib/hfcache/caddy-config", "/config", writable=True, shared=True)
        argv += secret("hfcache.tls-cert") + secret("hfcache.tls-key")
        argv += [
            "--entrypoint=/usr/bin/caddy",
            profile["caddy_image"],
            "run",
            "--config",
            "/etc/caddy/Caddyfile",
            "--adapter",
            "caddyfile",
        ]
    else:
        argv += secret("hfcache.api")
        argv += [profile["app_image"], "/opt/hfcache/.venv/bin/hfcache", *arguments]
    return argv


def inspect_container(name):
    result = subprocess.run(  # noqa: S603 - fixed local engine and fixed role name
        [*ENGINE, "container", "inspect", name], capture_output=True, check=False, text=True
    )
    if result.returncode:
        # Only Podman's explicit absence code is safe; engine errors are unknown.
        exists = subprocess.run([*ENGINE, "container", "exists", name], check=False)  # noqa: S603
        if exists.returncode == 1:
            return None
        msg = "container state unavailable"
        raise TypeError(msg)
    values = json.loads(result.stdout)
    if not isinstance(values, list) or len(values) != 1 or not isinstance(values[0], dict):
        msg = "container state malformed"
        raise RuntimeError(msg)
    return values[0]


def owned_container(profile, role):
    info = inspect_container(NAMES[role])
    if info is None:
        return None
    config, state = info.get("Config"), info.get("State")
    if not isinstance(config, dict) or not isinstance(state, dict):
        msg = "unknown container metadata preserved"
        raise TypeError(msg)
    labels = config.get("Labels")
    if (
        not isinstance(labels, dict)
        or not isinstance(info.get("Id"), str)
        or not re.fullmatch(r"[0-9a-f]{64}", info["Id"])
    ):
        msg = "unknown container identity preserved"
        raise RuntimeError(msg)
    expected = profile["caddy_image" if role == "caddy" else "app_image"]
    observed_image = info.get("Image")
    if isinstance(observed_image, str) and re.fullmatch(r"[0-9a-f]{64}", observed_image):
        observed_image = "sha256:" + observed_image
    if (
        observed_image != expected
        or labels.get("io.hfcache.role") != role
        or labels.get("io.hfcache.stack") != "rootless"
    ):
        msg = "unknown existing container preserved"
        raise RuntimeError(msg)
    if (
        type(state.get("Running")) is not bool
        or type(state.get("Pid")) is not int
        or state["Pid"] < 0
        or (state["Running"] and state["Pid"] == 0)
    ):
        msg = "unknown executor state preserved"
        raise RuntimeError(msg)
    return info


def prepare_start(profile, role):
    info = owned_container(profile, role)
    if info is not None:
        if info["State"]["Running"] or info["State"]["Pid"] != 0:
            msg = "existing executor preserved; drain explicitly"
            raise RuntimeError(msg)
        subprocess.run([*ENGINE, "rm", info["Id"]], check=True)  # noqa: S603


def archive_readonly(table=None):
    """Inspect local kernel mount information, never a live archive pathname."""
    body = Path("/proc/self/mountinfo").read_text() if table is None else table
    matches = []
    for line in body.splitlines():
        left, _, right = line.partition(" - ")
        fields = left.split()
        if len(fields) >= MIN_MOUNT_FIELDS and fields[4] == "/srv/hfcache" and right:
            matches.append((fields[5].split(","), right.split()[0]))
    # autofs plus its mounted NFS tree is expected; only NFS counts here.
    nfs = [(options, kind) for options, kind in matches if kind in {"nfs", "nfs4"}]
    if len(nfs) != 1 or "ro" not in nfs[0][0] or "rw" in nfs[0][0]:
        msg = "read-only NAS mount barrier unavailable"
        raise RuntimeError(msg)


def drain(profile, role):
    info = owned_container(profile, role)
    if info is None:
        return
    if info["State"]["Running"]:
        subprocess.run([*ENGINE, "stop", "--time", "-1", info["Id"]], check=True)  # noqa: S603
    stopped = owned_container(profile, role)
    if stopped is not None:
        if stopped["Id"] != info["Id"]:
            msg = "executor identity changed during drain; replacement preserved"
            raise RuntimeError(msg)
        if stopped["State"]["Running"] or stopped["State"]["Pid"] != 0:
            msg = "executor has not drained"
            raise RuntimeError(msg)
        subprocess.run([*ENGINE, "rm", stopped["Id"]], check=True)  # noqa: S603


def main():
    stopping = len(sys.argv) == 3 and sys.argv[1] == "stop" and sys.argv[2] in NAMES  # noqa: PLR2004 - fixed stop grammar
    try:
        profile = load_profile()
        if stopping:
            drain(profile, sys.argv[2])
            return 0
        role = sys.argv[1] if len(sys.argv) > 1 else ""
        argv = command(profile, role, sys.argv[2:])
        if role in {"api", "worker"}:
            archive_readonly()
        if role != "client":
            prepare_start(profile, role)
        # exec preserves manager-origin FD3 and LISTEN_PID for Podman's handoff.
        os.execv(PODMAN, argv)  # noqa: S606
    except Exception:  # noqa: BLE001 - unknown stop errors must never reach fallback termination
        sys.stderr.write("hfcache container boundary refused; retained state requires inspection\n")
        if stopping:
            # Never return into systemd's fallback termination of an unknown job.
            while True:
                time.sleep(30)
        return 20
    return 20


if __name__ == "__main__":
    raise SystemExit(main())
