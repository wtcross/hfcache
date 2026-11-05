"""Internal offline first activation for the protected release installer (INV-023).

Run only in the selected immutable application runtime, after the installer's
independent actual-executor drain and retained original archive-lock handoff.
The fixed activation role has no IP network or archive exposure. Rootless mounts
exclude credentials; native validates all configured sources against its reviewed
mask policy and hides original runtime objects through a private bind. This
module validates/backs up both bounded local stores and provisions local state;
it never initializes an archive or repairs partial/previous activation.
"""

import argparse
import hashlib
import json
import os
import pwd
import runpy
import subprocess
import sys
import tomllib
from pathlib import Path

from hfcache.api.intents import INTENT_NAME, MAX_INTENT_BYTES, IntentState, unavailable
from hfcache.api.lifecycle import open_directory
from hfcache.api.operations import OperationStore
from hfcache.config import load_config
from hfcache.models import dump, serialize
from hfcache.server_config import ServerConfig, validate_server_config_mapping

PUBLIC_STORE = Path("/var/lib/hfcache/api")
PRIVATE_STORE = Path("/var/lib/hfcache/verification")
COMPANION = Path("/run/hfcache/hfcache.lock.intent")
NATIVE_SERVER = Path("/etc/hfcache/server.toml")
NATIVE_ARCHIVE_CONFIG = Path("/etc/hfcache/config.toml")


def _backup(store: OperationStore, target: Path) -> dict[str, str]:
    """Caller holds the pinned original store flock; preserve all validated bytes."""
    target.mkdir(mode=0o700)
    descriptor = open_directory(target)
    hashes = {}
    try:
        with os.scandir(store._fd) as children:  # noqa: SLF001 - offline store transaction
            names = sorted(child.name for child in children)
        for name in names:
            maximum = store.limits.max_store_bytes
            body = store._read(name, maximum)  # noqa: SLF001 - same validator/pinned fd
            output = os.open(
                name,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                0o600,
                dir_fd=descriptor,
            )
            try:
                with os.fdopen(output, "wb", closefd=False) as stream:
                    stream.write(body)
                    stream.flush()
                    os.fsync(output)
            finally:
                os.close(output)
            hashes[name] = hashlib.sha256(body).hexdigest()
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return hashes


def prepare_intent_state(
    archive_id: str,
    backup: Path,
    *,
    public: Path = PUBLIC_STORE,
    private: Path = PRIVATE_STORE,
    companion: Path = COMPANION,
) -> None:
    """Single first-activation transaction; partial evidence is never overwritten."""
    initial = IntentState(schema_version=1, archive_id=archive_id)
    if any(not (root / ".lock").is_file() for root in (public, private)):
        raise unavailable()
    parent = open_directory(companion.parent)
    try:
        if os.path.lexists(companion) or backup.exists():
            raise unavailable()
        with (
            OperationStore(public, private=True, existing=True) as api,
            OperationStore(private, private=True, existing=True) as worker,
            api._locked(),  # noqa: SLF001 - coordinated offline transaction
            worker._locked(),  # noqa: SLF001 - coordinated offline transaction
        ):
            records, _ = api._scan()  # noqa: SLF001 - exact predecessor validator
            worker_records, _ = worker._scan()  # noqa: SLF001
            if any(record.archive_id != archive_id for record in (*records, *worker_records)):
                raise unavailable()
            backup_parent = open_directory(backup.parent)
            try:
                os.mkdir(backup.name, mode=0o700, dir_fd=backup_parent)
                os.fsync(backup_parent)
            finally:
                os.close(backup_parent)
            manifest = {
                "schema_version": 1,
                "archive_id": archive_id,
                "api": _backup(api, backup / "api"),
                "worker": _backup(worker, backup / "worker"),
            }
            descriptor = open_directory(backup)
            try:
                manifest_fd = os.open(
                    "manifest.json",
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                    0o600,
                    dir_fd=descriptor,
                )
                try:
                    with os.fdopen(manifest_fd, "wb", closefd=False) as stream:
                        stream.write(serialize(manifest).encode())
                        stream.flush()
                        os.fsync(manifest_fd)
                finally:
                    os.close(manifest_fd)
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
            descriptor = os.open(
                companion.name,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                0o600,
                dir_fd=parent,
            )
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
            os.fsync(parent)
            api._write(INTENT_NAME, dump(initial), MAX_INTENT_BYTES)  # noqa: SLF001 - original store flock retained
    finally:
        os.close(parent)


_MAX_NATIVE_METADATA = 32768
_MAX_NATIVE_MASKS = 64
_NATIVE_MASKS = (
    "/srv/hfcache",
    "/run/credentials",
    "/run/secrets",
    "/etc/credstore",
    "/etc/credstore.encrypted",
    "/etc/hfcache/credentials",
    "/var/lib/hfcache/hf-home",
    "/var/lib/hfcache/.cache/huggingface",
    "/run/hfcache-host-helper",
    "/var/lib/hfcache/verification.instance.lock",
)


def validate_native_sources(server: ServerConfig, masks: tuple[Path, ...]) -> None:
    """Refuse configured credential sources not covered by reviewed native masks."""
    if (
        server.archive_config != Path("/etc/hfcache/config.toml")
        or server.state_directory != PUBLIC_STORE
    ):
        message = "Native activation requires the fixed archive/configuration stores"
        raise unavailable(message)
    sources = [server.credentials.writer, server.credentials.reader, server.credentials.mcp_reader]
    if server.basic is not None:
        sources.append(server.basic.administrator)
    files = [source.file for source in sources if source is not None and source.file is not None]
    if server.listener.tls is not None:
        files.append(server.listener.tls.private_key)
    if any(not any(file == mask or file.is_relative_to(mask) for mask in masks) for file in files):
        message = "Native activation requires reviewed masks for every configured credential source"
        raise unavailable(message)


def _native_show(unit: str, properties: tuple[str, ...]) -> dict[str, str]:
    result = subprocess.run(  # noqa: S603 - fixed native metadata allowlist, no service effect
        [
            "/usr/bin/systemctl",
            "--system",
            "show",
            unit,
            "--no-pager",
            "--property=" + ",".join(properties),
        ],
        check=True,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=5,
        env={"PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C"},
    )
    if len(result.stdout.encode()) > _MAX_NATIVE_METADATA:
        raise unavailable()
    rows = result.stdout.splitlines()
    values = dict(row.split("=", 1) for row in rows)
    if len(rows) != len(values) or set(values) != set(properties):
        raise unavailable()
    return values


def _native_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value = dict(pairs)
    if len(value) != len(pairs):
        message = "Duplicate native metadata key"
        raise ValueError(message)
    return value


def _native_credentials() -> dict[str, list[list[str]]]:
    """Read fixed typed arrays; human systemctl rendering is not authority."""
    expected: dict[str, list[list[str]]] = {
        "LoadCredential": [],
        "LoadCredentialEncrypted": [["hfcache.api", "/etc/credstore.encrypted/hfcache.api"]],
    }
    credentials: dict[str, list[list[str]]] = {}
    for name, entries in expected.items():
        result = subprocess.run(  # noqa: S603 - fixed system-bus metadata, no service effect
            [
                "/usr/bin/busctl",
                "--system",
                "--json=short",
                "--timeout=5",
                "get-property",
                "org.freedesktop.systemd1",
                "/org/freedesktop/systemd1/unit/hfcache_2dapi_2eservice",
                "org.freedesktop.systemd1.Service",
                name,
            ],
            check=True,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=5,
            env={"PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C"},
        )
        if len(result.stdout.encode()) > _MAX_NATIVE_METADATA:
            raise unavailable()
        try:
            document = json.loads(result.stdout, object_pairs_hook=_native_object)
        except ValueError:
            raise unavailable() from None
        if document != {"type": "a(ss)", "data": entries}:
            message = "Native activation requires the fixed packaged API credential delivery"
            raise unavailable(message)
        credentials[name] = document["data"]
    return credentials


def native_mask_policy(selected: Path) -> tuple[str, str]:
    """Read-only fixed native authority; no token source is opened or executed.

    Reuse the existing mask grammar and actual server model. Cached API startup
    and packaged bytes exclude unmodelled Hub-file/unit overrides. The revision
    brackets the final offline invocation and non-replacing companion publication.
    """
    account = pwd.getpwnam("hfcache")
    if account.pw_uid <= 0 or account.pw_gid <= 0 or account.pw_dir != "/var/lib/hfcache":
        raise unavailable()
    api = _native_show(
        "hfcache-api.service",
        (
            "FragmentPath",
            "DropInPaths",
            "ExecStart",
            "ImportCredential",
        ),
    )
    entry = "/opt/hfcache/current/.venv/bin/hfcache"
    expected = (
        "{ path="
        + entry
        + " ; argv[]="
        + entry
        + " serve --server-config /etc/hfcache/server.toml ; ignore_errors=no ;"
    )
    credentials = _native_credentials()
    if (
        api["DropInPaths"]
        or api["ImportCredential"] != "hf-token"
        or api["FragmentPath"]
        not in {
            "/etc/systemd/system/hfcache-api.service",
            str(selected / "packaging/systemd/hfcache-api.service"),
            "/opt/hfcache/current/packaging/systemd/hfcache-api.service",
        }
        or not api["ExecStart"].startswith(expected)
        or api["ExecStart"].count("{ path=") != 1
        or not api["ExecStart"].endswith("}")
    ):
        message = "Native activation requires the fixed packaged API startup without overrides"
        raise unavailable(message)
    packaged = (selected / "packaging/systemd/hfcache-api.service").read_bytes()
    if Path(api["FragmentPath"]).read_bytes() != packaged:
        raise unavailable()
    worker = _native_show("hfcache-verification.service", ("LoadState", "InaccessiblePaths"))
    if worker["LoadState"] != "loaded":
        message = "Native activation requires the reviewed verifier mask policy"
        raise unavailable(message)
    archive = load_config(NATIVE_ARCHIVE_CONFIG)
    if archive.storage.archive_root != Path("/srv/hfcache"):
        message = "Native activation requires the fixed masked archive root /srv/hfcache"
        raise unavailable(message)
    probe = runpy.run_path(str(selected / "scripts/hardening-probe.py"))
    canonical = probe["canonical_path"]
    raw_masks = worker["InaccessiblePaths"].split()
    if len(raw_masks) > _MAX_NATIVE_MASKS:
        raise unavailable()
    try:
        masks = tuple(
            dict.fromkeys(
                Path(canonical(value.removeprefix("-"))) for value in (*_NATIVE_MASKS, *raw_masks)
            )
        )
    except probe["RefusedError"]:
        raise unavailable() from None
    raw = NATIVE_SERVER.read_bytes()
    server = validate_server_config_mapping(tomllib.loads(raw.decode("utf-8")))
    validate_native_sources(server, masks)
    mask_text = " ".join("-" + str(path) for path in masks)
    revision = hashlib.sha256(
        serialize(
            {
                "server": hashlib.sha256(raw).hexdigest(),
                "archive": hashlib.sha256(NATIVE_ARCHIVE_CONFIG.read_bytes()).hexdigest(),
                "api": api,
                "credentials": credentials,
                "worker": worker,
                "packaged": hashlib.sha256(packaged).hexdigest(),
                "masks": mask_text,
                "principal": [account.pw_uid, account.pw_gid, account.pw_dir],
            }
        ).encode()
    ).hexdigest()
    return mask_text, revision


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive-id", required=True)
    parser.add_argument("--backup-directory", type=Path)
    parser.add_argument("--native-masks-only", action="store_true")
    parser.add_argument("--native-masks")
    parser.add_argument("--native-revision")
    options = parser.parse_args()
    if options.native_masks_only and (
        options.native_masks is not None or options.native_revision is not None
    ):
        parser.error("native policy modes are mutually exclusive")
    if (options.native_masks is None) != (options.native_revision is None):
        parser.error("native masks and revision are required together")
    configured = load_config(NATIVE_ARCHIVE_CONFIG)
    if str(configured.storage.archive_id) != options.archive_id:
        raise unavailable()
    if options.native_masks_only or options.native_masks is not None:
        masks, revision = native_mask_policy(Path(sys.executable).parents[2])
        if options.native_masks_only:
            sys.stdout.write(masks + "\n" + revision + "\n")
            return
        if masks != options.native_masks or revision != options.native_revision:
            message = "Native activation authority changed; preserve state for review"
            raise unavailable(message)
    if options.backup_directory is None:
        parser.error("explicit backup directory required")
    prepare_intent_state(options.archive_id, options.backup_directory)


if __name__ == "__main__":
    main()
