"""The local exclusive lock, and what it does when someone else holds it.

Contention is exercised in-process rather than with a second process, because
`flock(2)` associates the lock with the *open file description* — a second
`open()` of the same path in the same process conflicts exactly as another
process would. That is what makes these tests deterministic instead of timed.

`/run/hfcache` is never touched: every test supplies its own directory.
"""

import fcntl
import json
import os
from typing import TYPE_CHECKING

import pytest

from hfcache.errors import ExitCode, SafetyError
from hfcache.locking import (
    LOCK_DIRECTORY,
    LOCK_NAME,
    exclusive_lock,
    lock_path,
    read_holder,
)

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def path(tmp_path: Path) -> Path:
    return lock_path(tmp_path / "run")


def hold(path: Path) -> int:
    """Take the lock the way another process would, and return the descriptor."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
    fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    return descriptor


def codes(problems) -> list[str]:
    return [problem.code for problem in problems]


# --------------------------------------------------------------------------- #
# Where the lock lives
# --------------------------------------------------------------------------- #


def test_the_lock_is_one_file_under_run_hfcache():
    # `AD-17`: one lock for every mutating command, on local tmpfs, never on NFS.
    assert lock_path() == LOCK_DIRECTORY / LOCK_NAME
    assert str(LOCK_DIRECTORY).startswith("/run/")


def test_the_lock_directory_is_created_if_systemd_did_not(tmp_path: Path):
    # `RuntimeDirectory=hfcache` makes it under the unit; a manual invocation on
    # a fresh boot has to make it itself.
    target = lock_path(tmp_path / "absent")

    with exclusive_lock(target, command="sync", wait_seconds=0):
        assert target.parent.is_dir()


def test_the_lock_directory_is_private_to_the_writer(tmp_path: Path):
    target = lock_path(tmp_path / "run")
    original = os.umask(0o000)
    try:
        with exclusive_lock(target, command="sync", wait_seconds=0):
            pass
    finally:
        os.umask(original)

    assert target.parent.stat().st_mode & 0o777 == 0o700


# --------------------------------------------------------------------------- #
# Holding it
# --------------------------------------------------------------------------- #


def test_the_lock_is_acquired_and_released(path: Path):
    with exclusive_lock(path, command="sync", wait_seconds=0):
        pass

    # Released means the next acquisition succeeds, which is the only observable
    # form of the claim.
    with exclusive_lock(path, command="prune", wait_seconds=0):
        pass


def test_the_holder_records_who_it_is(path: Path):
    with exclusive_lock(path, command="sync", wait_seconds=0):
        holder = read_holder(path)

    assert holder["command"] == "sync"
    assert holder["pid"] == os.getpid()
    assert holder["started_at"].endswith("Z")


def test_the_record_is_cleared_on_release(path: Path):
    # So a later command that fails to acquire never names a process that has
    # already finished.
    with exclusive_lock(path, command="sync", wait_seconds=0):
        pass

    assert read_holder(path) == {}


def test_the_lock_is_released_even_when_the_body_raises(path: Path):
    message = "the run failed"
    with (
        pytest.raises(RuntimeError, match=message),
        exclusive_lock(path, command="sync", wait_seconds=0),
    ):
        raise RuntimeError(message)

    with exclusive_lock(path, command="sync", wait_seconds=0):
        pass


# --------------------------------------------------------------------------- #
# When someone else holds it
# --------------------------------------------------------------------------- #


def test_a_held_lock_is_hfmnt010(path: Path):
    descriptor = hold(path)
    try:
        with (
            pytest.raises(SafetyError) as caught,
            exclusive_lock(path, command="sync", wait_seconds=0),
        ):
            pass  # pragma: no cover - the acquisition raises before the body
    finally:
        os.close(descriptor)

    assert codes(caught.value.problems) == ["HFMNT010"]
    assert caught.value.exit_code == ExitCode.SAFETY


def test_the_refusal_names_the_holder(path: Path):
    descriptor = hold(path)
    os.write(descriptor, json.dumps({"command": "verify --full", "pid": 4242}).encode("utf-8"))
    try:
        with (
            pytest.raises(SafetyError) as caught,
            exclusive_lock(path, command="sync", wait_seconds=0),
        ):
            pass  # pragma: no cover - the acquisition raises before the body
    finally:
        os.close(descriptor)

    message = caught.value.problems[0].message
    assert "verify --full" in message
    assert "4242" in message


def test_the_refusal_says_so_when_the_holder_left_no_record(path: Path):
    descriptor = hold(path)
    try:
        with (
            pytest.raises(SafetyError) as caught,
            exclusive_lock(path, command="sync", wait_seconds=0),
        ):
            pass  # pragma: no cover - the acquisition raises before the body
    finally:
        os.close(descriptor)

    assert "no record" in caught.value.problems[0].message


def test_a_waiting_command_retries_until_the_lock_is_free(
    path: Path, monkeypatch: pytest.MonkeyPatch
):
    # The wait is a poll, because `flock` has no timed variant. Releasing inside
    # the sleep makes the retry deterministic rather than a race with a thread.
    descriptor = hold(path)
    released = []

    def release(_seconds):
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        released.append(True)

    monkeypatch.setattr("hfcache.locking.time.sleep", release)
    try:
        with exclusive_lock(path, command="sync", wait_seconds=3600, poll_seconds=0.0):
            acquired = read_holder(path)
    finally:
        os.close(descriptor)

    assert released, "the first attempt must have failed for this to prove anything"
    assert acquired["command"] == "sync"


def test_a_zero_wait_gives_up_without_sleeping(path: Path, monkeypatch: pytest.MonkeyPatch):
    def refuse(_seconds):
        message = "wait_seconds=0 means try once and give up"
        raise AssertionError(message)

    monkeypatch.setattr("hfcache.locking.time.sleep", refuse)
    descriptor = hold(path)
    try:
        with pytest.raises(SafetyError), exclusive_lock(path, command="sync", wait_seconds=0):
            pass  # pragma: no cover - the acquisition raises before the body
    finally:
        os.close(descriptor)


# --------------------------------------------------------------------------- #
# Reading a holder record
# --------------------------------------------------------------------------- #


def test_an_absent_record_is_empty_rather_than_an_error(tmp_path: Path):
    assert read_holder(tmp_path / "absent") == {}


@pytest.mark.parametrize("content", ["", "{ not json", "[1, 2, 3]", '"a string"'])
def test_an_unusable_record_never_replaces_the_answer_already_known(tmp_path: Path, content):
    # This runs only when the lock is already known to be held. A parse error
    # must not turn that into a different, wrong report.
    path = tmp_path / "hfcache.lock"
    path.write_text(content, encoding="utf-8")

    assert read_holder(path) == {}
