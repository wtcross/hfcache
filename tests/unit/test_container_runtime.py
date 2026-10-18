"""Decision 127: exact artifacts, local-only engine and preserved executor evidence."""

import errno
import importlib.util
import io
import json
import os
import socket
import subprocess
import sys
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
    calls = fake_build_tools(builder, monkeypatch, context)
    result = builder.build(wheel, expected, context, "localhost/hfcache:proof")
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
        "requirements.txt",
        "wheels",
    ]
    assert len(calls) == 4


def test_failed_build_preserves_authenticated_inputs_and_no_success_manifest(
    builder, monkeypatch, tmp_path
):
    wheel = wheel_file(tmp_path)
    context = tmp_path / "failed"
    fake_build_tools(builder, monkeypatch, context, fail_build=True)
    with pytest.raises(subprocess.CalledProcessError):
        builder.build(wheel, builder.digest(wheel.read_bytes()), context, "localhost/hfcache:proof")
    assert (context / "inputs.json").exists()
    assert (context / "wheels" / wheel.name).read_bytes() == wheel.read_bytes()
    assert not (context / "build.json").exists()


def test_existing_context_is_preserved_before_export(builder, monkeypatch, tmp_path):
    wheel = wheel_file(tmp_path)
    context = tmp_path / "existing"
    context.mkdir()
    (context / "unknown").write_bytes(b"evidence")
    calls = fake_build_tools(builder, monkeypatch, context)
    with pytest.raises(FileExistsError):
        builder.build(wheel, builder.digest(wheel.read_bytes()), context, "localhost/hfcache:proof")
    assert calls == []
    assert (context / "unknown").read_bytes() == b"evidence"


@pytest.mark.parametrize(
    "tag", ["registry.example/hfcache:latest", "localhost/hfcache:bad tag", "localhost/other:tag"]
)
def test_builder_cannot_select_remote_publication_tag(builder, monkeypatch, tmp_path, tag):
    monkeypatch.setattr(builder.os, "geteuid", lambda: 1000)
    with pytest.raises(ValueError, match="local"):
        builder.build(tmp_path / "missing", "a" * 64, tmp_path / "new", tag)
    assert not (tmp_path / "new").exists()


def test_root_builder_refuses_before_artifact_or_engine_io(builder, monkeypatch, tmp_path):
    monkeypatch.setattr(builder.os, "geteuid", lambda: 0)
    with pytest.raises(ValueError, match="never root"):
        builder.build(tmp_path / "missing", "a" * 64, tmp_path / "new", "localhost/hfcache:proof")


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
    data = {"Config": {"Labels": {"io.hfcache.proof": "expected"}}, "Image": actual}
    monkeypatch.setattr(
        probe, "engine", lambda *_: subprocess.CompletedProcess([], 0, stdout=json.dumps([data]))
    )
    assert probe.inspect_owned("hfcache-proof-fixture-worker", "expected", IMAGE) == data


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
        "sys": SimpleNamespace(argv=["-c", "/source", "1", "1", "3"], exit=sys.exit),
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


def test_actual_descriptor_trampoline_keeps_named_fd3_and_clears_stale_host_pidfd(probe, tmp_path):
    path = tmp_path / "verify.sock"
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener:
        listener.bind(str(path))
        listener.listen(1)
        inode = path.stat().st_ino
        code = """
import json,os,socket
with socket.socket(fileno=3) as channel:
 assert channel.getsockopt(socket.SOL_SOCKET,socket.SO_ACCEPTCONN)==1
 assert os.environ['LISTEN_PID']==str(os.getpid())
 assert os.environ['LISTEN_FDS']=='1'
 assert os.environ['LISTEN_FDNAMES']=='hfcache-verification'
 assert 'LISTEN_PIDFDID' not in os.environ
 print(json.dumps({'fd3':True}))
"""
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                probe._TRAMPOLINE,
                str(listener.fileno()),
                sys.executable,
                "-c",
                code,
            ],
            pass_fds=(listener.fileno(),),
            check=True,
            capture_output=True,
            text=True,
            env={"PATH": os.environ["PATH"], "LISTEN_PIDFDID": "stale-host-identity"},
        )
        assert json.loads(result.stdout) == {"fd3": True}
        assert listener.getsockopt(socket.SOL_SOCKET, socket.SO_ACCEPTCONN) == 1
        assert path.stat().st_ino == inode
