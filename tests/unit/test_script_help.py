"""Human inspection must precede installed credentials, managers and workloads."""

import builtins
import io
import os
import runpy
import shlex
import socket
import subprocess
import sys
from contextlib import suppress
from pathlib import Path

import pytest

from tests.docs_contract import CHECKER

ROOT = Path(__file__).resolve().parents[2]


def approved_import_read(path):
    if isinstance(path, int):
        return False
    raw = Path(path)
    if ".." in raw.parts:
        return False
    candidate = raw.absolute()
    owners = [
        owner
        for owner in (ROOT, Path(sys.prefix), Path(sys.base_prefix))
        if candidate.is_relative_to(owner)
    ]
    if not owners:
        return False
    owner = max(owners, key=lambda item: len(item.parts))
    current = owner
    for part in candidate.relative_to(owner).parts:
        current = current / part
        if current.is_symlink():
            return False
    trusted_library = candidate.is_relative_to(Path(sys.prefix)) or candidate.is_relative_to(
        Path(sys.base_prefix)
    )
    code = candidate.suffix in {".py", ".pyc", ".so"}
    metadata = any(part.endswith(".dist-info") for part in candidate.parts)
    return (
        (trusted_library and (code or metadata or candidate.suffix == ".zip"))
        or (candidate.is_relative_to(ROOT) and code)
        or candidate == ROOT / "packaging/containers/images.json"
    )


@pytest.mark.parametrize(
    "script",
    [name for name, mode in CHECKER["HELP_MODES"].items() if mode == "python"]
    + ["../examples/copy-revision.py", "../examples/mcp-client.py"],
)
def test_every_approved_python_help_precedes_runtime_access(monkeypatch, capsys, script):
    attempted = []

    def forbidden(*args, **kwargs):
        attempted.append(str(args[0]) if args else "runtime access")
        message = "help accessed a process, network or runtime file"
        raise RuntimeError(message)

    original_path_text = Path.read_text
    original_path_bytes = Path.read_bytes
    original_path_open = Path.open
    original_open = builtins.open
    original_os_open = os.open

    code_read = approved_import_read

    def protected_open(path, mode="r", *args, **kwargs):
        if any(flag in mode for flag in "wax+") or not code_read(path):
            return forbidden(str(path))
        return original_open(path, mode, *args, **kwargs)

    def protected_os_open(path, flags, *args, **kwargs):
        if flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC) or not code_read(path):
            return forbidden()
        return original_os_open(path, flags, *args, **kwargs)

    def protected_path_text(path, *args, **kwargs):
        return original_path_text(path, *args, **kwargs) if code_read(path) else forbidden()

    def protected_path_bytes(path, *args, **kwargs):
        return original_path_bytes(path, *args, **kwargs) if code_read(path) else forbidden()

    def protected_path_open(path, mode="r", *args, **kwargs):
        if any(flag in mode for flag in "wax+") or not code_read(path):
            return forbidden()
        return original_path_open(path, mode, *args, **kwargs)

    with monkeypatch.context() as guard:
        guard.setattr(sys, "argv", [script, "--help"])
        guard.setattr(sys, "dont_write_bytecode", True)
        guard.setattr(subprocess, "run", forbidden)
        guard.setattr(subprocess, "Popen", forbidden)
        guard.setattr(os, "system", forbidden)
        guard.setattr(os, "open", protected_os_open)
        guard.setattr(builtins, "open", protected_open)
        guard.setattr(io, "open", protected_open)
        guard.setattr(socket, "create_connection", forbidden)
        for operation in ("connect", "connect_ex", "bind", "listen"):
            guard.setattr(socket.socket, operation, forbidden)
        guard.setattr(Path, "read_text", protected_path_text)
        guard.setattr(Path, "read_bytes", protected_path_bytes)
        guard.setattr(Path, "open", protected_path_open)
        try:
            module = runpy.run_path(str((ROOT / "scripts" / script).resolve()))
            result = module["main"]()
        except SystemExit as error:
            result = error.code
    assert result in (None, 0)
    assert attempted == []
    output = capsys.readouterr().out
    assert "usage:" in output.lower()
    assert CHECKER["audience_errors"](output) == []


@pytest.mark.parametrize(
    "script",
    [name for name, mode in CHECKER["HELP_MODES"].items() if mode == "bash"],
)
def test_every_approved_shell_help_uses_no_manager_engine_or_install_tool(tmp_path, script):
    tools = tmp_path / "bin"
    tools.mkdir()
    for name in (
        "systemctl",
        "systemd-run",
        "podman",
        "docker",
        "uv",
        "curl",
        "wget",
        "sudo",
        "mount",
        "mkdir",
        "install",
        "chmod",
        "chown",
        "useradd",
        "groupadd",
    ):
        blocker = tools / name
        blocker.write_text(
            "#!/bin/sh\nprintf '%s\\n' invoked >> "
            + shlex.quote(str(tmp_path / "runtime-calls"))
            + "\nprintf 'forbidden runtime command' >&2\nexit 99\n"
        )
        blocker.chmod(0o755)
    environment = {**os.environ, "PATH": str(tools) + ":" + os.environ["PATH"]}
    for name in ("BASH_ENV", "ENV", "SHELLOPTS", "BASHOPTS", "CDPATH"):
        environment.pop(name, None)
    result = subprocess.run(
        ["bash", str(ROOT / "scripts" / script), "--help"],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert not (tmp_path / "runtime-calls").exists()
    assert CHECKER["audience_errors"](result.stdout) == []


@pytest.mark.parametrize("kind", ["outside", "traversal", "symlink"])
def test_help_import_guard_records_even_a_caught_runtime_file_attempt(
    tmp_path, monkeypatch, capsys, kind
):
    owner = tmp_path / "repo"
    owner.mkdir()
    outside = tmp_path / "runtime.py"
    outside.write_text("owned fixture")
    alias = owner / "alias.py"
    alias.symlink_to(outside)
    runtime_file = {"outside": outside, "traversal": owner / "../runtime.py", "symlink": alias}[
        kind
    ]
    monkeypatch.setitem(
        test_every_approved_python_help_precedes_runtime_access.__globals__, "ROOT", owner
    )

    def bad_import(_path):
        with suppress(RuntimeError):
            runtime_file.read_text()

        def main():
            sys.stdout.write("usage: fixture\n")

        return {"main": main}

    monkeypatch.setattr(runpy, "run_path", bad_import)
    with pytest.raises(AssertionError):
        test_every_approved_python_help_precedes_runtime_access(monkeypatch, capsys, "fixture.py")


@pytest.mark.parametrize(
    ("script", "guarded"),
    [
        ("container-service.py", "load_profile"),
        ("hold-readonly-guard.py", "hold_original_lock"),
        ("check-installations.py", "run"),
    ],
)
def test_help_precedes_profile_locks_and_workloads(monkeypatch, capsys, script, guarded):
    module = runpy.run_path(str(ROOT / "scripts" / script))
    main = module["main"]

    def forbidden(*args, **kwargs):
        pytest.fail("help attempted runtime access")

    monkeypatch.setitem(main.__globals__, guarded, forbidden)
    monkeypatch.setattr(Path, "read_text", forbidden)
    monkeypatch.setattr(sys, "argv", [script, "--help"])
    try:
        result = main()
    except SystemExit as error:
        result = error.code
    assert result in (None, 0)
    assert "usage:" in capsys.readouterr().out.lower()


@pytest.mark.parametrize("arguments", [["--help"], ["-h"], ["status", "--help"]])
def test_container_client_wrapper_help_needs_no_installed_launcher(arguments):
    result = subprocess.run(
        ["bash", str(ROOT / "scripts/hfcache-client"), *arguments],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "Podman" in result.stdout
    assert "hfcache.api" in result.stdout


@pytest.mark.parametrize("handle", ["--help", "-h", "-original_key", "~original_key"])
def test_client_wrapper_forwards_original_handle_after_delimiter(tmp_path, handle):
    capture = tmp_path / "exec-arguments"
    arguments = [
        "--expected-client-scope",
        "a" * 64,
        "operations",
        "lookup",
        "--",
        handle,
    ]
    environment = {**os.environ, "HFCACHE_TEST_EXEC_CAPTURE": str(capture)}
    for name in ("BASH_ENV", "ENV", "SHELLOPTS", "BASHOPTS", "CDPATH"):
        environment.pop(name, None)
    # The actual repository script runs, but its fixed exec is intercepted by a
    # Bash function. No installed launcher, container, profile or archive opens.
    result = subprocess.run(
        [
            "bash",
            "-c",
            'exec() { printf "%s\\0" "$@" > "$HFCACHE_TEST_EXEC_CAPTURE"; exit 73; }; source "$@"',
            "hfcache-wrapper-test",
            str(ROOT / "scripts/hfcache-client"),
            *arguments,
        ],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == 73, (result.stdout, result.stderr)
    assert capture.read_bytes().split(b"\0") == [
        b"/usr/local/libexec/hfcache-container-service",
        b"client",
        *(argument.encode() for argument in arguments),
        b"",
    ]
    assert result.stdout == ""


@pytest.mark.parametrize("arguments", [["--help"], ["status", "--help"], ["-h", "--", "key"]])
def test_fixed_client_role_help_needs_no_profile(monkeypatch, arguments):
    module = runpy.run_path(str(ROOT / "scripts/container-service.py"))
    main = module["main"]

    def forbidden():
        pytest.fail("client help attempted installed profile access")

    monkeypatch.setitem(main.__globals__, "load_profile", forbidden)
    monkeypatch.setattr(sys, "argv", ["container-service.py", "client", *arguments])
    assert main() == 0


@pytest.mark.parametrize("handle", ["--help", "-h", "-original_key", "~original_key"])
def test_fixed_client_launcher_forwards_original_handle_after_delimiter(monkeypatch, handle):
    module = runpy.run_path(str(ROOT / "scripts/container-service.py"))
    main = module["main"]
    image = "sha256:" + "b" * 64
    arguments = [
        "--expected-client-scope",
        "a" * 64,
        "operations",
        "lookup",
        "--",
        handle,
    ]
    executions = []

    class Executed(BaseException):
        """Stop at the actual fixed process boundary without starting it."""

    def capture_exec(executable, argv):
        executions.append((executable, argv))
        raise Executed

    def forbidden(*args, **kwargs):
        pytest.fail("client forwarding attempted a workload or installed profile read")

    monkeypatch.setitem(main.__globals__, "load_profile", lambda: {"app_image": image})
    monkeypatch.setitem(main.__globals__, "archive_readonly", forbidden)
    monkeypatch.setitem(main.__globals__, "prepare_start", forbidden)
    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(os, "execv", capture_exec)
    monkeypatch.setattr(sys, "argv", ["container-service.py", "client", *arguments])
    with pytest.raises(Executed):
        main()
    assert len(executions) == 1
    executable, argv = executions[0]
    assert executable == "/usr/bin/podman"
    assert argv[:2] == ["/usr/bin/podman", "--remote=false"]
    assert argv[-len(arguments) - 2 :] == [image, "/opt/hfcache/.venv/bin/hfcache", *arguments]
    assert "--network=none" in argv
    assert "/srv/hfcache:/srv/hfcache:ro" not in argv


@pytest.mark.parametrize("argument", ["--dry-run", "--engine", "unknown"])
def test_fixed_launcher_invalid_grammar_precedes_profile(monkeypatch, argument):
    module = runpy.run_path(str(ROOT / "scripts/container-service.py"))
    main = module["main"]

    def forbidden():
        pytest.fail("invalid grammar attempted installed profile access")

    monkeypatch.setitem(main.__globals__, "load_profile", forbidden)
    monkeypatch.setattr(sys, "argv", ["container-service.py", argument])
    assert main() == 20
