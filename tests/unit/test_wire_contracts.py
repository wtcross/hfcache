"""WEB-003 precise authorities, serializer compatibility and fail-closed export."""

import ast
import copy
import json
import subprocess
import sys
from datetime import datetime  # noqa: TC003 - Pydantic resolves the test field at runtime
from pathlib import Path

import pytest
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from hfcache import wire_schema
from hfcache.api.command_models import CommandModel
from hfcache.card_models import RepositoryCardRead
from hfcache.config import ApplicationConfig
from hfcache.services.candidates import validate_candidate
from hfcache.services.queries import LocalQueries
from hfcache.wire_registry import (
    AUTHORITIES,
    RESULT_ROUTES,
    ROUTES,
    request_authorities,
    validate_payload,
)
from hfcache.wire_schema import Exporter, build_contracts, check_json_schema, render_contracts
from tests.fixtures import examples


@pytest.fixture(scope="module")
def contracts():
    return build_contracts()


def _nodes(value):
    if isinstance(value, list):
        for item in value:
            yield from _nodes(item)
    elif isinstance(value, dict):
        if "kind" in value:
            yield value
        for item in value.values():
            yield from _nodes(item)


def test_export_is_deterministic_closed_and_every_reference_resolves(contracts):
    assert render_contracts() == render_contracts()
    assert contracts["schema_version"] == 1
    assert len(contracts["source_digest"]) == 64
    assert "OperationReceipt" not in contracts["definitions"]
    for node in _nodes(contracts["definitions"]):
        assert "semantic_ids" in node
        assert set(node["semantic_ids"]) <= contracts["semantics"].keys()
        if node["kind"] == "ref":
            assert node["name"] in contracts["definitions"]
        if node["kind"] == "object":
            assert node["extra"] == "forbid"
    for route in contracts["routes"]:
        if route["request_body"] is not None:
            assert route["request_body"] in contracts["definitions"]
        for binding in route["binding_ids"]:
            assert contracts["semantics"][binding]["phase"] == "context"


@pytest.mark.parametrize("module", ["hfcache.api.host_actions", "hfcache.api.host_routes"])
def test_host_api_authorization_and_route_source_drift_refuses_export(monkeypatch, module):
    # DTO-only pins would miss a changed original-key gate, limit or renderer.
    assert module in wire_schema.AUDITED_SOURCES
    monkeypatch.setitem(wire_schema.AUDITED_SOURCES, module, "0" * 64)
    with pytest.raises(ValueError, match="Changed audited source module " + module):
        build_contracts()


def test_serialized_defaults_are_required_without_erasing_request_omission(contracts):
    envelope = contracts["definitions"]["Envelope"]
    assert all(field["required"] for field in envelope["fields"])
    assert {field["name"] for field in envelope["fields"]} >= {
        "schema_version",
        "errors",
        "warnings",
    }
    sync = contracts["definitions"]["RequestSyncSubmission"]
    assert (
        next(field for field in sync["fields"] if field["name"] == "selectors")["required"] is False
    )


def test_card_read_is_an_exact_closed_projection_not_a_durable_record_or_path_selector(contracts):
    route = next(item for item in contracts["routes"] if item["id"] == "repository_card")
    assert route["path"] == (
        "/api/v1/repositories/{repository_type}/{namespace}/{name}"
        "/publications/{commit_sha}/{publication_id}/card"
    )
    assert route["method"] == "GET"
    assert route["commands"] == ("card read",)
    assert route["binding_ids"] == ("publication.card",)
    assert route["request_body"] is None
    assert AUTHORITIES["RepositoryCardRead"] is RepositoryCardRead
    assert "RepositoryCard" not in contracts["definitions"]
    definition = contracts["definitions"]["RepositoryCardRead"]
    assert definition["kind"] == "object"
    assert definition["extra"] == "forbid"
    assert all(field["required"] for field in definition["fields"])
    assert not any(node["kind"] == "json" for node in _nodes(definition))
    assert contracts["semantics"]["publication.card"]["phase"] == "context"


def test_python_array_and_integer_bounds_survive_the_export(contracts):
    entry = next(
        field["node"]
        for field in contracts["definitions"]["CatalogSearchPayload"]["fields"]
        if field["name"] == "entries"
    )
    assert entry["max_items"] == 10000
    assert "maxLength" not in entry
    count = next(
        field["node"]
        for field in contracts["definitions"]["CatalogCoverage"]["fields"]
        if field["name"] == "repositories"
    )
    assert count["maximum"] == "9223372036854775807"
    assert count["minimum"] == "0"


def test_host_status_is_fixed_read_with_closed_required_unit_projection(contracts):
    route = next(route for route in contracts["routes"] if route["id"] == "host_status")
    assert (route["method"], route["path"], route["commands"], route["success"]) == (
        "GET",
        "/api/v1/host/status",
        ("host status",),
        "HostStatus",
    )
    assert route["binding_ids"] == ("host.status",)
    node = next(
        field["node"]
        for field in contracts["definitions"]["HostFacts"]["fields"]
        if field["name"] == "units"
    )
    assert node["kind"] == "object"
    assert node["extra"] == "forbid"
    assert {field["name"] for field in node["fields"]} == {
        "hfcache-sync.service",
        "hfcache-sync.timer",
        "hfcache-verify.service",
        "hfcache-verify.timer",
    }
    assert all(field["required"] for field in node["fields"])


def test_host_finite_mapping_lowering_refuses_changed_unit_allowlist():
    node = {
        "type": "dict",
        "keys_schema": {"type": "literal", "expected": ["other.service"]},
        "values_schema": {"type": "str"},
    }
    with pytest.raises(ValueError, match="Host unit keys changed"):
        Exporter().node(node, path="HostFacts.units")


def test_every_actual_json_route_and_original_job_result_is_registered():
    actual = set()
    for module in (
        "app",
        "catalog",
        "commands",
        "maintenance",
        "catalog_refresh",
        "host_status",
        "host_actions",
        "configuration",
        "intent_routes",
    ):
        tree = ast.parse(Path(f"src/hfcache/api/{module}.py").read_text())
        prefix = "/api/v1/catalog" if module == "catalog" else "/api/v1"

        def spelling(node, prefix=prefix):
            if isinstance(node, ast.Constant):
                return node.value
            if isinstance(node, ast.BinOp):
                return spelling(node.left) + spelling(node.right)
            assert isinstance(node, ast.Name)
            return {
                "PREFIX": prefix,
                "ROUTE": prefix + "/catalog/refreshes",
                "_APPLICATIONS": "/api/v1/config/applications",
                "_OBSERVER": "/api/v1/host/sync-observer",
                "_JOURNAL": "/api/v1/host/journal",
                "VALIDATIONS": "/api/v1/host/sync-schedule/validations",
                "SCHEDULE_CHANGES": "/api/v1/host/sync-schedule/changes",
                "OBSERVER_STOPS": "/api/v1/host/sync-observer/stops",
            }[node.id]

        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "app"
                and node.func.attr in {"get", "post"}
            ):
                actual.add((node.func.attr.upper(), spelling(node.args[0])))
    # These authenticated documents deliberately have no domain payload decoder.
    actual -= {("GET", "/api/v1/docs"), ("GET", "/api/v1/openapi.json")}
    # UI dispatch is deliberately add_api_route with a closed member switch;
    # bootstrap alone is a plain typed JSON authority, never a fake Envelope.
    source = Path("src/hfcache/api/app.py").read_text()
    assert 'member == "bootstrap.json"' in source
    assert '"/ui/{member:path}"' in source
    actual.add(("GET", "/ui/bootstrap.json"))
    assert {(route.method, route.path) for route in ROUTES} == actual
    assert len({(route.method, route.path, route.mode) for route in ROUTES}) == len(ROUTES)
    jobs = {route.path for route in ROUTES if route.response_kind == "acceptance"}
    assert {route.origin_path for route in RESULT_ROUTES} == jobs
    for result in RESULT_ROUTES:
        assert result.success in AUTHORITIES
        assert set(result.failure) <= AUTHORITIES.keys()


@pytest.mark.parametrize("mode", ["InstalledPlan", "InstalledValidation"])
def test_installed_request_modes_refuse_candidate_instead_of_switching_authority(mode):
    model = request_authorities()[mode]
    with pytest.raises(ValidationError):
        model.model_validate({"candidate": "schema_version=1"})


@pytest.mark.parametrize("mode", ["LiteralCandidatePlan", "LiteralCandidateValidation"])
@pytest.mark.parametrize("body", [{}, {"candidate": None}, {"candidate": ""}])
def test_literal_candidate_modes_require_nonempty_nonnull_exact_content(mode, body):
    with pytest.raises(ValidationError):
        request_authorities()[mode].model_validate(body)


def test_literal_request_bytes_and_old_canonical_digest_inputs_are_preserved():
    modes = request_authorities()
    content = "schema_version=1\n# preserve trailing LF\n"
    planned = modes["LiteralCandidatePlan"].model_validate({"candidate": content})
    assert isinstance(planned, CommandModel)
    assert planned.canonical_body() == {"selectors": [], "candidate": content}
    installed = modes["InstalledPlan"].model_validate({})
    full = modes["FullVerification"].model_validate({"mode": "full"})
    assert isinstance(installed, CommandModel)
    assert isinstance(full, CommandModel)
    assert installed.canonical_body() == {"selectors": []}
    assert full.canonical_body() == {
        "mode": "full",
        "revision": None,
        "run_id": None,
    }


@pytest.mark.parametrize(
    ("name", "body"),
    [
        (
            "ManifestPayload",
            lambda: {
                "manifest": examples.manifest().model_dump(mode="json"),
                "tree_base": "archive-root/",
            },
        ),
        (
            "ReferencePayload",
            lambda: {
                "reference": examples.reference().model_dump(mode="json"),
                "locator_base": "published/",
            },
        ),
        ("ReportPayload", lambda: {"report": examples.run_report().model_dump(mode="json")}),
        (
            "ReportPayload",
            lambda: {"report": examples.verification_report().model_dump(mode="json")},
        ),
        (
            "PrunePayload",
            lambda: {
                "plans": [examples.prune_plan().model_dump(mode="json")],
                "applied": [examples.pruned_record().model_dump(mode="json")],
            },
        ),
        (
            "PurgePayload",
            lambda: {"plans": [examples.purge_plan().model_dump(mode="json")], "applied": []},
        ),
    ],
)
def test_independent_existing_domain_serializers_round_trip_without_wire_changes(name, body):
    actual = json.loads(json.dumps(body()))
    decoded = validate_payload(name, actual)
    assert isinstance(decoded, BaseModel)
    assert decoded.model_dump(mode="json") == actual
    with pytest.raises(ValidationError):
        validate_payload(name, actual | {"unexpected": True})


@pytest.mark.parametrize(
    ("name", "report"),
    [
        ("RunResultPayload", examples.run_report),
        ("VerificationResultPayload", examples.verification_report),
    ],
)
def test_flat_report_extension_reuses_final_models_and_exact_locator(name, report):
    actual = report().model_dump(mode="json") | {"report": "runs/original.json"}
    assert validate_payload(name, actual) == actual
    for changed in (
        {key: value for key, value in actual.items() if key != "report"},
        actual | {"report": "../escape"},
        actual | {"extra": 1},
    ):
        with pytest.raises(
            ValueError, match=r"Missing report locator|validation error|archive-relative"
        ):
            validate_payload(name, changed)


def test_real_local_query_and_candidate_serializers_match_the_projections(tmp_path):
    config = ApplicationConfig.model_validate(
        {
            "schema_version": 1,
            "storage": {"archive_root": str(tmp_path), "archive_id": examples.ARCHIVE_ID},
            "repositories": [{"type": "model", "id": "owner/model"}],
        }
    )
    queries = LocalQueries(config)
    results = {
        "VersionPayload": queries.version().data,
        "InspectionPayload": queries.inspect_archive().as_payload(),
        "StatusPayload": queries.archive_status().data,
        "RepositoriesPayload": queries.list_repositories().data,
        "CandidateInvalidPayload": validate_candidate("not = valid = toml", config).data,
    }
    for name, actual in results.items():
        decoded = validate_payload(name, actual)
        assert isinstance(decoded, BaseModel)
        assert decoded.model_dump(mode="json") == actual


def test_schema_keyword_and_core_construct_changes_fail_closed():
    with pytest.raises(ValueError, match="Unaudited JSON Schema"):
        check_json_schema({"type": "object", "unevaluatedProperties": False})
    with pytest.raises(ValueError, match="Unaudited core schema"):
        Exporter().node({"type": "set", "items_schema": {"type": "str"}})
    with pytest.raises(ValueError, match="Unaudited core schema keys"):
        Exporter().node({"type": "str", "new_validation_constraint": 1})
    with pytest.raises(ValueError, match="Unaudited JSON Schema format"):
        check_json_schema({"type": "string", "format": "email"})


def test_new_custom_field_or_model_schema_hook_is_not_silently_ignored():
    class Unreviewed(BaseModel):
        model_config = ConfigDict(strict=True, extra="forbid")
        value: str

        @field_validator("value")
        @classmethod
        def new_rule(cls, value):
            return value

    with pytest.raises(ValueError, match="Unaudited or changed wire validator"):
        Exporter().authority("Unreviewed", Unreviewed)

    class NewKeyword(BaseModel):
        value: str = Field(json_schema_extra={"contentEncoding": "base64"})

    with pytest.raises(ValueError, match="Unaudited JSON Schema keywords"):
        Exporter().authority("NewKeyword", NewKeyword)

    class KnownKeywordOverride(BaseModel):
        model_config = ConfigDict(strict=True, extra="forbid")
        value: int = Field(json_schema_extra={"minimum": 100})

    with pytest.raises(ValueError, match="Unaudited JSON Schema metadata hook"):
        Exporter().authority("KnownKeywordOverride", KnownKeywordOverride)

    class PlainDatetime(BaseModel):
        model_config = ConfigDict(strict=True, extra="forbid")
        value: datetime

    with pytest.raises(ValueError, match="audited timestamp serializer"):
        Exporter().authority("PlainDatetime", PlainDatetime)


def test_changed_validator_source_pin_refuses_export(monkeypatch):
    changed = copy.copy(wire_schema.AUDITED_HOOKS)
    changed["hfcache.models.parse_timestamp"] = "0" * 64
    monkeypatch.setattr(wire_schema, "AUDITED_HOOKS", changed)
    with pytest.raises(ValueError, match="changed wire validator"):
        wire_schema.build_contracts()


def test_changed_helper_or_constant_module_requires_explicit_semantic_review(monkeypatch):
    changed = copy.copy(wire_schema.AUDITED_SOURCES)
    changed["hfcache.paths"] = "0" * 64
    monkeypatch.setattr(wire_schema, "AUDITED_SOURCES", changed)
    with pytest.raises(ValueError, match=r"Changed audited source module hfcache.paths"):
        wire_schema.build_contracts()


def test_nonstrict_or_open_object_models_cannot_be_labeled_closed():
    class OpenModel(BaseModel):
        value: str

    with pytest.raises(ValueError, match="strict validation and forbidden extra"):
        Exporter().authority("OpenModel", OpenModel)


def test_json_contexts_remain_object_only_and_repeated_queries_have_count_bounds(contracts):
    for node in _nodes(contracts["definitions"]):
        if node["kind"] == "json_value":
            assert node["object_only"] is True
    status = next(route for route in contracts["routes"] if route["id"] == "status")
    selector = next(param for param in status["query_parameters"] if param["name"] == "selector")
    assert selector["repeated"] is True
    assert selector["node"]["kind"] == "array"
    assert selector["node"]["max_items"] == 100
    catalog = next(route for route in contracts["routes"] if route["id"] == "catalog_search")
    tag = next(param for param in catalog["query_parameters"] if param["name"] == "tag_all")
    assert tag["node"]["max_items"] == 64


def test_export_check_refuses_drift_and_never_repairs_it_implicitly(tmp_path):
    path = tmp_path / "contract.json"
    base = [sys.executable, "scripts/export-web-contracts.py", "--output", str(path)]
    assert subprocess.run([*base, "--check"], capture_output=True, check=False).returncode == 1
    assert not path.exists()
    assert subprocess.run([*base, "--write"], capture_output=True, check=False).returncode == 0
    sibling = path.with_name("unicode-data.json")
    original_unicode = sibling.read_bytes()
    sibling.write_bytes(original_unicode + b" ")
    assert subprocess.run([*base, "--check"], capture_output=True, check=False).returncode == 1
    assert sibling.read_bytes().endswith(b" ")
    sibling.write_bytes(original_unicode)
    assert subprocess.run([*base, "--check"], capture_output=True, check=False).returncode == 0
    path.write_text(path.read_text() + " ")
    assert subprocess.run([*base, "--check"], capture_output=True, check=False).returncode == 1
    assert path.read_text().endswith(" ")


def test_safe_help_and_pure_import_need_no_optional_server_or_mcp():
    help_result = subprocess.run(
        [sys.executable, "-S", "scripts/export-web-contracts.py", "--help"],
        capture_output=True,
        check=False,
    )
    assert help_result.returncode == 0
    probe = """
import importlib.abc, sys
class RejectOptional(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'fastapi','starlette','fastmcp','mcp'}:
            raise RuntimeError('optional transport imported: '+fullname)
sys.meta_path.insert(0, RejectOptional())
import hfcache.wire_models, hfcache.wire_registry, hfcache.wire_schema
from pathlib import Path
root=Path.cwd()
def no_frontend_or_authority_reads(event,args):
    if event == 'open' and isinstance(args[0], (str,bytes)):
        path=Path(args[0]).absolute()
        forbidden=(root/'web',root/'docs',Path('/srv/hfcache'),Path('/etc/hfcache'))
        if any(path.is_relative_to(base) for base in forbidden):
            raise RuntimeError('forbidden frontend/policy/archive read')
    if event in {'socket.connect','subprocess.Popen'}:
        raise RuntimeError('unexpected external effect')
sys.addaudithook(no_frontend_or_authority_reads)
digest=hfcache.wire_schema.installed_source_digest()
assert len(digest)==64 and all(c in '0123456789abcdef' for c in digest)
assert digest == hfcache.wire_schema.build_contracts()['source_digest']
assert 'hfcache.api.app' not in sys.modules
assert not any(name.startswith(('fastapi','starlette','fastmcp')) for name in sys.modules)
"""
    result = subprocess.run([sys.executable, "-c", probe], capture_output=True, check=False)
    assert result.returncode == 0, result.stderr.decode()


def test_installed_digest_refuses_invalid_internal_identity(monkeypatch):
    monkeypatch.setattr(wire_schema, "build_contracts", lambda: {"source_digest": "invalid"})
    with pytest.raises(ValueError, match="Invalid installed wire authority digest"):
        wire_schema.installed_source_digest()


def test_bootstrap_is_an_independent_closed_plain_response(contracts):
    route = next(row for row in contracts["routes"] if row["id"] == "ui_bootstrap")
    assert route["path"] == "/ui/bootstrap.json"
    assert route["response_kind"] == "ui_bootstrap"
    assert route["success"] == "UiBootstrap"
    assert route["commands"] == ()
    assert route["failure"] == ()
    assert route["path_parameters"] == route["query_parameters"] == []
    assert route["request_body"] is None
    for name in ("UiAssetManifest", "UiBootstrap"):
        assert all(field["required"] for field in contracts["definitions"][name]["fields"])


def test_candidate_and_report_failure_shapes_remain_distinct_from_success(contracts):
    candidate = next(
        route
        for route in contracts["routes"]
        if route["id"] == "config_validate" and route["mode"] == "literal_candidate"
    )
    assert candidate["success"] == "CandidateValidPayload"
    assert candidate["failure"] == ("CandidateInvalidPayload",)
    verification = next(
        route for route in contracts["operation_results"] if route["commands"] == ("verify --full",)
    )
    assert set(verification["failure"]) == {
        "VerificationReport",
        "VerificationResultPayload",
        "EmptyPayload",
    }
    assert verification["origin_path"] == "/api/v1/verifications"
