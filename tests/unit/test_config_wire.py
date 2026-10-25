"""Independent public config serializers and closed wire export (decision153)."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from hfcache.config_models import ConfigRead, ManagedAssessment, ManagedValidation
from hfcache.wire_registry import AUTHORITIES, RESULT_ROUTES, ROUTES, request_authorities
from hfcache.wire_schema import Exporter, build_contracts, check_json_schema
from tests.fixtures import examples

FIXTURES = json.loads(Path("tests/fixtures/web_wire/config.json").read_text())


@pytest.mark.parametrize(
    ("key", "factory", "model"),
    [
        ("read", examples.configuration_read, ConfigRead),
        ("validation", examples.managed_validation, ManagedValidation),
        ("assessment", examples.managed_assessment, ManagedAssessment),
    ],
)
def test_independent_config_serialized_fixtures_match_original_models(key, factory, model):
    assert factory().model_dump(mode="json") == FIXTURES[key]
    assert model.model_validate(FIXTURES[key]).model_dump(mode="json") == FIXTURES[key]
    for field in ("candidate", "config_sha256", "token", "archive_root"):
        with pytest.raises(ValidationError):
            model.model_validate({**FIXTURES[key], field: "not-public"})


def test_only_public_configuration_models_are_registered_and_no_private_candidate_is_exported():
    contracts = build_contracts()
    assert {"ConfigRead", "ManagedValidation", "ManagedAssessment"} <= AUTHORITIES.keys()
    assert not any("Prepared" in name for name in contracts["definitions"])
    read = next(row for row in ROUTES if row.id == "config_read")
    assert (read.path, read.commands, read.success) == (
        "/api/v1/config",
        ("config read",),
        "ConfigRead",
    )
    validation = next(
        row for row in ROUTES if row.id == "config_validate" and row.mode == "managed"
    )
    assert validation.success == "ManagedValidation"
    plan = next(row for row in RESULT_ROUTES if row.origin_path == "/api/v1/plans")
    assert plan.success == "PlanResultPayload"
    assert contracts["definitions"]["PlanResultPayload"]["kind"] == "union"


def test_managed_export_request_modes_are_closed_without_changing_literal_forms():
    modes = request_authorities()
    for name in ("ManagedValidationRequest", "ManagedPlanRequest"):
        assert modes[name].model_validate(FIXTURES["request"]).model_dump()["managed"]["edits"]
        with pytest.raises(ValidationError):
            modes[name].model_validate({**FIXTURES["request"], "candidate": "schema_version=1"})
    with pytest.raises(ValidationError):
        modes["ManagedPlanRequest"].model_validate(
            {**FIXTURES["request"], "selectors": ["model:organization/subset"]}
        )
    with pytest.raises(ValidationError):
        modes["LiteralCandidatePlan"].model_validate(
            {"candidate": "schema_version=1", **FIXTURES["request"]}
        )


def test_discriminated_union_lowering_refuses_any_new_or_callable_discriminator():
    for discriminator, choices in (
        ("other", {}),
        (lambda _value: "kind", {}),
        ("kind", {"arbitrary": {"type": "str"}}),
    ):
        with pytest.raises(ValueError, match="closed managed-edit"):
            Exporter().node(
                {"type": "tagged-union", "discriminator": discriminator, "choices": choices}
            )
    with pytest.raises(ValueError, match="fixed managed-edit"):
        check_json_schema({"discriminator": {"propertyName": "unknown", "mapping": {}}})
