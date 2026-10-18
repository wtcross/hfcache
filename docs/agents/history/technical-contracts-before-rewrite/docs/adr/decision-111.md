> Historical technical reference preserved before consolidation. Current authority is the living contract.

# Decision 111 — Scope execution correlation and offline process initialization

- Status: Accepted; implemented by API-004.
- Date: 2026-10-17.
- Work package: API-004, this commit.
- Source: [progress decision 111](../../../../progress.md#decisions),
  [active plan](../../../../plans/2026-10-17-plan-rest-api-and-mcp.md),
  [task](../../../../plans/tasks/api-004-isolate-execution-context.md).

## Context and decision

Decision 64 assumed a process could have only one invocation because archive
writes serialize. Concurrent metadata requests and a long operation invalidate
that logging assumption without changing single-writer archive authority. The
existing full-verification context manager also changed `os.environ`, affecting
every request and lazily imported Hub library in the process.

Keep the closed module-level event API, but replace process-global correlation
with an immutable `Correlation` in a `ContextVar`. `ExecutionContext.activate()`
scopes run and optional request/operation IDs and restores prior bindings after
success or exceptions. `emit` captures the snapshot at record creation; later
formatting cannot borrow another request's identity, and caller fields cannot
override authoritative event/level/correlation values. `submit_with_context`
copies a separate context per service-thread submission; AD-19's existing sync
producer uses it and returns its worker to the previous scope even on failure.

Trusted boundaries mint request and operation IDs using the existing
32-lowercase-hex grammar. Caller-provided headers do not become authoritative
IDs. A request identifies one received interaction; an operation identifies one
admission and its observation/execution relationship. Domain run IDs continue
to identify envelopes/reports, and transaction IDs identify individual archive
journals. No ID replaces another. API-007/008 implement receipt relationships.

`configure_daemon` installs one request-neutral handler/level at startup and is
idempotent; CLI `configure` refuses to reconfigure an active daemon. Client
quiet/verbose behavior belongs in rendering and event selection. The isolated
CLI retains its per-invocation startup configuration and stderr-only output.

Shared verification constructs no Hub client or credential and never writes
`os.environ`. Remove the scoped `networking_disabled` toggle. The new
`offline.initialize_offline_process()` sets `HF_HUB_OFFLINE=1` permanently at
dedicated-process startup, before Hub imports/use. It supplies a library guard,
not no-IP enforcement. The existing verification unit keeps its offline/no-IP
policy; API-008/014 must build and prove that sandbox around the later executor,
through report/catalog persistence. There is no ASGI-process fallback.

Credential loaders register accepted exact secret values before use. Shared
sanitization covers sensitive keys, existing Hub/bearer/signed-URL shapes and
registered opaque credentials in nested diagnostic data. `Problem` snapshots
safe diagnostics; public rendering and application exception string/repr paths
sanitize again for late registrations or legacy mutable contexts. Unknown
arbitrary secrets cannot be recognized by a token-prefix regex. API-005/006
must apply this boundary to their credentials and transport exceptions.

## Rationale and alternatives

Explicitly passing a logger through every domain function would preserve
correlation but add plumbing without improving the closed event interface.
`ContextVar` scopes preserve that interface while independent thread copies
make propagation and restoration explicit. A process-global run ID or request
logger reconfiguration would leak IDs or verbosity into unrelated requests.
Capturing IDs only at formatting time fails delayed-handler provenance.

Per-request environment toggles cannot isolate concurrent work, and restoring
the old value does not repair that race or imported library constants. A
startup-only process flag supports the required dedicated verifier without
claiming it replaces its systemd socket restrictions. Exact-value registration
covers opaque credentials that recognizable-shape filtering alone misses.

## Consequences and relationships

Amends [decision 64](../../../../../adr/decision-064.md)'s one-run-per-process rationale,
[offline verification](../../../../../adr/offline-verification.md), the deferred-environment note
in [decision 110](../../../../../adr/decision-110.md), and [AD-19](../../../../../adr/ad-19.md)'s producer propagation
requirements. [Scheduling authority](../../../../../adr/systemd-scheduling.md) stays in systemd.
Durable `invocation_mode` remains `systemd`/`interactive` and describes the
executing host process via `INVOCATION_ID`; it does not prove timer or client
origin. Authenticated submitter metadata belongs to later operation receipts.
No durable archive schema, runtime dependency, listener, ASGI or MCP code is
introduced. Existing FS/TX, verification lock/persistence and no-repair rules
remain authoritative.

Evidence: [context, logger, secret and verification isolation tests](../../../../../../tests/unit/test_execution_isolation.py),
[delayed formatting and existing CLI logging tests](../../../../../../tests/unit/test_logging.py),
[sync producer propagation tests](../../../../../../tests/unit/test_synchronize.py),
[startup-only child-process tests](../../../../../../tests/unit/test_offline_process.py),
and [identity/result tests](../../../../../../tests/unit/test_queries.py).
Implementation: [execution context](../../../../../../src/hfcache/services/context.py),
[event capture and thread submission](../../../../../../src/hfcache/logging.py),
[redaction](../../../../../../src/hfcache/redaction.py),
[shared commands](../../../../../../src/hfcache/services/commands.py), and
[offline initialization](../../../../../../src/hfcache/offline.py).

## Rootless execution amendment (OPS-015, 2026-10-18)

[Decision 127](../../../../../adr/decision-127.md) preserves this provenance through rootless Podman:
the fixed launcher forwards only a canonical non-secret 32-lowercase-hex systemd
INVOCATION_ID to API/worker. Podman does not pass it implicitly, and no arbitrary
ambient environment is forwarded. The value still describes the executing
service invocation, not timer/client origin or authenticated authority. Actual
container review exposed the missing propagation; the task records its correction
and gate history without changing durable invocation fields.
