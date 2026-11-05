"""Retained browser requirements cover assertions without execution ledgers."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests/fixtures/web-acceptance"


def test_browser_requirements_have_unique_ids_assertions_and_coverage_groups():
    requirements = json.loads((FIXTURE / "requirements.json").read_text())
    groups = json.loads((FIXTURE / "coverage-groups.json").read_text())
    assert requirements["schema_version"] == groups["schema_version"] == 1
    seen = set()
    for group in groups["tasks"]:
        assert set(group) == {"id", "depends_on"}
        assert group["id"] not in seen
        assert set(group["depends_on"]) <= seen
        seen.add(group["id"])
    cases = requirements["cases"]
    assert len(cases) == 95
    assert len({case["id"] for case in cases}) == len(cases)
    for case in cases:
        assert case["owner"] in seen
        for field in ("requirement", "required_assertions"):
            assert case[field].strip()
        layers = case["minimum_layers"]
        assert len(layers) == len(set(layers))
        assert set(layers) == (
            {"documentation-validation", "integration", "human-functional-walkthrough"}
            if case["id"].startswith("DOC-")
            else {"unit", "integration", "functional"}
        )
