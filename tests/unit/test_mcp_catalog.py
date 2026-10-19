"""V44-V46: explicit catalog MCP reads share REST evidence and refuse authority."""

import asyncio
import json
from dataclasses import replace

import httpx
import pytest

from hfcache.api.catalog_mcp_reads import CatalogReadAdapter
from hfcache.config import load_config
from hfcache.identity import RepositoryIdentity
from hfcache.services.queries import LocalQueries
from tests.fixtures import examples
from tests.unit import test_catalog_queries as domain
from tests.unit.test_mcp_tools import (
    PRIVATE_INPUT,
    call,
    error_text,
    forbid_effects,
    mounted,
    wire,
)
from tests.unit.test_mcp_tools import archive as archive  # noqa: PLC0414 - fixture
from tests.unit.test_server_bootstrap import (
    TOKEN,
    isolate_logging,  # noqa: F401 - autouse fixture
)
from tests.unit.test_server_bootstrap import policy as socket_policy  # noqa: F401 - fixture

DATASET = RepositoryIdentity.of("dataset", "science/data")


@pytest.fixture
def catalog(archive):
    path = archive.server.archive_config
    with path.open("a") as stream:
        stream.write(
            f'\n[[repositories]]\ntype="model"\nid="{domain.MODEL.id}"\n'
            'tags=["coding", "local-inference"]\n'
            '\n[[repositories]]\ntype="dataset"\nid="science/data"\n'
            'tags=["science", "local-inference"]\nenabled=false\n'
        )
    domain.publish(archive.queries.layout)
    domain.publish(archive.queries.layout, DATASET)
    return replace(archive, queries=LocalQueries(load_config(path)))


@pytest.mark.parametrize(
    ("tool", "arguments", "path", "params"),
    [
        (
            "search_models",
            {"tags_all": [" Coding "], "bits": 4},
            "/catalog/search",
            [("type", "model"), ("tag_all", "coding"), ("bits", "4")],
        ),
        (
            "search_models",
            {"quantization": "Q8_0", "max_variant_bytes": 5_000_000_000},
            "/catalog/search",
            [("type", "model"), ("quantization", "Q8_0"), ("max_variant_bytes", "5000000000")],
        ),
        (
            "search_datasets",
            {"format": "parquet", "scope": "configured"},
            "/catalog/search",
            [("type", "dataset"), ("format", "parquet"), ("scope", "configured")],
        ),
        (
            "get_catalog_entry",
            {"repository_type": "model", "repository_id": domain.MODEL.id},
            f"/catalog/repositories/model/{domain.MODEL.id}",
            [],
        ),
        (
            "list_model_variants",
            {"repository_id": domain.MODEL.id, "limit": 1},
            f"/catalog/repositories/model/{domain.MODEL.id}/variants",
            [("limit", "1")],
        ),
        (
            "get_catalog_facets",
            {"facet": "tag", "scope": "all", "tags_any": ["coding", "science"]},
            "/catalog/facets",
            [("facet", "tag"), ("scope", "all"), ("tag_any", "coding"), ("tag_any", "science")],
        ),
        (
            "get_catalog_facets",
            {"facet": "quantization", "repository_type": "model", "bits": 4},
            "/catalog/facets",
            [("facet", "quantization"), ("type", "model"), ("bits", "4")],
        ),
    ],
)
def test_actual_rest_and_mcp_catalog_payload_identity_coverage_and_evidence_match(  # noqa: PLR0913, PLR0917 - transport parity parameters
    catalog, monkeypatch, tool, arguments, path, params
):
    async def check():
        async with (
            mounted(catalog) as client,
            httpx.AsyncClient(
                transport=httpx.ASGITransport(app=catalog.app),
                base_url="http://localhost",
                trust_env=False,
                headers={"Authorization": "Bearer " + TOKEN},
            ) as rest,
        ):
            forbid_effects(monkeypatch)
            mcp = wire(await call(client, catalog, tool, arguments), catalog)
            response = await rest.get("/api/v1" + path, params=params)
            assert response.status_code == 200, response.text
            http = response.json()
            assert mcp["archive_id"] == http["archive_id"]
            assert mcp["config_fingerprint"] == http["config_fingerprint"]
            assert mcp["envelope"]["data"] == http["envelope"]["data"]
            assert mcp["envelope"]["warnings"] == http["envelope"]["warnings"]
            assert mcp["envelope"]["command"] == tool
            if mcp["next_cursor"] is not None:
                assert mcp["next_cursor"] != http["next_cursor"]

    asyncio.run(check())


@pytest.mark.parametrize(
    ("tool", "arguments"),
    [
        ("search_datasets", {"bits": 4}),
        ("search_datasets", {"quantization": "Q4_0"}),
        ("search_models", {"tags_all": ["x"] * 65}),
        ("search_models", {"tags_any": ["x" * 129]}),
        ("search_models", {"q": "é" * 257}),
        ("search_models", {"limit": True}),
        ("search_models", {"limit": 1001}),
        ("search_models", {"bits": "4"}),
        ("search_models", {"max_variant_bytes": -1}),
        ("search_models", {"cursor": "é"}),
        ("search_models", {"tags_all": ["bad value " + PRIVATE_INPUT]}),
        ("get_catalog_entry", {"repository_type": "model", "repository_id": "../" + PRIVATE_INPUT}),
        (
            "get_catalog_entry",
            {
                "repository_type": "model",
                "repository_id": domain.MODEL.id,
                "commit_sha": examples.SHA,
            },
        ),
        (
            "list_model_variants",
            {
                "repository_id": domain.MODEL.id,
                "commit_sha": "a" * 39,
                "publication_id": examples.PUBLICATION,
            },
        ),
        ("get_catalog_facets", {"facet": "tag", "repository_type": "dataset", "bits": 4}),
    ],
)
def test_hostile_catalog_arguments_are_masked_without_reads_or_effects(
    catalog, monkeypatch, tool, arguments
):
    async def check():
        async with mounted(catalog) as client:
            forbid_effects(monkeypatch)
            text = error_text(await call(client, catalog, tool, arguments))
            assert "HF" in text
            assert PRIVATE_INPUT not in text
            assert "Traceback" not in text
            assert "ValidationError" not in text

    asyncio.run(check())


@pytest.mark.parametrize("change", ["tags", "tool", "filter"])
def test_catalog_cursor_binds_visible_curation_tool_and_normalized_intent(catalog, change):
    async def check():
        async with mounted(catalog) as client:
            first = wire(await call(client, catalog, "search_models", {"limit": 1}), catalog)
            assert first["next_cursor"] is not None
            arguments = {"limit": 1, "cursor": first["next_cursor"]}
            tool = "search_models"
            if change == "tags":
                path = catalog.server.archive_config
                path.write_text(path.read_text().replace('"coding"', '"changed"'))
            elif change == "tool":
                tool = "search_datasets"
            else:
                arguments["q"] = "different"
            assert "HFAPI007" in error_text(await call(client, catalog, tool, arguments))

    asyncio.run(check())


def test_exact_variant_walk_is_complete_and_partial_coverage_never_proves_absence(catalog):
    async def check():
        async with mounted(catalog) as client:
            arguments = {
                "repository_id": domain.MODEL.id,
                "commit_sha": examples.SHA,
                "publication_id": examples.PUBLICATION,
                "limit": 1,
            }
            bodies = []
            for _ in range(3):
                body = wire(await call(client, catalog, "list_model_variants", arguments), catalog)
                bodies.append(body)
                if body["next_cursor"] is None:
                    break
                arguments["cursor"] = body["next_cursor"]
            assert sum(len(body["envelope"]["data"]["entries"]) for body in bodies) == 2
            assert bodies[-1]["next_cursor"] is None
            empty = wire(await call(client, catalog, "search_models", {"q": "absent"}), catalog)
            assert empty["envelope"]["data"]["entries"] == []
            assert empty["envelope"]["data"]["coverage"]["incomplete"] is True
            assert empty["envelope"]["warnings"][0]["code"] == "HFWRN011"

    asyncio.run(check())


def test_catalog_facade_has_only_five_named_reads_and_no_command_capability():
    async def deny(_):
        pytest.fail("capability inspection must not execute")

    adapter = CatalogReadAdapter(deny)
    assert {name for name in dir(adapter) if not name.startswith("_")} == {
        "search_models",
        "search_datasets",
        "get_catalog_entry",
        "list_model_variants",
        "get_catalog_facets",
    }
    assert not hasattr(adapter, "__dict__")
    assert "refresh" not in json.dumps(sorted(dir(adapter)))
