"""V41-42: typed independent wire data and complete, bounded, identity-pinned walks."""

import copy
import json
import subprocess
import sys

import httpx
import pytest
from pydantic import TypeAdapter

from hfcache.catalog_query_models import CatalogQuery
from hfcache.client import ApiClient
from hfcache.client_catalog import collect_catalog
from hfcache.client_config import ClientConfig
from hfcache.client_errors import ClientProtocolError
from hfcache.client_models import ClientOperation
from hfcache.errors import ConfigurationError
from hfcache.identity import RepositoryIdentity, new_run_id
from hfcache.models import ArchiveIdField
from hfcache.services.catalog_queries import CatalogQueries
from hfcache.services.context import ExecutionContext
from tests.fixtures import examples
from tests.unit import test_api_client_adversarial as old_client
from tests.unit import test_catalog_queries as domain

layout = domain.layout
config = domain.config


def wire(config, page):
    return {
        "schema_version": 1,
        "request_id": new_run_id(),
        "archive_id": config.storage.archive_id,
        "config_fingerprint": config.fingerprint(),
        "envelope": page.result.envelope(ExecutionContext.create()).to_payload(),
        "next_cursor": page.next_cursor,
    }


@pytest.fixture
def pages(config, layout):
    domain.publish(layout)
    domain.publish(layout, RepositoryIdentity.of("model", "zz/second"))
    queries = CatalogQueries(config)
    first = queries.search(CatalogQuery(limit=1))
    second = queries.search(CatalogQuery(limit=1, cursor=first.next_cursor))
    return [wire(config, first), wire(config, second)]


@pytest.fixture
def client_factory(tmp_path):
    token = tmp_path / "selected-rest-token"
    token.write_text("fixture-reader-" + "R" * 40)
    token.chmod(0o600)
    opened = []

    def make(replies, **options):
        requests = []
        replies = iter(replies)

        def respond(request):
            requests.append(request)
            payload = next(replies)
            return httpx.Response(
                200, json=payload, headers={"X-Request-ID": payload["request_id"]}
            )

        client = ApiClient(
            ClientConfig.model_validate(
                {
                    "schema_version": 1,
                    "api_url": "https://archive.example/management",
                    "api_token_file": str(token),
                    "read_retries": 0,
                    **options,
                }
            ),
            transport=httpx.MockTransport(respond),
        )
        opened.append(client)
        return client, requests

    yield make
    for client in opened:
        client.close()


def test_typed_search_walk_preserves_first_server_envelope_and_complete_rows(client_factory, pages):
    client, requests = client_factory(pages)
    result = collect_catalog(
        client.iter_catalog_search(CatalogQuery(limit=1)),
        maximum_bytes=client.config.max_response_bytes,
    )
    expected = copy.deepcopy(pages[0]["envelope"])
    expected["data"]["entries"] += pages[1]["envelope"]["data"]["entries"]
    assert result.to_payload() == expected
    assert len(requests) == 2
    assert requests[0].url.path == "/management/api/v1/catalog/search"
    assert requests[1].url.params["cursor"] == pages[0]["next_cursor"]


def test_wire_aliases_and_expanding_unicode_keep_original_bounded_text(
    client_factory, config, layout
):
    domain.publish(layout)
    queries = CatalogQueries(config)
    query = CatalogQuery(
        q="ß" * 256, tags_all=(" LOCAL ", "coding", "CODING"), tags_any=("science",)
    )
    assert query.q is not None
    assert len(query.q) == 512
    assert query.with_cursor(None).canonical_filters() == query.canonical_filters()
    payload = wire(config, queries.search(query))
    client, requests = client_factory([payload])
    read = client.catalog_search(query)
    assert read.payload is not None
    assert read.payload.total_matches == 0
    assert requests[0].url.params["q"] == "ß" * 256
    assert requests[0].url.params.get_list("tag_all") == ["coding", "local"]
    assert requests[0].url.params.get_list("tag_any") == ["science"]


@pytest.mark.parametrize("version", [None, True, "1", 2])
def test_catalog_payload_version_is_explicit_and_independent(client_factory, pages, version):
    payload = copy.deepcopy(pages[0])
    if version is None:
        payload["envelope"]["data"].pop("schema_version")
    else:
        payload["envelope"]["data"]["schema_version"] = version
    client, _ = client_factory([payload])
    with pytest.raises(ClientProtocolError):
        client.catalog_search(CatalogQuery(limit=1))


@pytest.mark.parametrize(
    "change",
    [
        "catalog",
        "policy",
        "archive",
        "coverage",
        "duplicate",
        "short",
        "cycle",
        "command",
        "cursor_unicode",
    ],
)
def test_inconsistent_walk_never_becomes_a_successful_collection(client_factory, pages, change):
    first, second = copy.deepcopy(pages)
    data = second["envelope"]["data"]
    if change == "catalog":
        data["catalog_identity"] = "f" * 64
    elif change == "policy":
        second["config_fingerprint"] = "e" * 64
    elif change == "archive":
        second["archive_id"] = "11111111-1111-4111-8111-111111111111"
    elif change == "coverage":
        data["coverage"]["usable"] -= 1
        data["coverage"]["failed"] += 1
    elif change == "duplicate":
        data["entries"] = first["envelope"]["data"]["entries"]
    elif change == "short":
        data["entries"] = []
    elif change == "cycle":
        second["next_cursor"] = first["next_cursor"]
    elif change == "command":
        second["envelope"]["command"] = "status"
    else:
        second["next_cursor"] = "private-é"
    client, _ = client_factory([first, second])
    with pytest.raises(ClientProtocolError):
        collect_catalog(
            client.iter_catalog_search(CatalogQuery(limit=1)),
            maximum_bytes=client.config.max_response_bytes,
        )


def test_page_limit_and_unfinished_walk_fail_visibly(client_factory, pages):
    client, _ = client_factory(pages, max_pages=1)
    with pytest.raises(ClientProtocolError):
        collect_catalog(
            client.iter_catalog_search(CatalogQuery(limit=1)),
            maximum_bytes=client.config.max_response_bytes,
        )
    client, requests = client_factory(pages)
    with pytest.raises(ClientProtocolError):
        list(client.iter_catalog_search(CatalogQuery(cursor=pages[0]["next_cursor"])))
    assert requests == []


def test_aggregate_byte_limit_is_independent_of_each_valid_page(client_factory, config, layout):
    for name in ("org/a", "org/b", "org/c", "org/d"):
        domain.publish(layout, RepositoryIdentity.of("model", name))
    queries = CatalogQueries(config)
    all_pages = []
    cursor = None
    while True:
        page = queries.search(CatalogQuery(limit=1, cursor=cursor))
        all_pages.append(wire(config, page))
        cursor = page.next_cursor
        if cursor is None:
            break
    maximum = max(len(json.dumps(page).encode()) for page in all_pages) + 128
    assert (
        sum(len(json.dumps(page["envelope"]["data"]["entries"]).encode()) for page in all_pages)
        > maximum
    )
    client, _ = client_factory(all_pages, max_response_bytes=maximum)
    with pytest.raises(ClientProtocolError):
        collect_catalog(client.iter_catalog_search(CatalogQuery(limit=1)), maximum_bytes=maximum)


def test_facet_and_variant_pages_and_exact_detail_have_typed_payloads(
    client_factory, config, layout
):
    domain.publish(layout)
    queries = CatalogQueries(config)
    facets = queries.facets("quantization", CatalogQuery(limit=1))
    facets2 = queries.facets("quantization", CatalogQuery(limit=1, cursor=facets.next_cursor))
    client, requests = client_factory([wire(config, facets), wire(config, facets2)])
    combined = collect_catalog(
        client.iter_catalog_facets("quantization", CatalogQuery(limit=1)),
        maximum_bytes=client.config.max_response_bytes,
    )
    assert len(combined.data["entries"]) == 2
    assert requests[0].url.params["facet"] == "quantization"
    variants = queries.variants(domain.MODEL, limit=1)
    variants2 = queries.variants(domain.MODEL, limit=1, cursor=variants.next_cursor)
    client, _ = client_factory([wire(config, variants), wire(config, variants2)])
    combined = collect_catalog(
        client.iter_catalog_variants(domain.MODEL, limit=1),
        maximum_bytes=client.config.max_response_bytes,
    )
    assert len(combined.data["entries"]) == 2
    detail = queries.detail(domain.MODEL)
    client, requests = client_factory([wire(config, detail)])
    typed = client.catalog_entry(
        domain.MODEL, commit_sha=examples.SHA, publication_id=examples.PUBLICATION
    )
    assert typed.payload is not None
    assert typed.payload.entry.repository_id == domain.MODEL.id
    assert requests[0].url.params["publication_id"] == examples.PUBLICATION


def test_invalid_catalog_scope_refuses_before_transmission(client_factory):
    client, requests = client_factory([])
    with pytest.raises(ConfigurationError):
        client.catalog_entry(domain.MODEL, commit_sha=examples.SHA)
    with pytest.raises(ConfigurationError):
        client.catalog_variants(RepositoryIdentity.of("dataset", "org/data"))
    assert requests == []


def test_base_catalog_imports_keep_writer_hub_and_optional_frameworks_cold():
    code = """import sys
import hfcache.client, hfcache.client_catalog, hfcache.catalog_refresh_models
assert "hfcache.config" not in sys.modules
import hfcache.cli
blocked = ('hfcache.services.commands', 'hfcache.catalog_capture', 'hfcache.catalog_storage',
           'hfcache.archive', 'hfcache.hub', 'huggingface_hub',
           'fastapi', 'uvicorn', 'fastmcp', 'mcp')
loaded = [name for name in blocked if name in sys.modules]
assert not loaded, loaded
"""
    completed = subprocess.run(
        [sys.executable, "-I", "-c", code], capture_output=True, text=True, check=False
    )
    assert completed.returncode == 0, completed.stderr


@pytest.mark.parametrize("version", [None, True, "1", 2])
def test_refresh_result_observation_requires_its_independent_schema(client_factory, version):
    response = old_client._read(data={"schema_version": version})
    response["envelope"]["command"] = "catalog refresh"
    receipt = old_client._operation(state="succeeded")
    receipt["route"] = "/api/v1/catalog/refreshes"
    if version is None:
        response["envelope"]["data"].pop("schema_version")
    client, _ = client_factory([response])
    client._operations[receipt["operation_id"]] = ClientOperation.model_validate(receipt)
    with pytest.raises(ClientProtocolError):
        client.result(receipt["operation_id"])


def test_exact_detail_and_variants_cannot_substitute_another_identity(
    client_factory, config, layout
):
    domain.publish(layout)
    queries = CatalogQueries(config)
    detail = wire(config, queries.detail(domain.MODEL))
    detail["envelope"]["data"]["entry"]["repository_id"] = "other/repository"
    client, _ = client_factory([detail])
    with pytest.raises(ClientProtocolError):
        client.catalog_entry(domain.MODEL)
    variants = wire(config, queries.variants(domain.MODEL))
    variants["envelope"]["data"]["entries"][0]["publication_id"] = "0" * 32
    client, _ = client_factory([variants])
    with pytest.raises(ClientProtocolError):
        client.catalog_variants(
            domain.MODEL, commit_sha=examples.SHA, publication_id=examples.PUBLICATION
        )


@pytest.mark.parametrize(
    "value",
    [
        None,
        True,
        1,
        "",
        examples.ARCHIVE_ID.upper(),
        "{" + examples.ARCHIVE_ID + "}",
        examples.ARCHIVE_ID.replace("-", ""),
    ],
)
def test_pure_archive_identity_retains_strict_canonical_uuid_constraint(value):
    parser = TypeAdapter(ArchiveIdField)
    assert parser.validate_python(examples.ARCHIVE_ID) == examples.ARCHIVE_ID
    with pytest.raises(ValueError, match="Archive identity"):
        parser.validate_python(value)
