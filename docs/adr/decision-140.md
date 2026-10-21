# Serve an authenticated SPA through the existing application and Caddy

- Decision identity: 140.
- Asset/bootstrap refinement: [decision147](decision-147.md).
- Status: Amended accepted design; complete replacement conformance pending.
- Provider refinement: [decision146](decision-146.md) fixes the optional-server
  verifier, protected record, admission and legacy key-ownership contract.
- Date: 2026-10-20.

## Context and decision

Browser administration is replacing the Cockpit transport while REST bearer
clients and fourteen read-only MCP tools retain their interfaces. Serve the
strict-TypeScript React SPA from the existing ASGI application at the configured
public prefix plus `/ui/`, through the same Caddy instance, TLS endpoint and Unix
upstream. Caddy continues to proxy; it receives neither archive access nor a
management password hash. There is no second frontend server, Node runtime,
public listener, global Caddy Basic gate or caller-selected API address.

Provision one protected Basic administrator with an explicit stable subject and
Argon2id password hash. A maintained verifier belongs only to the optional server
dependency group; its locked selection, bounded parameters and actual verification
benchmark must accompany implementation. Authentication providers produce an
internal subject, method, credential class and capability set. UI controls consume
a separately versioned permission projection; the server independently enforces
each action. A Basic principal is REST/UI only and cannot authenticate MCP.

Keep existing bearer classes, strict `/capabilities` payloads and public
`OperationView.principal` unchanged. A Basic administrator's ordinary REST
operation projection uses `rest-writer`; that field remains a credential-class
compatibility label, never a claim of individual attribution. Internal Basic
key ownership uses a domain-separated stable-subject binding, independent of
password hash/rotation, before receipt lookup/admission. Historical bearer key
digests remain unchanged. Independently version any private subject/audit binding;
do not append fields to old strict receipts or leak credentials into evidence.

Authenticate before route disclosure and body parsing. Before expensive password
verification, apply cheap header/body-length and bounded authentication-work
admission. Unsafe Basic requests require the exact configured same origin, JSON
media type and a non-simple application header. Missing, null, duplicate or
unapproved Origin refuses. Nonbrowser bearer requests preserve their existing
no-Origin behavior. Reject credentialed CORS and simple form mutations. Actual
browser Basic challenge, retries and credential reuse must be proved in Chromium,
Firefox and WebKit; preinjected headers alone are insufficient.
Password hashing uses a dedicated off-event-loop bounded executor, independent
of observation capacity. Recheck failed-attempt limits when queued work starts;
cancellation retains capacity until the actual hash completes. Validate exact
PHC algorithm/version/parameter/salt/output bounds at startup before verification
so a protected malformed record cannot request unbounded memory or work.

The explicitly provisioned immutable asset root is disjoint from archive,
credentials, policy and writable state. Restart-only UI settings default disabled.
An enabled release with absent or mismatched manifest/assets fails startup. Validate
bounded indexed regular files with no-follow access and exact release identity;
never expose an arbitrary static directory or repository payload. Fallback handles
only recognized GET/HEAD UI navigation. Missing assets, API/MCP errors and other
methods retain their own failures. Prefix authority comes from configuration,
never forwarded headers, and native Unix exemptions retain their existing proof.

## Rationale and alternatives

Application authentication preserves direct Unix-socket protection and independent
REST/MCP bearer credentials. A proxy-wide Basic gate would obstruct those clients;
translating Basic to a shared hidden writer token would lose principal boundaries.
A second frontend service would add deployment and routing authority without
improving a static SPA. An explicit immutable indexed root prevents a convenience
file server from crossing into archive or credentials.

Native browser authentication keeps passwords outside JavaScript. Its browser
managed lifetime has no reliable application logout; the UI must explain this
and offer no misleading secure-logout control. Stable subject binding supports
credential rotation without changing original-key recovery. New administrative
capabilities remain separate from generic bearer write authority.

## Consequences and conformance

Shell/bootstrap/API/card output is authenticated and `no-store`; hashed assets
may use bounded private caching. Use restrictive same-origin CSP without inline
executable scripts/eval, framing, external assets or service workers. Bootstrap
has independent schema 1 and carries nonsecret deployment paths, contract/release
identity and effective permission context only. Release changes must preserve
unsaved drafts and original operation handles while offering an explicit reload.

At this decision, source still implements bearer-only REST/MCP and no UI routes.
This accepted design neither asserts availability nor changes authentication by
documentation alone. Acceptance requires unit/integration failures plus built UI
through actual Caddy and installed native/rootless isolated profiles, including
prefix/deep-link, route isolation, CSRF, challenge and release-switch cases.

## Evidence and relationships

Baseline source is `6b8fae2e0997403ae5c716a2e92148af0a972af9`.
Introducing design is this commit; executable conformance evidence remains pending.
Amends [112](decision-112.md), [113](decision-113.md),
[123](decision-123.md) and the browser transport in [122](decision-122.md),
while retaining their existing implementation requirements until replacement.
See [server](../server.md#web-ui-design-and-current-availability),
[API](../api.md#web-ui-and-administration-design),
[security](../security.md#browser-administration-design),
[web UI status](../web-ui/README.md), [host boundary](decision-141.md) and
[asset/build separation](decision-143.md).

## Authenticated asset and bootstrap amendment (2026-10-20)

[Decision147](decision-147.md) amends this record. This refinement fixes the indexed manifest, protected captured bytes, strict bootstrap, complete Basic-only UI namespace, exact route fallback, headers/cache and finite streaming behavior. The same existing Caddy/TLS/Unix upstream remains the only public path; no global proxy authentication, public asset exception or frontend runtime is added. Accepted design is separate from executable conformance.
