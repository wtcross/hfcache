"""Human audiences, real Markdown references and helper coverage fail closed offline."""

import json
import subprocess
from pathlib import Path

import pytest
from typer.main import get_command
from typer.testing import CliRunner

from hfcache import cli
from tests.docs_contract import CHECKER, ROOT


@pytest.mark.parametrize(
    "text",
    [
        "MCP-004 adds tools",
        "DOC-018",
        "NEW-123 implements a thing",
        "[plan](docs/agents/plans/current.md)",
        "`docs/plans/current.md`",
        "[task][x]\n\n[x]: ../agents/plans/tasks/mcp-004.md",
        '<a href="docs%2fagents%2fprogress.md">history</a>',
        "`docs%252Fagents%252Fworkflow.md`",
        "Phase 2 introduces the service",
        "Stage 2 introduces the MCP service.",
        "mcp-004 adds tools.",
        "This implementation plan owns the feature.",
        "The local CLI is unbounded.",
    ],
)
def test_leaked_tracking_and_old_client_claims_are_rejected(text):
    assert CHECKER["audience_errors"](text)


def test_real_domain_concepts_identifiers_and_runtime_events_are_allowed():
    text = (
        "hfcache plan; recovery plans; JSON-RPC; HFAPI019; AD-17 FS-19 TX-06 "
        "CP-11 INV-010 SHA-256 UID-981; progress events and pending.json"
    )
    assert CHECKER["audience_errors"](text) == []


def test_markdown_parser_checks_rendered_references_and_real_anchors(tmp_path):
    target = tmp_path / "a (copy).md"
    target.write_text("""Heading *with* `code`
========================
## Same
## Same
## Same-1
## Same
<a id='explicit' name='legacy'></a>
```
## fake
```
    ## indented-fake
""")
    source = tmp_path / "README.md"
    source.write_text(r"""[angle](<a (copy).md#heading-with-code> "title")
[escaped](a%20\(copy\).md#same-1-1)
[reference][x]
[collapsed][]
![image](a%20%28copy%29.md#same-2)
<a href='a%20%28copy%29.md#explicit'>anchor</a>
<img src="a%20%28copy%29.md#legacy">

[x]: <a (copy).md#same-1>
[collapsed]: <a (copy).md#heading-with-code>
""")
    assert CHECKER["check_links"](tmp_path, [source]) == []
    anchors = CHECKER["markdown_references"](target.read_text())[1]
    assert {"same", "same-1", "same-1-1", "same-2", "explicit", "legacy"} <= anchors
    assert "fake" not in anchors
    assert "indented-fake" not in anchors


@pytest.mark.parametrize(
    "markup",
    [
        "[x][missing]\n\n[missing]: absent.md",
        "[missing][]\n\n[missing]: absent.md",
        "![x](absent.png)",
        '<img src="absent.png">',
        "<a href='absent.md'>x</a>",
        "[x](README.md#absent)",
    ],
)
def test_missing_reference_image_html_or_fragment_fails(tmp_path, markup):
    source = tmp_path / "README.md"
    source.write_text(markup)
    assert CHECKER["check_links"](tmp_path, [source])


@pytest.mark.parametrize("link", ["../outside.md", "outside.md", "escape/nested.md"])
def test_escaping_links_do_not_inspect_outside_files(tmp_path, monkeypatch, link):
    root = tmp_path / "repo"
    root.mkdir()
    outside = tmp_path / "outside.md"
    outside.write_text("private")
    (root / "outside.md").symlink_to(outside)
    (root / "escape").symlink_to(tmp_path, target_is_directory=True)
    source = root / "README.md"
    source.write_text(f"[x]({link})")
    read_text = Path.read_text

    def owned_only(path, *args, **kwargs):
        assert path == source
        return read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", owned_only)
    assert CHECKER["check_links"](root, [source])


def test_discovery_includes_new_guides_and_adrs_but_excludes_only_owned_record_roots(tmp_path):
    for name in (
        "README.md",
        "docs/new/guide.md",
        "docs/adr/new.md",
        "examples/README.md",
        "AGENTS.md",
        "CLAUDE.md",
        "docs/agents/history.md",
        "node_modules/vendor.md",
        ".scratch/build.md",
    ):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture")
    paths = CHECKER["human_documents"](CHECKER["repository_index"](tmp_path))
    assert {p.relative_to(tmp_path).as_posix() for p in paths} == {
        "README.md",
        "docs/new/guide.md",
        "docs/adr/new.md",
        "examples/README.md",
    }


@pytest.mark.parametrize("fault", ["missing", "duplicate", "stale", "unclassified"])
def test_helper_catalog_requires_every_file_once_and_explicit_inspection_mode(tmp_path, fault):
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts/non-executable.py").write_text("# fixture")
    assert not (tmp_path / "scripts/non-executable.py").stat().st_mode & 0o111
    (tmp_path / "docs").mkdir()
    row = "| [tool](../scripts/non-executable.py) | purpose | inputs | effects | tests |\n"
    catalog = row
    modes = {"non-executable.py": "python"}
    if fault == "missing":
        catalog = ""
    elif fault == "duplicate":
        catalog += row
    elif fault == "stale":
        catalog += row.replace("non-executable.py", "removed.py")
    else:
        modes = {}
    (tmp_path / "docs/scripts.md").write_text(catalog)
    assert CHECKER["inventory_errors"](tmp_path, modes)


def test_checker_and_code_fences_never_execute_commands(tmp_path, monkeypatch):
    (tmp_path / "README.md").write_text("```bash\nmkdir SHOULD-NOT-EXIST\n```\n")
    (tmp_path / "scripts").mkdir()
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/scripts.md").write_text("")

    def forbidden(*args, **kwargs):
        pytest.fail("documentation checking executed a process")

    monkeypatch.setattr(subprocess, "run", forbidden)
    CHECKER["check"](tmp_path)
    assert not (tmp_path / "SHOULD-NOT-EXIST").exists()


def test_inline_formatting_cannot_hide_an_implementation_identifier(tmp_path):
    (tmp_path / "README.md").write_text("MCP-**004** adds tools.")
    (tmp_path / "scripts").mkdir()
    _, errors = CHECKER["check"](tmp_path)
    assert any("implementation identifier" in error for error in errors)


@pytest.mark.parametrize("kind", ["catalog", "helper", "human", "alias", "directory_alias"])
def test_symlinks_cannot_read_outside_or_hide_agent_authority(tmp_path, monkeypatch, kind):
    root = tmp_path / "repo"
    root.mkdir()
    (root / "scripts").mkdir()
    (root / "docs/agents").mkdir(parents=True)
    outside = tmp_path / "outside.md"
    outside.write_text("private")
    (root / "README.md").write_text(
        "[authority](docs/authority.md)" if kind in {"alias", "directory_alias"} else "Overview"
    )
    (root / "docs/agents/record.md").write_text("MCP-004")
    link = {
        "catalog": root / "docs/scripts.md",
        "helper": root / "scripts/tool.py",
        "human": root / "guide.md",
        "alias": root / "docs/authority.md",
        "directory_alias": root / "docs/authority.md",
    }[kind]
    target = (
        root / "docs/agents"
        if kind == "directory_alias"
        else root / "docs/agents/record.md"
        if kind == "alias"
        else outside
    )
    link.symlink_to(target, target_is_directory=kind == "directory_alias")
    read_text = Path.read_text

    def approved_only(path, *args, **kwargs):
        assert path not in {outside, link, root / "docs/agents/record.md"}
        return read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", approved_only)
    _, errors = CHECKER["check"](root)
    assert any(
        "unsafe" in error or "symlink" in error or "agent record" in error for error in errors
    )


def test_complete_repository_audience_links_anchors_and_catalog_pass_without_baseline():
    documents, errors = CHECKER["check"](ROOT)
    assert len(documents) > 150
    assert errors == []
    inventory = json.loads((ROOT / "docs/agents/documentation-inventory.json").read_text())
    assert "transitional_tracking_matches" not in inventory


def test_every_public_cli_help_path_is_current_and_does_not_construct_api_client(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("help constructed API client")

    monkeypatch.setattr(cli.cli_client, "connect", forbidden)
    runner = CliRunner()

    def walk(command, path):
        result = runner.invoke(cli.app, [*path, "--help"])
        assert result.exit_code == 0, result.output
        assert CHECKER["audience_errors"](result.output) == []
        for name, child in getattr(command, "commands", {}).items():
            walk(child, [*path, name])

    walk(get_command(cli.app), [])
