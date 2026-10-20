"""The explicit plugin gate cannot succeed by skipping frontend execution.

These are isolated gate-control fixtures, not actual frontend acceptance. The
real package gate separately runs the pinned toolchain and mounted Firefox suite.
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def gate_fixture(tmp_path, *, plugin=True, pnpm=True, make=True):
    repository = tmp_path / "fixture"
    scripts = repository / "scripts"
    scripts.mkdir(parents=True)
    script = scripts / "check.sh"
    shutil.copyfile(ROOT / "scripts/check.sh", script)
    if plugin:
        (repository / "cockpit").mkdir()
    tools = tmp_path / "tools"
    tools.mkdir()
    (tools / "dirname").symlink_to(shutil.which("dirname"))
    marker = tmp_path / "calls"
    for name, present in (("uv", True), ("pnpm", pnpm), ("make", make)):
        if present:
            executable = tools / name
            executable.write_text(
                '#!/bin/sh\nprintf "%s" "${0##*/}" >> "$GATE_FIXTURE_CALLS"\n'
                'for arg do printf "|%s" "$arg" >> "$GATE_FIXTURE_CALLS"; done\n'
                'printf "\\n" >> "$GATE_FIXTURE_CALLS"\n'
            )
            executable.chmod(0o755)
    environment = {
        **os.environ,
        "PATH": str(tools),
        "PNPM_HOME": str(tmp_path / "absent-pnpm-home"),
        "GATE_FIXTURE_CALLS": str(marker),
    }
    for name in ("BASH_ENV", "ENV", "SHELLOPTS", "BASHOPTS", "CDPATH"):
        environment.pop(name, None)
    return script, environment, marker


def invoke_gate(script, environment, *arguments):
    return subprocess.run(
        ["/usr/bin/bash", str(script), *arguments],
        env=environment,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )


@pytest.mark.parametrize("missing", ["plugin", "pnpm", "make"])
@pytest.mark.parametrize("extended", [False, True])
def test_required_frontend_missing_prerequisite_refuses_before_backend(tmp_path, missing, extended):
    script, environment, calls = gate_fixture(tmp_path, **{missing: False})
    result = invoke_gate(
        script, environment, "--require-cockpit", *(["--with-build"] if extended else [])
    )
    assert result.returncode == 69, result.stderr
    assert "Cockpit gate required" in result.stderr
    assert "SKIPPED" not in result.stderr + result.stdout
    assert "all checks passed" not in result.stdout
    assert not calls.exists(), "No backend/tool command runs after a missing prerequisite"


def test_required_frontend_executes_make_and_composes_with_extended_gate(tmp_path):
    script, environment, calls = gate_fixture(tmp_path)
    result = invoke_gate(script, environment, "--with-build", "--require-cockpit")
    assert result.returncode == 0, result.stderr
    invocations = calls.read_text().splitlines()
    assert "make|-C|cockpit|check|PNPM=" + str(Path(environment["PATH"]) / "pnpm") in invocations
    assert invocations[-1].endswith("|pytest|-m|build")
    assert "SKIPPED" not in result.stderr + result.stdout


def test_default_backend_mode_keeps_a_loud_unaccepted_frontend_skip(tmp_path):
    script, environment, calls = gate_fixture(tmp_path, pnpm=False)
    result = invoke_gate(script, environment)
    assert result.returncode == 0, result.stderr
    assert "plugin gate SKIPPED" in result.stderr
    assert all(not call.startswith("make|") for call in calls.read_text().splitlines())


def test_required_frontend_rechecks_tools_instead_of_accepting_a_late_skip(tmp_path):
    script, environment, calls = gate_fixture(tmp_path)
    uv = Path(environment["PATH"]) / "uv"
    uv.write_text('#!/bin/sh\nif [ "$1" = build ]; then /usr/bin/rm -- "$GATE_FIXTURE_MAKE"; fi\n')
    environment["GATE_FIXTURE_MAKE"] = str(Path(environment["PATH"]) / "make")
    result = invoke_gate(script, environment, "--require-cockpit")
    assert result.returncode == 69, result.stderr
    assert "Cockpit gate required" in result.stderr
    assert "SKIPPED" not in result.stderr + result.stdout
    assert "all checks passed" not in result.stdout
    assert not calls.exists()


def test_required_frontend_cannot_skip_after_final_successful_tool_discovery(tmp_path):
    script, environment, calls = gate_fixture(tmp_path)
    bootstrap = tmp_path / "controlled-final-discovery.bash"
    # Control only the file-removal ordering: the final discovery returns its
    # genuine successful result immediately after its owned fake make vanishes.
    bootstrap.write_text(
        "make_probes=0\n"
        "command() {\n"
        '  if [[ "$1" == -v && "${2:-}" == make ]]; then\n'
        '    if builtin command "$@"; then\n'
        "      make_probes=$((make_probes+1))\n"
        "      if [[ $make_probes == 2 ]]; then\n"
        '        /usr/bin/rm -- "$GATE_FIXTURE_MAKE"\n'
        "      fi\n"
        "      return 0\n"
        "    fi\n"
        "    return 1\n"
        "  fi\n"
        '  builtin command "$@"\n'
        "}\n"
    )
    environment["BASH_ENV"] = str(bootstrap)
    environment["GATE_FIXTURE_MAKE"] = str(Path(environment["PATH"]) / "make")
    result = invoke_gate(script, environment, "--require-cockpit")
    assert result.returncode != 0, "A successful preflight cannot authorize a later skipped stage"
    assert "SKIPPED" not in result.stderr + result.stdout
    assert "all checks passed" not in result.stdout
    assert not Path(environment["GATE_FIXTURE_MAKE"]).exists()
    assert all(not call.startswith("make|") for call in calls.read_text().splitlines())
