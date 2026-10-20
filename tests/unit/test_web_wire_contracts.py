"""WEB-003 independent originals and literal wire fixtures precede generated checks."""

import copy
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from hfcache.catalog_models import ModelVariant
from hfcache.catalog_query_models import CatalogEntry, CatalogSearchPayload
from hfcache.client_models import Capabilities, ClientRead
from hfcache.errors import HfcacheError
from hfcache.models import Reference

ROOT = Path(__file__).resolve().parents[2]
GOLDENS = json.loads((ROOT / "tests/fixtures/web_wire/goldens.json").read_text())
ORIGINALS = {
    "ClientRead": ClientRead,
    "Capabilities": Capabilities,
    "CatalogSearchPayload": CatalogSearchPayload,
    "CatalogEntry": CatalogEntry,
    "ModelVariant": ModelVariant,
    "Reference": Reference,
}


@pytest.mark.parametrize("fixture", GOLDENS, ids=lambda item: item["case_id"])
def test_hand_authored_wire_literals_validate_with_original_authorities(fixture):
    model = ORIGINALS[fixture["definition"]].model_validate(fixture["value"])
    assert model.model_dump(mode="json") == fixture["value"]


@pytest.mark.parametrize("version", [None, False, True, "1", 1.0, 0, 2])
def test_original_wrapper_oracle_rejects_unknown_or_coerced_schema(version):
    value = copy.deepcopy(GOLDENS[0]["value"])
    if version is None:
        value.pop("schema_version")
    else:
        value["schema_version"] = version
    with pytest.raises(ValidationError):
        ClientRead.model_validate(value)


@pytest.mark.parametrize(
    "fault",
    [
        "microsecond-reversal",
        "warnings",
        "failed-empty",
        "success-errors",
        "extra",
        "envelope-version",
    ],
)
def test_original_wrapper_semantics_are_independent_of_exported_structures(fault):
    value = copy.deepcopy(GOLDENS[0]["value"])
    envelope = value["envelope"]
    if fault == "microsecond-reversal":
        envelope["completed_at"] = "2026-10-20T12:00:00.000000Z"
    elif fault == "warnings":
        envelope["outcome"] = "success_with_warnings"
    elif fault == "failed-empty":
        envelope |= {"outcome": "failed", "exit_code": 20}
    elif fault == "success-errors":
        envelope["errors"] = [
            {
                "code": "HFMNT002",
                "message": "independent failure",
                "repository": None,
                "context": {},
            }
        ]
    elif fault == "extra":
        value["debug_authority"] = True
    else:
        envelope["schema_version"] = 2
    with pytest.raises((ValidationError, HfcacheError)):
        ClientRead.model_validate(value)


@pytest.mark.parametrize("field", ["commit_sha", "publication_id", "repository_id"])
@pytest.mark.parametrize("suffix", ["\n", "\r\n", "\x00"])
def test_original_identity_oracle_requires_full_match(field, suffix):
    value = copy.deepcopy(GOLDENS[5]["value"])
    value[field] += suffix
    with pytest.raises((ValidationError, HfcacheError)):
        Reference.model_validate(value)


def test_false_zero_and_null_remain_distinct_in_original_models():
    capabilities = Capabilities.model_validate(GOLDENS[1]["value"])
    entry = CatalogEntry.model_validate(GOLDENS[3]["value"])
    variant = ModelVariant.model_validate(GOLDENS[4]["value"])
    assert capabilities.maintenance_enabled is False
    assert entry.configured is True
    assert entry.enabled is False
    assert entry.representative_variant is None
    assert entry.matching_variant_count == 0
    assert variant.total_bytes == 0
    assert variant.encoding is None
    for model, fixture, field, invalid in (
        (Capabilities, GOLDENS[1], "maintenance_enabled", 0),
        (CatalogEntry, GOLDENS[3], "configured", None),
        (ModelVariant, GOLDENS[4], "total_bytes", False),
    ):
        value = copy.deepcopy(fixture["value"])
        value[field] = invalid
        with pytest.raises(ValidationError):
            model.model_validate(value)
