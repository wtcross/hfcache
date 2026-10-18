# Decision 117 — Revalidate explicit maintenance authority at execution

- Status: Accepted; implemented by API-010.
- Date: 2026-10-17.
- Work package: API-010, this commit.
- Source: [progress decision 117](../progress.md#decisions),
  [active plan](../plans/2026-10-17-plan-rest-api-and-mcp.md),
  [task](../plans/tasks/api-010-guarded-maintenance-api.md).

## Context and decision

Expose maintenance through separate typed preview/apply URLs for prune, purge,
recovery and quarantine, plus explicit repair and configured-archive initialization.
There is no omitted boolean that defaults to apply, generic command dispatcher,
caller-supplied plan to execute or arbitrary-path mutation. Preview jobs permit
REST readers; every side effect requires writer capability before body reception.
Every route is a bounded keyed job with admission-only 202 and exact terminal
Envelope observation, including previews' control-state effects.

Preview results describe current evidence and grant no future deletion authority.
Apply calls the shared service to acquire the common archive lock, compare fresh
installed policy with the admitted fingerprint, repeat domain scope/guard/evidence
checks and perform applicable reconciliation. Newly configured purge targets,
stale policy, altered quarantine evidence and ambiguous recovery remain refusals.
Do not accept a preview/result body as an execution plan or reconstruct work from
receipts after restart.

Preserve one eligible prune per repository per invocation, unmanaged-only purge,
canonical-cache deletion through supported APIs, prune's logical commit boundary,
original audit/manifest preservation and unknown evidence. Quarantine accepts
explicit transaction IDs only and proves the whole requested batch before removal;
it does not reconcile unrelated work. Repair re-downloads the exact SHA against
the original manifest, publishes/reverifies a new instance, preserves generation
and retains its predecessor through the grace period. The shared service redacts
registered secrets from audit reason text after installed credential resolution
and before durable repair/audit writing. Existing RET-011's separate
pruned-SHA generation gap is not repaired or hidden by a transport change.

`maintenance_enabled` is a restart-only, disabled-by-default initialization gate,
not a switch for ordinary maintenance routes. Initialization additionally requires
explicit confirmation and the configured root/UUID restated. It uses its own
locked known-empty-layout/mount checks, writes the sentinel last and refuses
existing or unexplained content. Startup, health, recovery, missing sentinel and
ordinary commands never call initialization implicitly. The disabled gate also precedes POST retry handling after restart, while original
GET history remains observable. Neither this gate nor an API bearer grants
authority to initialize a production archive during development. FS-21 names the
explicit initialization operation through CLI or guarded REST, preserving its
exclusion from startup/health/recovery.

## Rationale and alternatives

Distinct resources and strict typed inputs make destructive scope reviewable.
Treating a preview as a capability would trust stale filesystem/policy evidence;
fresh locked validation preserves the existing transaction safety boundary.
Reusing shared services preserves refusal ordering, partial payloads, classified
errors and pre/post-commit recovery without a second deletion engine.

Reject generic command/plan execution, mode defaults, initialization on startup,
HTTP-provided alternate-root authority, automatic cleanup of unknown evidence and treating
202/HTTP 200 as successful deletion. Extending the initialization gate to ordinary
prune/purge/recovery would silently change the accepted plan and hide their
existing writer/domain safeguards.

## Consequences and relationships

Extends [116](decision-116.md)'s typed admission boundary and
[115](decision-115.md)'s fresh under-lock execution guard. AD-06/13–17/20,
FS-14/19/21–23 and TX-06/07 retain their existing algorithms and evidence rules.
The API contract records ten additional maintenance rows; only the two candidate
rows remain API-012. Public CLI migration, installed service hardening and MCP
remain later tasks. No durable shape, runtime dependency or production operation
is introduced. The task records exact acceptance and full-gate evidence.

Governing contracts: [API](../api.md), [server initialization gate](../server.md),
[security](../security.md), [operations](../operations.md),
[recovery](../recovery.md) and [invariant register](../invariants.md).

Implementation: [strict scope DTOs](../../src/hfcache/api/maintenance_models.py),
[fixed maintenance routes](../../src/hfcache/api/maintenance.py),
[shared keyed admission](../../src/hfcache/api/commands.py),
[early authorization/initialization gate](../../src/hfcache/api/app.py) and
[guarded domain services/audit redaction](../../src/hfcache/services/commands.py).
Evidence: [model tests](../../tests/unit/test_maintenance_models.py),
[real HTTP/domain tests](../../tests/unit/test_api_maintenance.py),
[queued-scope/proof/idempotency tests](../../tests/unit/test_api_maintenance_adversarial.py)
and [shared-service tests](../../tests/unit/test_command_services.py).
