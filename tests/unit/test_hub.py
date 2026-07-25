"""The Hub adapter, exercised through the seam it exists to provide.

`FakeApi` implements the `HubApi` protocol and nothing else. That is the point
of plan §12's "deterministic fakes without mocking library internals": the seam
is an interface this application defines, so these tests do not know or care how
`HfApi` is built, and a library upgrade that changes its internals cannot make
them pass for the wrong reason.

Two properties get the most attention here.

`token=` is always passed explicitly and is never `None`, because `None`
re-enables implicit discovery inside `huggingface_hub` and would let a
developer's cached credential change what a production run does
(`docs/security.md` T-07). The fake records what it was given, so the tests can
assert on it.

Every library exception becomes one coded problem. The real exception types are
constructed here rather than approximated, so the classification is tested
against the hierarchy the library actually raises.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import httpx
import pytest
from huggingface_hub.errors import (
    GatedRepoError,
    HfHubHTTPError,
    RepositoryNotFoundError,
    RevisionNotFoundError,
)

from hfcache.credentials import ResolvedToken, TokenSource
from hfcache.errors import ExitCode, SynchronizationError
from hfcache.hub import (
    HubClient,
    RepositoryFacts,
    access_problems,
    hub_problem,
    tree_entries,
)
from hfcache.identity import CommitSha, RepositoryIdentity

SHA = "0123456789abcdef0123456789abcdef01234567"

MODEL = RepositoryIdentity.of("model", "organization/model-name")


@dataclass
class Info:
    """The fields `_facts` reads out of a `repo_info` response."""

    sha: str | None = SHA
    private: bool = False
    gated: bool = False
    last_modified: datetime | None = None


@dataclass
class Entry:
    """One item of a repository tree listing."""

    path: str
    size: int | None = 0


@dataclass
class FakeApi:
    """A `HubApi` with no library machinery, recording how it was called."""

    info: Any = field(default_factory=Info)
    identity: dict[str, Any] = field(default_factory=lambda: {"name": "hfcache-service"})
    raises: Exception | None = None
    calls: list[dict[str, Any]] = field(default_factory=list)
    endpoint: str = "https://huggingface.co"

    def whoami(self, token: Any = None) -> dict[Any, Any]:
        self.calls.append({"method": "whoami", "token": token})
        if self.raises is not None:
            raise self.raises
        return self.identity

    def repo_info(self, repo_id: str, **arguments: Any) -> Any:
        self.calls.append({"method": "repo_info", "repo_id": repo_id, **arguments})
        if self.raises is not None:
            raise self.raises
        return self.info


def anonymous() -> ResolvedToken:
    return ResolvedToken(source=TokenSource.NONE)


def authenticated() -> ResolvedToken:
    return ResolvedToken(source=TokenSource.SYSTEMD_CREDENTIAL, secret="hf_notARealToken")


def client(api: FakeApi, token: ResolvedToken | None = None) -> HubClient:
    return HubClient(api=api, token=token or anonymous())


def codes(problems) -> list[str]:
    return [problem.code for problem in problems]


URL = "https://huggingface.co/api/models/organization/model-name"


def response(status: int) -> httpx.Response:
    """A real transport response, because the library's errors expect one.

    Constructing the genuine article rather than a stand-in: these constructors
    read `headers`, `url`, and `request` as well as `status_code`, and a
    hand-rolled object that satisfies today's reads would quietly stop
    resembling one after an upgrade.
    """
    return httpx.Response(status_code=status, request=httpx.Request("GET", URL))


def http_error(status: int) -> HfHubHTTPError:
    """An `HfHubHTTPError` carrying a status, the way the library raises one."""
    return HfHubHTTPError("the Hub said no", response=response(status))


def gated(message: str) -> GatedRepoError:
    return GatedRepoError(message, response=response(403))


def absent(message: str) -> RepositoryNotFoundError:
    return RepositoryNotFoundError(message, response=response(404))


def no_revision(message: str) -> RevisionNotFoundError:
    return RevisionNotFoundError(message, response=response(404))


# --------------------------------------------------------------------------- #
# The token is always explicit
# --------------------------------------------------------------------------- #


def test_an_anonymous_run_passes_false_rather_than_none():
    # `token=None` re-enables implicit discovery inside the library, which is
    # exactly the ambient-credential problem this application refuses to have.
    api = FakeApi()

    client(api).repository(MODEL, "main")

    assert api.calls[0]["token"] is False


def test_an_authenticated_run_passes_the_resolved_token():
    api = FakeApi()

    client(api, authenticated()).repository(MODEL, "main")

    assert api.calls[0]["token"] == "hf_notARealToken"


def test_no_call_ever_omits_the_token():
    api = FakeApi()
    hub = client(api, authenticated())

    hub.whoami()
    hub.repository(MODEL, "main")

    assert all("token" in call for call in api.calls)
    assert all(call["token"] is not None for call in api.calls)


def test_the_real_client_is_built_over_the_configured_endpoint():
    # Constructing `HfApi` makes no request, so this checks the wiring without
    # contacting anything: an endpoint set in configuration must reach the
    # library rather than being decoration on a default.
    hub = HubClient.of(anonymous(), endpoint="https://hub.example.invalid")

    assert hub.endpoint == "https://hub.example.invalid"
    assert hub.api.endpoint == "https://hub.example.invalid"


# --------------------------------------------------------------------------- #
# whoami
# --------------------------------------------------------------------------- #


def test_an_anonymous_run_does_not_ask_who_it_is():
    # There is nothing to ask about, and asking would be a Hub round trip that
    # tells the operator nothing.
    api = FakeApi()

    identity = client(api).whoami()

    assert identity.name == "anonymous"
    assert not identity.authenticated
    assert api.calls == []


def test_an_authenticated_run_reports_the_account_the_hub_names():
    identity = client(FakeApi(), authenticated()).whoami()

    assert identity.name == "hfcache-service"
    assert identity.authenticated
    assert identity.as_payload() == {"authenticated": True, "name": "hfcache-service"}


def test_a_failed_whoami_is_a_coded_problem():
    api = FakeApi(raises=http_error(401))

    with pytest.raises(SynchronizationError) as caught:
        client(api, authenticated()).whoami()

    assert codes(caught.value.problems) == ["HFHUB001"]
    assert caught.value.exit_code == ExitCode.SYNC


# --------------------------------------------------------------------------- #
# Resolving a repository
# --------------------------------------------------------------------------- #


def test_a_repository_resolves_to_facts_this_application_owns():
    facts = client(FakeApi(info=Info(last_modified=datetime(2026, 7, 24, tzinfo=UTC)))).repository(
        MODEL, "main"
    )

    assert facts.commit_sha == SHA
    assert facts.identity == MODEL
    assert facts.last_modified == "2026-07-24T00:00:00+00:00"


def test_the_requested_revision_reaches_the_hub_verbatim():
    api = FakeApi()

    client(api).repository(MODEL, "v2.0")

    assert api.calls[0]["revision"] == "v2.0"
    assert api.calls[0]["repo_id"] == "organization/model-name"
    assert api.calls[0]["repo_type"] == "model"


def test_facts_render_for_the_envelope():
    payload = client(FakeApi()).repository(MODEL, "main").as_payload()

    assert payload["commit_sha"] == SHA
    assert payload["repository_id"] == "organization/model-name"
    assert payload["repository_type"] == "model"


@pytest.mark.parametrize("returned", [None, "", "0123456", "not-a-sha", "0" * 39])
def test_a_response_without_a_full_commit_sha_is_hfhub007(returned):
    # Every path, manifest, and reference is keyed by the full SHA, and an
    # abbreviation never reaches disk.
    api = FakeApi(info=Info(sha=returned))

    with pytest.raises(SynchronizationError) as caught:
        client(api).repository(MODEL, "main")

    assert codes(caught.value.problems) == ["HFHUB007"]


# --------------------------------------------------------------------------- #
# What schema version 1 refuses
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(("private", "gated"), [(True, False), (False, True), (True, True)])
def test_private_and_gated_repositories_are_refused(private, gated):
    api = FakeApi(info=Info(private=private, gated=gated))

    with pytest.raises(SynchronizationError) as caught:
        client(api).repository(MODEL, "main")

    assert codes(caught.value.problems) == ["HFHUB006"]
    assert "not an archive" in caught.value.problems[0].message


def test_a_public_repository_is_accepted():
    facts = RepositoryFacts(identity=MODEL, commit_sha=CommitSha(SHA), private=False, gated=False)

    assert access_problems(facts) == []


# --------------------------------------------------------------------------- #
# Every library exception becomes one code
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("exception", "code"),
    [
        (gated("gated"), "HFHUB006"),
        (absent("absent"), "HFHUB004"),
        (no_revision("no such revision"), "HFHUB007"),
        (http_error(404), "HFHUB004"),
        (http_error(403), "HFHUB005"),
        (http_error(429), "HFHUB010"),
        (http_error(500), "HFHUB001"),
        (http_error(503), "HFHUB001"),
        (OSError("connection reset"), "HFHUB001"),
        (TimeoutError("timed out"), "HFHUB001"),
    ],
)
def test_each_library_failure_maps_to_its_documented_code(exception, code):
    # `GatedRepoError` and `RepositoryNotFoundError` are both `HfHubHTTPError`
    # subclasses, so this also pins the order the specific cases are matched in.
    assert hub_problem(exception, identity=MODEL).code == code


def test_a_problem_names_the_repository_it_is_about():
    problem = hub_problem(absent("absent"), identity=MODEL)

    assert problem.location == "model:organization/model-name"
    assert "model:organization/model-name" in problem.message


def test_a_problem_without_a_repository_still_reads_well():
    # `whoami` has no repository to name.
    problem = hub_problem(absent("absent"))

    assert problem.location is None
    assert "the repository" in problem.message


def test_a_repository_failure_reaches_the_caller_as_one_coded_error():
    api = FakeApi(raises=absent("absent"))

    with pytest.raises(SynchronizationError) as caught:
        client(api).repository(MODEL, "main")

    assert codes(caught.value.problems) == ["HFHUB004"]


# --------------------------------------------------------------------------- #
# Tree listings
# --------------------------------------------------------------------------- #


def test_a_tree_listing_becomes_sorted_typed_entries():
    # `docs/architecture.md` §5.3: every generated array is byte-wise ascending
    # on the relative path, so two runs produce the same bytes.
    entries = tree_entries([Entry("z.json", 3), Entry("a.bin", 1024), Entry("m.txt", 7)])

    assert [entry.path for entry in entries] == ["a.bin", "m.txt", "z.json"]
    assert entries[0].size == 1024


def test_directories_are_dropped_from_a_tree_listing():
    # A directory has no size; the path grammar reconstructs containers on its
    # own from the files inside them.
    entries = tree_entries([Entry("nested", size=None), Entry("nested/model.bin", 8)])

    assert [entry.path for entry in entries] == ["nested/model.bin"]


def test_an_empty_tree_is_an_empty_tuple():
    assert tree_entries([]) == ()
