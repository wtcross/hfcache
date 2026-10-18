"""Decisions 115/128: strict inherited or PID1-owned private verification startup.

Importing this bootstrap does not import Hub, credentials or command services.
The API never launches it; the service manager supplies its independent sandbox.
"""

import argparse
import os
import pwd
import signal
import socket
import threading
from contextlib import nullcontext
from pathlib import Path

from hfcache.offline import initialize_offline_process
from hfcache.verification_listener import notify_ready, owned_listener, reserve_listener

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


def _only_activation_descriptor(maximum: int = _ACTIVATION_FD) -> bool:
    """Audit inheritance before NSS or shared runtime imports can open descriptors."""
    try:
        for entry in list(Path("/proc/self/fd").iterdir()):
            descriptor = int(entry.name)
            if descriptor > maximum:
                try:
                    os.fstat(descriptor)
                except OSError:
                    continue
                return False
    except OSError, ValueError:
        return False
    return True


def _valid_bootstrap(options: argparse.Namespace) -> bool:
    if (
        (options.api_uid is not None and options.api_uid < 0)
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
    ):
        return False
    if options.container_listener:
        return (
            os.getpid() == 1
            and not any(name.startswith("LISTEN_") for name in os.environ)
            and _only_activation_descriptor(2)
        )
    return (
        os.environ.get("LISTEN_PID") == str(os.getpid())
        and os.environ.get("LISTEN_FDS") == "1"
        and os.environ.get("LISTEN_FDNAMES") == _ACTIVATION_NAME
        and _pidfd_matches()
        and _only_activation_descriptor()
    )


def _run(
    options: argparse.Namespace,
    listener: socket.socket,
    api_uid: int,
    stop: threading.Event | None = None,
) -> int:
    # The entrypoint has audited inheritance and initialized offline before any
    # shared imports can open their own descriptors or load Hub libraries.
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
        if options.container_listener and (
            options.socket.is_relative_to(config.storage.archive_root)
            or config.storage.archive_root.is_relative_to(options.socket)
        ):
            raise unavailable()
        policy = InstalledPolicy(
            options.config, config.storage.archive_root, config.storage.archive_id
        )
        if stop is None:
            # Native activation retains its existing signal initialization.
            stop = threading.Event()
            signal.signal(signal.SIGTERM, lambda *_: stop.set())
            signal.signal(signal.SIGINT, lambda *_: stop.set())
        if not options.container_listener:
            validate_listener(listener, options.socket)
        with (
            instance_lock(root.with_name(root.name + ".instance.lock")),
            OperationStore(root) as store,
        ):
            scope = (
                owned_listener(listener, options.socket)
                if options.container_listener
                else nullcontext(None)
            )
            with scope as owned:
                if owned is not None:
                    validate_listener(
                        listener,
                        options.socket,
                        bound_address=owned.bound_address,
                        owned_identity=owned.identity,
                    )
                worker = VerificationWorker(policy, store)
                try:
                    if options.container_listener and not notify_ready(stop):
                        return 0
                    serve_worker(listener, worker, expected_uid=api_uid, stop=stop)
                finally:
                    # Readiness failures and stop-during-startup also join before
                    # the owned listener, store or instance lock can be released.
                    worker.close()
    except OSError, ValueError, HfcacheError:
        return 20
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Private isolated verification executor")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--state-directory", type=Path, required=True)
    parser.add_argument("--socket", type=Path, required=True)
    parser.add_argument("--container-listener", action="store_true")
    peer_flags = parser.add_mutually_exclusive_group()
    peer_flags.add_argument("--api-uid", type=int)
    peer_flags.add_argument("--api-user")
    options = parser.parse_args()
    if not _valid_bootstrap(options):
        return 20
    stop = threading.Event()
    previous = (
        {
            number: signal.signal(number, lambda *_: stop.set())
            for number in (signal.SIGTERM, signal.SIGINT)
        }
        if options.container_listener
        else {}
    )
    try:
        # Reserve owned FD3 before NSS/runtime can claim it; all descriptors
        # opened after this point are bootstrap resources, not inherited inputs.
        channel = (
            reserve_listener()
            if options.container_listener
            else socket.socket(fileno=_ACTIVATION_FD)
        )
        with channel:
            channel.set_inheritable(False)
            api_uid = (
                pwd.getpwnam(options.api_user).pw_uid
                if options.api_user is not None
                else (options.api_uid if options.api_uid is not None else os.geteuid())
            )
            if options.container_listener and stop.is_set():
                return 0
            for name in ("LISTEN_PID", "LISTEN_FDS", "LISTEN_FDNAMES", "LISTEN_PIDFDID"):
                os.environ.pop(name, None)
            initialize_offline_process()
            return _run(options, channel, api_uid, stop if options.container_listener else None)
    except KeyError, OSError, ValueError:
        return 20
    finally:
        for number, handler in previous.items():
            signal.signal(number, handler)


if __name__ == "__main__":
    raise SystemExit(main())
