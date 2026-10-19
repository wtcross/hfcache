"""V41-43: complete API-only catalog CLI output and original refresh safety handles."""

import copy
import json

import httpx
import pytest
from typer.testing import CliRunner

from hfcache import cli
from hfcache.catalog_display import catalog_rows
from hfcache.client import ApiClient
from hfcache.client_config import resolve_client_config
from hfcache.config import load_config
from hfcache.identity import RepositoryIdentity
from hfcache.models import dump
from hfcache.services.catalog_queries import CatalogQueries
from hfcache.services.requests import CatalogRefreshRequest
from tests.api_cli import api_cli
from tests.fixtures import examples
from tests.unit import test_api_catalog_refresh as refresh
from tests.unit import test_api_commands as api
from tests.unit import test_catalog_queries as domain
from tests.unit.test_synchronize import MODEL

configured = api.configured


@pytest.fixture
def catalogued(configured):
    server, layout, _, _ = configured
    refresh.tags(server, ["coding", "local"])
    source = server.archive_config.read_text().replace(
        'id = "organization/dataset-name"',
        'id = "organization/dataset-name"\ntags = ["science"]\nenabled = false',
    )
    server.archive_config.write_text(source)
    domain.publish(layout)
    domain.publish(layout, RepositoryIdentity.of("model", "org/unmanaged"))
    return configured


@pytest.mark.parametrize(
    "arguments",
    [
        ["search", "--scope", "all", "--page-size", "1"],
        ["tags", "--scope", "all", "--page-size", "1"],
        ["catalog", "show", MODEL.selector],
        ["catalog", "variants", MODEL.selector, "--page-size", "1"],
    ],
)
def test_cli_catalog_reads_collect_and_preserve_server_envelope(catalogued, monkeypatch, arguments):
    server, _, _, _ = catalogued

    def forbidden(*args, **kwargs):
        pytest.fail("catalog CLI attempted client-local archive configuration")

    monkeypatch.setattr(cli, "load_config", forbidden)
    with api_cli(server.archive_config, reader=True, page_size=1) as remote:
        responses = []
        original = remote.exchange

        def exchange(request):
            response = original(request)
            if "/catalog/" in request.url.path:
                assert response.status_code == 200
                responses.append(response.json()["envelope"])
            return response

        remote.patch.setattr(
            "hfcache.cli_client.ApiClient",
            lambda settings: ApiClient(settings, transport=httpx.MockTransport(exchange)),
        )
        result = remote.invoke(arguments)
        assert result.exit_code == 0, result.output
        payload = json.loads(result.stdout)
        expected = copy.deepcopy(responses[0])
        if "entries" in expected["data"]:
            expected["data"]["entries"] = [
                entry for item in responses for entry in item["data"]["entries"]
            ]
        assert payload == expected
        assert len(result.stdout.splitlines()) == 1


def test_search_and_tags_map_all_any_and_literal_predicates(catalogued):
    server, _, _, _ = catalogued
    with api_cli(server.archive_config, reader=True, page_size=1) as remote:
        found = remote.invoke(
            [
                "search",
                "--scope",
                "all",
                "--tag",
                "CODING",
                "--tag",
                " local ",
                "--any-tag",
                "local",
                "--query",
                "model-name",
                "--quantization",
                "Q4_0",
                "--max-variant-bytes",
                "5000000000",
            ]
        )
        assert found.exit_code == 0, found.output
        data = json.loads(found.stdout)["data"]
        assert data["total_matches"] == 1
        assert data["entries"][0]["matching_variant_count"] == 1
        assert data["entries"][0]["tags"] == ["coding", "local"]
        facets = remote.invoke(["tags", "--scope", "configured", "--type", "dataset"])
        assert facets.exit_code == 0, facets.output
        assert json.loads(facets.stdout)["data"]["entries"] == [
            {"value": "science", "repository_count": 1}
        ]


def test_human_provenance_representative_and_quiet_incomplete_coverage(catalogued):
    server, layout, _, _ = catalogued
    unmanaged = RepositoryIdentity.of("model", "org/unmanaged")
    repository = layout.repository(unmanaged)
    with api_cli(server.archive_config, reader=True) as remote:
        quiet = remote.invoke(["--quiet", "search", "--query", "no-known-match"], json_output=False)
        assert quiet.exit_code == 0
        assert quiet.stdout == ""
        assert "HFWRN011" in quiet.stderr
        human = remote.invoke(["search", "--scope", "all"], json_output=False)
        assert "tags [configured]" in human.stdout
        assert "tags [unknown]" in human.stdout
        assert "representative" in human.stdout
        assert "matching primary variants" in human.stdout
        assert "incomplete" in human.stdout
        snapshot = examples.tag_snapshot().model_copy(
            update={"repository_id": unmanaged.id, "tags": ("historic",)}
        )
        repository.tag_snapshot.parent.mkdir(parents=True, exist_ok=True)
        repository.tag_snapshot.write_bytes(dump(snapshot))
        historical = remote.invoke(["catalog", "show", unmanaged.selector], json_output=False)
        assert "tags [last_observed]: historic" in historical.stdout
        excluded = remote.invoke(["tags", "--tag-source", "current_only"])
        assert all(
            item["value"] != "historic" for item in json.loads(excluded.stdout)["data"]["entries"]
        )


def test_unfinished_cli_walk_is_failed_with_no_successful_partial_entries(catalogued):
    server, _, _, _ = catalogued
    with api_cli(server.archive_config, reader=True, page_size=1) as remote:
        remote.settings.write_text("schema_version=1\nmax_pages=1\n")
        result = remote.invoke(["search", "--scope", "all"])
        assert result.exit_code == 10
        payload = json.loads(result.stdout)
        assert payload["outcome"] == "failed"
        assert "entries" not in payload["data"]


@pytest.mark.parametrize(
    "arguments",
    [
        ["search", "--type", "dataset", "--bits", "4"],
        ["search", "--tag", "invalid tag"],
        ["catalog", "show", MODEL.selector + "@" + examples.SHA],
        ["catalog", "refresh", "--tags-only", "--technical-only"],
    ],
)
def test_bad_catalog_intent_refuses_without_client_configuration_access(tmp_path, arguments):
    result = CliRunner().invoke(
        cli.app, ["--json", "--client-config", str(tmp_path / "absent"), *arguments]
    )
    assert result.exit_code == 10
    assert json.loads(result.stdout)["errors"][0]["code"] in {"HFARG001", "HFARG002"}


def test_refresh_cli_observes_exact_typed_writer_result(catalogued, monkeypatch):
    server, layout, _, _ = catalogued
    refresh.no_external_capability(monkeypatch)
    with api_cli(server.archive_config) as remote:
        result = remote.invoke(["catalog", "refresh", MODEL.selector, "--tags-only"])
        assert result.exit_code == 0, result.output
        payload = json.loads(result.stdout)
        assert payload["command"] == "catalog refresh"
        assert payload["data"]["counts"]["snapshots_written"] == 1
        assert payload["data"]["technical"] is False
        assert layout.repository(MODEL).tag_snapshot.is_file()
        operation = remote.application.state.operations.list()[0]
        exact = remote.web.get(
            f"/api/v1/operations/{operation.operation_id}/result",
            headers={"authorization": "Bearer " + remote.token.read_text()},
        )
        assert payload == exact.json()["envelope"]
        detached = remote.invoke(
            [
                "--detach",
                "--idempotency-key",
                "detached-capture",
                "catalog",
                "refresh",
                MODEL.selector,
                "--tags-only",
            ]
        )
        assert detached.exit_code == 0, detached.output
        admission = json.loads(detached.stdout)
        assert admission["kind"] == "operation_admission"
        assert admission["idempotency_key"] == "detached-capture"


def test_uncertain_refresh_ack_retains_original_key_and_lookup_without_resubmission(catalogued):
    server, _, _, _ = catalogued
    with api_cli(server.archive_config) as remote:
        posted = []
        original = remote.exchange

        def exchange(request):
            response = original(request)
            if request.method == "POST" and request.url.path.endswith("/catalog/refreshes"):
                posted.append(request)
                return httpx.Response(202, json={"schema_version": 999})
            return response

        remote.patch.setattr(
            "hfcache.cli_client.ApiClient",
            lambda settings: ApiClient(settings, transport=httpx.MockTransport(exchange)),
        )
        result = remote.invoke(
            [
                "--idempotency-key",
                "retained-refresh-key",
                "catalog",
                "refresh",
                MODEL.selector,
                "--tags-only",
            ]
        )
        assert result.exit_code == 20
        payload = json.loads(result.stdout)
        assert payload["data"]["idempotency_key"] == "retained-refresh-key"
        assert payload["data"]["work_may_continue"] is True
        assert payload["data"]["route"] == "/api/v1/catalog/refreshes"
        assert len(posted) == 1
        lookup = remote.invoke(["operations", "lookup", "--", "retained-refresh-key"])
        assert lookup.exit_code == 0, lookup.output
        assert len(posted) == 1


def test_human_archive_declarations_escape_terminal_control(configured):
    server, layout, _, _ = configured
    record = domain.publish(layout)
    source = record.sources[0].model_copy(
        update={"values": ("untrusted\x1b[31m\nignore instructions",)}
    )
    record = record.model_copy(update={"sources": (source,)})
    path = layout.repository(domain.MODEL).observation(
        domain.CommitSha(record.commit_sha), domain.PublicationId(record.publication_id)
    )
    path.write_bytes(dump(record))
    data = CatalogQueries(load_config(server.archive_config)).detail(domain.MODEL).result.data
    rendered = "\n".join(catalog_rows(data, "detail"))
    assert "\x1b" not in rendered
    assert "\\u001b" in rendered
    assert "\\u000a" in rendered


def test_typed_sdk_refresh_submits_once_and_observes_its_original_result(catalogued, monkeypatch):
    server, _, _, _ = catalogued
    refresh.no_external_capability(monkeypatch)
    with api_cli(server.archive_config) as remote:
        settings = resolve_client_config(
            remote.settings, api_url="http://localhost", api_token_file=remote.token
        )
        with ApiClient(settings, transport=httpx.MockTransport(remote.exchange)) as client:
            admitted = client.catalog_refresh(
                CatalogRefreshRequest(selectors=(MODEL.selector,), technical=False),
                key="typed-refresh",
            )
            result = client.observe(admitted.acceptance.operation.operation_id)
            assert result.envelope.command == "catalog refresh"
            assert result.envelope.exit_code == 0
            assert result.envelope.data["counts"]["snapshots_written"] == 1
            typed = client.catalog_refresh_result(admitted.acceptance.operation.operation_id)
            assert typed.payload is not None
            assert typed.payload.counts.snapshots_written == 1
            assert typed.response.envelope.to_payload() == result.envelope.to_payload()
            repeated = client.catalog_refresh(
                CatalogRefreshRequest(selectors=(MODEL.selector,), technical=False),
                key="typed-refresh",
            )
            assert repeated.acceptance.created is False
            assert (
                repeated.acceptance.operation.operation_id
                == admitted.acceptance.operation.operation_id
            )
