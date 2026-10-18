"""Runbooks parse real CLI grammar; only named fixture suites execute workloads."""

import re
import shlex
import subprocess
from contextlib import ExitStack
from pathlib import Path

import pytest
from typer.core import TyperGroup
from typer.main import get_command

from hfcache import cli

ROOT = Path(__file__).parents[2]
RUNBOOKS = (ROOT / "docs/operations.md", ROOT / "docs/recovery.md")
GUIDES = (*RUNBOOKS, ROOT / "docs/quickstart.md")


def blocks(path: Path) -> list[str]:
    return re.findall(r"```bash\n(.*?)\n```", path.read_text(), re.DOTALL)


def commands() -> list[list[str]]:
    result = []
    for path in GUIDES:
        for block in blocks(path):
            for line in block.replace("\\\n", " ").splitlines():
                words = shlex.split(line, comments=True)
                if words and words[0] in {"${HF[@]}", "H", "/usr/local/libexec/hfcache-client"}:
                    assert "--config" not in words
                    result.append(["--client-config", "/fixture/client.toml", "--json", *words[1:]])
    return result


@pytest.mark.parametrize("path", GUIDES, ids=lambda path: path.name)
def test_runbook_shell_is_syntax_only_without_running_recipes(path):
    for block in blocks(path):
        subprocess.run(["bash", "-n"], input=block, text=True, check=True, capture_output=True)


@pytest.mark.parametrize("arguments", commands(), ids=lambda words: " ".join(words[3:]))
def test_every_runbook_operational_example_parses_without_invoking_callbacks(arguments):
    command = get_command(cli.app)
    with ExitStack() as stack:
        context = stack.enter_context(command.make_context("hfcache", list(arguments)))
        while isinstance(command, TyperGroup):
            pending = [
                *context._protected_args,
                *context.args,
            ]  # Only inspect parser state; never invoke.
            name, child, remaining = command.resolve_command(context, pending)
            assert child is not None
            command = child
            context = stack.enter_context(command.make_context(name, remaining, parent=context))
        assert context.args == []


def test_runbooks_preserve_uncertainty_and_do_not_offer_direct_writer_aliases():
    for path in RUNBOOKS:
        text = path.read_text()
        assert not re.search(r"\$[HD]\b|/opt/hfcache/current/\.venv", text)
        assert "never" in text.lower()
        assert "new key" in text
        assert "deployment-status.md" in text
        assert "operation" in text
        assert "verifier" in text
        assert "handles" in text
