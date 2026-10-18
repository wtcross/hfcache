"""Human inspection must precede installed credentials, managers and workloads."""

import runpy
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


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


@pytest.mark.parametrize("arguments", [["--help"], ["status", "--help"]])
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


def test_fixed_client_role_help_needs_no_profile(monkeypatch):
    module = runpy.run_path(str(ROOT / "scripts/container-service.py"))
    main = module["main"]

    def forbidden():
        pytest.fail("client help attempted installed profile access")

    monkeypatch.setitem(main.__globals__, "load_profile", forbidden)
    monkeypatch.setattr(sys, "argv", ["container-service.py", "client", "status", "--help"])
    assert main() == 0


@pytest.mark.parametrize("argument", ["--dry-run", "--engine", "unknown"])
def test_fixed_launcher_invalid_grammar_precedes_profile(monkeypatch, argument):
    module = runpy.run_path(str(ROOT / "scripts/container-service.py"))
    main = module["main"]

    def forbidden():
        pytest.fail("invalid grammar attempted installed profile access")

    monkeypatch.setitem(main.__globals__, "load_profile", forbidden)
    monkeypatch.setattr(sys, "argv", ["container-service.py", argument])
    assert main() == 20
