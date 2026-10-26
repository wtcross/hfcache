#!/usr/bin/python3 -I
"""Propose a fixed host-helper deployment index from actual protected files.

Read-only administrator preparation, not activation or conformance. Install the
reviewed protected entry and all four standard-library module copies first.
Explicit source provenance must come from the genuine build receipt; this tool
never invents a clean source commit.
No policy, key, configuration, archive or service is read or changed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pwd
import re
import stat
import sys
import types
from pathlib import Path

LIBRARY = Path("/usr/local/lib/hfcache-host-helper/host_policy.py")
OWNER = 0
MAX_BOOTSTRAP = 2 * 1024 * 1024
METADATA = (
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


def require(value):
    if not value:
        message = "protected host index preparation refused"
        raise ValueError(message)


def load_policy():
    """Capture only the fixed root-protected bootstrap, without package imports."""
    parent = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    descriptor = -1
    try:
        for part in LIBRARY.parent.parts[1:]:
            info = os.fstat(parent)
            require(
                info.st_uid in {0, OWNER}
                and (not info.st_mode & 0o022 or (info.st_uid == 0 and info.st_mode & stat.S_ISVTX))
            )
            child = os.open(
                part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=parent
            )
            os.close(parent)
            parent = child
        info = os.fstat(parent)
        require(info.st_uid == OWNER and not info.st_mode & 0o022)
        descriptor = os.open(
            LIBRARY.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=parent
        )
        before = os.fstat(descriptor)
        require(
            stat.S_ISREG(before.st_mode)
            and before.st_uid == OWNER
            and before.st_nlink == 1
            and not before.st_mode & 0o022
            and 0 < before.st_size <= MAX_BOOTSTRAP
        )
        body = bytearray()
        while len(body) <= MAX_BOOTSTRAP:
            part = os.read(descriptor, min(65536, MAX_BOOTSTRAP + 1 - len(body)))
            if not part:
                break
            body.extend(part)
        expected = tuple(getattr(before, name) for name in METADATA)
        require(
            len(body) == before.st_size
            and expected
            == tuple(getattr(os.fstat(descriptor), name) for name in METADATA)
            == tuple(
                getattr(os.stat(LIBRARY.name, dir_fd=parent, follow_symlinks=False), name)
                for name in METADATA
            )
        )
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        os.close(parent)
    module = types.ModuleType("_hfcache_protected_index_policy")
    module.__file__ = str(LIBRARY)
    sys.modules[module.__name__] = module
    exec(compile(body, str(LIBRARY), "exec"), module.__dict__)  # noqa: S102 - captured fixed administrator bootstrap
    module.__dict__["_bootstrap_sha256"] = hashlib.sha256(body).hexdigest()
    return module


def prepare(policy, profile, commit, snapshot, dirty):  # noqa: PLR0915 - two closed actual deployment branches
    """Emit a proposal only; all fixed bindings and original profile checks apply."""
    require(os.geteuid() == OWNER and profile in {"native", "rootless"})
    require(type(commit) is str and re.fullmatch(r"[0-9a-f]{40}", commit))
    require(type(snapshot) is str and re.fullmatch(r"[0-9a-f]{64}", snapshot))
    require(type(dirty) is bool)
    account = pwd.getpwnam("hfcache")
    require(account.pw_dir == "/var/lib/hfcache" and account.pw_uid > 0 and account.pw_gid > 0)
    inspection = policy._Inspection(policy.InspectionBudget())  # noqa: SLF001 - shared protected implementation
    capture = inspection.capture
    selector = policy.PREFIX / "current"
    parent = capture.parent(selector)
    try:
        selected = os.readlink(selector.name, dir_fd=parent)
    finally:
        os.close(parent)
    grammar = policy.NATIVE_VERSION if profile == "native" else policy.ROOTLESS_VERSION
    require(
        selected.startswith("releases/") and grammar.fullmatch(selected.removeprefix("releases/"))
    )
    capture.link(selector, selected)
    root = policy.PREFIX / selected
    inspection.selected = root

    # One local captured-byte cache prevents rehashing a32MiB interpreter from
    # consuming the64MiB budget twice. Every cached use and final output rechecks
    # the original full file metadata; no shared module or global is patched.
    original_read = capture.read
    bodies = {}

    def read(path, *, maximum=policy.MAX_AUTHORITY_BYTES, mode=None, gid=None):
        if path not in bodies:
            bodies[path] = original_read(path, maximum=maximum, mode=mode, gid=gid)
        info = path.lstat()
        require(tuple(getattr(info, name) for name in policy.METADATA) == capture.files[path])
        require(len(bodies[path]) <= maximum)
        require(mode is None or stat.S_IMODE(info.st_mode) == mode)
        require(gid is None or info.st_gid == gid)
        capture.budget.remaining()
        return bodies[path]

    capture.read = read
    paths = policy.binding_paths(profile)
    if profile == "native":
        pin = read(root / ".python-version", maximum=4096).decode("ascii").strip()
        require(re.fullmatch(r"3\.[0-9]+(?:\.[0-9]+)?", pin))
        package = ".venv/lib/python" + ".".join(pin.split(".")[:2]) + "/site-packages/hfcache"
        names = {
            "pyproject.toml",
            "uv.lock",
            ".python-version",
            ".venv/pyvenv.cfg",
            ".venv/bin/hfcache",
            "scripts/container-service.py",
            "scripts/release-profile.py",
            "src/hfcache/__init__.py",
            "src/hfcache/cli.py",
            *(relative for _host, relative in paths.values()),
            *(package + "/" + name for name in capture.tree(root / package)),
        }
        target, _names = policy.fixed_interpreter(capture, root, pin)
        relative = target.relative_to(policy.PREFIX / "python").as_posix()
        policy._relative(relative)  # noqa: SLF001 - shared closed authority schema
        evidence = {
            "package_root_relative": package,
            "python_link_relative": ".venv/bin/python",
            "python_target_relative": relative,
            "python_target_sha256": hashlib.sha256(
                read(target, maximum=policy.MAX_BYTES)
            ).hexdigest(),
        }
    else:
        names = capture.tree(root)
        release = policy._json(  # noqa: SLF001 - shared duplicate-key rejection
            read(root / "container-release.json", maximum=policy.MAX_METADATA_BYTES)
        )
        require(release["source_commit"] == commit)
        require(
            (release["service_uid"], release["service_gid"]) == (account.pw_uid, account.pw_gid)
        )
        evidence = {
            "artifact_index_sha256": hashlib.sha256(
                read(root / "artifact-index.json", maximum=policy.MAX_METADATA_BYTES)
            ).hexdigest(),
            "runtime_profile_sha256": hashlib.sha256(
                read(root / "rendered/runtime.json", maximum=policy.MAX_METADATA_BYTES)
            ).hexdigest(),
            "app_image_sha256": release["app_image"].removeprefix("sha256:"),
            "caddy_image_sha256": release["caddy_image"].removeprefix("sha256:"),
        }
    files = {}
    for name in sorted(names):
        body = read(root / name)
        files[name] = {
            "sha256": hashlib.sha256(body).hexdigest(),
            "bytes": len(body),
            "mode": stat.S_IMODE((root / name).lstat().st_mode),
        }
    # Independently installed receipt, never generated or activated here. Its
    # kernel digest attests provisioning; no secret/archive contents are read.
    policy._selinux_state(capture.budget, require_domain=False)  # noqa: SLF001 - fixed protected contract
    selinux_body = read(
        policy.SELINUX_INSTALLATION,
        maximum=policy.MAX_SELINUX_INSTALLATION,
        mode=0o644,
        gid=policy.OWNER_GID,
    )
    policy._selinux_installation(  # noqa: SLF001 - shared closed authority schema
        selinux_body, files[paths["helper_selinux_policy"][1]]["sha256"]
    )
    proposed = {
        "schema_version": 1,
        "profile": profile,
        "release": {"version": root.name, "selector_target": selected},
        "source": {"parent_commit": commit, "snapshot_sha256": snapshot, "dirty": dirty},
        "api_principal": {"host_uid": account.pw_uid, "host_gid": account.pw_gid},
        "bindings": {name: files[relative]["sha256"] for name, (_host, relative) in paths.items()},
        "authority_files": files,
        "profile_evidence": evidence,
        "selinux_installation_sha256": hashlib.sha256(selinux_body).hexdigest(),
    }
    encoded = json.dumps(proposed, sort_keys=True).encode()
    require(len(encoded) <= policy.MAX_METADATA_BYTES)
    inspection.deployment = policy._deployment(encoded)  # noqa: SLF001 - shared closed schema
    require(
        getattr(policy, "_bootstrap_sha256", None) == proposed["bindings"]["helper_policy_module"]
    )
    inspection.bindings()
    inspection.legacy = inspection.legacy_namespace()
    if profile == "native":
        inspection.native()
    else:
        inspection.rootless()
    capture.link(selector, selected)
    capture.revalidate()
    return proposed


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True, choices=("native", "rootless"))
    parser.add_argument(
        "--source-commit", required=True, help="genuine measured build parent commit"
    )
    parser.add_argument(
        "--source-snapshot", required=True, help="genuine measured build snapshot SHA256"
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--source-dirty", action="store_true")
    source.add_argument("--source-clean", action="store_true")
    args = parser.parse_args(argv)
    try:
        value = prepare(
            load_policy(), args.profile, args.source_commit, args.source_snapshot, args.source_dirty
        )
        print(json.dumps(value, sort_keys=True, indent=2))
    except Exception:  # noqa: BLE001 - fixed refusal, never raw host/configuration diagnostics
        sys.stderr.write("protected host index preparation refused; no deployment was changed\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
