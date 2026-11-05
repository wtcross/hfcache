"""Disposable release switching refuses live observers/executors (decision 121)."""

import ast
import fcntl
import hashlib
import importlib.util
import json
import os
import select
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
LIBRARY = ROOT / "scripts/release-functions.sh"
UNITS = (
    "hfcache-sync.timer",
    "hfcache-verify.timer",
    "hfcache-sync.service",
    "hfcache-verify.service",
    "hfcache-api.socket",
    "hfcache-api.service",
    "hfcache-verification.socket",
    "hfcache-verification.service",
)


@pytest.fixture
def release_fixture(tmp_path):
    prefix, runtime = tmp_path / "install", tmp_path / "runtime"
    runtime.mkdir(mode=0o700)
    (runtime / "hfcache.lock").write_bytes(b"persistent lock inode\n")
    (runtime / "hfcache.lock").chmod(0o600)
    for version in ("0.1.9", "0.1.10"):
        binary = prefix / "releases" / version / ".venv/bin/hfcache"
        binary.parent.mkdir(parents=True)
        binary.write_text(f"#!/bin/sh\nprintf '%s\\n' '{version}'\n")
        binary.chmod(0o755)
        python = binary.with_name("python")
        python.write_text("#!/bin/sh\nexit 1\n")
        python.chmod(0o755)
        (binary.parents[1] / "pyvenv.cfg").write_text("home = /fixture/python\n")
        native_source(binary.parents[2], version)
    (prefix / "current").symlink_to("releases/0.1.9")
    manager = tmp_path / "systemctl"
    manager.write_text(
        "#!/usr/bin/env python3\nimport json,os,sys\nfrom pathlib import Path\n"
        "states=json.loads(Path(os.environ['UNIT_STATES']).read_text())\n"
        "unit=sys.argv[2]\n"
        "if unit == states.get('unavailable'): sys.exit(1)\n"
        "fields={'LoadState':'loaded','ActiveState':'inactive','MainPID':'0',"
        "'ControlPID':'0','TasksCurrent':'0'}\n"
        "fields.update(states.get(unit,{}))\n"
        "for key,value in fields.items(): print(key+'='+value)\n"
    )
    manager.chmod(0o755)
    states = tmp_path / "states.json"
    states.write_text("{}")
    environment = dict(os.environ) | {
        "HFCACHE_SYSTEMCTL": str(manager),
        "HFCACHE_RUNTIME_DIRECTORY": str(runtime),
        "UNIT_STATES": str(states),
        "HFCACHE_CLIENT_STATE_DIRECTORY": str(tmp_path / "clients"),
    }
    return prefix, runtime, states, environment


def native_source(directory, version="0.2.1"):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / ".python-version").write_text("3.14\n")
    (directory / "pyproject.toml").write_text(f'[project]\nname="hfcache"\nversion="{version}"\n')
    (directory / "uv.lock").write_text(
        f'version=1\n[[package]]\nname="hfcache"\nversion="{version}"\n'
    )
    package = directory / "src/hfcache"
    package.mkdir(parents=True)
    for name in ("__init__.py", "cli.py"):
        (package / name).write_text('"""Disposable native source evidence."""\n')
    return directory


def run_library(fixture, command="require_quiescent; switch_to 0.1.10"):
    prefix, _, _, environment = fixture
    return subprocess.run(
        [
            "bash",
            "-c",
            'set -euo pipefail; source "$1"; PREFIX=$2; ' + command,
            "fixture",
            str(LIBRARY),
            str(prefix),
        ],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )


def test_upgrade_then_rollback_uses_same_guard_and_atomic_switch(release_fixture):
    prefix, runtime, _, _ = release_fixture
    lock = runtime / "hfcache.lock"
    inode, payload = lock.stat().st_ino, lock.read_bytes()
    before = subprocess.check_output([str(prefix / "current/.venv/bin/hfcache")], text=True)
    assert before.strip() == "0.1.9"
    upgraded = run_library(release_fixture)
    assert upgraded.returncode == 0, upgraded.stderr
    assert (prefix / "current").readlink() == Path("releases/0.1.10")
    assert (
        subprocess.check_output([str(prefix / "current/.venv/bin/hfcache")], text=True).strip()
        == "0.1.10"
    )
    rolled_back = run_library(release_fixture, "require_quiescent; switch_to 0.1.9")
    assert rolled_back.returncode == 0, rolled_back.stderr
    assert (prefix / "current").readlink() == Path("releases/0.1.9")
    assert (lock.stat().st_ino, lock.read_bytes()) == (inode, payload)
    assert not list(prefix.glob(".current.*"))


@pytest.mark.parametrize("unit", UNITS)
@pytest.mark.parametrize("load_state", ["loaded", "masked"])
def test_any_live_timer_observer_socket_or_executor_refuses_switch(
    release_fixture, unit, load_state
):
    prefix, runtime, states, _ = release_fixture
    states.write_text(json.dumps({unit: {"LoadState": load_state, "ActiveState": "active"}}))
    before = (runtime / "hfcache.lock").stat().st_ino
    result = run_library(release_fixture)
    assert result.returncode == 1
    assert unit in result.stderr
    assert (prefix / "current").readlink() == Path("releases/0.1.9")
    assert (runtime / "hfcache.lock").stat().st_ino == before


@pytest.mark.parametrize("load_state", ["loaded", "masked"])
@pytest.mark.parametrize("field", ["MainPID", "ControlPID", "TasksCurrent"])
def test_inactive_service_with_leftover_processes_refuses(release_fixture, field, load_state):
    _, _, states, _ = release_fixture
    states.write_text(
        json.dumps({"hfcache-verification.service": {"LoadState": load_state, field: "1"}})
    )
    result = run_library(release_fixture)
    assert result.returncode == 1
    assert "retains processes" in result.stderr


def test_inactive_masked_legacy_units_allow_switch_without_removing_masks(release_fixture):
    prefix, runtime, states, _ = release_fixture
    masked = {
        unit: {
            "LoadState": "masked",
            "ActiveState": "inactive",
            "MainPID": "0",
            "ControlPID": "0",
            "TasksCurrent": "[not set]",
            "ControlGroup": "",
        }
        for unit in UNITS[:4]
    }
    states.write_text(json.dumps(masked))
    lock = runtime / "hfcache.lock"
    identity, payload = lock.stat().st_ino, lock.read_bytes()
    result = run_library(release_fixture)
    assert result.returncode == 0, result.stderr
    assert (prefix / "current").readlink() == Path("releases/0.1.10")
    assert json.loads(states.read_text()) == masked
    assert (lock.stat().st_ino, lock.read_bytes()) == (identity, payload)


@pytest.mark.parametrize(
    ("load_state", "active_state"),
    [("masked", "failed"), ("error", "inactive"), ("bad-setting", "inactive")],
)
def test_unexplained_load_or_masked_activity_refuses(release_fixture, load_state, active_state):
    _, _, states, _ = release_fixture
    states.write_text(
        json.dumps({"hfcache-sync.timer": {"LoadState": load_state, "ActiveState": active_state}})
    )
    result = run_library(release_fixture)
    assert result.returncode == 1
    assert "hfcache-sync.timer" in result.stderr


def test_masked_service_without_task_and_cgroup_absence_refuses(release_fixture):
    _, _, states, _ = release_fixture
    states.write_text(
        json.dumps(
            {
                "hfcache-sync.service": {
                    "LoadState": "masked",
                    "TasksCurrent": "[not set]",
                    "ControlGroup": "/system.slice/hfcache-sync.service",
                }
            }
        )
    )
    result = run_library(release_fixture)
    assert result.returncode == 1
    assert "retains processes" in result.stderr


def test_orphan_flock_refuses_without_replacing_or_truncating_file(release_fixture):
    prefix, runtime, _, _ = release_fixture
    lock = runtime / "hfcache.lock"
    with lock.open("rb") as holder:
        fcntl.flock(holder, fcntl.LOCK_EX)
        result = run_library(release_fixture)
    assert result.returncode == 1
    assert "orphan" in result.stderr
    assert lock.read_bytes() == b"persistent lock inode\n"
    assert (prefix / "current").readlink() == Path("releases/0.1.9")


def test_guard_holds_the_original_lock_through_switch(release_fixture):
    prefix, runtime, _, environment = release_fixture
    script = (
        'set -euo pipefail; source "$1"; PREFIX=$2; require_quiescent; '
        "printf 'guarded\\n'; read -r response; switch_to 0.1.10"
    )
    with subprocess.Popen(
        ["bash", "-c", script, "fixture", str(LIBRARY), str(prefix)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=environment,
    ) as process:
        try:
            assert process.stdout is not None
            readable, _, _ = select.select([process.stdout], [], [], 5)
            assert readable, "guard did not become ready"
            assert process.stdout.readline() == "guarded\n"
            with (
                (runtime / "hfcache.lock").open("rb") as descriptor,
                pytest.raises(BlockingIOError),
            ):
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            _, error = process.communicate("continue\n", timeout=5)
            assert process.returncode == 0, error
            assert (prefix / "current").readlink() == Path("releases/0.1.10")
        finally:
            if process.poll() is None:
                process.kill()
                process.communicate(timeout=5)


@pytest.mark.parametrize("shape", ["symlink", "directory", "missing"])
def test_unexplained_lock_never_authorizes_switch(release_fixture, shape):
    prefix, runtime, _, _ = release_fixture
    lock = runtime / "hfcache.lock"
    lock.unlink()
    target = runtime / "unrelated"
    if shape == "symlink":
        target.write_bytes(b"preserve")
        lock.symlink_to(target)
    elif shape == "directory":
        lock.mkdir()
    result = run_library(release_fixture)
    assert result.returncode == 1
    assert (prefix / "current").readlink() == Path("releases/0.1.9")
    if shape == "symlink":
        assert target.read_bytes() == b"preserve"


def test_unavailable_service_manager_is_not_quiescence(release_fixture):
    _, _, states, _ = release_fixture
    states.write_text(json.dumps({"unavailable": "hfcache-api.service"}))
    result = run_library(release_fixture)
    assert result.returncode == 1
    assert "cannot establish" in result.stderr


def test_existing_release_or_traversal_is_never_followed_outside_prefix(release_fixture):
    prefix, _, _, _ = release_fixture
    for version in ("../escape", "/tmp/escape", "missing"):
        result = run_library(release_fixture, f"switch_to {version}")
        assert result.returncode == 1
        assert (prefix / "current").readlink() == Path("releases/0.1.9")
    alias = prefix / "releases/0.1.11"
    alias.symlink_to(prefix / "releases/0.1.10", target_is_directory=True)
    assert run_library(release_fixture, "switch_to 0.1.11").returncode == 1


def test_first_install_guard_does_not_create_runtime_lock(release_fixture):
    prefix, runtime, _, _ = release_fixture
    (prefix / "current").unlink()
    (runtime / "hfcache.lock").unlink()
    result = run_library(release_fixture, "require_quiescent")
    assert result.returncode == 0, result.stderr
    assert list(runtime.iterdir()) == []


def test_installer_dry_run_needs_no_root_and_executes_no_tool_or_mutation(tmp_path):
    prefix = tmp_path / "unused"
    environment = dict(os.environ) | {
        "HFCACHE_PREFIX": str(prefix),
        "HFCACHE_SOURCE": str(tmp_path / "nonexistent-source"),
        "HFCACHE_UV": str(tmp_path / "must-not-run"),
        "HFCACHE_SYSTEMCTL": str(tmp_path / "must-not-run"),
    }
    result = subprocess.run(
        ["bash", str(ROOT / "scripts/install-release.sh"), "--dry-run", "--switch", "0.1.10"],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )
    assert result.returncode == 0, result.stderr
    assert "locked server extra" in result.stdout
    assert "validate --local" in result.stdout
    assert "switch target: 0.1.10" in result.stdout
    assert not prefix.exists()


@pytest.mark.parametrize("mode", [["--help"], ["--list"], ["--dry-run"]])
def test_native_inspection_does_not_require_source_or_runtime(tmp_path, mode):
    prefix = tmp_path / "absent"
    result = subprocess.run(
        ["bash", str(ROOT / "scripts/install-release.sh"), *mode],
        env=dict(os.environ)
        | {
            "HFCACHE_SOURCE": str(tmp_path / "absent-source"),
            "HFCACHE_PREFIX": str(prefix),
            "HFCACHE_UV": str(tmp_path / "forbidden"),
            "HFCACHE_SYSTEMCTL": str(tmp_path / "forbidden"),
        },
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert not prefix.exists()


@pytest.mark.parametrize("location", ["current", "target", "source"])
@pytest.mark.parametrize("marker", ["container-release.json", "artifact-index.json", "rendered"])
def test_native_installer_refuses_cross_profile_before_any_tool(
    release_fixture, tmp_path, location, marker
):
    prefix, runtime, _, environment = release_fixture
    source = native_source(tmp_path / "source", "0.1.10")
    selected = {
        "current": prefix / "releases/0.1.9",
        "target": prefix / "releases/0.1.10",
        "source": source,
    }[location]
    (selected / marker).write_text("malformed or mixed metadata must still refuse\n")
    invoked = tmp_path / "tool-called"
    tool = tmp_path / "forbidden-tool"
    tool.write_text(f"#!/bin/sh\ntouch '{invoked}'\nexit 99\n")
    tool.chmod(0o755)
    environment |= {
        "HFCACHE_SOURCE": str(source),
        "HFCACHE_PREFIX": str(prefix),
        "HFCACHE_UV": str(tool),
        "HFCACHE_SYSTEMCTL": str(tool),
    }
    before = (runtime / "hfcache.lock").stat().st_ino
    result = subprocess.run(
        ["bash", str(ROOT / "scripts/install-release.sh"), "--no-switch"],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 20
    assert "native profile refused" in result.stderr
    assert not invoked.exists()
    assert (prefix / "current").readlink() == Path("releases/0.1.9")
    assert (runtime / "hfcache.lock").stat().st_ino == before
    assert not list((prefix / "releases").glob(".*"))
    assert (selected / marker).read_text().startswith("malformed")


@pytest.mark.parametrize("location", ["current", "target"])
def test_direct_switch_refuses_container_release_without_candidate_execution(
    release_fixture, location
):
    prefix, _, _, _ = release_fixture
    path = prefix / "releases" / ("0.1.9" if location == "current" else "0.1.10")
    (path / "container-release.json").write_text("{}")
    result = run_library(release_fixture, "switch_to 0.1.10")
    assert result.returncode == 1
    assert "native profile refused" in result.stderr
    assert (prefix / "current").readlink() == Path("releases/0.1.9")


@pytest.mark.parametrize(
    "shape", ["directory", "dangling", "external", "unknown", "partial", "double-slash", "dot"]
)
def test_unknown_current_layout_is_never_inferred_native(release_fixture, tmp_path, shape):
    prefix, _, _, _ = release_fixture
    current = prefix / "current"
    current.unlink()
    if shape == "directory":
        current.mkdir()
    elif shape == "dangling":
        current.symlink_to("releases/0.9.9")
    elif shape == "external":
        current.symlink_to(tmp_path)
    elif shape in {"double-slash", "dot"}:
        current.symlink_to("releases//0.1.9" if shape == "double-slash" else "releases/./0.1.9")
    else:
        current.symlink_to("releases/0.1.9")
        path = prefix / "releases/0.1.9"
        if shape == "unknown":
            (path / "other-profile.json").write_text("{}")
        else:
            (path / "uv.lock").unlink()
    result = run_library(release_fixture, "switch_to 0.1.10")
    assert result.returncode == 1
    assert "native profile refused" in result.stderr
    assert current.is_symlink() or current.is_dir()


def test_positive_native_source_allows_fresh_prefix_without_any_creation(tmp_path):
    prefix = tmp_path / "new-prefix"
    source = native_source(tmp_path / "source")
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/release-profile.py"),
            "--prefix",
            str(prefix),
            "--source",
            str(source),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert not prefix.exists()


def test_classifier_parses_on_the_native_bootstrap_host_python():
    # Bootstrap precedes installation of application Python 3.14.
    source = (ROOT / "scripts/release-profile.py").read_text()
    ast.parse(source, feature_version=(3, 12))


def test_staging_version_comes_from_the_classified_project(release_fixture, tmp_path):
    prefix, _, _, environment = release_fixture
    source = native_source(tmp_path / "source", "0.1.10")
    project = source / "pyproject.toml"
    project.write_text('[tool.fixture]\nversion = "9.9.9"\n' + project.read_text())
    alternate = prefix / "releases/9.9.9"
    alternate.mkdir()
    marker = alternate / "container-release.json"
    marker.write_bytes(b"preserve alternate container release\n")
    environment["NATIVE_SOURCE"] = str(source)
    result = run_library(
        release_fixture,
        'version=$(native_profiles --source "$NATIVE_SOURCE" --print-source-version); '
        'test "$version" = 0.1.10',
    )
    assert result.returncode == 0, result.stderr
    assert marker.read_bytes() == b"preserve alternate container release\n"
    assert (prefix / "current").readlink() == Path("releases/0.1.9")


def test_fresh_prefix_with_symlinked_ancestor_refuses_before_tools(tmp_path):
    other = tmp_path / "other-deployment"
    other.mkdir()
    marker = other / "container-release.json"
    marker.write_bytes(b"preserve\n")
    alias = tmp_path / "alias"
    alias.symlink_to(other, target_is_directory=True)
    prefix = alias / "new-native"
    source = native_source(tmp_path / "source")
    invoked = tmp_path / "tool-called"
    tool = tmp_path / "forbidden-tool"
    tool.write_text(f"#!/bin/sh\ntouch '{invoked}'\nexit 99\n")
    tool.chmod(0o755)
    result = subprocess.run(
        ["bash", str(ROOT / "scripts/install-release.sh"), "--no-switch"],
        env=dict(os.environ)
        | {
            "HFCACHE_SOURCE": str(source),
            "HFCACHE_PREFIX": str(prefix),
            "HFCACHE_UV": str(tool),
            "HFCACHE_SYSTEMCTL": str(tool),
        },
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 20
    assert "native profile refused" in result.stderr
    assert not invoked.exists()
    assert not prefix.exists()
    assert list(other.iterdir()) == [marker]
    assert marker.read_bytes() == b"preserve\n"


def test_native_classification_allows_managed_python_link_but_not_source_as_release(
    release_fixture, tmp_path
):
    prefix, _, _, _ = release_fixture
    python = prefix / "releases/0.1.10/.venv/bin/python"
    python.unlink()
    python.symlink_to(sys.executable)
    assert run_library(release_fixture).returncode == 0
    source = native_source(prefix / "releases/0.2.1")
    assert source.is_dir()
    assert run_library(release_fixture, "switch_to 0.2.1").returncode == 1


@pytest.mark.parametrize("stage", [False, True])
def test_optional_mcp_profile_is_read_only_until_install(tmp_path, stage):
    prefix = tmp_path / "unused"
    environment = dict(os.environ) | {
        "HFCACHE_PREFIX": str(prefix),
        "HFCACHE_SOURCE": str(ROOT),
        "HFCACHE_UV": str(tmp_path / "must-not-run"),
        "HFCACHE_SYSTEMCTL": str(tmp_path / "must-not-run"),
    }
    arguments = ["bash", str(ROOT / "scripts/install-release.sh"), "--dry-run", "--with-mcp"]
    if stage:
        arguments.append("--no-switch")
    result = subprocess.run(arguments, check=False, capture_output=True, text=True, env=environment)
    assert result.returncode == 0, result.stderr
    assert "locked server and mcp extras" in result.stdout
    assert f"mode: {'stage' if stage else 'install'}" in result.stdout
    assert not prefix.exists()


@pytest.mark.parametrize("mode", [["--list"], ["--switch", "0.1.10"]])
def test_optional_mcp_profile_cannot_change_an_existing_release(tmp_path, mode):
    prefix = tmp_path / "unused"
    result = subprocess.run(
        ["bash", str(ROOT / "scripts/install-release.sh"), "--dry-run", "--with-mcp", *mode],
        check=False,
        capture_output=True,
        text=True,
        env=dict(os.environ) | {"HFCACHE_PREFIX": str(prefix), "HFCACHE_SOURCE": str(ROOT)},
    )
    assert result.returncode == 1
    assert "only when building or staging" in result.stderr
    assert not prefix.exists()


@pytest.mark.parametrize("stage", [False, True])
def test_explicit_web_release_dry_run_does_not_open_assets_or_run_build_tools(tmp_path, stage):
    prefix = tmp_path / "unused"
    release = tmp_path / "unavailable release"
    arguments = [
        "bash",
        str(ROOT / "scripts/install-release.sh"),
        "--dry-run",
        "--web-release",
        str(release),
        "--web-release-sha256",
        "a" * 64,
    ]
    if stage:
        arguments.append("--no-switch")
    result = subprocess.run(
        arguments,
        check=False,
        capture_output=True,
        text=True,
        env=dict(os.environ)
        | {
            "HFCACHE_PREFIX": str(prefix),
            "HFCACHE_SOURCE": str(tmp_path / "unavailable-source"),
            "HFCACHE_UV": str(tmp_path / "forbidden"),
            "HFCACHE_SYSTEMCTL": str(tmp_path / "forbidden"),
        },
    )
    assert result.returncode == 0, result.stderr
    assert f"web release: {release}; index SHA256: {'a' * 64}" in result.stdout
    assert not release.exists()
    assert not prefix.exists()


@pytest.mark.parametrize(
    "arguments",
    [
        ["--web-release", "/unavailable"],
        ["--web-release-sha256", "a" * 64],
        ["--web-release"],
        ["--web-release-sha256"],
        ["--web-release", ""],
        ["--web-release-sha256", ""],
        ["--web-release", "/unavailable", "--web-release-sha256", "A" * 64],
        ["--web-release", "relative", "--web-release-sha256", "a" * 64],
        ["--web-release", "/unavailable", "--web-release", "/other"],
        ["--web-release-sha256", "a" * 64, "--web-release-sha256", "b" * 64],
    ],
)
def test_incomplete_or_invalid_web_release_selection_refuses_without_effects(tmp_path, arguments):
    prefix = tmp_path / "unused"
    result = subprocess.run(
        ["bash", str(ROOT / "scripts/install-release.sh"), "--dry-run", *arguments],
        check=False,
        capture_output=True,
        text=True,
        env=dict(os.environ)
        | {"HFCACHE_PREFIX": str(prefix), "HFCACHE_SOURCE": str(tmp_path / "absent-source")},
    )
    assert result.returncode == 1
    assert "--web-release" in result.stderr
    assert not prefix.exists()


@pytest.mark.parametrize("mode", [["--list"], ["--switch", "0.1.10"]])
def test_web_release_selection_cannot_reconfigure_an_existing_release(tmp_path, mode):
    prefix = tmp_path / "unused"
    result = subprocess.run(
        [
            "bash",
            str(ROOT / "scripts/install-release.sh"),
            "--dry-run",
            "--web-release",
            str(tmp_path / "absent-assets"),
            "--web-release-sha256",
            "a" * 64,
            *mode,
        ],
        check=False,
        capture_output=True,
        text=True,
        env=dict(os.environ) | {"HFCACHE_PREFIX": str(prefix)},
    )
    assert result.returncode == 1
    assert "only when building or staging" in result.stderr
    assert not prefix.exists()


def web_installer_fixture(tmp_path):
    """Retain real shell/profile code; substitute only the independent verifier CLI."""
    scripts = tmp_path / "installer scripts"
    scripts.mkdir()
    for name in ("install-release.sh", "release-functions.sh", "release-profile.py"):
        (scripts / name).write_bytes((ROOT / "scripts" / name).read_bytes())
    (scripts / "web-release.py").write_text(
        "import json,os,sys\nfrom pathlib import Path\n"
        "Path(os.environ['WEB_COMMAND']).write_text(json.dumps({"
        "'argv':sys.argv[1:],'no_bytecode':os.environ['PYTHONDONTWRITEBYTECODE']}))\n"
        "raise SystemExit(int(os.environ.get('WEB_EXIT','0')))\n"
    )
    command = tmp_path / "web-command.json"
    environment = dict(os.environ) | {
        "WEB_COMMAND": str(command),
        "HFCACHE_PREFIX": str(tmp_path / "new-prefix"),
        "HFCACHE_SOURCE": str(native_source(tmp_path / "native source")),
        "HFCACHE_UV": str(tmp_path / "forbidden-uv"),
        "HFCACHE_SYSTEMCTL": str(tmp_path / "forbidden-manager"),
    }
    return scripts, command, environment


def test_web_index_preflight_runs_after_native_classification_before_root_or_build(tmp_path):
    scripts, command, environment = web_installer_fixture(tmp_path)
    environment["WEB_EXIT"] = "23"
    release = tmp_path / "release assets"
    arguments = [
        "bash",
        str(scripts / "install-release.sh"),
        "--no-switch",
        "--web-release",
        str(release),
        "--web-release-sha256",
        "a" * 64,
    ]
    result = subprocess.run(arguments, check=False, capture_output=True, text=True, env=environment)
    assert result.returncode == 23, result.stderr
    assert json.loads(command.read_text()) == {
        "argv": [
            "verify-native",
            "--release",
            str(release),
            "--index-sha256",
            "a" * 64,
            "--source",
            environment["HFCACHE_SOURCE"],
        ],
        "no_bytecode": "1",
    }
    assert not Path(environment["HFCACHE_PREFIX"]).exists()
    command.unlink()
    (Path(environment["HFCACHE_SOURCE"]) / "container-release.json").write_text("{}")
    refused = subprocess.run(
        arguments, check=False, capture_output=True, text=True, env=environment
    )
    assert refused.returncode == 20
    assert "native profile refused" in refused.stderr
    assert not command.exists()


@pytest.mark.parametrize("enabled", [False, True])
def test_native_sync_selects_copied_python_only_for_explicit_full_web_release(tmp_path, enabled):
    scripts, command, environment = web_installer_fixture(tmp_path)
    prepared = tmp_path / "python" / "web-0.2.2-commit" / "bin/python3.14"
    donor = tmp_path / "python" / "cpython-3.14.6-linux-x86_64-gnu/bin/python3.14"
    (scripts / "web-release.py").write_text(
        "import json,os,sys\nfrom pathlib import Path\n"
        "Path(os.environ['WEB_COMMAND']).write_text(json.dumps(sys.argv[1:]))\n"
        "assert sys.argv[1]=='prepare-python'\n"
        "print(os.environ['PREPARED_PYTHON'])\n"
    )
    uv = tmp_path / "uv"
    uv.write_text(
        "#!/usr/bin/env python3\nimport json,os,sys\nfrom pathlib import Path\n"
        "Path(os.environ['SYNC_COMMAND']).write_text(json.dumps(sys.argv[1:]))\n"
    )
    uv.chmod(0o755)
    release = tmp_path / "release"
    release.mkdir()
    sync_record = tmp_path / "sync-command.json"
    environment |= {"PREPARED_PYTHON": str(prepared), "SYNC_COMMAND": str(sync_record)}
    original = (scripts / "install-release.sh").read_text()
    function = original[original.index("web_release() {") : original.index("\nMODE=install")]
    selection = original[
        original.index("SYNC_PYTHON=${PYTHON_VERSION}") : original.index('step "release tree')
    ]
    sync = original[original.index('step "uv sync') : original.index("step 'ownership and modes'")]
    shell = (
        "set -euo pipefail; SCRIPT_DIRECTORY=$1; WEB_RELEASE=$2; "
        "WEB_RELEASE_SHA256=$3; SOURCE=$4; INTERPRETER=$5; UV_PYTHON_INSTALL_DIR=$6; "
        "UV=$7; RELEASE=$8; PYTHON_VERSION=3.14.6; RELEASE_EXTRAS=(--extra server); "
        "step() { :; }; " + function + selection + sync
    )
    result = subprocess.run(
        [
            "bash",
            "-c",
            shell,
            "fixture",
            str(scripts),
            str(tmp_path / "web assets") if enabled else "",
            "a" * 64,
            environment["HFCACHE_SOURCE"],
            str(donor),
            str(tmp_path / "python"),
            str(uv),
            str(release),
        ],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )
    assert result.returncode == 0, result.stderr
    arguments = json.loads(sync_record.read_text())
    assert arguments[-2:] == ["--python", str(prepared) if enabled else "3.14.6"]
    if enabled:
        assert json.loads(command.read_text())[-4:] == [
            "--interpreter",
            str(donor),
            "--python-root",
            str(tmp_path / "python"),
        ]
    else:
        assert not command.exists()


def test_web_stage_hook_passes_exact_paths_to_host_verifier_before_release_rename(tmp_path):
    scripts, command, environment = web_installer_fixture(tmp_path)
    source = (scripts / "install-release.sh").read_text()
    start = source.index("web_release() {\n")
    end = source.index("\n}\n", start) + 3
    function = source[start:end]
    release, staging = tmp_path / "release assets", tmp_path / "staging tree"
    staging.mkdir()
    script = (
        "set -euo pipefail; SCRIPT_DIRECTORY=$1; WEB_RELEASE=$2; "
        "WEB_RELEASE_SHA256=$3; SOURCE=$4;\n"
        + function
        + '\nweb_release stage-native --destination "$5"'
    )
    result = subprocess.run(
        [
            "bash",
            "-c",
            script,
            "fixture",
            str(scripts),
            str(release),
            "a" * 64,
            environment["HFCACHE_SOURCE"],
            str(staging),
        ],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(command.read_text())["argv"] == [
        "stage-native",
        "--release",
        str(release),
        "--index-sha256",
        "a" * 64,
        "--source",
        environment["HFCACHE_SOURCE"],
        "--destination",
        str(staging),
    ]
    copy = source.index('cp -R "${SOURCE}/${item}" "${STAGING}/"')
    stage = source.index('web_release stage-native --destination "${STAGING}"')
    rename = source.index('mv -T "${STAGING}" "${RELEASE}"')
    assert copy < stage < rename


@pytest.fixture
def native_web_profile():
    spec = importlib.util.spec_from_file_location(
        "native_web_profile", ROOT / "scripts/release-profile.py"
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_native_web_index(root, index):
    (root / "web-release.json").write_text(
        json.dumps(index, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    )


@pytest.fixture
def indexed_native_web(tmp_path):
    root = tmp_path / "native-web"
    root.mkdir()
    files = {
        "ui/manifest.json": b'{"structural_test_fixture":true}\n',
        "ui/assets/app-12345678.js": b"binary fixture bytes\x00\xff",
        **{
            "host-helper/" + name: ("captured " + name + "\n").encode()
            for name in (
                "host-helper.py",
                "hfcache-host-helper.service",
                "hfcache-host-helper.cil",
                "host_policy.py",
                "host_protocol.py",
                "host_peer.py",
                "host_configuration.py",
                "host_actions.py",
                "host_selinux.py",
            )
        },
    }
    for name, body in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
    index = {
        "schema_version": 1,
        "kind": "hfcache_web_release",
        "version": "0.2.2",
        "source_commit": "a" * 40,
        "source_files": {"pyproject.toml": "b" * 64},
        "files": {name: hashlib.sha256(body).hexdigest() for name, body in files.items()},
        "ui_manifest_sha256": hashlib.sha256(files["ui/manifest.json"]).hexdigest(),
    }
    write_native_web_index(root, index)
    return root, index


def test_native_web_classification_verifies_copied_closure_without_candidate_execution(
    native_web_profile, indexed_native_web
):
    root, _ = indexed_native_web
    assert not (root / ".venv").exists()
    assert native_web_profile.native_web_layout(root, "0.2.2") is None


def test_native_web_classification_refuses_dangling_index_without_discarding_it(
    native_web_profile, tmp_path
):
    index = tmp_path / "web-release.json"
    index.symlink_to("unknown-index.json")
    with pytest.raises(OSError, match="Too many levels of symbolic links"):
        native_web_profile.native_web_layout(tmp_path, "0.2.2")
    assert index.is_symlink()
    assert index.readlink() == Path("unknown-index.json")


def test_native_web_classification_refuses_duplicate_index_fields(
    native_web_profile, indexed_native_web
):
    root, _ = indexed_native_web
    index = root / "web-release.json"
    raw = index.read_text()
    index.write_text('{"kind":"hfcache_web_release",' + raw[1:])
    with pytest.raises(ValueError, match="duplicate native index field"):
        native_web_profile.native_web_layout(root, "0.2.2")


@pytest.mark.parametrize(
    "change",
    [
        {"source_commit": "A" * 40},
        {"source_commit": "a" * 39},
        {"source_commit": None},
        {"files": []},
        {"files": {}},
        {"source_files": []},
        {"source_files": {}},
        {"source_files": {"../escaped": "a" * 64}},
        {"source_files": {"pyproject.toml": "invalid digest"}},
        {"version": "0.9.9"},
        {"ui_manifest_sha256": "f" * 64},
        {"schema_version": True},
    ],
)
def test_native_web_classification_refuses_unknown_identity_or_map(
    native_web_profile, indexed_native_web, change
):
    root, index = indexed_native_web
    write_native_web_index(root, index | change)
    with pytest.raises(ValueError, match="native web"):
        native_web_profile.native_web_layout(root, "0.2.2")


@pytest.mark.parametrize(
    "name", ["ui/manifest.json", "ui/assets/app-12345678.js", "host-helper/host_policy.py"]
)
@pytest.mark.parametrize("change", ["missing", "changed", "unindexed"])
def test_native_web_classification_refuses_missing_changed_or_extra_copied_bytes(
    native_web_profile, indexed_native_web, name, change
):
    root, _ = indexed_native_web
    path = root / name
    if change == "missing":
        path.unlink()
    elif change == "changed":
        path.write_bytes(b"changed indexed bytes\n")
    else:
        path.with_name("unindexed-extra").write_bytes(b"unindexed copied bytes\n")
    with pytest.raises((ValueError, OSError)):
        native_web_profile.native_web_layout(root, "0.2.2")


@pytest.mark.parametrize(
    "name",
    [
        "host-helper.py",
        "hfcache-host-helper.service",
        "hfcache-host-helper.cil",
        "host_policy.py",
        "host_protocol.py",
        "host_peer.py",
        "host_configuration.py",
        "host_actions.py",
        "host_selinux.py",
    ],
)
def test_native_web_classification_requires_all_nine_helper_index_members(
    native_web_profile, indexed_native_web, name
):
    root, index = indexed_native_web
    del index["files"]["host-helper/" + name]
    write_native_web_index(root, index)
    with pytest.raises(ValueError, match="native web closure not proven"):
        native_web_profile.native_web_layout(root, "0.2.2")


@pytest.mark.parametrize(
    "name", ["install-release.sh", "release-functions.sh", "check-hardening.sh"]
)
def test_operator_shell_scripts_parse_without_running(name):
    subprocess.run(["bash", "-n", str(ROOT / "scripts" / name)], check=True)


@pytest.mark.parametrize("shape", ["shared-parent", "shared-file", "hardlink"])
def test_shared_or_hardlinked_lock_is_unexplained(release_fixture, shape):
    prefix, runtime, _, _ = release_fixture
    lock = runtime / "hfcache.lock"
    if shape == "shared-parent":
        runtime.chmod(0o755)
    elif shape == "shared-file":
        lock.chmod(0o640)
    else:
        (runtime / "alias").hardlink_to(lock)
    result = run_library(release_fixture)
    assert result.returncode == 1
    assert "unexplained" in result.stderr
    assert (prefix / "current").readlink() == Path("releases/0.1.9")


def test_rollback_without_observer_support_preserves_pending_state(release_fixture):
    prefix, _, _, environment = release_fixture
    clients = Path(environment["HFCACHE_CLIENT_STATE_DIRECTORY"])
    clients.mkdir(mode=0o700)
    pending = clients / "pending.json"
    pending.write_bytes(b"unresolved evidence, even if a future format\n")
    result = run_library(release_fixture)
    assert result.returncode == 1
    assert "retained scheduled handles" in result.stderr
    assert (prefix / "current").readlink() == Path("releases/0.1.9")
    assert pending.read_bytes() == b"unresolved evidence, even if a future format\n"


def test_observer_capable_upgrade_retains_pending_evidence(release_fixture):
    prefix, _, _, environment = release_fixture
    clients = Path(environment["HFCACHE_CLIENT_STATE_DIRECTORY"])
    clients.mkdir(mode=0o700)
    pending = clients / "pending.json"
    pending.write_bytes(b"retained evidence\n")
    python = prefix / "releases/0.1.10/.venv/bin/python"
    python.write_text("#!/bin/sh\nexit 0\n")
    python.chmod(0o755)
    result = run_library(release_fixture)
    assert result.returncode == 0, result.stderr
    assert (prefix / "current").readlink() == Path("releases/0.1.10")
    assert pending.read_bytes() == b"retained evidence\n"


@pytest.mark.parametrize("cgroup", ["/system.slice/hfcache-api.service", "unknown"])
def test_unavailable_task_accounting_does_not_hide_live_cgroup(release_fixture, cgroup):
    _, _, states, _ = release_fixture
    states.write_text(
        json.dumps(
            {
                "hfcache-api.service": {
                    "TasksCurrent": "[not set]",
                    "ControlGroup": cgroup,
                }
            }
        )
    )
    result = run_library(release_fixture)
    assert result.returncode == 1
    assert "cannot prove" in result.stderr


def test_unrealized_cgroup_with_no_main_or_control_process_is_quiescent(release_fixture):
    _, _, states, _ = release_fixture
    states.write_text(
        json.dumps(
            {
                "hfcache-api.service": {
                    "TasksCurrent": "[not set]",
                    "ControlGroup": "",
                }
            }
        )
    )
    result = run_library(release_fixture)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("valid_policy", [True, False])
@pytest.mark.parametrize("with_mcp", [True, False])
def test_installed_smoke_parses_required_hub_policy_without_borrowing_credentials(
    tmp_path, valid_policy, with_mcp
):
    source = (ROOT / "scripts/install-release.sh").read_text()
    start = source.index("smoke() (\n")
    end = source.index("\n)\n", start) + 3
    function = source[start:end]
    archive = tmp_path / "archive-never-opened"
    config = tmp_path / "config.toml"
    config.write_text(
        f'schema_version={1 if valid_policy else 2}\n[storage]\narchive_root="{archive}"\n'
        'archive_id="00000000-0000-0000-0000-000000000001"\n[hub]\ntoken_mode="required"\n'
    )
    environment = dict(os.environ) | {"HFCACHE_ARCHIVE_CONFIG": str(config)}
    for name in (
        "HF_TOKEN",
        "HUGGING_FACE_HUB_TOKEN",
        "HUGGINGFACE_HUB_TOKEN",
        "CREDENTIALS_DIRECTORY",
    ):
        environment.pop(name, None)
    script = (
        f"set -euo pipefail; step() {{ :; }}; WITH_MCP={str(with_mcp).lower()};\n"
        + function
        + '\nsmoke "$1"'
    )
    result = subprocess.run(
        ["bash", "-c", script, "fixture", str(Path(sys.executable).parent / "hfcache")],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )
    assert (result.returncode == 0) is valid_policy, result.stderr
    assert not archive.exists()
    assert "HFARG008" not in result.stderr


def test_native_offline_activation_keeps_fixed_runtime_and_offline_confinement():
    source = (ROOT / "scripts/install-release.sh").read_text()
    branch = source.split("if [[ ${MODE} == prepare-intent-state ]]; then", 1)[1].split(
        "[[ -z ${INTENT_ARCHIVE_ID} ]]", 1
    )[0]
    assert (
        "HFCACHE_SYSTEMCTL=/usr/bin/systemctl "
        "HFCACHE_RUNTIME_DIRECTORY=/run/hfcache require_quiescent" in branch
    )
    assert '"${selected}/.venv/bin/python" -I -B -m hfcache.api.intent_activation' in branch
    for control in [
        "--property=User=hfcache",
        "--property=Group=hfcache",
        "--property=NoNewPrivileges=yes",
        "--property=PrivateNetwork=yes",
        "--property=IPAddressDeny=any",
        "--property=RestrictAddressFamilies=AF_UNIX",
        "--property=ProtectSystem=strict",
        "--property=ProtectHome=yes",
        "--property=UnsetEnvironment=HF_TOKEN",
        "--property=Environment=HF_HOME=/run/hfcache/hf-home",
        "HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1",
        "--property=InaccessiblePaths=${native_masks}",
        "--property=BindPaths=/run/hfcache/intent-activation:/run/hfcache",
        "--native-masks-only",
        '"--native-masks=${native_masks}" --native-revision "${native_revision}"',
        "--property=ProtectProc=invisible",
    ]:
        assert control in branch
    writable = next(line for line in branch.splitlines() if "ReadWritePaths=" in line)
    assert "/srv/hfcache" not in writable
    assert "LoadCredential" not in branch
    assert "ImportCredential" not in branch
    assert "--backup-directory /var/lib/hfcache/intent-activation-backups/initial" in branch
    assert 'source = Path("/run/hfcache/intent-activation/hfcache.lock.intent")' in branch
    assert 'target = Path("/run/hfcache/hfcache.lock.intent")' in branch
    assert "os.link(source, target, follow_symlinks=False)" in branch
    assert "os.fsync(descriptor)" in branch
    assert "native policy changed; preserve partial activation" in branch
