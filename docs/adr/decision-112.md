# Decision 112 — Separate server authority and verified bearer capabilities

- Status: Accepted; implemented incrementally by API-005, with metadata-route/lifespan enforcement advanced by [decision 113](decision-113.md)
  and command authority extended by [decision 116](decision-116.md).
- Date: 2026-10-17.
- Work package: API-005, this commit.
- Source: [progress decision 112](../progress.md#decisions),
  [active plan](../plans/2026-10-17-plan-rest-api-and-mcp.md),
  [task](../plans/tasks/api-005-server-config-and-bearer-auth.md).

## Context and decision

The existing archive TOML defines what a local invocation may retain. A daemon
also needs a stable transport/authentication boundary while archive policy can
change between requests. Putting those settings into every archive configuration
would mix the operator's storage intent with management credentials and would
make client installation require server imports.

Implement separate strict, frozen, schema-1 `ServerConfig` with explicit listener,
TLS/proxy, credential-source, limits and maintenance settings. Load server
transport/authentication at startup, requiring restart to change them. Provide
`InstalledPolicy.snapshot()` to reload the installed archive policy and compute
its existing secret-free fingerprint, while pinning the server to its startup
archive root and UUID. A changed authority fails closed until restart. This
package supplies the primitive; HTTP requests and queued-lock revalidation are
wired in API-006/008. No configuration-install API is introduced.

Implement framework-independent authenticated principals and fixed REST
reader/writer capabilities. Credentials come only from explicit protected files
or named systemd credentials; required writer failure prevents startup, and an
unprovisioned optional reader grants no access. Validate source safety and
bounded token shape, reject duplicate values, register exact opaque values for
redaction and use constant-time comparisons. A nonsecret principal identifies a
configured capability class, not an individual user or a token digest. Do not
reuse or discover Hub credentials. Every authorized reader must be entitled to
all archived content under AD-21; no per-repository ACL is implied.

Keep FastAPI's bearer integration in an optional adapter, with application-owned
verification and stable 401/403 behavior. Extraction alone grants no authority.
Missing, malformed or invalid authentication is 401 with a Bearer challenge;
a valid principal lacking the required capability receives 403. Route protection,
Host/Origin/body bounds and HTTP exception translation remain API-006 work.
MCP credentials/endpoints/dependencies remain behind the REST acceptance gate.
The central taxonomy assigns exit-10 codes `HFAPI001` to authentication,
`HFAPI002` to capability denial, `HFAPI003` to unsafe/malformed/racing configured
credentials and `HFAPI004` to duplicate class values. The API token grammar
rejects Hub-style `hf_` values; group-readable files must belong to one of the
server's effective/supplementary groups. Neither rule repurposes a Hub credential.

Make `httpx` a direct base dependency and add FastAPI/Uvicorn only in `server`.
The base CLI imports without optional server packages. The gate provisions the
implemented extra instead of silently skipping its tests, and smoke-installs
both locked base/server wheels into real isolated environments. Python 3.14 lock and
installation evidence belongs to this package; no existing dependency is
upgraded merely to add this boundary.

The small `create_http_client` primitive constructs verified default/custom-CA
HTTPX transport with optional Unix sockets, no environment discovery, redirects
or transport retries, and bounded connections/timeouts. It sends no request;
endpoint/authentication/response policy remains API-011 work.

## Rationale and alternatives

The standard library supplies TOML, immutable models' supporting primitives,
safe file operations and constant-time comparison, but a handwritten HTTP/TLS,
ASGI lifecycle and bearer/OpenAPI implementation would add correctness and
security obligations already covered by maintained transports. HTTPX supports
verified TLS and Unix-socket HTTP; FastAPI provides the security-dependency and
ASGI interfaces; Uvicorn provides the HTTP/socket/lifespan host. Domain services
retain orchestration and archive authority. These are the scoped FW-04 material
correctness additions authorized by decision 108, not a workflow framework.

Reject shared API/Hub credentials, ambient discovery, literal tokens in TOML,
anonymous local-socket exemptions and implicit optional-credential fallback.
Reject a hot-switched archive root/UUID and global per-request auth mutation.
Reject user-management infrastructure or fine-grained ACL claims for this fixed
whole-archive capability boundary.

## Dependencies and official documentation

On CPython 3.14, the lock selects HTTPX `0.28.1` (already transitive, now direct),
FastAPI `0.143.3` and Uvicorn `0.54.0`. Their newly required runtime transitives
include Starlette `1.8.0` and opentelemetry-api `1.45.1`; existing locked versions
are retained. `uv.lock` is the installation authority. No FastMCP is added.

Official sources checked during API-005:

- [HTTPX SSL verification](https://www.python-httpx.org/advanced/ssl/) and
  [transport interfaces, including Unix sockets](https://www.python-httpx.org/advanced/transports/).
- [FastAPI security tools and HTTPBearer](https://fastapi.tiangolo.com/reference/security/)
  and [application lifespan](https://fastapi.tiangolo.com/advanced/events/),
  [release notes](https://fastapi.tiangolo.com/release-notes/) and the
  [locked release metadata](https://pypi.org/pypi/fastapi/0.143.3/json).
- [Uvicorn socket, TLS, worker and resource settings](https://uvicorn.dev/settings/).
- [Uvicorn release notes](https://www.uvicorn.org/release-notes/) and
  [locked release metadata](https://pypi.org/pypi/uvicorn/0.54.0/json).
- [HTTPX bounded timeouts](https://www.python-httpx.org/advanced/timeouts/)
  and [client API](https://www.python-httpx.org/api/).
- [uv project dependencies and extras](https://docs.astral.sh/uv/concepts/projects/dependencies/).
- [Python 3.14 descriptor operations](https://docs.python.org/3.14/library/os.html)
  and [constant-time comparison](https://docs.python.org/3.14/library/hmac.html).
- [RFC 6750 bearer token alphabet and header use](https://www.rfc-editor.org/rfc/rfc6750#section-2.1).

## Consequences and relationships

**API-006 amendment (2026-10-17, [decision 113](decision-113.md)).**
The deferred authenticated metadata application, transport bounds and controlled
lifespan now use the primitives above. Job/receipt execution, CLI migration,
isolated verification and deployment remain later tasks. API-005's no-listener
statement records its original scope; API-006 adds an explicit `serve` bootstrap
without claiming a production installation.

Implements part of [decision 108](decision-108.md)'s dependency boundary and
amends [FW-01–FW-04](fw-01.md)'s actual dependency set. Preserves
[AD-21](ad-21.md), [decision 111](decision-111.md)'s secret registration and
correlation rules, FS/TX, durable archive schemas and existing Hub token
semantics. Archive-policy fingerprints exclude Hub credential source metadata
and values; API credentials are outside those snapshots and no server fingerprint
format is introduced. Authentication diagnostics never echo input tokens.
Operation receipts remain
API-007 work and must store only the nonsecret principal, never token values.
No app factory, runtime REST endpoint, listener, production rollout, MCP import
or isolated verification executor is introduced.

Governing contracts: [server configuration/authentication](../server.md),
[API capabilities](../api.md), [configuration domains](../configuration.md),
[security](../security.md), and [invariants](../invariants.md).
Implementation: [server policy](../../src/hfcache/server_config.py),
[credential/capability core](../../src/hfcache/api/auth.py),
[optional FastAPI dependencies](../../src/hfcache/api/security.py),
[HTTPX factory](../../src/hfcache/http_transport.py), and
[locked isolated-install checks](../../scripts/check-installations.py).
Evidence: [strict configuration/reload/property tests](../../tests/unit/test_server_config.py),
[adversarial credential/class tests](../../tests/unit/test_server_auth_adversarial.py),
[FastAPI adapter tests](../../tests/unit/test_api_security.py),
[transport defaults](../../tests/unit/test_http_transport.py), and the green
gate recorded in the [API-005 task](../plans/tasks/api-005-server-config-and-bearer-auth.md).

## API-009 authority amendment

[Decision 116](decision-116.md) adds the trusted startup-only
`serve --hub-token-file` development option, distinct from API bearer sources and
request input. Shared services resolve only that explicit file or installed
systemd Hub authority under existing token-mode/account rules. Candidate hooks
perform pure bounded syntax/authority assessment and compare endpoint, credential
identity and archive authority before any future credential-bearing planning.
Current HTTP candidate fields remain rejected until API-012. No additional
runtime dependency, server configuration field or credential fingerprint is added.
