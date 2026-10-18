# Decision 118 — Observe one API authority without replaying uncertain submissions

- Status: Accepted; implemented by API-011 on 2026-10-18; public operational
  CLI/observation completed by [decision 120](decision-120.md).
- Date: 2026-10-17.
- Work package: API-011, this commit.
- Source: [progress decision 118](../progress.md#decisions),
  [active plan](../plans/2026-10-17-plan-rest-api-and-mcp.md),
  [task](../plans/tasks/api-011-typed-client-and-client-config.md).
Native Unix/public-prefix routing is amended by [decision 123](decision-123.md).

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

## API-012 reader integration amendment

[Decision 119](decision-119.md) migrates actual read CLI modes through this client,
preserving exact server Envelope IDs/times/exit and complete finite page/joined
inventory. Explicit local validation stays bootstrap, never a fallback. Candidate
content is read on the CLI host, validated separately from authority compatibility
and planned only with installed credentials. Side-effecting CLI/operation UX
remains API-013; the client adds no archive filesystem authority.

## API-013 operational CLI amendment (2026-10-18)

[Decision 120](decision-120.md) uses the finite observer for every operational
CLI mode. Default output remains the exact terminal server Envelope; only
explicit detach emits identified admission. Show/lookup preserve exact server
metadata Envelopes. Validated key/accepted-ID messages remain on stderr even
quiet, and bounded sanitized event/status/result reads share one deadline.
Timeout/Ctrl-C retains handles and uncertainty, without cancellation or replay.
No direct local mutation backend, new dependency or durable shape is introduced.


## 2026-10-18 native Unix prefix and REST acceptance amendment (API-016)

Existing local Unix clients retain fixed unprefixed paths without another
client field/version. Actual supported Unix transport gets native effective-prefix
links; public TCP continues its configured safe URL prefix, verified TLS and strict
link checks. The client still cannot select another interface through request
headers, follow arbitrary links or replay uncertain work. See
[decision 123](decision-123.md).

## 2026-10-18 bounded small-page observation correction (API-017)

A final real CLI-to-socket integration with max_page_size=1 exposed a fixed
internal events limit of 100: a sync could durably succeed while observation
failed HFAPI006. This violated the existing bounded-client/faithful-observation
contract. `events(limit=None)` now omits the field so the server chooses its
existing min(100, max_page_size, operation_max_events) default; explicit integer
limits keep their semantics. Progress observation drains retained contiguous
pages through an empty page, counting that response too against the same
drain's max_pages and the absolute observation deadline. Retention gaps and
admitted operation identity stay explicit; no extra capabilities request, new role/schema/dependency or replay/
cancellation authority is introduced. This is an existing-contract correction,
not a new architectural decision. [Final integration task](../plans/tasks/api-017-final-integration-and-handoff.md)
owns exact subprocess/direct-client proof and required fresh gate evidence.


Correction accepted 2026-10-18: [actual CLI socket integration](../../tests/unit/test_interface_integration.py)
and [observer budget tests](../../tests/unit/test_cli_operation_helpers.py) pass;
the final task records the first required --with-build gate exit 0 (3,624 Python
tests), final installed-reader drill and completed plan. This adds evidence to
the existing decision; installed-host acceptance remains separate.
