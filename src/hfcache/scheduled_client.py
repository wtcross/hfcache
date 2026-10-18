"""Fixed scheduled API clients retain observation evidence across restarts (decision 121).

This private record is a safety handle, never a queue: an existing record permits
only lookup and observation. Each HTTP observation has the ordinary finite client
budget while the oneshot remains active until the exact terminal result exists.
"""

import argparse
import fcntl
import json
import os
import signal
import stat
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING, Literal, Self
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, model_validator

from hfcache.client import ApiClient
from hfcache.client_config import ClientConfig, resolve_client_config
from hfcache.client_errors import ClientConnectionError
from hfcache.client_models import (
    ArchiveId,
    ClientOperation,
    Identifier,
    Version,
)
from hfcache.errors import HfcacheError, SafetyError
from hfcache.models import serialize
from hfcache.redaction import redact_text, sanitize

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import FrameType

    from hfcache.reporting import Envelope

Command = Literal["sync", "verify-full"]
_MAX_HANDLE_BYTES = 4096
_RETRY_SECONDS = 5.0
_ROUTES = {"sync": "/api/v1/syncs", "verify-full": "/api/v1/verifications"}
_BODY = {"sync": {}, "verify-full": {"mode": "full"}}
_STABLE_FIELDS = (
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


def _unsafe() -> SafetyError:
    return SafetyError.single(
        "Scheduled observation evidence is unsafe or incompatible", code="HFAPI014"
    )


def _endpoint(config: ClientConfig) -> str:
    return "unix:" + str(config.socket) if config.socket is not None else config.url


class ScheduledObservation(BaseModel):
    """Independent schema 1 contains no bearer, digest, request body or replay authority."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True, hide_input_in_errors=True)

    schema_version: Version
    command: Command
    endpoint: str
    archive_id: ArchiveId
    principal: Literal["rest-writer"]
    idempotency_key: Identifier
    operation_id: Identifier | None

    @model_validator(mode="after")
    def endpoint_shape(self) -> Self:
        if self.endpoint.startswith("unix:"):
            settings = ClientConfig(schema_version=1, api_socket=Path(self.endpoint[5:]))
            if _endpoint(settings) != self.endpoint:
                raise _unsafe()
        else:
            settings = ClientConfig(schema_version=1, api_url=self.endpoint)
            if settings.url != self.endpoint:
                raise _unsafe()
        return self


def _pairs(values: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in values:
        if key in result:
            raise _unsafe()
        result[key] = value
    return result


def _private(info: os.stat_result, *, directory: bool = False) -> None:
    expected = 0o700 if directory else 0o600
    kind = stat.S_ISDIR if directory else stat.S_ISREG
    if (
        not kind(info.st_mode)
        or info.st_uid != os.geteuid()
        or stat.S_IMODE(info.st_mode) != expected
        or (not directory and info.st_nlink != 1)
    ):
        raise _unsafe()


def _ancestor(descriptor: int) -> None:
    info = os.fstat(descriptor)
    if info.st_uid not in {0, os.geteuid()} or (
        info.st_mode & 0o022 and not info.st_mode & stat.S_ISVTX
    ):
        raise _unsafe()


def _open_parent(path: Path) -> int:
    text = str(path)
    if (
        not path.is_absolute()
        or len(text.encode("utf-8")) > _MAX_HANDLE_BYTES
        or any(part in {".", ".."} for part in text.split("/"))
        or any(not character.isprintable() for character in text)
        or "\\" in text
        or not path.name
    ):
        raise _unsafe()
    descriptor = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        _ancestor(descriptor)
        for part in path.parent.parts[1:]:
            following = os.open(
                part,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                dir_fd=descriptor,
            )
            os.close(descriptor)
            descriptor = following
            _ancestor(descriptor)
    except BaseException:
        os.close(descriptor)
        raise
    return descriptor


class ObservationFile:
    """Pinned private directory and persistent inode lock protect one timer handle."""

    def __init__(self, path: Path, checkpoint: Callable[[str], None] | None = None) -> None:
        self.path = path
        self.checkpoint = checkpoint or (lambda _: None)
        self.parent = self.directory = self.lock = -1
        self.observed = False
        self.record: tuple[int, ...] | None = None

    def __enter__(self) -> Self:
        try:
            self.parent = _open_parent(self.path)
            try:
                os.mkdir(self.path.name, mode=0o700, dir_fd=self.parent)
            except FileExistsError:
                pass
            else:
                os.fsync(self.parent)
            self.directory = os.open(
                self.path.name,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                dir_fd=self.parent,
            )
            _private(os.fstat(self.directory), directory=True)
            self.lock = os.open(
                ".lock",
                os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
                0o600,
                dir_fd=self.directory,
            )
            _private(os.fstat(self.lock))
            fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.check()
        except OSError, ValueError:
            self.__exit__(None, None, None)
            raise _unsafe() from None
        except BaseException:
            self.__exit__(None, None, None)
            raise
        return self

    def __exit__(self, *_: object) -> None:
        for name in ("lock", "directory", "parent"):
            descriptor = getattr(self, name)
            if descriptor >= 0:
                os.close(descriptor)
                setattr(self, name, -1)

    def check(self) -> bool:
        for descriptor, name, parent in (
            (self.directory, self.path.name, self.parent),
            (self.lock, ".lock", self.directory),
        ):
            opened = os.fstat(descriptor)
            linked = os.stat(name, dir_fd=parent, follow_symlinks=False)
            if (opened.st_dev, opened.st_ino) != (linked.st_dev, linked.st_ino):
                raise _unsafe()
            _private(opened, directory=descriptor == self.directory)
        if os.fstat(self.lock).st_size != 0:
            raise _unsafe()
        present = False
        with os.scandir(self.directory) as entries:
            for entry in entries:
                if entry.name not in {".lock", "pending.json"}:
                    raise _unsafe()
                present = present or entry.name == "pending.json"
        self._check_record()
        return present

    def _check_record(self) -> None:
        if not self.observed:
            return
        try:
            linked = os.stat("pending.json", dir_fd=self.directory, follow_symlinks=False)
        except FileNotFoundError:
            if self.record is not None:
                raise _unsafe() from None
        else:
            if self.record != tuple(getattr(linked, name) for name in _STABLE_FIELDS):
                raise _unsafe()

    def read(self) -> ScheduledObservation | None:
        present = self.check()
        descriptor = -1
        try:
            descriptor = os.open(
                "pending.json",
                os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
                dir_fd=self.directory,
            )
            before = os.fstat(descriptor)
            _private(before)
            if not 0 < before.st_size <= _MAX_HANDLE_BYTES:
                raise _unsafe()
            raw = bytearray()
            while len(raw) <= _MAX_HANDLE_BYTES:
                part = os.read(descriptor, _MAX_HANDLE_BYTES + 1 - len(raw))
                if not part:
                    break
                raw.extend(part)
            after = os.fstat(descriptor)
            if len(raw) != before.st_size or any(
                getattr(before, field) != getattr(after, field) for field in _STABLE_FIELDS
            ):
                raise _unsafe()
            payload = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs)
            handle = ScheduledObservation.model_validate(payload)
            self.observed = True
            self.record = tuple(getattr(after, name) for name in _STABLE_FIELDS)
            self._check_record()
        except FileNotFoundError:
            if present:
                raise _unsafe() from None
            self.observed = True
            self.record = None
            return None
        except OSError, ValueError, UnicodeError, RecursionError:
            raise _unsafe() from None
        else:
            return handle
        finally:
            if descriptor >= 0:
                os.close(descriptor)

    def write(self, handle: ScheduledObservation) -> None:
        self.check()
        raw = serialize(handle.model_dump(mode="json")).encode("utf-8")
        if len(raw) > _MAX_HANDLE_BYTES:
            raise _unsafe()
        temporary = ".pending-" + uuid4().hex + ".tmp"
        self.checkpoint("before_write")
        descriptor = os.open(
            temporary,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
            0o600,
            dir_fd=self.directory,
        )
        try:
            position = 0
            while position < len(raw):
                written = os.write(descriptor, raw[position:])
                if written <= 0:
                    raise _unsafe()
                position += written
            self.checkpoint("before_file_fsync")
            os.fsync(descriptor)
            self.checkpoint("after_file_fsync")
            created = os.fstat(descriptor)
        finally:
            os.close(descriptor)
        self.checkpoint("before_rename")
        # A crash leaves unexplained temporary evidence intact (FS-19).
        self._check_record()
        linked = os.stat(temporary, dir_fd=self.directory, follow_symlinks=False)
        if (created.st_dev, created.st_ino) != (linked.st_dev, linked.st_ino):
            raise _unsafe()
        os.rename(temporary, "pending.json", src_dir_fd=self.directory, dst_dir_fd=self.directory)
        self.observed = True
        linked = os.stat("pending.json", dir_fd=self.directory, follow_symlinks=False)
        self.record = tuple(getattr(linked, name) for name in _STABLE_FIELDS)
        self.checkpoint("after_rename")
        self.checkpoint("before_directory_fsync")
        os.fsync(self.directory)
        self.checkpoint("after_directory_fsync")

    def complete(self) -> None:
        self.check()
        self.checkpoint("before_unlink")
        self.check()
        os.unlink("pending.json", dir_fd=self.directory)
        self.checkpoint("after_unlink")
        os.fsync(self.directory)
        self.checkpoint("after_completion_fsync")


def _binding(config: ClientConfig, command: Command) -> dict[str, object]:
    if config.expected_archive_id is None or command not in _ROUTES:
        raise _unsafe()
    return {
        "schema_version": 1,
        "command": command,
        "endpoint": _endpoint(config),
        "archive_id": config.expected_archive_id,
        "principal": "rest-writer",
    }


def _operation(handle: ScheduledObservation, operation: object) -> None:
    if (
        not isinstance(operation, ClientOperation)
        or operation.route != _ROUTES[handle.command]
        or operation.archive_id != handle.archive_id
        or operation.principal != handle.principal
        or (handle.operation_id is not None and operation.operation_id != handle.operation_id)
    ):
        raise _unsafe()


def _recover(
    client: ApiClient, handle: ScheduledObservation, sleep: Callable[[float], None]
) -> ScheduledObservation:
    if redact_text(handle.idempotency_key) != handle.idempotency_key:
        raise _unsafe()
    while True:
        try:
            operation = client.lookup(handle.idempotency_key)
        except ClientConnectionError:
            sleep(_RETRY_SECONDS)
            continue
        _operation(handle, operation)
        return handle.model_copy(update={"operation_id": operation.operation_id})


def _authenticate(client: ApiClient, *, recovering: bool, sleep: Callable[[float], None]) -> None:
    while True:
        try:
            capabilities = client.capabilities()
        except ClientConnectionError:
            if not recovering:
                raise
            sleep(_RETRY_SECONDS)
            continue
        if (
            capabilities.credential_class != "rest-writer"
            or not capabilities.operations
            or not capabilities.operation_history
        ):
            raise _unsafe()
        return


def _await_terminal(
    client: ApiClient,
    operation_id: str,
    command: Command,
    state: ObservationFile,
    sleep: Callable[[float], None],
) -> Envelope:
    while True:
        try:
            result = client.observe(operation_id).envelope
        except ClientConnectionError:
            sleep(_RETRY_SECONDS)
            continue
        if result.command != ("sync" if command == "sync" else "verify --full"):
            raise _unsafe()
        state.complete()
        return result


def run_scheduled(  # noqa: PLR0913 - explicit injection seams for durable boundary tests
    config: ClientConfig,
    command: Command,
    state_directory: Path,
    *,
    client_factory: Callable[[ClientConfig], ApiClient] = ApiClient,
    sleep: Callable[[float], None] = time.sleep,
    checkpoint: Callable[[str], None] | None = None,
    on_key: Callable[[str], None] | None = None,
    on_accepted: Callable[[str], None] | None = None,
) -> Envelope:
    """Observe one fixed scheduled intention; an old record never authorizes POST."""
    binding = _binding(config, command)
    try:
        with ObservationFile(state_directory, checkpoint) as state:
            existing = state.read()
            if existing is not None and any(
                getattr(existing, name) != value for name, value in binding.items()
            ):
                raise _unsafe()
            with client_factory(config) as client:
                _authenticate(client, recovering=existing is not None, sleep=sleep)
                handle = existing
                if handle is None:
                    handle = ScheduledObservation.model_validate(
                        binding | {"idempotency_key": uuid4().hex, "operation_id": None}
                    )
                    state.write(handle)
                    state.check()
                    try:
                        submitted = client.submit(
                            _ROUTES[command],
                            _BODY[command],
                            key=handle.idempotency_key,
                            on_key=on_key,
                        )
                    except HfcacheError:
                        handle = _recover(client, handle, sleep)
                    else:
                        _operation(handle, submitted.acceptance.operation)
                        handle = handle.model_copy(
                            update={
                                "operation_id": submitted.acceptance.operation.operation_id,
                            }
                        )
                else:
                    handle = _recover(client, handle, sleep)
                if (
                    handle.operation_id is None
                    or redact_text(handle.operation_id) != handle.operation_id
                ):
                    raise _unsafe()
                if existing is not None and on_key is not None:
                    on_key(handle.idempotency_key)
                if on_accepted is not None:
                    on_accepted(handle.operation_id)
                if handle != existing:
                    state.write(handle)
                return _await_terminal(client, handle.operation_id, command, state, sleep)
    except OSError, ValueError:
        raise _unsafe() from None


def main() -> int:
    parser = argparse.ArgumentParser(description="Observe one fixed scheduled hfcache API job")
    parser.add_argument("--client-config", type=Path, required=True)
    parser.add_argument("--state-directory", type=Path, required=True)
    parser.add_argument("command", choices=("sync", "verify-full"))
    options = parser.parse_args()
    stop_requested = False

    def check_stop() -> None:
        if stop_requested:
            raise KeyboardInterrupt

    def observer_sleep(seconds: float) -> None:
        check_stop()
        time.sleep(seconds)
        check_stop()

    def create_client(config: ClientConfig) -> ApiClient:
        check_stop()
        return ApiClient(config, sleep=observer_sleep)

    def key_notice(value: str) -> None:
        check_stop()
        sys.stderr.write(f"Idempotency key: {value}\n")

    def accepted_notice(value: str) -> None:
        check_stop()
        sys.stderr.write(f"Accepted operation: {value}\n")

    def terminate(_number: int, _frame: FrameType | None) -> None:
        nonlocal stop_requested
        stop_requested = True
        raise KeyboardInterrupt

    previous_handlers = {
        number: signal.getsignal(number) for number in (signal.SIGINT, signal.SIGTERM)
    }
    for number in previous_handlers:
        signal.signal(number, terminate)
    try:
        try:
            result = run_scheduled(
                resolve_client_config(options.client_config),
                options.command,
                options.state_directory,
                client_factory=create_client,
                sleep=observer_sleep,
                on_key=key_notice,
                on_accepted=accepted_notice,
            )
        except HfcacheError as error:
            sys.stderr.write(str(error) + "\n")
            _recovery_notice(options.state_directory)
            return int(error.exit_code)
        except KeyboardInterrupt:
            sys.stderr.write("HFAPI019: Scheduled observer stopped; accepted work may continue\n")
            _recovery_notice(options.state_directory)
            return 20
        sys.stdout.write(serialize(sanitize(result.to_payload()), indent=None))
        return result.exit_code
    finally:
        for number, handler in previous_handlers.items():
            signal.signal(number, handler)


def _recovery_notice(path: Path) -> None:
    safe_path = redact_text(str(path)).encode("unicode_escape").decode("ascii")
    sys.stderr.write(
        f"Accepted work may continue; preserve recovery state in {safe_path} "
        "and restart the same observer to look up its original key.\n"
    )


if __name__ == "__main__":
    raise SystemExit(main())
