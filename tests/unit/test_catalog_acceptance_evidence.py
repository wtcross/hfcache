"""V55: acceptance references resolve and serial package evidence remains auditable."""

import ast
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLAN_ROOT = ROOT / "docs/agents/plans"
SUPPORT = PLAN_ROOT / "support/tags-and-discovery"


def test_acceptance_matrix_has_live_concrete_evidence_for_every_case():
    record = json.loads((SUPPORT / "acceptance-evidence.json").read_text())
    assert record["schema_version"] == 1
    planned = re.findall(
        r"^\| (V[0-9]{2}) \|", (SUPPORT / "validation-matrix.md").read_text(), re.MULTILINE
    )
    assert [row["case"] for row in record["cases"]] == planned == [f"V{i:02}" for i in range(1, 56)]
    assert record["required_final_gate"] == "scripts/check.sh --with-build"
    for row in record["cases"]:
        assert row["evidence"], row["case"]
        for reference in row["evidence"]:
            filename, name = reference.split("::", 1)
            path = ROOT / filename
            assert path.is_file(), reference
            text = path.read_text()
            if path.suffix == ".py":
                functions = {
                    node.name for node in ast.parse(text).body if isinstance(node, ast.FunctionDef)
                }
                assert name in functions, reference
            else:
                assert path.suffix == ".ts"
                assert any("test(" + quote + name + quote in text for quote in ("'", '"', "`")), (
                    reference
                )


def test_predecessor_commits_and_plan_selector_preserve_the_execution_record():
    completed = subprocess.run(
        ["git", "log", "--format=%s", "--name-only", "75d93a5..HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    packages = {}
    current = None
    for line in completed.stdout.splitlines():
        match = re.match(r"^CAT-([0-9]{3}): ", line)
        if match:
            current = int(match[1])
            assert current not in packages
            packages[current] = set()
        elif line and current is not None:
            packages[current].add(line)
    for number in range(1, 16):
        tasks = list((PLAN_ROOT / "tasks").glob(f"cat-{number:03}-*.md"))
        assert len(tasks) == 1
        text = tasks[0].read_text()
        assert re.search(r"\| Status \| complete(?:d)? \|", text)
        assert "scripts/check.sh" in text
        assert number in packages
        files = packages[number]
        assert str(tasks[0].relative_to(ROOT)) in files
        assert "docs/agents/progress.md" in files
        assert "docs/agents/plans/current.md" in files
    final_task = (
        PLAN_ROOT / "tasks/cat-016-compatibility-docs-and-final-acceptance.md"
    ).read_text()
    plan = (PLAN_ROOT / "2026-10-19-plan-tags-and-discovery.md").read_text()
    selector = (PLAN_ROOT / "current.md").read_text()
    if "| Status | complete |" in final_task:
        assert "| Status | complete |" in plan
        # INV-011: completion clears the selector in that package, without
        # preventing a later authorized plan from selecting new work.
        final_commits = subprocess.run(
            ["git", "log", "--format=%H", "--grep=^CAT-016: "],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
        assert len(final_commits) == 1
        completed_selector = subprocess.run(
            ["git", "show", f"{final_commits[0]}:docs/agents/plans/current.md"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        assert "| State | inactive |" in completed_selector
        assert "| Next task | None |" in completed_selector
        assert "| Last completed plan | [Tags and discovery]" in completed_selector
    else:
        assert "| Status | in_progress |" in final_task
        assert "| Status | active |" in plan
        assert "| State | active |" in selector
        assert "[CAT-016:" in selector
