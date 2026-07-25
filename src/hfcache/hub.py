"""The only place `huggingface_hub` is called, and the only place it is caught.

Plan §12 asks for a narrow adapter over the public API, injectable so tests can
use deterministic fakes rather than mock library internals. That narrowness is
a safety property, not a style preference:

* **Nothing above this module sees a library object.** Storage, retention, and
  verification receive `RepositoryFacts`, `TreeEntry`, and `CommitSha` — types
  this application owns. A `huggingface_hub` upgrade that changes a response
  shape breaks here, loudly, rather than somewhere that writes to the archive.

* **Every call passes `token=` explicitly.** Never `None`, which re-enables
  implicit discovery inside the library and would let a developer's cached
  credential silently change what a production run does (plan §12,
  `docs/security.md` T-07). Anonymous means `token=False`.

* **Every exception becomes a coded problem.** The library raises a dozen
  different types for conditions an operator experiences as three or four, and
  translating them once here is what lets the rest of the application reason
  about `HFHUB###` codes instead of about someone else's exception hierarchy.

* **Private and gated repositories are refused** in schema version 1
  (`HFHUB006`), before any content is fetched. An archive of content the
  operator may lose access to is not an archive.

Nothing here executes repository code, instantiates a model or a builder, or
shells out to `hf`, `git`, or `git-lfs` (plan §12, `NG-*`). The Hub is a source
of *files and metadata* and is treated as nothing else.
"""

import socket
import ssl
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Final, Protocol, Self, final
from urllib.parse import urlsplit

from huggingface_hub import HfApi
from huggingface_hub.errors import (
    GatedRepoError,
    HfHubHTTPError,
    RepositoryNotFoundError,
    RevisionNotFoundError,
)

from hfcache.errors import Problem, SynchronizationError
from hfcache.identity import CommitSha, parse_commit_sha

if TYPE_CHECKING:
    from collections.abc import Sequence

    from hfcache.credentials import ResolvedToken
    from hfcache.identity import RepositoryIdentity

__all__ = [
    "CONNECT_TIMEOUT_SECONDS",
    "FORBIDDEN",
    "NOT_FOUND",
    "RATE_LIMITED",
    "TLS_PORT",
    "HubClient",
    "HubIdentity",
    "RepositoryFacts",
    "TreeEntry",
    "access_problems",
    "endpoint_host",
    "hub_problem",
    "identity_problems",
    "resolve_host",
    "tree_entries",
    "verify_tls",
]

NOT_FOUND: Final = 404
FORBIDDEN: Final = 403
RATE_LIMITED: Final = 429


@final
@dataclass(frozen=True, slots=True)
class HubIdentity:
    """Who the Hub says this run is, from `whoami` (plan §12 item 1)."""

    name: str
    authenticated: bool

    def as_payload(self) -> dict[str, Any]:
        """Render for a `--json` payload. The name, never the credential."""
        return {"authenticated": self.authenticated, "name": self.name}


@final
@dataclass(frozen=True, slots=True)
class TreeEntry:
    """One file the Hub says a revision contains.

    `size` is the Hub's claim about the file and is used only for estimation
    (plan §13.2 step 3). It never becomes a manifest's expected size: that comes
    from hashing the bytes that actually landed (`AD-18`).
    """

    path: str
    size: int


@final
@dataclass(frozen=True, slots=True)
class RepositoryFacts:
    """What one repository revision is, in this application's own terms.

    Deliberately not the library's `ModelInfo`: everything above this module
    works with these fields, so a library response shape can change without
    reaching code that writes to the archive.
    """

    identity: RepositoryIdentity
    commit_sha: CommitSha
    private: bool
    gated: bool
    last_modified: str | None = None

    def as_payload(self) -> dict[str, Any]:
        """Render for a `--json` payload."""
        return {
            "commit_sha": self.commit_sha,
            "last_modified": self.last_modified,
            "repository_id": self.identity.id,
            "repository_type": self.identity.type,
        }


class HubApi(Protocol):
    """The slice of `HfApi` this adapter uses.

    A protocol rather than the class, so a test supplies an object with these
    methods and no library machinery at all. That is what plan §12 means by
    "deterministic fakes without mocking library internals": the seam is an
    interface this application defines, not a patched attribute on someone
    else's module.

    `token` is typed as `HfApi` types it rather than as `str | Literal[False]`:
    the invariant this application enforces is that it is always *passed*, which
    `ResolvedToken.hub_argument` guarantees by never returning `None`.
    """

    endpoint: str
    """Where this client points. Read back so a test can prove the wiring."""

    # `FBT001` is right in general and wrong here: this signature is `HfApi`'s,
    # not one this application chose, and narrowing it would stop the real client
    # from satisfying the protocol.
    def whoami(self, token: str | bool | None = None) -> dict[Any, Any]:  # noqa: FBT001
        ...

    def repo_info(
        self,
        repo_id: str,
        *,
        repo_type: str,
        revision: str,
        token: str | bool | None = None,
    ) -> Any:  # noqa: ANN401 - a library response, narrowed to `RepositoryFacts` by `_facts`
        ...


def hub_problem(exc: Exception, *, identity: RepositoryIdentity | None = None) -> Problem:
    """Translate one library exception into the code an operator acts on.

    The ordering matters. `GatedRepoError` and `RepositoryNotFoundError` are both
    `HfHubHTTPError` subclasses, so the specific cases are matched first; a bare
    HTTP error is classified by status, and anything else is a transport failure,
    which from here is indistinguishable from the endpoint being unreachable.
    """
    where = identity.selector if identity else None
    if isinstance(exc, GatedRepoError):
        message = (
            f"{where or 'the repository'} is gated; schema version 1 archives public content "
            f"only, because access that can be revoked is not an archive"
        )
        return Problem(code="HFHUB006", message=message, location=where)
    if isinstance(exc, RepositoryNotFoundError):
        message = f"{where or 'the repository'} was not found on the Hub"
        return Problem(code="HFHUB004", message=message, location=where)
    if isinstance(exc, RevisionNotFoundError):
        message = f"the requested revision of {where or 'the repository'} could not be resolved"
        return Problem(code="HFHUB007", message=message, location=where)
    if isinstance(exc, HfHubHTTPError):
        return _http_problem(exc, where)
    message = f"the Hub could not be reached: {type(exc).__name__}: {exc}"
    return Problem(code="HFHUB001", message=message, location=where)


def _http_problem(exc: HfHubHTTPError, where: str | None) -> Problem:
    """Classify an HTTP failure by status, defaulting to unreachable.

    `HfHubHTTPError` requires a response to construct, so a status is always
    present; it is read defensively anyway, because this is the one place where
    being wrong about the library's shape would mean reporting the wrong code to
    an operator.
    """
    status = getattr(getattr(exc, "response", None), "status_code", None)
    if status == NOT_FOUND:
        return Problem(
            code="HFHUB004",
            message=f"{where or 'the repository'} was not found on the Hub",
            location=where,
        )
    if status == FORBIDDEN:
        return Problem(
            code="HFHUB005",
            message=f"access to {where or 'the repository'} was forbidden by the Hub",
            location=where,
        )
    if status == RATE_LIMITED:
        message = (
            "the Hub rate-limited this run after the built-in retry budget was exhausted; "
            "the next scheduled run will resume from the same place"
        )
        return Problem(code="HFHUB010", message=message, location=where)
    message = f"the Hub returned {status}: {exc}"
    return Problem(code="HFHUB001", message=message, location=where)


@final
@dataclass(frozen=True, slots=True)
class HubClient:
    """Every Hub call this application makes.

    `token` is a `ResolvedToken` rather than a string, because the invariant that
    matters is not "the token is right" but "`token=` is always passed
    explicitly". `ResolvedToken.hub_argument` returns `False` for anonymous and
    never `None`, so implicit discovery cannot be reached from here.
    """

    api: HubApi
    token: ResolvedToken
    endpoint: str = "https://huggingface.co"

    @classmethod
    def of(cls, token: ResolvedToken, *, endpoint: str) -> Self:
        """Build a client over the real `HfApi` for a configured endpoint."""
        return cls(api=HfApi(endpoint=endpoint), token=token, endpoint=endpoint)

    def whoami(self) -> HubIdentity:
        """Ask the Hub who this run is (plan §12 item 1).

        Anonymous access is a valid answer, not a failure: `token_mode =
        "optional"` means a missing credential is normal, and an anonymous run
        can archive public content perfectly well.
        """
        if not self.token.has_token:
            return HubIdentity(name="anonymous", authenticated=False)
        try:
            response = self.api.whoami(token=self.token.hub_argument)
        except Exception as exc:
            raise SynchronizationError([hub_problem(exc)]) from exc
        return HubIdentity(name=str(response.get("name", "")), authenticated=True)

    def repository(self, identity: RepositoryIdentity, revision: str) -> RepositoryFacts:
        """Resolve one repository reference to facts this application owns.

        Refuses private and gated content before anything is fetched
        (`HFHUB006`): an archive of content whose access can be revoked is not
        an archive, and finding that out after a download is finding out too
        late.
        """
        try:
            info = self.api.repo_info(
                identity.id,
                repo_type=identity.type,
                revision=revision,
                token=self.token.hub_argument,
            )
        except Exception as exc:
            raise SynchronizationError([hub_problem(exc, identity=identity)]) from exc

        facts = _facts(identity, info)
        if problems := access_problems(facts):
            raise SynchronizationError(problems)
        return facts


def _facts(identity: RepositoryIdentity, info: object) -> RepositoryFacts:
    """Read the fields this application needs out of one library response.

    A missing or unresolvable `sha` is `HFHUB007` rather than an attribute
    error: it is the one field the whole design depends on, since every path,
    manifest, and reference is keyed by the full commit SHA and an abbreviation
    never reaches disk.
    """
    raw = getattr(info, "sha", None)
    try:
        commit_sha = parse_commit_sha(raw, code="HFHUB007")
    except ValueError as exc:
        message = (
            f"the Hub did not return a full commit SHA for {identity.selector}: {exc}. "
            f"Every path and manifest is keyed by it, and an abbreviation never reaches disk"
        )
        raise SynchronizationError.single(
            message, code="HFHUB007", location=identity.selector
        ) from exc
    modified = getattr(info, "last_modified", None)
    return RepositoryFacts(
        identity=identity,
        commit_sha=commit_sha,
        private=bool(getattr(info, "private", False)),
        gated=bool(getattr(info, "gated", False)),
        last_modified=modified.isoformat() if modified is not None else None,
    )


def access_problems(facts: RepositoryFacts) -> list[Problem]:
    """Refuse content schema version 1 does not archive (`HFHUB006`).

    Separated from the call so the policy is testable without a Hub, and so the
    reason is stated once: private and gated repositories can have access
    withdrawn, and an archive whose contents depend on a grant that may be
    revoked is not doing the job it exists for.
    """
    if not (facts.private or facts.gated):
        return []
    kind = "private" if facts.private else "gated"
    message = (
        f"{facts.identity.selector} is {kind}; schema version 1 archives public content only, "
        f"because access that can be withdrawn is not an archive"
    )
    return [Problem(code="HFHUB006", message=message, location=facts.identity.selector)]


def tree_entries(raw: Sequence[object]) -> tuple[TreeEntry, ...]:
    """Normalize a repository tree listing into this application's own type.

    Directories are dropped: the archive publishes files, and a directory in the
    listing is a container the path grammar reconstructs on its own.
    """
    entries = [
        TreeEntry(path=str(getattr(item, "path", "")), size=int(getattr(item, "size", 0) or 0))
        for item in raw
        if getattr(item, "size", None) is not None
    ]
    return tuple(sorted(entries, key=lambda entry: entry.path))


# --------------------------------------------------------------------------- #
# Reachability (`doctor` checks 15-17)
# --------------------------------------------------------------------------- #

TLS_PORT: Final = 443
CONNECT_TIMEOUT_SECONDS: Final = 10.0
"""Long enough for a slow network, short enough that `doctor` still answers.

`doctor` is what an operator runs when something is already wrong, so it must
finish. A scheduled sync has its own retry budget and does not depend on this.
"""


def endpoint_host(endpoint: str) -> str:
    """The host `hub.endpoint` names.

    Configuration has already proven the endpoint is a well-formed `https://`
    URL (`HFCFG014`), so this parses rather than validates.
    """
    return urlsplit(endpoint).hostname or ""


def resolve_host(host: str) -> tuple[str, ...]:
    """Resolve a hostname, or report `HFHUB001`.

    DNS is separated from the TLS connection because they fail for unrelated
    reasons and an operator fixes them in different places: one is a resolver or
    a search domain, the other a certificate, a proxy, or a firewall.
    """
    try:
        infos = socket.getaddrinfo(host, TLS_PORT, proto=socket.IPPROTO_TCP)
    except OSError as exc:
        message = f"{host} did not resolve: {exc.strerror or exc}"
        raise SynchronizationError.single(message, code="HFHUB001", location=host) from exc
    return tuple(sorted({str(info[4][0]) for info in infos}))


def verify_tls(
    host: str,
    *,
    port: int = TLS_PORT,
    timeout: float = CONNECT_TIMEOUT_SECONDS,
    context: ssl.SSLContext | None = None,
) -> str:
    """Connect and verify the certificate, or report `HFHUB002`.

    Verification is the default context's, with hostname checking on: the point
    is to prove the deployment's trust store and clock agree with the Hub's
    certificate, and a check that disabled verification would prove nothing.

    `context` and `port` exist so a test can perform a *real* handshake against a
    local server with its own certificate authority. Injecting the trust anchor
    rather than the answer is what keeps the test honest — the code under test
    still verifies, it simply verifies against a CA the test created.
    """
    verifier = ssl.create_default_context() if context is None else context
    try:
        with (
            socket.create_connection((host, port), timeout=timeout) as raw,
            verifier.wrap_socket(raw, server_hostname=host) as secured,
        ):
            certificate = secured.getpeercert() or {}
            version = secured.version() or "unknown"
    except (OSError, ssl.SSLError) as exc:
        message = f"the TLS connection to {host} could not be verified: {exc}"
        raise SynchronizationError.single(message, code="HFHUB002", location=host) from exc
    return f"{version}, certificate valid until {certificate.get('notAfter', 'unknown')}"


def identity_problems(identity: HubIdentity, expected_account: str) -> list[Problem]:
    """Refuse a run whose Hub identity is not the one configured (`HFHUB003`).

    Only checked when `hub.expected_account` is set, which is what makes it
    optional. It exists so a credential swapped by mistake is caught before a
    scheduled run archives content under the wrong account's rate limits and
    permissions, rather than after.
    """
    if not expected_account or identity.name == expected_account:
        return []
    message = (
        f"the Hub reports this run as {identity.name!r}, but hub.expected_account is "
        f"{expected_account!r}; the credential in use is not the one configured"
    )
    return [Problem(code="HFHUB003", message=message, location="hub.expected_account")]
