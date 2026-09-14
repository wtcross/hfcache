"""The sync run — plan §13.1 and §13.2, end to end against a fake Hub.

Everything here goes through `synchronize`, the same entry point the `sync`
command calls, against a `HubClient` whose `HubApi` is a directory of files this
test wrote. That is what makes a whole publication assertable without a network:
the seam plan §12 asks for is an interface this application defines, so a fake
that satisfies it exercises every line between resolution and the current
reference.

What is asserted is the *sequence's* properties rather than each step's — the
steps have their own tests. A second run of an unchanged repository downloads
nothing. A newly observed SHA leaves the older revision published. The current
reference always names a tree that exists. The run report describes what
happened.
"""

import fcntl
import json
import os
import shutil
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from threading import Event, Lock, Thread
from typing import TYPE_CHECKING, Any, override

import pytest
from typer.testing import CliRunner

import hfcache.purge as purge_module
from hfcache import sync as sync_module
from hfcache.archive import initialize_archive
from hfcache.cli import app
from hfcache.config import ApplicationConfig, load_config, validate_config_mapping
from hfcache.credentials import ResolvedToken, TokenSource
from hfcache.errors import (
    ExitCode,
    IntegrityError,
    RetentionError,
    SafetyError,
    SynchronizationError,
)
from hfcache.hub import HubClient
from hfcache.identity import CommitSha, RepositoryIdentity, new_run_id, new_transaction_id
from hfcache.locking import lock_path
from hfcache.manifests import RevisionManifest
from hfcache.paths import ArchiveLayout, RepositoryLayout
from hfcache.publication import published_repositories, read_reference, retained_references
from hfcache.reporting import RepositoriesCatalog, RunReport
from hfcache.retention import plan_prune
from hfcache.storage import parse_mount_table
from hfcache.sync import synchronize
from hfcache.transactions import open_transaction, read_journal

if TYPE_CHECKING:
    from collections.abc import Sequence

    from hfcache.identity import RunId
    from hfcache.transactions import Transaction

ARCHIVE_ID = "3f2a1c88-7b40-4a2e-9c1d-0e5b6a7f8d90"

MODEL = RepositoryIdentity.of("model", "organization/model-name")
DATASET = RepositoryIdentity.of("dataset", "organization/dataset-name")

SHA_A = "1111111111111111111111111111111111111111"
SHA_B = "2222222222222222222222222222222222222222"

CONTENT = {"config.json": b'{"model_type": "gpt2"}', "weights.bin": b"0" * 4096}


CONFIG = """
schema_version = 1

[storage]
archive_root = "{root}"
archive_id = "{archive_id}"
minimum_free_space_gib = {reserve_gib}
minimum_free_space_percent = 0
maximum_revisions = 5

[sync]
lock_wait_seconds = 0

[[repositories]]
id = "organization/model-name"
type = "model"

[[repositories]]
id = "organization/dataset-name"
type = "dataset"
"""


@dataclass
class Info:
    sha: str
    private: bool = False
    gated: bool = False
    last_modified: Any = None


@dataclass
class Entry:
    path: str
    size: int
    blob_id: str | None = None
    lfs: Any = None
    xet_hash: str | None = None


@dataclass
class DryRun:
    filename: str
    file_size: int
    will_download: bool


@dataclass
class FakeHub:
    """A Hub whose repositories are dictionaries, and whose cache is real.

    `snapshot_download` writes the content into the cache directory it is given
    with the layout the real one uses — a `blobs/` directory of content reached
    through symlinks from `snapshots/<sha>/`. Publication resolves those links
    and hardlinks the blobs, so the inode sharing this archive depends on is
    exercised rather than approximated.
    """

    revisions: dict[str, dict[str, bytes]] = field(default_factory=dict)
    heads: dict[str, str] = field(default_factory=dict)
    downloads: list[str] = field(default_factory=list)
    private: bool = False
    endpoint: str = "https://huggingface.co"

    def whoami(self, token: Any = None) -> dict:  # pragma: no cover - anonymous here
        return {"name": "anonymous"}

    def repo_info(self, repo_id: str, *, repo_type: str, revision: str, token: Any = None) -> Any:
        return Info(sha=self.heads[f"{repo_type}:{repo_id}"], private=self.private)

    def list_repo_tree(self, repo_id: str, **arguments: Any) -> Any:
        return [
            Entry(path=path, size=len(payload), blob_id="a" * 40)
            for path, payload in sorted(self.revisions[str(arguments["revision"])].items())
        ]

    def snapshot_download(  # noqa: PLR0913 - `HubApi`'s signature, not one chosen here
        self,
        repo_id: str,
        *,
        repo_type: str,
        revision: str,
        cache_dir: str,
        max_workers: int = 1,
        token: Any = None,
        dry_run: Any = False,
        local_files_only: bool = False,
    ) -> Any:
        root = Path(cache_dir) / f"{repo_type}s--{repo_id.replace('/', '--')}"
        snapshot = root / "snapshots" / revision
        files = self.revisions[revision]
        if dry_run:
            return [
                DryRun(filename=path, file_size=len(payload), will_download=not snapshot.exists())
                for path, payload in sorted(files.items())
            ]
        if not snapshot.exists():
            self.downloads.append(revision)
            for path, payload in files.items():
                blob = root / "blobs" / f"{revision}-{path.replace('/', '_')}"
                blob.parent.mkdir(parents=True, exist_ok=True)
                blob.write_bytes(payload)
                link = snapshot / path
                link.parent.mkdir(parents=True, exist_ok=True)
                link.symlink_to(blob)
        return str(snapshot)


@pytest.fixture
def hub() -> FakeHub:
    return FakeHub(
        revisions={SHA_A: dict(CONTENT), SHA_B: {**CONTENT, "extra.txt": b"a newer revision"}},
        heads={MODEL.selector: SHA_A, DATASET.selector: SHA_A},
    )


@pytest.fixture
def client(hub: FakeHub) -> HubClient:
    return HubClient(api=hub, token=ResolvedToken(source=TokenSource.NONE))


@pytest.fixture(autouse=True)
def _local_lock(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Take the lock somewhere this test user owns.

    `/run/hfcache` belongs to the service identity in production. The lock
    itself is real `flock(2)` either way — only where the file lives changes.
    """
    run_directory = tmp_path / "run"
    run_directory.mkdir()
    monkeypatch.setattr("hfcache.locking.LOCK_DIRECTORY", run_directory)


@pytest.fixture
def layout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> ArchiveLayout:
    """An initialized archive the application sees as a read/write NFSv4 mount.

    The substitution is the mount *table*, not the check: `storage` reads the
    real `/proc/self/mountinfo` in production and a file this test wrote here,
    so the same parsing and the same predicates run either way.
    """
    root = tmp_path / "archive"
    root.mkdir(mode=0o750)
    real = os.path.realpath(root)
    line = f"457 47 0:68 / {real} rw,relatime shared:488 - nfs4 nas:/x rw,vers=4.2\n"
    table = tmp_path / "mountinfo"
    table.write_text(line, encoding="utf-8")
    monkeypatch.setattr("hfcache.storage.MOUNT_TABLE", table)

    built = ArchiveLayout(root=root)
    initialize_archive(built, archive_id=ARCHIVE_ID, table=parse_mount_table(line))
    return built


@pytest.fixture
def config(tmp_path: Path, layout: ArchiveLayout) -> ApplicationConfig:
    path = tmp_path / "config.toml"
    path.write_text(
        CONFIG.format(root=layout.root, archive_id=ARCHIVE_ID, reserve_gib=0), encoding="utf-8"
    )
    return load_config(path)


def envelope(config: ApplicationConfig) -> dict[str, Any]:
    return {
        "application_version": "0.1.0",
        "archive_id": config.storage.archive_id,
        "config_fingerprint": config.fingerprint(),
        "hostname": "hfcachewriter.lab.example.com",
        "huggingface_hub_version": "1.24.0",
        "invocation_mode": "interactive",
        "python_version": "3.14.6",
    }


def run_transaction(layout: ArchiveLayout, config: ApplicationConfig, run_id: RunId) -> Transaction:
    """The §7.6 journal `cli._run` opens, with checkpoints 1-3 already recorded.

    The run transaction is the command's, not `synchronize`'s: `TX-07`
    reconciliation happens between checkpoints 2 and 3 and needs `recovery`,
    which imports this module's `repair` dependency. What is mirrored here is
    the *state* `synchronize` is handed — an open journal standing at
    `journals_reconciled` — so checkpoints 4-7 are recorded against exactly what
    production gives them.
    """
    transaction = open_transaction(
        layout,
        transaction_id=new_transaction_id(),
        operation="sync",
        run_id=run_id,
        archive_id=config.storage.archive_id,
        config_fingerprint=config.fingerprint(),
    )
    transaction.checkpoint("run_started", run_id=run_id)
    transaction.checkpoint("preflight_passed", checks=[])
    transaction.checkpoint("journals_reconciled", reconciled_transaction_ids=[])
    return transaction


def run(
    client: HubClient,
    layout: ArchiveLayout,
    config: ApplicationConfig,
    selected: Sequence[Any] | None = None,
):
    run_id = new_run_id()
    return synchronize(
        client,
        layout,
        config,
        run_transaction(layout, config, run_id),
        selected=selected if selected is not None else config.repositories,
        envelope=envelope(config),
        run_id=run_id,
        started_at=datetime.now(UTC),
    )


def statuses(outcome) -> dict[str, str]:
    return {f"{r.repository_type}:{r.repository_id}": r.status for r in outcome.report.repositories}


# --------------------------------------------------------------------------- #
# First sync
# --------------------------------------------------------------------------- #


def test_a_first_sync_publishes_every_enabled_repository(client, layout, config):
    outcome = run(client, layout, config)

    assert statuses(outcome) == {
        MODEL.selector: "published",
        DATASET.selector: "published",
    }
    assert outcome.exit_code == ExitCode.SUCCESS


def test_every_hub_path_appears_in_the_publication(client, layout, config):
    run(client, layout, config)

    reference = read_reference(layout, RepositoryLayout(archive=layout, identity=MODEL).current_ref)
    tree = layout.published / str(reference.tree)
    for path, payload in CONTENT.items():
        assert (tree / path).read_bytes() == payload


def test_the_published_file_shares_an_inode_with_the_cache_blob(client, layout, config):
    run(client, layout, config)

    reference = read_reference(layout, RepositoryLayout(archive=layout, identity=MODEL).current_ref)
    published = layout.published / str(reference.tree) / "weights.bin"
    assert published.stat().st_nlink >= 2


def test_the_run_report_is_durable_and_reads_back(client, layout, config):
    outcome = run(client, layout, config)

    assert outcome.report_path.is_relative_to(layout.runs)
    assert (
        RunReport.model_validate_json(outcome.report_path.read_text(encoding="utf-8"))
        == outcome.report
    )


def test_the_run_report_counts_what_was_moved(client, layout, config):
    outcome = run(client, layout, config)

    expected = sum(len(payload) for payload in CONTENT.values()) * 2
    assert outcome.report.totals.downloaded_bytes == expected
    assert outcome.report.totals.hashed_bytes == expected


def test_the_catalog_describes_both_repositories_as_managed(client, layout, config):
    # The persisted catalog, not a fresh rebuild: the run is what knows which
    # repositories are configured, so it is the run that has to record it.
    run(client, layout, config)

    catalog = RepositoriesCatalog.model_validate_json(
        layout.repositories_catalog.read_text(encoding="utf-8")
    )
    assert [entry.repository_id for entry in catalog.repositories] == [DATASET.id, MODEL.id]
    assert all(entry.managed for entry in catalog.repositories)
    assert all(entry.enabled for entry in catalog.repositories)


def test_repositories_are_processed_in_configuration_order(
    client, layout, config, monkeypatch: pytest.MonkeyPatch
):
    # Not selector order and not alphabetical: two runs naming the same
    # repositories must do the same things in the same sequence.
    reversed_selection = list(reversed(config.repositories))
    original_download = HubClient.download
    original_publish = sync_module.publish_revision
    download_order: list[RepositoryIdentity] = []
    publication_order: list[RepositoryIdentity] = []

    def observed_download(self, identity, commit_sha, *, cache_dir, max_workers):
        download_order.append(identity)
        return original_download(
            self,
            identity,
            commit_sha,
            cache_dir=cache_dir,
            max_workers=max_workers,
        )

    def observed_publish(*args, **kwargs):
        publication_order.append(kwargs["identity"])
        return original_publish(*args, **kwargs)

    monkeypatch.setattr(HubClient, "download", observed_download)
    monkeypatch.setattr(sync_module, "publish_revision", observed_publish)

    outcome = run(client, layout, config, selected=reversed_selection)

    # The *report* is sorted for readability; what matters is that both ran.
    assert len(outcome.report.repositories) == 2
    assert download_order == [MODEL, DATASET]
    assert publication_order == [MODEL, DATASET]


def test_download_prefetch_overlaps_hashing_with_one_four_worker_transfer(
    client, layout, config, monkeypatch: pytest.MonkeyPatch
):
    """Hash A while the sole producer downloads B, never two snapshots at once."""
    original_download = HubClient.download
    original_tree = HubClient.tree
    original_hash = sync_module.hash_snapshot
    original_capacity = sync_module.require_capacity
    first_tree_started = Event()
    second_download_entered = Event()
    second_download_completed = Event()
    counter_lock = Lock()
    active = 0
    peak = 0
    worker_budgets: list[int] = []
    capacity_needs: list[int] = []

    def observed_capacity(layout, storage, *, needed_bytes):
        capacity_needs.append(needed_bytes)
        return original_capacity(layout, storage, needed_bytes=needed_bytes)

    def observed_download(self, identity, commit_sha, *, cache_dir, max_workers):
        nonlocal active, peak
        with counter_lock:
            active += 1
            peak = max(peak, active)
            worker_budgets.append(max_workers)
        try:
            if identity == DATASET:
                second_download_entered.set()
                assert first_tree_started.wait(timeout=5), "main-thread tree read never started"
            downloaded = original_download(
                self,
                identity,
                commit_sha,
                cache_dir=cache_dir,
                max_workers=max_workers,
            )
            if identity == DATASET:
                second_download_completed.set()
            return downloaded
        finally:
            with counter_lock:
                active -= 1

    def observed_tree(self, identity, commit_sha):
        if identity == MODEL:
            assert second_download_entered.wait(timeout=5), "the producer did not run ahead"
            first_tree_started.set()
        return original_tree(self, identity, commit_sha)

    def waiting_hash(snapshot, tree, *, identity, known=None):
        if identity == MODEL:
            assert second_download_completed.wait(timeout=5), "the next download never overlapped"
        return original_hash(snapshot, tree, identity=identity, known=known)

    monkeypatch.setattr(HubClient, "download", observed_download)
    monkeypatch.setattr(HubClient, "tree", observed_tree)
    monkeypatch.setattr(sync_module, "hash_snapshot", waiting_hash)
    monkeypatch.setattr(sync_module, "require_capacity", observed_capacity)

    outcome = run(client, layout, config)

    assert outcome.exit_code == ExitCode.SUCCESS
    assert peak == 1
    assert worker_budgets == [4, 4]
    logical = sum(len(payload) for payload in CONTENT.values())
    assert capacity_needs == [logical * 2, logical, logical]


def test_queue_capacity_is_admitted_in_aggregate_before_any_transfer(
    client, layout, config, hub, monkeypatch: pytest.MonkeyPatch
):
    logical = sum(len(payload) for payload in CONTENT.values())
    requested: list[int] = []

    def aggregate_only(_layout, _storage, *, needed_bytes):
        requested.append(needed_bytes)
        if needed_bytes > logical:
            message = "the whole queue does not fit"
            raise SafetyError.single(message, code="HFMNT011")
        return []

    monkeypatch.setattr(sync_module, "require_capacity", aggregate_only)

    outcome = run(client, layout, config)

    assert requested == [logical * 2]
    assert hub.downloads == []
    assert set(statuses(outcome).values()) == {"failed"}
    assert all(result.errors == ("HFMNT011",) for result in outcome.report.repositories)


def test_aggregate_admission_includes_every_copy_publication(
    client, layout, tmp_path, hub, monkeypatch: pytest.MonkeyPatch
):
    path = tmp_path / "copy.toml"
    document = CONFIG.format(root=layout.root, archive_id=ARCHIVE_ID, reserve_gib=0).replace(
        "minimum_free_space_gib = 0",
        'publication_mode = "copy"\nminimum_free_space_gib = 0',
    )
    path.write_text(document, encoding="utf-8")
    copy_config = load_config(path)
    logical = sum(len(payload) for payload in CONTENT.values())
    requested: list[int] = []

    def refuse_aggregate(_layout, _storage, *, needed_bytes):
        requested.append(needed_bytes)
        message = "the copy queue does not fit"
        raise SafetyError.single(message, code="HFMNT011")

    monkeypatch.setattr(sync_module, "require_capacity", refuse_aggregate)

    outcome = run(client, layout, copy_config)

    # Two repositories, each needing one cache copy and one publication copy.
    assert requested == [logical * 4]
    assert hub.downloads == []
    assert set(statuses(outcome).values()) == {"failed"}


def test_copy_publication_rechecks_capacity_after_prefetch_before_staging_bytes(
    client, layout, tmp_path, hub, monkeypatch: pytest.MonkeyPatch
):
    path = tmp_path / "copy-recheck.toml"
    document = CONFIG.format(root=layout.root, archive_id=ARCHIVE_ID, reserve_gib=0).replace(
        "minimum_free_space_gib = 0",
        'publication_mode = "copy"\nminimum_free_space_gib = 0',
    )
    path.write_text(document, encoding="utf-8")
    copy_config = load_config(path)
    logical = sum(len(payload) for payload in CONTENT.values())
    requested: list[int] = []
    publications: list[RepositoryIdentity] = []
    original_publish = sync_module.publish_revision

    def changing_capacity(_layout, _storage, *, needed_bytes):
        requested.append(needed_bytes)
        if needed_bytes == logical:
            message = "copy headroom disappeared after prefetch"
            raise SafetyError.single(message, code="HFMNT011")
        return []

    def observed_publish(*args, **kwargs):
        publications.append(kwargs["identity"])
        return original_publish(*args, **kwargs)

    monkeypatch.setattr(sync_module, "require_capacity", changing_capacity)
    monkeypatch.setattr(sync_module, "publish_revision", observed_publish)

    outcome = run(client, layout, copy_config)

    assert requested[0] == logical * 4  # aggregate cache + copy publication admission
    assert requested.count(logical * 2) == 2  # one guarded transfer recheck per repository
    assert requested.count(logical) == 2  # immediate guarded copy checks
    assert len(hub.downloads) == 2
    assert publications == []
    assert set(statuses(outcome).values()) == {"failed"}
    assert all(result.errors == ("HFMNT011",) for result in outcome.report.repositories)
    assert list(layout.staging.iterdir()) == []


def test_copy_publication_and_prefetch_never_overlap_cache_allocation(  # noqa: PLR0915
    client, layout, tmp_path, monkeypatch: pytest.MonkeyPatch
):
    path = tmp_path / "copy-serialized.toml"
    document = CONFIG.format(root=layout.root, archive_id=ARCHIVE_ID, reserve_gib=0).replace(
        "minimum_free_space_gib = 0",
        'publication_mode = "copy"\nminimum_free_space_gib = 0',
    )
    path.write_text(document, encoding="utf-8")
    copy_config = load_config(path)
    original_download = HubClient.download
    original_hash = sync_module.hash_snapshot
    original_publish = sync_module.publish_revision
    model_hash_finished = Event()
    dataset_download_active = Event()
    release_download = Event()
    publication_entered = Event()
    counter_lock = Lock()
    active_allocators = 0
    peak_allocators = 0

    def enter_allocator() -> None:
        nonlocal active_allocators, peak_allocators
        with counter_lock:
            active_allocators += 1
            peak_allocators = max(peak_allocators, active_allocators)

    def leave_allocator() -> None:
        nonlocal active_allocators
        with counter_lock:
            active_allocators -= 1

    def held_download(self, identity, commit_sha, *, cache_dir, max_workers):
        enter_allocator()
        try:
            if identity == DATASET:
                assert model_hash_finished.wait(timeout=5)
                dataset_download_active.set()
                assert release_download.wait(timeout=5)
            return original_download(
                self,
                identity,
                commit_sha,
                cache_dir=cache_dir,
                max_workers=max_workers,
            )
        finally:
            leave_allocator()

    def observed_hash(snapshot, tree, *, identity, known=None):
        hashed = original_hash(snapshot, tree, identity=identity, known=known)
        if identity == MODEL:
            model_hash_finished.set()
            assert dataset_download_active.wait(timeout=5)
        return hashed

    def observed_publish(*args, **kwargs):
        publication_entered.set()
        enter_allocator()
        try:
            return original_publish(*args, **kwargs)
        finally:
            leave_allocator()

    monkeypatch.setattr(HubClient, "download", held_download)
    monkeypatch.setattr(sync_module, "hash_snapshot", observed_hash)
    monkeypatch.setattr(sync_module, "publish_revision", observed_publish)
    outcomes: list[Any] = []
    failures: list[BaseException] = []

    def execute() -> None:
        try:
            outcomes.append(run(client, layout, copy_config))
        except BaseException as error:  # noqa: BLE001 - transfer a thread failure to pytest
            failures.append(error)

    worker = Thread(target=execute, daemon=True)
    worker.start()
    assert dataset_download_active.wait(timeout=5)
    assert not publication_entered.wait(timeout=0.2)
    release_download.set()
    worker.join(timeout=10)

    assert not worker.is_alive()
    assert failures == []
    assert len(outcomes) == 1
    assert outcomes[0].exit_code == ExitCode.SUCCESS
    assert peak_allocators == 1


def test_same_sha_prefetch_is_consumed_before_any_global_retention(
    client, layout, config, monkeypatch: pytest.MonkeyPatch
):
    """Pruning A cannot remove the complete same-SHA snapshot queued for B."""
    published: list[RepositoryIdentity] = []
    retained: list[RepositoryIdentity] = []
    original_publish = sync_module.publish_revision

    def observed_publish(*args, **kwargs):
        identity = kwargs["identity"]
        outcome = original_publish(*args, **kwargs)
        published.append(identity)
        return outcome

    def globally_delete_commit(cache_layout, identity, _config, *, run_id):
        del run_id
        assert published == [MODEL, DATASET]
        retained.append(identity)
        for snapshot in cache_layout.hub_cache.glob(f"*/snapshots/{SHA_A}"):
            shutil.rmtree(snapshot)

    monkeypatch.setattr(sync_module, "publish_revision", observed_publish)
    monkeypatch.setattr(sync_module, "_apply_retention", globally_delete_commit)

    outcome = run(client, layout, config)

    assert statuses(outcome) == {MODEL.selector: "published", DATASET.selector: "published"}
    assert retained == [MODEL, DATASET]
    assert list(layout.hub_cache.glob(f"*/snapshots/{SHA_A}")) == []
    for identity in (MODEL, DATASET):
        reference = read_reference(
            layout, RepositoryLayout(archive=layout, identity=identity).current_ref
        )
        assert (layout.published / str(reference.tree) / "weights.bin").read_bytes() == CONTENT[
            "weights.bin"
        ]


def test_a_deferred_prune_failure_reports_failure_but_keeps_the_publication(
    client, layout, config, monkeypatch: pytest.MonkeyPatch
):
    def fail_model_prune(_layout, identity, _config, *, run_id):
        del run_id
        if identity == MODEL:
            message = "the deferred prune stopped"
            raise RetentionError.single(message, code="HFRET002")

    monkeypatch.setattr(sync_module, "_apply_retention", fail_model_prune)

    outcome = run(client, layout, config)

    assert outcome.exit_code == ExitCode.RETENTION
    assert statuses(outcome) == {MODEL.selector: "failed", DATASET.selector: "published"}
    model = next(
        result for result in outcome.report.repositories if result.repository_id == MODEL.id
    )
    logical = sum(len(payload) for payload in CONTENT.values())
    assert model.errors == ("HFRET002",)
    assert model.downloaded_bytes == logical
    assert model.hashed_bytes == logical
    assert model.publication_id is not None
    assert model.publication_generation == 1
    assert model.resolved_commit_sha == SHA_A
    assert model.pruned is None
    assert RepositoryLayout(archive=layout, identity=MODEL).current_ref.is_file()


def test_a_disabled_repository_is_reported_rather_than_omitted(client, layout, tmp_path):
    path = tmp_path / "disabled.toml"
    path.write_text(
        CONFIG.format(root=tmp_path / "archive", archive_id=ARCHIVE_ID, reserve_gib=0).replace(
            'id = "organization/dataset-name"\ntype = "dataset"',
            'id = "organization/dataset-name"\ntype = "dataset"\nenabled = false',
        ),
        encoding="utf-8",
    )
    configuration = load_config(path)

    outcome = run(client, ArchiveLayout(root=configuration.storage.archive_root), configuration)

    assert statuses(outcome)[DATASET.selector] == "disabled"
    assert statuses(outcome)[MODEL.selector] == "published"


# --------------------------------------------------------------------------- #
# Second sync
# --------------------------------------------------------------------------- #


def test_a_second_sync_of_an_unchanged_repository_downloads_nothing(client, layout, config, hub):
    run(client, layout, config)
    hub.downloads.clear()

    outcome = run(client, layout, config)

    assert hub.downloads == []
    assert set(statuses(outcome).values()) == {"skipped"}
    assert outcome.report.totals.downloaded_bytes == 0


def test_a_second_sync_leaves_the_current_reference_alone(client, layout, config):
    first = run(client, layout, config)
    reference = read_reference(layout, RepositoryLayout(archive=layout, identity=MODEL).current_ref)

    run(client, layout, config)

    after = read_reference(layout, RepositoryLayout(archive=layout, identity=MODEL).current_ref)
    assert after.publication_id == reference.publication_id
    assert first.report.repositories[0].publication_generation == 1


def test_a_newly_observed_sha_publishes_and_keeps_the_older_revision(client, layout, config, hub):
    run(client, layout, config)
    hub.heads[MODEL.selector] = SHA_B

    outcome = run(client, layout, config)

    assert statuses(outcome)[MODEL.selector] == "published"
    references = retained_references(layout, MODEL)
    assert [reference.commit_sha for reference in references] == [SHA_A, SHA_B]
    assert [reference.publication_generation for reference in references] == [1, 2]


def test_the_current_reference_follows_the_newly_observed_sha(client, layout, config, hub):
    run(client, layout, config)
    hub.heads[MODEL.selector] = SHA_B

    run(client, layout, config)

    repository = RepositoryLayout(archive=layout, identity=MODEL)
    reference = read_reference(layout, repository.current_ref)
    assert reference.commit_sha == SHA_B
    assert (layout.published / str(reference.tree) / "extra.txt").is_file()


def test_returning_to_a_retained_sha_moves_the_reference_without_downloading(
    client, layout, config, hub
):
    # Upstream moved back to something the archive already holds: no bytes
    # fetched, but consumers are now pointed elsewhere, which is a change worth
    # seeing in a run report.
    run(client, layout, config)
    hub.heads[MODEL.selector] = SHA_B
    run(client, layout, config)
    hub.downloads.clear()
    hub.heads[MODEL.selector] = SHA_A

    outcome = run(client, layout, config)

    assert hub.downloads == []
    assert statuses(outcome)[MODEL.selector] == "ref_moved_to_retained_revision"
    repository = RepositoryLayout(archive=layout, identity=MODEL)
    assert read_reference(layout, repository.current_ref).commit_sha == SHA_A


def test_re_observing_a_sha_does_not_reorder_retention(client, layout, config, hub):
    # §15.1: re-observing an existing SHA makes no duplicate and does not
    # change the generation it already holds.
    run(client, layout, config)
    hub.heads[MODEL.selector] = SHA_B
    run(client, layout, config)
    hub.heads[MODEL.selector] = SHA_A
    run(client, layout, config)

    references = retained_references(layout, MODEL)
    assert [(r.commit_sha, r.publication_generation) for r in references] == [
        (SHA_A, 1),
        (SHA_B, 2),
    ]


def test_the_second_run_reuses_the_digest_of_an_unchanged_object(client, layout, config, hub):
    # §16.1's only permitted cross-run reuse: the same inode at the same size,
    # named against the retained publication the digest came from.
    run(client, layout, config)
    hub.heads[MODEL.selector] = SHA_B

    run(client, layout, config)

    repository = RepositoryLayout(archive=layout, identity=MODEL)
    reference = read_reference(layout, repository.current_ref)
    manifest = RevisionManifest.model_validate_json(
        (layout.published / str(reference.manifest)).read_text(encoding="utf-8")
    )
    # `extra.txt` is new; the rest are the same blobs SHA_A published.
    assert manifest.verification.reused_digests == 0
    assert manifest.verification.hashed_objects == len(manifest.files)


def test_the_current_reference_always_names_a_tree_that_exists(client, layout, config, hub):
    # `FS-10`, over a sequence of runs rather than at one write.
    for head in (SHA_A, SHA_B, SHA_A, SHA_B):
        hub.heads[MODEL.selector] = head
        run(client, layout, config)
        repository = RepositoryLayout(archive=layout, identity=MODEL)
        reference = read_reference(layout, repository.current_ref)
        assert (layout.published / str(reference.tree)).is_dir()
        assert (layout.published / str(reference.manifest)).is_file()


# --------------------------------------------------------------------------- #
# Failure inside one repository
# --------------------------------------------------------------------------- #


def test_a_repository_that_fails_is_recorded_and_the_run_continues(client, layout, config, hub):
    # `AD-06`: a failure means the run learned nothing new about this
    # repository, never that what it already holds is suspect.
    del hub.heads[MODEL.selector]

    outcome = run(client, layout, config)

    assert statuses(outcome)[MODEL.selector] == "failed"
    assert statuses(outcome)[DATASET.selector] == "published"


def test_an_estimate_failure_stays_with_its_repository_and_queues_later_work(
    client, layout, config, monkeypatch: pytest.MonkeyPatch
):
    original = HubClient.estimate

    def refuse_first(self, identity, commit_sha, *, cache_dir, max_workers):
        if identity == MODEL:
            message = "model estimate failed"
            raise SynchronizationError.single(message, code="HFHUB009")
        return original(
            self,
            identity,
            commit_sha,
            cache_dir=cache_dir,
            max_workers=max_workers,
        )

    monkeypatch.setattr(HubClient, "estimate", refuse_first)

    outcome = run(client, layout, config)

    assert statuses(outcome) == {MODEL.selector: "failed", DATASET.selector: "published"}
    failed = next(
        result for result in outcome.report.repositories if result.repository_id == MODEL.id
    )
    assert failed.errors == ("HFHUB009",)


def test_a_prefetch_download_failure_does_not_abandon_the_remaining_queue(
    client, layout, config, monkeypatch: pytest.MonkeyPatch
):
    original = HubClient.download

    def refuse_first(self, identity, commit_sha, *, cache_dir, max_workers):
        if identity == MODEL:
            message = "model transfer failed"
            raise SynchronizationError.single(message, code="HFHUB009")
        return original(
            self,
            identity,
            commit_sha,
            cache_dir=cache_dir,
            max_workers=max_workers,
        )

    monkeypatch.setattr(HubClient, "download", refuse_first)

    outcome = run(client, layout, config)

    assert statuses(outcome) == {MODEL.selector: "failed", DATASET.selector: "published"}
    failed = next(result for result in outcome.report.repositories if result.status == "failed")
    assert failed.errors == ("HFHUB009",)
    assert list(layout.staging.iterdir()) == []


def test_an_interrupt_finishes_the_active_download_and_cancels_the_pending_queue(
    client, layout, tmp_path, hub, monkeypatch: pytest.MonkeyPatch
):
    third = RepositoryIdentity.of("model", "organization/third-model")
    path = tmp_path / "three-repositories.toml"
    path.write_text(
        CONFIG.format(root=layout.root, archive_id=ARCHIVE_ID, reserve_gib=0)
        + '\n[[repositories]]\nid = "organization/third-model"\ntype = "model"\n',
        encoding="utf-8",
    )
    three_repositories = load_config(path)
    hub.heads[third.selector] = SHA_A
    original_download = HubClient.download
    second_started = Event()
    release_second = Event()
    seen: list[RepositoryIdentity] = []
    shutdown_calls: list[tuple[bool, bool]] = []

    def held_download(self, identity, commit_sha, *, cache_dir, max_workers):
        seen.append(identity)
        if identity == DATASET:
            second_started.set()
            assert release_second.wait(timeout=5), "interrupt shutdown did not release the writer"
        return original_download(
            self,
            identity,
            commit_sha,
            cache_dir=cache_dir,
            max_workers=max_workers,
        )

    class ObservedExecutor(ThreadPoolExecutor):
        @override
        def shutdown(self, wait: bool = True, *, cancel_futures: bool = False) -> None:
            shutdown_calls.append((wait, cancel_futures))
            if cancel_futures:
                # Cancel the third future while the second is deterministically
                # active, then let that sole cache writer complete and join it.
                super().shutdown(wait=False, cancel_futures=True)
                release_second.set()
                if wait:
                    super().shutdown(wait=True)
                return
            super().shutdown(wait=wait)

    def interrupt_hash(_snapshot, _tree, *, identity, known=None):
        del identity, known
        assert second_started.wait(timeout=5), "the next transfer never became active"
        raise KeyboardInterrupt

    monkeypatch.setattr(HubClient, "download", held_download)
    monkeypatch.setattr(sync_module, "ThreadPoolExecutor", ObservedExecutor)
    monkeypatch.setattr(sync_module, "hash_snapshot", interrupt_hash)

    with pytest.raises(KeyboardInterrupt):
        run(client, layout, three_repositories)

    assert shutdown_calls == [(True, True)]
    assert seen == [MODEL, DATASET]


def test_a_download_completed_before_hash_failure_is_counted_in_the_report(
    client, layout, config, monkeypatch: pytest.MonkeyPatch
):
    original = sync_module.hash_snapshot
    logical = sum(len(payload) for payload in CONTENT.values())

    def refuse_model_hash(snapshot, tree, *, identity, known=None):
        if identity == MODEL:
            message = "model hash failed"
            raise SynchronizationError.single(message, code="HFSYN009")
        return original(snapshot, tree, identity=identity, known=known)

    monkeypatch.setattr(sync_module, "hash_snapshot", refuse_model_hash)

    outcome = run(client, layout, config)

    failed = next(result for result in outcome.report.repositories if result.status == "failed")
    assert failed.repository_id == MODEL.id
    assert failed.downloaded_bytes == logical
    assert failed.resolved_commit_sha == SHA_A
    assert outcome.report.totals.downloaded_bytes == logical * 2
    assert statuses(outcome)[DATASET.selector] == "published"
    assert list(layout.staging.iterdir()) == []


def test_a_failed_transaction_is_closed_as_failed(client, layout, config, hub):
    # The journal has to say what happened: an open journal blocks the next run
    # (`TX-07`), and a run that failed for a reason the archive already knows
    # should not need an operator.
    hub.revisions[SHA_A] = dict(CONTENT)

    def refuse_download(self, identity, commit_sha, *, cache_dir, max_workers):
        message = "the Hub went away mid-download"
        raise SynchronizationError.single(message, code="HFHUB009")

    original = HubClient.download
    try:
        HubClient.download = refuse_download
        outcome = run(client, layout, config)
    finally:
        HubClient.download = original

    assert set(statuses(outcome).values()) == {"failed"}
    journals = [
        read_journal(layout, path).journal for path in sorted(layout.transactions.glob("*.json"))
    ]
    publications = [journal for journal in journals if journal.operation == "publication"]
    assert publications
    for journal in publications:
        assert journal.state == "failed"
    # The *run* committed. Every repository failed and the run reports it, but
    # the run transaction itself did all seven of its own steps — which is the
    # difference §7.6 draws between a run that failed and a run that finished
    # with failures in it.
    assert [journal.state for journal in journals if journal.operation == "sync"] == ["committed"]


def test_a_run_that_may_not_continue_stops_at_the_first_failure(client, layout, tmp_path, hub):
    path = tmp_path / "strict.toml"
    path.write_text(
        CONFIG.format(root=layout.root, archive_id=ARCHIVE_ID, reserve_gib=0).replace(
            "lock_wait_seconds = 0",
            "lock_wait_seconds = 0\ncontinue_on_repository_error = false",
        ),
        encoding="utf-8",
    )
    strict = load_config(path)
    del hub.heads[MODEL.selector]

    outcome = run(client, layout, strict)

    # The dataset is never reached, so it has no entry at all.
    assert list(statuses(outcome)) == [MODEL.selector]


def test_strict_mode_never_prefetches_after_a_late_repository_failure(
    client, layout, tmp_path, monkeypatch: pytest.MonkeyPatch
):
    path = tmp_path / "strict-hash.toml"
    path.write_text(
        CONFIG.format(root=layout.root, archive_id=ARCHIVE_ID, reserve_gib=0).replace(
            "lock_wait_seconds = 0",
            "lock_wait_seconds = 0\ncontinue_on_repository_error = false",
        ),
        encoding="utf-8",
    )
    strict = load_config(path)
    original_download = HubClient.download
    seen: list[RepositoryIdentity] = []

    def observed_download(self, identity, commit_sha, *, cache_dir, max_workers):
        seen.append(identity)
        return original_download(
            self,
            identity,
            commit_sha,
            cache_dir=cache_dir,
            max_workers=max_workers,
        )

    def refuse_hash(_snapshot, _tree, *, identity, known=None):
        message = f"{identity.selector} hash failed"
        raise SynchronizationError.single(message, code="HFSYN009")

    monkeypatch.setattr(HubClient, "download", observed_download)
    monkeypatch.setattr(sync_module, "hash_snapshot", refuse_hash)

    outcome = run(client, layout, strict)

    assert seen == [MODEL]
    assert list(statuses(outcome)) == [MODEL.selector]


def test_a_download_the_archive_has_no_room_for_is_refused_before_it_starts(
    client, layout, tmp_path
):
    # Plan §13.2 step 4: the repository that would have overflowed is the one
    # that reports it, before the transfer rather than after.
    path = tmp_path / "reserved.toml"
    path.write_text(
        CONFIG.format(root=layout.root, archive_id=ARCHIVE_ID, reserve_gib=1_000_000),
        encoding="utf-8",
    )

    outcome = run(client, layout, load_config(path))

    assert set(statuses(outcome).values()) == {"failed"}
    assert outcome.report.repositories[0].errors == ("HFMNT011",)
    # Nothing was published.
    assert not RepositoryLayout(archive=layout, identity=MODEL).current_ref.exists()


def test_a_snapshot_missing_a_listed_file_fails_completeness(client, layout, config, hub):
    original = FakeHub.snapshot_download

    def truncated(self, repo_id, **arguments):
        result = original(self, repo_id, **arguments)
        if not arguments.get("dry_run"):
            (Path(result) / "config.json").unlink(missing_ok=True)
        return result

    try:
        FakeHub.snapshot_download = truncated
        outcome = run(client, layout, config)
    finally:
        FakeHub.snapshot_download = original

    assert set(statuses(outcome).values()) == {"failed"}
    assert "HFSYN002" in outcome.report.repositories[0].errors


# --------------------------------------------------------------------------- #
# The `sync` command (`docs/cli.md` §2)
# --------------------------------------------------------------------------- #


@pytest.fixture
def config_file(tmp_path: Path, layout: ArchiveLayout) -> Path:
    path = tmp_path / "config.toml"
    path.write_text(
        CONFIG.format(root=layout.root, archive_id=ARCHIVE_ID, reserve_gib=0), encoding="utf-8"
    )
    return path


@pytest.fixture
def _wired(hub: FakeHub, monkeypatch: pytest.MonkeyPatch) -> None:
    """Point the command's real `HubClient.of` at the fake, and nothing else."""

    def of(cls, token, *, endpoint):
        return cls(api=hub, token=token, endpoint=endpoint)

    monkeypatch.setattr(HubClient, "of", classmethod(of))
    monkeypatch.setattr("hfcache.preflight.resolve_host", lambda _host: ("192.0.2.1",))
    monkeypatch.setattr("hfcache.preflight.verify_tls", lambda _host: "TLSv1.3")


@pytest.mark.usefixtures("_wired")
def test_the_sync_command_publishes_and_exits_zero(config_file: Path):
    result = CliRunner().invoke(app, ["--json", "--config", str(config_file), "sync"])

    assert result.exit_code == ExitCode.SUCCESS
    payload = json.loads(result.stdout)["data"]
    assert {entry["status"] for entry in payload["repositories"]} == {"published"}
    assert payload["report"].startswith("runs/")


@pytest.mark.usefixtures("_wired")
def test_required_token_syncs_private_repositories(config_file: Path, tmp_path: Path, hub: FakeHub):
    config_file.write_text(
        config_file.read_text(encoding="utf-8").replace(
            "[storage]", '[hub]\ntoken_mode = "required"\n\n[storage]'
        ),
        encoding="utf-8",
    )
    token = tmp_path / "token"
    token.write_text("hf_privateRepositoryCredential\n", encoding="utf-8")
    hub.private = True

    result = CliRunner().invoke(
        app,
        ["--json", "--config", str(config_file), "--token-file", str(token), "sync"],
    )

    assert result.exit_code == ExitCode.SUCCESS
    payload = json.loads(result.stdout)["data"]
    assert {entry["status"] for entry in payload["repositories"]} == {"published"}


@pytest.mark.usefixtures("_wired")
def test_sync_refuses_a_mismatched_expected_account(config_file: Path, hub: FakeHub):
    config_file.write_text(
        config_file.read_text(encoding="utf-8").replace(
            "[storage]", '[hub]\nexpected_account = "intended-account"\n\n[storage]'
        ),
        encoding="utf-8",
    )

    result = CliRunner().invoke(app, ["--json", "--config", str(config_file), "sync"])

    assert result.exit_code == ExitCode.SYNC
    assert json.loads(result.stdout)["errors"][0]["code"] == "HFHUB003"
    assert hub.downloads == []


@pytest.mark.usefixtures("_wired")
def test_the_sync_command_takes_the_exclusive_lock(config_file: Path, layout: ArchiveLayout):
    # Held for the whole run rather than per repository: proving the archive
    # sound and then letting another command mutate it would prove nothing.
    held = os.open(lock_path(), os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
        result = CliRunner().invoke(app, ["--json", "--config", str(config_file), "sync"])
    finally:
        os.close(held)

    assert result.exit_code == ExitCode.SAFETY
    assert [error["code"] for error in json.loads(result.stdout)["errors"]] == ["HFMNT010"]


@pytest.mark.usefixtures("_wired")
def test_the_sync_command_restricts_a_run_to_its_selectors(config_file: Path):
    result = CliRunner().invoke(
        app, ["--json", "--config", str(config_file), "sync", "model:organization/model-name"]
    )

    payload = json.loads(result.stdout)["data"]
    assert [entry["repository_id"] for entry in payload["repositories"]] == [
        "organization/model-name"
    ]


@pytest.mark.usefixtures("_wired")
def test_the_sync_command_prints_one_line_per_repository(config_file: Path):
    result = CliRunner().invoke(app, ["--config", str(config_file), "sync"])

    assert "model:organization/model-name  published" in result.output
    assert "dataset:organization/dataset-name  published" in result.output


@pytest.mark.usefixtures("_wired")
def test_the_sync_command_exits_thirty_when_a_repository_failed(config_file: Path, hub: FakeHub):
    del hub.heads[MODEL.selector]

    result = CliRunner().invoke(app, ["--json", "--config", str(config_file), "sync"])

    assert result.exit_code == ExitCode.SYNC
    assert json.loads(result.stdout)["outcome"] == "failed"


def test_the_sync_command_refuses_an_unmounted_archive(tmp_path: Path):
    # Exit `20` before any Hub request (plan §19), which is what keeps a missing
    # NAS from filling the writer's root filesystem.
    path = tmp_path / "absent.toml"
    path.write_text(
        CONFIG.format(root="/nonexistent/archive/root", archive_id=ARCHIVE_ID, reserve_gib=0),
        encoding="utf-8",
    )

    result = CliRunner().invoke(app, ["--json", "--config", str(path), "sync"])

    assert result.exit_code == ExitCode.SAFETY


@pytest.mark.usefixtures("_wired")
def test_a_run_that_clears_the_reserve_only_narrowly_warns_and_still_publishes(
    client, layout, tmp_path
):
    # `HFWRN005` is "close to the reserve", not "over it"; a run that can still
    # complete should (`docs/cli.md` §5.6), and the warning is durable.
    total = os.statvfs(layout.root).f_frsize * os.statvfs(layout.root).f_blocks
    available = os.statvfs(layout.root).f_frsize * os.statvfs(layout.root).f_bavail
    path = tmp_path / "narrow.toml"
    # A reserve just under what is free: the run fits, but only just.
    path.write_text(
        CONFIG.format(
            root=layout.root,
            archive_id=ARCHIVE_ID,
            reserve_gib=max(1, int(available / (1024**3)) - 1),
        ),
        encoding="utf-8",
    )
    assert total > 0

    outcome = run(client, layout, load_config(path))

    assert set(statuses(outcome).values()) == {"completed_with_warnings"}
    assert outcome.report.warnings == ("HFWRN005",)
    assert outcome.report.outcome == "success_with_warnings"
    assert outcome.exit_code == ExitCode.SUCCESS


def test_the_sync_command_reports_a_configuration_problem_as_exit_ten(tmp_path: Path):
    result = CliRunner().invoke(app, ["--json", "--config", str(tmp_path / "absent.toml"), "sync"])

    assert result.exit_code == ExitCode.CONFIGURATION


@pytest.mark.usefixtures("_wired")
def test_the_sync_command_prints_each_failure_on_stderr(config_file: Path, hub: FakeHub):
    del hub.heads[MODEL.selector]

    result = CliRunner().invoke(app, ["--config", str(config_file), "sync"])

    assert "model:organization/model-name  failed" in result.output
    assert "HFHUB001" in result.output or "HFSYN" in result.output


@pytest.mark.usefixtures("_wired")
def test_quiet_suppresses_the_per_repository_lines(config_file: Path):
    # `--quiet` suppresses informational output; the durable run report is still
    # written, which is where an unattended run's evidence belongs. Asserted
    # against `output` rather than `stdout`, so it also covers the §24 event log:
    # quiet raises that to WARNING, and a clean run has nothing at that level.
    result = CliRunner().invoke(app, ["--quiet", "--config", str(config_file), "sync"])

    assert result.exit_code == ExitCode.SUCCESS
    assert result.output.strip() == ""


@pytest.mark.usefixtures("_wired")
def test_a_run_leaves_the_plan_section_24_event_trail_on_stderr(config_file: Path):
    """The whole point of `OBS-002`: a scheduled run is legible from the journal.

    Asserted as a *sequence* rather than a set, because the order is what makes
    the trail readable — a reader following one repository sees it resolved,
    downloaded, and published in that order, and can tell a run that stopped
    part way from one that never started.
    """
    result = CliRunner().invoke(app, ["--config", str(config_file), "sync"])

    assert result.exit_code == ExitCode.SUCCESS
    lines = [line for line in result.stderr.splitlines() if line.startswith("event=")]
    events = [line.split(" ", 1)[0].removeprefix("event=") for line in lines]
    assert events[0] == "run.started"
    assert events[-1] == "run.completed"

    # Publication and the next download deliberately overlap, so their global
    # interleaving is scheduler-dependent.  Each repository's causal sequence
    # remains fixed and readable.
    for identity in (MODEL, DATASET):
        per_repository = [
            line.split(" ", 1)[0].removeprefix("event=")
            for line in lines
            if f"repository={identity.selector}" in line
        ]
        assert per_repository == [
            "repository.resolved",
            "repository.queued",
            "download.started",
            "download.completed",
            "hash.started",
            "hash.completed",
            "publication.completed",
        ]

    completed = next(line for line in lines if line.startswith("event=hash.completed"))
    assert "hashed_objects=" in completed
    assert "hashed_bytes=" in completed
    assert "reused_digests=" in completed


@pytest.mark.usefixtures("_wired")
def test_every_event_in_a_run_carries_the_report_s_run_id(config_file: Path):
    # The join §24 exists to make possible: one identifier across the envelope on
    # stdout, the lines on stderr, and `runs/<…>.json` on the archive.
    result = CliRunner().invoke(app, ["--json", "--config", str(config_file), "sync"])

    run_id = json.loads(result.stdout)["run_id"]
    emitted = [line for line in result.stderr.splitlines() if line.startswith("event=")]
    assert emitted
    # `run.started` onwards; the preflight lines above it predate the run id and
    # deliberately carry the startup one instead.
    assert all(f"run_id={run_id}" in line for line in emitted)


@pytest.mark.usefixtures("_wired")
def test_a_failing_repository_says_so_in_the_event_trail(config_file: Path, hub: FakeHub):
    del hub.heads[MODEL.selector]

    result = CliRunner().invoke(app, ["--config", str(config_file), "sync"])

    failed = [
        line for line in result.stderr.splitlines() if line.startswith("event=repository.fai")
    ]
    assert len(failed) == 1
    assert "repository=model:organization/model-name" in failed[0]
    assert "level=error" in failed[0]


# --------------------------------------------------------------------------- #
# The §7.6 run transaction and `TX-07` reconciliation
# --------------------------------------------------------------------------- #


def sync_journals(layout: ArchiveLayout):
    """Every run journal the archive holds, oldest first."""
    return [
        journal
        for journal in (
            read_journal(layout, path).journal
            for path in sorted(layout.transactions.glob("*.json"))
        )
        if journal.operation == "sync"
    ]


@pytest.mark.usefixtures("_wired")
def test_the_run_records_every_documented_checkpoint_in_order(config_file: Path, layout):
    result = CliRunner().invoke(app, ["--config", str(config_file), "sync"])

    assert result.exit_code == ExitCode.SUCCESS
    (journal,) = sync_journals(layout)
    assert [checkpoint.name for checkpoint in journal.checkpoints] == [
        "run_started",
        "preflight_passed",
        "journals_reconciled",
        "repositories_processed",
        "catalog_rebuilt",
        "run_report_written",
        "run_completed",
    ]
    assert journal.state == "committed"


def test_a_failure_before_the_rename_leaves_no_staging_behind(client, layout, config, hub):
    """A journal closed `failed` is resolved, so recovery never looks at it. If
    the failed publication left its staging behind, nothing would ever reclaim it
    and `status` would report a finished-and-failed run as outstanding work
    forever — decision 56's problem in the failure path."""

    def refuse(*_arguments, **_keywords):
        message = "the snapshot could not be assembled"
        raise SynchronizationError.single(message, code="HFSYN001")

    original = HubClient.verify_local
    try:
        HubClient.verify_local = refuse
        outcome = run(client, layout, config)
    finally:
        HubClient.verify_local = original

    assert set(statuses(outcome).values()) == {"failed"}
    assert list(layout.staging.iterdir()) == []


def test_a_failure_after_the_rename_keeps_its_staged_manifest(client, layout, config, hub):
    """The other side of the same rule. Past checkpoint 5 a tree is published and
    the staged manifest is the only thing that can validate it (§7.3), so it is
    preserved — a resolved journal in that state is something an operator has to
    look at, and deleting the evidence first would be the wrong help."""
    original = sync_module.publish_revision_reference

    def refuse(*_arguments, **_keywords):
        message = "the reference could not be published"
        raise SynchronizationError.single(message, code="HFSYN007")

    try:
        sync_module.publish_revision_reference = refuse
        outcome = run(client, layout, config)
    finally:
        sync_module.publish_revision_reference = original

    assert set(statuses(outcome).values()) == {"failed"}
    staged = sorted(layout.staging.rglob("manifest.json"))
    assert staged, "the staged manifest is the only thing that can validate the published tree"


@pytest.mark.usefixtures("_wired")
def test_a_completed_run_leaves_nothing_reading_as_unfinished(config_file: Path, layout):
    """Decision 56, from the place an operator sees it. `status` reads
    `.store/staging` to count unfinished transactions, so a successful run that
    left staging behind would report finished work as outstanding — and after
    `stale_staging_age_hours` would warn `HFWRN004` about it."""
    result = CliRunner().invoke(app, ["--json", "--config", str(config_file), "sync"])

    assert result.exit_code == ExitCode.SUCCESS
    assert list(layout.staging.iterdir()) == []
    status = CliRunner().invoke(app, ["--json", "--config", str(config_file), "status"])
    archive = json.loads(status.stdout)["data"]["archive"]
    assert archive["unfinished_transactions"] == 0
    assert archive["findings"] == []


@pytest.mark.usefixtures("_wired")
def test_the_run_journal_carries_the_evidence_each_checkpoint_names(config_file: Path, layout):
    CliRunner().invoke(app, ["--config", str(config_file), "sync"])

    (journal,) = sync_journals(layout)
    evidence = {checkpoint.name: checkpoint.evidence for checkpoint in journal.checkpoints}
    assert evidence["run_started"]["archive_id"] == ARCHIVE_ID
    assert [check["outcome"] for check in evidence["preflight_passed"]["checks"]]
    assert evidence["journals_reconciled"] == {
        "pending_transaction_ids": [],
        "reconciled_transaction_ids": [],
    }
    assert evidence["repositories_processed"]["statuses"] == {
        DATASET.selector: "published",
        MODEL.selector: "published",
    }
    assert evidence["catalog_rebuilt"]["catalog_path"] == "published/catalog/repositories.json"
    assert evidence["run_report_written"]["run_report_path"].startswith("runs/")
    assert evidence["run_completed"] == {"exit_code": 0, "outcome": "success"}


@pytest.mark.usefixtures("_wired")
def test_the_run_journal_never_reconciles_itself(config_file: Path, layout):
    """`TX-01` opens it before the run may act, so it is unfinished throughout.

    Without the exclusion the run would find its own journal, propose
    `close_journal` for work still executing, and close it under itself.
    """
    CliRunner().invoke(app, ["--config", str(config_file), "sync"])

    (journal,) = sync_journals(layout)
    reconciled = journal.checkpoints[2].evidence
    assert journal.transaction_id not in reconciled["reconciled_transaction_ids"]
    assert len(journal.checkpoints) == 7


@pytest.mark.usefixtures("_wired")
def test_a_run_finishes_what_the_previous_run_left_unfinished(config_file: Path, layout, hub):
    """`TX-07`: the reconciliation is real work, not a formality."""
    abandoned = new_transaction_id()
    open_transaction(
        layout,
        transaction_id=abandoned,
        operation="publication",
        run_id=new_run_id(),
        archive_id=ARCHIVE_ID,
        config_fingerprint="0" * 64,
        repository_id=MODEL.id,
        repository_type=MODEL.type,
    ).checkpoint("staging_created", staging_path=f".store/staging/{abandoned}")
    (layout.staging / abandoned).mkdir(parents=True)
    os.utime(layout.staging / abandoned, (0, 0))

    result = CliRunner().invoke(app, ["--config", str(config_file), "sync"])

    assert result.exit_code == ExitCode.SUCCESS
    (journal,) = sync_journals(layout)
    reconciled = journal.checkpoints[2].evidence
    assert reconciled["reconciled_transaction_ids"] == [abandoned]
    # The report the reconciliation wrote is named, so an operator reading the
    # run journal can follow it (`recovery_report` carries no `_path` suffix
    # because it belongs to the recovery transaction, not to this one).
    assert reconciled["recovery_report"].startswith("runs/")
    assert list(layout.quarantine.iterdir()), "the abandoned staging is preserved"


@pytest.mark.usefixtures("_wired")
def test_a_journal_that_asked_for_an_operator_stops_the_run_before_the_hub(
    config_file: Path, layout, hub
):
    """§7.9, and the whole reason `TX-07` is a rule: an unattended run must not
    download into an archive whose last run stopped somewhere nobody looked."""
    stopped = new_transaction_id()
    transaction = open_transaction(
        layout,
        transaction_id=stopped,
        operation="publication",
        run_id=new_run_id(),
        archive_id=ARCHIVE_ID,
        config_fingerprint="0" * 64,
        repository_id=MODEL.id,
        repository_type=MODEL.type,
    )
    transaction.needs_operator("HFTXN004", "two equally valid resolutions")

    result = CliRunner().invoke(app, ["--json", "--config", str(config_file), "sync"])

    assert result.exit_code == ExitCode.SAFETY
    assert [error["code"] for error in json.loads(result.stdout)["errors"]] == ["HFTXN004"]
    assert hub.downloads == [], "not one byte was fetched"
    # The run closed its own journal rather than leaving a second unfinished one
    # behind, and the journal that stopped it is untouched.
    (run_journal,) = sync_journals(layout)
    assert run_journal.state == "failed"
    assert [checkpoint.name for checkpoint in run_journal.checkpoints] == [
        "run_started",
        "preflight_passed",
    ]
    assert read_journal(layout, layout.journal(stopped)).journal.state == "needs_operator"


@pytest.mark.usefixtures("_wired")
def test_a_run_that_cannot_write_its_report_closes_its_journal_as_failed(
    config_file: Path, layout, monkeypatch
):
    def refuse(*_arguments, **_keywords):
        message = "the run report could not be written"
        raise SynchronizationError.single(message, code="HFSYN008")

    monkeypatch.setattr("hfcache.sync.write_model", refuse)

    result = CliRunner().invoke(app, ["--json", "--config", str(config_file), "sync"])

    assert result.exit_code == ExitCode.SYNC
    (journal,) = sync_journals(layout)
    assert journal.state == "failed"
    assert journal.error is not None
    assert journal.error.code == "HFSYN008"


# --------------------------------------------------------------------------- #
# Aggregate reporting (`docs/cli.md` §3)
# --------------------------------------------------------------------------- #


def test_the_run_report_aggregates_every_code_encountered(client, layout, config, hub):
    # Aggregation hides nothing: the single number a scheduler sees is one
    # decision, and every code is still listed.
    del hub.heads[MODEL.selector]
    del hub.heads[DATASET.selector]

    outcome = run(client, layout, config)

    assert outcome.exit_code == ExitCode.SYNC
    assert outcome.report.errors
    assert outcome.report.outcome == "failed"
    assert outcome.report.exit_code == int(ExitCode.SYNC)


def test_integrity_outranks_synchronization_in_the_reported_exit(client, layout, config, hub):
    # `docs/cli.md` §3's order is operator urgency: possible corruption first.
    del hub.heads[MODEL.selector]
    original = HubClient.verify_local

    def integrity_failure(self, identity, commit_sha, *, cache_dir):
        message = "a manifest is unusable"
        raise IntegrityError.single(message, code="HFVER007")

    try:
        HubClient.verify_local = integrity_failure
        outcome = run(client, layout, config)
    finally:
        HubClient.verify_local = original

    # A `KeyError` from the fake's head lookup is a transport failure to the
    # adapter, which is the honest classification for "the Hub did not answer".
    assert set(outcome.report.errors) == {"HFHUB001", "HFVER007"}
    assert outcome.exit_code == ExitCode.INTEGRITY


def test_a_clean_run_reports_no_errors_and_exits_zero(client, layout, config):
    outcome = run(client, layout, config)

    assert outcome.report.errors == ()
    assert outcome.report.outcome == "success"
    assert outcome.exit_code == ExitCode.SUCCESS


# --------------------------------------------------------------------------- #
# `status` and `list` over what a run produced
# --------------------------------------------------------------------------- #


@pytest.mark.usefixtures("_wired")
def test_status_reports_retained_and_current_state(config_file: Path):
    CliRunner().invoke(app, ["--config", str(config_file), "sync"])

    result = CliRunner().invoke(app, ["--json", "--config", str(config_file), "status"])

    entries = {
        f"{e['repository_type']}:{e['repository_id']}": e
        for e in json.loads(result.stdout)["data"]["repositories"]
    }
    assert entries[MODEL.selector]["retained_revisions"] == 1
    assert entries[MODEL.selector]["current_commit_sha"] == SHA_A
    assert entries[MODEL.selector]["retained_generations"] == [1]
    assert entries[MODEL.selector]["last_run_status"] == "published"


@pytest.mark.usefixtures("_wired")
def test_status_answers_for_a_repository_that_was_never_synced(config_file: Path):
    # A configured repository with nothing archived yet is a normal state.
    result = CliRunner().invoke(app, ["--json", "--config", str(config_file), "status"])

    entry = json.loads(result.stdout)["data"]["repositories"][0]
    assert result.exit_code == ExitCode.SUCCESS
    assert entry["retained_revisions"] == 0
    assert entry["current_commit_sha"] is None
    assert entry["last_run_status"] is None


@pytest.mark.usefixtures("_wired")
def test_status_never_contacts_the_hub(config_file: Path, hub: FakeHub):
    # It must answer when the Hub is unreachable, so it does not resolve.
    hub.heads.clear()

    result = CliRunner().invoke(app, ["--json", "--config", str(config_file), "status"])

    assert result.exit_code == ExitCode.SUCCESS
    assert {e["upstream_state"] for e in json.loads(result.stdout)["data"]["repositories"]} == {
        "unknown"
    }


@pytest.mark.usefixtures("_wired")
def test_list_reads_manifests_and_references_not_the_catalog(config_file: Path, layout):
    CliRunner().invoke(app, ["--config", str(config_file), "sync"])
    # The catalog is derived and can be missing (`FS-16`); `list` answers anyway.
    layout.repositories_catalog.unlink()

    result = CliRunner().invoke(app, ["--json", "--config", str(config_file), "list"])

    entries = json.loads(result.stdout)["data"]["repositories"]
    assert result.exit_code == ExitCode.SUCCESS
    assert {e["repository_id"] for e in entries} == {MODEL.id, DATASET.id}
    assert all(e["retained_revisions"] == 1 for e in entries)
    assert all(e["current_commit_sha"] == SHA_A for e in entries)


@pytest.mark.usefixtures("_wired")
def test_list_revisions_describes_each_retained_revision(config_file: Path, hub: FakeHub):
    CliRunner().invoke(app, ["--config", str(config_file), "sync"])
    hub.heads[MODEL.selector] = SHA_B
    CliRunner().invoke(app, ["--config", str(config_file), "sync"])

    result = CliRunner().invoke(
        app, ["--json", "--config", str(config_file), "list", "--revisions"]
    )

    entries = {e["repository_id"]: e for e in json.loads(result.stdout)["data"]["repositories"]}
    revisions = entries[MODEL.id]["revisions"]
    assert [r["commit_sha"] for r in revisions] == [SHA_A, SHA_B]
    assert [r["publication_generation"] for r in revisions] == [1, 2]
    assert all(r["total_bytes"] > 0 and r["file_count"] > 0 for r in revisions)


@pytest.mark.usefixtures("_wired")
def test_list_restricts_to_one_repository_type(config_file: Path):
    CliRunner().invoke(app, ["--config", str(config_file), "sync"])

    result = CliRunner().invoke(
        app, ["--json", "--config", str(config_file), "list", "--type", "dataset"]
    )

    entries = json.loads(result.stdout)["data"]["repositories"]
    assert [e["repository_id"] for e in entries] == [DATASET.id]


@pytest.mark.usefixtures("_wired")
def test_list_restricts_to_its_selectors(config_file: Path):
    CliRunner().invoke(app, ["--config", str(config_file), "sync"])

    result = CliRunner().invoke(
        app, ["--json", "--config", str(config_file), "list", "model:organization/model-name"]
    )

    entries = json.loads(result.stdout)["data"]["repositories"]
    assert [e["repository_id"] for e in entries] == [MODEL.id]


def test_list_refuses_a_type_that_is_not_a_repository_type(config_file: Path):
    result = CliRunner().invoke(
        app, ["--json", "--config", str(config_file), "list", "--type", "space"]
    )

    assert result.exit_code == ExitCode.CONFIGURATION
    assert [error["code"] for error in json.loads(result.stdout)["errors"]] == ["HFARG002"]


@pytest.mark.usefixtures("_wired")
def test_list_prints_one_line_per_repository(config_file: Path):
    CliRunner().invoke(app, ["--config", str(config_file), "sync"])

    result = CliRunner().invoke(app, ["--config", str(config_file), "list"])

    assert "1 revisions" in result.output
    assert SHA_A in result.output


def test_list_answers_for_an_archive_with_nothing_published(config_file: Path):
    result = CliRunner().invoke(app, ["--json", "--config", str(config_file), "list"])

    assert result.exit_code == ExitCode.SUCCESS
    assert json.loads(result.stdout)["data"]["repositories"] == []


@pytest.mark.usefixtures("_wired")
def test_status_answers_over_a_damaged_reference(config_file: Path, layout):
    # `status` is the command an operator runs first, so it answers even when
    # part of the archive is unreadable rather than failing with it.
    CliRunner().invoke(app, ["--config", str(config_file), "sync"])
    repository = RepositoryLayout(archive=layout, identity=MODEL)
    repository.current_ref.write_text("{ not json", encoding="utf-8")

    result = CliRunner().invoke(app, ["--json", "--config", str(config_file), "status"])

    entries = {
        f"{e['repository_type']}:{e['repository_id']}": e
        for e in json.loads(result.stdout)["data"]["repositories"]
    }
    assert result.exit_code == ExitCode.SUCCESS
    assert entries[MODEL.selector]["current_commit_sha"] is None
    # The undamaged repository still reports fully.
    assert entries[DATASET.selector]["current_commit_sha"] == SHA_A


@pytest.mark.usefixtures("_wired")
def test_status_skips_a_run_report_it_cannot_read(config_file: Path, layout):
    # Informational rather than authoritative: the references above it are the
    # archive's truth, so a damaged report costs one field and not the command.
    CliRunner().invoke(app, ["--config", str(config_file), "sync"])
    for report in layout.runs.glob("*.json"):
        report.write_text("{ not json", encoding="utf-8")

    result = CliRunner().invoke(app, ["--json", "--config", str(config_file), "status"])

    entries = json.loads(result.stdout)["data"]["repositories"]
    assert result.exit_code == ExitCode.SUCCESS
    assert {entry["last_run_status"] for entry in entries} == {None}
    assert entries[0]["retained_revisions"] == 1


def test_status_reports_no_last_run_when_the_archive_is_absent(tmp_path: Path):
    path = tmp_path / "absent.toml"
    path.write_text(
        CONFIG.format(root="/nonexistent/archive/root", archive_id=ARCHIVE_ID, reserve_gib=0),
        encoding="utf-8",
    )

    result = CliRunner().invoke(app, ["--json", "--config", str(path), "status"])

    entries = json.loads(result.stdout)["data"]["repositories"]
    assert result.exit_code == ExitCode.SUCCESS
    assert {entry["last_run_status"] for entry in entries} == {None}
    assert {entry["retained_revisions"] for entry in entries} == {0}


# --------------------------------------------------------------------------- #
# Retention (plan §15, `docs/architecture.md` §7.4)
# --------------------------------------------------------------------------- #


def heads_through(client, layout, config, hub, count: int) -> list[str]:
    """Publish `count` unique revisions of the model, oldest first."""
    published = []
    for index in range(count):
        commit = f"{index + 1:040d}"
        hub.revisions[commit] = {**CONTENT, "generation.txt": str(index).encode()}
        hub.heads[MODEL.selector] = commit
        run(client, layout, config)
        published.append(commit)
    return published


def test_five_revisions_are_kept_unchanged(client, layout, config, hub):
    published = heads_through(client, layout, config, hub, 5)

    references = retained_references(layout, MODEL)
    assert [reference.commit_sha for reference in references] == published
    assert [reference.publication_generation for reference in references] == [1, 2, 3, 4, 5]


def test_default_retention_keeps_three_and_a_fourth_removes_the_oldest(client, layout, config, hub):
    """RET-010: omission adopts three while explicit five remains compatible."""
    mapping = config.model_dump(mode="json")
    del mapping["storage"]["maximum_revisions"]
    default_config = validate_config_mapping(mapping)
    published = heads_through(client, layout, default_config, hub, 3)
    assert [r.commit_sha for r in retained_references(layout, MODEL)] == published

    fourth = f"{4:040d}"
    hub.revisions[fourth] = {**CONTENT, "generation.txt": b"3"}
    hub.heads[MODEL.selector] = fourth
    run(client, layout, default_config)

    retained = retained_references(layout, MODEL)
    assert [r.commit_sha for r in retained] == [*published[1:], fourth]
    assert [r.publication_generation for r in retained] == [2, 3, 4]
    repository = RepositoryLayout(archive=layout, identity=MODEL)
    assert read_reference(layout, repository.current_ref).commit_sha == fourth
    assert not repository.revision(CommitSha(published[0])).exists()


def test_a_sixth_revision_removes_the_oldest(client, layout, config, hub):
    published = heads_through(client, layout, config, hub, 6)

    references = retained_references(layout, MODEL)
    assert [reference.commit_sha for reference in references] == published[1:]
    assert len(references) == 5
    # The generation is retired, never reissued (`FS-20`).
    assert [reference.publication_generation for reference in references] == [2, 3, 4, 5, 6]


def test_the_pruned_tree_and_reference_are_gone(client, layout, config, hub):
    published = heads_through(client, layout, config, hub, 6)

    repository = RepositoryLayout(archive=layout, identity=MODEL)
    assert not repository.revision_ref(CommitSha(published[0])).exists()
    assert not any(repository.revision(CommitSha(published[0])).glob("*"))


def test_a_prune_leaves_no_empty_container_behind(client, layout, config, hub):
    """`RET-008`: §7.4 tombstones the instance and its manifest, one level below
    their SHA directories. Both containers go too, or the consumer-visible tree
    accumulates one pair per pruned SHA forever."""
    published = heads_through(client, layout, config, hub, 6)

    repository = RepositoryLayout(archive=layout, identity=MODEL)
    pruned = CommitSha(published[0])
    assert not repository.revision(pruned).exists(), "revisions/<sha>/ survived the prune"
    assert not repository.revision_manifests(pruned).exists(), "manifests/<sha>/ survived"
    # The five that remain are untouched, which is the thing an over-eager
    # cleanup would break.
    for commit in published[1:]:
        assert repository.revision(CommitSha(commit)).is_dir()
        assert repository.revision_manifests(CommitSha(commit)).is_dir()


def test_a_pruned_sha_that_returns_is_republished_into_a_fresh_container(
    client, layout, config, hub
):
    """The container is removed, so a later re-observation has to recreate it.

    This is not hypothetical: it is what the live archive did on 2026-07-26, when
    a pruned dataset SHA was re-synced and became generation 7 (decision 62).
    """
    published = heads_through(client, layout, config, hub, 6)
    repository = RepositoryLayout(archive=layout, identity=MODEL)
    pruned = CommitSha(published[0])
    assert not repository.revision(pruned).exists()

    hub.heads[MODEL.selector] = str(pruned)
    run(client, layout, config)

    assert repository.revision(pruned).is_dir(), "the returning SHA rebuilt its container"
    reference = read_reference(layout, repository.revision_ref(pruned))
    assert reference.commit_sha == str(pruned)
    # A new generation, because the old one was retired and is never reissued.
    assert reference.publication_generation == 7


def test_the_pruned_revision_leaves_durable_evidence(client, layout, config, hub):
    # The manifest byte for byte plus a provenance record: together they prove
    # what was there and why it went (`docs/schemas.md` §9.1).
    published = heads_through(client, layout, config, hub, 6)

    repository = RepositoryLayout(archive=layout, identity=MODEL)
    audit = repository.pruned_records(CommitSha(published[0]))
    assert sorted(path.name.split(".", 1)[1] for path in audit.iterdir()) == [
        "manifest.json",
        "prune.json",
    ]


def test_the_current_revision_survives_the_prune(client, layout, config, hub):
    published = heads_through(client, layout, config, hub, 6)

    repository = RepositoryLayout(archive=layout, identity=MODEL)
    reference = read_reference(layout, repository.current_ref)
    assert reference.commit_sha == published[5]
    assert (layout.published / str(reference.tree)).is_dir()


def test_the_prune_is_reported_in_the_run_that_caused_it(client, layout, config, hub):
    heads_through(client, layout, config, hub, 5)
    hub.revisions["6" * 40] = {**CONTENT, "generation.txt": b"5"}
    hub.heads[MODEL.selector] = "6" * 40

    outcome = run(client, layout, config)

    result = next(r for r in outcome.report.repositories if r.repository_id == MODEL.id)
    assert result.pruned is not None
    assert result.pruned.publication_generation == 1


def test_no_trash_survives_a_completed_prune(client, layout, config, hub):
    heads_through(client, layout, config, hub, 6)

    assert list(layout.trash.iterdir()) == []


def test_the_prune_journal_records_every_checkpoint_in_order(client, layout, config, hub):
    heads_through(client, layout, config, hub, 6)

    prunes = [
        read_journal(layout, path).journal
        for path in sorted(layout.transactions.glob("*.json"))
        if read_journal(layout, path).journal.operation == "prune"
    ]
    assert len(prunes) == 1
    assert [checkpoint.name for checkpoint in prunes[0].checkpoints] == [
        "plan_persisted",
        "cache_revision_deleted",
        "revision_ref_removed",
        "tree_tombstoned",
        "manifest_tombstoned",
        "catalog_published",
        "prune_logically_committed",
        "audit_record_written",
        "trash_removed",
        "containers_removed",
        "prune_completed",
    ]
    assert prunes[0].state == "committed"


def test_a_repository_below_the_limit_never_prunes(client, layout, config, hub):
    heads_through(client, layout, config, hub, 3)

    prunes = [
        path
        for path in layout.transactions.glob("*.json")
        if read_journal(layout, path).journal.operation == "prune"
    ]
    assert prunes == []


def test_the_catalog_reflects_the_five_that_remain(client, layout, config, hub):
    published = heads_through(client, layout, config, hub, 6)

    catalog = RepositoriesCatalog.model_validate_json(
        layout.repositories_catalog.read_text(encoding="utf-8")
    )
    entry = next(e for e in catalog.repositories if e.repository_id == MODEL.id)
    assert [revision.commit_sha for revision in entry.revisions] == published[1:]


def test_a_repository_with_no_current_reference_is_never_pruned(client, layout, config, hub):
    # A repository whose first publication has not completed: pruning it would
    # remove a revision while consumers have nothing to be pointed at.
    heads_through(client, layout, config, hub, 6)
    RepositoryLayout(archive=layout, identity=MODEL).current_ref.unlink()

    assert plan_prune(layout, MODEL, maximum=1, generated_at=datetime.now(UTC)) is None


def test_a_cache_deletion_failure_is_hfret002(client, layout, config, hub, monkeypatch):
    # Published hardlinks keep the bytes regardless, so the revision is
    # preserved and the run reports the failure rather than losing data.
    heads_through(client, layout, config, hub, 5)

    def refuse(cache_dir, commit_sha):
        message = "the cache is unreadable"
        raise OSError(message)

    monkeypatch.setattr("huggingface_hub.scan_cache_dir", refuse)
    hub.revisions["6" * 40] = {**CONTENT, "generation.txt": b"5"}
    hub.heads[MODEL.selector] = "6" * 40

    outcome = run(client, layout, config)

    result = next(r for r in outcome.report.repositories if r.repository_id == MODEL.id)
    assert result.status == "failed"
    assert result.errors == ("HFRET002",)
    # Nothing was removed: six revisions remain, which is the preferred outcome.
    assert len(retained_references(layout, MODEL)) == 6


# --------------------------------------------------------------------------- #
# The `prune` command (`docs/cli.md` §2)
# --------------------------------------------------------------------------- #


@pytest.mark.usefixtures("_wired")
def test_prune_dry_run_reports_the_plan_and_mutates_nothing(config_file: Path, layout, hub):
    for index in range(6):
        commit = f"{index + 1:040d}"
        hub.revisions[commit] = {**CONTENT, "generation.txt": str(index).encode()}
        hub.heads[MODEL.selector] = commit
        hub.heads[DATASET.selector] = commit
        CliRunner().invoke(app, ["--config", str(config_file), "sync"])
    # `sync` already pruned to five; a further plan needs a lower maximum, so
    # this asserts the *shape* of a dry run rather than forcing a second prune.
    before = {reference.commit_sha for reference in retained_references(layout, MODEL)}

    result = CliRunner().invoke(app, ["--json", "--config", str(config_file), "prune", "--dry-run"])

    assert result.exit_code == ExitCode.SUCCESS
    assert json.loads(result.stdout)["data"]["plans"] == []
    assert {r.commit_sha for r in retained_references(layout, MODEL)} == before


@pytest.mark.usefixtures("_wired")
def test_prune_dry_run_describes_the_revision_it_would_remove(config_file: Path, layout, hub):
    for index in range(6):
        commit = f"{index + 1:040d}"
        hub.revisions[commit] = {**CONTENT, "generation.txt": str(index).encode()}
        hub.heads[MODEL.selector] = commit
        CliRunner().invoke(app, ["--config", str(config_file), "sync"])
    # Lower the limit so a plan exists to describe.
    lowered = config_file.parent / "lowered.toml"
    lowered.write_text(
        config_file.read_text(encoding="utf-8").replace(
            "maximum_revisions = 5", "maximum_revisions = 3"
        ),
        encoding="utf-8",
    )

    result = CliRunner().invoke(app, ["--json", "--config", str(lowered), "prune", "--dry-run"])

    assert result.exit_code == ExitCode.SUCCESS
    plans = json.loads(result.stdout)["data"]["plans"]
    assert len(plans) == 1
    assert plans[0]["selected"]["publication_generation"] == 2
    assert len(retained_references(layout, MODEL)) == 5

    # One reviewed invocation removes one revision per repository (§7.4).
    for generation, remaining in [(2, 4), (3, 3)]:
        result = CliRunner().invoke(
            app, ["--json", "--config", str(lowered), "prune", "--apply", MODEL.selector]
        )
        assert result.exit_code == ExitCode.SUCCESS
        applied = json.loads(result.stdout)["data"]["applied"]
        assert len(applied) == 1
        assert applied[0]["publication_generation"] == generation
        assert len(retained_references(layout, MODEL)) == remaining

    retained = retained_references(layout, MODEL)
    assert [r.publication_generation for r in retained] == [4, 5, 6]
    repository = RepositoryLayout(archive=layout, identity=MODEL)
    assert read_reference(layout, repository.current_ref).publication_generation == 6
    result = CliRunner().invoke(app, ["--json", "--config", str(lowered), "prune", "--dry-run"])
    assert json.loads(result.stdout)["data"]["plans"] == []


@pytest.mark.usefixtures("_wired")
def test_prune_requires_exactly_one_mode(config_file: Path):
    both = CliRunner().invoke(
        app, ["--json", "--config", str(config_file), "prune", "--dry-run", "--apply"]
    )
    neither = CliRunner().invoke(app, ["--json", "--config", str(config_file), "prune"])

    for result in (both, neither):
        assert result.exit_code == ExitCode.CONFIGURATION
        assert [error["code"] for error in json.loads(result.stdout)["errors"]] == ["HFARG002"]


@pytest.mark.usefixtures("_wired")
def test_prune_apply_takes_the_lock_and_completes_a_plan(config_file: Path, layout, hub):
    for index in range(6):
        commit = f"{index + 1:040d}"
        hub.revisions[commit] = {**CONTENT, "generation.txt": str(index).encode()}
        hub.heads[MODEL.selector] = commit
        CliRunner().invoke(app, ["--config", str(config_file), "sync"])

    result = CliRunner().invoke(app, ["--json", "--config", str(config_file), "prune", "--apply"])

    assert result.exit_code == ExitCode.SUCCESS
    payload = json.loads(result.stdout)["data"]
    assert payload["plans"] == []
    assert payload["applied"] == []


@pytest.mark.usefixtures("_wired")
def test_prune_apply_stops_on_a_journal_that_asked_for_an_operator(config_file: Path, layout, hub):
    """`TX-07` again: a plan built over an archive with an unfinished
    publication in it would be counting revisions nobody has finished deciding
    about."""
    for index in range(6):
        commit = f"{index + 1:040d}"
        hub.revisions[commit] = {**CONTENT, "generation.txt": str(index).encode()}
        hub.heads[MODEL.selector] = commit
        CliRunner().invoke(app, ["--config", str(config_file), "sync"])
    open_transaction(
        layout,
        transaction_id=new_transaction_id(),
        operation="prune",
        run_id=new_run_id(),
        archive_id=ARCHIVE_ID,
        config_fingerprint="0" * 64,
    ).needs_operator("HFTXN004", "two equally valid resolutions")
    before = {reference.commit_sha for reference in retained_references(layout, MODEL)}

    result = CliRunner().invoke(app, ["--json", "--config", str(config_file), "prune", "--apply"])

    assert result.exit_code == ExitCode.SAFETY
    assert [error["code"] for error in json.loads(result.stdout)["errors"]] == ["HFTXN004"]
    assert {r.commit_sha for r in retained_references(layout, MODEL)} == before


@pytest.mark.usefixtures("_wired")
def test_prune_prints_that_there_is_nothing_to_do(config_file: Path):
    result = CliRunner().invoke(app, ["--config", str(config_file), "prune", "--dry-run"])

    assert "nothing to prune" in result.output


@pytest.mark.usefixtures("_wired")
def test_prune_apply_completes_retention_an_earlier_failure_deferred(
    config_file: Path, layout, hub
):
    # The command's documented reason to exist (`docs/cli.md` §2). The sixth
    # publication's prune fails at cache deletion, leaving six revisions; a
    # later `prune --apply` finishes the job.
    for index in range(5):
        commit = f"{index + 1:040d}"
        hub.revisions[commit] = {**CONTENT, "generation.txt": str(index).encode()}
        hub.heads[MODEL.selector] = commit
        CliRunner().invoke(app, ["--config", str(config_file), "sync"])

    def refuse(cache_dir, commit_sha=None):
        message = "the cache is unreadable"
        raise OSError(message)

    hub.revisions["6" * 40] = {**CONTENT, "generation.txt": b"5"}
    hub.heads[MODEL.selector] = "6" * 40
    # Scoped, so undoing it leaves the lock directory and the Hub wiring alone.
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr("huggingface_hub.scan_cache_dir", refuse)
        CliRunner().invoke(app, ["--config", str(config_file), "sync"])
    assert len(retained_references(layout, MODEL)) == 6

    result = CliRunner().invoke(app, ["--json", "--config", str(config_file), "prune", "--apply"])

    assert result.exit_code == ExitCode.SUCCESS
    applied = json.loads(result.stdout)["data"]["applied"]
    assert [record["publication_generation"] for record in applied] == [1]
    assert len(retained_references(layout, MODEL)) == 5


@pytest.mark.usefixtures("_wired")
def test_prune_reports_a_failure_rather_than_a_traceback(
    config_file: Path, layout, hub, monkeypatch
):
    for index in range(5):
        commit = f"{index + 1:040d}"
        hub.revisions[commit] = {**CONTENT, "generation.txt": str(index).encode()}
        hub.heads[MODEL.selector] = commit
        CliRunner().invoke(app, ["--config", str(config_file), "sync"])

    def refuse(cache_dir, commit_sha=None):
        message = "the cache is unreadable"
        raise OSError(message)

    hub.revisions["6" * 40] = {**CONTENT, "generation.txt": b"5"}
    hub.heads[MODEL.selector] = "6" * 40
    monkeypatch.setattr("huggingface_hub.scan_cache_dir", refuse)
    CliRunner().invoke(app, ["--config", str(config_file), "sync"])

    result = CliRunner().invoke(app, ["--json", "--config", str(config_file), "prune", "--apply"])

    assert result.exit_code == ExitCode.RETENTION
    assert [error["code"] for error in json.loads(result.stdout)["errors"]] == ["HFRET002"]
    # Nothing removed: six revisions remain, which §15.2 prefers to losing one.
    assert len(retained_references(layout, MODEL)) == 6


# --------------------------------------------------------------------------- #
# Nothing deletes on an upstream error or a configuration edit (`AD-06`)
# --------------------------------------------------------------------------- #


def test_a_repository_removed_from_configuration_keeps_every_revision(
    client, layout, config, hub, tmp_path
):
    # Removing an entry from a file is not a request to delete an archive.
    heads_through(client, layout, config, hub, 3)
    reduced = tmp_path / "reduced.toml"
    reduced.write_text(
        CONFIG.format(root=layout.root, archive_id=ARCHIVE_ID, reserve_gib=0).replace(
            '[[repositories]]\nid = "organization/model-name"\ntype = "model"\n', ""
        ),
        encoding="utf-8",
    )

    run(client, layout, load_config(reduced))

    assert len(retained_references(layout, MODEL)) == 3
    assert RepositoryLayout(archive=layout, identity=MODEL).current_ref.exists()


def test_an_unmanaged_repository_stays_in_the_catalog_as_unmanaged(
    client, layout, config, hub, tmp_path
):
    heads_through(client, layout, config, hub, 2)
    reduced = tmp_path / "reduced.toml"
    reduced.write_text(
        CONFIG.format(root=layout.root, archive_id=ARCHIVE_ID, reserve_gib=0).replace(
            '[[repositories]]\nid = "organization/model-name"\ntype = "model"\n', ""
        ),
        encoding="utf-8",
    )

    run(client, layout, load_config(reduced))

    catalog = RepositoriesCatalog.model_validate_json(
        layout.repositories_catalog.read_text(encoding="utf-8")
    )
    entry = next(e for e in catalog.repositories if e.repository_id == MODEL.id)
    assert entry.managed is False
    assert entry.enabled is None
    assert len(entry.revisions) == 2


def test_an_unmanaged_repository_is_never_pruned(client, layout, config, hub, tmp_path):
    # A prune is triggered by a *successful publication* of that repository
    # (`AD-04`); a repository nothing is publishing to cannot reach one.
    heads_through(client, layout, config, hub, 6)
    reduced = tmp_path / "reduced.toml"
    reduced.write_text(
        CONFIG.format(root=layout.root, archive_id=ARCHIVE_ID, reserve_gib=0).replace(
            '[[repositories]]\nid = "organization/model-name"\ntype = "model"\n', ""
        ),
        encoding="utf-8",
    )
    before = [r.commit_sha for r in retained_references(layout, MODEL)]

    run(client, layout, load_config(reduced))

    assert [r.commit_sha for r in retained_references(layout, MODEL)] == before


@pytest.mark.parametrize("code", ["HFHUB004", "HFHUB005", "HFHUB001"])
def test_an_upstream_error_never_prunes_or_deletes(client, layout, config, hub, code):
    # A 403, a 404, and a deleted repository never trigger deletion (`AD-06`).
    heads_through(client, layout, config, hub, 6)
    before = [r.commit_sha for r in retained_references(layout, MODEL)]
    current = read_reference(
        layout, RepositoryLayout(archive=layout, identity=MODEL).current_ref
    ).commit_sha

    def unavailable(self, identity, revision):
        message = f"{identity.selector} is unavailable"
        raise SynchronizationError.single(message, code=code)

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(HubClient, "repository", unavailable)
        outcome = run(client, layout, config)

    assert statuses(outcome)[MODEL.selector] == "failed"
    assert [r.commit_sha for r in retained_references(layout, MODEL)] == before
    assert (
        read_reference(
            layout, RepositoryLayout(archive=layout, identity=MODEL).current_ref
        ).commit_sha
        == current
    )


def test_a_disabled_repository_keeps_its_revisions(client, layout, config, hub, tmp_path):
    heads_through(client, layout, config, hub, 3)
    disabled = tmp_path / "off.toml"
    disabled.write_text(
        CONFIG.format(root=layout.root, archive_id=ARCHIVE_ID, reserve_gib=0).replace(
            'id = "organization/model-name"\ntype = "model"',
            'id = "organization/model-name"\ntype = "model"\nenabled = false',
        ),
        encoding="utf-8",
    )

    outcome = run(client, layout, load_config(disabled))

    assert statuses(outcome)[MODEL.selector] == "disabled"
    assert len(retained_references(layout, MODEL)) == 3


# --------------------------------------------------------------------------- #
# Dependency warnings (plan §17, `AD-07`)
# --------------------------------------------------------------------------- #


def test_an_undeclared_dependency_warns_and_still_exits_zero(client, layout, config, hub):
    # `AD-07`: the warning is durable and visible, and changes nothing else.
    hub.revisions[SHA_A] = {
        **CONTENT,
        "README.md": b"---\nbase_model: meta-llama/Llama-3.1-8B\n---\n\n# A model\n",
    }

    outcome = run(client, layout, config)

    result = next(r for r in outcome.report.repositories if r.repository_id == MODEL.id)
    assert result.status == "completed_with_warnings"
    assert "HFDEP001" in result.warnings
    assert outcome.exit_code == ExitCode.SUCCESS
    assert outcome.report.outcome == "success_with_warnings"


def test_a_warning_is_preserved_when_another_repository_fails(client, layout, config, hub):
    hub.revisions[SHA_A] = {
        **CONTENT,
        "README.md": b"---\nbase_model: meta-llama/Llama-3.1-8B\n---\n\n# A model\n",
    }
    del hub.heads[DATASET.selector]

    outcome = run(client, layout, config)

    assert outcome.exit_code == ExitCode.SYNC
    assert outcome.report.outcome == "failed"
    assert statuses(outcome) == {
        MODEL.selector: "completed_with_warnings",
        DATASET.selector: "failed",
    }
    assert "HFDEP001" in outcome.report.warnings
    assert outcome.report.errors


def test_the_dependency_is_written_into_the_immutable_manifest(client, layout, config, hub):
    hub.revisions[SHA_A] = {
        **CONTENT,
        "README.md": b"---\nbase_model: meta-llama/Llama-3.1-8B\n---\n\n# A model\n",
    }

    run(client, layout, config)

    repository = RepositoryLayout(archive=layout, identity=MODEL)
    reference = read_reference(layout, repository.current_ref)
    manifest = RevisionManifest.model_validate_json(
        (layout.published / str(reference.manifest)).read_text(encoding="utf-8")
    )
    assert [item.detected_id for item in manifest.dependencies] == ["meta-llama/Llama-3.1-8B"]
    assert manifest.dependencies[0].declared is False


def test_a_declared_dependency_produces_no_warning(client, layout, config, hub, tmp_path):
    hub.revisions[SHA_A] = {
        **CONTENT,
        "README.md": b"---\nbase_model: meta-llama/Llama-3.1-8B\n---\n\n# A model\n",
    }
    declared = tmp_path / "declared.toml"
    declared.write_text(
        CONFIG.format(root=layout.root, archive_id=ARCHIVE_ID, reserve_gib=0).replace(
            'id = "organization/model-name"\ntype = "model"',
            'id = "organization/model-name"\ntype = "model"\n'
            'declared_dependencies = ["meta-llama/Llama-3.1-8B"]',
        ),
        encoding="utf-8",
    )

    outcome = run(client, layout, load_config(declared))

    result = next(r for r in outcome.report.repositories if r.repository_id == MODEL.id)
    assert result.status == "published"
    assert result.warnings == ()


def test_a_dependency_never_triggers_a_download(client, layout, config, hub):
    # `NG-05`: a detector that fetched what it found would turn one configured
    # repository into an unbounded transitive closure.
    hub.revisions[SHA_A] = {
        **CONTENT,
        "README.md": b"---\nbase_model: meta-llama/Llama-3.1-8B\n---\n\n# A model\n",
    }

    run(client, layout, config)

    assert set(hub.downloads) == {SHA_A}
    assert published_repositories(layout) == (DATASET, MODEL)


def test_a_dependency_that_is_also_configured_is_recorded_as_managed(
    client, layout, config, hub, tmp_path
):
    hub.revisions[SHA_A] = {
        **CONTENT,
        "README.md": b"---\nbase_model: organization/dataset-name\n---\n\n# A model\n",
    }

    run(client, layout, config)

    repository = RepositoryLayout(archive=layout, identity=MODEL)
    reference = read_reference(layout, repository.current_ref)
    manifest = RevisionManifest.model_validate_json(
        (layout.published / str(reference.manifest)).read_text(encoding="utf-8")
    )
    assert manifest.dependencies[0].managed is True


# --------------------------------------------------------------------------- #
# `purge` command (`AD-20`, `PUR-001`)
# --------------------------------------------------------------------------- #


@pytest.mark.usefixtures("_wired")
def test_purge_requires_an_explicit_scope(config_file: Path):
    result = CliRunner().invoke(app, ["--json", "--config", str(config_file), "purge", "--dry-run"])

    assert result.exit_code == ExitCode.CONFIGURATION
    assert [error["code"] for error in json.loads(result.stdout)["errors"]] == ["HFARG003"]


@pytest.mark.usefixtures("_wired")
def test_purge_refuses_all_unmanaged_with_a_selector(config_file: Path):
    result = CliRunner().invoke(
        app,
        [
            "--json",
            "--config",
            str(config_file),
            "purge",
            "--dry-run",
            "--all-unmanaged",
            MODEL.selector,
        ],
    )

    assert result.exit_code == ExitCode.CONFIGURATION
    assert [error["code"] for error in json.loads(result.stdout)["errors"]] == ["HFARG002"]


@pytest.mark.usefixtures("_wired")
def test_purge_refuses_a_revision_selector(config_file: Path):
    result = CliRunner().invoke(
        app,
        [
            "--json",
            "--config",
            str(config_file),
            "purge",
            "--dry-run",
            f"{MODEL.selector}@{SHA_A}",
        ],
    )

    assert result.exit_code == ExitCode.CONFIGURATION
    assert [error["code"] for error in json.loads(result.stdout)["errors"]] == ["HFARG001"]


@pytest.mark.usefixtures("_wired")
def test_purge_refuses_a_repository_still_in_configuration(config_file: Path):
    result = CliRunner().invoke(
        app,
        [
            "--json",
            "--config",
            str(config_file),
            "purge",
            "--dry-run",
            MODEL.selector,
        ],
    )

    assert result.exit_code == ExitCode.CONFIGURATION
    assert [error["code"] for error in json.loads(result.stdout)["errors"]] == ["HFARG007"]


@pytest.mark.usefixtures("_wired")
def test_purge_all_unmanaged_removes_only_repositories_absent_from_configuration(
    config_file: Path,
    layout: ArchiveLayout,
    hub: FakeHub,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    hub.heads[MODEL.selector] = SHA_A
    hub.heads[DATASET.selector] = SHA_A
    synced = CliRunner().invoke(app, ["--config", str(config_file), "sync"])
    assert synced.exit_code == ExitCode.SUCCESS
    reduced = tmp_path / "reduced.toml"
    reduced.write_text(
        config_file.read_text(encoding="utf-8").replace(
            '[[repositories]]\nid = "organization/model-name"\ntype = "model"\n', ""
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(purge_module, "delete_cache_revisions", lambda *_args: 0)

    dry_run = CliRunner().invoke(
        app,
        ["--json", "--config", str(reduced), "purge", "--dry-run", "--all-unmanaged"],
    )
    assert dry_run.exit_code == ExitCode.SUCCESS
    assert [plan["repository_id"] for plan in json.loads(dry_run.stdout)["data"]["plans"]] == [
        MODEL.id
    ]
    assert RepositoryLayout(archive=layout, identity=MODEL).directory.is_dir()

    applied = CliRunner().invoke(
        app,
        ["--json", "--config", str(reduced), "purge", "--apply", "--all-unmanaged"],
    )
    assert applied.exit_code == ExitCode.SUCCESS
    assert not RepositoryLayout(archive=layout, identity=MODEL).directory.exists()
    assert RepositoryLayout(archive=layout, identity=DATASET).directory.is_dir()
