"""The Hub adapter against the real Hub.

Marked `live` and deselected by default. Run it with `pytest -m live`.

Every other Hub test uses a fake, which is right: it makes the suite fast,
offline, and deterministic, and it pins the adapter's own logic. It also cannot
tell you that `huggingface_hub`'s response shape is still what `_facts` reads,
or that `huggingface.co`'s certificate verifies against this host's trust store.
Those are the two things this file exists for.

It reads only — `repo_info`, `whoami`, `list_repo_tree`, a `snapshot_download`
dry run, DNS, TLS — and downloads nothing. The dry run in particular is asserted
to leave no cache directory behind, because `plan` is run by operators sizing a
dataset before the archive exists at all.

The two repositories are the ones the archive itself syncs (`examples/config.toml`,
"Test repositories"), so these tests and the first real sync exercise the same
upstream content; a test that fails because one was renamed is reporting
something true.
"""

import os
from datetime import UTC, datetime

import pytest

from hfcache.archive import initialize_archive
from hfcache.credentials import ResolvedToken, TokenSource
from hfcache.errors import SynchronizationError
from hfcache.hub import (
    HubClient,
    endpoint_host,
    resolve_host,
    verify_tls,
)
from hfcache.identity import (
    RepositoryIdentity,
    new_publication_id,
    new_run_id,
    new_transaction_id,
)
from hfcache.manifests import RevisionManifest
from hfcache.paths import ArchiveLayout, RepositoryLayout
from hfcache.publication import create_staging, next_generation, read_reference
from hfcache.storage import parse_mount_table
from hfcache.sync import (
    Timeline,
    build_manifest,
    completeness_problems,
    hash_snapshot,
    publish_revision,
    snapshot_paths,
)
from hfcache.transactions import open_transaction
from hfcache.verification import resolve_archive, verify_targets

pytestmark = pytest.mark.live

ENDPOINT = "https://huggingface.co"

# The two test repositories, chosen at `HUB-004` under docs/development.md opt-in test fixtures
# and recorded
# in `examples/config.toml` and `examples/config.toml`. Small, public, long-standing,
# and owned by `hf-internal-testing`, which exists to be depended on by tests.
MODEL = RepositoryIdentity.of("model", "hf-internal-testing/tiny-random-gpt2")
DATASET = RepositoryIdentity.of("dataset", "hf-internal-testing/fixtures_ade20k")


@pytest.fixture(scope="module")
def client() -> HubClient:
    """An anonymous client, which is what a public archive runs as."""
    return HubClient.of(ResolvedToken(source=TokenSource.NONE), endpoint=ENDPOINT)


def test_the_endpoint_host_resolves():
    assert resolve_host(endpoint_host(ENDPOINT))


def test_the_endpoint_certificate_verifies_against_this_hosts_trust_store():
    # Not a mock: this proves the writer's CA bundle and clock agree with the
    # Hub, which is what `doctor` check 16 reports to an operator.
    detail = verify_tls(endpoint_host(ENDPOINT))

    assert "TLS" in detail


def test_an_anonymous_run_needs_no_identity(client: HubClient):
    identity = client.whoami()

    assert identity.name == "anonymous"
    assert not identity.authenticated


@pytest.mark.parametrize("identity", [MODEL, DATASET], ids=["model", "dataset"])
def test_a_real_repository_resolves_to_a_full_commit_sha(client: HubClient, identity):
    # The one field the whole design depends on: every path, manifest, and
    # reference is keyed by it.
    facts = client.repository(identity, "main")

    assert len(facts.commit_sha) == 40
    assert facts.commit_sha == facts.commit_sha.lower()
    assert not facts.private
    assert not facts.gated


def test_resolving_the_same_reference_twice_gives_the_same_sha(client: HubClient):
    first = client.repository(MODEL, "main")
    second = client.repository(MODEL, "main")

    assert first.commit_sha == second.commit_sha


def test_a_repository_that_does_not_exist_is_hfhub004(client: HubClient):
    absent = RepositoryIdentity.of("model", "hfcache-test/definitely-not-a-real-repository")

    with pytest.raises(SynchronizationError) as caught:
        client.repository(absent, "main")

    assert [problem.code for problem in caught.value.problems] == ["HFHUB004"]


def test_a_revision_that_does_not_exist_is_reported(client: HubClient):
    with pytest.raises(SynchronizationError) as caught:
        client.repository(MODEL, "a-branch-that-does-not-exist")

    # The Hub distinguishes a missing revision from a missing repository, and so
    # does the adapter; both are refusals rather than a crash.
    assert [problem.code for problem in caught.value.problems] == ["HFHUB007"]


@pytest.mark.parametrize("identity", [MODEL, DATASET], ids=["model", "dataset"])
def test_a_real_tree_listing_reads_as_typed_entries(client: HubClient, identity):
    facts = client.repository(identity, "main")

    tree = client.tree(identity, facts.commit_sha)

    assert tree
    assert all(entry.path and entry.size >= 0 for entry in tree)
    # Sorted and unique, which is what every generated array in the archive is
    # required to be (`docs/architecture.md` §5.3).
    paths = [entry.path for entry in tree]
    assert paths == sorted(paths)
    assert len(set(paths)) == len(paths)


@pytest.mark.parametrize("identity", [MODEL, DATASET], ids=["model", "dataset"])
def test_a_dry_run_costs_a_revision_without_downloading_it(client: HubClient, identity, tmp_path):
    # The cache directory does not exist and must not be created: `plan` mutates
    # nothing, and an operator sizing a dataset runs it before `archive init`.
    cache = tmp_path / "hub"

    estimate = client.estimate(
        identity, client.repository(identity, "main").commit_sha, cache_dir=cache, max_workers=2
    )

    assert not cache.exists()
    assert estimate.file_count > 0
    assert estimate.logical_bytes > 0
    # Nothing is cached, so the whole revision is new.
    assert estimate.new_bytes == estimate.logical_bytes
    assert estimate.cached_bytes == 0


@pytest.mark.parametrize("identity", [MODEL, DATASET], ids=["model", "dataset"])
def test_a_real_download_fetches_every_file_of_the_revision(client: HubClient, identity, tmp_path):
    # docs/development.md test contract: download every file, into a cache this test owns and throws
    # away. Both repositories are exercised because a model's weight files go
    # through the Xet transfer path and a dataset's payload largely does not.
    cache = tmp_path / "hub"
    facts = client.repository(identity, "main")
    tree = client.tree(identity, facts.commit_sha)

    snapshot = client.download(identity, facts.commit_sha, cache_dir=cache, max_workers=2)

    assert snapshot.is_relative_to(cache.resolve())
    for entry in tree:
        landed = snapshot / entry.path
        assert landed.resolve().is_file(), entry.path
        assert landed.stat().st_size == entry.size, entry.path


@pytest.mark.parametrize("identity", [MODEL, DATASET], ids=["model", "dataset"])
def test_a_real_download_passes_both_completeness_checks(client: HubClient, identity, tmp_path):
    # docs/cli.md sync contract against real content: the library's own local-only
    # assembly, and this application's independent comparison of what landed
    # with what the Hub listed. Both have to hold — the first says the library
    # is satisfied, the second says what satisfied it is the promised path set.
    cache = tmp_path / "hub"
    facts = client.repository(identity, "main")
    tree = client.tree(identity, facts.commit_sha)
    client.download(identity, facts.commit_sha, cache_dir=cache, max_workers=2)

    snapshot = client.verify_local(identity, facts.commit_sha, cache_dir=cache)

    assert completeness_problems(snapshot, tree, identity=identity, cache_root=cache) == []


def test_the_local_check_needs_no_network(client: HubClient, tmp_path, monkeypatch):
    # It is the check a `verify` run performs with `HF_HUB_OFFLINE=1` set
    # (docs/security.md hardening posture), so it must not reach the Hub at all.
    cache = tmp_path / "hub"
    facts = client.repository(DATASET, "main")
    client.download(DATASET, facts.commit_sha, cache_dir=cache, max_workers=2)

    monkeypatch.setenv("HF_HUB_OFFLINE", "1")

    assert client.verify_local(DATASET, facts.commit_sha, cache_dir=cache).is_dir()


def test_a_cache_missing_a_blob_fails_the_local_check(client: HubClient, tmp_path):
    # The one failure this check exists to catch: the download reported success
    # and the bytes are no longer there.
    cache = tmp_path / "hub"
    facts = client.repository(DATASET, "main")
    snapshot = client.download(DATASET, facts.commit_sha, cache_dir=cache, max_workers=2)
    target = next(path for path in sorted(snapshot.iterdir()) if path.is_file())
    target.resolve().unlink()

    with pytest.raises(SynchronizationError) as caught:
        client.verify_local(DATASET, facts.commit_sha, cache_dir=cache)

    assert [problem.code for problem in caught.value.problems] == ["HFSYN001"]


def test_a_second_download_of_the_same_sha_fetches_nothing(client: HubClient, tmp_path):
    # docs/development.md test contract's "run a second sync and confirm no unnecessary download",
    # proven at the adapter: after one download the dry run reports the whole
    # revision as cached, which is the number a sync's capacity gate reads.
    cache = tmp_path / "hub"
    facts = client.repository(DATASET, "main")
    client.download(DATASET, facts.commit_sha, cache_dir=cache, max_workers=2)

    again = client.estimate(DATASET, facts.commit_sha, cache_dir=cache, max_workers=2)

    assert again.new_bytes == 0
    assert again.cached_bytes == again.logical_bytes > 0


def test_a_real_revision_produces_a_manifest_that_round_trips(client: HubClient, tmp_path):
    # The whole ingestion sequence against real content: resolve, list, download,
    # check completeness, hash, describe. The manifest model enforces its own
    # arithmetic, ordering, and timeline, so building one from real bytes and
    # reading it back is the end-to-end proof that the pieces agree.
    cache = tmp_path / "hub"
    facts = client.repository(DATASET, "main")
    tree = client.tree(DATASET, facts.commit_sha)
    started = datetime.now(UTC)
    client.download(DATASET, facts.commit_sha, cache_dir=cache, max_workers=2)
    snapshot = client.verify_local(DATASET, facts.commit_sha, cache_dir=cache)
    assert completeness_problems(snapshot, tree, identity=DATASET, cache_root=cache) == []
    hashed = hash_snapshot(snapshot, tree, identity=DATASET)
    finished = datetime.now(UTC)

    manifest = build_manifest(
        identity=DATASET,
        requested_revision="main",
        commit_sha=facts.commit_sha,
        publication_id=new_publication_id(),
        publication_generation=1,
        publication_mode="hardlink",
        tree=tree,
        hashed=hashed,
        layout=RepositoryLayout(archive=ArchiveLayout(root=tmp_path / "archive"), identity=DATASET),
        hub_endpoint=ENDPOINT,
        timeline=Timeline(
            first_observed_at=started,
            download_started_at=started,
            download_completed_at=finished,
            verified_at=finished,
            published_at=finished,
        ),
    )

    assert manifest.file_count == len(tree)
    assert manifest.total_bytes == sum(entry.size for entry in tree)
    assert RevisionManifest.model_validate_json(manifest.to_json()) == manifest
    # Every digest was computed here; nothing was reused, since the cache is new.
    assert manifest.verification.reused_digests == 0
    assert all(entry.provenance.hashed for entry in manifest.files)


def test_a_real_lfs_file_records_its_upstream_identifiers(client: HubClient, tmp_path):
    # Comparison values only (`AD-18`). The model's weight file is the one that
    # exercises the LFS and Xet paths.
    facts = client.repository(MODEL, "main")

    tree = client.tree(MODEL, facts.commit_sha)

    weights = next(entry for entry in tree if entry.path.endswith(".safetensors"))
    assert weights.git_oid
    assert weights.lfs_sha256


def test_the_dry_run_and_the_tree_agree_about_the_revisions_size(client: HubClient, tmp_path):
    # Two independent Hub answers about the same immutable revision. `plan`
    # reports the tree's size as the repository's and the dry run's as what
    # would be fetched, so a disagreement would make those two numbers
    # incomparable.
    facts = client.repository(DATASET, "main")

    tree = client.tree(DATASET, facts.commit_sha)
    estimate = client.estimate(DATASET, facts.commit_sha, cache_dir=tmp_path / "hub", max_workers=2)

    assert estimate.file_count == len(tree)
    assert estimate.logical_bytes == sum(entry.size for entry in tree)


@pytest.mark.parametrize("identity", [MODEL, DATASET], ids=["model", "dataset"])
def test_a_real_revision_is_published_end_to_end(client: HubClient, identity, tmp_path):
    # Phase 4's acceptance, on a throwaway archive: one public model and one
    # public dataset can be archived, every Hub path appears in the publication,
    # and the references a consumer reads resolve to what they name.
    #
    # The archive here is a temporary directory described to the application as
    # an NFSv4 mount. `/srv/hfcache` is deliberately untouched: initializing it
    # is a one-time authorization spent at the §29 rollout checkpoint, not by a
    # test run.
    root = tmp_path / "archive"
    root.mkdir()
    layout = ArchiveLayout(root=root)
    initialize_archive(
        layout,
        archive_id="3f2a1c88-7b40-4a2e-9c1d-0e5b6a7f8d90",
        table=parse_mount_table(
            f"457 47 0:68 / {os.path.realpath(root)} rw,relatime shared:488 - nfs4 nas:/x rw\n"
        ),
    )

    facts = client.repository(identity, "main")
    tree = client.tree(identity, facts.commit_sha)
    started = datetime.now(UTC)
    client.download(identity, facts.commit_sha, cache_dir=layout.hub_cache, max_workers=2)
    snapshot = client.verify_local(identity, facts.commit_sha, cache_dir=layout.hub_cache)
    assert (
        completeness_problems(snapshot, tree, identity=identity, cache_root=layout.hub_cache) == []
    )
    hashed = hash_snapshot(snapshot, tree, identity=identity)
    finished = datetime.now(UTC)

    repository = RepositoryLayout(archive=layout, identity=identity)
    transaction_id = new_transaction_id()
    transaction = open_transaction(
        layout,
        transaction_id=transaction_id,
        operation="publication",
        run_id=new_run_id(),
        archive_id="3f2a1c88-7b40-4a2e-9c1d-0e5b6a7f8d90",
        config_fingerprint="c" * 64,
        repository_id=identity.id,
        repository_type=identity.type,
    )
    staging = create_staging(layout, transaction_id)
    transaction.checkpoint("staging_created", staging_path="x")
    transaction.checkpoint("download_completed", cache_revision=facts.commit_sha)
    transaction.checkpoint("content_hashed", hashed_objects=hashed.hashed_objects)
    manifest = build_manifest(
        identity=identity,
        requested_revision="main",
        commit_sha=facts.commit_sha,
        publication_id=new_publication_id(),
        publication_generation=next_generation(layout, identity),
        publication_mode="hardlink",
        tree=tree,
        hashed=hashed,
        layout=repository,
        hub_endpoint=ENDPOINT,
        timeline=Timeline(
            first_observed_at=started,
            download_started_at=started,
            download_completed_at=finished,
            verified_at=finished,
            published_at=finished,
        ),
    )

    outcome = publish_revision(
        layout,
        transaction,
        identity=identity,
        snapshot=snapshot,
        manifest=manifest,
        hashed=hashed,
        staging=staging,
        publication_mode="hardlink",
        cache_root=layout.hub_cache,
    )
    transaction.checkpoint("publication_committed", state="committed")
    transaction.commit()

    # Every Hub path appears in the publication, at the size the Hub listed and
    # as the same inode as the cache blob — hardlink publication, no second copy.
    for entry in tree:
        landed = outcome.tree / entry.path
        assert landed.is_file(), entry.path
        assert landed.stat().st_size == entry.size, entry.path
        assert landed.samefile(snapshot / entry.path), entry.path

    # The reference a consumer reads resolves to the tree and the manifest.
    reference = read_reference(layout, repository.current_ref)
    assert (layout.published / str(reference.tree)).is_dir()
    assert (layout.published / str(reference.manifest)).is_file()
    assert reference.commit_sha == facts.commit_sha

    # And the manifest describes exactly what was published.
    published = RevisionManifest.model_validate_json(
        (layout.published / str(reference.manifest)).read_text(encoding="utf-8")
    )
    assert published == manifest
    assert list(snapshot_paths(outcome.tree)) == [entry.path for entry in published.files]

    # Phase 6's acceptance on the same real content: reading it all back
    # verifies clean without constructing any Hub client, and reads each
    # physical object once. Isolated-process offline initialization and the
    # no-IP executor sandbox have their separate acceptance tests (API-004).
    verified = verify_targets(resolve_archive(layout), started_at=started)
    assert verified.findings == ()
    assert verified.outcome == "clean"
    assert verified.revisions == 1
    assert verified.objects_read == len(tree)
    assert verified.bytes_read == sum(entry.size for entry in tree)

    # A flipped byte in a published file is found, and finding it changes
    # nothing — the manifest and the reference are the bytes they were.
    damaged = outcome.tree / tree[0].path
    before = damaged.read_bytes()
    manifest_bytes = (layout.published / str(reference.manifest)).read_bytes()
    damaged.unlink()
    damaged.write_bytes(bytes([before[0] ^ 0xFF]) + before[1:])
    found = verify_targets(resolve_archive(layout), started_at=started)
    assert [finding.kind for finding in found.findings] == ["digest_mismatch"]
    assert (layout.published / str(reference.manifest)).read_bytes() == manifest_bytes
    assert repository.revision_ref(facts.commit_sha).is_file()
