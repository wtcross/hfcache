"""ADR135: explicit host permission requires read-only, pinned rootless proof."""

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.unit.test_container_release_installer import (
    deployment as deployment,  # noqa: PLC0414 - register shared hermetic fixture
)
from tests.unit.test_container_release_installer import staged

SCRIPT = Path(__file__).parents[2] / "scripts/container-service.py"
SPEC = importlib.util.spec_from_file_location("cockpit_host_profile", SCRIPT)
assert SPEC is not None
assert SPEC.loader is not None
runtime = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runtime)


@pytest.fixture
def host(deployment, monkeypatch):
    selected = staged(deployment)
    selector = deployment.prefix / "current"
    selector.unlink()
    selector.symlink_to("releases/" + deployment.release["version"])
    policy = deployment.prefix.parent / "cockpit-policy.json"
    permissions = dict.fromkeys(runtime.INSPECTION_ACTIONS, True)
    policy.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "source_commit": deployment.release["source_commit"],
                "index_sha256": hashlib.sha256(
                    (selected / "artifact-index.json").read_bytes()
                ).hexdigest(),
                "permissions": permissions,
            }
        )
    )
    locks = deployment.prefix.parent / "locks"
    info = deployment.lock.stat()
    locks.write_text(
        f"1: FLOCK ADVISORY WRITE 1234 {os.major(info.st_dev):02x}:"
        f"{os.minor(info.st_dev):02x}:{info.st_ino} 0 EOF\n"
    )
    owner = os.geteuid()
    monkeypatch.setattr(runtime, "INSPECTION_OWNER", owner)
    monkeypatch.setattr(runtime, "INSPECTION_PREFIX", deployment.prefix)
    monkeypatch.setattr(runtime, "INSPECTION_POLICY", policy)
    monkeypatch.setattr(runtime, "INSPECTION_MOUNTS", deployment.mountinfo)
    monkeypatch.setattr(runtime, "INSPECTION_LOCKS", locks)
    monkeypatch.setattr(runtime, "INSPECTION_LOCK", deployment.lock)
    monkeypatch.setattr(runtime, "INSPECTION_BINDINGS", deployment.bindings)
    monkeypatch.setattr(runtime, "RELEASE_ROOT", selected)
    monkeypatch.setattr(os, "geteuid", lambda: 0)
    calls = []
    units = {
        name: {
            "Id": name,
            "LoadState": "masked",
            "ActiveState": "inactive",
            "SubState": "dead",
            "UnitFileState": "masked",
            "MainPID": "0",
        }
        for name in runtime.INSPECTION_UNITS
    }
    units[runtime.INSPECTION_GUARD] = {
        "Id": runtime.INSPECTION_GUARD,
        "LoadState": "loaded",
        "ActiveState": "active",
        "SubState": "running",
        "UnitFileState": "enabled",
        "MainPID": "1234",
    }

    def show(unit):
        calls.append(unit)
        assert unit in units
        return units[unit].copy()

    monkeypatch.setattr(runtime, "_inspection_system_show", show)

    def forbidden(*_args, **_kwargs):
        pytest.fail("inspection attempted launcher, Podman, flock or service mutation")

    monkeypatch.setattr(runtime, "load_profile", forbidden)
    monkeypatch.setattr(runtime, "prepare_start", forbidden)
    monkeypatch.setattr(runtime, "drain", forbidden)
    monkeypatch.setattr(os, "execv", forbidden)
    return SimpleNamespace(
        deployment=deployment,
        selected=selected,
        policy=policy,
        locks=locks,
        units=units,
        calls=calls,
        permissions=permissions,
        selector=selector,
    )


def unknown(reason):
    return {"schema_version": 1, "state": "unknown", "reason": reason}


def change_policy(host, change):
    value = json.loads(host.policy.read_bytes())
    change(value)
    host.policy.write_text(json.dumps(value))


def test_guarded_inspection_pins_release_and_holds_without_archive_or_secret_reads(
    host, monkeypatch
):
    opened = []
    original_open = os.open

    def observed(path, flags, *args, **kwargs):
        opened.append((str(path), flags))
        assert not flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC)
        assert not str(path).startswith("/srv")
        assert "secret" not in str(path)
        return original_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", observed)
    before = host.deployment.lock.stat()
    result = runtime.inspect_cockpit()
    assert result["state"] == "guarded", result
    assert result["deployment"] == "rootless"
    assert result["source_commit"] == host.deployment.release["source_commit"]
    assert result["image"] == host.deployment.release["app_image"]
    assert (
        result["index_sha256"]
        == hashlib.sha256((host.selected / "artifact-index.json").read_bytes()).hexdigest()
    )
    assert result["policy_sha256"] == hashlib.sha256(host.policy.read_bytes()).hexdigest()
    assert result["permissions"] == {
        **host.permissions,
        "archive": False,
        "observer": False,
        "schedule": False,
    }
    assert result["facts"]["guard"] == "held"
    assert result["facts"]["archive_mount"] == "nfs-ro"
    assert set(result["facts"]["units"]) == set(runtime.INSPECTION_UNITS)
    assert len(json.dumps(result).encode()) < 16384
    after = host.deployment.lock.stat()
    assert (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) == (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
    )
    assert not any(
        path == str(host.deployment.lock) or path == host.deployment.lock.name
        for path, _flags in opened
    )
    assert set(host.calls) == {*runtime.INSPECTION_UNITS, runtime.INSPECTION_GUARD}


@pytest.mark.parametrize("mount", ["absent", "local-ro", "local-rw"])
def test_explicit_permitted_fixture_means_submission_permission_not_writable_archive(host, mount):
    host.units[runtime.INSPECTION_GUARD].update(
        LoadState="not-found",
        ActiveState="inactive",
        SubState="dead",
        UnitFileState="not-found",
        MainPID="0",
    )
    body = "1 0 0:1 / / rw - ext4 /dev/local rw\n"
    if mount != "absent":
        body += (
            f"2 1 0:2 / /srv/hfcache {'ro' if mount == 'local-ro' else 'rw'} - tmpfs fixture rw\n"
        )
    host.deployment.mountinfo.write_text(body)
    result = runtime.inspect_cockpit()
    assert result["state"] == "permitted", result
    assert result["facts"]["archive_mount"] == mount
    assert result["permissions"]["archive"] is True
    # This release's nine bindings prove neither system scheduled observer.
    assert result["permissions"]["observer"] is False
    assert result["permissions"]["schedule"] is False


def test_absent_guard_and_masks_never_create_permissions(host):
    host.units[runtime.INSPECTION_GUARD].update(
        ActiveState="inactive", SubState="dead", MainPID="0"
    )
    change_policy(
        host,
        lambda value: value.update(permissions=dict.fromkeys(runtime.INSPECTION_ACTIONS, False)),
    )
    for unit in runtime.INSPECTION_UNITS:
        host.units[unit].update(LoadState="loaded", UnitFileState="enabled")
    result = runtime.inspect_cockpit()
    assert result["state"] == "permitted"
    assert not any(result["permissions"].values())


def test_loaded_unmasked_units_cannot_authorize_unproven_rootless_observer_bindings(host):
    host.units[runtime.INSPECTION_GUARD].update(
        ActiveState="inactive", SubState="dead", MainPID="0"
    )
    for unit in runtime.INSPECTION_UNITS:
        host.units[unit].update(LoadState="loaded", UnitFileState="enabled")
    result = runtime.inspect_cockpit()
    assert result["permissions"]["archive"] is True
    assert result["permissions"]["schedule"] is False
    assert result["permissions"]["observer"] is False


def test_missing_policy_denies_before_release_or_manager_reads_and_is_not_created(host):
    host.policy.unlink()
    assert runtime.inspect_cockpit() == unknown("policy-missing")
    assert not host.policy.exists()
    assert host.calls == []


@pytest.mark.parametrize(
    "kind", ["symlink", "hardlink", "writable", "oversize", "fifo", "directory"]
)
def test_unsafe_policy_is_preserved_and_denied_without_manager_reads(host, kind):
    original = host.policy.read_bytes()
    if kind == "symlink":
        other = host.policy.with_name("policy-target")
        host.policy.rename(other)
        host.policy.symlink_to(other)
    elif kind == "hardlink":
        os.link(host.policy, host.policy.with_name("policy-link"))
    elif kind == "writable":
        host.policy.chmod(0o666)
    elif kind == "oversize":
        host.policy.write_bytes(b"x" * 4097)
    else:
        host.policy.unlink()
        if kind == "fifo":
            os.mkfifo(host.policy)
        else:
            host.policy.mkdir()
    assert runtime.inspect_cockpit() == unknown("policy-invalid")
    assert host.calls == []
    if kind not in {"fifo", "directory", "oversize"}:
        assert host.policy.read_bytes() == original


@pytest.mark.parametrize(
    "change",
    [
        lambda value: value.update(extra=True),
        lambda value: value.update(schema_version=True),
        lambda value: value.update(source_commit="unknown"),
        lambda value: value.update(index_sha256="unknown"),
        lambda value: value["permissions"].update(archive=1),
        lambda value: value["permissions"].update(arbitrary=True),
        lambda value: value["permissions"].pop("archive"),
    ],
)
def test_policy_unknown_schema_or_inferred_permissions_are_refused(host, change):
    change_policy(host, change)
    assert runtime.inspect_cockpit() == unknown("policy-invalid")
    assert host.calls == []


def test_duplicate_policy_field_cannot_smuggle_authority(host):
    host.policy.write_bytes(
        host.policy.read_bytes().replace(
            b'"schema_version": 1', b'"schema_version": 1, "schema_version": 1'
        )
    )
    assert runtime.inspect_cockpit() == unknown("policy-invalid")


@pytest.mark.parametrize("name", ["source_commit", "index_sha256"])
def test_policy_pin_drift_refuses_selected_release_without_runtime_reads(host, name):
    change_policy(host, lambda value: value.update({name: "f" * len(value[name])}))
    assert runtime.inspect_cockpit() == unknown("deployment-unverified")
    assert host.calls == []


@pytest.mark.parametrize(
    "name",
    [
        "scripts/container-service.py",
        "scripts/install-container-release.py",
        "rendered/runtime.json",
        "rendered/client.toml",
    ],
)
def test_changed_indexed_helper_or_policy_refuses_without_executing_it(host, name):
    (host.selected / name).write_bytes(b"SYNTHETIC_API_SECRET\n")
    assert runtime.inspect_cockpit() == unknown("deployment-unverified")
    assert host.calls == []


def test_unauthenticated_installer_bytes_never_execute_even_when_they_are_valid_python(host):
    marker = host.policy.with_name("must-not-exist")
    (host.selected / "scripts/install-container-release.py").write_text(
        "from pathlib import Path\n" + f"Path({str(marker)!r}).write_text('SYNTHETIC_API_SECRET')\n"
    )
    assert runtime.inspect_cockpit() == unknown("deployment-unverified")
    assert not marker.exists()
    assert host.calls == []


def test_release_missing_authenticated_installer_proof_is_unsupported(host):
    index = json.loads((host.selected / "artifact-index.json").read_bytes())
    index["files"].pop("scripts/install-container-release.py")
    body = json.dumps(index).encode()
    (host.selected / "artifact-index.json").write_bytes(body)
    change_policy(host, lambda value: value.update(index_sha256=hashlib.sha256(body).hexdigest()))
    assert runtime.inspect_cockpit() == unknown("deployment-unverified")
    assert host.calls == []


@pytest.mark.parametrize("relative", tuple(runtime.INSPECTION_BINDINGS.values()))
def test_native_or_unreviewed_fixed_binding_refuses_before_runtime_inspection(host, relative):
    binding = next(path for path, value in host.deployment.bindings.items() if value == relative)
    binding.unlink()
    binding.symlink_to("/opt/hfcache/native/.venv/bin/hfcache")
    assert runtime.inspect_cockpit() == unknown("deployment-unverified")
    assert host.calls == []


@pytest.mark.parametrize("kind", ["pid", "inode", "missing", "oversize"])
def test_guard_active_is_not_proof_of_original_lock_without_kernel_match(host, kind):
    if kind == "pid":
        host.units[runtime.INSPECTION_GUARD]["MainPID"] = "5678"
    elif kind == "inode":
        host.locks.write_text("1: FLOCK ADVISORY WRITE 1234 00:01:1234 0 EOF\n")
    elif kind == "missing":
        host.locks.unlink()
    else:
        host.locks.write_bytes(b"x" * 1048577)
    assert runtime.inspect_cockpit() == unknown("facts-unavailable")


@pytest.mark.parametrize("kind", ["symlink", "mode", "replacement"])
def test_unsafe_or_replaced_original_lock_is_not_repaired_or_acquired(host, kind):
    path = host.deployment.lock
    if kind == "symlink":
        predecessor = path.with_name("predecessor")
        path.rename(predecessor)
        path.symlink_to(predecessor)
    elif kind == "mode":
        path.chmod(0o640)
    else:
        replacement = path.with_name("replacement")
        replacement.write_bytes(b"replacement")
        replacement.chmod(0o600)
        replacement.replace(path)
    assert runtime.inspect_cockpit() == unknown("facts-unavailable")


def test_nas_mount_drift_or_duplicate_rows_denies_without_opening_archive(host):
    original = host.deployment.mountinfo.read_text()
    host.deployment.mountinfo.write_text(original.replace("hfcache ro - nfs4", "hfcache rw - nfs4"))
    assert runtime.inspect_cockpit() == unknown("facts-unavailable")
    host.deployment.mountinfo.write_text(
        original + "3 1 0:3 / /srv/hfcache ro - nfs4 other:/archive rw\n"
    )
    assert runtime.inspect_cockpit() == unknown("facts-unavailable")


def test_current_selector_transition_invalidates_even_a_verified_prior_snapshot(host, monkeypatch):
    original = runtime._inspection_system_show

    def changed(unit):
        value = original(unit)
        if unit == runtime.INSPECTION_UNITS[0]:
            host.selector.unlink()
            host.selector.symlink_to("releases/0.1.9")
        return value

    monkeypatch.setattr(runtime, "_inspection_system_show", changed)
    assert runtime.inspect_cockpit() == unknown("facts-unavailable")
    assert host.selector.readlink() == Path("releases/0.1.9")


def test_policy_transition_invalidates_prior_permission_snapshot(host, monkeypatch):
    original = runtime._inspection_system_show

    def changed(unit):
        value = original(unit)
        if unit == runtime.INSPECTION_UNITS[0]:
            change_policy(host, lambda policy: policy["permissions"].update(configuration=False))
        return value

    monkeypatch.setattr(runtime, "_inspection_system_show", changed)
    assert runtime.inspect_cockpit() == unknown("facts-unavailable")


def test_newly_held_guard_invalidates_inactive_permission_snapshot(host, monkeypatch):
    host.units[runtime.INSPECTION_GUARD].update(
        ActiveState="inactive", SubState="dead", MainPID="0"
    )
    original = runtime._inspection_system_show

    def changed(unit):
        value = original(unit)
        if unit == runtime.INSPECTION_UNITS[0]:
            host.units[runtime.INSPECTION_GUARD].update(
                ActiveState="active", SubState="running", MainPID="1234"
            )
        return value

    monkeypatch.setattr(runtime, "_inspection_system_show", changed)
    assert runtime.inspect_cockpit() == unknown("facts-unavailable")


def test_system_manager_reader_has_closed_argv_clean_environment_and_bounded_output(monkeypatch):
    original = subprocess.Popen
    calls = []

    def controlled(argv, **options):
        calls.append((argv, options))
        body = (
            "Id=hfcache-sync.timer\nLoadState=loaded\nActiveState=inactive\n"
            "SubState=dead\nUnitFileState=linked\nMainPID=0\n"
        )
        return original(
            [sys.executable, "-c", "import sys; sys.stdout.write(" + repr(body) + ")"], **options
        )

    monkeypatch.setenv("DBUS_SYSTEM_BUS_ADDRESS", "SYNTHETIC_API_SECRET")
    monkeypatch.setenv("SYSTEMD_UNIT_PATH", "/untrusted")
    monkeypatch.setattr(subprocess, "Popen", controlled)
    facts = runtime._inspection_system_show("hfcache-sync.timer")
    assert facts["UnitFileState"] == "linked"
    argv, options = calls[0]
    assert argv == [
        "/usr/bin/systemctl",
        "--system",
        "show",
        "hfcache-sync.timer",
        "--no-pager",
        "--property=Id,LoadState,ActiveState,SubState,UnitFileState,MainPID",
    ]
    assert options["env"] == {
        "PATH": "/usr/sbin:/usr/bin:/sbin:/bin",
        "LANG": "C",
        "LC_ALL": "C",
        "SYSTEMD_COLORS": "0",
    }
    assert options["stdin"] is subprocess.DEVNULL
    assert options["stderr"] is subprocess.DEVNULL
    assert options["cwd"] == "/"
    with pytest.raises(ValueError, match="read-only Cockpit inspection refused"):
        runtime._inspection_system_show("hfcache.target")
    assert len(calls) == 1


@pytest.mark.parametrize(
    "body", ["x" * 16385, "Id=hfcache-sync.timer\nId=hfcache-sync.timer\n", "SYNTHETIC_API_SECRET"]
)
def test_untrusted_manager_output_never_becomes_partial_permission(monkeypatch, body):
    original = subprocess.Popen

    def controlled(_argv, **options):
        return original(
            [sys.executable, "-c", "import sys; sys.stdout.write(" + repr(body) + ")"], **options
        )

    monkeypatch.setattr(subprocess, "Popen", controlled)
    with pytest.raises(ValueError, match="read-only Cockpit inspection refused"):
        runtime._inspection_system_show("hfcache-sync.timer")


def test_manager_deadline_ends_only_its_owned_readonly_query(monkeypatch):
    original = subprocess.Popen
    children = []
    times = iter([0.0, 6.0])

    def controlled(_argv, **options):
        child = original([sys.executable, "-c", "import time; time.sleep(60)"], **options)
        children.append(child)
        return child

    monkeypatch.setattr(subprocess, "Popen", controlled)
    monkeypatch.setattr(runtime.time, "monotonic", lambda: next(times))
    with pytest.raises(ValueError, match="read-only Cockpit inspection refused"):
        runtime._inspection_system_show("hfcache-sync.timer")
    assert len(children) == 1
    assert children[0].returncode is not None


@pytest.mark.parametrize("argument", ["/tmp/policy.json", "--user", "--", "client", "--engine"])
def test_inspection_rejects_every_extra_argument_before_host_reads(monkeypatch, argument, capsys):
    def forbidden(*_args, **_kwargs):
        pytest.fail("invalid inspect grammar attempted runtime access")

    monkeypatch.setattr(runtime, "inspect_cockpit", forbidden)
    monkeypatch.setattr(runtime, "load_profile", forbidden)
    monkeypatch.setattr(runtime.sys, "argv", [str(SCRIPT), "inspect-cockpit", argument])
    assert runtime.main() == 20
    assert capsys.readouterr().out == ""


def test_inspection_role_denies_nonroot_before_any_profile_or_host_read(monkeypatch, capsys):
    def forbidden(*_args, **_kwargs):
        pytest.fail("unprivileged inspection attempted a host read or launcher")

    monkeypatch.setattr(os, "geteuid", lambda: 12345)
    monkeypatch.setattr(runtime, "load_profile", forbidden)
    monkeypatch.setattr(Path, "read_text", forbidden)
    monkeypatch.setattr(os, "open", forbidden)
    monkeypatch.setattr(os, "execv", forbidden)
    monkeypatch.setattr(runtime.sys, "argv", [str(SCRIPT), "inspect-cockpit"])
    assert runtime.main() == 0
    output = capsys.readouterr()
    assert json.loads(output.out) == {
        "schema_version": 1,
        "state": "unknown",
        "reason": "privilege-required",
    }
    assert output.err == ""


def test_inspection_static_help_names_its_readonly_scope(monkeypatch, capsys):
    def forbidden(*_args, **_kwargs):
        pytest.fail("help attempted runtime access")

    monkeypatch.setattr(runtime, "load_profile", forbidden)
    monkeypatch.setattr(os, "open", forbidden)
    monkeypatch.setattr(runtime.sys, "argv", [str(SCRIPT), "inspect-cockpit", "--help"])
    assert runtime.main() == 0
    output = capsys.readouterr()
    assert "inspect-cockpit" in output.out
    assert "read-only" in output.out
    assert output.err == ""
