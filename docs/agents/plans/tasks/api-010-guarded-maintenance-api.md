# API-010: Expose retention, recovery, repair, quarantine, and guarded initialization

| Field | Value |
| --- | --- |
| Work package | `API-010` |
| Status | completed |
| Plan | [2026-10-17-plan-rest-api-and-mcp.md](../2026-10-17-plan-rest-api-and-mcp.md) |
| Depends on | [API-009](api-009-sync-verification-and-diagnostics-api.md) |
| Phase | 2 — REST implementation |
| Feature branch | `feat/rest-api-and-mcp` |
| Suggested commit | `API-010: expose guarded maintenance and initialization operations` |

## Scope and acceptance

1. Add separate typed preview/apply routes for prune, purge, recovery, and quarantine, plus repair and initialization. Do not expose a generic command string or bool whose omitted default silently applies changes.
2. For every side effect, check writer capability and idempotency, then revalidate admitted config fingerprint, explicit scope, guards, and applicable reconciliation under the archive lock. Dry-run output grants no future deletion authority. Preserve the one-round prune limit, unmanaged-only purge, batch quarantine proof, and recovery ambiguity refusals.
3. Preserve exact-manifest repair, publication/generation identity, grace periods, original audits, cache API deletion boundary, and unknown evidence. Return domain failures and partial diagnostic payloads without replacing their classifications with generic HTTP success.
4. Initialization is an explicit disabled-by-default maintenance capability on the configured archive only, requiring confirmation plus restated root/UUID. Startup, health, recovery, and missing-sentinel requests must never call init. Do not exercise init or any destructive route against production during implementation.

## Contracts, invariants, and ADRs

`AD-06`, `AD-13`–`AD-17`, `AD-20`, `FS-14`/`FS-19`/`FS-21`–`FS-23`, `TX-06`/`TX-07`; plan §4.

Use the [invariant register](../../../invariants.md) and
[ADR index](../../../adr/README.md) to load the cited sections and related records.
Record the review outcome and any explicit lack of impact on completion.

## Documentation in this package

Finish all existing-operation parity rows and destructive-action examples in API/CLI docs. Update security threat/control coverage, server maintenance-gate instructions, recovery/operations guidance, and any affected invariants/ADR notes.

## Validation

Completed strict role/mode/scope and idempotency checks, queued stale policy /
newly configured purge refusal, supplied-plan rejection, changed batch evidence,
unknown/repair preservation and synthetic configured-target initialization checks.
The full default suite includes existing pre/post-commit transaction/crash,
retention/purge/repair/recovery/quarantine regressions; exact evidence follows.

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

Implementation continues under Tyler's authorized active plan after API-009
completed in `84d2bc6`; git, completed dependency and current selector were
reconciled before starting. API-010 is the sole task in progress. Collaborators
share this package: typed maintenance DTOs/routes and shared admission; static
writer/initialization boundary and real HTTP/domain tests; adversarial queued
scope/proof/idempotency tests; and Markdown contracts/records. Decision 117 records
the contract in the actual progress log and ADR index.

Contract-first review covers AD-06/13–17/20, FS-14/19/21–23, TX-06/07 and the
related security/retention/recovery invariants. Separate preview/apply URLs never
default into mutation; previews confer no later apply authority. Writer capability,
durable keys and under-lock fresh scope/evidence remain mandatory for side effects.
`maintenance_enabled` gates initialization only, as the plan/current server
contract specify. Initialization requires the configured root/UUID restated and
explicit confirmation; startup, health, recovery and missing sentinel cannot init.
No production archive/listener/host operation, dependency, MCP, deployment, push,
merge or tag is authorized. Actual completion evidence remains pending.

Contract/source review settled `maintenance_models.py` strict preview/apply DTOs,
`maintenance.install_maintenance_routes`, and shared command admission/offload/
service helpers. Prune/purge selectors and quarantine ID sets canonicalize before
hashing; URL identity defines mode, never an omitted boolean or supplied plan.
The initialization gate precedes body/POST retry handling even for old bindings,
while original GET history remains observable. Malformed fields are 422; a valid
but mismatched configured root/UUID can be admitted but terminates HFARG002/10
without initializing. Repair redacts registered API/Hub secrets from the audit
reason after credential resolution and before durable domain writing.

Ten additional parity rows have HTTP/domain/adversarial evidence paths (27
implemented / 2 candidate rows planned). FS-21 now explicitly names initialization
through either CLI or guarded REST; it still excludes startup/health/recovery.
AD-06/13–17/20, FS-14/19/21–23, TX-06/07 and related invariants retain one-round
prune, unmanaged-only purge, whole-batch quarantine proof, exact original-manifest
repair, unknown evidence/audit preservation and existing commit recovery. RET-011
remains unchanged. Decision 117 and amendments 116/AD-16/17/20 capture the boundary.
Focused checks passed: the model/shared-service/runner selection has 143 tests;
root's seven real HTTP/domain cases cover prune/current preservation, unknown-file
purge refusal/audit, exact-manifest repair/generation/grace, recovery/run identity,
selected cleanup preserving unselected data/journals, and synthetic initialization
with no health-side init. The adversarial suite has 127 passing cases, including
queued purge becoming managed and altered two-ID quarantine whole-batch refusal
with every file preserved. Functional source and contracts then froze. During the
gate, the application's module docstring was corrected to describe authenticated
query/command adapters; supplemental format/Ruff/whitespace passed and the builds
consume that correction. No functional change or gate failure resulted. The first full gate subsequently
exited 0; completed evidence follows.

## Completion evidence

Completed 2026-10-17, this commit.

- Six strict DTOs and ten fixed resources implement prune/purge/recovery/
  quarantine preview versus apply, exact-manifest repair and guarded configured-
  archive initialization. Every job requires a canonical key and returns the
  existing admission-only 202 model/links. URL identity determines mode; unknown
  `apply`/`dry_run`/`plan` fields and implicit/all-entry cleanup are refused.
  Shared `admit_command`/`offload_command`/`command_service` helpers retain one
  authority and the installed sync wait budget, with no CLI subprocess dispatch.
- Writer-only routes authorize before body reception. Initialization additionally
  checks its disabled-by-default server gate before body/old POST binding, strict
  confirmation and restated configured root/UUID. Malformed fields are wire 422;
  valid mismatches terminate HFARG002/10 without init. Previously bound history
  remains observable after the gate is disabled. Synthetic enabled/disabled/
  mismatched/existing/unknown-layout fixtures prove no implicit health/startup init.
- Seven real HTTP/shared-domain cases preserve one-round prune/current refs,
  unknown-file purge refusal then unmanaged purge/audit, exact-manifest repair /
  generation / 168-hour predecessor grace, recovery quarantine/report run ID,
  selected cleanup preserving unselected entries and original journals, and
  configured-target synthetic initialization. A failed/blocked terminal Envelope
  retains domain exit and diagnostic payload rather than implying successful apply.
- The released adversarial suite passed 127 tests in 15.19 seconds. It covers
  pre-body roles/gates, strict scope/mode/authority rejection, keyed repeats,
  supplied-preview refusal and fresh locked scope/proof. A real queued purge
  target becoming configured refuses without deleting files; a two-ID quarantine
  preview followed by changed unknown evidence refuses the entire batch and
  preserves every file. No preview or missing history grants deletion authority.
- Repair audit reasons redact registered opaque API/Hub secrets after credential
  resolution and before durable domain writing; ordinary reason text is preserved.
  Focused command:
  `rtk uv run --locked --extra server pytest tests/unit/test_maintenance_models.py tests/unit/test_command_services.py tests/unit/test_command_models.py tests/unit/test_runner.py -q`
  passed 143 tests in 5.11 seconds. Root's seven real HTTP/domain cases and the
  adversarial selection are separate, overlapping evidence within the final gate.
- Definitive command:
  `rtk proxy bash scripts/check.sh > .scratch/api-010-gate.log 2>&1`
  exited 0 on its first full attempt. Lock check/server-extra sync passed;
  327 files were formatted, Ruff passed, Pyrefly reported 0 errors (11 suppressed,
  54 hidden warnings); Python passed 2,685 tests, 40 deselected, in 163.41 seconds.
  Version 0.1.10 sdist/wheel built; locked isolated base/server wheel installation,
  import/help/version passed. Cockpit eslint/stylelint/types, 45 tests (0 failures)
  and the production build passed. No functional correction or gate failure;
  a module-docstring-only correction had supplemental format/Ruff/whitespace
  checks and was consumed by the final builds/installations.
- Reviewed AD-06/13–17/20, FS-14/19/21–23, TX-06/07 and related INV-001/002/
  005/006/012–014. Existing guard/reconciliation/commit, one-round retention,
  unmanaged purge, canonical-cache API, original manifest/audit, exact repair/
  grace and whole-batch proof rules remain unchanged. RET-011 is explicitly
  preserved. Decision 117 and amendments to 116/AD-16/17/20 record the transport;
  FS-21 now explicitly names the same initialization operation through CLI or
  guarded REST while excluding startup/health/recovery. API/server/CLI/security/
  architecture/invariants, operator/recovery guidance, README, plan and Unreleased
  agree. No durable shape or dependency changed; no new compatibility drill needed.
- Final local-link/dependency/current/matrix, all 117 numbered decision/ADR and
  whitespace audits pass. Matrix: 27 implemented / 2 candidate rows planned.
  The completed [progress audit](../../progress.md#rest-api-and-read-only-mcp-api-2026-10-17)
  records the package; current selects API-011 pending. Public clients, candidates,
  installed-host hardening and MCP retain their later task gates. Live/NFS/
  installed-host and extra build-marker checks did not run. No production archive/
  listener operation, deployment, push, merge or tag; no new operator action required.
