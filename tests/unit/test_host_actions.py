"""Real owned filesystem/syscalls; protected-capture/SID and manager adapters only."""

import ast
import hashlib
import json
import os
import signal
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

from hfcache import host_actions as actions
from hfcache import host_policy
from hfcache import logging as logging_module
from hfcache.host_actions_models import (
    HostJournalPage,
    HostObserverStatus,
    ObserverStopOutcome,
    ScheduleChangeOutcome,
)
from tests.unit.test_host_authorization import status

ARCHIVE = "6ce912b6-141f-4bd2-a871-c19625c86aa9"


@pytest.fixture
def writer(tmp_path, monkeypatch):  # noqa: PLR0915 - one explicit owned protected-capture adapter
    etc = tmp_path / "etc"
    timer = tmp_path / "timer"
    etc.mkdir(mode=0o750)
    timer.mkdir(mode=0o755)
    for name, path in {
        "ROOT": etc / ".host-actions",
        "LOCK": etc / ".host-actions.lock",
        "PENDING": etc / ".host-actions.pending",
        "SCHEDULE_DIRECTORY": timer,
        "SCHEDULE": timer / "50-cockpit.conf",
        "BACKUPS": timer / ".hfcache-actions",
    }.items():
        monkeypatch.setattr(actions, name, path)
    actions.ROOT.mkdir(mode=0o700)
    actions.BACKUPS.mkdir(mode=0o700)
    actions.LOCK.touch(mode=0o600)
    monkeypatch.setattr(actions, "OWNER", os.getuid())
    monkeypatch.setattr(actions, "OWNER_GID", os.getgid())
    contexts = {}
    context_paths = {}

    def context(value):
        info = os.fstat(value) if isinstance(value, int) else value.lstat()
        identity = info.st_dev, info.st_ino
        prior = context_paths.get(identity)
        if prior is not None and (
            not prior.exists() or (prior.stat().st_dev, prior.stat().st_ino) != identity
        ):
            contexts.pop(identity, None)
        if identity not in contexts:
            path = Path(f"/proc/self/fd/{value}").readlink() if isinstance(value, int) else value
            kind = actions.STATE_TYPE
            if path in {actions.LOCK, actions.PENDING}:
                kind = actions.GUARD_TYPE
            elif path == timer:
                kind = actions.SCHEDULE_DIRECTORY_TYPE
            elif path == actions.SCHEDULE or path.name in {"staged.conf", "predecessor.conf"}:
                kind = actions.SCHEDULE_TYPE
            contexts[identity] = f"system_u:object_r:{kind}:s0"
            context_paths[identity] = path
        return contexts[identity]

    monkeypatch.setattr(actions, "_context", context)
    state = SimpleNamespace(
        active=False, calls=[], key=b"k" * 32, permissions={"schedule": True, "observer": True}
    )
    default = b"[Timer]\nOnCalendar=daily\nRandomizedDelaySec=1h\n"

    binding = status()["binding"] | {"archive_id": ARCHIVE}

    def snapshot():
        inspection = SimpleNamespace(
            key=state.key,
            deployment_body=b"deployment-one",
            policy_body=b"policy-one",
            capture=SimpleNamespace(local=lambda _p: None),
        )
        inspection.revision = lambda domain, *parts: host_policy._Inspection.revision(
            cast("host_policy._Inspection", inspection), domain, *parts
        )

        def schedule():
            managed = actions.SCHEDULE.read_bytes() if actions.SCHEDULE.exists() else None
            inspection.schedule_files = default, managed
            return {
                "revision": inspection.revision(
                    b"host-schedule-v1", default, b"0" if managed is None else b"1", managed or b""
                )
            }

        inspection.schedule = schedule
        schedule()
        return SimpleNamespace(
            _inspection=inspection,
            budget=host_policy.InspectionBudget(),
            archive_id=ARCHIVE,
            profile="native",
            selected_release=tmp_path / "selected-release",
            api_principal=(os.getuid(), os.getgid()),
            deployment_sha256=hashlib.sha256(b"deployment-one").hexdigest(),
            host_action_status=lambda: {
                "binding": binding,
                "permissions": dict(state.permissions),
                "permission_reasons": {
                    k: "granted" if v else "policy-denied" for k, v in state.permissions.items()
                },
            },
        )

    def show(unit, _budget):
        assert unit == "hfcache-sync.timer"
        return {"ActiveState": "active" if state.active else "inactive"}

    def confirm(captured, managed, *, action, timer_was_active=None):
        if action == "observer":
            return
        assert (actions.SCHEDULE.read_bytes() if actions.SCHEDULE.exists() else None) == managed
        expected = action == "resume" if action in {"pause", "resume"} else timer_was_active
        assert state.active == expected
        assert captured._inspection.key == state.key

    policy = SimpleNamespace(
        _json=host_policy._json,
        InspectionError=host_policy.InspectionError,
        revalidate=lambda _captured: None,
        require_host_actions=lambda _captured: None,
        observer_process_context=lambda _pid, _budget: actions.SYNC_OBSERVER_CONTEXT,
        _show=show,
        confirm_schedule=confirm,
    )

    def tool(argv, _budget, **kwargs):
        if argv[0] == "/usr/bin/systemd-analyze":
            if argv[1] == "calendar":
                return b"Normalized form: *-*-* 00:00:00\nNext elapse: tomorrow\n"
            return b"Human: 30min\n"
        assert argv[0:2] == ["/usr/bin/systemctl", "--system"]
        command = argv[2]
        assert command in {"daemon-reload", "restart", "stop", "start"}
        assert argv[3:] == ([] if command == "daemon-reload" else ["hfcache-sync.timer"])
        state.calls.append(command)
        if command == "stop":
            state.active = False
        if command in {"start", "restart"}:
            state.active = True
        return b""

    monkeypatch.setattr(actions, "_tool", tool)

    def request(action="replace", *, operation_id="a" * 32, revision=None):
        current = snapshot()._inspection.schedule()["revision"]
        body = {"action": action, "expected_revision": revision or current}
        if action == "replace":
            body.update(on_calendar="daily", randomized_delay_sec=None)
        return {"operation_id": operation_id, "request_digest": operation_id * 2, "request": body}

    return SimpleNamespace(
        policy=policy,
        snapshot=snapshot,
        state=state,
        request=request,
        root=tmp_path,
        context=context,
        apply=lambda body: actions.change_schedule(policy, snapshot(), body),
        observe=lambda body: actions.read_schedule_outcome(
            policy, snapshot(), {k: body[k] for k in ("operation_id", "request_digest")}
        ),
    )


def test_actual_replace_reset_and_active_only_restart_keep_predecessor_inode(writer):
    first = writer.request()
    outcome = writer.apply(first)
    assert outcome["state"] == "confirmed"
    assert not outcome["pending"]
    ScheduleChangeOutcome.model_validate(outcome)
    assert writer.state.calls == ["daemon-reload"]
    inode = actions.SCHEDULE.stat().st_ino
    original = actions.SCHEDULE.read_bytes()
    writer.state.active = True
    second = writer.request("reset", operation_id="b" * 32)
    observed = writer.apply(second)
    ScheduleChangeOutcome.model_validate(observed)
    assert writer.state.calls == ["daemon-reload", "daemon-reload", "restart"]
    retained = actions.BACKUPS / second["operation_id"] / "predecessor.conf"
    assert retained.stat().st_ino == inode
    assert retained.read_bytes() == original
    assert not actions.SCHEDULE.exists()
    before = list(writer.state.calls)
    assert writer.apply(second) == observed
    assert writer.observe(first)["state"] == "confirmed"
    assert writer.state.calls == before


@pytest.mark.parametrize(
    ("action", "initial", "final", "command"),
    [("pause", True, False, "stop"), ("resume", False, True, "start")],
)
def test_timer_setters_never_change_enablement_or_other_units(
    writer, action, initial, final, command
):
    writer.state.active = initial
    request = writer.request(action)
    outcome = writer.apply(request)
    ScheduleChangeOutcome.model_validate(outcome)
    assert writer.state.active == final
    assert writer.state.calls == [command]
    assert not actions.SCHEDULE.exists()


def test_stale_revision_has_durable_known_no_effect_and_no_replay(writer):
    request = writer.request(revision="f" * 64)
    result = writer.apply(request)
    assert result["state"] == "unchanged"
    assert not result["pending"]
    assert result["stored_revision"] != result["expected_revision"]
    ScheduleChangeOutcome.model_validate(result)
    assert not writer.state.calls
    assert not actions.SCHEDULE.exists()
    assert writer.observe(request) == result
    assert writer.apply(request) == result
    assert writer.apply(writer.request(operation_id="b" * 32))["state"] == "confirmed"


def _tree(root):
    return {
        str(p.relative_to(root)): (
            actions._identity(p.lstat()),
            p.read_bytes() if p.is_file() else None,
        )
        for p in sorted(root.rglob("*"))
    }


def test_missing_and_corrupt_history_reads_are_noncreating_and_unknown(writer):
    request = writer.request()
    before = _tree(writer.root)
    result = writer.observe(request)
    assert result["state"] == "unknown"
    assert not result["pending"]
    assert _tree(writer.root) == before
    writer.apply(request)
    record = actions.ROOT / request["operation_id"] / "record.json"
    record.write_bytes(b"{}")
    before = _tree(writer.root)
    assert writer.observe(request)["state"] == "unknown"
    assert _tree(writer.root) == before
    with pytest.raises(ValueError, match="protected host action refused"):
        writer.apply(writer.request(operation_id="b" * 32))
    assert _tree(writer.root) == before


@pytest.mark.parametrize("mutation", ["bytes", "extra", "missing"])
def test_authenticated_predecessor_history_refuses_changed_or_unknown_files(writer, mutation):
    writer.apply(writer.request(operation_id="c" * 32))
    writer.apply(writer.request(operation_id="d" * 32))
    path = actions.BACKUPS / ("d" * 32) / "predecessor.conf"
    if mutation == "bytes":
        path.write_bytes(b"[Timer]\nOnCalendar=hourly\n")
    elif mutation == "extra":
        path.with_name("unexplained").write_bytes(b"must be preserved")
    else:
        path.unlink()
    before, calls = _tree(writer.root), list(writer.state.calls)
    with pytest.raises(ValueError, match="protected host action refused"):
        writer.apply(writer.request())
    assert _tree(writer.root) == before
    assert writer.state.calls == calls


def test_original_private_directory_cannot_be_replaced_between_checks(writer):
    files = actions._Files(writer.policy, writer.snapshot())
    files.directory(actions.ROOT)
    actions.ROOT.rename(actions.ROOT.with_name("retained-original"))
    actions.ROOT.mkdir(mode=0o700)
    with pytest.raises(ValueError, match="protected host action refused"):
        files.directory(actions.ROOT)


def test_history_capacity_refuses_without_creating_pending_or_manager_effect(writer, monkeypatch):
    monkeypatch.setattr(actions, "MAX_RECORDS", 1)
    writer.apply(writer.request(operation_id="c" * 32))
    before, calls = _tree(writer.root), list(writer.state.calls)
    with pytest.raises(ValueError, match="protected host action refused"):
        writer.apply(writer.request())
    assert _tree(writer.root) == before
    assert writer.state.calls == calls


def test_authenticated_but_incoherent_outcome_is_preserved_and_not_trusted(writer):
    request = writer.request()
    writer.apply(request)
    path = actions.ROOT / request["operation_id"] / "record.json"
    encoded = json.loads(path.read_bytes())
    encoded["record"]["outcome"]["manager_state"] = "unknown"
    encoded["authentication"] = actions._seal(
        writer.state.key, encoded["record"], b"host-action-record-v1"
    )
    path.write_bytes(actions._encoded(encoded))
    before = _tree(writer.root)
    assert writer.observe(request)["state"] == "unknown"
    with pytest.raises(ValueError, match="protected host action refused"):
        writer.apply(writer.request(operation_id="b" * 32))
    assert _tree(writer.root) == before


@pytest.mark.parametrize("boundary", ["predecessor", "installed"])
def test_changed_rename_source_never_confirms_or_sends_manager_request(
    writer, monkeypatch, boundary
):
    writer.apply(writer.request(operation_id="c" * 32))
    request = writer.request()
    calls = list(writer.state.calls)
    retained = writer.root / "externally-retained-source"

    def cut(name):
        if name == boundary + ":before_rename":
            source = (
                actions.SCHEDULE
                if boundary == "predecessor"
                else actions.BACKUPS / request["operation_id"] / "staged.conf"
            )
            source.rename(retained)
            source.write_bytes(retained.read_bytes())
            source.chmod(0o644)

    monkeypatch.setattr(actions, "checkpoint", cut)
    with pytest.raises(ValueError, match="protected host action refused"):
        writer.apply(request)
    assert retained.is_file()
    assert writer.state.calls == calls
    assert actions.PENDING.exists()
    result = writer.observe(request)
    assert result["pending"]
    assert result["state"] == "effect_unconfirmed"


@pytest.mark.parametrize(
    "point",
    [
        "pending:after_directory_fsync",
        "directory:after_directory_fsync",
        "prepared:after_file_fsync",
        "predecessor:after_rename",
        "installed:after_rename",
        "manager:daemon-reload:before_send",
        "manager:daemon-reload:after_ack",
        "confirmed:after_file_fsync",
        "pending:before_unlink",
    ],
)
def test_real_durability_cuts_preserve_original_and_observe_without_replay(
    writer, monkeypatch, point
):
    writer.apply(writer.request(operation_id="d" * 32))
    original = actions.SCHEDULE.read_bytes()
    original_inode = actions.SCHEDULE.stat().st_ino
    request = writer.request()
    fired = []

    def fault(name):
        if name == point and not fired:
            fired.append(name)
            raise OSError(5, "owned durability cut")

    monkeypatch.setattr(actions, "checkpoint", fault)
    with pytest.raises(OSError, match="owned durability cut"):
        writer.apply(request)
    assert fired == [point]
    monkeypatch.setattr(actions, "checkpoint", lambda _name: None)
    before = _tree(writer.root)
    calls = list(writer.state.calls)
    result = writer.observe(request)
    assert result["pending"]
    assert result["state"] in {
        "unknown",
        "prepared",
        "effect_unconfirmed",
        "confirmed",
    }
    assert _tree(writer.root) == before
    assert any(
        p.is_file() and p.stat().st_ino == original_inode and p.read_bytes() == original
        for p in writer.root.rglob("*")
    )
    with pytest.raises(ValueError, match="protected host action refused"):
        writer.apply(writer.request(operation_id="b" * 32))
    assert writer.state.calls == calls
    assert _tree(writer.root) == before


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("on_calendar", "daily\n[Service]"),
        ("on_calendar", "\\x"),
        ("on_calendar", " " * 4),
        ("on_calendar", "a" * 4097),
        ("randomized_delay_sec", ""),
        ("randomized_delay_sec", "x" * 257),
    ],
)
def test_invalid_validation_never_invokes_tool(writer, monkeypatch, field, value):
    calls = []
    monkeypatch.setattr(actions, "_tool", lambda *args, **_kwargs: calls.append(args))
    body = {"on_calendar": "daily", "randomized_delay_sec": None, field: value}
    with pytest.raises(host_policy.InspectionError):
        actions.validate_schedule(writer.policy, writer.snapshot(), body)
    assert not calls


def test_real_systemd_validation_and_owned_command_overflow_drain(writer, monkeypatch):
    monkeypatch.undo()
    budget = host_policy.InspectionBudget()
    raw = actions._tool(
        ["/usr/bin/systemd-analyze", "calendar", "--iterations=1", "--", "daily"], budget
    )
    assert b"Normalized form:" in raw
    assert b"Next elapse:" in raw
    with pytest.raises(ValueError, match="protected host action refused"):
        actions._tool(
            [sys.executable, "-c", "print('x'*20000)"], host_policy.InspectionBudget(), maximum=16
        )
    with pytest.raises(TimeoutError):
        actions._tool(
            [sys.executable, "-c", "import time;time.sleep(10)"],
            host_policy.InspectionBudget(),
            seconds=0.1,
        )


def test_module_stays_stdlib_python312_and_journal_catalog_matches():
    ast.parse(Path(actions.__file__).read_text(), feature_version=(3, 12))
    assert frozenset(logging_module.EVENTS) == actions.JOURNAL_EVENTS
    assert actions.SYNC_OBSERVER_CONTEXT == host_policy.SYNC_OBSERVER_CONTEXT
    assert str(host_policy.SYNC_OBSERVER_DROP_IN) == actions.SYNC_OBSERVER_DROP_IN


def test_revoked_native_schedule_permission_is_durable_no_effect(writer):
    request = writer.request()
    writer.state.permissions["schedule"] = False
    result = writer.apply(request)
    ScheduleChangeOutcome.model_validate(result)
    assert result["state"] == "unchanged"
    assert not result["pending"]
    assert not writer.state.calls
    assert not actions.SCHEDULE.exists()
    assert writer.observe(request) == result


def test_actual_pidfd_stops_only_original_even_when_manager_replaces_invocation(
    writer, monkeypatch
):
    original = subprocess.Popen([sys.executable, "-c", "import time;time.sleep(30)"])
    replacement = subprocess.Popen([sys.executable, "-c", "import time;time.sleep(30)"])
    expected = {
        "boot_id": actions._boot(),
        "invocation_id": "d" * 32,
        "main_pid": original.pid,
        "start_ticks": actions._proc_start(original.pid),
    }
    manager = {
        "MainPID": str(original.pid),
        "InvocationID": expected["invocation_id"],
        "ActiveState": "activating",
        "SubState": "start",
    }
    calls = []

    def child(_policy, _snapshot, observed, descriptor, *, send):
        assert observed == expected
        assert actions._live(descriptor)
        calls.append(send)
        if send:
            manager.update(MainPID=str(replacement.pid), InvocationID="e" * 32)
            signal.pidfd_send_signal(descriptor, signal.SIGTERM)

    monkeypatch.setattr(actions, "_manager_observer", lambda _snapshot: dict(manager))
    monkeypatch.setattr(actions, "_child", child)
    request = {
        "operation_id": "e" * 32,
        "request_digest": "e" * 64,
        "request": {"expected": expected},
    }
    try:
        outcome = actions.stop_sync_observer(writer.policy, writer.snapshot(), request)
        ObserverStopOutcome.model_validate(outcome)
        assert outcome["state"] == "confirmed"
        assert outcome["expected"] == expected
        assert outcome["stop_state"] == "exit_confirmed"
        assert not outcome["pending"]
        assert original.wait(2) == -signal.SIGTERM
        assert replacement.poll() is None
        assert calls == [False, True]
        writer.state.permissions["observer"] = False
        assert actions.stop_sync_observer(writer.policy, writer.snapshot(), request) == outcome
        assert (
            actions.read_observer_outcome(
                writer.policy,
                writer.snapshot(),
                {k: request[k] for k in ("operation_id", "request_digest")},
            )
            == outcome
        )
        assert calls == [False, True]
    finally:
        for process in (original, replacement):
            if process.poll() is None:
                process.terminate()
            process.wait()


def test_stale_observer_binding_retains_known_no_signal_outcome(writer, monkeypatch):
    process = subprocess.Popen([sys.executable, "-c", "import time;time.sleep(30)"])
    expected = {
        "boot_id": actions._boot(),
        "invocation_id": "d" * 32,
        "main_pid": process.pid,
        "start_ticks": actions._proc_start(process.pid),
    }
    monkeypatch.setattr(
        actions,
        "_capture_observer",
        lambda _policy, _snapshot: (expected, os.pidfd_open(process.pid)),
    )
    signals = []
    monkeypatch.setattr(actions, "_child", lambda *_args, **kwargs: signals.append(kwargs))
    request = {
        "operation_id": "e" * 32,
        "request_digest": "e" * 64,
        "request": {"expected": expected | {"start_ticks": expected["start_ticks"] + 1}},
    }
    try:
        outcome = actions.stop_sync_observer(writer.policy, writer.snapshot(), request)
        ObserverStopOutcome.model_validate(outcome)
        assert outcome["state"] == "unchanged"
        assert outcome["stop_state"] == "not_sent"
        assert not signals
        assert process.poll() is None
        assert not actions.PENDING.exists()
    finally:
        process.terminate()
        process.wait()


def test_lost_original_signal_ack_retains_pending_and_never_resends(writer, monkeypatch):
    process = subprocess.Popen([sys.executable, "-c", "import time;time.sleep(30)"])
    expected = {
        "boot_id": actions._boot(),
        "invocation_id": "d" * 32,
        "main_pid": process.pid,
        "start_ticks": actions._proc_start(process.pid),
    }
    monkeypatch.setattr(
        actions,
        "_capture_observer",
        lambda _policy, _snapshot: (expected, os.pidfd_open(process.pid)),
    )
    monkeypatch.setattr(
        actions,
        "_manager_observer",
        lambda _snapshot: {
            "MainPID": str(process.pid),
            "InvocationID": expected["invocation_id"],
        },
    )
    signals = []

    def child(_policy, _snapshot, observed, descriptor, *, send):
        assert observed == expected
        assert send
        signals.append(descriptor)
        signal.pidfd_send_signal(descriptor, signal.SIGTERM)
        raise OSError(5, "owned signal acknowledgement loss")

    monkeypatch.setattr(actions, "_child", child)
    request = {
        "operation_id": "e" * 32,
        "request_digest": "e" * 64,
        "request": {"expected": expected},
    }
    try:
        with pytest.raises(OSError, match="owned signal acknowledgement loss"):
            actions.stop_sync_observer(writer.policy, writer.snapshot(), request)
        assert process.wait(2) == -signal.SIGTERM
        before = _tree(writer.root)
        query = {key: request[key] for key in ("operation_id", "request_digest")}
        outcome = actions.read_observer_outcome(writer.policy, writer.snapshot(), query)
        ObserverStopOutcome.model_validate(outcome)
        assert outcome["state"] == "effect_unconfirmed"
        assert outcome["stop_state"] == "unknown"
        assert outcome["pending"]
        assert actions.stop_sync_observer(writer.policy, writer.snapshot(), request) == outcome
        assert len(signals) == 1
        assert _tree(writer.root) == before
    finally:
        if process.poll() is None:
            process.terminate()
        process.wait()


def test_guarded_rootless_observer_read_never_uses_system_manager(writer, monkeypatch):
    captured = writer.snapshot()
    captured.profile = "rootless"
    original = captured.host_action_status()
    captured.host_action_status = lambda: (
        original
        | {
            "permissions": {"schedule": False, "observer": False},
            "permission_reasons": {"schedule": "profile-unproved", "observer": "profile-unproved"},
        }
    )
    monkeypatch.setattr(
        actions, "_manager_observer", lambda _: pytest.fail("rootless manager fallback")
    )
    value = actions.read_sync_observer(writer.policy, captured, {})
    HostObserverStatus.model_validate(value)
    assert value["reason"] == "profile-unproved"
    assert value["expected"] is None


def test_known_unsupported_sid_keeps_original_identity_without_stop_eligibility(
    writer, monkeypatch
):
    process = subprocess.Popen([sys.executable, "-c", "import time;time.sleep(30)"])
    sid = "system_u:system_r:init_t:s0"
    expected = {
        "boot_id": actions._boot(),
        "invocation_id": "d" * 32,
        "main_pid": process.pid,
        "start_ticks": actions._proc_start(process.pid),
    }
    monkeypatch.setattr(writer.policy, "observer_process_context", lambda _pid, _budget: sid)
    monkeypatch.setattr(
        actions,
        "_manager_observer",
        lambda _snapshot: {
            "MainPID": str(process.pid),
            "InvocationID": expected["invocation_id"],
            "ActiveState": "activating",
            "SubState": "start",
        },
    )
    bodies = []

    def child_tool(argv, _budget, **options):
        assert argv == [str(actions.HELPER), "--observer-stop-child"]
        body = json.loads(options["body"])
        assert body["expected"] == expected
        assert body["expected_context"] == sid
        assert body["signal"] is False
        assert options["pass_fds"] == (body["pidfd"],)
        assert actions._live(body["pidfd"])
        bodies.append(body)
        return json.dumps({"schema_version": 1, "expected": expected, "signalled": False}).encode()

    monkeypatch.setattr(actions, "_tool", child_tool)
    captured = writer.snapshot()
    status = captured.host_action_status()
    status["permissions"]["observer"] = False
    status["permission_reasons"]["observer"] = "profile-unproved"
    captured.host_action_status = lambda: status
    try:
        observed = actions.read_sync_observer(writer.policy, captured, {})
        HostObserverStatus.model_validate(observed)
        assert observed["state"] == "observed"
        assert observed["expected"] == expected
        assert observed["permissions"] == {"schedule": True, "observer": False}
        assert observed["permission_reasons"]["observer"] == "profile-unproved"
        request = {
            "operation_id": "f" * 32,
            "request_digest": "f" * 64,
            "request": {"expected": expected},
        }
        outcome = actions.stop_sync_observer(writer.policy, captured, request)
        assert outcome["state"] == "unchanged"
        assert outcome["stop_state"] == "not_sent"
        assert len(bodies) == 1
        descriptor = os.pidfd_open(process.pid)
        try:
            with pytest.raises(ValueError, match="protected host action refused"):
                actions._child(writer.policy, captured, expected, descriptor, send=True)
        finally:
            os.close(descriptor)
        assert len(bodies) == 1
        assert process.poll() is None
    finally:
        process.terminate()
        process.wait()


@pytest.mark.parametrize(
    ("dropins", "bound", "accepted"),
    [
        ("", False, True),
        (actions.SYNC_OBSERVER_DROP_IN, False, False),
        (actions.SYNC_OBSERVER_DROP_IN, True, True),
        ("/etc/unknown.conf", True, False),
        (actions.SYNC_OBSERVER_DROP_IN + " /etc/unknown.conf", True, False),
    ],
)
def test_manager_observer_accepts_only_absent_or_exact_indexed_context_dropin(
    monkeypatch, dropins, bound, accepted
):
    selected = Path("/opt/hfcache/releases/0.2.46")
    fields = {
        "Id": "hfcache-sync.service",
        "LoadState": "loaded",
        "ActiveState": "inactive",
        "SubState": "dead",
        "MainPID": "0",
        "InvocationID": "",
        "DropInPaths": dropins,
        "FragmentPath": str(selected / "packaging/systemd/hfcache-sync.service"),
        "User": "hfcache",
        "Group": "hfcache",
        "Type": "oneshot",
        "SELinuxContext": actions.SYNC_OBSERVER_CONTEXT if bound else "",
    }
    captured = SimpleNamespace(
        selected_release=selected,
        budget=host_policy.InspectionBudget(),
        deployment={"bindings": {actions.SYNC_OBSERVER_BINDING: "a" * 64} if bound else {}},
    )
    monkeypatch.setattr(
        actions,
        "_tool",
        lambda *_args, **_kwargs: (
            "\n".join(key + "=" + value for key, value in fields.items()) + "\n"
        ).encode(),
    )
    if accepted:
        assert actions._manager_observer(captured) == fields
    else:
        with pytest.raises(ValueError, match="protected host action refused"):
            actions._manager_observer(captured)


def test_unprivileged_signal_entry_refuses_before_any_read_or_signal(writer, monkeypatch):
    monkeypatch.setattr(actions.os, "getuid", lambda: 12345)
    with pytest.raises(ValueError, match="protected host action refused"):
        actions.observer_signal_child(writer.policy)


def _journal_line(index, *, message=None):
    return json.dumps(
        {
            "__CURSOR": f"owned-cursor-{index}",
            "__REALTIME_TIMESTAMP": "1793073082853000",
            "MESSAGE": message
            or "event=run.started level=info run_id=" + "a" * 32 + " secret=opaque-do-not-return",
        }
    ).encode()


def test_journal_closed_projection_and_cursor_does_not_skip_boundary(writer, monkeypatch):
    calls = []
    lines = [_journal_line(i) for i in range(4)]

    def tool(argv, budget, **kwargs):
        calls.append(argv)
        assert argv[:4] == ["/usr/bin/journalctl", "--system", "--no-pager", "--output=json"]
        assert "--unit=hfcache-sync.service" in argv
        return b"\n".join(lines[:3] if len(calls) == 1 else lines[1:])

    monkeypatch.setattr(actions, "_tool", tool)
    captured = writer.snapshot()
    page = actions.read_journal(
        writer.policy, captured, {"source": "sync-observer", "cursor": None, "limit": 2}
    )
    HostJournalPage.model_validate(page)
    assert len(page["entries"]) == 2
    assert page["truncated"]
    assert not page["gap"]
    assert all("secret" not in entry["message"] for entry in page["entries"])
    cursor, gap = actions._decode_cursor(
        writer.policy, captured, "sync-observer", page["next_cursor"]
    )
    assert cursor == "owned-cursor-1"
    assert not gap
    following = actions.read_journal(
        writer.policy,
        captured,
        {"source": "sync-observer", "cursor": page["next_cursor"], "limit": 2},
    )
    HostJournalPage.model_validate(following)
    assert "--cursor=owned-cursor-1" in calls[-1]
    assert len(following["entries"]) == 2
    assert not following["gap"]


def test_forged_cross_source_expired_and_vanished_cursors_are_explicit(writer, monkeypatch):
    captured = writer.snapshot()
    cursor = actions._cursor(captured, "sync-observer", "cursor-1")
    with pytest.raises(host_policy.InspectionError):
        actions._decode_cursor(writer.policy, captured, "verify-observer", cursor)
    with pytest.raises(host_policy.InspectionError):
        actions._decode_cursor(writer.policy, captured, "sync-observer", "not-authenticated")
    real_time = actions.time.time
    with monkeypatch.context() as patch:
        patch.setattr(actions.time, "time", lambda: real_time() + 301)
        assert actions._decode_cursor(writer.policy, captured, "sync-observer", cursor) == (
            None,
            True,
        )
    monkeypatch.setattr(
        actions,
        "_tool",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(ValueError("owned missing cursor")),
    )
    page = actions.read_journal(
        writer.policy, captured, {"source": "sync-observer", "cursor": cursor, "limit": 80}
    )
    HostJournalPage.model_validate(page)
    assert page["gap"]
    assert not page["entries"]


def test_journal_capacity_and_unrecognized_prose_never_expose_payload(writer, monkeypatch):
    calls = []
    monkeypatch.setattr(
        actions,
        "_tool",
        lambda *args, **_kwargs: (
            calls.append(args)
            or _journal_line(0, message="Authorization: Bearer SECRET exception argv=private")
        ),
    )
    assert actions.JOURNAL_CAPACITY.acquire(blocking=False)
    assert actions.JOURNAL_CAPACITY.acquire(blocking=False)
    try:
        with pytest.raises(host_policy.InspectionError):
            actions.read_journal(
                writer.policy,
                writer.snapshot(),
                {"source": "sync-observer", "cursor": None, "limit": 80},
            )
        assert not calls
    finally:
        actions.JOURNAL_CAPACITY.release()
        actions.JOURNAL_CAPACITY.release()
    page = actions.read_journal(
        writer.policy, writer.snapshot(), {"source": "sync-observer", "cursor": None, "limit": 80}
    )
    HostJournalPage.model_validate(page)
    assert not page["entries"]
    assert page["truncated"]
