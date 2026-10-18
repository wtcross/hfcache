"""API-002 shared query results preserve CLI contracts without transport imports."""

import ast
import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from hfcache.config import ApplicationConfig
from hfcache.errors import ConfigurationError, Problem
from hfcache.identity import RunId
from hfcache.metadata import MetadataReader
from hfcache.services.context import ExecutionContext, ServiceResult, new_operation_id
from hfcache.services.queries import (
    LocalQueries,
    MetadataQueries,
    RepositoryQuery,
    query_version,
    validate_config,
)
from tests.api_cli import api_cli
from tests.fixtures import examples


@pytest.fixture
def queries(tmp_path):
    config = ApplicationConfig.model_validate(
        {
            "schema_version": 1,
            "storage": {"archive_root": str(tmp_path), "archive_id": examples.ARCHIVE_ID},
            "repositories": [
                {"id": "zeta/configured-first", "type": "model"},
                {"id": "alpha/configured-second", "type": "dataset", "enabled": False},
            ],
        }
    )
    return LocalQueries(config)


def _publication(queries):
    reference = examples.reference()
    identity = reference.identity
    repository = queries.layout.repository(identity)
    paths = [
        (repository.current_ref, reference),
        (repository.revision_ref(examples.SHA), reference),
        (repository.manifest(examples.SHA, examples.PUBLICATION), examples.manifest()),
    ]
    for path, model in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(model.to_json(), encoding="utf-8")
    repository.instance(examples.SHA, examples.PUBLICATION).mkdir(parents=True)
    return identity


def test_result_and_problem_payloads_are_independent_immutable_snapshots():
    original = {"rows": [{"value": "first"}]}
    problem = Problem(code="HFWRN003", message="preserved", context={"items": ["one"]})
    result = ServiceResult("status", original, warnings=(problem,))
    original["rows"][0]["value"] = "changed"
    problem.context["items"].append("two")
    rendered = result.data
    rendered["rows"][0]["value"] = "adapter change"

    assert result.data == {"rows": [{"value": "first"}]}
    with pytest.raises(TypeError):
        # pyrefly: ignore [unsupported-operation] - exercise the runtime immutability boundary
        result.payload["new"] = True
    with pytest.raises(TypeError):
        result.warnings[0].context["new"] = True
    with pytest.raises(FrozenInstanceError):
        # pyrefly: ignore [read-only] - exercise the runtime immutability boundary
        result.command = "changed"

    context = ExecutionContext(RunId(examples.RUN), examples.at("2026-07-24T20:00:00.000000Z"))
    envelope = result.envelope(context, completed_at=examples.at("2026-07-24T20:01:00.000000Z"))
    assert envelope.warnings[0].context == {"items": ["one"]}
    assert json.loads(envelope.to_json())["outcome"] == "success_with_warnings"
    assert envelope.to_json(indent=None) == result.envelope(
        context, completed_at=examples.at("2026-07-24T20:01:00.000000Z")
    ).to_json(indent=None)


def test_execution_identity_rejects_invalid_run_id_and_naive_time():
    with pytest.raises(ValueError, match="run id"):
        ExecutionContext(RunId("../escape"), examples.at("2026-07-24T20:00:00.000000Z"))
    with pytest.raises(ValueError, match="timezone-aware"):
        ExecutionContext(
            RunId(examples.RUN), examples.at("2026-07-24T20:00:00.000000Z").replace(tzinfo=None)
        )


def test_server_minted_correlation_is_independent_and_does_not_widen_schema1():
    first = ExecutionContext.new_request()
    second = ExecutionContext.new_request()
    operation_id = new_operation_id()
    identifiers = {first.run_id, first.request_id, second.run_id, second.request_id, operation_id}
    assert len(identifiers) == 5
    assert all(value is not None and len(value) == 32 for value in identifiers)
    payload = ServiceResult("version", {}).envelope(first).model_dump(mode="json")
    assert payload["run_id"] == first.run_id
    assert payload["schema_version"] == 1
    assert "request_id" not in payload
    assert "operation_id" not in payload
    with pytest.raises(ValueError, match="run id"):
        ExecutionContext.create(request_id="../untrusted-request")


def test_status_keeps_configuration_order_and_appends_unmanaged_inventory(queries):
    identity = _publication(queries)
    rows = queries.archive_status().data["repositories"]

    assert [item["repository_id"] for item in rows] == [
        "zeta/configured-first",
        "alpha/configured-second",
        identity.id,
    ]
    assert rows[0]["enabled"] is True
    assert rows[1]["enabled"] is False
    assert rows[2] | {"managed": False, "enabled": None, "requested_revision": None} == rows[2]
    assert rows[2]["current_commit_sha"] == examples.SHA
    assert rows[2]["retained_generations"] == [1]
    assert {item["upstream_state"] for item in rows} == {"unknown"}
    assert {item["verification_state"] for item in rows} == {"unverified"}


@pytest.mark.parametrize("method", ["archive_status", "list_repositories"])
def test_unmanaged_selectors_restrict_the_union(queries, method):
    identity = _publication(queries)
    result = getattr(queries, method)(RepositoryQuery(selectors=(identity.selector,)))

    assert [item["repository_id"] for item in result.data["repositories"]] == [identity.id]
    with pytest.raises(ConfigurationError) as caught:
        getattr(queries, method)(RepositoryQuery(selectors=("model:absent/repository",)))
    assert [problem.code for problem in caught.value.problems] == ["HFARG004"]


def test_list_remains_inventory_authoritative_when_catalog_is_corrupt(queries):
    identity = _publication(queries)
    queries.layout.catalog.mkdir(parents=True)
    (queries.layout.catalog / "repositories.json").write_text("broken", encoding="utf-8")
    (queries.layout.catalog / "verification.json").write_text("broken", encoding="utf-8")

    rows = queries.list_repositories(RepositoryQuery(revisions=True)).data["repositories"]

    assert [row["repository_id"] for row in rows] == [identity.id]
    assert rows[0]["managed"] is False
    assert rows[0]["revisions"][0]["publication_id"] == examples.PUBLICATION
    assert rows[0]["revisions"][0]["verification_state"] == "unverified"
    assert queries.list_repositories(RepositoryQuery(repository_type="dataset")).data == {
        "repositories": []
    }


def test_metadata_queries_take_no_lock_do_no_hub_work_and_write_nothing(queries, monkeypatch):
    _publication(queries)

    def forbidden(*args, **kwargs):
        pytest.fail("local metadata query attempted a credential, Hub, lock, or write operation")

    monkeypatch.setattr("hfcache.credentials.resolve_token", forbidden)
    monkeypatch.setattr("hfcache.hub.HubClient.of", forbidden)
    monkeypatch.setattr("hfcache.locking.exclusive_lock", forbidden)
    monkeypatch.setattr("hfcache.storage.write_model", forbidden)
    before = {path: path.read_bytes() for path in queries.layout.root.rglob("*") if path.is_file()}

    queries.version()
    queries.archive_status()
    queries.list_repositories(RepositoryQuery(revisions=True))
    queries.inspect_archive()
    estimate = queries.estimate_verification()
    validate_config(queries.config, token_source="none")

    assert estimate.exit_code == 0
    assert estimate.data["measured_throughput_bytes_per_second"] is None
    assert estimate.data["estimated_duration_seconds"] is None
    assert before == {
        path: path.read_bytes() for path in queries.layout.root.rglob("*") if path.is_file()
    }


def test_service_modules_and_read_protocol_have_no_transport_or_command_authority():
    root = Path(__file__).parents[2] / "src" / "hfcache" / "services"
    for path in root.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                assert not {item.name.split(".")[0] for item in node.names} & {
                    "typer",
                    "fastapi",
                    "fastmcp",
                }
            if isinstance(node, ast.ImportFrom):
                assert (node.module or "").split(".")[0] not in {"typer", "fastapi", "fastmcp"}
                assert node.module != "hfcache.cli"
                if path.name in {"queries.py", "context.py"}:
                    assert node.module not in {"hfcache.credentials", "hfcache.hub"}
    assert not {"synchronize", "repair_revision", "validate_config", "resolve_token"} & set(
        vars(MetadataQueries)
    )


@pytest.mark.parametrize("command", ["status", "list"])
def test_cli_query_envelopes_delegate_and_allow_unmanaged_selectors(
    queries, command, tmp_path_factory, monkeypatch
):
    identity = _publication(queries)
    capacity = MetadataReader(queries.layout.root).capacity()
    monkeypatch.setattr(MetadataReader, "capacity", lambda _self: capacity)
    # Daemon control state stays outside the archive it observes.
    path = tmp_path_factory.mktemp("query-cli") / "config.toml"
    path.write_text(
        f'schema_version = 1\n[storage]\narchive_root = "{queries.layout.root}"\n'
        f'archive_id = "{examples.ARCHIVE_ID}"\n',
        encoding="utf-8",
    )
    with api_cli(path) as remote:
        result = remote.invoke([command, identity.selector])

    assert result.exit_code == 0, result.output
    envelope = json.loads(result.stdout)
    direct = LocalQueries(
        ApplicationConfig.model_validate(
            {
                "schema_version": 1,
                "storage": {
                    "archive_root": str(queries.layout.root),
                    "archive_id": examples.ARCHIVE_ID,
                },
            }
        )
    )
    service = direct.archive_status() if command == "status" else direct.list_repositories()
    assert envelope["data"] == service.data
    assert envelope["schema_version"] == 1
    assert [row["managed"] for row in envelope["data"]["repositories"]] == [False]


def test_version_works_without_any_config_or_archive(queries, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("version read archive configuration")

    monkeypatch.setattr("hfcache.config.load_config", forbidden)
    assert set(query_version().data) == {
        "application",
        "huggingface_hub",
        "python",
        "transfer_backend",
    }


def test_validation_reports_only_nonsecret_credential_source(queries):
    result = validate_config(queries.config, token_source="disabled")
    assert result.data == {
        "config_fingerprint": queries.config.fingerprint(),
        "enabled_repositories": 1,
        "repositories": 2,
        "token_source": "disabled",
    }
