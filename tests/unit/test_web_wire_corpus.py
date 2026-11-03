"""Independent original-model corpus coverage and disposable-factory boundaries."""

import json
import socket
from functools import partial
from importlib import import_module
from tempfile import TemporaryDirectory

import pytest
from pydantic import BaseModel

from hfcache import archive
from hfcache.wire_registry import AUTHORITIES, ROUTES, request_authorities, validate_payload
from hfcache.wire_schema import build_contracts
from tests import web_wire_corpus


@pytest.fixture(scope="module")
def corpus():
    return web_wire_corpus.serialized_corpus()


@pytest.fixture(scope="module")
def original_models():
    models = {}
    for module in (
        "hfcache.card_models",
        "hfcache.catalog_models",
        "hfcache.catalog_query_models",
        "hfcache.catalog_refresh_models",
        "hfcache.client_models",
        "hfcache.host_models",
        "hfcache.host_actions_models",
        "hfcache.config_models",
        "hfcache.config",
        "hfcache.models",
        "hfcache.manifests",
        "hfcache.reporting",
        "hfcache.wire_models",
        "hfcache.ui_models",
    ):
        for value in vars(import_module(module)).values():
            if isinstance(value, type) and issubclass(value, BaseModel):
                models[value.__name__] = value
                models["Request" + value.__name__] = value
    for name, model in request_authorities().items():
        models["Request" + name] = model
        models["Request" + model.__name__] = model
    return models


def test_original_serializer_corpus_covers_every_public_named_definition(corpus):
    assert len(corpus) == 374
    assert len({entry["case_id"] for entry in corpus}) == len(corpus)
    names = {entry["definition"] for entry in corpus}
    assert len(names) == 179
    assert names == build_contracts()["definitions"].keys()
    assert names.isdisjoint({"OperationReceipt", "ResultReference", "TransactionJournal"})
    for entry in corpus:
        assert entry.keys() == {"case_id", "definition", "value"}
        assert json.loads(json.dumps(entry["value"], allow_nan=False)) == entry["value"]


def test_host_models_keep_original_authorities_and_real_nested_unit_examples(
    corpus, original_models
):
    host_names = {
        "HostBinding",
        "HostPermissions",
        "HostPermissionReasons",
        "HostUnitState",
        "HostSyncSchedule",
        "HostFacts",
        "HostStatus",
    }
    assert host_names <= {entry["definition"] for entry in corpus}
    for name in host_names:
        assert original_models[name].__module__ == "hfcache.host_models"
        assert original_models[name].__name__ == name
    facts = next(entry["value"] for entry in corpus if entry["definition"] == "HostFacts")
    assert facts["units"].keys() == {
        "hfcache-sync.service",
        "hfcache-verify.service",
        "hfcache-sync.timer",
        "hfcache-verify.timer",
    }
    unit_examples = [entry["value"] for entry in corpus if entry["definition"] == "HostUnitState"]
    assert all(unit in unit_examples for unit in facts["units"].values())


def test_every_serialized_example_still_validates_with_its_original_python_authority(
    corpus, original_models
):
    for entry in corpus:
        name, value = entry["definition"], entry["value"]
        decoded = (
            validate_payload(name, value)
            if name in AUTHORITIES
            else original_models[name].model_validate(value)
        )
        # Request omission is intentional; output serializers must remain exact.
        if not name.startswith("Request"):
            serialized = (
                decoded.model_dump(mode="json") if isinstance(decoded, BaseModel) else decoded
            )
            assert serialized == value, entry["case_id"]


def test_mode_fixture_inventory_and_original_canonical_request_bodies_are_complete():
    modes = web_wire_corpus.covered_route_modes()
    assert len(modes) == 60
    assert modes == {(route.method, route.path, route.mode) for route in ROUTES}
    bodies = web_wire_corpus.request_samples()
    for name, model in request_authorities().items():
        model.model_validate(bodies["Request" + name])
    assert bodies["RequestInstalledValidation"] == {}
    assert bodies["RequestValidationSubmission"] == {}
    candidate = bodies["RequestLiteralCandidateValidation"]["candidate"]
    assert candidate.endswith("\n")
    assert bodies["RequestLiteralCandidatePlan"]["candidate"] == candidate
    assert bodies["RequestFullVerification"] == {
        "mode": "full",
        "revision": None,
        "run_id": None,
    }


def test_factory_needs_no_network_or_archive_initialization_and_cleans_its_tree(
    tmp_path, monkeypatch
):
    created = []

    def owned_temporary(*, prefix):
        temporary = TemporaryDirectory(prefix=prefix, dir=tmp_path)
        created.append(temporary.name)
        return temporary

    def forbidden(*args, **kwargs):
        pytest.fail("Original serializer corpus attempted network or archive initialization")

    monkeypatch.setattr(web_wire_corpus, "TemporaryDirectory", owned_temporary)
    monkeypatch.setattr(archive, "initialize_archive", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket.socket, "connect_ex", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    assert len(web_wire_corpus.serialized_corpus()) == 374
    assert len(created) == 1
    assert not any(tmp_path.iterdir())


def test_differential_negative_corpus_contains_only_original_authority_refusals(original_models):
    entries = web_wire_corpus.malformed_serialized_corpus()
    assert len(entries) == 2000
    assert len({entry["case_id"] for entry in entries}) == len(entries)
    assert {entry["definition"] for entry in entries} == build_contracts()["definitions"].keys()
    identities = set()
    for entry in entries:
        name, value = entry["definition"], entry["value"]
        identities.add(json.dumps([name, value], sort_keys=True))
        validate = (
            partial(validate_payload, name)
            if name in AUTHORITIES
            else original_models[name].model_validate
        )
        with pytest.raises((ValueError, TypeError)):
            validate(value)
    assert len(identities) == len(entries)
    # Accepted original cases must never become negatives merely for coverage.
    assert json.dumps(["EmptyPayload", {}], sort_keys=True) not in identities
    assert (
        json.dumps(["RequestSyncSubmission", {"selectors": []}], sort_keys=True) not in identities
    )
    assert any(
        entry["definition"] == "ClientOperation"
        and isinstance(entry["value"], dict)
        and entry["value"].get("transaction_ids") == [None]
        for entry in entries
    )
