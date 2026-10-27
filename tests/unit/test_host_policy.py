"""ADR150: captured neutral authority, no archive access or mutation.

Temporary native and original-installer rootless trees exercise the reader's
actual filesystem and release checks. They are unit fixtures, not installed
fixed-prefix conformance evidence.
"""

import ast
import copy
import hashlib
import json
import os
import stat
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

import pytest

from hfcache import host_policy as policy
from hfcache import host_selinux
from hfcache.host_models import HostStatus
from tests.unit.test_container_release_installer import (
    deployment as deployment,  # noqa: PLC0414 - original indexed-stage fixture
)
from tests.unit.test_container_release_installer import staged

REPOSITORY = Path(__file__).parents[2]
ARCHIVE_ID = "e6a53ffd-c362-4aa4-bb6a-9cda7d5d021b"


def encoded(value):
    return json.dumps(value, sort_keys=True).encode()


def digest(body):
    return hashlib.sha256(body).hexdigest()


def write(path, body, mode=0o644):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    path.chmod(mode)


def file_record(path):
    return {
        "sha256": digest(path.read_bytes()),
        "bytes": path.stat().st_size,
        "mode": stat.S_IMODE(path.stat().st_mode),
    }


def common_sources(selected, profile):
    for name in (
        "helper_daemon",
        "helper_unit",
        "helper_policy_module",
        "helper_protocol_module",
        "helper_peer_module",
        "helper_configuration_module",
        "helper_actions_module",
        "helper_selinux_module",
        "helper_selinux_policy",
    ):
        relative = policy.binding_paths(profile)[name][1]
        write(selected / relative, ("# protected " + name + "\n").encode())


def selinux_receipt(selected, profile):
    """Explicitly model root provisioning; no temporary tree proves SELinux."""
    source = selected / policy.binding_paths(profile)["helper_selinux_policy"][1]
    return encoded(
        {
            "schema_version": 1,
            "module": {
                "name": "hfcache_host_helper",
                "version": 1,
                "priority": 400,
                "source_sha256": digest(source.read_bytes()),
                "loaded_sha256": "e" * 64,
            },
            "domain": policy.SELINUX_CONTEXT,
            "kernel_policy_sha256": "f" * 64,
            "labels": {**policy.SELINUX_LABELS, "archive": "hfcache_archive_t"},
        }
    )


def authority(profile, selected):
    files = {
        path.relative_to(selected).as_posix(): file_record(path)
        for path in selected.rglob("*")
        if path.is_file() and not path.is_symlink()
    }
    if profile == "native":
        evidence = {
            "package_root_relative": ".venv/lib/python3.14/site-packages/hfcache",
            "python_link_relative": ".venv/bin/python",
            "python_target_relative": "cpython/bin/python3.14",
            "python_target_sha256": digest(b"unit interpreter bytes\n"),
        }
    else:
        release = json.loads((selected / "container-release.json").read_bytes())
        evidence = {
            "artifact_index_sha256": digest((selected / "artifact-index.json").read_bytes()),
            "runtime_profile_sha256": digest((selected / "rendered/runtime.json").read_bytes()),
            "app_image_sha256": release["app_image"].removeprefix("sha256:"),
            "caddy_image_sha256": release["caddy_image"].removeprefix("sha256:"),
        }
    return {
        "schema_version": 1,
        "profile": profile,
        "release": {"version": "0.2.0", "selector_target": "releases/0.2.0"},
        "source": {"parent_commit": "c" * 40, "snapshot_sha256": "d" * 64, "dirty": True},
        "api_principal": {"host_uid": os.geteuid() or 981, "host_gid": os.getegid() or 981},
        "bindings": {
            name: files[relative]["sha256"]
            for name, (_host, relative) in policy.binding_paths(profile).items()
        },
        "authority_files": files,
        "profile_evidence": evidence,
        "selinux_installation_sha256": digest(selinux_receipt(selected, profile)),
    }


def configure(  # noqa: PLR0915 - one explicit protected profile adapter
    selected, profile, monkeypatch, tmp_path, *, deployment=None
):
    prefix = selected.parent.parent
    paths = policy.binding_paths(profile)
    if profile == "rootless":
        assert deployment is not None
        original = list(deployment.bindings.items())
        patched = {
            name: (original[i][0], original[i][1])
            for i, name in enumerate(policy.ROOTLESS_BINDINGS)
        }
        monkeypatch.setattr(policy, "ROOTLESS_BINDINGS", patched)
    else:
        patched = {
            name: (tmp_path / "installed" / host.relative_to("/"), relative)
            for name, (host, relative) in policy.NATIVE_BINDINGS.items()
        }
        monkeypatch.setattr(policy, "NATIVE_BINDINGS", patched)
    fixed_paths = policy.binding_paths

    def binding_paths(selected_profile, *, observer_context=False):
        return {
            name: (tmp_path / "common" / host.relative_to("/"), relative)
            if name.startswith("helper_")
            else (host, relative)
            for name, (host, relative) in fixed_paths(
                selected_profile, observer_context=observer_context
            ).items()
        }

    monkeypatch.setattr(policy, "binding_paths", binding_paths)
    index = authority(profile, selected)
    for name, (host, relative) in policy.binding_paths(profile).items():
        if profile == "rootless" and name in policy.ROOTLESS_BINDINGS:
            continue
        write(host, (selected / relative).read_bytes(), 0o755 if name == "helper_daemon" else 0o644)
    configuration = tmp_path / "etc/config.toml"
    write(
        configuration,
        (
            'schema_version = 1\n[storage]\narchive_root = "/srv/hfcache"\n'
            f'archive_id = "{ARCHIVE_ID}"\n'
            '# unit-secret-never-export\n[hub]\ncredential_name = "unit-hidden-source"\n'
        ).encode(),
        0o640,
    )
    if os.getegid() == 0:
        os.chown(configuration, os.geteuid(), index["api_principal"]["host_gid"])
    key = tmp_path / "etc/key"
    write(key, b"k" * 32, 0o600)
    policy_file = tmp_path / "etc/policy.json"
    deployment_file = tmp_path / "etc/deployment.json"
    selinux_installation = tmp_path / "etc/selinux.json"
    write(selinux_installation, selinux_receipt(selected, profile))
    mountinfo = tmp_path / "mountinfo"
    write(mountinfo, b"1 0 0:1 / / rw - ext4 /dev/local rw\n")
    lock = deployment.lock if deployment is not None else tmp_path / "run/hfcache.lock"
    if deployment is None:
        write(lock, b"never read this lock body", 0o600)
    locks = tmp_path / "locks"
    write(locks, b"")
    for name, value in {
        "OWNER": os.geteuid(),
        "OWNER_GID": os.getegid(),
        "PREFIX": prefix,
        "POLICY": policy_file,
        "DEPLOYMENT": deployment_file,
        "CONFIGURATION": configuration,
        "REVISION_KEY": key,
        "SELINUX_INSTALLATION": selinux_installation,
        "MOUNTINFO": mountinfo,
        "LOCK": lock,
        "LOCKS": locks,
        "SCHEDULE_DIRECTORY": tmp_path / "schedule",
        "SCHEDULE": tmp_path / "schedule/50-cockpit.conf",
        "SYNC_OBSERVER_DROP_IN": tmp_path / "observer-context/50-hfcache-observer.conf",
        "SYNC_OBSERVER_STATE": tmp_path / "var-lib/scheduled/sync",
    }.items():
        monkeypatch.setattr(policy, name, value)
    # Platform behavior is modeled only in these profile/unit fixtures. Dedicated
    # metadata tests and actual installed guests own SELinux acceptance.
    monkeypatch.setattr(policy, "_selinux_state", lambda budget, **_kwargs: budget.remaining())
    capture_label = policy._Capture.label
    monkeypatch.setattr(policy._Capture, "label", lambda _self, _path, _label: None)
    permissions = dict.fromkeys(policy.ACTIONS, True)
    units = {
        unit: {
            "Id": unit,
            "LoadState": "loaded",
            "ActiveState": "inactive",
            "SubState": "dead",
            "UnitFileState": "disabled",
            "MainPID": "0",
        }
        for unit in (*policy.UNITS, policy.GUARD)
    }
    units[policy.GUARD].update(LoadState="not-found", UnitFileState="not-found")
    calls = []

    def show(unit, budget, *, include_invocation=False, include_observer_context=False):
        budget.remaining()
        calls.append(unit)
        row = {
            key: value
            for key, value in units[unit].items()
            if key not in {"SELinuxContext", "DropInPaths"}
        }
        if include_observer_context:
            row.update({key: units[unit].get(key, "") for key in ("SELinuxContext", "DropInPaths")})
        return row | ({"InvocationID": "e" * 32} if include_invocation else {})

    monkeypatch.setattr(policy, "_show", show)
    state = SimpleNamespace(
        selected=selected,
        profile=profile,
        index=index,
        permissions=permissions,
        config=configuration,
        key=key,
        policy=policy_file,
        deployment=deployment_file,
        mountinfo=mountinfo,
        lock=lock,
        locks=locks,
        units=units,
        calls=calls,
        paths=paths,
        capture_label=capture_label,
    )
    publish(state)
    return state


def publish(host):
    write(host.deployment, encoded(host.index))
    write(
        host.policy,
        encoded(
            {
                "schema_version": 1,
                "deployment_sha256": digest(host.deployment.read_bytes()),
                "permissions": host.permissions,
            }
        ),
        0o600,
    )


@pytest.fixture
def native(tmp_path, monkeypatch):
    selected = tmp_path / "opt/releases/0.2.0"
    selected.mkdir(parents=True)
    (selected.parent.parent / "current").symlink_to("releases/0.2.0")
    for name, body in {
        "pyproject.toml": b'[project]\nname="hfcache"\nversion="0.2.0"\n',
        "uv.lock": b'version=1\n[[package]]\nname="hfcache"\nversion="0.2.0"\n',
        ".python-version": b"3.14.6\n",
        ".venv/pyvenv.cfg": b"unit fixture\n",
        ".venv/bin/hfcache": b"#!"
        + str(selected / ".venv/bin/python").encode()
        + b"\n# unit entrypoint\n",
        "src/hfcache/__init__.py": b"# source\n",
        "src/hfcache/cli.py": b"# source\n",
        ".venv/lib/python3.14/site-packages/hfcache/__init__.py": b"# installed\n",
        ".venv/lib/python3.14/site-packages/hfcache/__pycache__/__init__.cpython-314.pyc": (
            b"unit cache bytes\n"
        ),
    }.items():
        write(selected / name, body, 0o755 if name == ".venv/bin/hfcache" else 0o644)
    for relative in ("scripts/container-service.py", "scripts/release-profile.py"):
        write(selected / relative, (REPOSITORY / relative).read_bytes())
    target = selected.parent.parent / "python/cpython/bin/python3.14"
    write(target, b"unit interpreter bytes\n", 0o755)
    (selected / ".venv/bin/python").symlink_to(target)
    for _host, relative in policy.NATIVE_BINDINGS.values():
        body = (
            b"[Timer]\nOnCalendar=*-*-* 00:00:00\nRandomizedDelaySec=300\n"
            if relative.endswith("sync.timer")
            else b"# unit fixture\n"
        )
        write(selected / relative, body)
    common_sources(selected, "native")
    return configure(selected, "native", monkeypatch, tmp_path)


@pytest.fixture
def rootless(deployment, tmp_path, monkeypatch):
    common_sources(deployment.source, "rootless")
    for path in (deployment.source / "host-helper").iterdir():
        relative = path.relative_to(deployment.source).as_posix()
        deployment.release["files"][relative] = digest(path.read_bytes())
    selected = staged(deployment)
    (deployment.prefix / "current").unlink()
    (deployment.prefix / "current").symlink_to("releases/0.2.0")
    return configure(selected, "rootless", monkeypatch, tmp_path, deployment=deployment)


@pytest.mark.parametrize("fixture", ["native", "rootless"])
def test_actual_protected_trees_use_original_profile_checks_and_safe_status(fixture, request):
    host = request.getfixturevalue(fixture)
    snapshot = policy.inspect_authority()
    status = snapshot.status()
    HostStatus.model_validate(status)
    assert status["state"] == "supported"
    assert status["profile"] == fixture
    assert status["facts"]["guard"] == "absent"
    assert status["facts"]["archive_mount"] == "absent"
    assert snapshot.api_principal == tuple(host.index["api_principal"].values())
    assert status["binding"]["source_dirty"] is True
    assert set(host.calls) == {*policy.UNITS, policy.GUARD}
    assert snapshot.status() == status
    status["permissions"]["configuration"] = False
    assert snapshot.status()["permissions"]["configuration"] is True
    assert b"unit-secret-never-export" not in encoded(snapshot.status())
    assert "unit-secret-never-export" not in repr(snapshot)
    assert "kkkkkkkk" not in repr(snapshot)
    if fixture == "rootless":
        assert not snapshot.status()["permissions"]["schedule"]
        assert not snapshot.status()["permissions"]["observer"]
        assert snapshot.status()["facts"]["sync_schedule"]["reason"] == "profile-unproved"
    else:
        assert snapshot.status()["facts"]["sync_schedule"]["on_calendar"] == "*-*-* 00:00:00"


def test_dedicated_host_effect_grants_require_additional_captured_proof(native, monkeypatch):
    snapshot = policy.inspect_authority()
    legacy = snapshot.status()
    assert not legacy["permissions"]["schedule"]
    assert not legacy["permissions"]["observer"]
    assert legacy["permissions"]["configuration"]
    derived = snapshot.host_action_status()
    assert not derived["permissions"]["schedule"]
    assert not derived["permissions"]["observer"]
    assert derived["permission_reasons"]["schedule"] == "authority-unknown"
    assert snapshot.status() == legacy
    captures = []
    monkeypatch.setattr(policy, "require_host_actions", captures.append)
    assert snapshot.host_action_status()["permissions"]["schedule"]
    assert snapshot.status()["permissions"]["schedule"]
    assert captures == [snapshot, snapshot]


@pytest.mark.parametrize("running", [False, True])
def test_missing_observer_mac_keeps_effective_schedule_grant_and_original_state(
    native, monkeypatch, running
):
    if running:
        native.units["hfcache-sync.service"].update(
            ActiveState="activating", SubState="start", MainPID="1234"
        )
    snapshot = policy.inspect_authority()
    monkeypatch.setattr(policy, "require_host_actions", lambda _snapshot: None)
    value = snapshot.host_action_status()
    assert value["permissions"]["schedule"]
    assert not value["permissions"]["observer"]
    assert value["permission_reasons"]["observer"] == "profile-unproved"
    assert value["facts"]["units"]["hfcache-sync.service"]["active"] == (
        "activating" if running else "inactive"
    )
    if not running:
        public = snapshot.status()
        HostStatus.model_validate(public)
        assert public["permissions"]["schedule"]
        assert not public["permissions"]["observer"]


def _optional_observer(host):
    """Real indexed files/manager metadata; SID provisioning remains an owned adapter."""
    body = ("[Service]\nSELinuxContext=" + policy.SYNC_OBSERVER_CONTEXT + "\n").encode()
    write(host.selected / policy.SYNC_OBSERVER_RELATIVE, body)
    write(policy.SYNC_OBSERVER_DROP_IN, body)
    policy.SYNC_OBSERVER_DROP_IN.parent.chmod(0o755)
    host.index["authority_files"][policy.SYNC_OBSERVER_RELATIVE] = file_record(
        host.selected / policy.SYNC_OBSERVER_RELATIVE
    )
    host.index["bindings"][policy.SYNC_OBSERVER_BINDING] = digest(body)
    host.units["hfcache-sync.service"].update(
        SELinuxContext=policy.SYNC_OBSERVER_CONTEXT, DropInPaths=str(policy.SYNC_OBSERVER_DROP_IN)
    )
    publish(host)
    captures = []
    labels = SimpleNamespace(
        installation_labels=host_selinux.installation_labels,
        observer_state_labels=lambda inspection, _receipt, _need: captures.append(inspection),
    )
    return labels, captures


def test_optional_observer_binding_is_native_only_and_keeps_old_indexes_valid(native):
    old = copy.deepcopy(native.index)
    assert policy._deployment(encoded(old)) == old
    _optional_observer(native)
    assert policy._deployment(encoded(native.index)) == native.index
    forged = copy.deepcopy(native.index)
    forged["profile"] = "rootless"
    with pytest.raises(policy.InspectionError):
        policy._deployment(encoded(forged))
    forged = copy.deepcopy(old)
    forged["bindings"]["another_context"] = "f" * 64
    with pytest.raises(policy.InspectionError):
        policy._deployment(encoded(forged))


@pytest.mark.parametrize("process_context", ["init_t", "hfcache_sync_observer_t"])
def test_optional_observer_context_joins_actual_manager_and_process_before_grant(
    native, monkeypatch, process_context
):
    labels, captures = _optional_observer(native)
    native.units["hfcache-sync.service"]["MainPID"] = "1234"
    snapshot = policy.inspect_authority(host_labels=labels)
    monkeypatch.setattr(policy, "require_host_actions", lambda _snapshot: None)
    monkeypatch.setattr(
        policy,
        "observer_process_context",
        lambda _pid, _budget: "system_u:system_r:" + process_context + ":s0",
    )
    value = snapshot.host_action_status()
    assert value["permissions"]["schedule"]
    assert value["permissions"]["observer"] == (process_context == "hfcache_sync_observer_t")
    assert value["permission_reasons"]["observer"] == (
        "granted" if process_context == "hfcache_sync_observer_t" else "profile-unproved"
    )
    assert captures


@pytest.mark.parametrize("change", ["extra", "manager", "bytes"])
def test_optional_observer_capture_refuses_later_dropin_or_manager_drift(native, change):
    labels, _ = _optional_observer(native)
    snapshot = policy.inspect_authority(host_labels=labels)
    policy.require_sync_observer_context(snapshot)
    if change == "extra":
        write(policy.SYNC_OBSERVER_DROP_IN.parent / "99-unknown.conf", b"[Service]\n")
    elif change == "manager":
        native.units["hfcache-sync.service"]["SELinuxContext"] = "system_u:system_r:init_t:s0"
    else:
        policy.SYNC_OBSERVER_DROP_IN.write_bytes(b"[Service]\nSELinuxContext=-bad\n")
    with pytest.raises(policy.InspectionError):
        policy.revalidate(snapshot)


@pytest.mark.parametrize("name", ["50-hfcache-observer.conf", "99-unknown.conf"])
def test_schedule_reload_cannot_adopt_an_unindexed_sync_service_dropin(native, name):
    write(policy.SYNC_OBSERVER_DROP_IN.parent / name, b"[Service]\n")
    policy.SYNC_OBSERVER_DROP_IN.parent.chmod(0o755)
    snapshot = policy.inspect_authority()
    with pytest.raises(policy.InspectionError):
        snapshot._inspection.observer_dropins()
    assert (policy.SYNC_OBSERVER_DROP_IN.parent / name).read_bytes() == b"[Service]\n"


def test_absent_optional_context_parent_is_revalidated_without_creating_it(native):
    snapshot = policy.inspect_authority()
    snapshot._inspection.observer_dropins()
    assert not policy.SYNC_OBSERVER_DROP_IN.parent.exists()
    policy.SYNC_OBSERVER_DROP_IN.parent.mkdir(mode=0o755)
    with pytest.raises(policy.InspectionError):
        policy.revalidate(snapshot)


@pytest.mark.parametrize("optional", [False, True])
@pytest.mark.parametrize(
    "loaded",
    [
        "/run/systemd/system/hfcache-sync.service.d/override.conf",
        "/usr/lib/systemd/system/hfcache-sync.service.d/unknown.conf",
    ],
)
def test_common_host_action_proof_refuses_loaded_unknown_sync_dropin(native, optional, loaded):
    if optional:
        _optional_observer(native)
    labels = SimpleNamespace(
        installation_labels=host_selinux.installation_labels,
        host_action_labels=lambda *_args: None,
        observer_state_labels=host_selinux.observer_state_labels,
    )
    native.units["hfcache-sync.service"]["DropInPaths"] = (
        str(policy.SYNC_OBSERVER_DROP_IN) + " " + loaded if optional else loaded
    )
    snapshot = policy.inspect_authority(host_labels=labels)
    with pytest.raises(policy.InspectionError):
        policy.require_host_actions(snapshot)
    assert not snapshot.host_action_status()["permissions"]["schedule"]
    assert not snapshot.status()["permissions"]["schedule"]
    assert snapshot.status()["permissions"]["configuration"]


@pytest.mark.parametrize("optional", [False, True])
def test_common_schedule_proof_revalidates_loaded_dropins_without_observer_mac(native, optional):
    if optional:
        _optional_observer(native)
    labels = SimpleNamespace(
        installation_labels=host_selinux.installation_labels,
        host_action_labels=lambda *_args: None,
        observer_state_labels=host_selinux.observer_state_labels,
    )
    snapshot = policy.inspect_authority(host_labels=labels)
    policy.require_host_actions(snapshot)
    status = snapshot.host_action_status()
    assert status["permissions"]["schedule"]
    assert not status["permissions"]["observer"]
    assert status["permission_reasons"]["observer"] == "profile-unproved"
    policy.revalidate(snapshot)
    native.units["hfcache-sync.service"]["DropInPaths"] = (
        "/run/systemd/system/hfcache-sync.service.d/override.conf"
    )
    with pytest.raises(policy.InspectionError):
        policy.revalidate(snapshot)


@pytest.mark.parametrize(
    ("raw", "valid"),
    [
        (b"system_u:system_r:init_t:s0", True),
        (b"system_u:system_r:hfcache_sync_observer_t:s0\n", True),
        (b"unconfined_u:unconfined_r:unconfined_t:s0-s0:c0.c1023\0", True),
        (b"system_u:system_r:init_t:s0\n\0", False),
        (b"system_u:system_r:init_t:s0\0\0", False),
        (b"system_u:system_r:init_t:s0\nprivate", False),
        (b"x" * 4097, False),
    ],
)
def test_process_sid_reader_is_bounded_exact_and_does_not_infer_signal_authority(
    tmp_path, monkeypatch, raw, valid
):
    path = tmp_path / "owned-process-context"
    path.write_bytes(raw)
    original = os.open
    target = Path("/proc/1234/attr/current")

    def open_owned(name, flags):
        assert Path(name) == target
        return original(path, flags)

    with monkeypatch.context() as patch:
        patch.setattr(policy.os, "open", open_owned)
        if valid:
            assert (
                policy.observer_process_context(1234, policy.InspectionBudget())
                == raw.rstrip(b"\0\n").decode()
            )
        else:
            with pytest.raises(policy.InspectionError):
                policy.observer_process_context(1234, policy.InspectionBudget())


def test_starting_oneshot_is_truthful_only_in_dedicated_status(native):
    native.units["hfcache-sync.service"].update(ActiveState="activating", SubState="start")
    snapshot = policy.inspect_authority()
    dedicated = snapshot.host_action_status()
    assert dedicated["facts"]["units"]["hfcache-sync.service"]["active"] == "activating"
    public = snapshot.status()
    HostStatus.model_validate(public)
    assert public["state"] == "unavailable"
    assert public["reason"] == "facts-unavailable"


@pytest.mark.parametrize("foreign_drift", [False, True])
def test_confirm_schedule_rebases_only_owned_leaf_and_observer_state(native, foreign_drift):
    policy.SCHEDULE_DIRECTORY.mkdir(mode=0o755)
    write(policy.SCHEDULE, b"[Timer]\nOnCalendar=weekly\n")
    snapshot = policy.inspect_authority()
    original = policy.SCHEDULE.stat().st_ino
    retained = policy.SCHEDULE_DIRECTORY / "retained-original"
    policy.SCHEDULE.rename(retained)
    candidate = b"[Timer]\nOnCalendar=\nOnCalendar=daily\n"
    write(policy.SCHEDULE, candidate)
    # Preservation is real, but the private backup directory is separately
    # proven by the writer; this focused capture test keeps schedule entries closed.
    retained.rename(native.config.parent / "owned-schedule-predecessor")
    assert (native.config.parent / "owned-schedule-predecessor").stat().st_ino == original
    native.units["hfcache-sync.service"].update(ActiveState="activating", SubState="start")
    if foreign_drift:
        native.key.write_bytes(b"z" * 32)
        with pytest.raises(policy.InspectionError):
            policy.confirm_schedule(snapshot, candidate, action="replace", timer_was_active=False)
    else:
        policy.confirm_schedule(snapshot, candidate, action="replace", timer_was_active=False)
        # The captured generation itself was not widened or silently refreshed.
        with pytest.raises(policy.InspectionError):
            policy.revalidate(snapshot)


@pytest.mark.parametrize("fixture", ["native", "rootless"])
def test_shared_configuration_does_not_share_private_helper_authority_label(
    fixture, request, monkeypatch
):
    host = request.getfixturevalue(fixture)
    captured = []
    monkeypatch.setattr(
        policy._Capture,
        "label",
        lambda _self, path, label: captured.append((path, label)),
    )
    policy.inspect_authority()
    assert (host.config.parent, "hfcache_host_helper_configuration_dir_t") in captured
    assert (host.config, "hfcache_host_helper_application_conf_t") in captured
    assert (host.config, "hfcache_host_helper_conf_t") not in captured
    for private in (host.policy, host.deployment, host.key, policy.SELINUX_INSTALLATION):
        assert (private, "hfcache_host_helper_conf_t") in captured
        assert (private, "hfcache_host_helper_application_conf_t") not in captured


def test_config_read_is_editable_and_opaque_revision_from_same_capture(native):
    snapshot = policy.inspect_authority()
    before = snapshot.budget.files
    result = policy.read_config_base(snapshot)
    assert set(result) == {
        "schema_version",
        "archive_id",
        "base_revision",
        "editable",
        "editable_fields",
        "protected_fields",
    }
    assert result["schema_version"] == 1
    assert result["archive_id"] == ARCHIVE_ID
    assert result["base_revision"] == snapshot.base_revision
    assert result["editable_fields"] == list(policy.EDITABLE_FIELDS)
    assert "unit-hidden-source" not in json.dumps(result)
    assert len(result["base_revision"]) == 64
    assert result["base_revision"] != digest(native.config.read_bytes())
    assert snapshot.budget.files > before
    native.config.write_bytes(native.config.read_bytes() + b"\n# concurrent change\n")
    with pytest.raises(policy.InspectionError):
        policy.read_config_base(snapshot)


@pytest.mark.parametrize("fixture", ["native", "rootless"])
def test_explicit_policy_false_stays_false_when_guard_absent(fixture, request):
    host = request.getfixturevalue(fixture)
    host.permissions = dict.fromkeys(policy.ACTIONS, False)
    publish(host)
    assert not any(policy.inspect_authority().status()["permissions"].values())


def test_guard_held_is_positive_without_opening_lock_or_archive(native, monkeypatch):
    # Unit fixture owns this existing inode; never acquire or read the lock.
    uid, gid = native.index["api_principal"].values()
    if os.geteuid() == 0:
        os.chown(native.lock, uid, gid)
    info = native.lock.stat()
    write(
        native.locks,
        (
            f"1: FLOCK ADVISORY WRITE 1234 {os.major(info.st_dev):02x}:"
            f"{os.minor(info.st_dev):02x}:{info.st_ino} 0 EOF\n"
        ).encode(),
    )
    native.units[policy.GUARD].update(
        LoadState="loaded",
        ActiveState="active",
        SubState="running",
        UnitFileState="enabled",
        MainPID="1234",
    )
    monkeypatch.setattr(policy, "_process_start", lambda _pid, _budget: 999)

    def child(_budget):
        # Transport is stubbed here; the original indexed lock predicate and
        # metadata reads still execute in this ordinary same-account fixture.
        inspection = policy._Inspection(policy.InspectionBudget())
        inspection.load()
        assert (
            inspection.legacy["_inspection_guard"](
                inspection.capture.mounts, {"service_uid": uid, "service_gid": gid}
            )
            == "held"
        )
        return {
            "schema_version": 1,
            "deployment_sha256": digest(native.deployment.read_bytes()),
            "guard": "held",
            "unit": native.units[policy.GUARD] | {"InvocationID": "e" * 32},
            "start_ticks": 999,
            "lock": {
                "device": info.st_dev,
                "inode": info.st_ino,
                "uid": uid,
                "gid": gid,
                "mode": 0o600,
            },
            "work": {"files": 0, "bytes": 0},
        }

    monkeypatch.setattr(policy, "_guard_child", child)
    opened = []
    original = os.open

    def observed(path, flags, *args, **kwargs):
        opened.append(str(path))
        assert not flags & (os.O_CREAT | os.O_WRONLY | os.O_RDWR | os.O_TRUNC)
        assert str(path) != native.lock.name
        assert not str(path).startswith("/srv")
        return original(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", observed)
    status = policy.inspect_authority().status()
    assert status["state"] == "guarded"
    assert status["permissions"]["archive"] is False
    assert status["permission_reasons"]["archive"] == "guard-held"
    assert opened


@pytest.mark.parametrize(
    "change",
    ["policy", "deployment", "config", "key", "selector", "package", "unit", "mount", "guard"],
)
def test_captured_generation_rejects_each_concurrent_authority_change(native, change):
    snapshot = policy.inspect_authority()
    if change in {"policy", "deployment", "config", "key"}:
        path = getattr(native, change)
        path.write_bytes(path.read_bytes() + b" ")
    elif change == "selector":
        path = policy.PREFIX / "current"
        path.unlink()
        path.symlink_to("releases/0.1.0")
    elif change == "package":
        write(
            native.selected
            / native.index["profile_evidence"]["package_root_relative"]
            / "unindexed.pyc",
            b"extra",
        )
    elif change == "unit":
        native.units[policy.UNITS[0]]["ActiveState"] = "active"
    elif change == "mount":
        write(
            native.mountinfo,
            native.mountinfo.read_bytes() + b"2 1 0:2 / /srv/hfcache ro - nfs4 fixture ro\n",
        )
    else:
        native.units[policy.GUARD].update(LoadState="loaded", ActiveState="active", MainPID="1")
    with pytest.raises(policy.InspectionError):
        policy.revalidate(snapshot)


@pytest.mark.parametrize("name", list(policy.ROOTLESS_BINDINGS))
def test_all_nine_original_rootless_bindings_are_still_required(rootless, name):
    path = policy.binding_paths("rootless")[name][0]
    original = path.readlink()
    path.unlink()
    path.symlink_to(str(original) + ".changed")
    with pytest.raises(policy.InspectionError):
        policy.inspect_authority()
    assert path.readlink() == Path(str(original) + ".changed")
    assert rootless.calls == []


@pytest.mark.parametrize("fixture", ["native", "rootless"])
@pytest.mark.parametrize(
    "name",
    [
        "helper_daemon",
        "helper_unit",
        "helper_policy_module",
        "helper_protocol_module",
        "helper_peer_module",
        "helper_configuration_module",
        "helper_actions_module",
        "helper_selinux_module",
    ],
)
def test_each_trusted_bootstrap_copy_is_bound(fixture, name, request):
    host = request.getfixturevalue(fixture)
    path = policy.binding_paths(fixture)[name][0]
    path.write_bytes(path.read_bytes() + b"# changed\n")
    with pytest.raises(policy.InspectionError):
        policy.inspect_authority()
    assert host.calls == []


@pytest.mark.parametrize(
    "kind", ["symlink", "hardlink", "writable", "wrong-mode", "oversize", "fifo"]
)
def test_unsafe_policy_fails_before_any_manager_read(native, kind):
    path = native.policy
    if kind == "symlink":
        other = path.with_suffix(".original")
        path.rename(other)
        path.symlink_to(other)
    elif kind == "hardlink":
        os.link(path, path.with_suffix(".second"))
    elif kind == "writable":
        path.chmod(0o666)
    elif kind == "wrong-mode":
        path.chmod(0o644)
    elif kind == "oversize":
        path.write_bytes(b"x" * 4097)
    else:
        path.unlink()
        os.mkfifo(path)
    with pytest.raises(policy.InspectionError, match="protected host inspection refused") as result:
        policy.inspect_authority()
    assert result.value.reason == "policy-invalid"
    assert not native.calls


@pytest.mark.parametrize(
    ("kind", "reason"),
    [("policy", "policy-missing"), ("key", "key-missing"), ("config", "config-unavailable")],
)
def test_missing_inputs_are_never_created_or_partially_granted(native, kind, reason):
    path = getattr(native, kind)
    path.unlink()
    with pytest.raises(policy.InspectionError) as result:
        policy.inspect_authority()
    assert result.value.reason == reason
    assert not path.exists()
    assert not native.calls


@pytest.mark.parametrize(
    "kind",
    [
        "symlink-parent",
        "writable-parent",
        "changed-inode",
        "same-size-content",
        "extra-cache",
        "cache-symlink",
    ],
)
def test_native_package_requires_actual_ordinary_complete_inventory(native, kind):
    package = native.selected / native.index["profile_evidence"]["package_root_relative"]
    leaf = package / "__init__.py"
    if kind == "symlink-parent":
        moved = package.with_name("other")
        package.rename(moved)
        package.symlink_to(moved)
    elif kind == "writable-parent":
        package.chmod(0o777)
    elif kind == "changed-inode":
        body = leaf.read_bytes()
        leaf.unlink()
        write(leaf, body + b"changed")
    elif kind == "same-size-content":
        leaf.write_bytes(b"x" * leaf.stat().st_size)
    elif kind == "extra-cache":
        write(package / "__pycache__/extra.pyc", b"extra")
    else:
        (package / "extra.pyc").symlink_to(leaf)
    with pytest.raises(policy.InspectionError):
        policy.inspect_authority()


@pytest.mark.parametrize(
    "kind",
    [
        "interpreter-bytes",
        "interpreter-alias",
        "entrypoint",
        "classifier",
        "unknown-json",
        "mixed-layout",
    ],
)
def test_native_layout_and_actual_runtime_provenance_are_both_required(native, kind):
    if kind == "interpreter-bytes":
        target = (
            policy.PREFIX / "python" / native.index["profile_evidence"]["python_target_relative"]
        )
        target.write_bytes(b"changed executable bytes")
    elif kind == "interpreter-alias":
        link = native.selected / ".venv/bin/python"
        target = link.readlink()
        link.unlink()
        link.symlink_to(str(target.parent / "." / target.name) + ".alias")
    elif kind == "entrypoint":
        path = native.selected / ".venv/bin/hfcache"
        write(path, b"#!/usr/bin/python\n", 0o755)
        native.index["authority_files"][".venv/bin/hfcache"] = file_record(path)
        publish(native)
    elif kind == "classifier":
        (native.selected / "scripts/release-profile.py").write_bytes(
            b"raise Exception('do not execute')\n"
        )
    elif kind == "unknown-json":
        write(native.selected / "unknown.json", b"{}")
    else:
        (native.selected / "rendered").mkdir()
    with pytest.raises(policy.InspectionError):
        policy.inspect_authority()


@pytest.mark.parametrize("body", [b'{"x":1,"x":2}', b'{"x":NaN}', b"[]"])
def test_closed_json_rejects_duplicates_nonfinite_and_wrong_root(body):
    with pytest.raises(policy.InspectionError):
        policy._json(body)


@pytest.mark.parametrize(
    "mutation",
    ["schema-bool", "permission-int", "permission-extra", "digest-uppercase", "extra-root"],
)
def test_policy_is_exact_six_boolean_index_bound_shape(native, mutation):
    value = json.loads(native.policy.read_bytes())
    if mutation == "schema-bool":
        value["schema_version"] = True
    elif mutation == "permission-int":
        value["permissions"]["archive"] = 1
    elif mutation == "permission-extra":
        value["permissions"]["extra"] = False
    elif mutation == "digest-uppercase":
        value["deployment_sha256"] = "A" * 64
    else:
        value["extra"] = None
    with pytest.raises(policy.InspectionError):
        policy._policy(encoded(value))


@pytest.mark.parametrize("uid", [1, 983, 100000, (1 << 32) - 2])
def test_principal_uses_actual_positive_host_ids_not_one_fixture_uid(native, uid):
    value = copy.deepcopy(native.index)
    value["api_principal"] = {"host_uid": uid, "host_gid": uid}
    assert policy._deployment(encoded(value))["api_principal"]["host_uid"] == uid


@pytest.mark.parametrize("uid", [0, -1, 65534, True, "983", (1 << 32) - 1])
def test_principal_rejects_root_unmapped_wrong_type_or_invalid_kernel_id(native, uid):
    value = copy.deepcopy(native.index)
    value["api_principal"]["host_uid"] = uid
    with pytest.raises(policy.InspectionError):
        policy._deployment(encoded(value))


@pytest.mark.parametrize(
    "mutation",
    [
        "unknown",
        "wrong-branch",
        "parent-selector",
        "absolute",
        "traversal",
        "alias",
        "writable",
        "bool-size",
        "missing-binding",
        "different-binding",
        "fake-commit",
        "dirty-int",
    ],
)
def test_deployment_is_closed_and_protects_all_authority_records(native, mutation):
    value = copy.deepcopy(native.index)
    name = next(iter(value["authority_files"]))
    if mutation == "unknown":
        value["extra"] = True
    elif mutation == "wrong-branch":
        value["profile"] = "rootless"
    elif mutation == "parent-selector":
        value["release"]["selector_target"] = "releases/../0.2.0"
    elif mutation in {"absolute", "traversal", "alias"}:
        new = {"absolute": "/etc/shadow", "traversal": "../shadow", "alias": "a//b"}[mutation]
        value["authority_files"][new] = value["authority_files"].pop(name)
    elif mutation == "writable":
        value["authority_files"][name]["mode"] = 0o666
    elif mutation == "bool-size":
        value["authority_files"][name]["bytes"] = True
    elif mutation == "missing-binding":
        value["bindings"].pop("helper_daemon")
    elif mutation == "different-binding":
        value["bindings"]["helper_daemon"] = "f" * 64
    elif mutation == "fake-commit":
        value["source"]["parent_commit"] = "dirty"
    else:
        value["source"]["dirty"] = 1
    with pytest.raises(policy.InspectionError):
        policy._deployment(encoded(value))


def test_larger_work_budget_does_not_expand_authority_table_cardinality(native):
    value = copy.deepcopy(native.index)
    files = value["authority_files"]
    entry = next(iter(files.values()))
    for number in range(1024 - len(files)):
        files[f"extra/leaf-{number}"] = copy.deepcopy(entry)
    assert len(files) == 1024
    policy._deployment(encoded(value))
    files["extra/overflow"] = copy.deepcopy(entry)
    with pytest.raises(policy.InspectionError):
        policy._deployment(encoded(value))


def test_default_and_managed_schedule_preserve_safe_original_source_semantics(native):
    before = policy.inspect_authority().status()["facts"]["sync_schedule"]
    write(
        policy.SCHEDULE,
        b"[Timer]\nOnCalendar=\nOnCalendar=Mon *-*-* 01:00:00\n"
        b"OnCalendar=Tue *-*-* 02:00:00\nRandomizedDelaySec=15min\n",
    )
    after = policy.inspect_authority().status()["facts"]["sync_schedule"]
    assert after["source"] == "managed"
    assert after["on_calendar"] == "Tue *-*-* 02:00:00"
    assert after["randomized_delay_sec"] == "15min"
    assert after["revision"] != before["revision"]


@pytest.mark.parametrize(
    "body",
    [
        b"[Service]\nExecStart=bad\n",
        b"[Timer]\nUnknown=1\n",
        b"[Timer]\nOnCalendar=bad\\value\n",
        b"[Timer]\nOnCalendar=\n",
    ],
)
def test_unsupported_managed_schedule_is_whole_status_unknown(native, body):
    write(policy.SCHEDULE, body)
    with pytest.raises(policy.InspectionError) as result:
        policy.inspect_authority()
    assert result.value.reason == "facts-unavailable"


def test_unknown_schedule_dropin_and_postcapture_extra_are_refused(native):
    snapshot = policy.inspect_authority()
    write(policy.SCHEDULE_DIRECTORY / "other.conf", b"[Timer]\nOnCalendar=daily\n")
    with pytest.raises(policy.InspectionError):
        policy.revalidate(snapshot)
    with pytest.raises(policy.InspectionError):
        policy.inspect_authority()


@pytest.mark.parametrize(
    "kind", ["unknown-guard", "guard-no-lock", "unknown-unit", "nfs-rw-rootless"]
)
def test_unavailable_facts_fail_whole_inspection_without_partial_permission(rootless, kind):
    if kind == "unknown-guard":
        rootless.units[policy.GUARD].update(ActiveState="activating", MainPID="0")
    elif kind == "guard-no-lock":
        rootless.units[policy.GUARD].update(
            LoadState="loaded", ActiveState="active", SubState="running", MainPID="1234"
        )
    elif kind == "unknown-unit":

        def fail(_unit, _budget):
            message = "unit-secret must not leak"
            raise ValueError(message)

        # This reader normally enforces the closed manager fields itself.
        policy_show = policy._show
        rootless.units[policy.UNITS[0]]["ActiveState"] = "unknown"
        rootless.calls.clear()
        original = rootless.units[policy.UNITS[0]]
        assert original["ActiveState"] == "unknown"
        # Monkeypatching the query result bypasses its parser; fail at the seam.
        rootless.units[policy.UNITS[0]] = original
        with pytest.MonkeyPatch.context() as patch:
            patch.setattr(
                policy,
                "_show",
                lambda unit, budget: (
                    fail(unit, budget) if unit == policy.UNITS[0] else policy_show(unit, budget)
                ),
            )
            with pytest.raises(policy.InspectionError):
                policy.inspect_authority()
        return
    else:
        write(
            rootless.mountinfo,
            rootless.mountinfo.read_bytes() + b"2 1 0:2 / /srv/hfcache rw - nfs4 fixture rw\n",
        )
    with pytest.raises(policy.InspectionError):
        policy.inspect_authority()


def test_budget_never_resets_and_caps_all_reads_rechecks_and_commands(native, monkeypatch):
    clock = [time.monotonic_ns()]
    monkeypatch.setattr(policy.time, "monotonic_ns", lambda: clock[0])
    budget = policy.InspectionBudget(deadline_ns=clock[0] + 1_000_000_000)
    snapshot = policy.inspect_authority(budget=budget)
    assert snapshot.budget is budget
    used = budget.files, budget.bytes
    policy.revalidate(snapshot)
    assert budget.files > used[0]
    assert budget.bytes > used[1]
    assert budget.remaining() <= 1
    clock[0] += 1_000_000_001
    with pytest.raises(TimeoutError):
        policy.read_config_base(snapshot)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"maximum_files": 4097},
        {"maximum_bytes": 64 * 1024 * 1024 + 1},
        {"maximum_files": True},
        {"files": 1},
        {"bytes": -1},
    ],
)
def test_budget_cannot_expand_hard_limits_or_start_with_hidden_usage(kwargs):
    with pytest.raises(policy.InspectionError):
        policy.InspectionBudget(**kwargs)


def test_budget_counts_actual_bytes_and_files_and_refuses_negative_accounting():
    budget = policy.InspectionBudget(maximum_files=1, maximum_bytes=3)
    budget.consume(files=1, size=3)
    with pytest.raises(policy.InspectionError):
        budget.consume(size=1)
    with pytest.raises(policy.InspectionError):
        budget.consume(files=-1)
    with pytest.raises(policy.InspectionError):
        policy.InspectionBudget(maximum_files=1).consume(files=2)


def test_unbounded_requested_deadline_is_clamped(monkeypatch):
    monkeypatch.setattr(policy.time, "monotonic_ns", lambda: 100)
    budget = policy.InspectionBudget(deadline_ns=10**30)
    assert budget.deadline_ns == 100 + policy.MAX_INSPECTION_NS


def test_bootstrap_source_is_stdlib_only_python312_and_has_no_mutation_commands():
    path = REPOSITORY / "src/hfcache/host_policy.py"
    tree = ast.parse(path.read_bytes(), feature_version=(3, 12))
    imported = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
    assert not any(name and name.startswith("hfcache") for name in imported)
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in {"write_bytes", "write_text", "mkdir", "unlink", "flock"}
        for node in ast.walk(tree)
    )


def test_fixed_manager_query_uses_remaining_deadline_and_reaps_its_exact_child(
    monkeypatch,
):
    actual = subprocess.Popen
    owned = []
    argv_seen = []

    def child(argv, **kwargs):
        argv_seen.append(argv)
        command = [os.sys.executable, "-c", "import time; time.sleep(10)"]
        process = actual(command, **kwargs)
        owned.append(process)
        return process

    monkeypatch.setattr(policy.subprocess, "Popen", child)
    budget = policy.InspectionBudget(deadline_ns=time.monotonic_ns() + 100_000_000)
    with pytest.raises(TimeoutError):
        policy._show(policy.UNITS[0], budget)
    assert owned
    assert owned[0].poll() is not None
    assert argv_seen[0][:3] == ["/usr/bin/systemctl", "--system", "show"]
    assert not set(argv_seen[0]) & {"start", "stop", "restart", "enable", "disable"}


def test_failed_read_closes_descriptors_and_preserves_unsafe_leaf(native):
    before = set(os.listdir("/proc/self/fd"))  # noqa: PTH208 - exact descriptor accounting
    native.policy.chmod(0o666)
    for _ in range(3):
        with pytest.raises(policy.InspectionError):
            policy.inspect_authority()
    assert set(os.listdir("/proc/self/fd")) == before  # noqa: PTH208
    assert stat.S_IMODE(native.policy.stat().st_mode) == 0o666


@pytest.mark.parametrize(
    "kind", ["changed-stage", "extra-stage", "changed-runtime", "changed-image", "changed-index"]
)
def test_original_rootless_stage_runtime_image_and_tree_checks_are_not_layout_claims(
    rootless, kind
):
    if kind == "changed-stage":
        path = rootless.selected / "packaging/containers/server.toml.in"
        path.write_bytes(path.read_bytes() + b"# changed\n")
    elif kind == "extra-stage":
        write(rootless.selected / "unexplained", b"extra")
    elif kind == "changed-runtime":
        path = rootless.selected / "rendered/runtime.json"
        path.write_bytes(path.read_bytes() + b"\n")
    elif kind == "changed-index":
        rootless.index["profile_evidence"]["artifact_index_sha256"] = "a" * 64
        publish(rootless)
    else:
        rootless.index["profile_evidence"]["app_image_sha256"] = "b" * 64
        publish(rootless)
    with pytest.raises(policy.InspectionError):
        policy.inspect_authority()


def test_native_binding_can_be_exact_reviewed_selector_link(native):
    host, relative = policy.binding_paths("native")["api_service"]
    host.unlink()
    host.symlink_to(policy.PREFIX / "current" / relative)
    assert policy.inspect_authority().profile == "native"
    host.unlink()
    host.symlink_to(native.selected / relative)
    with pytest.raises(policy.InspectionError):
        policy.inspect_authority()


@pytest.mark.parametrize("kind", ["replacement", "same-inode-write", "parent-alias"])
def test_actual_file_read_brackets_inode_content_and_parent_binding(native, monkeypatch, kind):
    capture = policy._Capture(policy.InspectionBudget())
    capture.mounts = capture.mount_rows()
    path = native.policy
    read = os.read
    changed = False

    def concurrent(descriptor, maximum):
        nonlocal changed
        body = read(descriptor, maximum)
        if not changed and body and body.startswith(b'{"deployment_sha256"'):
            changed = True
            if kind == "replacement":
                path.unlink()
                write(path, body, 0o600)
            elif kind == "same-inode-write":
                path.write_bytes(b"x" * len(body))
            else:
                original = path.parent
                moved = original.with_name("moved")
                original.rename(moved)
                original.symlink_to(moved)
        return body

    monkeypatch.setattr(os, "read", concurrent)
    if kind == "parent-alias":
        # FD-relative leaf read remains the captured inode. The immediate
        # parent recheck must refuse its changed public path before any grant.
        capture.read(path, mode=0o600)
        with pytest.raises(policy.InspectionError):
            capture.revalidate()
    else:
        with pytest.raises(policy.InspectionError):
            capture.read(path, mode=0o600)
    assert changed


def test_tree_enumeration_is_bounded_before_materializing_unknown_entries(native, monkeypatch):
    capture = policy._Capture(policy.InspectionBudget())
    capture.mounts = capture.mount_rows()
    root = native.selected / native.index["profile_evidence"]["package_root_relative"]
    monkeypatch.setattr(policy, "MAX_FILES", 1)
    with pytest.raises(policy.InspectionError) as result:
        capture.tree(root)
    assert result.value.reason == "facts-unavailable"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("archive_root", "/different"),
        ("archive_id", "E6A53FFD-C362-4AA4-BB6A-9CDA7D5D021B"),
        ("schema_version", True),
    ],
)
def test_config_base_identity_is_fixed_and_strict_without_full_app_import(native, field, value):
    if field == "schema_version":
        body = native.config.read_text().replace("schema_version = 1", "schema_version = true")
    else:
        original = "/srv/hfcache" if field == "archive_root" else ARCHIVE_ID
        body = native.config.read_text().replace(original, value)
    native.config.write_text(body)
    with pytest.raises(policy.InspectionError) as result:
        policy.inspect_authority()
    assert result.value.reason == "config-unavailable"


@pytest.mark.parametrize("body", [b"short", b"x" * 33])
def test_revision_key_must_be_exactly_32_protected_bytes(native, body):
    native.key.write_bytes(body)
    with pytest.raises(policy.InspectionError) as result:
        policy.inspect_authority()
    assert result.value.reason == "key-invalid"


@pytest.mark.parametrize("bad", [".", "a/./b", "a/../b", "a//b", "/a", "a\x00b"])
def test_authority_leaf_names_have_one_exact_relative_spelling(bad):
    with pytest.raises(policy.InspectionError):
        policy._relative(bad)


def manager_output(unit):
    return (
        f"Id={unit}\nLoadState=loaded\nActiveState=inactive\n"
        "SubState=dead\nUnitFileState=disabled\n"
        + ("" if unit.endswith(".timer") else "MainPID=0\n")
    ).encode()


@pytest.mark.parametrize("unit", policy.UNITS)
def test_actual_fixed_query_parser_accepts_service_and_timer_shapes(unit, monkeypatch):
    actual = subprocess.Popen
    body = manager_output(unit)

    def child(_argv, **kwargs):
        return actual(
            [
                os.sys.executable,
                "-c",
                "import os,sys;os.write(1,bytes.fromhex(sys.argv[1]))",
                body.hex(),
            ],
            **kwargs,
        )

    monkeypatch.setattr(policy.subprocess, "Popen", child)
    value = policy._show(unit, policy.InspectionBudget())
    assert value["MainPID"] == "0"
    assert value["Id"] == unit


@pytest.mark.parametrize(
    "kind", ["duplicate", "wrong-unit", "unknown", "missing", "bad-pid", "oversize", "failure"]
)
def test_actual_manager_parser_fails_closed_for_bad_accounting(kind, monkeypatch):
    actual = subprocess.Popen
    unit = policy.UNITS[0]
    body = manager_output(unit)
    if kind == "duplicate":
        body += b"MainPID=0\n"
    elif kind == "wrong-unit":
        body = body.replace(unit.encode(), b"other.service")
    elif kind == "unknown":
        body = body.replace(b"ActiveState=inactive", b"ActiveState=unrecognized")
    elif kind == "missing":
        body = body.replace(b"MainPID=0\n", b"")
    elif kind == "bad-pid":
        body = body.replace(b"MainPID=0", b"MainPID=-1")
    elif kind == "oversize":
        body = b"x" * 16385
    returncode = 1 if kind == "failure" else 0

    def child(_argv, **kwargs):
        return actual(
            [
                os.sys.executable,
                "-c",
                "import os,sys;os.write(1,bytes.fromhex(sys.argv[1]));sys.exit(int(sys.argv[2]))",
                body.hex(),
                str(returncode),
            ],
            **kwargs,
        )

    monkeypatch.setattr(policy.subprocess, "Popen", child)
    with pytest.raises(policy.InspectionError):
        policy._show(unit, policy.InspectionBudget())


@pytest.mark.parametrize("fixture", ["native", "rootless"])
def test_enumeration_adapters_are_per_inspection_and_never_change_shared_modules(fixture, request):
    request.getfixturevalue(fixture)
    original_walk, original_iterdir = os.walk, Path.iterdir
    with ThreadPoolExecutor(max_workers=8) as pool:
        snapshots = list(pool.map(lambda _: policy.inspect_authority(), range(8)))
    assert len({id(snapshot.budget) for snapshot in snapshots}) == 8
    assert all(snapshot.profile == fixture for snapshot in snapshots)
    assert os.walk is original_walk
    assert Path.iterdir is original_iterdir


def test_directory_snapshot_rejects_a_real_concurrent_membership_change(native, monkeypatch):
    capture = policy._Capture(policy.InspectionBudget())
    capture.mounts = capture.mount_rows()
    root = native.selected / native.index["profile_evidence"]["package_root_relative"]
    original = os.scandir

    class ConcurrentEntries:
        def __init__(self, path):
            self.iterator = original(path)
            self.changed = False

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            self.iterator.close()

        def __iter__(self):
            return self

        def __next__(self):
            entry = next(self.iterator)
            if not self.changed:
                self.changed = True
                write(root / "concurrent.pyc", b"new member")
            return entry

    monkeypatch.setattr(os, "scandir", ConcurrentEntries)
    with pytest.raises(policy.InspectionError):
        capture.entries(root)


def test_shared_deadline_consumers_can_use_15_seconds_but_commands_default_to_5(monkeypatch):
    monkeypatch.setattr(policy.time, "monotonic_ns", lambda: 100)
    budget = policy.InspectionBudget()
    assert budget.remaining(15.0) == 15.0
    assert budget.remaining() == 5.0
    with pytest.raises(policy.InspectionError):
        budget.remaining(15.001)


def test_actual_pinned_interpreter_may_exceed_source_leaf_limit_within_shared_budget(native):
    # CPython3.14's real installed executable is about32MiB. Its separately
    # pinned ordinary bytes use the64MiB aggregate, not the16MiB source limit.
    target = policy.PREFIX / "python" / native.index["profile_evidence"]["python_target_relative"]
    body = b"x" * (policy.MAX_AUTHORITY_BYTES + 1)
    target.write_bytes(body)
    native.index["profile_evidence"]["python_target_sha256"] = digest(body)
    publish(native)
    snapshot = policy.inspect_authority()
    assert snapshot.profile == "native"
    assert snapshot.budget.bytes > policy.MAX_AUTHORITY_BYTES
    assert snapshot.budget.bytes <= policy.MAX_BYTES
    before = snapshot.budget.bytes
    policy.revalidate(snapshot)
    # Exact captured executable metadata is rechecked; no unbudgeted reread.
    assert snapshot.budget.bytes - before < policy.MAX_AUTHORITY_BYTES


def configuration_label_capture(native, monkeypatch):
    """Use the real config label/metadata reader with an explicit unit SID adapter."""
    context = "system_u:object_r:" + policy.SELINUX_LABELS["application_config"] + ":s0"
    monkeypatch.setattr(policy.os, "getxattr", lambda *_args, **_kwargs: context.encode())
    monkeypatch.setattr(
        policy._Capture,
        "label",
        lambda capture, path, kind: (
            native.capture_label(capture, path, kind) if path == policy.CONFIGURATION else None
        ),
    )
    return context


def replace_configuration(host):
    candidate = host.config.read_bytes() + b"\n# intentional replacement\n"
    incoming = host.config.with_name("replacement.toml")
    write(incoming, candidate, 0o640)
    if os.getegid() == 0:
        os.chown(incoming, os.geteuid(), host.index["api_principal"]["host_gid"])
    incoming.replace(host.config)
    return candidate, policy._identity(host.config.lstat())


def test_installed_configuration_rechecks_real_capture_without_second_runtime_load(
    native, monkeypatch
):
    context = configuration_label_capture(native, monkeypatch)
    target = policy.PREFIX / "python" / native.index["profile_evidence"]["python_target_relative"]
    # One real executable fits the original aggregate; two reads alone exceed it.
    body = b"x" * (policy.MAX_BYTES // 2 + 1)
    target.write_bytes(body)
    native.index["profile_evidence"]["python_target_sha256"] = digest(body)
    publish(native)
    snapshot = policy.inspect_authority()
    capture = snapshot._inspection.capture
    original = {
        name: getattr(capture, name).copy()
        for name in ("parents", "files", "links", "absent", "labels", "mounts")
    }
    original_body = snapshot._inspection.config_body
    candidate, identity = replace_configuration(native)
    before_files, before_bytes = snapshot.budget.files, snapshot.budget.bytes
    reads = []
    actual_read = policy._Capture.read

    def read(capture, path, **kwargs):
        reads.append(path)
        return actual_read(capture, path, **kwargs)

    monkeypatch.setattr(policy._Capture, "read", read)
    policy.confirm_configuration(snapshot, candidate, identity, context)
    assert target not in reads
    assert native.key in reads
    assert native.policy in reads
    assert snapshot.budget.files > before_files
    assert before_bytes < snapshot.budget.bytes <= policy.MAX_BYTES
    assert snapshot._inspection.config_body == original_body
    assert all(getattr(capture, name) == value for name, value in original.items())
    # The pre-effect snapshot still refuses its replaced original config leaf.
    with pytest.raises(policy.InspectionError):
        policy.revalidate(snapshot)


@pytest.mark.parametrize(
    "mutation", ["key", "policy", "deployment", "package", "unit", "mount", "config", "context"]
)
def test_configuration_confirmation_preserves_original_other_authority_checks(
    native, monkeypatch, mutation
):
    context = configuration_label_capture(native, monkeypatch)
    snapshot = policy.inspect_authority()
    candidate, identity = replace_configuration(native)
    if mutation in {"key", "policy", "deployment"}:
        path = getattr(native, mutation)
        path.write_bytes(path.read_bytes() + b"drift")
    elif mutation == "package":
        path = native.selected / native.index["profile_evidence"]["package_root_relative"]
        write(path / "unexpected.py", b"# drift\n")
    elif mutation == "unit":
        native.units[policy.UNITS[0]]["ActiveState"] = "active"
    elif mutation == "mount":
        native.mountinfo.write_bytes(b"1 0 0:1 / / ro - ext4 /dev/local ro\n")
    elif mutation == "config":
        # Even identical bytes/SID at a different inode must not replace the
        # writer's exact observed installed descriptor identity.
        incoming = native.config.with_name("unexpected-replacement.toml")
        write(incoming, candidate, 0o640)
        if os.getegid() == 0:
            os.chown(incoming, os.geteuid(), native.index["api_principal"]["host_gid"])
        incoming.replace(native.config)
    else:
        context = context.replace("system_u", "other_u")
    with pytest.raises(policy.InspectionError):
        policy.confirm_configuration(snapshot, candidate, identity, context)


def native_uv_aliases(native, *, minor_selector=True):
    """Original uv0.11.32 raw aliases, backed by actual ordinary fixture bytes."""
    directory = policy.PREFIX / "python" / f"cpython-3.14.6-linux-{os.uname().machine}-gnu"
    target = directory / "bin/python3.14"
    write(target, b"unit interpreter bytes\n", 0o755)
    selector = directory.with_name(f"cpython-3.14-linux-{os.uname().machine}-gnu")
    selector.symlink_to(str(directory))
    primary = native.selected / ".venv/bin/python"
    primary.unlink()
    primary.symlink_to(selector / "bin/python3.14" if minor_selector else target)
    for name in ("python3", "python3.14"):
        (primary.parent / name).symlink_to("python")
    entry = primary.parent / "hfcache"
    write(entry, b"#!" + str(primary.with_name("python3")).encode() + b"\n# fixture\n", 0o755)
    native.index["authority_files"][".venv/bin/hfcache"] = file_record(entry)
    pin = native.selected / ".python-version"
    write(pin, b"3.14\n")
    native.index["authority_files"][".python-version"] = file_record(pin)
    native.index["profile_evidence"]["python_target_relative"] = target.relative_to(
        policy.PREFIX / "python"
    ).as_posix()
    publish(native)
    return selector, target


@pytest.mark.parametrize("minor_selector", [True, False])
def test_original_uv_aliases_bind_canonical_interpreter_and_entry(native, minor_selector):
    selector, _target = native_uv_aliases(native, minor_selector=minor_selector)
    snapshot = policy.inspect_authority()
    policy.revalidate(snapshot)
    if minor_selector:
        selector.unlink()
        selector.symlink_to(selector.parent / "cpython-3.14.7-linux-x86_64-gnu")
    else:
        alias = native.selected / ".venv/bin/python3"
        alias.unlink()
        alias.symlink_to("python3.14")
    with pytest.raises(policy.InspectionError):
        policy.revalidate(snapshot)


@pytest.mark.parametrize(
    "change", ["relative-selector", "foreign-selector", "extra-chain", "alias", "unverified-entry"]
)
def test_native_fixed_alias_chain_refuses_substitutions(native, change):
    selector, target = native_uv_aliases(native)
    if change in {"relative-selector", "foreign-selector", "extra-chain"}:
        selector.unlink()
        destination = target.parent.parent.name if change == "relative-selector" else "/tmp/foreign"
        if change == "extra-chain":
            other = selector.with_name("other")
            other.symlink_to(target.parent.parent)
            destination = str(other)
        selector.symlink_to(destination)
    elif change == "alias":
        alias = native.selected / ".venv/bin/python3"
        alias.unlink()
        alias.symlink_to(str(target))
    else:
        entry = native.selected / ".venv/bin/hfcache"
        write(entry, b"#!" + str(native.selected / ".venv/bin/other").encode() + b"\n", 0o755)
        native.index["authority_files"][".venv/bin/hfcache"] = file_record(entry)
        publish(native)
    with pytest.raises((policy.InspectionError, OSError)):
        policy.inspect_authority()


def test_absent_fixed_python_alias_cannot_appear_after_capture(native):
    snapshot = policy.inspect_authority()
    (native.selected / ".venv/bin/python3").symlink_to("python")
    with pytest.raises(policy.InspectionError):
        policy.revalidate(snapshot)


def test_config_read_requires_its_independent_permission_and_not_other_categories(native):
    native.permissions = dict.fromkeys(policy.ACTIONS, False)
    publish(native)
    denied = policy.inspect_authority()
    with pytest.raises(policy.InspectionError) as result:
        policy.read_config_base(denied)
    assert result.value.reason == "operation-denied"
    native.permissions["configuration"] = True
    publish(native)
    admitted = policy.inspect_authority()
    assert policy.read_config_base(admitted)["archive_id"] == ARCHIVE_ID
    assert admitted.status()["permissions"] == dict.fromkeys(policy.ACTIONS, False) | {
        "configuration": True
    }


def test_config_read_cannot_use_a_grant_after_policy_revocation(native):
    snapshot = policy.inspect_authority()
    native.permissions["configuration"] = False
    publish(native)
    with pytest.raises(policy.InspectionError):
        policy.read_config_base(snapshot)


@pytest.mark.parametrize("drift", [None, "base", "mode", "sid"])
def test_real_snapshot_revalidation_allows_owned_directory_entries_but_rejects_drift(
    native, monkeypatch, drift
):
    # Model only this directory's kernel SID; use the actual capture method,
    # _Inspection.validate and all original file/parent checks against real files.
    context = [b"system_u:object_r:hfcache_host_helper_configuration_dir_t:s0"]
    directory = native.config.parent

    def label(capture, path, expected):
        if path == directory:
            native.capture_label(capture, path, expected)

    def getxattr(path, name, *, follow_symlinks):
        assert path == directory
        assert name == "security.selinux"
        assert not follow_symlinks
        return context[0]

    monkeypatch.setattr(policy._Capture, "label", label)
    monkeypatch.setattr(os, "getxattr", getxattr)
    snapshot = policy.inspect_authority()
    before = native.config.stat()
    (directory / ".configuration-applications").mkdir(mode=0o700)
    for name in (".configuration.pending", ".candidate.toml", ".configuration-backup.tmp"):
        write(directory / name, b"owned transaction fixture", 0o600)
    assert native.config.stat() == before
    policy.revalidate(snapshot)
    if drift == "base":
        native.config.write_bytes(native.config.read_bytes() + b"# changed tags\n")
    elif drift == "mode":
        directory.chmod(0o710)
    elif drift == "sid":
        # A same-type SELinux User change also violates the full SID binding.
        context[0] = context[0].replace(b"system_u:", b"unconfined_u:")
    else:
        return
    with pytest.raises(policy.InspectionError):
        policy.revalidate(snapshot)
