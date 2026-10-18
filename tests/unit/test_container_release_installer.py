"""Decision 127: local immutable artifacts and noncreating guarded selection."""

import copy
import fcntl
import hashlib
import importlib.util
import json
import os
import shutil
import stat
import subprocess
import tomllib
from pathlib import Path
from types import SimpleNamespace

import pytest

from hfcache.client_config import ClientConfig
from hfcache.server_config import validate_server_config_mapping

REPOSITORY = Path(__file__).parents[2]
SPEC = importlib.util.spec_from_file_location(
    "container_release_installer", REPOSITORY / "scripts/install-container-release.py"
)
assert SPEC is not None
assert SPEC.loader is not None
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)


def digest(body):
    return hashlib.sha256(body).hexdigest()


def quiet():
    return {
        "LoadState": "loaded",
        "ActiveState": "inactive",
        "MainPID": "0",
        "ControlPID": "0",
        "TasksCurrent": "0",
        "ControlGroup": "",
    }


@pytest.fixture
def deployment(tmp_path, monkeypatch):
    source = tmp_path / "source"
    source.mkdir()
    for name in sorted(installer.REQUIRED):
        target = source / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPOSITORY / name, target)
    (source / "scripts/extra.py").write_text("# also authenticated\n")
    prefix = tmp_path / "opt"
    (prefix / "releases/0.1.9").mkdir(parents=True)
    (prefix / "releases/0.1.9/preserved").write_bytes(b"old release")
    (prefix / "current").symlink_to("releases/0.1.9")
    runtime = tmp_path / "runtime"
    runtime.mkdir(mode=0o700)
    lock = runtime / "hfcache.lock"
    lock.write_bytes(b"original lock inode\n")
    lock.chmod(0o600)
    mountinfo = tmp_path / "mountinfo"
    mountinfo.write_text(
        "1 0 0:1 / / rw - ext4 /dev/local rw\n2 1 0:2 / /srv/hfcache ro - nfs4 nas:/archive rw\n"
    )
    cgroups = tmp_path / "cgroups"
    cgroups.mkdir()
    binding_root = tmp_path / "installed"
    bindings = {
        binding_root / path.relative_to("/"): relative
        for path, relative in installer.BINDINGS.items()
    }
    for path, relative in bindings.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.symlink_to(prefix / "current" / relative)
    base = {
        "defaultAction": "SCMP_ACT_ERRNO",
        "defaultErrnoRet": 38,
        "architectures": ["SCMP_ARCH_X86_64", "SCMP_ARCH_X86", "SCMP_ARCH_X32"],
        "syscalls": [
            {"names": ["read", "write", "socket", "socketcall"], "action": "SCMP_ACT_ALLOW"},
            {
                "names": ["socket", "unshare"],
                "action": "SCMP_ACT_ALLOW",
                "args": [{"index": 0, "value": 16, "op": "SCMP_CMP_EQ"}],
            },
            {"names": ["socketcall"], "action": "SCMP_ACT_ALLOW", "includes": {"caps": ["X"]}},
            {"names": ["ptrace"], "action": "SCMP_ACT_ERRNO", "errnoRet": 1},
        ],
    }
    default = tmp_path / "default-seccomp.json"
    default.write_bytes(installer.encoded(base))
    release = {
        "schema_version": 1,
        "version": "0.2.0",
        "hostname": "writer.example.test",
        "service_uid": os.geteuid() or 981,
        "service_gid": os.getegid() or 981,
        "app_image": "sha256:" + "a" * 64,
        "caddy_image": "sha256:" + "b" * 64,
        "source_commit": "c" * 40,
        "wheel_sha256": "d" * 64,
        "files": {
            name: digest((source / name).read_bytes())
            for name in sorted(installer.REQUIRED | {"scripts/extra.py"})
        },
    }
    calls = []
    manager = SimpleNamespace(returncode=0, stdout="active\n")
    engine = SimpleNamespace(returncode=0, stdout="[]")

    def run(argv, **_kwargs):
        calls.append(argv)
        return manager if argv[0] == "/usr/bin/systemctl" else engine

    monkeypatch.setattr(installer, "PREFIX", prefix)
    monkeypatch.setattr(installer, "LOCK_PATH", lock)
    monkeypatch.setattr(installer, "BINDINGS", bindings)
    monkeypatch.setattr(installer, "OWNER_UID", os.geteuid())
    monkeypatch.setattr(installer, "CGROUP_ROOT", cgroups)
    monkeypatch.setattr(installer, "MOUNTINFO", mountinfo)
    monkeypatch.setattr(installer, "system_show", lambda *_args, **_kwargs: quiet())
    monkeypatch.setattr(
        installer,
        "subprocess",
        SimpleNamespace(run=run, SubprocessError=subprocess.SubprocessError),
    )
    return SimpleNamespace(
        source=source,
        bindings=bindings,
        binding_root=binding_root,
        prefix=prefix,
        lock=lock,
        mountinfo=mountinfo,
        cgroups=cgroups,
        default=default,
        base=base,
        release=release,
        manager=manager,
        engine=engine,
        calls=calls,
    )


def staged(deployment):
    return installer.stage(deployment.source, deployment.release, deployment.default)


def assert_preserved(deployment):
    assert (deployment.prefix / "current").readlink() == Path("releases/0.1.9")
    assert (deployment.prefix / "releases/0.1.9/preserved").read_bytes() == b"old release"
    assert deployment.lock.read_bytes() == b"original lock inode\n"


@pytest.mark.parametrize("hostname", ["writer.example.test", "localhost", "127.0.0.1"])
def test_stage_authenticates_every_source_and_recomputes_rendered_policy(deployment, hostname):
    deployment.release["hostname"] = hostname
    target = staged(deployment)
    assert installer._verify_stage(target) == deployment.release
    index = json.loads((target / "artifact-index.json").read_bytes())
    assert set(index) == {"schema_version", "files"}
    assert set(index["files"]) == installer._expected_files(deployment.release)
    for name, expected in index["files"].items():
        assert digest((target / name).read_bytes()) == expected
    server = validate_server_config_mapping(
        tomllib.loads((target / "rendered/server.toml").read_text())
    )
    client = ClientConfig.model_validate(
        tomllib.loads((target / "rendered/client.toml").read_text())
    )
    assert str(server.listener.unix_socket) == str(client.api_socket) == "/run/hfcache/api/api.sock"
    assert not server.maintenance_enabled
    assert server.listener.tcp_enabled is False
    assert server.listener.allowed_hosts == tuple(
        dict.fromkeys([hostname, "localhost", "127.0.0.1"])
    )
    provenance = json.loads((target / "rendered/seccomp-provenance.json").read_bytes())
    assert provenance == {
        "default_sha256": digest(deployment.default.read_bytes()),
        "derived_sha256": digest((target / "rendered/worker-seccomp.json").read_bytes()),
    }
    assert_preserved(deployment)


def test_switch_is_atomic_under_original_noncreating_lock(deployment, monkeypatch):
    target = staged(deployment)
    before = deployment.lock.stat()
    replace = os.replace
    observed = []

    def replace_guarded(source, destination, **kwargs):
        assert_preserved(deployment)
        with deployment.lock.open("rb") as contender, pytest.raises(BlockingIOError):
            fcntl.flock(contender, fcntl.LOCK_EX | fcntl.LOCK_NB)
        observed.append((source, destination))
        replace(source, destination, **kwargs)

    monkeypatch.setattr(
        installer, "os", SimpleNamespace(**(vars(os) | {"replace": replace_guarded}))
    )
    assert installer.switch("0.2.0") == target
    assert observed == [(".current-container-next", "current")]
    assert (deployment.prefix / "current").readlink() == Path("releases/0.2.0")
    assert deployment.lock.stat().st_ino == before.st_ino
    assert deployment.lock.read_bytes() == b"original lock inode\n"
    assert not (deployment.prefix / ".current-container-next").exists()
    assert any("--remote=false" in argv for argv in deployment.calls)
    assert all(
        not set(argv) & {"start", "stop", "restart", "pull", "run", "rm"}
        for argv in deployment.calls
    )


@pytest.mark.parametrize(
    "name",
    [
        "scripts/container-service.py",
        "scripts/extra.py",
        "packaging/containers/server.toml.in",
        "rendered/runtime.json",
        "rendered/server.toml",
        "rendered/client.toml",
        "rendered/Caddyfile",
        "rendered/default-seccomp.json",
        "rendered/worker-seccomp.json",
        "rendered/seccomp-provenance.json",
        "container-release.json",
        "artifact-index.json",
    ],
)
def test_every_changed_staged_artifact_refuses_switch_and_preserves_evidence(deployment, name):
    target = staged(deployment)
    path = target / name
    path.write_bytes(path.read_bytes() + b"\nchanged")
    with pytest.raises((ValueError, json.JSONDecodeError)):
        installer.switch("0.2.0")
    assert path.read_bytes().endswith(b"changed")
    assert_preserved(deployment)


@pytest.mark.parametrize(
    "name", ["rendered/runtime.json", "rendered/worker-seccomp.json", "scripts/extra.py"]
)
def test_resealing_index_does_not_authorize_changed_policy_or_original_source(deployment, name):
    target = staged(deployment)
    changed = target / name
    changed.write_bytes(b'{"schema_version":1,"unexpected":true}\n')
    index = json.loads((target / "artifact-index.json").read_bytes())
    index["files"][name] = digest(changed.read_bytes())
    (target / "artifact-index.json").write_bytes(installer.encoded(index))
    with pytest.raises(ValueError, match=r"changed"):
        installer.switch("0.2.0")
    assert_preserved(deployment)


@pytest.mark.parametrize("kind", ["file", "directory", "link", "hardlink", "fifo"])
def test_unexplained_staged_evidence_is_preserved(deployment, kind):
    target = staged(deployment)
    extra = target / "unexplained"
    if kind == "directory":
        extra.mkdir()
    elif kind == "link":
        extra.symlink_to("rendered/runtime.json")
    elif kind == "hardlink":
        extra.hardlink_to(target / "rendered/runtime.json")
    elif kind == "fifo":
        os.mkfifo(extra)
    else:
        extra.write_bytes(b"unknown")
    with pytest.raises(ValueError, match="unexplained"):
        installer.switch("0.2.0")
    assert extra.lstat()
    assert_preserved(deployment)


@pytest.mark.parametrize("kind", ["missing", "locked", "symlink", "hardlink", "writable"])
def test_unsafe_or_busy_original_lock_never_creates_or_selects(deployment, kind):
    staged(deployment)
    held = None
    if kind == "missing":
        deployment.lock.unlink()
    elif kind == "locked":
        held = deployment.lock.open("rb")
        fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
    elif kind == "symlink":
        deployment.lock.rename(deployment.lock.with_suffix(".original"))
        deployment.lock.symlink_to("hfcache.original")
    elif kind == "hardlink":
        deployment.lock.with_suffix(".other").hardlink_to(deployment.lock)
    else:
        deployment.lock.chmod(0o660)
    try:
        with pytest.raises((OSError, ValueError)):
            installer.switch("0.2.0")
        assert (deployment.prefix / "current").readlink() == Path("releases/0.1.9")
        if kind == "missing":
            assert not deployment.lock.exists()
    finally:
        if held is not None:
            held.close()


def test_failed_stage_preserves_partial_artifacts_and_refuses_retry(deployment):
    (deployment.source / "scripts/extra.py").write_bytes(b"changed after manifest")
    with pytest.raises(ValueError, match="source artifact"):
        staged(deployment)
    partial = deployment.prefix / "releases/.container-stage-0.2.0"
    assert partial.is_dir()
    with pytest.raises(ValueError, match="preserved"):
        staged(deployment)
    assert partial.is_dir()
    assert_preserved(deployment)


def test_unknown_atomic_selector_evidence_is_never_removed(deployment):
    staged(deployment)
    unknown = deployment.prefix / ".current-container-next"
    unknown.write_bytes(b"unexplained")
    with pytest.raises(FileExistsError):
        installer.switch("0.2.0")
    assert unknown.read_bytes() == b"unexplained"
    assert_preserved(deployment)


def test_lock_path_swap_after_acquisition_is_refused_and_preserved(deployment, monkeypatch):
    staged(deployment)
    flock = fcntl.flock
    original = deployment.lock.with_suffix(".preserved")

    def swapped(descriptor, operation):
        flock(descriptor, operation)
        deployment.lock.rename(original)
        deployment.lock.write_bytes(b"substituted lock")
        deployment.lock.chmod(0o600)

    monkeypatch.setattr(
        installer,
        "fcntl",
        SimpleNamespace(flock=swapped, LOCK_EX=fcntl.LOCK_EX, LOCK_NB=fcntl.LOCK_NB),
    )
    with pytest.raises(ValueError, match="lock changed"):
        installer.switch("0.2.0")
    assert (deployment.prefix / "current").readlink() == Path("releases/0.1.9")
    assert original.read_bytes() == b"original lock inode\n"
    assert deployment.lock.read_bytes() == b"substituted lock"


def test_stage_fsync_failure_preserves_unselected_partial_tree(deployment, monkeypatch):
    fsync = os.fsync

    def fail_after_file(descriptor):
        if stat.S_ISREG(os.fstat(descriptor).st_mode):
            message = "fixture fsync failure"
            raise OSError(message)
        fsync(descriptor)

    monkeypatch.setattr(installer, "os", SimpleNamespace(**(vars(os) | {"fsync": fail_after_file})))
    with pytest.raises(OSError, match="fixture fsync"):
        staged(deployment)
    partial = deployment.prefix / "releases/.container-stage-0.2.0"
    assert any(path.is_file() for path in partial.rglob("*"))
    assert not (deployment.prefix / "releases/0.2.0").exists()
    assert_preserved(deployment)


def test_switch_directory_fsync_failure_preserves_new_atomic_selector_without_rollback(
    deployment, monkeypatch
):
    staged(deployment)
    fsync = os.fsync

    def fail_acknowledgment(descriptor):
        if (deployment.prefix / "current").readlink() == Path("releases/0.2.0"):
            message = "fixture directory fsync failure"
            raise OSError(message)
        fsync(descriptor)

    monkeypatch.setattr(
        installer, "os", SimpleNamespace(**(vars(os) | {"fsync": fail_acknowledgment}))
    )
    with pytest.raises(OSError, match="fixture directory fsync"):
        installer.switch("0.2.0")
    assert (deployment.prefix / "current").readlink() == Path("releases/0.2.0")
    assert (deployment.prefix / "releases/0.1.9/preserved").read_bytes() == b"old release"
    assert deployment.lock.read_bytes() == b"original lock inode\n"


@pytest.mark.parametrize(
    "value", ["/srv/hfcache", "../../outside", "releases/unknown", "releases/0.1.9/extra"]
)
def test_unrecognized_previous_selector_is_preserved_without_following(deployment, value):
    staged(deployment)
    selector = deployment.prefix / "current"
    selector.unlink()
    selector.symlink_to(value)
    with pytest.raises(ValueError, match="previous selector"):
        installer.switch("0.2.0")
    assert selector.readlink() == Path(value)


@pytest.mark.parametrize("schema", [True, 2, None])
def test_future_or_missing_artifact_index_version_refuses(deployment, schema):
    target = staged(deployment)
    path = target / "artifact-index.json"
    index = json.loads(path.read_bytes())
    if schema is None:
        del index["schema_version"]
    else:
        index["schema_version"] = schema
    path.write_bytes(installer.encoded(index))
    with pytest.raises(ValueError, match="artifact index"):
        installer.switch("0.2.0")
    assert_preserved(deployment)


@pytest.mark.parametrize(
    "change",
    [
        {"LoadState": "error"},
        {"ActiveState": "activating"},
        {"MainPID": "1"},
        {"MainPID": None},
        {"ControlPID": "1"},
        {"ControlPID": None},
        {"TasksCurrent": "1"},
        {"TasksCurrent": None},
        {"TasksCurrent": "unknown"},
        {"ControlGroup": None},
    ],
)
def test_unknown_or_surviving_service_accounting_refuses(deployment, change):
    state = quiet() | change
    if change.get("ControlGroup", "") is None:
        state.pop("ControlGroup")
    with pytest.raises(ValueError, match=r"executor"):
        installer._quiescent_unit("hfcache-api.service", state)


def test_cgroup_accounting_reads_actual_descendants_and_requires_files(deployment):
    group = deployment.cgroups / "service/child"
    group.mkdir(parents=True)
    (group.parent / "cgroup.procs").write_text("")
    (group / "cgroup.procs").write_text("123\n")
    state = quiet() | {"ControlGroup": "/service"}
    with pytest.raises(ValueError, match="surviving"):
        installer._quiescent_unit("hfcache-api.service", state)
    (group / "cgroup.procs").write_text("")
    installer._quiescent_unit("hfcache-api.service", state)
    (group / "cgroup.procs").unlink()
    with pytest.raises(FileNotFoundError):
        installer._quiescent_unit("hfcache-api.service", state)


def test_inactive_user_manager_does_not_skip_actual_engine_inventory(deployment):
    deployment.manager.returncode, deployment.manager.stdout = 3, "inactive\n"
    deployment.engine.stdout = '[{"Id":"survivor"}]'
    with pytest.raises(ValueError, match="surviving rootless"):
        installer.quiescent(deployment.release)
    assert any("--remote=false" in argv for argv in deployment.calls)


@pytest.mark.parametrize(
    ("returncode", "output"),
    [(1, "unknown"), (4, "inactive"), (0, "inactive"), (3, ""), (0, "active\nextra")],
)
def test_unknown_user_manager_accounting_refuses(deployment, returncode, output):
    deployment.manager.returncode, deployment.manager.stdout = returncode, output
    with pytest.raises(ValueError, match="manager accounting"):
        installer.quiescent(deployment.release)


@pytest.mark.parametrize(("options", "kind"), [("rw", "nfs4"), ("ro,rw", "nfs4"), ("ro", "ext4")])
def test_selection_requires_exact_readonly_nfs_mount_barrier(deployment, options, kind):
    deployment.mountinfo.write_text(
        "1 0 0:1 / / rw - ext4 /dev/local rw\n"
        f"2 1 0:2 / /srv/hfcache {options} - {kind} nas:/archive rw\n"
    )
    with pytest.raises(ValueError, match="NAS barrier"):
        installer.quiescent(deployment.release)


def test_known_autofs_row_does_not_hide_or_invalidate_readonly_nfs_barrier(deployment):
    deployment.mountinfo.write_text(
        deployment.mountinfo.read_text() + "3 1 0:3 / /srv/hfcache rw - autofs systemd-1 rw\n"
    )
    installer.quiescent(deployment.release)
    deployment.mountinfo.write_text(
        deployment.mountinfo.read_text() + "4 1 0:4 / /srv/hfcache rw - xfs /dev/local rw\n"
    )
    with pytest.raises(ValueError, match="NAS barrier"):
        installer.quiescent(deployment.release)


def test_policy_removes_every_broad_socket_allow_without_weakening_other_rules(deployment):
    original = copy.deepcopy(deployment.base)
    policy = installer.worker_seccomp(deployment.base)
    assert deployment.base == original
    assert policy["defaultAction"] == "SCMP_ACT_ERRNO"
    expected = copy.deepcopy(original)
    expected.pop("architectures")
    expected["archMap"] = [{"architecture": "SCMP_ARCH_X86_64", "subArchitectures": []}]
    expected["syscalls"] = [
        {"names": ["read", "write"], "action": "SCMP_ACT_ALLOW"},
        {"names": ["unshare"], "action": "SCMP_ACT_ALLOW", "args": original["syscalls"][1]["args"]},
        original["syscalls"][3],
        {
            "names": ["socket"],
            "action": "SCMP_ACT_ALLOW",
            "args": [{"index": 0, "value": 1, "op": "SCMP_CMP_EQ"}],
        },
    ]
    assert policy == expected
    for family in (0, 2, 10, 16, 40):
        allowed = [
            rule
            for rule in policy["syscalls"]
            if rule["action"] == "SCMP_ACT_ALLOW"
            and "socket" in rule["names"]
            and all(arg["value"] == family for arg in rule.get("args", []))
        ]
        assert allowed == []


@pytest.mark.parametrize(
    "base",
    [
        {},
        {"defaultAction": "SCMP_ACT_ALLOW", "syscalls": []},
        {"defaultAction": "SCMP_ACT_ERRNO", "syscalls": []},
        {
            "defaultAction": "SCMP_ACT_ERRNO",
            "syscalls": [
                {
                    "names": ["socket"],
                    "action": "SCMP_ACT_ALLOW",
                    "args": [{"index": 0, "value": 2, "op": "SCMP_CMP_EQ"}],
                }
            ],
        },
        {"defaultAction": "SCMP_ACT_ERRNO", "syscalls": [None]},
    ],
)
def test_unproven_default_socket_policy_refuses(base):
    with pytest.raises(ValueError, match=r"default"):
        installer.worker_seccomp(base)


@pytest.mark.parametrize(
    "change",
    [
        {"schema_version": True},
        {"schema_version": 2},
        {"service_uid": True},
        {"app_image": "localhost/latest"},
        {"extra": "unknown"},
    ],
)
def test_manifest_is_explicit_closed_and_strict(deployment, change):
    with pytest.raises(ValueError, match=r"release|service"):
        installer.manifest(deployment.release | change)


def test_protected_manifest_rejects_duplicate_keys_and_writable_ancestors(deployment):
    path = deployment.source / "manifest.json"
    path.write_bytes(
        installer.encoded(deployment.release).replace(
            b'"schema_version": 1', b'"schema_version": 1, "schema_version": 1'
        )
    )
    with pytest.raises(ValueError, match="duplicate"):
        installer.protected_json(path)
    path.write_bytes(installer.encoded(deployment.release))
    deployment.source.chmod(0o777)
    with pytest.raises(ValueError, match="untrusted"):
        installer.protected_json(path)


def test_no_nas_path_or_symlink_alias_is_opened(deployment, monkeypatch):
    target = deployment.source / "alias"
    target.symlink_to("/srv/hfcache")
    for path in (Path("/srv/hfcache/anything"), target / "anything"):
        with pytest.raises(ValueError, match=r"local|symlink"):
            installer.local(path)
    mount = deployment.mountinfo.read_text()
    deployment.mountinfo.write_text(
        mount + f"3 1 0:3 / {deployment.source} ro - nfs4 nas:/other ro\n"
    )
    with pytest.raises(ValueError, match="proven local"):
        installer.read_file(deployment.source / "scripts/extra.py")


def test_ambiguous_overmounted_local_and_nfs_paths_refuse_before_file_access(deployment):
    deployment.mountinfo.write_text(
        deployment.mountinfo.read_text()
        + f"3 1 0:3 / {deployment.source} ro - nfs4 nas:/other ro\n"
        + f"4 1 0:4 / {deployment.source} rw - xfs /dev/local rw\n"
    )
    with pytest.raises(ValueError, match="proven local"):
        installer.local(deployment.source / "scripts/extra.py")


def test_host_installer_runs_with_its_system_python_without_the_application_environment():
    result = subprocess.run(
        ["/usr/bin/python3", str(REPOSITORY / "scripts/install-container-release.py"), "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "{render,stage,switch}" in result.stdout


@pytest.mark.parametrize("installed", tuple(installer.BINDINGS))
@pytest.mark.parametrize("kind", ["missing", "static-copy", "stale-link"])
def test_every_fixed_entrypoint_binding_must_follow_current(deployment, installed, kind):
    staged(deployment)
    path = deployment.binding_root / installed.relative_to("/")
    relative = deployment.bindings[path]
    path.unlink()
    if kind == "static-copy":
        path.write_bytes(b"preserved previous installed file")
    elif kind == "stale-link":
        path.symlink_to(deployment.prefix / "releases/0.1.9" / relative)
    with pytest.raises((FileNotFoundError, ValueError)):
        installer.switch("0.2.0")
    assert_preserved(deployment)
    if kind == "static-copy":
        assert path.read_bytes() == b"preserved previous installed file"
    elif kind == "stale-link":
        assert path.readlink() == deployment.prefix / "releases/0.1.9" / relative
    else:
        assert not path.exists()


def test_binding_link_owner_and_parent_are_protected(deployment, monkeypatch):
    staged(deployment)
    binding = next(iter(deployment.bindings))
    os_stat = os.stat

    def wrong_owner(path, **kwargs):
        info = os_stat(path, **kwargs)
        if path == binding.name:
            fields = list(info)
            fields[4] = os.geteuid() + 1
            return os.stat_result(fields)
        return info

    with monkeypatch.context() as scope:
        scope.setattr(installer, "os", SimpleNamespace(**(vars(os) | {"stat": wrong_owner})))
        with pytest.raises(ValueError, match="release binding"):
            installer.switch("0.2.0")
    binding.parent.chmod(0o777)
    with pytest.raises(ValueError, match="untrusted deployment parent"):
        installer.switch("0.2.0")
    assert_preserved(deployment)


def test_two_release_switch_and_rollback_pin_helper_profile_and_units_together(deployment):
    previous = deployment.prefix / "releases/0.1.9"
    (previous / "preserved").unlink()
    previous.rmdir()
    helper_source = deployment.source / "scripts/container-service.py"
    original_helper = helper_source.read_bytes()
    old = copy.deepcopy(deployment.release)
    old["version"] = "0.1.9"
    helper_source.write_bytes(original_helper + b"\n# old selected release\n")
    old["files"]["scripts/container-service.py"] = digest(helper_source.read_bytes())
    installer.stage(deployment.source, old, deployment.default)
    new = copy.deepcopy(deployment.release)
    new["app_image"] = "sha256:" + "e" * 64
    helper_source.write_bytes(original_helper + b"\n# new selected release\n")
    new["files"]["scripts/container-service.py"] = digest(helper_source.read_bytes())
    installer.stage(deployment.source, new, deployment.default)
    helper_link = deployment.binding_root / "usr/local/libexec/hfcache-container-service"
    lock_inode = deployment.lock.stat().st_ino
    for release, marker in ((new, b"new"), (old, b"old"), (new, b"new")):
        installer.switch(release["version"])
        physical_root = helper_link.resolve().parents[1]
        assert physical_root == deployment.prefix / "releases" / release["version"]
        assert helper_link.read_bytes().endswith(marker + b" selected release\n")
        descriptor = os.open(physical_root / "rendered/runtime.json", os.O_RDONLY | os.O_NOFOLLOW)
        try:
            profile = json.loads(os.read(descriptor, 16384))
        finally:
            os.close(descriptor)
        assert profile["app_image"] == release["app_image"]
        assert deployment.lock.stat().st_ino == lock_inode
        for path, relative in deployment.bindings.items():
            assert path.resolve() == physical_root / relative
    assert installer._verify_stage(previous) == old
    assert installer._verify_stage(deployment.prefix / "releases/0.2.0") == new
