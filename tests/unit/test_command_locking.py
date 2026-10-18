"""Verification owns the common lock through evidence persistence (AD-17/INV-007)."""

import fcntl
import multiprocessing
import os
from pathlib import Path

import pytest

from hfcache import locking, storage, verification
from hfcache.archive import initialize_archive
from hfcache.config import ApplicationConfig, load_config
from hfcache.errors import ExitCode
from hfcache.identity import CommitSha, PublicationId
from hfcache.paths import ArchiveLayout
from hfcache.publication import read_verification_catalog
from hfcache.services import commands
from hfcache.services.context import ExecutionContext
from hfcache.storage import parse_mount_table
from tests.unit.test_verification import ARCHIVE_ID, DATASET, MODEL, SHA_A, SHA_B, nfs_line, publish
from tests.unit.test_verify_command import write_run_report


@pytest.fixture
def command_archive(tmp_path, monkeypatch):
    root = tmp_path / "archive"
    root.mkdir()
    mount_table = tmp_path / "mountinfo"
    mount_table.write_text(nfs_line(str(root)), encoding="utf-8")
    lock_directory = tmp_path / "run"
    monkeypatch.setattr(storage, "MOUNT_TABLE", mount_table)
    monkeypatch.setattr(locking, "LOCK_DIRECTORY", lock_directory)
    layout = ArchiveLayout(root)
    initialize_archive(layout, archive_id=ARCHIVE_ID, table=parse_mount_table(nfs_line(str(root))))
    config = ApplicationConfig.model_validate(
        {
            "schema_version": 1,
            "storage": {
                "archive_root": str(root),
                "archive_id": ARCHIVE_ID,
                "minimum_free_space_gib": 0,
                "minimum_free_space_percent": 0,
            },
            "verification": {"lock_wait_seconds": 10},
        }
    )
    return layout, config, mount_table, lock_directory


def _assert_lock_owned(path):
    """A fresh open description must be excluded even inside the owning process."""
    descriptor = os.open(path, os.O_RDWR)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        else:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
            pytest.fail("verification released the common archive lock before persistence ended")
    finally:
        os.close(descriptor)


@pytest.mark.parametrize("mode", ["new", "full", "revision"])
def test_every_nonestimate_mode_holds_lock_during_scope_hash_report_and_merge(
    command_archive, monkeypatch, mode
):
    layout, config, _, _ = command_archive
    published = publish(layout)
    _, run_id = write_run_report(
        layout, commit_sha=published.commit_sha, publication_id=published.publication_id
    )
    called = []

    def observe(module, name):
        original = getattr(module, name)

        def guarded_phase(*args, **kwargs):
            _assert_lock_owned(locking.lock_path())
            called.append(name)
            return original(*args, **kwargs)

        monkeypatch.setattr(module, name, guarded_phase)

    resolver = {"new": "resolve_run", "full": "resolve_archive", "revision": "require_retained"}
    for name in (resolver[mode], "verify_targets", "build_report", "persist_verification"):
        observe(commands, name)
    observe(verification, "verification_catalog")
    request = commands.VerificationRequest(
        new=mode == "new",
        full=mode == "full",
        revision=f"{MODEL.selector}@{SHA_A}" if mode == "revision" else None,
        run_id=run_id if mode == "new" else None,
    )

    result = commands.CommandServices(config, ExecutionContext.create()).verify(request)

    assert result.exit_code == ExitCode.SUCCESS
    assert called == [
        resolver[mode],
        "verify_targets",
        "build_report",
        "persist_verification",
        "verification_catalog",
    ]
    # Once the complete operation returns, a separate command may enter.
    with locking.exclusive_lock(locking.lock_path(), command="after verify", wait_seconds=0):
        pass


def test_estimate_never_takes_the_archive_lock_or_persists(command_archive, monkeypatch):
    _, config, _, _ = command_archive

    def forbidden(*args, **kwargs):
        pytest.fail("a verification estimate acquired the writer lock or persisted evidence")

    monkeypatch.setattr(locking, "exclusive_lock", forbidden)
    monkeypatch.setattr(commands, "persist_verification", forbidden)
    result = commands.CommandServices(config, ExecutionContext.create()).verify(
        commands.VerificationRequest(estimate=True)
    )

    assert result.exit_code == ExitCode.SUCCESS
    assert result.data["mode"] == "estimate"


@pytest.mark.parametrize("mode", ["new", "full", "revision"])
def test_every_persisting_mode_refuses_unproven_storage_before_resolving_scope(
    command_archive, monkeypatch, mode
):
    layout, config, _, _ = command_archive
    layout.sentinel.unlink()

    def forbidden(*args, **kwargs):
        pytest.fail("verification resolved content or wrote evidence before proving storage")

    for name in ("resolve_run", "resolve_archive", "require_retained", "persist_verification"):
        monkeypatch.setattr(commands, name, forbidden)
    request = commands.VerificationRequest(
        new=mode == "new",
        full=mode == "full",
        revision=f"{MODEL.selector}@{SHA_A}" if mode == "revision" else None,
    )

    result = commands.CommandServices(config, ExecutionContext.create()).verify(request)

    assert result.exit_code == ExitCode.SAFETY
    assert any(problem.code == "HFMNT005" for problem in result.errors)
    assert not tuple(layout.runs.glob("*.json"))


def _verify_in_process(paths, selector, pause_catalog, signals, output):
    """Spawned worker instruments the real service, lock and catalog merge."""
    config_path, mount_table, lock_directory = paths
    ready, release, attempted = signals
    try:
        storage.MOUNT_TABLE = Path(mount_table)
        locking.LOCK_DIRECTORY = Path(lock_directory)
        original_acquire = locking._acquire

        def announce_attempt(*args, **kwargs):
            attempted.set()
            return original_acquire(*args, **kwargs)

        locking._acquire = announce_attempt
        if pause_catalog:
            original_catalog = verification.verification_catalog

            def pause_after_merge(*args, **kwargs):
                catalog = original_catalog(*args, **kwargs)
                ready.set()
                if not release.wait(15):
                    message = "interleaving test did not release the first catalog merge"
                    raise TimeoutError(message)
                return catalog

            verification.verification_catalog = pause_after_merge
        result = commands.CommandServices(
            load_config(Path(config_path)), ExecutionContext.create()
        ).verify(commands.VerificationRequest(revision=selector))
        output.send(("result", result.exit_code))
    finally:
        output.close()


def test_multiprocess_interleaving_preserves_unrelated_failures_and_instance_state(
    command_archive, tmp_path, monkeypatch
):
    layout, config, mount_table, lock_directory = command_archive
    first = publish(layout, identity=MODEL, commit_sha=SHA_A)
    second = publish(layout, identity=DATASET, commit_sha=SHA_B)
    for identity, published in ((MODEL, first), (DATASET, second)):
        tree = layout.repository(identity).instance(
            CommitSha(published.commit_sha), PublicationId(published.publication_id)
        )
        (tree / "config.json").unlink()
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        f'schema_version = 1\n[storage]\narchive_root = "{layout.root}"\n'
        f'archive_id = "{config.storage.archive_id}"\nminimum_free_space_gib = 0\n'
        "minimum_free_space_percent = 0\n[verification]\nlock_wait_seconds = 10\n",
        encoding="utf-8",
    )
    # Pytest's importlib mode discovers tests without putting this repository
    # on sys.path; spawned interpreters must import this worker by its package.
    monkeypatch.syspath_prepend(str(Path(__file__).parents[2]))
    context = multiprocessing.get_context("spawn")
    first_ready, release_first = context.Event(), context.Event()
    first_attempt, second_attempt = context.Event(), context.Event()
    receive_first, send_first = context.Pipe(duplex=False)
    receive_second, send_second = context.Pipe(duplex=False)
    first_process = context.Process(
        target=_verify_in_process,
        args=(
            (str(config_path), str(mount_table), str(lock_directory)),
            f"{MODEL.selector}@{SHA_A}",
            True,
            (first_ready, release_first, first_attempt),
            send_first,
        ),
    )
    second_process = context.Process(
        target=_verify_in_process,
        args=(
            (str(config_path), str(mount_table), str(lock_directory)),
            f"{DATASET.selector}@{SHA_B}",
            False,
            (first_ready, release_first, second_attempt),
            send_second,
        ),
    )
    processes = []
    try:
        first_process.start()
        processes.append(first_process)
        assert first_ready.wait(10), "first verifier never reached its catalog merge"
        # This pause is after reading the old catalog and before publishing the
        # new one: releasing early would permit a lost read/merge/write update.
        _assert_lock_owned(locking.lock_path())
        second_process.start()
        processes.append(second_process)
        assert second_attempt.wait(10), "second verifier never attempted the common lock"
        _assert_lock_owned(locking.lock_path())
        release_first.set()
        for process in processes:
            process.join(15)
            assert not process.is_alive(), "verification process did not finish"
            assert process.exitcode == 0
        for receiver in (receive_first, receive_second):
            assert receiver.poll(1), "verification process returned no classified outcome"
            assert receiver.recv() == ("result", int(ExitCode.INTEGRITY))
    finally:
        release_first.set()
        for process in processes:
            if process.is_alive():
                process.terminate()
            process.join(5)
        for connection in (receive_first, send_first, receive_second, send_second):
            connection.close()

    catalog = read_verification_catalog(layout)
    assert catalog is not None
    assert {
        (item.repository_type, item.repository_id) for item in catalog.outstanding_failures
    } == {
        (MODEL.type, MODEL.id),
        (DATASET.type, DATASET.id),
    }
    states = {
        (repository.repository_type, repository.repository_id, revision.commit_sha): (
            revision.publication_id,
            revision.outcome,
        )
        for repository in catalog.repositories
        for revision in repository.revisions
    }
    assert states == {
        (MODEL.type, MODEL.id, SHA_A): (first.publication_id, "failed"),
        (DATASET.type, DATASET.id, SHA_B): (second.publication_id, "failed"),
    }
