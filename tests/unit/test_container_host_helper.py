"""ADR150: API-only projected helper mount, protected host startup facts."""

import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

SCRIPT = Path(__file__).parents[2] / "scripts/container-service.py"
SPEC = importlib.util.spec_from_file_location("container_host_helper", SCRIPT)
assert SPEC is not None
assert SPEC.loader is not None
runtime = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runtime)
PROFILE = {
    "schema_version": 1,
    "service_uid": 983,
    "service_gid": 983,
    "app_image": "sha256:" + "a" * 64,
    "caddy_image": "sha256:" + "b" * 64,
}
BOOT = "8ee81fa2-685b-435b-a312-c8f4195036d0"


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def write(path, body, mode=0o644):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.chmod(0o600)
    path.write_bytes(body)
    path.chmod(mode)


def digest(body):
    return hashlib.sha256(body).hexdigest()


@pytest.fixture
def host(tmp_path, monkeypatch):
    profile = PROFILE | {"service_uid": os.geteuid() or 983, "service_gid": os.getegid() or 983}
    account = SimpleNamespace(
        pw_uid=profile["service_uid"], pw_gid=profile["service_gid"], pw_dir="/var/lib/hfcache"
    )
    monkeypatch.setattr(
        runtime.pwd, "getpwnam", lambda name: account if name == "hfcache" else None
    )
    monkeypatch.setenv("HOME", account.pw_dir)
    prefix = tmp_path / "opt"
    selected = prefix / "releases/0.2.0"
    configuration = selected / "rendered/server.toml"
    write(
        configuration,
        f'[host_helper]\nenabled=true\nprofile="rootless"\napi_host_gid={profile["service_gid"]}\n'.encode(),
    )
    raw_runtime = encoded(profile)
    write(selected / "rendered/runtime.json", raw_runtime)
    write(selected / "artifact-index.json", b'{"schema_version":1,"files":{}}')
    (prefix / "current").symlink_to("releases/0.2.0")
    deployment = tmp_path / "etc/deployment.json"
    value = {
        "schema_version": 1,
        "profile": "rootless",
        "release": {"version": "0.2.0", "selector_target": "releases/0.2.0"},
        "source": {},
        "api_principal": {"host_uid": profile["service_uid"], "host_gid": profile["service_gid"]},
        "bindings": {},
        "authority_files": {},
        "selinux_installation_sha256": "9" * 64,
        "profile_evidence": {
            "artifact_index_sha256": digest((selected / "artifact-index.json").read_bytes()),
            "runtime_profile_sha256": digest(raw_runtime),
            "app_image_sha256": "a" * 64,
            "caddy_image_sha256": "b" * 64,
        },
    }
    write(deployment, encoded(value))
    parent = tmp_path / "run/api"
    parent.mkdir(parents=True, mode=0o750)
    parent.chmod(0o750)
    if os.getegid() == 0:
        os.chown(parent, os.geteuid(), int(profile["service_gid"]))
    info = parent.stat()
    binding = {
        "schema_version": 1,
        "boot_id": BOOT,
        "helper_generation": "e" * 32,
        "deployment_sha256": digest(deployment.read_bytes()),
        "policy_sha256": "f" * 64,
        "parent": {
            "device": info.st_dev,
            "inode": info.st_ino,
            "uid": 0,
            "gid": profile["service_gid"],
            "mode": 0o750,
        },
        "helper": {"pid": 1234, "start_ticks": 999, "uid": 0, "gid": 0},
    }
    binding_file = parent / "binding.json"
    write(binding_file, encoded(binding), 0o440)
    if os.getegid() == 0:
        os.chown(binding_file, os.geteuid(), int(profile["service_gid"]))
    boot_file = tmp_path / "boot"
    write(boot_file, (BOOT + "\n").encode(), 0o444)
    for name, item in {
        "HOST_HELPER_PREFIX": prefix,
        "HOST_HELPER_DEPLOYMENT": deployment,
        "HOST_HELPER_PARENT": parent,
        "HOST_HELPER_BOOT": boot_file,
        "HOST_HELPER_OWNER": os.geteuid(),
        "RELEASE_ROOT": selected,
        "PROFILE_DIRECTORY": selected / "rendered",
    }.items():
        monkeypatch.setattr(runtime, name, item)
    return SimpleNamespace(
        profile=profile,
        account=account,
        prefix=prefix,
        selected=selected,
        configuration=configuration,
        deployment=deployment,
        index=value,
        parent=parent,
        binding=binding,
        binding_file=binding_file,
        boot=boot_file,
    )


def test_enabled_projection_uses_actual_host_group_and_projects_only_fixed_identity(host):
    value = runtime.host_helper_projection(host.profile)
    assert value == {
        "schema_version": 1,
        "profile": "rootless",
        "deployment_sha256": digest(host.deployment.read_bytes()),
        "boot_id": BOOT,
        "parent": {
            "device": host.parent.stat().st_dev,
            "inode": host.parent.stat().st_ino,
            "uid": 65534,
            "gid": 981,
            "mode": 488,
        },
        "peer": {"pid": 0, "uid": 65534, "gid": 65534},
    }
    argv = runtime.command(host.profile, "api", invocation_id="a" * 32, helper_projection=value)
    assert f"{host.parent}:/run/hfcache-host-helper/api:ro" in argv
    projected = next(
        argument.split("=", 2)[2]
        for argument in argv
        if argument.startswith("--env=HFCACHE_HOST_HELPER_PARENT=")
    )
    assert projected == encoded(value).decode()
    assert not any(
        "host-helper" in argument and (":rw" in argument or ",z" in argument) for argument in argv
    )


def test_enabled_api_preserves_hub_and_original_archive_lock_labels(host):
    """ADR150/159: Podman retains the independently provisioned object labels."""
    projection = runtime.host_helper_projection(host.profile)
    original = runtime.command(host.profile, "api", invocation_id="")
    enabled = runtime.command(host.profile, "api", invocation_id="", helper_projection=projection)
    for path in (
        "/var/lib/hfcache/hf-home",
        "/var/cache/hfcache",
        "/run/hfcache/hfcache.lock",
    ):
        assert f"{path}:{path}:rw,z" in original
        assert f"{path}:{path}:rw" in enabled
        assert f"{path}:{path}:rw,z" not in enabled

    # Every other command byte retains the original role's permissions. The
    # only additional authority is the existing read-only helper projection.
    expected = [
        item.removesuffix(",z")
        if item
        in {
            "/var/lib/hfcache/hf-home:/var/lib/hfcache/hf-home:rw,z",
            "/var/cache/hfcache:/var/cache/hfcache:rw,z",
            "/run/hfcache/hfcache.lock:/run/hfcache/hfcache.lock:rw,z",
        }
        else item
        for item in original
    ]
    projected = enabled.index(f"{host.parent}:/run/hfcache-host-helper/api:ro")
    assert enabled[projected - 1] == "--volume"
    assert enabled[projected + 1] == (
        "--env=HFCACHE_HOST_HELPER_PARENT=" + encoded(projection).decode()
    )
    assert enabled[: projected - 1] + enabled[projected + 2 :] == expected


@pytest.mark.parametrize(
    "body", [b"# no helper\n", b"[host_helper]\nenabled=false\n", b"[host_helper]\n"]
)
def test_absent_or_disabled_helper_retains_original_api_hub_relabel_arguments(host, body):
    write(host.configuration, body)
    projection = runtime.host_helper_projection(host.profile)
    assert projection is None
    original = runtime.command(host.profile, "api", invocation_id="")
    assert (
        runtime.command(host.profile, "api", invocation_id="", helper_projection=projection)
        == original
    )
    assert "/var/lib/hfcache/hf-home:/var/lib/hfcache/hf-home:rw,z" in original
    assert "/var/cache/hfcache:/var/cache/hfcache:rw,z" in original


@pytest.mark.parametrize("value", [None, True, 1, "", "9" * 63, "9" * 65, "G" * 64])
def test_helper_startup_requires_exact_selinux_installation_digest_even_with_fresh_binding(
    host, value
):
    host.index["selinux_installation_sha256"] = value
    write(host.deployment, encoded(host.index))
    host.binding["deployment_sha256"] = digest(host.deployment.read_bytes())
    write(host.binding_file, encoded(host.binding), 0o440)
    with pytest.raises(ValueError, match="protected host helper projection refused"):
        runtime.host_helper_projection(host.profile)


def test_helper_startup_rejects_missing_selinux_receipt_binding_without_legacy_fallback(host):
    del host.index["selinux_installation_sha256"]
    write(host.deployment, encoded(host.index))
    host.binding["deployment_sha256"] = digest(host.deployment.read_bytes())
    write(host.binding_file, encoded(host.binding), 0o440)
    with pytest.raises(ValueError, match="protected host helper projection refused"):
        runtime.host_helper_projection(host.profile)


@pytest.mark.parametrize(
    "body", [b"# no helper\n", b"[host_helper]\nenabled=false\n", b"[host_helper]\n"]
)
def test_disabled_mode_never_reads_deployment_parent_or_binding(host, monkeypatch, body):
    write(host.configuration, body)
    original = runtime._HelperProjectionRead.read
    opened = []

    def read(self, path, *args, **kwargs):
        opened.append(path)
        assert path == host.configuration
        return original(self, path, *args, **kwargs)

    monkeypatch.setattr(runtime._HelperProjectionRead, "read", read)
    assert runtime.host_helper_projection(host.profile) is None
    assert opened == [host.configuration]


@pytest.mark.parametrize("role", ["worker", "caddy", "client"])
def test_no_non_api_role_can_receive_helper_mount_or_environment(host, role):
    projection = runtime.host_helper_projection(host.profile)
    assert not any(
        "host-helper" in argument or "HFCACHE_HOST_HELPER" in argument
        for argument in runtime.command(host.profile, role)
    )
    with pytest.raises(ValueError, match="protected host helper projection refused"):
        runtime.command(host.profile, role, helper_projection=projection)


def test_explicit_invocation_is_pure_and_never_changes_shared_environment(monkeypatch):
    monkeypatch.setenv("INVOCATION_ID", "a" * 32)
    assert "--env=INVOCATION_ID=" + "a" * 32 in runtime.command(PROFILE, "api")
    assert "--env=INVOCATION_ID=" + "b" * 32 in runtime.command(
        PROFILE, "api", invocation_id="b" * 32
    )
    assert not any(
        "INVOCATION_ID" in argument
        for argument in runtime.command(PROFILE, "api", invocation_id="")
    )
    assert os.environ["INVOCATION_ID"] == "a" * 32


@pytest.mark.parametrize(
    "change", ["enabled-type", "native", "group", "inactive-parameters", "explicit-hash"]
)
def test_optin_is_explicit_and_malformed_or_wrong_profile_never_falls_back(host, change):
    body = host.configuration.read_text()
    if change == "enabled-type":
        body = body.replace("enabled=true", 'enabled="true"')
    elif change == "native":
        body = body.replace('profile="rootless"', 'profile="native"')
    elif change == "group":
        body = body.replace(f"api_host_gid={host.profile['service_gid']}", "api_host_gid=9999")
    elif change == "inactive-parameters":
        body = body.replace("enabled=true", "enabled=false")
    else:
        body += 'deployment_sha256="' + "0" * 64 + '"\n'
    write(host.configuration, body.encode())
    with pytest.raises(ValueError, match="protected host helper projection refused"):
        runtime.host_helper_projection(host.profile)


def test_optional_explicit_digest_is_checked_without_requiring_a_hash_cycle(host):
    body = (
        host.configuration.read_text()
        + 'deployment_sha256="'
        + digest(host.deployment.read_bytes())
        + '"\n'
    )
    write(host.configuration, body.encode())
    assert runtime.host_helper_projection(host.profile)["deployment_sha256"] == digest(
        host.deployment.read_bytes()
    )


@pytest.mark.parametrize(
    "change",
    [
        "deployment-digest",
        "boot",
        "parent-inode",
        "parent-mode",
        "parent-group",
        "helper-user",
        "profile",
        "principal",
        "runtime",
        "image",
        "index",
        "selector",
    ],
)
def test_each_protected_binding_join_is_required(host, change):  # noqa: PLR0912 - fixed independent joins
    if change in {
        "deployment-digest",
        "boot",
        "parent-inode",
        "parent-mode",
        "parent-group",
        "helper-user",
    }:
        value = copy.deepcopy(host.binding)
        if change == "deployment-digest":
            value["deployment_sha256"] = "0" * 64
        elif change == "boot":
            value["boot_id"] = "00000000-0000-0000-0000-000000000001"
        elif change == "parent-inode":
            value["parent"]["inode"] += 1
        elif change == "parent-mode":
            value["parent"]["mode"] = 0o755
        elif change == "parent-group":
            value["parent"]["gid"] += 1
        else:
            value["helper"]["uid"] = 983
        write(host.binding_file, encoded(value), 0o440)
    elif change == "selector":
        (host.prefix / "current").unlink()
        (host.prefix / "current").symlink_to("releases/9.9.9")
    else:
        value = copy.deepcopy(host.index)
        if change == "profile":
            value["profile"] = "native"
        elif change == "principal":
            value["api_principal"]["host_uid"] += 1
        elif change == "runtime":
            value["profile_evidence"]["runtime_profile_sha256"] = "0" * 64
        elif change == "index":
            value["profile_evidence"]["artifact_index_sha256"] = "0" * 64
        else:
            value["profile_evidence"]["app_image_sha256"] = "c" * 64
        write(host.deployment, encoded(value))
        binding = host.binding | {"deployment_sha256": digest(host.deployment.read_bytes())}
        write(host.binding_file, encoded(binding), 0o440)
    with pytest.raises(ValueError, match="protected host helper projection refused"):
        runtime.host_helper_projection(host.profile)


@pytest.mark.parametrize(
    "kind", ["symlink", "hardlink", "writable", "oversize", "fifo", "parent-alias"]
)
def test_unsafe_protected_deployment_is_refused_without_creation_or_repair(host, kind):
    path = host.deployment
    if kind == "symlink":
        other = path.with_name("target")
        path.rename(other)
        path.symlink_to(other)
    elif kind == "hardlink":
        os.link(path, path.with_name("second"))
    elif kind == "writable":
        path.chmod(0o666)
    elif kind == "oversize":
        path.write_bytes(b"x" * (1048576 + 1))
    elif kind == "fifo":
        path.unlink()
        os.mkfifo(path)
    else:
        original = path.parent
        moved = original.with_name("moved")
        original.rename(moved)
        original.symlink_to(moved)
    with pytest.raises((ValueError, OSError)):
        runtime.host_helper_projection(host.profile)


def test_projection_command_does_no_filesystem_reads_and_accepts_no_arbitrary_paths(
    host, monkeypatch
):
    projection = runtime.host_helper_projection(host.profile)

    def forbidden(*_args, **_kwargs):
        pytest.fail("pure argv builder performed I/O")

    monkeypatch.setattr(os, "open", forbidden)
    assert runtime.command(host.profile, "api", helper_projection=projection)
    bad = projection | {"socket": "/tmp/attacker.sock"}
    with pytest.raises(ValueError, match="protected host helper projection refused"):
        runtime.command(host.profile, "api", helper_projection=bad)


def test_enabled_missing_binding_is_not_a_silent_disabled_fallback(host):
    host.binding_file.unlink()
    with pytest.raises(FileNotFoundError):
        runtime.host_helper_projection(host.profile)
    assert not host.binding_file.exists()


def test_shared_projection_constructor_is_pure_and_matches_protected_loader(host, monkeypatch):
    expected = runtime.host_helper_projection(host.profile)

    def forbidden(*_args, **_kwargs):
        pytest.fail("pure projection constructor performed I/O")

    monkeypatch.setattr(os, "open", forbidden)
    assert (
        runtime.helper_parent_projection(
            expected["deployment_sha256"],
            BOOT,
            expected["parent"]["device"],
            expected["parent"]["inode"],
        )
        == expected
    )


@pytest.mark.parametrize(
    "kind",
    [
        "root-uid",
        "wrong-gid",
        "wrong-mode",
        "bool-inode",
        "peer-pid",
        "extra-field",
        "uppercase-hash",
        "wrong-boot",
    ],
)
def test_pure_command_rejects_unknown_or_forged_projection_shapes(host, kind):
    projection = runtime.host_helper_projection(host.profile)
    if kind == "root-uid":
        projection["parent"]["uid"] = 0
    elif kind == "wrong-gid":
        projection["parent"]["gid"] = 983
    elif kind == "wrong-mode":
        projection["parent"]["mode"] = 0o755
    elif kind == "bool-inode":
        projection["parent"]["inode"] = True
    elif kind == "peer-pid":
        projection["peer"]["pid"] = 1234
    elif kind == "extra-field":
        projection["peer"]["path"] = "/tmp/attacker"
    elif kind == "uppercase-hash":
        projection["deployment_sha256"] = "A" * 64
    else:
        projection["boot_id"] = "not-a-boot-id"
    with pytest.raises(ValueError, match=r"."):
        runtime.command(host.profile, "api", helper_projection=projection)


@pytest.mark.parametrize("role", ["api", "worker", "caddy", "client"])
def test_main_only_api_loads_protected_projection_before_original_exec(host, monkeypatch, role):
    calls = []
    projection = runtime.host_helper_projection(host.profile)
    monkeypatch.setattr(runtime, "load_profile", lambda: host.profile)
    monkeypatch.setattr(runtime, "archive_readonly", lambda: None)
    monkeypatch.setattr(runtime, "prepare_start", lambda *_args: None)

    def project(profile):
        assert profile == host.profile
        calls.append("projection")
        return projection

    def enabled(profile):
        assert profile == host.profile
        calls.append("worker-optin")
        return True

    def archive_lock(profile):
        assert profile == host.profile
        calls.append("archive-lock")

    class Executed(BaseException):
        pass

    def execute(_program, argv):
        calls.append(argv)
        raise Executed

    monkeypatch.setattr(runtime, "host_helper_projection", project)
    monkeypatch.setattr(runtime, "host_helper_enabled", enabled)
    monkeypatch.setattr(runtime, "host_helper_archive_lock", archive_lock)
    monkeypatch.setattr(runtime.os, "execv", execute)
    monkeypatch.setattr(runtime.sys, "argv", ["container-service", role])
    with pytest.raises(Executed):
        runtime.main()
    if role == "api":
        assert calls[:2] == ["projection", "archive-lock"]
        assert any("HFCACHE_HOST_HELPER_PARENT" in value for value in calls[2])
    elif role == "worker":
        assert calls[:2] == ["worker-optin", "archive-lock"]
        assert "/run/hfcache/hfcache.lock:/run/hfcache/hfcache.lock:rw" in calls[2]
        assert not any("HFCACHE_HOST_HELPER_PARENT" in value for value in calls[2])
    else:
        assert len(calls) == 1
        assert not any("HFCACHE_HOST_HELPER_PARENT" in value for value in calls[0])


def test_actual_concurrent_deployment_replacement_is_refused(host, monkeypatch):
    original = os.read
    changed = False

    def concurrent(descriptor, maximum):
        nonlocal changed
        body = original(descriptor, maximum)
        if not changed and b'"authority_files"' in body:
            changed = True
            host.deployment.unlink()
            write(host.deployment, body)
        return body

    monkeypatch.setattr(os, "read", concurrent)
    with pytest.raises(ValueError, match="protected host helper projection refused"):
        runtime.host_helper_projection(host.profile)
    assert changed


def test_failed_projection_read_drains_fds_and_preserves_unsafe_metadata(host):
    host.deployment.chmod(0o666)
    before = set(os.listdir("/proc/self/fd"))  # noqa: PTH208 - exact descriptor accounting
    for _ in range(3):
        with pytest.raises(ValueError, match="protected host helper projection refused"):
            runtime.host_helper_projection(host.profile)
    assert set(os.listdir("/proc/self/fd")) == before  # noqa: PTH208
    assert host.deployment.stat().st_mode & 0o777 == 0o666


@pytest.mark.parametrize("enabled", [False, True])
def test_worker_optin_reads_only_captured_server_configuration(host, monkeypatch, enabled):
    if not enabled:
        write(host.configuration, b"[host_helper]\nenabled=false\n")
    original = runtime._HelperProjectionRead.read
    opened = []

    def read(self, path, *args, **kwargs):
        opened.append(path)
        assert path == host.configuration
        return original(self, path, *args, **kwargs)

    host.deployment.unlink()
    host.binding_file.unlink()
    monkeypatch.setattr(runtime._HelperProjectionRead, "read", read)
    assert runtime.host_helper_enabled(host.profile) is enabled
    assert opened == [host.configuration]


@pytest.mark.parametrize(
    "body",
    [
        b"[host_helper]\nenabled=1\n",
        b"[host_helper]\nenabled=false\nprofile='rootless'\n",
        b"[host_helper]\nenabled=true\nprofile='native'\napi_host_gid=983\n",
        b"[host_helper]\nenabled=true\nprofile='rootless'\napi_host_gid=true\n",
        b"[host_helper]\nenabled=true\nprofile='rootless'\napi_host_gid=999999\n",
    ],
)
def test_worker_refuses_malformed_helper_optin(host, body):
    write(host.configuration, body)
    with pytest.raises(ValueError, match="protected host helper projection refused"):
        runtime.host_helper_enabled(host.profile)


def test_worker_refuses_invalid_optional_digest_without_reading_index(host):
    write(host.configuration, host.configuration.read_bytes() + b"deployment_sha256='bad'\n")
    host.deployment.unlink()
    with pytest.raises(ValueError, match="protected host helper projection refused"):
        runtime.host_helper_enabled(host.profile)


def test_worker_refuses_configuration_inode_replacement_during_capture(host, monkeypatch):
    original = os.read
    changed = False

    def replace(descriptor, maximum):
        nonlocal changed
        body = original(descriptor, maximum)
        if not changed and b"[host_helper]" in body:
            changed = True
            host.configuration.rename(host.configuration.with_suffix(".original"))
            write(host.configuration, body)
        return body

    monkeypatch.setattr(os, "read", replace)
    with pytest.raises(ValueError, match="protected host helper projection refused"):
        runtime.host_helper_enabled(host.profile)
    assert changed


def test_worker_preserves_only_archive_lock_bind_without_helper_authority(host, monkeypatch):
    original = runtime.command(host.profile, "worker", invocation_id="")

    def forbidden(*_args, **_kwargs):
        pytest.fail("pure worker argv builder performed I/O")

    monkeypatch.setattr(os, "open", forbidden)
    enabled = runtime.command(host.profile, "worker", invocation_id="", preserve_archive_lock=True)
    lock = "/run/hfcache/hfcache.lock:/run/hfcache/hfcache.lock:rw"
    assert enabled == [lock if item == lock + ",z" else item for item in original]
    assert not any("host-helper" in item or "HFCACHE_HOST_HELPER" in item for item in enabled)


@pytest.mark.parametrize("value", [None, 0, 1, "true", [], {}])
def test_archive_lock_preservation_requires_boolean_flag(host, value):
    with pytest.raises(ValueError, match="protected host helper projection refused"):
        runtime.command(host.profile, "worker", preserve_archive_lock=value)


@pytest.mark.parametrize("role", ["caddy", "client"])
def test_other_roles_refuse_archive_lock_preservation(host, role):
    with pytest.raises(ValueError, match="protected host helper projection refused"):
        runtime.command(host.profile, role, preserve_archive_lock=True)


@pytest.fixture
def archive_lock(host, monkeypatch):
    path = host.parent.parent / "hfcache/hfcache.lock"
    write(path, b"original-lock-body-is-not-read", 0o600)
    if os.geteuid() == 0:
        os.chown(path, host.profile["service_uid"], host.profile["service_gid"])
        os.chown(path.parent, host.profile["service_uid"], host.profile["service_gid"])
    path.parent.chmod(0o700)
    companion = path.with_name(path.name + ".intent")
    write(companion, b"", 0o600)
    if os.geteuid() == 0:
        os.chown(companion, host.profile["service_uid"], host.profile["service_gid"])
    context = b"system_u:object_r:hfcache_host_helper_archive_lock_t:s0"
    reads = []

    def getxattr(target, name, *, follow_symlinks):
        assert target in {path, companion}
        assert name == "security.selinux"
        assert follow_symlinks is False
        reads.append(target)
        return context

    monkeypatch.setattr(runtime, "HOST_HELPER_ARCHIVE_LOCK", path)
    monkeypatch.setattr(os, "getxattr", getxattr)
    return SimpleNamespace(path=path, context=context, reads=reads)


def test_enabled_launch_lock_check_reads_metadata_only_and_preserves_inode(
    host, archive_lock, monkeypatch
):
    original = os.open
    before = archive_lock.path.stat()

    def open_parent(path, *args, **kwargs):
        assert path not in {archive_lock.path, archive_lock.path.name}
        return original(path, *args, **kwargs)

    monkeypatch.setattr(os, "open", open_parent)
    runtime.host_helper_archive_lock(host.profile)
    after = archive_lock.path.stat()
    assert archive_lock.reads == [
        archive_lock.path,
        archive_lock.path.with_name(archive_lock.path.name + ".intent"),
    ]
    assert (before.st_dev, before.st_ino, before.st_mode) == (
        after.st_dev,
        after.st_ino,
        after.st_mode,
    )


@pytest.mark.parametrize(
    "context",
    [
        b"",
        b"system_u:object_r:container_file_t:s0",
        b"system_u:system_r:hfcache_host_helper_archive_lock_t:s0",
        b"system_u:object_r:hfcache_host_helper_archive_lock_t:s0:c1",
        b"system_u:object_r:hfcache_host_helper_archive_lock_t:s1",
        b"system_u:object_r:hfcache_host_helper_archive_lock_t:s0\n",
        b"system_u:object_r:hfcache_host_helper_archive_lock_t:s0\0\0",
        b"\xff:object_r:hfcache_host_helper_archive_lock_t:s0",
        b"x" * 4097,
    ],
)
def test_enabled_launch_refuses_unprovisioned_or_unknown_lock_context(
    host, archive_lock, monkeypatch, context
):
    monkeypatch.setattr(os, "getxattr", lambda *_args, **_kwargs: context)
    with pytest.raises(ValueError, match="protected host helper projection refused"):
        runtime.host_helper_archive_lock(host.profile)


@pytest.mark.parametrize("change", ["missing", "symlink", "hardlink", "mode", "uid", "gid"])
def test_enabled_launch_refuses_unsafe_original_lock(host, archive_lock, change):
    profile = host.profile.copy()
    path = archive_lock.path
    if change == "missing":
        path.unlink()
    elif change == "symlink":
        original = path.with_suffix(".original")
        path.rename(original)
        path.symlink_to(original)
    elif change == "hardlink":
        os.link(path, path.with_suffix(".alias"))
    elif change == "mode":
        path.chmod(0o640)
    else:
        profile["service_" + change] += 1
    with pytest.raises((ValueError, OSError)):
        runtime.host_helper_archive_lock(profile)
    assert archive_lock.reads == []


def test_enabled_launch_refuses_lock_inode_swap_during_context_read(
    host, archive_lock, monkeypatch
):
    def swapped(*_args, **_kwargs):
        archive_lock.path.rename(archive_lock.path.with_suffix(".original"))
        write(archive_lock.path, b"replacement", 0o600)
        return archive_lock.context

    monkeypatch.setattr(os, "getxattr", swapped)
    with pytest.raises(ValueError, match="protected host helper projection refused"):
        runtime.host_helper_archive_lock(host.profile)


@pytest.mark.parametrize("role", ["api", "worker"])
def test_invalid_enabled_lock_refuses_before_engine_mutation(host, monkeypatch, role):
    def forbidden(*_args, **_kwargs):
        pytest.fail("invalid lock reached engine or archive operation")

    def refused(_profile):
        message = "unprovisioned original lock"
        raise ValueError(message)

    monkeypatch.setattr(runtime, "load_profile", lambda: host.profile)
    monkeypatch.setattr(runtime, "host_helper_archive_lock", refused)
    monkeypatch.setattr(runtime, "archive_readonly", forbidden)
    monkeypatch.setattr(runtime, "prepare_start", forbidden)
    monkeypatch.setattr(runtime.os, "execv", forbidden)
    monkeypatch.setattr(runtime.sys, "argv", ["container-service", role])
    assert runtime.main() == 20


@pytest.mark.parametrize("role", ["api", "worker"])
def test_disabled_launch_never_observes_lock_or_helper_authority(host, monkeypatch, role):
    write(host.configuration, b"[host_helper]\nenabled=false\n")
    host.deployment.unlink()
    host.binding_file.unlink()

    def forbidden(*_args, **_kwargs):
        pytest.fail("disabled helper reached archive-lock label check")

    class Executed(BaseException):
        pass

    def execute(_program, argv):
        assert "/run/hfcache/hfcache.lock:/run/hfcache/hfcache.lock:rw,z" in argv
        raise Executed

    monkeypatch.setattr(runtime, "load_profile", lambda: host.profile)
    monkeypatch.setattr(runtime, "host_helper_archive_lock", forbidden)
    monkeypatch.setattr(runtime, "archive_readonly", lambda: None)
    monkeypatch.setattr(runtime, "prepare_start", lambda *_args: None)
    monkeypatch.setattr(runtime.os, "execv", execute)
    monkeypatch.setattr(runtime.sys, "argv", ["container-service", role])
    with pytest.raises(Executed):
        runtime.main()


def test_bound_alternate_home_requires_matching_measured_account_and_effective_home(
    host, monkeypatch
):
    home = "/var/lib/hfcache/container-home"
    host.account.pw_dir = home
    host.index["profile_evidence"]["account_home"] = home
    write(host.deployment, encoded(host.index))
    host.binding["deployment_sha256"] = digest(host.deployment.read_bytes())
    write(host.binding_file, encoded(host.binding), 0o440)
    monkeypatch.setenv("HOME", home)
    assert runtime.host_helper_projection(host.profile)["deployment_sha256"] == digest(
        host.deployment.read_bytes()
    )
    monkeypatch.setenv("HOME", "/var/lib/hfcache")
    with pytest.raises(ValueError, match="protected host helper projection refused"):
        runtime.host_helper_projection(host.profile)


@pytest.mark.parametrize("home", ["/tmp/alternate", "/var/lib/hfcache/container-home/", True])
def test_projection_rejects_unreviewed_or_alias_home_before_podman(host, home):
    host.index["profile_evidence"]["account_home"] = home
    write(host.deployment, encoded(host.index))
    host.binding["deployment_sha256"] = digest(host.deployment.read_bytes())
    write(host.binding_file, encoded(host.binding), 0o440)
    with pytest.raises(ValueError, match="protected host helper projection refused"):
        runtime.host_helper_projection(host.profile)


@pytest.mark.parametrize("mode", ["guarded-readonly", "manual-writer"])
def test_schema2_projection_requires_exact_sibling_and_independent_mode(host, monkeypatch, mode):
    profile = host.profile | {"schema_version": 2, "archive_mode": mode}
    selected = host.selected.with_name("0.2.0-" + mode)
    host.selected.rename(selected)
    (host.prefix / "current").unlink()
    (host.prefix / "current").symlink_to("releases/" + selected.name)
    monkeypatch.setattr(runtime, "RELEASE_ROOT", selected)
    monkeypatch.setattr(runtime, "PROFILE_DIRECTORY", selected / "rendered")
    write(selected / "rendered/runtime.json", encoded(profile))
    host.index["release"]["release_id"] = selected.name
    host.index["release"]["selector_target"] = "releases/" + selected.name
    host.index["profile_evidence"]["archive_mode"] = mode
    host.index["profile_evidence"]["runtime_profile_sha256"] = digest(encoded(profile))
    write(host.deployment, encoded(host.index))
    host.binding["deployment_sha256"] = digest(host.deployment.read_bytes())
    write(host.binding_file, encoded(host.binding), 0o440)
    assert (
        runtime.host_helper_projection(profile)["deployment_sha256"]
        == host.binding["deployment_sha256"]
    )
    host.index["profile_evidence"]["archive_mode"] = (
        "manual-writer" if mode == "guarded-readonly" else "guarded-readonly"
    )
    write(host.deployment, encoded(host.index))
    host.binding["deployment_sha256"] = digest(host.deployment.read_bytes())
    write(host.binding_file, encoded(host.binding), 0o440)
    with pytest.raises(ValueError, match="protected host helper projection refused"):
        runtime.host_helper_projection(profile)
