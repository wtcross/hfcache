# Decision 118 — Observe one API authority without replaying uncertain submissions

- Status: Accepted; implemented by API-011 on 2026-10-18.
- Date: 2026-10-17.
- Work package: API-011, this commit.
- Source: [progress decision 118](../progress.md#decisions),
  [active plan](../plans/2026-10-17-plan-rest-api-and-mcp.md),
  [task](../plans/tasks/api-011-typed-client-and-client-config.md).

## Context and decision

Implement a synchronous typed HTTP client for reader and writer hosts independently
of archive policy, mounts, Hub credentials and optional server/MCP frameworks.
Use separate strict schema-1 client TOML. Explicit CLI URL/socket selection
replaces the configured endpoint as one mutually exclusive group; otherwise use
client config, then the local Unix default. Only explicit API token-file or named
systemd sources resolve credentials, with documented precedence and no anonymous
fallback after an unusable selected source. Global CLI options are stored now;
operational command migration remains API-012/013.

Verify TLS with system/default or explicit CA trust, disable ambient proxy/netrc/
credential behavior and redirects, and refuse unsafe URLs, token query/userinfo,
endpoint escape and caller-selected off-origin response links. There is no silent
archive-filesystem fallback or automatic daemon startup. The reader needs neither
archive TOML/mount nor service identity/Hub credential.

Apply finite transport/response/page/retry/poll budgets and strict wire version,
capability, Envelope, identity and scope checks. Walk pages without silently losing
rows or substituting fresh publication identity; retain the first Envelope's
invocation metadata when reconstructing paged results. Existing report/result
run identity remains domain evidence. An operation's admitted policy fingerprint
must not be replaced by the current capabilities/policy fingerprint. Request,
operation and domain run IDs remain distinct. Unknown required capabilities or
unsupported versions refuse rather than guessing.

Generate or accept one nonsecret idempotency key before transmission and retain
it across any permitted retry. Authenticate non-submitting lookup with that same
key; missing/expired history never proves nonexecution. Any unusable post-transmission acknowledgement, including malformed/truncated
202, wrong operation identity or untrusted error body, is uncertain HFAPI020:
admission may already exist. A validated remote problem retains its taxonomy and original key/route;
pre-send validation stays config/protocol. Neither a lost POST response nor
observer timeout can cause a new-key replay, fabricate a terminal Envelope or
cancel accepted work. Poll/read retries are bounded and preserve operation
identity; a caller can deliberately inspect/continue observation later.

Central taxonomy adds HFAPI017 client configuration and HFAPI018 protocol/
compatibility at exit 10, HFAPI019 connectivity and HFAPI020 uncertain submission
at exit 20. Transport/auth/config failures remain distinct from exact domain
Envelope exits, including partial failures. Diagnostics never echo bearer values,
response bodies, token-bearing URLs or arbitrary transport exceptions.

## Rationale and alternatives

A separate reader configuration avoids forcing archive secrets/paths onto a reader
or importing optional server dependencies for local help/version. Endpoint choices
must override as a group so a configured socket cannot silently win over an
explicit remote URL. Explicit sources and verified no-redirect transport keep a
bearer bound to one intended authority.

Reject silent fallback, ambient credentials/proxies, cross-origin redirect
forwarding, guessed wire compatibility, unbounded pagination/retries and new-key
submission replay. A synchronous client fits Typer's command lifecycle without
creating a second event loop, domain engine, scheduler or writer authority.

## Consequences and relationships

Implements the client portion of [108](decision-108.md)/[112](decision-112.md)
and the retained-key observation boundary of [109](decision-109.md)/
[114](decision-114.md). Preserves INV-001–003/006/008/012–014, FS-12 and AD-21.
Bulk transfer/local-copy verification remains the independent consumer workflow;
metadata discovery does not become an artifact-file server. No durable shape,
dependency, CLI runtime migration, MCP or production operation is introduced.

[Client contract](../api-client.md) owns exact configuration, defaults, APIs,
bounds and troubleshooting. [API](../api.md), [CLI](../cli.md),
[configuration](../configuration.md), [security](../security.md) and
[invariants](../invariants.md) record the affected boundaries; the task records
actual acceptance/full-gate evidence.

Implementation: [independent settings/source selection](../../src/hfcache/client_config.py),
[strict wire models](../../src/hfcache/client_models.py),
[synchronous client](../../src/hfcache/client.py) and
[reader example](../../packaging/client.example.toml).
Evidence: [core client tests](../../tests/unit/test_api_client.py),
[configuration tests](../../tests/unit/test_client_config.py),
[real Unix/TCP/TLS tests](../../tests/unit/test_api_client_sockets.py),
[adversarial client tests](../../tests/unit/test_api_client_adversarial.py),
[locked base/server import smoke](../../scripts/check-installations.py) and
[task compatibility/gate evidence](../plans/tasks/api-011-typed-client-and-client-config.md).

Official HTTPX documentation checked for the already locked 0.28.1 client API:
[Unix/custom transports](https://www.python-httpx.org/advanced/transports/),
[timeouts](https://www.python-httpx.org/advanced/timeouts/),
[environment discovery controls](https://www.python-httpx.org/environment_variables/)
and [streaming responses](https://www.python-httpx.org/quickstart/#streaming-responses).
No new dependency/version resolution is introduced by this package.
