"""Decision 127: exact artifacts, local-only engine and preserved executor evidence."""

import errno
import importlib.util
import io
import json
import os
import subprocess
import tarfile
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
IMAGE = "sha256:" + "a" * 64
CLOSURE = b"example==1.0 \\\n    --hash=sha256:" + b"b" * 64 + b"\n"


def load_script(name):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), ROOT / "scripts" / name)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def builder():
    return load_script("build-container.py")


@pytest.fixture
def probe():
    return load_script("check-container-worker.py")


def wheel_file(tmp_path, *, name="hfcache", version="0.1.10"):
    body = io.BytesIO()
    with zipfile.ZipFile(body, "w") as archive:
        archive.writestr(
            f"{name}-{version}.dist-info/METADATA", f"Name: {name}\nVersion: {version}\n"
        )
    wheel = tmp_path / f"hfcache-{version}-py3-none-any.whl"
    wheel.write_bytes(body.getvalue())
    return wheel


def python_file(builder, tmp_path, monkeypatch, members=None):
    body = io.BytesIO()
    with tarfile.open(fileobj=body, mode="w:gz") as archive:
        if members is None:
            executable = tarfile.TarInfo("python/bin/python3.14")
            executable.mode = 0o755
            members = [(executable, b"synthetic executable fixture")]
        for item, content in members:
            item.size = len(content)
            archive.addfile(item, io.BytesIO(content))
    path = tmp_path / "python.tar.gz"
    path.write_bytes(body.getvalue())
    monkeypatch.setitem(builder.PYTHON_DISTRIBUTION, "sha256", builder.digest(body.getvalue()))
    return path


@pytest.mark.parametrize("expected", ["0" * 64, "SHA256:bad", "A" * 64, ""])
def test_wheel_requires_explicit_matching_digest_before_any_builder(builder, tmp_path, expected):
    wheel = wheel_file(tmp_path)
    with pytest.raises(ValueError, match="SHA256"):
        builder.wheel_input(wheel, expected)
    assert wheel.exists()


@pytest.mark.parametrize(("name", "version"), [("other", "0.1.10"), ("hfcache", "unsafe version")])
def test_authenticated_wrong_wheel_is_refused(builder, tmp_path, name, version):
    wheel = wheel_file(tmp_path, name=name, version=version)
    with pytest.raises(ValueError, match="exact hfcache"):
        builder.wheel_input(wheel, builder.digest(wheel.read_bytes()))


def test_symlink_wheel_is_refused_without_following_it(builder, tmp_path):
    original = wheel_file(tmp_path)
    alias = tmp_path / "alias.whl"
    alias.symlink_to(original)
    with pytest.raises(ValueError, match="symlinks"):
        builder.wheel_input(alias, builder.digest(original.read_bytes()))


@pytest.mark.parametrize(
    ("path", "table"),
    [
        ("/srv/hfcache/a", "1 0 0:1 / / rw - ext4 /dev/a rw"),
        (
            "/mnt/alias/a",
            "1 0 0:1 / / rw - ext4 /dev/a rw\n2 1 0:2 / /mnt/alias ro - nfs4 host:/a ro",
        ),
        ("/mnt/cifs/a", "1 0 0:1 / / rw - cifs host:/a rw"),
    ],
)
def test_nas_or_nonlocal_alias_is_rejected_before_any_target_stat(
    builder, monkeypatch, path, table
):
    def forbidden(*_):
        pytest.fail("must refuse from lexical path/mount table before target I/O")

    monkeypatch.setattr(Path, "lstat", forbidden)
    with pytest.raises(ValueError, match="local"):
        builder.local_path(Path(path), mountinfo=table)


@pytest.mark.parametrize(
    "body",
    [
        b"",
        b"# comments only\n",
        b"example==1.0\n",
        b"-e /home/example\n",
        b"example @ https://example/a\n",
        b"--index-url https://example\n",
    ],
)
def test_unhashed_or_authority_bearing_export_is_refused(builder, body):
    with pytest.raises(ValueError, match="export"):
        builder.hashed_requirements(body)


def fake_build_tools(builder, monkeypatch, context, *, fail_build=False):
    calls = []
    monkeypatch.setattr(builder.os, "geteuid", lambda: 1000)
    monkeypatch.setattr(builder, "executable", lambda name: f"/usr/bin/{name}")

    def run(arguments, **kwargs):
        calls.append(arguments)
        if arguments[0].endswith("/uv"):
            assert "--locked" in arguments
            assert "--no-emit-project" in arguments
            assert arguments.count("--extra") == 2
            assert "--no-hashes" not in arguments
            return subprocess.CompletedProcess(arguments, 0, stdout=CLOSURE)
        if arguments[0].endswith("/git"):
            return subprocess.CompletedProcess(
                arguments, 0, stdout="c" * 40 if "rev-parse" in arguments else ""
            )
        assert arguments[:3] == ["/usr/bin/podman", "--remote=false", "build"]
        assert "--pull=never" in arguments
        assert "--http-proxy=false" in arguments
        if fail_build:
            raise subprocess.CalledProcessError(125, arguments)
        (context / "image.id").write_text(IMAGE)
        return subprocess.CompletedProcess(arguments, 0)

    monkeypatch.setattr(builder.subprocess, "run", run)
    return calls


def test_exact_wheel_closure_and_final_identity_are_recorded_without_source_copy(
    builder, monkeypatch, tmp_path
):
    wheel = wheel_file(tmp_path)
    expected = builder.digest(wheel.read_bytes())
    context = tmp_path / "new-build"
    interpreter = python_file(builder, tmp_path, monkeypatch)
    calls = fake_build_tools(builder, monkeypatch, context)
    result = builder.build(
        wheel, expected, context, "localhost/hfcache:proof", python_archive=interpreter
    )
    assert result["image_id"] == IMAGE
    assert result["wheel_sha256"] == expected
    assert result["dependency_closure_sha256"] == builder.digest(CLOSURE)
    assert json.loads((context / "build.json").read_text()) == result
    assert (context / "wheels" / wheel.name).read_bytes() == wheel.read_bytes()
    assert (
        f"/build/wheels/{wheel.name} --hash=sha256:{expected}"
        in (context / "requirements.txt").read_text()
    )
    assert sorted(path.name for path in context.iterdir()) == [
        "Containerfile",
        "build.json",
        "image.id",
        "inputs.json",
        "python",
        "requirements.txt",
        "wheels",
    ]
    assert len(calls) == 4


def test_failed_build_preserves_authenticated_inputs_and_no_success_manifest(
    builder, monkeypatch, tmp_path
):
    wheel = wheel_file(tmp_path)
    context = tmp_path / "failed"
    interpreter = python_file(builder, tmp_path, monkeypatch)
    fake_build_tools(builder, monkeypatch, context, fail_build=True)
    with pytest.raises(subprocess.CalledProcessError):
        builder.build(
            wheel,
            builder.digest(wheel.read_bytes()),
            context,
            "localhost/hfcache:proof",
            python_archive=interpreter,
        )
    assert (context / "inputs.json").exists()
    assert (context / "wheels" / wheel.name).read_bytes() == wheel.read_bytes()
    assert not (context / "build.json").exists()


def test_provenance_hashes_the_validated_context_recipe_even_if_source_changes(
    builder, monkeypatch, tmp_path
):
    original = (ROOT / "packaging/containers/Containerfile").read_bytes()
    repository = tmp_path / "source"
    recipe = repository / "packaging/containers/Containerfile"
    recipe.parent.mkdir(parents=True)
    recipe.write_bytes(original)
    (repository / "uv.lock").write_bytes(b"synthetic lock input")
    monkeypatch.setattr(builder, "REPOSITORY", repository)
    wheel = wheel_file(tmp_path)
    interpreter = python_file(builder, tmp_path, monkeypatch)
    context = tmp_path / "context"
    fake_build_tools(builder, monkeypatch, context)
    run = builder.subprocess.run

    def source_changes(arguments, **kwargs):
        if arguments[0].endswith("/uv"):
            recipe.write_bytes(b"different source bytes after capture")
        return run(arguments, **kwargs)

    monkeypatch.setattr(builder.subprocess, "run", source_changes)
    result = builder.build(
        wheel,
        builder.digest(wheel.read_bytes()),
        context,
        "localhost/hfcache:proof",
        python_archive=interpreter,
    )
    assert (context / "Containerfile").read_bytes() == original
    assert result["containerfile_sha256"] == builder.digest(original)
    assert builder.digest(recipe.read_bytes()) != result["containerfile_sha256"]


def test_existing_context_is_preserved_before_export(builder, monkeypatch, tmp_path):
    wheel = wheel_file(tmp_path)
    context = tmp_path / "existing"
    context.mkdir()
    (context / "unknown").write_bytes(b"evidence")
    interpreter = python_file(builder, tmp_path, monkeypatch)
    calls = fake_build_tools(builder, monkeypatch, context)
    with pytest.raises(FileExistsError):
        builder.build(
            wheel,
            builder.digest(wheel.read_bytes()),
            context,
            "localhost/hfcache:proof",
            python_archive=interpreter,
        )
    assert calls == []
    assert (context / "unknown").read_bytes() == b"evidence"


@pytest.mark.parametrize(
    "tag", ["registry.example/hfcache:latest", "localhost/hfcache:bad tag", "localhost/other:tag"]
)
def test_builder_cannot_select_remote_publication_tag(builder, monkeypatch, tmp_path, tag):
    monkeypatch.setattr(builder.os, "geteuid", lambda: 1000)
    with pytest.raises(ValueError, match="local"):
        builder.build(
            tmp_path / "missing",
            "a" * 64,
            tmp_path / "new",
            tag,
            python_archive=tmp_path / "unused",
        )
    assert not (tmp_path / "new").exists()


def test_root_builder_refuses_before_artifact_or_engine_io(builder, monkeypatch, tmp_path):
    monkeypatch.setattr(builder.os, "geteuid", lambda: 0)
    with pytest.raises(ValueError, match="never root"):
        builder.build(
            tmp_path / "missing",
            "a" * 64,
            tmp_path / "new",
            "localhost/hfcache:proof",
            python_archive=tmp_path / "unused",
        )


def test_python_hash_mismatch_refuses_before_parse_context_or_engine(
    builder, monkeypatch, tmp_path
):
    interpreter = tmp_path / "python.tar.gz"
    interpreter.write_bytes(b"untrusted archive bytes")
    monkeypatch.setattr(builder.tarfile, "open", lambda **_: pytest.fail("unauthenticated parse"))
    wheel = wheel_file(tmp_path)
    context = tmp_path / "new"
    calls = fake_build_tools(builder, monkeypatch, context)
    with pytest.raises(ValueError, match="Python archive SHA256"):
        builder.build(
            wheel,
            builder.digest(wheel.read_bytes()),
            context,
            "localhost/hfcache:proof",
            python_archive=interpreter,
        )
    assert not context.exists()
    assert calls == []
    assert interpreter.read_bytes() == b"untrusted archive bytes"


@pytest.mark.parametrize("kind", ["symlink", "hardlink", "fifo", "directory", "empty"])
def test_python_archive_refuses_aliases_and_nonregular_inputs(builder, tmp_path, kind):
    path = tmp_path / "python.tar.gz"
    if kind in {"symlink", "hardlink"}:
        original = tmp_path / "original"
        original.write_bytes(b"preserved source")
        path.symlink_to(original) if kind == "symlink" else path.hardlink_to(original)
    elif kind == "fifo":
        os.mkfifo(path)
    elif kind == "directory":
        path.mkdir()
    else:
        path.touch()
    with pytest.raises((OSError, ValueError)):
        builder.python_archive_input(path)
    assert path.lstat()


def test_safe_internal_python_links_remain_usable(builder, monkeypatch, tmp_path):
    executable = tarfile.TarInfo("python/bin/python3.14")
    executable.mode = 0o755
    link = tarfile.TarInfo("python/bin/python3")
    link.type = tarfile.SYMTYPE
    link.linkname = "python3.14"
    archive = python_file(builder, tmp_path, monkeypatch, [(executable, b"fixture"), (link, b"")])
    context = tmp_path / "context"
    context.mkdir()
    builder.extract_python(builder.python_archive_input(archive), context)
    assert (context / "python/bin/python3").is_symlink()
    assert (context / "python/bin/python3").read_bytes() == b"fixture"


@pytest.mark.parametrize("drift", ["base", "donor", "ca"])
def test_recipe_drift_refuses_before_context_or_engine(builder, monkeypatch, tmp_path, drift):
    recipe = (ROOT / "packaging/containers/Containerfile").read_text()
    before, after = {
        "base": ("FROM " + builder.PYTHON_BASE, "FROM docker.io/other:latest"),
        "donor": ("COPY --from=" + builder.UV_BUILDER, "COPY --from=docker.io/other:latest"),
        "ca": (builder.CA_SHA256, "0" * 64),
    }[drift]
    fake_root = tmp_path / "repository"
    replacement = fake_root / "packaging/containers/Containerfile"
    replacement.parent.mkdir(parents=True)
    replacement.write_text(recipe.replace(before, after))
    monkeypatch.setattr(builder, "REPOSITORY", fake_root)
    wheel = wheel_file(tmp_path)
    interpreter = python_file(builder, tmp_path, monkeypatch)
    context = tmp_path / "context"
    calls = fake_build_tools(builder, monkeypatch, context)
    with pytest.raises(ValueError, match="Containerfile differs"):
        builder.build(
            wheel,
            builder.digest(wheel.read_bytes()),
            context,
            "localhost/hfcache:proof",
            python_archive=interpreter,
        )
    assert not context.exists()
    assert calls == []


@pytest.mark.parametrize(
    "name", ["/python/escape", "python/../escape", "other/bin/python3.14", "python/evil\\name"]
)
def test_interpreter_tree_refuses_uncontained_names(builder, monkeypatch, tmp_path, name):
    item = tarfile.TarInfo(name)
    archive = python_file(builder, tmp_path, monkeypatch, [(item, b"unexplained")])
    context = tmp_path / "context"
    context.mkdir()
    with pytest.raises(ValueError, match="unsafe Python"):
        builder.extract_python(builder.python_archive_input(archive), context)
    assert list((context / "python").iterdir()) == []
    assert not (tmp_path / "escape").exists()


@pytest.mark.parametrize("target", ["/etc/passwd", "../../escape", "../requirements.txt"])
def test_interpreter_symlinks_cannot_escape_the_python_subtree(
    builder, monkeypatch, tmp_path, target
):
    link = tarfile.TarInfo("python/alias")
    link.type = tarfile.SYMTYPE
    link.linkname = target
    archive = python_file(builder, tmp_path, monkeypatch, [(link, b"")])
    context = tmp_path / "context"
    context.mkdir()
    sentinel = context / "requirements.txt"
    sentinel.write_bytes(b"preserve other context inputs")
    with pytest.raises(tarfile.FilterError):
        builder.extract_python(builder.python_archive_input(archive), context)
    assert sentinel.read_bytes() == b"preserve other context inputs"
    assert not (context / "python/alias").is_symlink()


@pytest.mark.parametrize("kind", [tarfile.LNKTYPE, tarfile.FIFOTYPE, tarfile.CHRTYPE])
def test_interpreter_hardlinks_and_special_files_never_gain_authority(
    builder, monkeypatch, tmp_path, kind
):
    item = tarfile.TarInfo("python/unsafe")
    item.type = kind
    item.linkname = "python/other"
    archive = python_file(builder, tmp_path, monkeypatch, [(item, b"")])
    context = tmp_path / "context"
    context.mkdir()
    with pytest.raises(ValueError, match="unsafe Python"):
        builder.extract_python(builder.python_archive_input(archive), context)
    assert list((context / "python").iterdir()) == []


@pytest.mark.parametrize("limit", ["members", "expanded", "duplicate"])
def test_interpreter_extraction_has_count_size_and_duplicate_bounds(
    builder, monkeypatch, tmp_path, limit
):
    first = tarfile.TarInfo("python/first")
    second = tarfile.TarInfo("python/first" if limit == "duplicate" else "python/second")
    archive = python_file(builder, tmp_path, monkeypatch, [(first, b"first"), (second, b"second")])
    if limit == "members":
        monkeypatch.setattr(builder, "_MAX_PYTHON_MEMBERS", 1)
    if limit == "expanded":
        monkeypatch.setattr(builder, "_MAX_PYTHON_EXPANDED", 1)
    context = tmp_path / "context"
    context.mkdir()
    with pytest.raises(ValueError, match="tree bounds"):
        builder.extract_python(builder.python_archive_input(archive), context)
    assert list((context / "python").iterdir()) == []


def test_every_app_build_stage_is_pinned_micro_and_foreign_inputs_are_only_binary_or_ca():
    pins = json.loads((ROOT / "packaging/containers/images.json").read_text())
    recipe = (ROOT / "packaging/containers/Containerfile").read_text()
    stages = [line.split()[1] for line in recipe.splitlines() if line.startswith("FROM ")]
    assert stages
    assert set(stages) == {pins["python"], pins["build"]}
    assert all(
        stage.startswith("registry.access.redhat.com/ubi10/ubi-micro@sha256:") for stage in stages
    )
    assert f"COPY --from={pins['uv_binary_image']} /uv /usr/local/bin/uv" in recipe
    assert (
        f"COPY --from={pins['ca_bundle_image']} "
        "/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem /etc/ssl/cert.pem" in recipe
    )
    assert pins["ca_bundle_sha256"] in recipe
    assert "COPY python/ /opt/hfcache/python/" in recipe


def test_probe_uses_bounded_isolated_payload_without_replacement_or_auto_cleanup(probe, tmp_path):
    arguments = probe.base_arguments(
        IMAGE, "hfcache-proof-fixture-worker", tmp_path / "seccomp", "marker"
    )
    for required in (
        "--pull=never",
        "--http-proxy=false",
        "--userns=keep-id:uid=981,gid=981",
        "--network=none",
        "--read-only",
        "--cap-drop=all",
        "--security-opt=no-new-privileges",
    ):
        assert required in arguments
    for forbidden in ("--replace", "--rm", "--init", "--env-host", "--privileged"):
        assert forbidden not in arguments
    assert not any("label=disable" in item or "/srv/" in item for item in arguments)
    for mask in probe._MASKS:
        assert f"--tmpfs={mask}:ro,size=4096,mode=000,nodev,nosuid,noexec" in arguments


def test_every_probe_engine_exchange_is_explicitly_local(probe, monkeypatch):
    captured = []

    def run(arguments, **kwargs):
        captured.append(arguments)
        return subprocess.CompletedProcess(arguments, 0, stdout="{}")

    monkeypatch.setattr(probe.subprocess, "run", run)
    monkeypatch.setenv("CONTAINER_HOST", "ssh://must-never-be-used")
    probe.engine("info", "--format=json")
    probe.engine("stop", "--time", "-1", "hfcache-proof-fixture-worker")
    assert all(arguments[:2] == ["/usr/bin/podman", "--remote=false"] for arguments in captured)
    assert captured[-1][2:] == ["stop", "--time", "-1", "hfcache-proof-fixture-worker"]


def test_unknown_container_identity_is_never_stopped_or_removed(probe, monkeypatch):
    def inspect(*arguments, **kwargs):
        assert arguments[0] == "inspect"
        return subprocess.CompletedProcess(
            arguments,
            0,
            stdout=json.dumps(
                [{"Config": {"Labels": {"io.hfcache.proof": "other"}}, "Image": IMAGE}]
            ),
        )

    monkeypatch.setattr(probe, "engine", inspect)
    with pytest.raises(ValueError, match="preserve"):
        probe.inspect_owned("hfcache-proof-fixture-worker", "expected", IMAGE)


@pytest.mark.parametrize("actual", [IMAGE, IMAGE.removeprefix("sha256:")])
def test_inspect_accepts_exact_podman_bare_or_prefixed_image_identity(probe, monkeypatch, actual):
    data = {
        "Id": "c" * 64,
        "Config": {"Labels": {"io.hfcache.proof": "expected"}},
        "Image": actual,
        "State": {"Running": False, "Pid": 0},
    }
    monkeypatch.setattr(
        probe, "engine", lambda *_: subprocess.CompletedProcess([], 0, stdout=json.dumps([data]))
    )
    assert probe.inspect_owned("hfcache-proof-fixture-worker", "expected", IMAGE) == data


@pytest.mark.parametrize(
    "change",
    [
        {"Id": "unexpected"},
        {"State": {}},
        {"State": {"Running": "true", "Pid": 123}},
        {"State": {"Running": True, "Pid": 0}},
    ],
)
def test_malformed_container_identity_never_authorizes_proof_drain(probe, monkeypatch, change):
    data = {
        "Id": "c" * 64,
        "Config": {"Labels": {"io.hfcache.proof": "expected"}},
        "Image": IMAGE,
        "State": {"Running": True, "Pid": 123},
    } | change
    calls = []

    def engine(*arguments, **kwargs):
        calls.append(arguments)
        assert arguments[0] == "inspect"
        return subprocess.CompletedProcess([], 0, stdout=json.dumps([data]))

    monkeypatch.setattr(probe, "engine", engine)
    with pytest.raises(ValueError, match="preserve"):
        probe.inspect_owned("hfcache-proof-fixture-worker", "expected", IMAGE)
    assert len(calls) == 1


def test_proof_failure_records_fixed_stage_and_class_without_exception_text(
    probe, monkeypatch, tmp_path
):
    workspace = tmp_path / "new"

    def fail(image, path, profile, trace):
        path.mkdir(mode=0o700)
        trace.update({"workspace": str(path), "stage": "isolation"})
        message = "private-marker-that-must-never-be-recorded"
        raise ValueError(message)

    monkeypatch.setattr(probe, "_prove", fail)
    with pytest.raises(ValueError, match="private-marker"):
        probe.prove(IMAGE, workspace, tmp_path / "seccomp")
    body = (workspace / "failure.json").read_text()
    assert "private-marker" not in body
    assert json.loads(body) == {
        "schema_version": 1,
        "stage": "isolation",
        "error_class": "ValueError",
        "status": "failed",
    }


def test_payload_reports_fixed_ip_check_when_a_policy_allows_ip_creation(probe, capsys):
    """The default-policy composition defect must fail proof, never weaken it."""
    original_import = __import__
    fake_os = SimpleNamespace(
        geteuid=lambda: 981, getegid=lambda: 981, environ={"HF_HUB_OFFLINE": "1"}
    )
    fake_socket = SimpleNamespace(
        AF_INET=2,
        AF_INET6=10,
        SOCK_STREAM=1,
        socket=lambda *_: SimpleNamespace(close=lambda: None),
    )

    def imports(name, *args, **kwargs):
        if name == "os":
            return fake_os
        if name == "socket":
            return fake_socket
        return original_import(name, *args, **kwargs)

    namespace = {"__builtins__": {**vars(__import__("builtins")), "__import__": imports}}
    with pytest.raises(SystemExit, match="1"):
        exec(probe._ISOLATION, namespace)
    assert json.loads(capsys.readouterr().out) == {
        "failed_check": "ip4_socket",
        "error_class": "AssertionError",
    }


def test_payload_accepts_measured_enosys_denial_and_records_both_socket_errnos(probe, capsys):
    """The installed default filter intentionally returns ENOSYS, not EPERM."""
    original_import = __import__

    def denied(*_):
        raise PermissionError(errno.EACCES, "synthetic inaccessible file")

    def socket_denied(*_):
        raise OSError(errno.ENOSYS, "synthetic filter denial")

    def busy(*_):
        raise BlockingIOError

    fake_os = SimpleNamespace(
        geteuid=lambda: 981,
        getegid=lambda: 981,
        getpid=lambda: 1,
        environ={"HF_HUB_OFFLINE": "1"},
        open=denied,
        O_RDONLY=0,
        O_NOFOLLOW=1,
        stat=lambda path: SimpleNamespace(st_ino=3 if path == "/run/hfcache/hfcache.lock" else 0),
        statvfs=lambda _: SimpleNamespace(f_flag=1),
        ST_RDONLY=1,
    )
    modules = {
        "os": fake_os,
        "socket": SimpleNamespace(AF_INET=2, AF_INET6=10, SOCK_STREAM=1, socket=socket_denied),
        "fcntl": SimpleNamespace(LOCK_EX=2, LOCK_NB=4, flock=busy),
        "sys": SimpleNamespace(argv=["-c", "/source", "1", "1", "3"]),
    }

    def imports(name, *args, **kwargs):
        return modules[name] if name in modules else original_import(name, *args, **kwargs)

    def opened(path, mode):
        assert path in {"/proc/1/cmdline", "/run/hfcache/hfcache.lock"}
        return io.BytesIO(b"hfcache.verification_worker")

    namespace = {
        "__builtins__": {**vars(__import__("builtins")), "__import__": imports, "open": opened}
    }
    exec(probe._ISOLATION, namespace)
    result = json.loads(capsys.readouterr().out)
    assert result["ip_sockets_denied"] is True
    assert result["ip_socket_errno"] == {"ip4_socket": errno.ENOSYS, "ip6_socket": errno.ENOSYS}


@pytest.mark.parametrize("rootless", [False, None])
def test_nonroot_engine_or_remote_graphroot_is_not_proof(probe, monkeypatch, rootless):
    monkeypatch.setattr(probe.os, "geteuid", lambda: 1000)
    monkeypatch.setattr(
        probe,
        "engine",
        lambda *_: subprocess.CompletedProcess(
            [],
            0,
            stdout=json.dumps(
                {
                    "host": {"security": {"rootless": rootless}},
                    "store": {"graphRoot": "/srv/hfcache/forbidden"},
                }
            ),
        ),
    )
    with pytest.raises(ValueError, match="rootless"):
        probe.rootless_storage()


def _ready_text(**changes):
    fields = {
        "Type": "notify",
        "NotifyAccess": "all",
        "ActiveState": "active",
        "SubState": "running",
        "MainPID": "123",
        "ControlGroup": "/user.slice/user-1000.slice/user@1000.service/app.slice/proof.service",
        "ExecMainStartTimestampMonotonic": "100",
        "ActiveEnterTimestampMonotonic": "200",
    } | changes
    return "\n".join(f"{key}={value}" for key, value in fields.items())


def test_transient_proof_uses_actual_user_notify_and_unbounded_non_killing_stop(probe):
    command = probe.transient_command(
        "hfcache-proof-fixture-worker.service", "hfcache-proof-fixture-worker", ["podman", "run"]
    )
    assert command[:2] == ["/usr/bin/systemd-run", "--user"]
    assert {"--property=Type=notify", "--property=NotifyAccess=all"} <= set(command)
    assert "--property=TimeoutStopSec=infinity" in command
    assert "--property=SendSIGKILL=no" in command
    # The parent drains the validated exact ID; no name-based stop command can
    # return an error into systemd's fallback termination path.
    assert not any("ExecStop=" in argument for argument in command)
    assert command[-2:] == ["podman", "run"]
    assert not any("conmon" in argument or "SIGKILL=yes" in argument for argument in command)


@pytest.mark.parametrize(
    "change",
    [
        {"Type": "exec"},
        {"NotifyAccess": "main"},
        {"SubState": "exited"},
        {"MainPID": "0"},
        {"MainPID": "unknown"},
        {"ControlGroup": ""},
        {"ExecMainStartTimestampMonotonic": "0"},
        {"ActiveEnterTimestampMonotonic": "99"},
    ],
)
def test_readiness_refuses_optimistic_or_incomplete_manager_state(probe, change):
    with pytest.raises(ValueError, match="readiness"):
        probe.ready_state(_ready_text(**change))


def test_readiness_waits_through_starting_and_records_actual_notify_transition(probe, monkeypatch):
    states = iter([_ready_text(ActiveState="activating", SubState="start"), _ready_text()])
    captured = []

    def manager(*arguments, **kwargs):
        captured.append(arguments)
        return subprocess.CompletedProcess([], 0, stdout=next(states))

    monkeypatch.setattr(probe, "manager", manager)
    monkeypatch.setattr(probe.time, "sleep", lambda _: None)
    result = probe.wait_ready(
        "hfcache-proof-fixture-worker.service", SimpleNamespace(poll=lambda: None)
    )
    assert result["MainPID"] == "123"
    assert result["ActiveEnterTimestampMonotonic"] == "200"
    assert len(captured) == 2


def test_exit_before_ready_never_becomes_acceptance(probe, monkeypatch):
    monkeypatch.setattr(
        probe,
        "manager",
        lambda *_args, **_kwargs: subprocess.CompletedProcess(
            [], 0, stdout=_ready_text(ActiveState="failed")
        ),
    )
    with pytest.raises(ValueError, match="readiness"):
        probe.wait_ready("hfcache-proof-fixture-worker.service", SimpleNamespace(poll=lambda: 20))
