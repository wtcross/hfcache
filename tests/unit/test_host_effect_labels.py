"""Optional receipt admission and actual bounded fixed-file metadata capture.

SIDs are an explicit owned adapter; these tests do not prove installed MAC rules.
"""

import copy
import json
import os
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from hfcache import host_policy as policy
from hfcache import host_selinux as labels


def need(value):
    if not value:
        message = "fixed host label proof refused"
        raise ValueError(message)


def roles(version=2):
    return {
        **policy.SELINUX_LABELS,
        **(labels.HOST_ACTION_LABELS if version == 2 else {}),
        "archive": "nfs_t",
    }


@pytest.mark.parametrize("version", [1, 2])
def test_receipt_version_is_explicit_and_preserves_the_old_closed_role_set(version):
    value = roles(version)
    assert labels.installation_labels(version, value, policy.SELINUX_LABELS, need) == value
    assert set(value) == {
        *policy.SELINUX_LABELS,
        *(labels.HOST_ACTION_LABELS if version == 2 else {}),
        "archive",
    }


def test_v2_observer_state_is_one_closed_optional_role_without_changing_schedule_labels():
    base = roles()
    selected = {**base, "observer_state": labels.OBSERVER_STATE_TYPE}
    assert labels.installation_labels(2, base, policy.SELINUX_LABELS, need) == base
    assert labels.installation_labels(2, selected, policy.SELINUX_LABELS, need) == selected
    for version, value in (
        (1, {**roles(1), "observer_state": labels.OBSERVER_STATE_TYPE}),
        (2, {**selected, "observer_context": "arbitrary"}),
        (2, {**base, "observer_state": "unconfined_service_t"}),
    ):
        with pytest.raises(ValueError, match="fixed host label proof refused"):
            labels.installation_labels(version, value, policy.SELINUX_LABELS, need)


@pytest.mark.parametrize("version", [True, False, 0, 3, "2", None])
def test_receipt_version_never_coerces_or_adopts_future_authority(version):
    with pytest.raises(ValueError, match="fixed host label proof refused"):
        labels.installation_labels(version, roles(), policy.SELINUX_LABELS, need)


@pytest.mark.parametrize("version", [1, 2])
@pytest.mark.parametrize("change", ["missing", "extra", "wrong_type", "archive", "mixed_version"])
def test_partial_or_broader_optional_roles_refuse_instead_of_granting(version, change):
    value = roles(version)
    if change == "missing":
        del value["configuration"]
    elif change == "extra":
        value["path"] = "/etc/systemd/system"
    elif change == "wrong_type":
        value["configuration"] = "unconfined_t"
    elif change == "archive":
        value["archive"] = "var_log_t"
    else:
        value = roles(1 if version == 2 else 2)
    with pytest.raises(ValueError, match="fixed host label proof refused"):
        labels.installation_labels(version, value, policy.SELINUX_LABELS, need)


@pytest.fixture
def native_labels(tmp_path, monkeypatch):
    schedule = tmp_path / "sync.timer.d"
    history = schedule / ".hfcache-actions"
    state = tmp_path / ".host-actions"
    selected = tmp_path / "release"
    unit = selected / "packaging/systemd/hfcache-sync.timer"
    history.mkdir(parents=True, mode=0o700)
    schedule.chmod(0o755)
    state.mkdir(mode=0o700)
    unit.parent.mkdir(parents=True)
    unit.write_bytes(b"[Timer]\nOnCalendar=daily\n")
    unit.chmod(0o644)
    monkeypatch.setattr(labels, "SCHEDULE_DIRECTORY", schedule)
    monkeypatch.setattr(labels, "SCHEDULE_HISTORY", history)
    monkeypatch.setattr(labels, "HOST_ACTION_STATE", state)
    monkeypatch.setattr(labels, "SCHEDULE", schedule / "50-cockpit.conf")
    monkeypatch.setattr(labels, "LEGACY_POLICY", tmp_path / "cockpit-policy.json")
    monkeypatch.setattr(labels, "OWNER", os.geteuid())
    monkeypatch.setattr(labels, "OWNER_GID", os.getegid())
    monkeypatch.setattr(policy, "OWNER", os.geteuid())
    monkeypatch.setattr(policy, "OWNER_GID", os.getegid())
    contexts = {
        schedule: labels.HOST_ACTION_LABELS["schedule_directory"],
        history: labels.HOST_ACTION_LABELS["host_action_state"],
        state: labels.HOST_ACTION_LABELS["host_action_state"],
        unit: labels.HOST_ACTION_LABELS["sync_timer_unit"],
        labels.SCHEDULE: labels.HOST_ACTION_LABELS["schedule_file"],
    }

    def sid(path, name, *, follow_symlinks):
        assert name == "security.selinux"
        assert follow_symlinks is False
        return f"system_u:object_r:{contexts[path]}:s0\0".encode()

    monkeypatch.setattr(os, "getxattr", sid)
    inspection = SimpleNamespace(
        deployment={"profile": "native"},
        selected=selected,
        capture=policy._Capture(policy.InspectionBudget()),
    )
    inspection.capture.mounts = [(Path("/"), "ext4", {"rw"}, {"rw"})]
    return inspection, contexts


@pytest.fixture
def observer_state(native_labels, monkeypatch):
    inspection, contexts = native_labels
    state = labels.HOST_ACTION_STATE.parent / "scheduled-sync"
    state.mkdir(mode=0o700)
    monkeypatch.setattr(labels, "SYNC_OBSERVER_STATE", state)
    monkeypatch.setattr(policy, "SYNC_OBSERVER_STATE", state)
    inspection.deployment["api_principal"] = {
        "host_uid": os.geteuid(),
        "host_gid": os.getegid(),
    }
    inspection.capture.observer_principal = (os.geteuid(), os.getegid())
    contexts[state] = labels.OBSERVER_STATE_TYPE
    receipt = {
        "schema_version": 2,
        "labels": {**roles(), "observer_state": labels.OBSERVER_STATE_TYPE},
    }
    return inspection, contexts, receipt, state


def test_observer_state_metadata_proof_never_reads_pending_and_survives_ordinary_entries(
    observer_state, monkeypatch
):
    inspection, _contexts, receipt, state = observer_state
    pending = state / "pending.json"
    pending.write_bytes(b"retained original recovery bytes; never a provisioning input\n")
    before = pending.read_bytes()
    original = os.open

    def no_payload(path, flags, *args, **kwargs):
        assert path not in (pending, pending.name)
        return original(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", no_payload)
    original_read = Path.read_bytes

    def no_body(path):
        assert path != pending
        return original_read(path)

    monkeypatch.setattr(Path, "read_bytes", no_body)
    labels.observer_state_labels(inspection, receipt, need)
    assert inspection.capture.labels[state][1] == labels.OBSERVER_STATE_TYPE
    # Atomic SDK pending publication changes directory timestamps, not its
    # original owner/mode/SID/inode. This never validates pending contents.
    (state / "another-owned-entry").write_bytes(b"ordinary bounded SDK activity\n")
    inspection.capture.revalidate()
    assert original_read(pending) == before


@pytest.mark.parametrize("change", ["v1", "missing_role", "wrong_sid", "mode", "owner", "link"])
def test_observer_state_refuses_missing_or_incompatible_provisioning(observer_state, change):
    inspection, contexts, receipt, state = observer_state
    if change == "v1":
        receipt["schema_version"] = 1
    elif change == "missing_role":
        del receipt["labels"]["observer_state"]
    elif change == "wrong_sid":
        contexts[state] = "var_lib_t"
    elif change == "mode":
        state.chmod(0o750)
    elif change == "owner":
        inspection.deployment["api_principal"]["host_uid"] += 1
    else:
        destination = state.with_name("retained-state")
        state.rename(destination)
        state.symlink_to(destination)
    with pytest.raises((ValueError, policy.InspectionError)):
        labels.observer_state_labels(inspection, receipt, need)


def test_observer_state_replacement_cannot_reuse_a_previous_proof(observer_state):
    inspection, _contexts, receipt, state = observer_state
    labels.observer_state_labels(inspection, receipt, need)
    state.rename(state.with_name("retained-state"))
    state.mkdir(mode=0o700)
    with pytest.raises(policy.InspectionError):
        inspection.capture.revalidate()


@pytest.mark.parametrize("managed", [False, True])
def test_native_labels_capture_only_fixed_existing_objects_without_creating_a_guard(
    native_labels, managed
):
    inspection, contexts = native_labels
    if managed:
        labels.SCHEDULE.write_bytes(b"[Timer]\nOnCalendar=weekly\n")
        labels.SCHEDULE.chmod(0o644)
    before = set(labels.SCHEDULE_DIRECTORY.iterdir())
    labels.host_action_labels(inspection, {"schema_version": 2, "labels": roles()}, need)
    assert set(inspection.capture.labels) == set(contexts) - (
        set() if managed else {labels.SCHEDULE}
    )
    assert inspection.capture.budget.files > len(inspection.capture.labels)
    assert set(labels.SCHEDULE_DIRECTORY.iterdir()) == before
    assert list(labels.HOST_ACTION_STATE.iterdir()) == []
    assert not (labels.HOST_ACTION_STATE.parent / ".host-actions.lock").exists()
    assert not (labels.HOST_ACTION_STATE.parent / ".host-actions.pending").exists()


def test_schedule_label_proof_does_not_require_optional_observer_state(native_labels, monkeypatch):
    inspection, _contexts = native_labels
    absent = labels.HOST_ACTION_STATE.parent / "unprovisioned-sdk-state"
    monkeypatch.setattr(labels, "SYNC_OBSERVER_STATE", absent)
    receipt = {
        "schema_version": 2,
        "labels": {**roles(), "observer_state": labels.OBSERVER_STATE_TYPE},
    }
    labels.host_action_labels(inspection, receipt, need)
    assert absent not in inspection.capture.labels
    assert not absent.exists()


@pytest.mark.parametrize(
    "change", ["rootless", "v1", "missing_role", "wrong_sid", "mode", "link", "hardlink"]
)
def test_unproven_effect_labels_refuse_before_native_effects(native_labels, change):
    inspection, contexts = native_labels
    receipt = {"schema_version": 2, "labels": copy.deepcopy(roles())}
    if change == "rootless":
        inspection.deployment["profile"] = "rootless"
    elif change == "v1":
        receipt["schema_version"] = 1
    elif change == "missing_role":
        del receipt["labels"]["sync_timer_unit"]
    elif change == "wrong_sid":
        contexts[labels.SCHEDULE_DIRECTORY] = "systemd_unit_file_t"
    elif change == "mode":
        labels.HOST_ACTION_STATE.chmod(0o750)
    else:
        other = labels.HOST_ACTION_STATE / "preserved"
        other.write_bytes(b"original\n")
        other.chmod(0o644)
        if change == "link":
            labels.SCHEDULE.symlink_to(other)
        else:
            os.link(other, labels.SCHEDULE)
    with pytest.raises((ValueError, policy.InspectionError)):
        labels.host_action_labels(inspection, receipt, need)


def legacy_policy() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "source_commit": "a" * 40,
        "index_sha256": "b" * 64,
        "permissions": {name: name == "configuration" for name in labels.LEGACY_ACTIONS},
    }


@pytest.mark.parametrize("mode", [None, 0o600, 0o640, 0o644])
def test_legacy_gate_captures_safe_absence_or_closed_disabled_policy_without_migration(
    native_labels, mode
):
    inspection, _ = native_labels
    if mode is not None:
        labels.LEGACY_POLICY.write_text(json.dumps(legacy_policy()))
        labels.LEGACY_POLICY.chmod(mode)
    labels.legacy_host_actions_disabled(inspection, need)
    if mode is None:
        assert labels.LEGACY_POLICY in inspection.capture.absent
        assert not labels.LEGACY_POLICY.exists()
    else:
        assert labels.LEGACY_POLICY in inspection.capture.files
        assert json.loads(labels.LEGACY_POLICY.read_bytes()) == legacy_policy()
        assert labels.LEGACY_POLICY.stat().st_mode & 0o777 == mode
    inspection.capture.revalidate()


@pytest.mark.parametrize(
    "change",
    [
        "schedule",
        "observer",
        "boolean_version",
        "extra",
        "missing",
        "commit",
        "index",
        "permissions_extra",
        "permission_nonbool",
        "duplicate",
        "oversize",
        "writable",
        "symlink",
        "hardlink",
        "fifo",
    ],
)
def test_legacy_gate_never_adopts_malformed_or_enabled_host_authority(native_labels, change):  # noqa: PLR0912 - independent closed legacy-policy adversary matrix
    inspection, _ = native_labels
    value = legacy_policy()
    if change in {"schedule", "observer"}:
        value["permissions"][change] = True
    elif change == "boolean_version":
        value["schema_version"] = True
    elif change == "extra":
        value["path"] = "/etc/systemd/system"
    elif change == "missing":
        del value["source_commit"]
    elif change == "commit":
        value["source_commit"] = "A" * 40
    elif change == "index":
        value["index_sha256"] = "unverified"
    elif change == "permissions_extra":
        value["permissions"]["execute"] = False
    elif change == "permission_nonbool":
        value["permissions"]["schedule"] = 0
    raw = json.dumps(value).encode()
    if change == "duplicate":
        raw = raw.replace(b'"schema_version": 1', b'"schema_version": 1, "schema_version": 1')
    elif change == "oversize":
        raw += b" " * labels.MAX_LEGACY_POLICY_BYTES
    labels.LEGACY_POLICY.write_bytes(raw)
    labels.LEGACY_POLICY.chmod(0o600)
    if change == "writable":
        labels.LEGACY_POLICY.chmod(0o620)
    elif change == "symlink":
        old = labels.LEGACY_POLICY.with_suffix(".original")
        labels.LEGACY_POLICY.rename(old)
        labels.LEGACY_POLICY.symlink_to(old)
    elif change == "hardlink":
        os.link(labels.LEGACY_POLICY, labels.LEGACY_POLICY.with_suffix(".alias"))
    elif change == "fifo":
        labels.LEGACY_POLICY.unlink()
        os.mkfifo(labels.LEGACY_POLICY)
    with pytest.raises((ValueError, OSError)):
        labels.legacy_host_actions_disabled(inspection, need)


@pytest.mark.parametrize("initially_present", [False, True])
def test_legacy_absence_appearance_and_changed_bytes_revoke_the_same_capture(
    native_labels, initially_present
):
    inspection, _ = native_labels
    if initially_present:
        labels.LEGACY_POLICY.write_text(json.dumps(legacy_policy()))
        labels.LEGACY_POLICY.chmod(0o600)
    labels.legacy_host_actions_disabled(inspection, need)
    value = legacy_policy()
    value["permissions"]["observer"] = True
    labels.LEGACY_POLICY.write_text(json.dumps(value))
    labels.LEGACY_POLICY.chmod(0o600)
    with pytest.raises(policy.InspectionError):
        inspection.capture.revalidate()


def test_legacy_policy_parent_symlink_refuses_without_following_it(
    native_labels, tmp_path, monkeypatch
):
    inspection, _ = native_labels
    target = tmp_path / "target"
    target.mkdir()
    parent = tmp_path / "redirect"
    parent.symlink_to(target, target_is_directory=True)
    monkeypatch.setattr(labels, "LEGACY_POLICY", parent / "cockpit-policy.json")
    with pytest.raises(NotADirectoryError):
        labels.legacy_host_actions_disabled(inspection, need)
