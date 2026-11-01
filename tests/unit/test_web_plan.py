"""WEB-001: executable ownership and evidence rules for the web acceptance matrix.

The bundle's original manifest identifies supplied reference assets. Task files
and support records evolve during execution, so their original hashes are not a
current-content contract. Planned node IDs deliberately need not exist yet and
never establish a passing acceptance case.
"""

import copy
import hashlib
import json
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SUPPORT = ROOT / "docs/agents/plans/support/web-ui"
CASE_LAYERS = {"unit", "integration", "functional"}
DOC_LAYERS = {"documentation-validation", "integration", "human-functional-walkthrough"}
EXECUTION_FIELDS = {
    "layer",
    "node_ids",
    "command",
    "exit_status",
    "source_sha256",
    "artifact_sha256",
    "profile",
    "evidence_locator",
    "observed_assertion",
}


def load(name):
    return json.loads((SUPPORT / name).read_text())


def object_fields(value, expected):
    assert type(value) is dict
    assert set(value) == expected


def nonempty(value):
    assert type(value) is str
    assert value.strip()


def owned_file(name):
    assert type(name) is str
    path = Path(name)
    assert not path.is_absolute()
    assert ".." not in path.parts
    result = ROOT / path
    assert result.is_file()
    assert not result.is_symlink()
    assert result.resolve().is_relative_to(ROOT)
    return result


def validate_evidence(row, case):
    """A completed label needs recorded executions, hashes and observed results.

    This validates the evidence record; it does not run planned tests or imply
    that recorded application/platform fixture evidence is production acceptance.
    """
    object_fields(row, {"id", "owner", "status", "required_layers", "planned_tests", "executions"})
    assert row["id"] == case["id"]
    assert row["owner"] == case["owner"]
    assert row["status"] in {"pending", "in_progress", "blocked", "completed"}
    assert row["required_layers"] == case["minimum_layers"]
    assert type(row["planned_tests"]) is list
    assert row["planned_tests"]
    planned = set()
    for binding in row["planned_tests"]:
        object_fields(binding, {"layer", "node_id"})
        assert binding["layer"] in row["required_layers"]
        nonempty(binding["node_id"])
        planned.add(binding["layer"])
    assert planned == set(row["required_layers"])
    assert type(row["executions"]) is list
    passed = set()
    for execution in row["executions"]:
        object_fields(execution, EXECUTION_FIELDS)
        assert execution["layer"] in row["required_layers"]
        assert type(execution["node_ids"]) is list
        assert execution["node_ids"]
        for node_id in execution["node_ids"]:
            nonempty(node_id)
        for field in ("command", "profile", "evidence_locator", "observed_assertion"):
            nonempty(execution[field])
        for field in ("source_sha256", "artifact_sha256"):
            assert re.fullmatch(r"[0-9a-f]{64}", execution[field])
        assert type(execution["exit_status"]) is int
        if execution["exit_status"] == 0:
            passed.add(execution["layer"])
    if row["status"] == "completed":
        assert passed == set(row["required_layers"])


def test_task_index_schema_unique_ids_reciprocal_links_and_dependency_order():
    index = load("task-index.json")
    object_fields(
        index,
        {
            "schema_version",
            "plan",
            "baseline_commit",
            "branch",
            "task_status_authority",
            "tasks",
        },
    )
    assert type(index["schema_version"]) is int
    assert index["schema_version"] == 1
    assert re.fullmatch(r"[0-9a-f]{40}", index["baseline_commit"])
    assert index["branch"] == "feat/web-ui"
    assert "individual task Markdown files" in index["task_status_authority"]
    plan = owned_file(index["plan"]).read_text()
    ordered_tasks = plan.split("## Ordered task records\n", 1)[1].split("## Execution", 1)[0]
    assert type(index["tasks"]) is list
    assert index["tasks"]
    seen = set()
    paths = set()
    positions = []
    for task in index["tasks"]:
        object_fields(task, {"id", "path", "title", "phase", "depends_on"})
        assert re.fullmatch(r"WEB-[0-9]{3}", task["id"])
        assert task["id"] not in seen
        assert task["path"] not in paths
        assert re.fullmatch(r"P[0-9]+", task["phase"])
        nonempty(task["title"])
        assert type(task["depends_on"]) is list
        assert len(task["depends_on"]) == len(set(task["depends_on"]))
        # Requiring earlier nodes proves both closure and absence of cycles.
        assert set(task["depends_on"]) <= seen
        path = owned_file(task["path"])
        text = path.read_text()
        assert text.startswith(f"# {task['id']}: {task['title']}\n")
        assert "../2026-10-20-plan-web-ui.md" in text
        dependencies = re.search(r"^\| Depends on \| (.*?) \|$", text, re.MULTILINE)
        assert dependencies is not None
        assert re.findall(r"WEB-[0-9]{3}", dependencies[1]) == task["depends_on"]
        target = f"tasks/{path.name}"
        assert ordered_tasks.count(f"]({target})") == 1
        positions.append(ordered_tasks.index(f"]({target})"))
        seen.add(task["id"])
        paths.add(task["path"])
    assert positions == sorted(positions)
    assert {f"WEB-{number:03}" for number in range(1, 27)} <= seen


def test_all_95_cases_have_strict_schema_owners_and_exact_matrix_rows():
    index = load("acceptance-cases.json")
    object_fields(index, {"schema_version", "purpose", "cases"})
    assert type(index["schema_version"]) is int
    assert index["schema_version"] == 1
    nonempty(index["purpose"])
    assert type(index["cases"]) is list
    assert len(index["cases"]) == 95
    owners = {task["id"] for task in load("task-index.json")["tasks"]}
    cases = []
    for case in index["cases"]:
        object_fields(
            case,
            {"id", "owner", "requirement", "required_assertions", "minimum_layers", "test_binding"},
        )
        assert re.fullmatch(r"[A-Z]+-[0-9]{2}", case["id"])
        assert case["owner"] in owners
        for field in ("requirement", "required_assertions", "test_binding"):
            nonempty(case[field])
        assert type(case["minimum_layers"]) is list
        assert len(case["minimum_layers"]) == len(set(case["minimum_layers"]))
        assert set(case["minimum_layers"]) == (
            DOC_LAYERS if case["id"].startswith("DOC-") else CASE_LAYERS
        )
        cases.append((case["id"], case["owner"], case["requirement"], case["required_assertions"]))
    assert len({case[0] for case in cases}) == len(cases)
    matrix = (SUPPORT / "acceptance-matrix.md").read_text()
    rows = re.findall(
        r"^\| `([A-Z]+-[0-9]{2})` / \[(WEB-[0-9]{3})\]\([^)]+\) \| (.*?) \| (.*?) \|$",
        matrix,
        re.MULTILINE,
    )
    assert rows == cases


def test_supplied_design_assets_retain_original_manifest_hashes():
    manifest = load("bundle-manifest.json")
    references = [
        row
        for row in manifest["files"]
        if "/reference/" in row["path"] and Path(row["path"]).suffix in {".html", ".png"}
    ]
    assert len(references) == 5
    for reference in references:
        data = owned_file(reference["path"]).read_bytes()
        assert len(data) == reference["bytes"]
        assert hashlib.sha256(data).hexdigest() == reference["sha256"]
        if "original_sha256" in reference:
            original = subprocess.run(
                ["git", "show", f"c692d7ae4b866fefd8a743a21afdb729da0f39c4:{reference['path']}"],
                cwd=ROOT,
                check=True,
                capture_output=True,
            ).stdout
            assert len(original) == reference["original_bytes"]
            assert hashlib.sha256(original).hexdigest() == reference["original_sha256"]


def test_acceptance_evidence_has_every_owned_case_and_planned_layer():
    index = load("acceptance-evidence.json")
    object_fields(index, {"schema_version", "purpose", "cases"})
    assert type(index["schema_version"]) is int
    assert index["schema_version"] == 1
    nonempty(index["purpose"])
    assert type(index["cases"]) is list
    cases = load("acceptance-cases.json")["cases"]
    assert [row["id"] for row in index["cases"]] == [case["id"] for case in cases]
    for row, case in zip(index["cases"], cases, strict=True):
        validate_evidence(row, case)


@pytest.mark.parametrize(
    "fault", ["planned_only", "one_layer", "failed", "no_artifact", "no_profile"]
)
def test_completion_cannot_be_established_by_plans_or_incomplete_executions(fault):
    case = load("acceptance-cases.json")["cases"][0]
    row = copy.deepcopy(load("acceptance-evidence.json")["cases"][0])
    row["status"] = "completed"
    row["executions"] = [
        {
            "layer": layer,
            "node_ids": [f"tests/fixture.py::test_{layer}"],
            "command": "fixture validation command",
            "exit_status": 0,
            "source_sha256": "1" * 64,
            "artifact_sha256": "2" * 64,
            "profile": "synthetic evidence-validator test only",
            "evidence_locator": "fixture://evidence-validator",
            "observed_assertion": "synthetic record, not executed application acceptance",
        }
        for layer in case["minimum_layers"]
    ]
    if fault == "planned_only":
        row["executions"] = []
    elif fault == "one_layer":
        row["executions"] = row["executions"][:1]
    elif fault == "failed":
        row["executions"][0]["exit_status"] = 1
    elif fault == "no_artifact":
        row["executions"][0]["artifact_sha256"] = ""
    else:
        row["executions"][0]["profile"] = ""
    with pytest.raises(AssertionError):
        validate_evidence(row, case)
