"""Strict web gate controls use disposable fake tools, never runtime services.

These tests establish refusal and ordering, not frontend or installed acceptance.
The real locked workspace and browser smoke execute separately in the strict gate.
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
WEB_CHECKS = (
    "lint",
    "typecheck",
    "test:strict-fixtures",
    "test:unit",
    "test:component",
    "build",
    "test:browser",
)
WEB_FILES = ("package.json", "pnpm-lock.yaml", "tsconfig.json")


def web_gate_fixture(tmp_path, *, missing=None, cockpit=False):
    repository = tmp_path / "repository"
    scripts = repository / "scripts"
    scripts.mkdir(parents=True)
    script = scripts / "check.sh"
    shutil.copyfile(ROOT / "scripts/check.sh", script)
    if missing != "web":
        web = repository / "web"
        web.mkdir()
        for name in WEB_FILES:
            if missing != name:
                (web / name).write_text("fixture\n")
    if cockpit:
        (repository / "cockpit").mkdir()
    tool_directory = tmp_path / "tools"
    tool_directory.mkdir()
    (tool_directory / "dirname").symlink_to(shutil.which("dirname"))
    calls = tmp_path / "calls"
    for name in ("uv", "node", "pnpm", "make"):
        if name == missing:
            continue
        tool = tool_directory / name
        tool.write_text(
            '#!/bin/sh\nprintf "%s" "${0##*/}" >> "$GATE_FIXTURE_CALLS"\n'
            'for arg do printf "|%s" "$arg" >> "$GATE_FIXTURE_CALLS"; done\n'
            'printf "\\n" >> "$GATE_FIXTURE_CALLS"\n'
            'if [ "${0##*/}" = uv ] && [ "$1" = build ] '
            '&& [ -n "${GATE_FIXTURE_REMOVE:-}" ]; then\n'
            '  /usr/bin/rm -- "$GATE_FIXTURE_REMOVE"\n'
            "fi\n"
            'if [ "${0##*/}" = pnpm ]; then\n'
            '  if [ "${3:-}" = install ] && [ "${GATE_FIXTURE_FAIL:-}" = install ]; then\n'
            "    exit 23\n"
            "  fi\n"
            '  if [ "${3:-}" = run ] && [ "${4:-}" = "${GATE_FIXTURE_FAIL:-}" ]; then\n'
            "    exit 23\n"
            "  fi\n"
            "fi\n"
            "exit 0\n"
        )
        tool.chmod(0o755)
    environment = {
        **os.environ,
        "PATH": str(tool_directory),
        "PNPM_HOME": str(tmp_path / "absent-pnpm-home"),
        "GATE_FIXTURE_CALLS": str(calls),
    }
    for name in ("BASH_ENV", "ENV", "SHELLOPTS", "BASHOPTS", "CDPATH"):
        environment.pop(name, None)
    return script, environment, calls


def invoke(script, environment, *arguments):
    return subprocess.run(
        ["/usr/bin/bash", str(script), *arguments],
        env=environment,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )


@pytest.mark.parametrize("missing", ["web", *WEB_FILES, "node", "pnpm"])
@pytest.mark.parametrize("extended", [False, True])
def test_required_web_missing_prerequisite_refuses_before_backend(tmp_path, missing, extended):
    script, environment, calls = web_gate_fixture(tmp_path, missing=missing)
    result = invoke(script, environment, "--require-web", *(["--with-build"] if extended else []))
    assert result.returncode == 69, result.stderr
    assert "Web gate required" in result.stderr
    assert "all checks passed" not in result.stdout
    assert not calls.exists()


def test_required_web_preserves_backend_cockpit_and_extended_build_order(tmp_path):
    script, environment, calls = web_gate_fixture(tmp_path, cockpit=True)
    result = invoke(script, environment, "--require-web", "--require-cockpit", "--with-build")
    assert result.returncode == 0, result.stderr
    invocations = calls.read_text().splitlines()
    frontend = [call for call in invocations if call.startswith("pnpm|")]
    assert frontend == ["pnpm|--dir|web|install|--frozen-lockfile"] + [
        f"pnpm|--dir|web|run|{check}" for check in WEB_CHECKS
    ]
    cockpit_index = next(i for i, call in enumerate(invocations) if call.startswith("make|"))
    first_web_index = invocations.index(frontend[0])
    assert invocations[0] == "uv|lock|--check"
    assert any(
        call.endswith("|python|scripts/check-docs.py") for call in invocations[:cockpit_index]
    )
    assert any(
        call.endswith("|python|scripts/check-installations.py")
        for call in invocations[:cockpit_index]
    )
    assert cockpit_index < first_web_index < len(invocations) - 1
    assert invocations[-1].endswith("|pytest|-m|build")
    assert "OMITTED" not in result.stderr + result.stdout
    assert "SKIPPED" not in result.stderr + result.stdout


@pytest.mark.parametrize("stage", ["install", *WEB_CHECKS])
def test_each_required_web_failure_stops_without_success_or_later_stages(tmp_path, stage):
    script, environment, calls = web_gate_fixture(tmp_path)
    environment["GATE_FIXTURE_FAIL"] = stage
    result = invoke(script, environment, "--require-web", "--with-build")
    assert result.returncode == 23, result.stderr
    invocations = calls.read_text().splitlines()
    expected_last = (
        "pnpm|--dir|web|install|--frozen-lockfile"
        if stage == "install"
        else f"pnpm|--dir|web|run|{stage}"
    )
    assert invocations[-1] == expected_last
    assert "all checks passed" not in result.stdout
    assert not any(call.endswith("|pytest|-m|build") for call in invocations)


@pytest.mark.parametrize("removed", ["package.json", "node", "pnpm"])
def test_required_web_rechecks_late_source_and_tool_disappearance(tmp_path, removed):
    script, environment, calls = web_gate_fixture(tmp_path)
    target = (
        script.parent.parent / "web" / removed
        if removed in WEB_FILES
        else Path(environment["PATH"]) / removed
    )
    environment["GATE_FIXTURE_REMOVE"] = str(target)
    result = invoke(script, environment, "--require-web")
    assert result.returncode == 69, result.stderr
    assert "Web gate required" in result.stderr
    assert "all checks passed" not in result.stdout
    assert all(not call.startswith("pnpm|") for call in calls.read_text().splitlines())


def test_required_web_tool_loss_after_final_discovery_cannot_become_a_skip(tmp_path):
    script, environment, calls = web_gate_fixture(tmp_path)
    bootstrap = tmp_path / "controlled-discovery.bash"
    bootstrap.write_text(
        "node_probes=0\n"
        "command() {\n"
        '  if [[ "$1" == -v && "${2:-}" == node ]]; then\n'
        '    if builtin command "$@"; then\n'
        "      node_probes=$((node_probes+1))\n"
        '      if [[ $node_probes == 2 ]]; then /usr/bin/rm -- "$GATE_FIXTURE_PNPM"; fi\n'
        "      return 0\n"
        "    fi\n"
        "    return 1\n"
        "  fi\n"
        '  builtin command "$@"\n'
        "}\n"
    )
    environment["BASH_ENV"] = str(bootstrap)
    environment["GATE_FIXTURE_PNPM"] = str(Path(environment["PATH"]) / "pnpm")
    result = invoke(script, environment, "--require-web")
    assert result.returncode != 0
    assert "all checks passed" not in result.stdout
    assert "OMITTED" not in result.stderr + result.stdout
    assert all(not call.startswith("pnpm|") for call in calls.read_text().splitlines())


def test_default_backend_gate_loudly_omits_web_without_requiring_node(tmp_path):
    script, environment, calls = web_gate_fixture(tmp_path, missing="node")
    result = invoke(script, environment)
    assert result.returncode == 0, result.stderr
    assert "web/ exists but its gate is OMITTED; use --require-web" in result.stderr
    assert "does not establish web UI acceptance" in result.stderr
    assert all(not call.startswith("pnpm|") for call in calls.read_text().splitlines())


@pytest.mark.parametrize("help_flag", ["-h", "--help"])
def test_help_is_safe_even_without_web_prerequisites(tmp_path, help_flag):
    script, environment, calls = web_gate_fixture(tmp_path, missing="web")
    result = invoke(script, environment, "--require-web", help_flag)
    assert result.returncode == 0, result.stderr
    assert "--require-web" in result.stdout
    assert "preliminary browser smoke" in result.stdout
    assert not calls.exists()


def test_unimplemented_functional_flag_cannot_silently_claim_acceptance(tmp_path):
    script, environment, calls = web_gate_fixture(tmp_path)
    result = invoke(script, environment, "--require-web", "--with-web-functional")
    assert result.returncode == 64
    assert "unknown argument: --with-web-functional" in result.stderr
    assert "all checks passed" not in result.stdout
    assert not calls.exists()
