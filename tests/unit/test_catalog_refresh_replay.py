"""V27: keyed refresh observes its original result; a new key captures new curation."""

import socket
from dataclasses import asdict

import pytest

from hfcache.api.auth import CredentialClass, Principal
from hfcache.api.operations import OperationStore
from hfcache.api.runner import OperationRunner
from hfcache.catalog_storage import CatalogWriter, read_tag_snapshot
from hfcache.hub import HubClient
from hfcache.server_config import InstalledPolicy
from hfcache.services import commands
from hfcache.services.commands import CommandServices
from hfcache.services.requests import CatalogRefreshRequest
from tests.unit import test_synchronize as sync_fixtures
from tests.unit.test_synchronize import ARCHIVE_ID, MODEL

_local_lock = sync_fixtures._local_lock
config_file = sync_fixtures.config_file
layout = sync_fixtures.layout


def test_refresh_replay_preserves_exact_result_until_new_key(  # noqa: PLR0915 - one replay/new-capture lifecycle
    config_file, layout, tmp_path, monkeypatch
):
    original = config_file.read_text().replace(
        f'id = "{MODEL.id}"\n', f'id = "{MODEL.id}"\ntags = ["original"]\n'
    )
    config_file.write_text(original)
    policy = InstalledPolicy(config_file, layout.root, ARCHIVE_ID)
    first_policy = policy.snapshot()
    request = CatalogRefreshRequest(selectors=(MODEL.selector,), technical=False)
    executions = []
    writes = []
    original_write = CatalogWriter.write

    def denied(*_args, **_kwargs):
        pytest.fail("offline refresh attempted credentials, Hub access or network")

    def write(self, record, **kwargs):
        writes.append(record.kind)
        return original_write(self, record, **kwargs)

    def execute(snapshot, context):
        executions.append(snapshot)
        return CommandServices(
            snapshot.config, context, curation_source=lambda: policy.snapshot().config
        ).refresh_catalog(request)

    monkeypatch.setattr(commands, "resolve_token", denied)
    monkeypatch.setattr(HubClient, "of", denied)
    monkeypatch.setattr(socket, "create_connection", denied)
    monkeypatch.setattr(socket, "getaddrinfo", denied)
    monkeypatch.setattr(CatalogWriter, "write", write)
    with (
        OperationStore(tmp_path / "operation-state") as store,
        OperationRunner(store, policy) as runner,
    ):

        def submit(key):
            return runner.submit(
                Principal(CredentialClass.REST_WRITER),
                key,
                "/api/v1/catalog/refreshes",
                asdict(request),
                command="catalog refresh",
                execute=execute,
                wait_seconds=10,
            )

        first = submit("original-capture")
        first_result = runner.wait(first.receipt.operation_id, timeout=5)
        assert first.created
        assert first_result.exit_code == 0
        assert first_result.data["counts"]["snapshots_written"] == 1
        snapshot = read_tag_snapshot(layout, MODEL, ARCHIVE_ID)
        assert snapshot is not None
        assert snapshot.tags == ("original",)
        path = layout.repository(MODEL).tag_snapshot
        original_snapshot = path.read_bytes()
        assert len(executions) == 1
        assert writes == ["repository_tag_snapshot"]

        config_file.write_text(original.replace('tags = ["original"]', 'tags = ["changed"]'))
        changed_policy = policy.snapshot()
        assert changed_policy.fingerprint == first_policy.fingerprint
        assert changed_policy.config.curation_fingerprint() != snapshot.curation_fingerprint
        replay = submit("original-capture")
        replay_result = runner.wait(replay.receipt.operation_id, timeout=5)
        assert not replay.created
        assert replay.receipt.operation_id == first.receipt.operation_id
        assert replay_result.model_dump(mode="json") == first_result.model_dump(mode="json")
        assert path.read_bytes() == original_snapshot
        assert len(executions) == 1
        assert writes == ["repository_tag_snapshot"]

        refreshed = submit("new-capture")
        refreshed_result = runner.wait(refreshed.receipt.operation_id, timeout=5)
        assert refreshed.created
        assert refreshed.receipt.operation_id != first.receipt.operation_id
        assert refreshed_result.exit_code == 0
        current = read_tag_snapshot(layout, MODEL, ARCHIVE_ID)
        assert current is not None
        assert current.tags == ("changed",)
        assert current.curation_fingerprint == changed_policy.config.curation_fingerprint()
        assert refreshed_result.data["curation_fingerprint"] == current.curation_fingerprint
        assert path.read_bytes() != original_snapshot
        assert len(executions) == 2
        assert writes == ["repository_tag_snapshot", "repository_tag_snapshot"]
