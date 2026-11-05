"""Catalog coverage references resolve to maintained product tests."""

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_catalog_coverage_references_live_product_tests():
    record = json.loads((ROOT / "tests/fixtures/catalog/coverage.json").read_text())
    assert record["schema_version"] == 1
    rows = record["cases"]
    # Two removed-interface cases and the retired process-ledger case are absent;
    # Other catalog requirements retain live test bindings.
    assert [row["case"] for row in rows] == [
        f"V{i:02}" for i in range(1, 56) if i not in {5, 6, 55}
    ]
    for row in rows:
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
