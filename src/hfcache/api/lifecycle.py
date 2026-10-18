"""One daemon inode lock and a bounded, context-propagating metadata pool."""

import asyncio
import fcntl
import os
import stat
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

from hfcache.errors import SafetyError
from hfcache.logging import submit_with_context

_LOCK_MODE = 0o600

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from pathlib import Path


def unavailable() -> SafetyError:
    return SafetyError.single("metadata service is full or draining", code="HFAPI009")


@contextmanager
def instance_lock(path: Path) -> Iterator[None]:
    """Retain one existing/created inode; never unlink a potentially held lock."""
    descriptor = -1
    parent = -1
    try:
        parent = open_directory(path.parent)
        descriptor = os.open(
            path.name,
            os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
            0o600,
            dir_fd=parent,
        )
        info = os.fstat(descriptor)
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_uid != os.geteuid()
            or stat.S_IMODE(info.st_mode) != _LOCK_MODE
            or info.st_nlink != 1
        ):
            raise OSError  # noqa: TRY301 - classify invalid inode and flock failures together
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError, ValueError:
        message = "daemon instance lock is unsafe, unavailable or already held"
        raise SafetyError.single(message, code="HFAPI011") from None
    else:
        yield
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if parent >= 0:
            os.close(parent)


def open_directory(path: Path) -> int:
    """Open every directory component without following symlinks."""
    if not path.is_absolute() or ".." in path.parts:
        raise OSError
    descriptor = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        for part in path.parts[1:]:
            following = os.open(
                part,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                dir_fd=descriptor,
            )
            os.close(descriptor)
            descriptor = following
    except BaseException:
        os.close(descriptor)
        raise
    return descriptor


class MetadataLease:
    def __init__(self, pool: MetadataPool, function: Callable[[], Any]) -> None:
        self.pool = pool
        self.worker_done = False
        self.request_done = False
        self.released = False
        loop = asyncio.get_running_loop()
        future = submit_with_context(pool.executor, function)
        self.worker = future
        future.add_done_callback(lambda _: loop.call_soon_threadsafe(self.finished))
        self.future = asyncio.wrap_future(future)

    def finished(self) -> None:
        self.worker_done = True
        self.release()

    def finish_request(self) -> None:
        self.request_done = True
        # A finished worker's queued event-loop callback may still be pending.
        # Inspect the real future; an asyncio cancellation alone cannot prove a
        # running thread has stopped and must never free its admission slot.
        self.worker_done = self.worker.done()
        self.release()

    def release(self) -> None:
        if self.worker_done and self.request_done and not self.released:
            self.pool.inflight -= 1
            self.released = True


class MetadataPool:
    """Capacity covers running, queued and slow streaming observers until finished."""

    def __init__(self, *, workers: int, pending: int) -> None:
        self.executor = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="hfcache-read")
        self.capacity = workers + pending
        self.inflight = 0
        self.closed = False

    def submit(self, function: Callable[[], Any]) -> MetadataLease:
        if self.closed or self.inflight >= self.capacity:
            raise unavailable()
        self.inflight += 1
        try:
            return MetadataLease(self, function)
        except BaseException:
            self.inflight -= 1
            raise

    async def close(self) -> None:
        self.closed = True
        await asyncio.to_thread(self.executor.shutdown, wait=True, cancel_futures=False)
