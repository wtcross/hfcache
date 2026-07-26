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
from typing import TYPE_CHECKING, Any

import httpx
import pytest
from huggingface_hub.errors import (
    GatedRepoError,
    HfHubHTTPError,
    IncompleteSnapshotError,
    RepositoryNotFoundError,
    RevisionNotFoundError,
)

from hfcache.credentials import ResolvedToken, TokenSource
from hfcache.errors import ExitCode, SynchronizationError
from hfcache.hub import (
    HubClient,
    HubIdentity,
    RepositoryFacts,
    access_problems,
    download_estimate,
    endpoint_host,
    hub_problem,
    identity_problems,
    resolve_host,
    tree_entries,
    verify_tls,
)
from hfcache.identity import CommitSha, RepositoryIdentity

if TYPE_CHECKING:
    from pathlib import Path

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
class DryRunEntry:
    """One record of a `snapshot_download(dry_run=True)` result."""

    filename: str
    file_size: int
    will_download: bool = True


@dataclass
class FakeApi:
    """A `HubApi` with no library machinery, recording how it was called."""

    info: Any = field(default_factory=Info)
    identity: dict[str, Any] = field(default_factory=lambda: {"name": "hfcache-service"})
    tree: Any = field(default_factory=list)
    dry_run_result: Any = None
    snapshot: Any = None
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

    def list_repo_tree(self, repo_id: str, **arguments: Any) -> Any:
        # A generator, like the library's: the request is made during iteration,
        # so a failure has to be raised there rather than at the call.
        self.calls.append({"method": "list_repo_tree", "repo_id": repo_id, **arguments})

        def listing():
            if self.raises is not None:
                raise self.raises
            yield from self.tree

        return listing()

    def snapshot_download(self, repo_id: str, **arguments: Any) -> Any:
        self.calls.append({"method": "snapshot_download", "repo_id": repo_id, **arguments})
        if self.raises is not None:
            raise self.raises
        if arguments.get("dry_run"):
            return self.dry_run_result if self.dry_run_result is not None else []
        return self.snapshot


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
    # Not a refusal: "this revision has no files" is a truthful answer to what
    # the metadata call asked, and whether such a revision is worth publishing
    # belongs to the package that publishes one.
    assert tree_entries([]) == ()


def test_upstream_identifiers_are_read_off_the_listing():
    # Comparison values for the manifest (plan §10.1), never digests.
    @dataclass
    class Lfs:
        sha256: str

    @dataclass
    class Rich:
        path: str
        size: int
        blob_id: str
        lfs: object
        xet_hash: str

    entries = tree_entries([Rich("model.bin", 8, "a" * 40, Lfs("b" * 64), "c" * 64)])

    assert entries[0].git_oid == "a" * 40
    assert entries[0].lfs_sha256 == "b" * 64
    assert entries[0].xet_hash == "c" * 64


def test_an_absent_identifier_is_none_and_never_the_string_none():
    # `lfs` is absent on a small file and `xet_hash` on a repository not using
    # Xet, so the absent case is the common one.
    entries = tree_entries([Entry("config.json", 2)])

    assert (entries[0].git_oid, entries[0].lfs_sha256, entries[0].xet_hash) == (None, None, None)


def test_a_file_entry_with_no_path_is_hfhub008():
    # The listing is the exact path set every later step joins onto a filesystem
    # path; an empty name would reach that join looking legitimate.
    with pytest.raises(SynchronizationError) as caught:
        tree_entries([Entry("model.bin", 8), Entry("", 4)], identity=MODEL)

    assert codes(caught.value.problems) == ["HFHUB008"]
    assert caught.value.problems[0].location == MODEL.selector


def test_a_file_entry_with_no_path_reports_without_an_identity():
    with pytest.raises(SynchronizationError) as caught:
        tree_entries([Entry("", 4)])

    assert caught.value.problems[0].location is None
    assert "the repository" in caught.value.problems[0].message


def test_the_tree_is_listed_recursively_against_the_resolved_sha():
    # Against the SHA rather than the reference: a moving branch could enumerate
    # one commit and download the next.
    api = FakeApi(tree=[Entry("nested/model.bin", 8), Entry("README.md", 2)])

    entries = client(api).tree(MODEL, CommitSha(SHA))

    call = api.calls[-1]
    assert call["method"] == "list_repo_tree"
    assert call["revision"] == SHA
    assert call["recursive"] is True
    assert call["repo_type"] == "model"
    assert call["token"] is False
    assert [entry.path for entry in entries] == ["README.md", "nested/model.bin"]


def test_a_tree_listing_that_fails_during_iteration_is_a_coded_problem():
    # `list_repo_tree` returns a generator, so the request happens while the
    # listing is drained. Draining outside the `try` would let the library's own
    # exception escape instead of a coded problem.
    api = FakeApi(raises=absent("gone"))

    with pytest.raises(SynchronizationError) as caught:
        client(api).tree(MODEL, CommitSha(SHA))

    assert codes(caught.value.problems) == ["HFHUB004"]


# --------------------------------------------------------------------------- #
# Download estimation
# --------------------------------------------------------------------------- #


def test_an_estimate_separates_what_the_revision_is_from_what_would_be_fetched():
    estimate = download_estimate(
        [
            DryRunEntry("model.bin", 1000, will_download=True),
            DryRunEntry("config.json", 24, will_download=False),
        ]
    )

    assert estimate.file_count == 2
    assert estimate.logical_bytes == 1024
    assert estimate.new_bytes == 1000
    assert estimate.cached_bytes == 24


def test_a_fully_cached_revision_estimates_no_new_bytes():
    # The second sync of an unchanged repository: large logically, free to fetch.
    estimate = download_estimate([DryRunEntry("model.bin", 1000, will_download=False)])

    assert estimate.logical_bytes == 1000
    assert estimate.new_bytes == 0
    assert estimate.cached_bytes == 1000


def test_an_empty_dry_run_estimates_nothing():
    estimate = download_estimate([])

    assert (estimate.file_count, estimate.logical_bytes, estimate.new_bytes) == (0, 0, 0)


def test_the_estimate_is_a_dry_run_against_the_cache_the_download_would_write(tmp_path):
    # The same explicit cache path a real download gets: an estimate against a
    # different cache would report bytes as new that the sync would have reused.
    api = FakeApi(dry_run_result=[DryRunEntry("model.bin", 512)])

    estimate = client(api).estimate(MODEL, CommitSha(SHA), cache_dir=tmp_path, max_workers=4)

    call = api.calls[-1]
    assert call["method"] == "snapshot_download"
    assert call["dry_run"] is True
    assert call["cache_dir"] == str(tmp_path)
    assert call["revision"] == SHA
    assert call["repo_type"] == "model"
    assert call["max_workers"] == 4
    assert call["token"] is False
    assert estimate.new_bytes == 512


def test_no_allow_or_ignore_filters_are_ever_passed(tmp_path):
    # The product contract is repository-complete (plan §12 item 4), so an
    # estimate over a subset would estimate the wrong thing.
    api = FakeApi(dry_run_result=[])

    client(api).estimate(MODEL, CommitSha(SHA), cache_dir=tmp_path, max_workers=1)

    assert "allow_patterns" not in api.calls[-1]
    assert "ignore_patterns" not in api.calls[-1]


def test_an_estimate_that_did_not_return_file_records_is_hfhub009(tmp_path):
    # `dry_run=True` is what keeps this call from downloading. A result shaped
    # like a completed download means the flag did not take effect, so it is
    # refused rather than interpreted.
    api = FakeApi(dry_run_result="/some/snapshot/path")

    with pytest.raises(SynchronizationError) as caught:
        client(api).estimate(MODEL, CommitSha(SHA), cache_dir=tmp_path, max_workers=1)

    assert codes(caught.value.problems) == ["HFHUB009"]


def test_an_estimate_failure_is_a_coded_problem(tmp_path):
    api = FakeApi(raises=absent("gone"))

    with pytest.raises(SynchronizationError) as caught:
        client(api).estimate(MODEL, CommitSha(SHA), cache_dir=tmp_path, max_workers=1)

    assert codes(caught.value.problems) == ["HFHUB004"]


# --------------------------------------------------------------------------- #
# Downloading a revision (plan §13.2 step 5)
# --------------------------------------------------------------------------- #


def snapshot_in(cache: Path, name: str = "snapshots/" + SHA) -> Path:
    """A directory inside a cache root, the way a completed download leaves one."""
    path = cache / name
    path.mkdir(parents=True)
    return path


def test_a_download_passes_every_argument_plan_12_requires_be_explicit(tmp_path):
    cache = tmp_path / "hub"
    snapshot = snapshot_in(cache)
    api = FakeApi(snapshot=str(snapshot))

    local = client(api).download(MODEL, CommitSha(SHA), cache_dir=cache, max_workers=4)

    call = api.calls[-1]
    assert call["repo_id"] == "organization/model-name"
    assert call["repo_type"] == "model"
    assert call["revision"] == SHA
    assert call["cache_dir"] == str(cache)
    assert call["max_workers"] == 4
    assert call["token"] is False
    assert call["dry_run"] is False
    assert local == snapshot.resolve()


def test_a_download_never_passes_allow_or_ignore_filters(tmp_path):
    # There is no supported way to archive part of a repository, so there is no
    # argument that would express one.
    cache = tmp_path / "hub"
    api = FakeApi(snapshot=str(snapshot_in(cache)))

    client(api).download(MODEL, CommitSha(SHA), cache_dir=cache, max_workers=1)

    assert "allow_patterns" not in api.calls[-1]
    assert "ignore_patterns" not in api.calls[-1]


def test_a_download_is_pinned_to_the_sha_not_the_reference_that_produced_it(tmp_path):
    cache = tmp_path / "hub"
    api = FakeApi(snapshot=str(snapshot_in(cache)))

    client(api).download(MODEL, CommitSha(SHA), cache_dir=cache, max_workers=1)

    assert api.calls[-1]["revision"] == SHA


def test_a_snapshot_reached_through_a_symlink_resolves_inside_the_cache(tmp_path):
    # The cache reaches its snapshots through symlinks by design, so the path is
    # resolved before it is compared rather than refused for being one.
    cache = tmp_path / "hub"
    snapshot = snapshot_in(cache)
    link = cache / "link"
    link.symlink_to(snapshot)
    api = FakeApi(snapshot=str(link))

    assert client(api).download(MODEL, CommitSha(SHA), cache_dir=cache, max_workers=1) == snapshot


@pytest.mark.parametrize("returned", [None, "", 7], ids=["none", "empty", "not-a-string"])
def test_a_download_that_returned_no_path_is_hfhub009(tmp_path, returned):
    cache = tmp_path / "hub"
    cache.mkdir()
    api = FakeApi(snapshot=returned)

    with pytest.raises(SynchronizationError) as caught:
        client(api).download(MODEL, CommitSha(SHA), cache_dir=cache, max_workers=1)

    assert codes(caught.value.problems) == ["HFHUB009"]


def test_a_snapshot_that_is_not_there_is_hfhub009(tmp_path):
    # A snapshot that cannot be resolved was not downloaded, whatever the
    # library returned.
    cache = tmp_path / "hub"
    cache.mkdir()
    api = FakeApi(snapshot=str(cache / "snapshots" / SHA))

    with pytest.raises(SynchronizationError) as caught:
        client(api).download(MODEL, CommitSha(SHA), cache_dir=cache, max_workers=1)

    assert codes(caught.value.problems) == ["HFHUB009"]


def test_a_snapshot_outside_the_cache_root_is_hfhub009(tmp_path):
    # `FS-15`: every source the archive publishes from is *shown* contained, and
    # a value that came from a library gets the same proof as one that came from
    # a repository.
    cache = tmp_path / "hub"
    cache.mkdir()
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    api = FakeApi(snapshot=str(elsewhere))

    with pytest.raises(SynchronizationError) as caught:
        client(api).download(MODEL, CommitSha(SHA), cache_dir=cache, max_workers=1)

    assert codes(caught.value.problems) == ["HFHUB009"]
    assert "outside the private cache root" in caught.value.problems[0].message


def test_a_snapshot_that_is_not_a_directory_is_hfhub009(tmp_path):
    cache = tmp_path / "hub"
    cache.mkdir()
    regular = cache / "not-a-tree"
    regular.write_text("", encoding="utf-8")
    api = FakeApi(snapshot=str(regular))

    with pytest.raises(SynchronizationError) as caught:
        client(api).download(MODEL, CommitSha(SHA), cache_dir=cache, max_workers=1)

    assert codes(caught.value.problems) == ["HFHUB009"]


def test_a_download_failure_is_a_coded_problem(tmp_path):
    api = FakeApi(raises=absent("gone"))

    with pytest.raises(SynchronizationError) as caught:
        client(api).download(MODEL, CommitSha(SHA), cache_dir=tmp_path, max_workers=1)

    assert codes(caught.value.problems) == ["HFHUB004"]


# --------------------------------------------------------------------------- #
# The local-only completeness check (plan §12 item 5, §13.2 step 6)
# --------------------------------------------------------------------------- #


def test_the_local_check_asks_the_library_to_work_without_the_network(tmp_path):
    cache = tmp_path / "hub"
    snapshot = snapshot_in(cache)
    api = FakeApi(snapshot=str(snapshot))

    local = client(api).verify_local(MODEL, CommitSha(SHA), cache_dir=cache)

    call = api.calls[-1]
    assert call["local_files_only"] is True
    assert call["dry_run"] is False
    assert call["revision"] == SHA
    assert call["cache_dir"] == str(cache)
    assert local == snapshot.resolve()


def test_the_local_check_parallelizes_nothing(tmp_path):
    # Nothing is fetched, so there is nothing to fetch concurrently.
    cache = tmp_path / "hub"
    api = FakeApi(snapshot=str(snapshot_in(cache)))

    client(api).verify_local(MODEL, CommitSha(SHA), cache_dir=cache)

    assert api.calls[-1]["max_workers"] == 1


def test_a_cache_that_can_no_longer_assemble_the_revision_is_hfsyn001(tmp_path):
    # The download reported success, so the bytes were there and now are not.
    cache = tmp_path / "hub"
    cache.mkdir()
    # The genuine article, constructed the way the library constructs it, so the
    # classification is tested against the exception it actually raises.
    api = FakeApi(raises=IncompleteSnapshotError("model.bin is missing", str(cache)))

    with pytest.raises(SynchronizationError) as caught:
        client(api).verify_local(MODEL, CommitSha(SHA), cache_dir=cache)

    assert codes(caught.value.problems) == ["HFSYN001"]
    assert caught.value.exit_code == ExitCode.SYNC


def test_the_local_check_reports_its_own_code_not_the_downloads(tmp_path):
    # The same observation — no usable snapshot — means something different
    # depending on which step noticed it.
    cache = tmp_path / "hub"
    cache.mkdir()
    api = FakeApi(snapshot=None)

    with pytest.raises(SynchronizationError) as caught:
        client(api).verify_local(MODEL, CommitSha(SHA), cache_dir=cache)

    assert codes(caught.value.problems) == ["HFSYN001"]


# --------------------------------------------------------------------------- #
# Reachability (`doctor` checks 15-17)
# --------------------------------------------------------------------------- #


def test_the_endpoint_host_is_read_out_of_the_configured_url():
    # Configuration already proved it is a well-formed https URL (`HFCFG014`),
    # so this parses rather than validates.
    assert endpoint_host("https://huggingface.co") == "huggingface.co"
    assert endpoint_host("https://hub.example.test:8443/prefix") == "hub.example.test"


def test_a_resolvable_host_reports_its_addresses():
    # `localhost` resolves from `/etc/hosts`, so this needs no network.
    addresses = resolve_host("localhost")

    assert addresses
    assert all(isinstance(address, str) for address in addresses)


def test_a_host_that_does_not_resolve_is_hfhub001(monkeypatch: pytest.MonkeyPatch):
    def refuse(*args, **kwargs):
        raise OSError(-2, "Name or service not known")

    monkeypatch.setattr("hfcache.hub.socket.getaddrinfo", refuse)

    with pytest.raises(SynchronizationError) as caught:
        resolve_host("no-such-host.invalid")

    assert codes(caught.value.problems) == ["HFHUB001"]


def test_a_connection_that_cannot_be_made_is_hfhub002(monkeypatch: pytest.MonkeyPatch):
    def refuse(*args, **kwargs):
        raise OSError(111, "Connection refused")

    monkeypatch.setattr("hfcache.hub.socket.create_connection", refuse)

    with pytest.raises(SynchronizationError) as caught:
        verify_tls("localhost")

    assert codes(caught.value.problems) == ["HFHUB002"]


def test_a_certificate_that_does_not_verify_is_hfhub002(tls_server):
    # The same local server, verified against the *default* trust store, which
    # has never heard of its certificate authority. The code under test is doing
    # real verification and correctly refusing.
    _, port, _ = tls_server

    with pytest.raises(SynchronizationError) as caught:
        verify_tls("localhost", port=port)

    assert codes(caught.value.problems) == ["HFHUB002"]


def test_a_certificate_that_verifies_reports_the_protocol_and_expiry(tls_server):
    # A real handshake against a real server. Only the trust anchor is injected,
    # not the answer: the code under test still verifies, against a certificate
    # authority this test created.
    _, port, trust = tls_server

    detail = verify_tls("localhost", port=port, context=trust)

    assert "TLS" in detail
    assert "certificate valid until" in detail


# --------------------------------------------------------------------------- #
# The configured identity
# --------------------------------------------------------------------------- #


def test_an_unset_expected_account_verifies_nothing():
    assert identity_problems(HubIdentity(name="anyone", authenticated=True), "") == []


def test_a_matching_identity_is_no_problem():
    identity = HubIdentity(name="hfcache-service", authenticated=True)

    assert identity_problems(identity, "hfcache-service") == []


def test_an_identity_that_is_not_the_configured_one_is_hfhub003():
    # A credential swapped by mistake is caught before a scheduled run archives
    # content under the wrong account, rather than after.
    identity = HubIdentity(name="somebody-else", authenticated=True)

    problems = identity_problems(identity, "hfcache-service")

    assert codes(problems) == ["HFHUB003"]
    assert problems[0].location == "hub.expected_account"
