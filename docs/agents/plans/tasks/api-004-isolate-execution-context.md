# API-004: Make correlation and offline execution safe for concurrent requests

| Field | Value |
| --- | --- |
| Work package | `API-004` |
| Status | completed |
| Plan | [2026-10-17-plan-rest-api-and-mcp.md](../2026-10-17-plan-rest-api-and-mcp.md) |
| Depends on | [API-003](api-003-extract-guarded-commands.md) |
| Phase | 1 — Shared services |
| Feature branch | `feat/rest-api-and-mcp` |
| Suggested commit | `API-004: isolate request context and preserve offline execution boundaries` |

## Scope and acceptance

1. Replace process-global run correlation with context-scoped or explicitly passed execution data. Configure logging once per daemon startup, not per request, while retaining the CLI’s isolated startup behavior.
2. Define request ID, operation ID, domain run ID, and transaction ID relationships. Generate authoritative IDs server-side and correlate them without replacing existing run/report identities. Propagate context deliberately into service threads and the existing sync producer; restore context after success and exceptions.
3. Keep per-request quiet/verbose behavior in client rendering/event selection rather than changing the server logger’s global level. Extend secret redaction to arbitrary opaque API tokens and sanitize exception/problem contexts.
4. Remove any requirement to toggle `HF_HUB_OFFLINE` in an ASGI process. Verification service must structurally construct no Hub client/credential. Retain process-scoped offline initialization for the isolated executor added later. Preserve the existing durable invocation-mode vocabulary; distinguish authenticated submitter metadata in operation receipts instead of claiming every daemon request is a timer.

## Contracts, invariants, and ADRs

`AD-19`, `INV-002`, `INV-005`/`INV-006`; logging/security and offline-verification contracts; plan §§2, 5–6.

Use the [invariant register](../../../invariants.md) and
[ADR index](../../../adr/README.md) to load the cited sections and related records.
Record the review outcome and any explicit lack of impact on completion.

## Documentation in this package

Update logging/event and provenance contracts, API correlation fields, security redaction requirements, and architecture concurrency notes. Amend affected ADR rationale where process-per-CLI assumptions no longer hold.

## Validation

Planned checks, not execution evidence:

Interleave two reads and a long operation with distinct IDs, including worker-thread logs, sync producer events, failures, and subsequent requests. Assert no cross-request ID/verbosity leakage, duplicate handlers, stdout logging, or environment mutation. Run existing logging/Hub/CLI suites and `scripts/check.sh`.

## Execution and completion rules

Follow the [parent plan](../2026-10-17-plan-rest-api-and-mcp.md) and
[repository workflow](../../workflow.md). Work only on
`feat/rest-api-and-mcp`. A task may include several related subtasks, but this
work package owns one implementation commit. Read the affected invariant and ADR
sections before editing; update their enforcement/decision links where behavior
changes. Include code, tests, documentation, task evidence, the current pointer,
and completed progress audit together. Do not run production operations or weaken
host controls. Do not push, merge, tag, or deploy.

Mark `in_progress` only when authorized and dependencies are complete. On a real
blocker, record the exact missing prerequisite and unblock condition. A skipped
required test is not passing evidence. Use `this commit` until a real commit exists.

## Execution notes and handoff

Implementation authorized by the active plan and Tyler's 2026-10-17 instruction;
API-003 is completed in `e1a9263`. API-004 collaborators share this work-package
boundary on `feat/rest-api-and-mcp`; no later task has begun.

Replaced process-global correlation with frozen `Correlation` snapshots in a
`ContextVar`. `ExecutionContext.activate()` and command service scopes restore
earlier bindings after success/failure. Event emission captures the snapshot;
reserved call-site fields cannot replace event/level/run/request/operation IDs.
`submit_with_context` gives each worker an independent copy; the existing sync
producer uses it and reused threads retain no request scope. Trusted helpers mint
independent request/operation IDs; schema-1 run/report and transaction identity
remain unchanged. `configure_daemon` is idempotent startup configuration and
CLI reconfiguration refuses an active daemon. Quiet/verbose request preferences
cannot change its handler or level.

The shared `redaction` module registers resolved exact secret values before use,
including opaque tokens without an `hf_` prefix, and sanitizes nested diagnostics,
known secret keys/value shapes, `Problem` output and application exception
string/repr paths. Output re-sanitization covers late registration and legacy
mutable contexts. The registry is process-lived, not reset between requests.
API credential registration and transport exception wiring remain API-005/006.

Removed the unsafe `networking_disabled` context manager. Every shared
verification mode constructs no Hub client/credential and never writes the
environment. `offline.initialize_offline_process()` is reserved for a dedicated
process's startup before Hub imports/use; its permanent library flag does not
enforce no-IP isolation. The existing verification unit retains its policy;
the new isolated executor and host acceptance remain API-008/014. No unsafe
ASGI fallback is added. Durable `invocation_mode` values remain unchanged and
describe the execution host; future receipts carry authenticated submitter
metadata separately, without claiming every daemon request is timer-originated.

Reviewed AD-19, INV-002/005/006/007/012/015 and decisions 64/108/109/110,
offline verification and scheduling ADRs. Decision 111 amends affected rationale;
architecture, invariant links, API/server correlation, security, CLI output,
schema provenance prose, original-plan amendments and Unreleased notes agree.
No durable schema, dependency, ASGI, MCP, deployment or production operation was
introduced. Required local acceptance and the full gate passed; the next selected
task is API-005. Host acceptance remains with API-008/014 and the operator handoff.

## Completion evidence

2026-10-17, API-004, this commit.

Two reads and a long-operation scope interleave with distinct IDs, including
copied service workers and a raised worker exception; all event records retain
their own correlation, enclosing scopes restore and reused workers remain clean.
The existing sync producer propagates request/operation/run IDs and still joins
its transfer before lock release on interruption. A delayed log-record formatting
regression proves emission-time provenance; reserved event/level/ID fields cannot
be spoofed by call-site data. Daemon startup/repeated-call tests retain exactly
one handler and startup level, reject CLI reconfiguration and emit no stdout.
Trusted ID generation stays independent while Envelope serialization remains
schema 1. Exact recovery report IDs use the service context without changing
standalone caller behavior.

Opaque-token tests cover nested diagnostic keys/values, logs, exceptions,
`Problem` snapshots/rendering, later registration and legacy context mutation.
Every verification mode refuses any environment write or Hub/credential
construction. Three child-process startup cases (unset, `0`, `1`) initialize the
permanent offline flag before Hub import and leave the parent environment alone.
These hermetic tests do not claim installed-host no-IP acceptance.

Reviewed AD-19, INV-002/005/006/007/012/015 and decisions 64/108/109/110,
offline verification and systemd scheduling. Added decision 111 and index entry;
amended decision 64, AD-19, offline verification, decision 110's deferred guard,
and scheduling provenance. Updated API/server correlation, architecture,
invariants, CLI output/offline effects, security, durable invocation-mode prose,
original-plan amendments and Unreleased notes. Durable schemas/dependencies
remain unchanged. Isolated executor work remains API-008/014; transport auth,
receipt submitter metadata, REST and MCP remain their pending packages.

Validation:

- `rtk uv run pytest tests/unit/test_logging.py tests/unit/test_hub.py tests/unit/test_cli.py tests/unit/test_credentials.py tests/unit/test_verify_command.py tests/unit/test_execution_isolation.py tests/unit/test_offline_process.py tests/unit/test_command_services.py -q`:
  310 passed in 13.41s.
- `rtk uv run pytest tests/unit/test_synchronize.py -k 'service_and_sync_producer or interrupt_finishes' -q`:
  6 passed, 113 deselected in 1.79s.
- `rtk uv run pytest tests/unit/test_synchronize.py tests/unit/test_recovery_planning.py tests/unit/test_command_services.py tests/unit/test_queries.py -q`:
  163 passed in 47.98s.
- `rtk proxy bash scripts/check.sh > .scratch/api-004-gate.log 2>&1`:
  exit `0` on the first full attempt; no gate-cycle failures or fixes. Lock check,
  Ruff formatting (280 files), lint and Pyrefly (0 errors) pass; 1,835 Python
  tests pass, 40 deselected in 108.80s. Wheel/sdist build; Cockpit lint/styles,
  types, 45 tests and production build all pass.
- `rtk proxy python .scratch/audit_records.py`: local documentation links,
  task dependencies/current pointer and parity-table structure pass. Numbered
  decision/ADR coverage audit passes all 111 records without duplicates.
  `rtk git diff --check` passes.

No opt-in live Hub, NFS or installed-host tests ran; no production operation,
deployment, push, merge or tag occurred. The local tests cover the changed
shared-service boundary; executor egress and host hardening acceptance remain
explicit future API-008/014 requirements. Completed
[progress audit](../../progress.md#rest-api-and-read-only-mcp-api-2026-10-17)
and current pointer agree.
