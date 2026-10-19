"""REST acceptance requires all semantic rows and real, selected test evidence."""

import ast
import re
from functools import cache
from pathlib import Path

import pytest

from tests.rest_parity import PARITY, Evidence, ParityMode
from tests.rest_reference import CATALOG_API_REFERENCE, PARITY_REFERENCE, REFERENCE

ROOT = Path(__file__).resolve().parents[2]


@cache
def matrix_rows() -> tuple[tuple[str, ...], ...]:
    document = (ROOT / "docs/api.md").read_text()
    section = document.split("## Routes and effects\n", 1)[1].split("\n## ", 1)[0]
    lines = [line for line in section.splitlines() if line.startswith("| ")]
    assert lines[0].startswith("| Method/path | Mode | CLI mapping | Capability |")
    return tuple(
        tuple(part.strip().strip("`") for part in line.split("|")[1:-1]) for line in lines[2:]
    )


@cache
def evidence_function(reference: Evidence) -> ast.FunctionDef | ast.AsyncFunctionDef:
    assert re.fullmatch(r"test_[a-z0-9_]+", reference.module)
    assert reference.function.startswith("test_")
    path = ROOT / "tests/unit" / f"{reference.module}.py"
    functions = [
        node
        for node in ast.parse(path.read_text()).body
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        and node.name == reference.function
    ]
    assert len(functions) == 1, reference.citation
    return functions[0]


def parameter_values(
    function: ast.FunctionDef | ast.AsyncFunctionDef, parameter: str
) -> tuple[ast.expr, ...]:
    found: list[ast.expr] = []
    for decorator in function.decorator_list:
        if not isinstance(decorator, ast.Call) or not ast.unparse(decorator.func).endswith(
            ".parametrize"
        ):
            continue
        names = ast.literal_eval(decorator.args[0])
        if isinstance(names, str):
            names = [name.strip() for name in names.split(",")]
        if parameter not in names:
            continue
        index = names.index(parameter)
        cases = decorator.args[1]
        assert isinstance(cases, ast.List | ast.Tuple), "selected evidence must declare its cases"
        for case in cases.elts:
            if isinstance(case, ast.Call) and ast.unparse(case.func) == "pytest.param":
                found.append(case.args[index])
            elif len(names) == 1:
                found.append(case)
            else:
                assert isinstance(case, ast.List | ast.Tuple)
                found.append(case.elts[index])
    return tuple(found)


def test_manifest_has_exactly_all_34_unique_semantic_rows_in_contract_order():
    rows = matrix_rows()
    assert len(PARITY) == len(PARITY_REFERENCE) == 34
    assert len(REFERENCE) == len(rows) == 44
    assert len({mode.cli_mode for mode in PARITY}) == len(PARITY)
    assert list(PARITY_REFERENCE) == [mode.cli_mode for mode in PARITY]
    assert rows == REFERENCE
    assert len({row[:2] for row in rows}) == 44
    assert all(len(row) == 9 for row in rows)


@pytest.mark.parametrize("mode", PARITY, ids=lambda mode: mode.cli_mode)
def test_each_semantic_mode_matches_documented_authority_and_concrete_evidence(mode: ParityMode):
    assert mode.cli_tests
    assert mode.api_tests
    expansions = {
        "read_evidence": (
            "GET /runs",
            "GET /runs/{run_id}",
            "GET /repositories/{repository_type}/{namespace}/{name}/references/{revision}",
            (
                "GET /repositories/{repository_type}/{namespace}/{name}"
                "/manifests/{commit_sha}/{publication_id}"
            ),
        ),
        "observe_operation": (
            "GET /operations",
            "GET /operations/lookup",
            "GET /operations/{operation_id}",
            "GET /operations/{operation_id}/result",
            "GET /operations/{operation_id}/events",
        ),
    }
    assert tuple(key[0] for key in PARITY_REFERENCE[mode.cli_mode]) == expansions.get(
        mode.service, (mode.route,)
    )
    for key in PARITY_REFERENCE[mode.cli_mode]:
        row = next(row for row in matrix_rows() if row[:2] == key)
        assert row[3].split()[0] == mode.role
        assert row[4] == ("keyed job" if mode.execution == "J" else "synchronous")
        assert row[5] == mode.lock
        assert row[6] == ("yes" if mode.hub in {"yes", "explicit"} else "no")
        assert row[7] == mode.effects.removeprefix("receipt; ").replace("receipt only", "none")
        assert row[8] == ("receipt, events and result" if mode.execution == "J" else "none")


@pytest.mark.parametrize("mode", PARITY, ids=lambda mode: mode.cli_mode)
def test_every_named_function_and_selected_parameter_case_exists_without_imports(mode: ParityMode):
    for reference in (*mode.cli_tests, *mode.api_tests):
        function = evidence_function(reference)
        assert (reference.parameter is None) == (reference.case is None), reference.citation
        if reference.parameter is not None and reference.case is not None:
            expected = ast.dump(ast.parse(reference.case, mode="eval").body)
            actual = [ast.dump(value) for value in parameter_values(function, reference.parameter)]
            assert expected in actual, (reference.citation, reference.parameter, reference.case)


def test_heavy_verification_modes_trace_real_private_worker_and_exact_cli_mode():
    for label, worker_case in (
        ("verify --new [--run-id]", "'new'"),
        ("verify --full", "'full'"),
        ("verify --revision", "'revision'"),
    ):
        mode = next(mode for mode in PARITY if mode.cli_mode == label)
        assert PARITY_REFERENCE[label] == (
            ("POST /verifications", f"mode={ast.literal_eval(worker_case)}"),
        )
        assert mode.role == "W"
        assert mode.lock == "worker archive"
        assert any(
            reference.module == "test_verification_executor" and reference.case == worker_case
            for reference in mode.api_tests
        )
        assert any(reference.parameter == "arguments" for reference in mode.cli_tests)
    named = next(mode for mode in PARITY if mode.cli_mode == "verify --new [--run-id]")
    assert any("named_run_cli" in reference.function for reference in named.cli_tests)


@pytest.mark.parametrize("flag", ["--dry-run", "--apply"])
def test_purge_rows_cover_both_scope_branches_with_their_distinct_modes(flag):
    mode = next(mode for mode in PARITY if mode.cli_mode.startswith(f"purge {flag} "))
    assert any(
        reference.parameter == "arguments" and "--all-unmanaged" in (reference.case or "")
        for reference in mode.cli_tests
    )
    assert any(
        reference.function == "test_explicit_unmanaged_purge_cli_scope_keeps_configured_repository"
        and reference.case == repr(flag)
        for reference in mode.cli_tests
    )


@pytest.mark.parametrize("route", tuple(CATALOG_API_REFERENCE))
def test_catalog_routes_have_independent_http_evidence_before_cli_acceptance(route):
    row = next(row for row in matrix_rows() if row[0] == route)
    expected = (
        (
            "default",
            "SDK / HTTP",
            "W",
            "keyed job",
            "archive",
            "no",
            "supplemental metadata",
            "receipt, events and result",
        )
        if route.startswith("POST ")
        else ("default", "SDK / HTTP", "R", "synchronous", "none", "no", "none", "none")
    )
    labels = {
        "GET /catalog/search": "search",
        "GET /catalog/facets": "tags",
        "GET /catalog/repositories/{repository_type}/{namespace}/{name}": "catalog show TYPE:ID",
        "GET /catalog/repositories/{repository_type}/{namespace}/{name}/variants": (
            "catalog variants TYPE:ID"
        ),
        "POST /catalog/refreshes": "catalog refresh [selectors]",
    }
    assert row[1:] == (*expected[:1], labels[route], *expected[2:])
    evidence_function(Evidence(*CATALOG_API_REFERENCE[route]))
