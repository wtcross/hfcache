# API-007: Persist bounded operation receipts and idempotent admission

| Field | Value |
| --- | --- |
| Work package | `API-007` |
| Status | completed |
| Plan | [2026-10-17-plan-rest-api-and-mcp.md](../2026-10-17-plan-rest-api-and-mcp.md) |
| Depends on | [API-006](api-006-fastapi-lifecycle-and-reads.md) |
| Phase | 2 — REST implementation |
| Feature branch | `feat/rest-api-and-mcp` |
| Suggested commit | `API-007: persist operation receipts and idempotent admission` |

## Scope and acceptance

1. Implement versioned service-private JSON operation receipts, result references, and bounded sequenced events under an injectable local state directory. Reuse deterministic atomic write/fsync primitives and protect permissions; never place this control state in publication trees.
2. Persist admission before work becomes runnable and before returning 202. Make a receipt the authoritative key binding so a crash cannot leave an accepted operation without deduplication. Rebuild only derived indexes; do not introduce SQLite, a broker, or journal-driven execution.
3. Bind each Idempotency-Key uniquely within the authenticated principal namespace and compare its stored canonical route/request digest. Same request/key returns its original operation despite a later config change; mismatched reuse, including another route, returns 409. Add a non-submitting authenticated key lookup for lost acknowledgements. Enforce unique concurrent admission and require keys for side effects.
4. Define queued/waiting/running/terminal/interrupted transitions, current/result/events APIs, key/result retention, oversized/full storage refusal, and malformed/unknown-version record preservation. Never delete unfinished or unexplained receipts. Expose no raw credentials/candidate secrets. A status fetch must never run an operation.

## Contracts, invariants, and ADRs

`AD-12`, `AD-14`/`AD-16`, `FW-01`/`FW-02`, `INV-002`, `INV-005`; plan §5.

Use the [invariant register](../../invariants.md) and
[ADR index](../../adr/README.md) to load the cited sections and related records.
Record the review outcome and any explicit lack of impact on completion.

## Documentation in this package

Add receipt/result/event schemas and compatibility rules to schemas/API docs, idempotency examples, retention/expiry/uncertain-state runbook, and the bounded-registry decision with explicit FW scope amendment. Update security and recovery docs.

## Validation

- Definitive full gate: `rtk proxy bash scripts/check.sh > .scratch/api-007-gate.log 2>&1`
  exited `0`. Lock check and locked server-extra sync passed; Ruff formatted/checks
  were clean across 306 Python files; pyrefly reported 0 errors (11 suppressed,
  53 hidden warnings). Python: **2,224 passed, 40 deselected in 118.15 seconds**.
  Version `0.1.10` sdist/wheel built; real isolated locked base/server wheel
  installation, imports, help and local version checks passed. Cockpit lint,
  stylelint/types, **45 tests** with no failures and the production build passed.
- The first full gate was already green: 2,222 Python tests passed, with 40
  deselected in 118.06 seconds. Its log is preserved as
  `.scratch/api-007-gate-first-green.log`. A final acceptance audit added two
  explicit injected-ENOSPC admission/result-fsync regressions without source
  changes; the definitive gate above includes them. No gate attempt failed.
- Final operations/adversarial/store/storage selection: **161 passed in 3.34
  seconds**; core operations alone: 21 passed in 0.64 seconds. Earlier broader
  core/model/storage/HTTP/config/taxonomy selection: 414 passed in 4.18 seconds;
  root's final HTTP/config sweep: 178 passed in 8.51 seconds; auditor-owned
  adversarial selection: 44 passed. Counts describe separate selections.
- Seven injected atomic-write seams cover before-write, before/after file fsync,
  before/after rename and before/after directory fsync. Threaded distinct-handle
  and spawned-process races retain one durable key binding. Tests cover matching
  retries before fresh policy resolution, route/request conflicts, class-local
  lookup, unknown/malformed/duplicate-key/unsafe state preservation, quota refusal,
  unavailable/corrupt results, explicit expiry and retained event gaps.
- ENOSPC at admission/result fsync refuses acknowledgement/completion, leaves
  no invented result and preserves existing receipt/key authority. No physical
  disk was filled. Domain-run identity cannot be rebound and transaction evidence
  retains its ordered prefix. Generated-ID/temp-name collisions and replacement
  cleanup preserve unexplained inodes.
- Independent schema fixtures and model tests pass; changing the archive version
  in a regression does not change operation schema version 1. The actual isolated
  predecessor/tagged-wheel compatibility drill is recorded below.
- `rtk proxy python .scratch/audit_records.py`, decision/ADR coverage, parity
  review and `rtk git diff --check` pass. There are 114 numbered decisions with
  matching ADRs and 9 implemented / 20 planned API matrix rows. No live Hub, NFS,
  installed-host or extra build-marker suite was run.

## Execution and completion rules

Follow the [parent plan](../2026-10-17-plan-rest-api-and-mcp.md) and
[repository workflow](../../agents/workflow.md). Work only on
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

Implementation continues under Tyler's instruction and the active plan after
API-006 completed in `a856397`. API-007 was the sole package in progress during implementation.
Collaborators share the API-007 boundary with explicit ownership: operation
receipt/store models and persistence tests; HTTP observation/configuration wiring;
adversarial durability/retention review; and contracts/task/progress records.
Review covers AD-12/14/16, FW-01/02, INV-002/005/014, decision 109 and plan §5.
This package adds durable non-resuming admission primitives and observation only;
heavyweight execution remains API-008 and command submission routes API-009/010.
No MCP work, production operations, deployment, push, merge or tag is authorized.

Contract-first review allocated actual decision 114 and amended decision 109,
FW-01/FW-02, AD-12, INV-002/005/006/014 and the API/server/schema/security/recovery
contracts. Receipt schema version 1 is independent of archive JSON. All REST
read-capable principals share operation observation under AD-21, while hashed-key
lookup stays within the fixed credential-class namespace across token rotation.
No raw key or replayable request body is persisted. Count/space caps cannot evict
unexpired terminal bindings; nonterminal/interrupted/ambiguous records retain
history and reserved capacity. The final gate and isolated compatibility drill
are complete; detailed evidence is retained here.

The compatibility drill used actual built/installed wheels in isolated locked
offline environments for predecessor `a856397` (`0.1.10`) and tagged release
`v0.1.3` (`0.1.3`). Command:
`rtk uv run --locked --extra server python .scratch/api-007-compatibility.py > .scratch/api-007-compatibility.log 2>&1`.
Both old `hfcache operations show <fixture-id>` invocations exited `2` with
`No such command`, and neither binary provided `hfcache.api.operations`.
The three synthetic control-state files remained byte-for-byte unchanged;
no archive path was created and no dependency network access was needed.
This proves absent reader support, not receipt compatibility or nonexecution.
The schema/recovery/deployment rollback rule preserves local state and requires
a compatible server for uncertain history before any deliberate retry.

The planned simultaneous duplicate-POST check is phased with the public
submission routes in API-009/010. This package proves concurrent duplicate
admission at its authoritative core, including separate processes; it does not
claim a nonexistent HTTP submission endpoint passed. Root's final HTTP/config
sweep passed 178 tests in 8.51 seconds. The completed full-gate evidence above
includes the additional ENOSPC acceptance cases.

## Completion evidence

Completed 2026-10-17, API-007, this commit. The service-private store persists the
receipt/key authority before admission returns, with no raw key/body storage,
strict independently versioned models, bounded events and exact referenced domain
Envelopes. Concurrent retries retain one operation; unsafe/full/unexplained state
refuses new admission without deleting evidence. Interrupted/nonterminal history
retains capacity indefinitely; unexpired terminal keys cannot be evicted by count.
The five authenticated GET surfaces expose bounded whole-archive observation and
class-local non-submitting lookup without domain execution or fresh-policy reload.
State/archive overlap refuses before default state creation.

Decision 114 and amendments to 109, FW-01/FW-02 and AD-12/14/16 retain existing
archive authority and the no-resuming-engine boundary. INV-002/005/006/014 and
architecture/API/server/CLI/configuration/schema/security/recovery/deployment
contracts, README, Unreleased and plan amendments were reviewed and updated.
The final record/link/dependency/parity/decision audits and whitespace review pass.
The completed [progress audit](../../progress.md) accompanies this package.

API-008 remains responsible for the heavyweight lane, under-lock policy checks,
exact surviving-worker reconciliation and isolated verification; API-009/010 own
public submission routes. Startup opens/closes history without replay or automatic
classification. No MCP work, production archive/listener operation, deployment,
push, merge or tag occurred. Operator-only installed-host acceptance remains in
the later packaging/deployment tasks; no new production action is requested here.
The current selector advances to API-008 pending.
