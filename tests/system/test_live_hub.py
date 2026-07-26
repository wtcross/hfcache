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

The two repositories are the ones the archive itself syncs (`docs/progress.md`,
"Test repositories"), so these tests and the first real sync exercise the same
upstream content; a test that fails because one was renamed is reporting
something true.
"""

import pytest

from hfcache.credentials import ResolvedToken, TokenSource
from hfcache.errors import SynchronizationError
from hfcache.hub import (
    HubClient,
    endpoint_host,
    resolve_host,
    verify_tls,
)
from hfcache.identity import RepositoryIdentity

pytestmark = pytest.mark.live

ENDPOINT = "https://huggingface.co"

# The two test repositories, chosen at `HUB-004` under plan §36.5 and recorded
# in `docs/progress.md` and `examples/config.toml`. Small, public, long-standing,
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
    # Plan §26.3: download every file, into a cache this test owns and throws
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


def test_a_second_download_of_the_same_sha_fetches_nothing(client: HubClient, tmp_path):
    # Plan §26.3's "run a second sync and confirm no unnecessary download",
    # proven at the adapter: after one download the dry run reports the whole
    # revision as cached, which is the number a sync's capacity gate reads.
    cache = tmp_path / "hub"
    facts = client.repository(DATASET, "main")
    client.download(DATASET, facts.commit_sha, cache_dir=cache, max_workers=2)

    again = client.estimate(DATASET, facts.commit_sha, cache_dir=cache, max_workers=2)

    assert again.new_bytes == 0
    assert again.cached_bytes == again.logical_bytes > 0


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
