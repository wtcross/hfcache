"""V36-38: real authenticated HTTP projection, strict grammar and cursor binding."""

import asyncio
import threading

import pytest

from hfcache.api.app import create_app
from hfcache.catalog_query_models import CatalogQuery
from hfcache.catalog_storage import CatalogWriter
from hfcache.config import load_config
from hfcache.identity import RepositoryIdentity
from hfcache.paths import ArchiveLayout
from hfcache.server_config import validate_server_config_mapping
from hfcache.services.catalog_queries import CatalogQueries
from tests.fixtures import examples
from tests.unit import test_api_reads as api
from tests.unit import test_catalog_queries as catalog

configured = api.configured
client_context = api.client_context
PREFIX = "/api/v1/catalog"
STEM = PREFIX + "/repositories/model/" + examples.REPOSITORY_ID


@pytest.fixture
def prepared(configured):
    data, policy, archive, lock = configured
    layout = ArchiveLayout(archive)
    api.write_model(layout.sentinel, examples.sentinel())
    catalog.publish(layout)
    catalog.publish(layout, RepositoryIdentity.of("model", "zz/second"))
    with policy.open("a") as stream:
        for name in (examples.REPOSITORY_ID, "zz/second"):
            stream.write(
                f'\n[[repositories]]\ntype="model"\nid="{name}"\ntags=["coding","local"]\n'
            )
    return data, policy, layout, lock


def application(prepared):
    data, _, _, lock = prepared
    return create_app(validate_server_config_mapping(data), instance_lock_path=lock)


def test_catalog_routes_share_strict_wrappers_and_original_capabilities(prepared):
    app = application(prepared)

    async def read(client):
        search = await client.get(PREFIX + "/search?quantization=Q4_0&max_variant_bytes=5000000000")
        assert search.status_code == 200
        payload = search.json()
        assert set(payload) == {
            "schema_version",
            "request_id",
            "archive_id",
            "config_fingerprint",
            "envelope",
            "next_cursor",
        }
        assert payload["envelope"]["data"]["total_matches"] == 2
        assert payload["envelope"]["data"]["entries"][0]["matching_variant_count"] == 1
        for token in (api.READER, api.WRITER):
            headers = {"authorization": f"Bearer {token}"}
            assert (await client.get(STEM, headers=headers)).status_code == 200
            variants = await client.get(STEM + "/variants?limit=1", headers=headers)
            assert variants.status_code == 200
            assert variants.json()["next_cursor"]
        facets = await client.get(PREFIX + "/facets?facet=quantization&bits=4")
        assert facets.json()["envelope"]["data"]["entries"] == [
            {"value": "Q4_0", "repository_count": 2}
        ]
        old = (await client.get("/api/v1/capabilities")).json()["envelope"]["data"]
        assert set(old) == {
            "api_version",
            "credential_class",
            "capabilities",
            "instance_id",
            "reads",
            "operations",
            "operation_history",
            "mcp",
            "maintenance_enabled",
            "max_page_size",
        }
        assert (await client.get("/api/v1/repositories")).status_code == 200
        schema = (await client.get("/api/v1/openapi.json")).json()
        assert schema["paths"][PREFIX + "/search"]["get"]["x-catalog-payload"]["properties"][
            "catalog_identity"
        ]
        parameters = {
            item["name"]: item["schema"]
            for item in schema["paths"][PREFIX + "/search"]["get"]["parameters"]
        }
        assert parameters["bits"]["minimum"] == 1
        assert parameters["bits"]["maximum"] == 64

    asyncio.run(client_context(app, read))


@pytest.mark.parametrize(
    "query",
    [
        "unknown=value",
        "type=model&type=model",
        "limit=1&limit=2",
        "q=a&q=b",
        "bits=true",
        "bits=4.0",
        "bits=-1",
        "bits=%2B4",
        "bits=04",
        "bits=0",
        "bits=65",
        "max_variant_bytes=9223372036854775808",
        "max_variant_bytes=-1",
        "limit=0",
        "limit=10001",
        "tag_all=",
        "tag_all=non%20canonical",
        "scope=latest",
        "revision_scope=latest",
        "tag_source=upstream",
        "type=dataset&bits=4",
        "cursor=%C3%A9",
    ],
)
def test_catalog_search_rejects_unknown_repeated_or_coerced_parameters(prepared, query):
    app = application(prepared)

    async def read(client):
        response = await client.get(PREFIX + "/search?" + query)
        assert response.status_code == 422
        assert set(response.json()) == {"request_id", "code", "message", "exit_code"}

    asyncio.run(client_context(app, read))


def test_authentication_and_body_budgets_precede_routing_and_no_raw_echo(prepared):
    app = application(prepared)

    async def read(client):
        for token in ("", "hf_" + "A" * 40, "unknown-value"):
            result = await client.request(
                "GET",
                PREFIX + "/search?unknown=private-marker",
                headers={"authorization": f"Bearer {token}"},
                content=b"private-marker",
            )
            assert result.status_code == 401
            assert "private-marker" not in result.text
        assert (await client.request("GET", PREFIX + "/search", content=b"{}")).status_code == 422
        assert (
            await client.get(PREFIX + "/search", headers={"x-overflow": "a" * 33000})
        ).status_code == 413
        assert (await client.get(PREFIX + "/search?q=" + "x" * 8193)).status_code == 413
        for path in (
            STEM + "?commit_sha=" + examples.SHA,
            STEM + "?publication_id=" + examples.PUBLICATION,
            STEM + "?limit=1",
            STEM + "?revision_scope=retained&revision_scope=current",
            PREFIX + "/repositories/models/org/name",
            PREFIX + "/repositories/dataset/org/name/variants",
            PREFIX + "/facets?facet=unknown",
        ):
            assert (await client.get(path)).status_code == 422

    asyncio.run(client_context(app, read))


def test_cursor_canonical_tag_sets_and_tag_only_staleness_keep_policy_hash(prepared):
    app = application(prepared)
    _, policy, _, _ = prepared
    original = load_config(policy).fingerprint()

    async def read(client):
        params = [
            ("tag_all", "CODING"),
            ("tag_all", " local "),
            ("tag_all", "coding"),
            ("limit", "1"),
        ]
        first = (await client.get(PREFIX + "/search", params=params)).json()
        canonical = (
            await client.get(PREFIX + "/search?tag_all=local&tag_all=coding&limit=1")
        ).json()
        assert first["next_cursor"] == canonical["next_cursor"]
        cursor = first["next_cursor"]
        assert cursor
        assert (
            await client.get(
                PREFIX + "/search", params={"tag_all": ["coding", "local"], "cursor": cursor}
            )
        ).status_code == 200
        assert (
            await client.get(PREFIX + "/facets", params={"facet": "tag", "cursor": cursor})
        ).status_code == 409
        policy.write_text(policy.read_text().replace('["coding","local"]', '["coding","changed"]'))
        assert load_config(policy).fingerprint() == original
        stale = await client.get(
            PREFIX + "/search", params={"tag_all": ["coding", "local"], "cursor": cursor}
        )
        assert stale.status_code == 409
        assert stale.json()["code"] == "HFAPI007"

    asyncio.run(client_context(app, read))


def test_exact_detail_and_full_variant_pages_do_not_fall_back(prepared):
    app = application(prepared)

    async def read(client):
        params = {"commit_sha": examples.SHA, "publication_id": examples.PUBLICATION}
        detail = await client.get(STEM, params=params)
        assert detail.status_code == 200
        assert "variants" not in detail.json()["envelope"]["data"]["observations"][0]
        first = (await client.get(STEM + "/variants", params=params | {"limit": 1})).json()
        second = (
            await client.get(
                STEM + "/variants", params=params | {"limit": 1, "cursor": first["next_cursor"]}
            )
        ).json()
        assert first["envelope"]["data"]["total_matches"] == 2
        assert second["next_cursor"] is None
        assert first["envelope"]["data"]["entries"] != second["envelope"]["data"]["entries"]
        missing = await client.get(STEM, params=params | {"publication_id": "0" * 32})
        assert missing.status_code == 404
        assert missing.json()["code"] == "HFAPI007"
        assert missing.json()["exit_code"] == 10

    asyncio.run(client_context(app, read))


def test_reads_are_off_thread_and_cannot_write_resolve_credentials_or_open_payload(
    prepared, monkeypatch
):
    app = application(prepared)
    _, policy, layout, _ = prepared
    snapshots = {str(path): path.read_bytes() for path in layout.root.rglob("*") if path.is_file()}
    threads = []
    original = CatalogQueries.search

    def tracked(self, query=CatalogQuery(), **kwargs):  # noqa: B008 - immutable test intent
        threads.append(threading.current_thread())
        return original(self, query, **kwargs)

    def forbidden(*args, **kwargs):
        pytest.fail("catalog GET acquired writer/network/credential capability")

    monkeypatch.setattr(CatalogQueries, "search", tracked)
    monkeypatch.setattr(CatalogWriter, "__init__", forbidden)
    monkeypatch.setattr("hfcache.credentials.resolve_token", forbidden)
    monkeypatch.setattr("socket.create_connection", forbidden)

    async def read(client):
        result = await client.get(PREFIX + "/search")
        assert result.status_code == 200
        assert (
            result.json()["envelope"]["data"]
            == CatalogQueries(load_config(policy)).search().result.data
        )
        assert app.state.pool.inflight == 0

    asyncio.run(client_context(app, read))
    assert threads[0] != threading.main_thread()
    assert snapshots == {
        str(path): path.read_bytes() for path in layout.root.rglob("*") if path.is_file()
    }


def test_catalog_full_scan_and_wire_refusal_are_classified(prepared):
    data, _, _, _ = prepared
    data["limits"] = {"max_scan_entries": 10}
    app = application(prepared)

    async def read(client):
        result = await client.get(PREFIX + "/search?limit=1")
        assert result.status_code == 503
        assert result.json()["code"] == "HFAPI005"

    asyncio.run(client_context(app, read))


def test_catalog_encoded_wrapper_cannot_exceed_response_budget(prepared):
    data, policy, _, _ = prepared
    data["limits"] = {"max_response_bytes": 1024}
    with policy.open("a") as stream:
        stream.write('\n[[repositories]]\ntype="model"\nid="org/unpublished"\n')
    app = application(prepared)

    async def read(client):
        response = await client.get(PREFIX + "/search?scope=configured&q=unpublished")
        assert response.status_code == 413
        assert response.json()["code"] == "HFAPI006"

    asyncio.run(client_context(app, read))


def test_unsafe_namespace_refuses_with_integrity_taxonomy_and_preserves_it(prepared):
    _, _, layout, _ = prepared
    original = layout.metadata.with_name("preserved-metadata")
    layout.metadata.rename(original)
    layout.metadata.symlink_to(original, target_is_directory=True)
    app = application(prepared)

    async def read(client):
        response = await client.get(PREFIX + "/search")
        assert response.status_code == 409
        assert response.json()["code"] == "HFVER007"
        assert response.json()["exit_code"] == 40
        assert layout.metadata.is_symlink()

    asyncio.run(client_context(app, read))
