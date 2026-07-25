"""The Hub adapter against the real Hub.

Marked `live` and deselected by default. Run it with `pytest -m live`.

Every other Hub test uses a fake, which is right: it makes the suite fast,
offline, and deterministic, and it pins the adapter's own logic. It also cannot
tell you that `huggingface_hub`'s response shape is still what `_facts` reads,
or that `huggingface.co`'s certificate verifies against this host's trust store.
Those are the two things this file exists for.

It reads only — `repo_info`, `whoami`, DNS, TLS — and downloads nothing. The
repositories it names are chosen for being tiny and long-lived; a test that
fails because one was renamed is reporting something true.
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

# Small, public, and long-standing. `HUB-004` chooses the two repositories the
# archive actually syncs; these are only here to prove the adapter reads a real
# response correctly.
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
