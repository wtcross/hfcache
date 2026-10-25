"""Real finite observers retain ownership through parent-side pipe failures."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
from pathlib import Path

import pytest

from hfcache import host_peer as module


class ObserverError(Exception):
    """A parent-side refusal that cleanup must preserve unchanged."""


def observer_fixture(tmp_path, monkeypatch, *, size=module.MAX_OUTPUT, interrupt_cleanup=False):
    """Use a finite same-UID child; this does not model host credential proof."""
    completed = tmp_path / "completed"
    observer = tmp_path / "observer"
    observer.write_text(
        f"#!{sys.executable}\n"
        "import os,signal,sys,time\n"
        "signal.signal(signal.SIGALRM, lambda *_: os._exit(73))\n"
        "signal.alarm(3)\n"
        "sys.stdin.buffer.read()\n"
        + ("time.sleep(.05)\nos.kill(os.getppid(),signal.SIGUSR1)\n" if interrupt_cleanup else "")
        + f"body=b'x'*{size!r}\n"
        "while body:\n"
        "    body=body[os.write(1,body):]\n"
        f"with open({str(completed)!r},'w') as stream:\n"
        f"    stream.write({str(size)!r})\n"
        "signal.alarm(0)\n"
        "time.sleep(.03)\n"
    )
    observer.chmod(0o700)
    monkeypatch.setattr(module, "OBSERVER", str(observer))
    original_popen = subprocess.Popen
    children = []

    def forbid_signal(*_args, **_kwargs):
        pytest.fail("observer ownership must not depend on parent signaling")

    def same_uid_child(*args, **kwargs):
        assert kwargs.pop("user") == os.getuid()
        assert kwargs.pop("group") == os.getgid()
        assert kwargs.pop("extra_groups") == ()
        child = original_popen(*args, **kwargs)
        child.kill = forbid_signal
        child.terminate = forbid_signal
        child.send_signal = forbid_signal
        children.append(child)
        return child

    monkeypatch.setattr(module.subprocess, "Popen", same_uid_child)
    return completed, children


@pytest.mark.parametrize(
    "stage", ["construct", "register", "select", "read", "interrupt", "cleanup-interrupt"]
)
def test_parent_failure_drains_full_pipe_reaps_and_preserves_original_error(
    tmp_path, monkeypatch, stage
):
    completed, children = observer_fixture(
        tmp_path, monkeypatch, interrupt_cleanup=stage == "cleanup-interrupt"
    )
    failure = KeyboardInterrupt() if stage == "interrupt" else ObserverError(stage)
    selector_factory = module.selectors.DefaultSelector
    original_read = module.os.read

    class FailingSelector:
        def __init__(self):
            if stage == "construct":
                raise failure
            self.selector = selector_factory()

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            self.selector.close()

        def register(self, *args):
            if stage in {"register", "cleanup-interrupt"}:
                raise failure
            return self.selector.register(*args)

        def select(self, *args):
            if stage in {"select", "interrupt"}:
                raise failure
            return self.selector.select(*args)

    def read(descriptor, size):
        if stage == "read" and children:
            output = children[0].stdout
            assert output is not None
            if descriptor == output.fileno():
                raise failure
        return original_read(descriptor, size)

    monkeypatch.setattr(module.selectors, "DefaultSelector", FailingSelector)
    monkeypatch.setattr(module.os, "read", read)
    interruptions = []

    def interrupt(_signum, _frame):
        interruptions.append(True)
        raise KeyboardInterrupt

    previous = signal.signal(signal.SIGUSR1, interrupt)
    try:
        with pytest.raises(type(failure)) as caught:
            module._observe_as_account(
                {"remaining_seconds": 2}, os.getuid(), os.getgid(), profile="rootless"
            )
    finally:
        signal.signal(signal.SIGUSR1, previous)
    assert caught.value is failure
    assert len(interruptions) == int(stage == "cleanup-interrupt")
    assert len(children) == 1
    assert children[0].returncode == 0
    assert completed.read_text() == str(module.MAX_OUTPUT)
    assert not Path(f"/proc/{children[0].pid}").exists()


@pytest.mark.parametrize("operation", ["stdin-close", "stdout-read", "wait", "unusable-reader"])
def test_cleanup_interruption_or_unusable_reader_keeps_first_error_and_actual_reap(
    tmp_path, monkeypatch, operation
):
    completed, children = observer_fixture(tmp_path, monkeypatch)
    popen = module.subprocess.Popen
    failure = ObserverError("selector unavailable")
    calls = []

    def interrupt_once(original, *, on_call=1):
        def wrapped(*args, **kwargs):
            calls.append(True)
            if len(calls) == on_call:
                if operation == "unusable-reader":
                    message = "owned reader unavailable"
                    raise OSError(message)
                raise KeyboardInterrupt
            return original(*args, **kwargs)

        return wrapped

    def child_with_interrupted_cleanup(*args, **kwargs):
        child = popen(*args, **kwargs)
        assert child.stdin is not None
        assert child.stdout is not None
        if operation == "stdin-close":
            monkeypatch.setattr(child.stdin, "close", interrupt_once(child.stdin.close, on_call=2))
        elif operation in {"stdout-read", "unusable-reader"}:
            monkeypatch.setattr(child.stdout, "read", interrupt_once(child.stdout.read))
        else:
            monkeypatch.setattr(child, "wait", interrupt_once(child.wait))
        return child

    def refuse_selector():
        raise failure

    monkeypatch.setattr(module.subprocess, "Popen", child_with_interrupted_cleanup)
    monkeypatch.setattr(module.selectors, "DefaultSelector", refuse_selector)
    with pytest.raises(ObserverError) as caught:
        module._observe_as_account(
            {"remaining_seconds": 2}, os.getuid(), os.getgid(), profile="rootless"
        )
    assert caught.value is failure
    assert calls
    assert len(children) == 1
    assert not Path(f"/proc/{children[0].pid}").exists()
    if operation == "unusable-reader":
        assert children[0].returncode == 1
        assert not completed.exists()
    else:
        assert children[0].returncode == 0
        assert completed.read_text() == str(module.MAX_OUTPUT)


@pytest.mark.parametrize("overflow", [False, True])
def test_normal_observer_output_bound_still_drains_and_reaps(tmp_path, monkeypatch, overflow):
    size = module.MAX_OUTPUT + int(overflow)
    completed, children = observer_fixture(tmp_path, monkeypatch, size=size)
    if overflow:
        with pytest.raises(module.PeerError):
            module._observe_as_account(
                {"remaining_seconds": 2}, os.getuid(), os.getgid(), profile="rootless"
            )
    else:
        assert (
            module._observe_as_account(
                {"remaining_seconds": 2}, os.getuid(), os.getgid(), profile="rootless"
            )
            == b"x" * size
        )
    assert children[0].returncode == 0
    assert completed.read_text() == str(size)
    assert not Path(f"/proc/{children[0].pid}").exists()


@pytest.mark.parametrize("interruptions", [1, 2])
def test_drain_entry_interruptions_preserve_first_error_and_reap_full_finite_child(
    tmp_path, monkeypatch, interruptions
):
    size = 2 * 1024 * 1024
    completed, children = observer_fixture(tmp_path, monkeypatch, size=size)
    first = ObserverError("original observer refusal")
    drain = module._drain_observer
    calls = []

    def interrupted_entry(*args):
        calls.append(True)
        if len(calls) <= interruptions:
            raise KeyboardInterrupt
        return drain(*args)

    def refuse_selector():
        raise first

    monkeypatch.setattr(module, "_drain_observer", interrupted_entry)
    monkeypatch.setattr(module.selectors, "DefaultSelector", refuse_selector)
    with pytest.raises(ObserverError) as caught:
        module._observe_as_account(
            {"remaining_seconds": 2}, os.getuid(), os.getgid(), profile="rootless"
        )
    assert caught.value is first
    assert len(calls) == interruptions + 1
    assert len(children) == 1
    assert children[0].returncode == 0
    assert completed.read_text() == str(size)
    assert not Path(f"/proc/{children[0].pid}").exists()
