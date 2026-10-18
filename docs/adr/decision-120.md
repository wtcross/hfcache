# Decision 120 — Separate command execution from resumable CLI observation

- Status: Accepted; implemented by API-013 on 2026-10-18, this commit.
- Date: 2026-10-18.
- Work package: API-013, this commit.
- Source: [progress decision 120](../progress.md#decisions),
  [active plan](../plans/2026-10-17-plan-rest-api-and-mcp.md),
  [task](../plans/tasks/api-013-migrate-write-cli-and-operation-waiting.md).

## Context and decision

Migrate every operational CLI mode to typed API requests rather than importing
or invoking local mutation services. Keep help/local version, explicit local
validation and foreground server bootstrap as their named local boundaries.
Pure request types may be shared without importing their domain executors.
The server retains credential, scope, preflight, flock, recovery, private verifier
and result-persistence authority; a reader/client gains none of those powers.

Default command behavior waits for the exact terminal schema-1 server Envelope,
preserving domain command/run identity, timestamps, warnings/errors, payload and
application exit priority. HTTP 202 means admission only. Explicit detach emits a
separately identified admission object with operation identity and safe observation
links, never a fabricated successful command Envelope.
Its exact JSON shape is `schema_version=1`, `kind="operation_admission"`,
`idempotency_key` and the validated server `acceptance`; it has no terminal
`outcome`/`exit_code`. Show/lookup preserve existing server metadata Envelopes,
not another observation wire family.

Validate and print the nonsecret idempotency key to stderr before the first POST,
then print accepted operation identity before observing, even in quiet mode.
Accept an explicit key for a deliberate same-request retry. Acknowledgement loss
retains that original key; validated remote refusals retain their server taxonomy
and key too. Lookup authenticates in the credential-class namespace and submits
nothing. Missing/expired history never proves nonexecution.
Validated retained-key 5xx refusals warn that accepted work may continue while
retaining their taxonomy, because an error acknowledgement may follow admission.

Observe sanitized bounded sequenced events, status and exact result under one
finite observation deadline. That deadline includes individual reads and retries;
arriving progress cannot reset it. Observer timeout, Ctrl-C or connection loss
retains known key/operation handles and says accepted work may continue. No
observer action cancels accepted server work, generates a new-key replay or
fabricates terminal domain failure/success. Explicit operation show/wait/lookup
allows later observation without submission. A stopped CLI/client service does
not prove the actual API executor stopped; server drain and exact verifier
reconciliation retain their existing authority.
The renderer escapes nonprintable/control event text, keeping one plain stderr
line per event without exposing raw logs.

Keep initialization's user-restated root and explicit confirmation. When the
legacy optional archive UUID is omitted, obtain it only from authenticated
configured-target inspection; a supplied UUID must match. Inspection and
no-confirm refusal submit no operation and load no local archive configuration.
The server's strict initialization DTO and disabled-by-default maintenance gate
remain unchanged; no implicit initialization or production authorization follows.
Failed inspection remains the exact server Envelope. A successful inspection
followed by client-only no-confirm refusal uses local invocation metadata plus
inspection data/UUID/fingerprint; this narrow argument error is not a claimed
server execution result.

## Rationale and alternatives

The writer must remain the sole operational truth when CLI callers run on reader
hosts or lose their connection. Retaining a direct local backend would create a
second runtime authority and make client loss appear to stop execution. Rendering
an admission receipt as legacy success would hide later failure and overwrite
domain evidence with observer metadata. Reject those alternatives.

Safety handles cannot depend on verbosity: losing the first acknowledgement is
exactly when a generated key is needed. Finite observation plus explicit resume
keeps long-running execution separate from the client's timeout or lifecycle.
Missing history and interrupted waiting remain uncertainty, not replay authority.

## Consequences and relationships

Implements the public CLI integration of [118](decision-118.md) and
[119](decision-119.md), preserving the non-resuming receipt/execution rules of
[114](decision-114.md)/[115](decision-115.md) and explicit maintenance authority
in [117](decision-117.md). Clarifies INV-006/012–014, AD-16/17 and TX-07 without
changing archive algorithms, durable formats, whole-archive roles, dependency
versions, isolated-verification requirements or MCP gates. Installed systemd/
Cockpit integration and host acceptance remain later work.

[CLI](../cli.md), [client](../api-client.md), [API](../api.md),
[operations](../operations.md), [recovery](../recovery.md) and
[invariants](../invariants.md) define the current boundary. The task records
actual acceptance and full-gate evidence.

Enforcement: [CLI modes](../../src/hfcache/cli.py),
[pure shared requests](../../src/hfcache/services/requests.py),
[pure local bootstrap descriptions](../../src/hfcache/services/bootstrap.py),
[submission/observation helpers](../../src/hfcache/cli_client.py) and
[bounded typed client](../../src/hfcache/client.py).
Evidence: [authenticated server/private-worker fixture](../../tests/api_cli.py),
[write CLI integration](../../tests/unit/test_cli_api_writes.py),
[helper tests](../../tests/unit/test_cli_operation_helpers.py) and
[CLI interruption/idempotency/security tests](../../tests/unit/test_cli_operations_adversarial.py).
