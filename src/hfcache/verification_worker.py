"""Systemd socket-activated verification entry point, with startup-only offline init.

Importing this bootstrap does not import Hub, credentials or command services.
The API never launches it; the service manager supplies its independent sandbox.
"""

import argparse
import os
import pwd
import signal
import socket
import threading
from pathlib import Path

from hfcache.offline import initialize_offline_process

_ACTIVATION_FD = 3
_ACTIVATION_NAME = "hfcache-verification"


def _pidfd_matches() -> bool:
    if (identity := os.environ.get("LISTEN_PIDFDID")) is None:
        return True
    try:
        descriptor = os.pidfd_open(os.getpid())
        try:
            return identity == str(os.fstat(descriptor).st_ino)
        finally:
            os.close(descriptor)
    except OSError, ValueError:
        return False


def _only_activation_descriptor() -> bool:
    """Audit inheritance before NSS or shared runtime imports can open descriptors."""
    try:
        for entry in list(Path("/proc/self/fd").iterdir()):
            descriptor = int(entry.name)
            if descriptor > _ACTIVATION_FD:
                try:
                    os.fstat(descriptor)
                except OSError:
                    continue
                return False
    except OSError, ValueError:
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Private socket-activated verification executor")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--state-directory", type=Path, required=True)
    parser.add_argument("--socket", type=Path, required=True)
    peer_flags = parser.add_mutually_exclusive_group()
    peer_flags.add_argument("--api-uid", type=int)
    peer_flags.add_argument("--api-user")
    options = parser.parse_args()
    if (
        os.environ.get("LISTEN_PID") != str(os.getpid())
        or os.environ.get("LISTEN_FDS") != "1"
        or os.environ.get("LISTEN_FDNAMES") != _ACTIVATION_NAME
        or (options.api_uid is not None and options.api_uid < 0)
        or any(
            not path.is_absolute()
            for path in (options.config, options.state_directory, options.socket)
        )
        or any(
            name in os.environ
            for name in (
                "HF_TOKEN",
                "HUGGING_FACE_HUB_TOKEN",
                "HUGGINGFACE_HUB_TOKEN",
                "HUGGINGFACEHUB_API_TOKEN",
                "CREDENTIALS_DIRECTORY",
                "HF_TOKEN_PATH",
                "HFCACHE_API_TOKEN",
                "HFCACHE_MCP_TOKEN",
            )
        )
        or not _pidfd_matches()
        or not _only_activation_descriptor()
    ):
        return 20
    try:
        api_uid = (
            pwd.getpwnam(options.api_user).pw_uid
            if options.api_user is not None
            else (options.api_uid if options.api_uid is not None else os.geteuid())
        )
    except KeyError:
        return 20
    for name in ("LISTEN_PID", "LISTEN_FDS", "LISTEN_FDNAMES", "LISTEN_PIDFDID"):
        os.environ.pop(name, None)
    initialize_offline_process()
    # Initialize the process-wide library switch before shared command imports.
    from hfcache.api.lifecycle import instance_lock  # noqa: PLC0415
    from hfcache.api.operations import OperationStore  # noqa: PLC0415
    from hfcache.config import load_config  # noqa: PLC0415
    from hfcache.errors import HfcacheError  # noqa: PLC0415
    from hfcache.server_config import InstalledPolicy  # noqa: PLC0415
    from hfcache.verification_executor import (  # noqa: PLC0415
        VerificationWorker,
        serve_worker,
        validate_listener,
    )
    from hfcache.verification_protocol import unavailable  # noqa: PLC0415

    try:
        config = load_config(options.config)
        root = options.state_directory
        if root.is_relative_to(
            config.storage.archive_root
        ) or config.storage.archive_root.is_relative_to(root):
            raise unavailable()
        policy = InstalledPolicy(
            options.config, config.storage.archive_root, config.storage.archive_id
        )
        stop = threading.Event()
        signal.signal(signal.SIGTERM, lambda *_: stop.set())
        signal.signal(signal.SIGINT, lambda *_: stop.set())
        with socket.socket(fileno=_ACTIVATION_FD) as listener:
            listener.set_inheritable(False)
            validate_listener(listener, options.socket)
            with (
                instance_lock(root.with_name(root.name + ".instance.lock")),
                OperationStore(root) as store,
            ):
                worker = VerificationWorker(policy, store)
                serve_worker(listener, worker, expected_uid=api_uid, stop=stop)
    except OSError, ValueError, HfcacheError:
        return 20
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
