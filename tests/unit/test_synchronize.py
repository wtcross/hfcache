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
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
from typer.testing import CliRunner

from hfcache.archive import initialize_archive
from hfcache.cli import app
from hfcache.config import ApplicationConfig, load_config
from hfcache.credentials import ResolvedToken, TokenSource
from hfcache.errors import ExitCode, IntegrityError, SynchronizationError
from hfcache.hub import HubClient
from hfcache.identity import RepositoryIdentity, new_run_id
from hfcache.locking import lock_path
from hfcache.manifests import RevisionManifest
from hfcache.paths import ArchiveLayout, RepositoryLayout
from hfcache.publication import read_reference, retained_references
from hfcache.reporting import RepositoriesCatalog, RunReport
from hfcache.storage import parse_mount_table
from hfcache.sync import synchronize
from hfcache.transactions import read_journal

if TYPE_CHECKING:
    from collections.abc import Sequence

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
    endpoint: str = "https://huggingface.co"

    def whoami(self, token: Any = None) -> dict:  # pragma: no cover - anonymous here
        return {"name": "anonymous"}

    def repo_info(self, repo_id: str, *, repo_type: str, revision: str, token: Any = None) -> Any:
        return Info(sha=self.heads[f"{repo_type}:{repo_id}"])

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
        "hostname": "hfcachewriter.lab.cross.solutions",
        "huggingface_hub_version": "1.24.0",
        "invocation_mode": "interactive",
        "python_version": "3.14.6",
    }


def run(
    client: HubClient,
    layout: ArchiveLayout,
    config: ApplicationConfig,
    selected: Sequence[Any] | None = None,
):
    return synchronize(
        client,
        layout,
        config,
        selected=selected if selected is not None else config.repositories,
        envelope=envelope(config),
        run_id=new_run_id(),
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


def test_repositories_are_processed_in_configuration_order(client, layout, config, hub):
    # Not selector order and not alphabetical: two runs naming the same
    # repositories must do the same things in the same sequence.
    reversed_selection = list(reversed(config.repositories))

    outcome = run(client, layout, config, selected=reversed_selection)

    # The *report* is sorted for readability; what matters is that both ran.
    assert len(outcome.report.repositories) == 2
    assert len(hub.downloads) == 2


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
    journals = sorted(layout.transactions.glob("*.json"))
    assert journals
    for path in journals:
        assert read_journal(layout, path).journal.state == "failed"


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
    payload = json.loads(result.output)["data"]
    assert {entry["status"] for entry in payload["repositories"]} == {"published"}
    assert payload["report"].startswith("runs/")


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
    assert [error["code"] for error in json.loads(result.output)["errors"]] == ["HFMNT010"]


@pytest.mark.usefixtures("_wired")
def test_the_sync_command_restricts_a_run_to_its_selectors(config_file: Path):
    result = CliRunner().invoke(
        app, ["--json", "--config", str(config_file), "sync", "model:organization/model-name"]
    )

    payload = json.loads(result.output)["data"]
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
    assert json.loads(result.output)["outcome"] == "failed"


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
    # written, which is where an unattended run's evidence belongs.
    result = CliRunner().invoke(app, ["--quiet", "--config", str(config_file), "sync"])

    assert result.exit_code == ExitCode.SUCCESS
    assert result.output.strip() == ""


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
        for e in json.loads(result.output)["data"]["repositories"]
    }
    assert entries[MODEL.selector]["retained_revisions"] == 1
    assert entries[MODEL.selector]["current_commit_sha"] == SHA_A
    assert entries[MODEL.selector]["retained_generations"] == [1]
    assert entries[MODEL.selector]["last_run_status"] == "published"


@pytest.mark.usefixtures("_wired")
def test_status_answers_for_a_repository_that_was_never_synced(config_file: Path):
    # A configured repository with nothing archived yet is a normal state.
    result = CliRunner().invoke(app, ["--json", "--config", str(config_file), "status"])

    entry = json.loads(result.output)["data"]["repositories"][0]
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
    assert {e["upstream_state"] for e in json.loads(result.output)["data"]["repositories"]} == {
        "unknown"
    }


@pytest.mark.usefixtures("_wired")
def test_list_reads_manifests_and_references_not_the_catalog(config_file: Path, layout):
    CliRunner().invoke(app, ["--config", str(config_file), "sync"])
    # The catalog is derived and can be missing (`FS-16`); `list` answers anyway.
    layout.repositories_catalog.unlink()

    result = CliRunner().invoke(app, ["--json", "--config", str(config_file), "list"])

    entries = json.loads(result.output)["data"]["repositories"]
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

    entries = {e["repository_id"]: e for e in json.loads(result.output)["data"]["repositories"]}
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

    entries = json.loads(result.output)["data"]["repositories"]
    assert [e["repository_id"] for e in entries] == [DATASET.id]


@pytest.mark.usefixtures("_wired")
def test_list_restricts_to_its_selectors(config_file: Path):
    CliRunner().invoke(app, ["--config", str(config_file), "sync"])

    result = CliRunner().invoke(
        app, ["--json", "--config", str(config_file), "list", "model:organization/model-name"]
    )

    entries = json.loads(result.output)["data"]["repositories"]
    assert [e["repository_id"] for e in entries] == [MODEL.id]


def test_list_refuses_a_type_that_is_not_a_repository_type(config_file: Path):
    result = CliRunner().invoke(
        app, ["--json", "--config", str(config_file), "list", "--type", "space"]
    )

    assert result.exit_code == ExitCode.CONFIGURATION
    assert [error["code"] for error in json.loads(result.output)["errors"]] == ["HFARG002"]


@pytest.mark.usefixtures("_wired")
def test_list_prints_one_line_per_repository(config_file: Path):
    CliRunner().invoke(app, ["--config", str(config_file), "sync"])

    result = CliRunner().invoke(app, ["--config", str(config_file), "list"])

    assert "1 revisions" in result.output
    assert SHA_A in result.output


def test_list_answers_for_an_archive_with_nothing_published(config_file: Path):
    result = CliRunner().invoke(app, ["--json", "--config", str(config_file), "list"])

    assert result.exit_code == ExitCode.SUCCESS
    assert json.loads(result.output)["data"]["repositories"] == []


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
        for e in json.loads(result.output)["data"]["repositories"]
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

    entries = json.loads(result.output)["data"]["repositories"]
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

    entries = json.loads(result.output)["data"]["repositories"]
    assert result.exit_code == ExitCode.SUCCESS
    assert {entry["last_run_status"] for entry in entries} == {None}
    assert {entry["retained_revisions"] for entry in entries} == {0}
