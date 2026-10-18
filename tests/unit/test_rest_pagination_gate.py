"""REST gate: complete size-one walks over real mixed local metadata and history."""

import asyncio
from datetime import timedelta

import pytest

from hfcache.api.app import create_app
from hfcache.client import ApiClient
from hfcache.client_config import ClientConfig
from hfcache.client_errors import RemoteApiError
from hfcache.config import load_config
from hfcache.identity import CommitSha, PublicationId, RepositoryIdentity, RunId
from hfcache.server import build_server, listeners
from hfcache.services.queries import LocalQueries, RepositoryQuery
from tests.fixtures import examples
from tests.unit.test_api_reads import write_model
from tests.unit.test_server_bootstrap import (
    TOKEN,
    exercise,
    isolate_logging,  # noqa: F401 - autouse fixture
)
from tests.unit.test_server_bootstrap import policy as socket_policy  # noqa: F401 - fixture


@pytest.fixture
def policy(request):
    return request.getfixturevalue("socket_policy")


def published(queries, identity, number):
    repository = queries.layout.repository(identity)
    for generation in (1, 2):
        sha = CommitSha(f"{number * 10 + generation:040x}")
        publication = PublicationId(f"{number * 10 + generation:032x}")
        repository.instance(sha, publication).mkdir(parents=True)
        manifest = examples.manifest().model_copy(
            update={
                "repository_type": identity.type,
                "repository_id": identity.id,
                "commit_sha": sha,
                "publication_id": publication,
                "publication_generation": generation,
                "tree": str(repository.manifest_tree_field(sha, publication)),
            }
        )
        reference = examples.reference().model_copy(
            update={
                "repository_type": identity.type,
                "repository_id": identity.id,
                "commit_sha": sha,
                "publication_id": publication,
                "publication_generation": generation,
                "tree": str(repository.tree_reference(sha, publication)),
                "manifest": str(repository.manifest_reference(sha, publication)),
            }
        )
        write_model(repository.manifest(sha, publication), manifest)
        write_model(repository.revision_ref(sha), reference)
        write_model(repository.current_ref, reference)


def test_all_size_one_pages_match_local_truth_and_preserve_empty_unmanaged_and_exact_ids(  # noqa: PLR0915 - complete collection acceptance in one real lifespan
    policy, tmp_path
):
    configured = [
        RepositoryIdentity.of("dataset", "zeta/data"),
        RepositoryIdentity.of("model", "middle/empty"),
        RepositoryIdentity.of("model", "alpha/model"),
    ]
    with policy.archive_config.open("a") as stream:
        for identity in configured:
            stream.write(
                f'\n[[repositories]]\ntype="{identity.type}"\nid="{identity.id}"\nenabled=false\n'
            )
    config = load_config(policy.archive_config)
    queries = LocalQueries(config)
    write_model(queries.layout.sentinel, examples.sentinel())
    unmanaged = RepositoryIdentity.of("dataset", "orphan/data")
    for number, identity in enumerate((configured[0], configured[2], unmanaged), 1):
        published(queries, identity, number)
    queries.layout.repository(configured[1]).directory.mkdir(parents=True)
    for index in range(1, 5):
        original = examples.run_report()
        report = original.model_copy(
            update={
                "run_id": f"{index:032x}",
                "started_at": original.started_at + timedelta(seconds=index),
                "completed_at": original.completed_at + timedelta(seconds=index),
            }
        )
        write_model(queries.layout.run_report(report.started_at, RunId(report.run_id)), report)

    app = create_app(policy, instance_lock_path=tmp_path / "daemon.lock")
    server = build_server(app, policy)

    def read_all():  # noqa: PLR0915 - crosswalk all collection families and exact resource IDs
        principal = app.state.credentials.authenticate(f"Bearer {TOKEN}")
        # Fixture history is durable but deliberately not enqueued/executed.
        admitted = [
            app.state.operations.admit(
                principal,
                f"history-{index}",
                "/api/v1/plans",
                {},
                app.state.policy.snapshot,
            ).receipt
            for index in range(3)
        ]
        settings = ClientConfig(
            schema_version=1,
            api_socket=policy.listener.unix_socket,
            api_token_file=policy.credentials.writer.file,
            expected_archive_id=config.storage.archive_id,
            read_retries=0,
        )
        with ApiClient(settings) as client:

            def walk(path, field, expected, params=None):
                pages = list(client.iter_pages(path, field, {"limit": 1} | (params or {})))
                assert len(pages) == len(expected)
                assert all(len(page.envelope.data[field]) == 1 for page in pages)
                assert len({page.request_id for page in pages}) == len(pages)
                assert len({page.envelope.run_id for page in pages}) == len(pages)
                assert {page.archive_id for page in pages} == {config.storage.archive_id}
                assert len({page.config_fingerprint for page in pages}) == 1
                assert all(page.next_cursor is not None for page in pages[:-1])
                assert pages[-1].next_cursor is None
                rows = [row for page in pages for row in page.envelope.data[field]]
                assert rows == expected
                return rows

            status = queries.archive_status().data["repositories"]
            rows = walk("/api/v1/status", "repositories", status)
            assert [(row["repository_type"], row["repository_id"]) for row in rows] == [
                (identity.type, identity.id) for identity in (*configured, unmanaged)
            ]
            assert rows[1]["current_commit_sha"] is None
            assert rows[-1]["managed"] is False
            inventory = queries.list_repositories().data["repositories"]
            rows = walk("/api/v1/repositories", "repositories", inventory)
            empty = next(row for row in rows if row["repository_id"] == "middle/empty")
            assert empty["retained_revisions"] == 0
            full = queries.list_repositories(RepositoryQuery(revisions=True)).data["repositories"]
            revisions = [
                {
                    "repository_type": repository["repository_type"],
                    "repository_id": repository["repository_id"],
                    **revision,
                }
                for repository in full
                for revision in repository["revisions"]
            ]
            walk("/api/v1/repositories/revisions", "revisions", revisions)
            assert len(revisions) == 6
            for row in revisions:
                stem = "/api/v1/repositories/" + row["repository_type"] + "/" + row["repository_id"]
                manifest = client.read(
                    stem + "/manifests/" + row["commit_sha"] + "/" + row["publication_id"]
                ).envelope.data["manifest"]
                assert manifest["publication_id"] == row["publication_id"]
                assert manifest["commit_sha"] == row["commit_sha"]
                reference = client.read(stem + "/references/" + row["commit_sha"]).envelope.data[
                    "reference"
                ]
                assert reference["publication_id"] == row["publication_id"]
            run_ids = walk("/api/v1/runs", "runs", list(queries.list_reports()))
            for identifier in run_ids:
                report = client.read("/api/v1/runs/" + identifier)
                assert (
                    report.envelope.run_id == report.envelope.data["report"]["run_id"] == identifier
                )

            selectors = [configured[2].selector, configured[0].selector, unmanaged.selector]
            expected = queries.list_repositories(RepositoryQuery(tuple(selectors), "model")).data[
                "repositories"
            ]
            walk(
                "/api/v1/repositories",
                "repositories",
                expected,
                {"selector": selectors, "type": "model"},
            )
            pages = client.iter_pages("/api/v1/operations", "operations", {"limit": 1})
            first = next(pages)
            app.state.operations.transition(admitted[0].operation_id, "interrupted")
            remainder = list(pages)
            observed = [first, *remainder]
            rows = [row for page in observed for row in page.envelope.data["operations"]]
            assert [row["operation_id"] for row in rows] == [
                receipt.operation_id for receipt in app.state.operations.list()
            ]
            assert rows[-1]["state"] == "interrupted"
            assert len(rows) == len(admitted) == len(observed)
            assert observed[-1].next_cursor is None

            first = client.read("/api/v1/operations", {"limit": 1})
            app.state.operations.admit(
                principal, "new-membership", "/api/v1/plans", {}, app.state.policy.snapshot
            )
            with pytest.raises(RemoteApiError) as stale:
                client.read("/api/v1/operations", {"limit": 1, "cursor": first.next_cursor})
            assert stale.value.status_code == 409
            assert stale.value.problems[0].code == "HFAPI007"

    with listeners(policy.listener) as channels:

        async def request():
            await asyncio.to_thread(read_all)

        asyncio.run(exercise(server, channels, request))
