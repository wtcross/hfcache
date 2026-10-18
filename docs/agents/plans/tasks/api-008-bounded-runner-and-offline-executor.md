# API-008: Run bounded operations and implement the private offline executor

| Field | Value |
| --- | --- |
| Work package | `API-008` |
| Status | completed |
| Plan | [2026-10-17-plan-rest-api-and-mcp.md](../2026-10-17-plan-rest-api-and-mcp.md) |
| Depends on | [API-007](api-007-operation-receipts-and-idempotency.md) |
| Phase | 2 — REST implementation |
| Feature branch | `feat/rest-api-and-mcp` |
| Suggested commit | `API-008: add bounded execution and isolated verification protocol` |

## Scope and acceptance

1. Implement one heavyweight command lane, bounded FIFO admission, queue/lock deadlines, and a separate small read pool. Carry frozen config and correlation; stale fingerprint checks occur inside the command’s archive lock. Keep the lock independent of daemon admission and avoid nested flock acquisition.
2. Add the private verification-worker protocol and entry point. It accepts only verification mode/scope, exact operation ID, and expected installed-config fingerprint. Add protected Unix-socket/peer checks, bounded messages, durable terminal receipts, and status/reattach by exact operation identity. It loads no inbound API/Hub credentials and executes the shared fully guarded verification service.
3. Implement an injectable delegation adapter; the production API refuses verification if the isolated worker is unavailable. Do not create an insecure in-process production fallback, generic exec endpoint, or broad systemctl/sudo grant. Shipped hardening/unit integration is completed in API-014.
4. Stop admission before draining; join domain work before releasing safety ownership. Handle process death, incomplete receipts, a surviving verification worker, and dropped clients explicitly. Never automatically replay old queued/running mutations on startup; classify uncertain work as interrupted and preserve evidence.

## Contracts, invariants, and ADRs

`AD-17`/`AD-19`, `FS-19`, `TX-07`, `INV-002`/`INV-003`/`INV-007`; plan §§5–6.

Use the [invariant register](../../../invariants.md) and
[ADR index](../../../adr/README.md) to load the cited sections and related records.
Record the review outcome and any explicit lack of impact on completion.

## Documentation in this package

Document execution state transitions, deadlines, no-replay semantics, worker trust boundary/protocol, standalone limitations, and drain/recovery procedures in server/API/operations docs. Add verification-isolation ADR amendments and relevant invariants.

## Validation

- Definitive gate: `rtk proxy bash scripts/check.sh > .scratch/api-008-gate.log 2>&1`
  exited `0` after the bootstrap correction below. Lock/locked-extra checks,
  formatting across 314 Python files and Ruff passed; pyrefly reported 0 errors
  (11 suppressed, 54 hidden warnings). **2,309 Python tests passed, 40 deselected
  in 124.99 seconds**. Version `0.1.10` sdist/wheel built; real isolated locked
  base/server wheel installation, import, help and local-version checks passed.
  Cockpit eslint/stylelint/types, **45 tests** with no failures and production
  build passed.
- The first full gate was green at 2,307 Python tests, 40 deselected in 124.45
  seconds, with all later stages passing. Its log remains
  `.scratch/api-008-gate-first-green.log`. A subsequent real activated-entry-point
  probe exposed a bootstrap import-order defect; two process regressions and
  the corrected source are included in the definitive gate. No gate attempt
  failed; the positive probe was the failing validation that prompted the fix.
- Final owned runner/locking/service/adversarial selection: **71 passed in 5.98
  seconds**. Broader synchronize/runner/service selection previously passed
  **187 in 52.70 seconds** before its final cases. Actual sync-producer drain
  integration: **1 passed, 119 deselected in 1.24 seconds**. Root's final HTTP /
  real-verifier selection before the bootstrap additions: **63 passed in 6.60
  seconds**. These counts describe separate selections.
- Corrected actual inherited-FD-3 bootstrap selection: **3 passed, 42 deselected
  in 1.84 seconds**. The exact manual positive command/result is retained below.
  Both positive activation and extra inherited synthetic credential-descriptor
  refusal run in real child processes; no production systemd service is used.
- Tests prove FIFO/capacity, zero-wait single attempt, shared queue/lock deadline,
  poll-overshoot refusal and fresh policy comparison inside a real cross-process
  flock before any preflight probe. Matching retries bypass fresh availability
  probes; old requests never replay. Exact live monitors reserve the lane and
  exact terminal results bridge lost acknowledgements/API-receipt crashes.
- Unavailable or wrong-archive worker evidence preserves active receipts and
  blocks execution across restarts. Protocol tests cover strict explicit version,
  duplicate/oversized/truncated frames, peers/socket safety, every verification
  mode through the real shared service, integrity exit 40, exact result hash/
  bytes and no credential/Hub construction. A stale private label without a
  live owned thread is not accepted as liveness proof.
- HTTP metadata stays responsive during blocked heavy work; repeated lifespan
  cancellation cannot release store/instance ownership before joined drain.
  Real sync-producer drain retains the archive lock until producer completion.
  Classified local errors preserve failed results; unknown execution/result-save
  failures halt without inventing a different domain outcome.
- Record/link/dependency/current-pointer, decision/ADR and parity audits plus
  `rtk git diff --check` pass: 115 numbered decisions have ADRs; the API matrix
  remains 9 implemented / 20 planned rows. Archive/control record shapes and
  schema versions are unchanged; no new durable-format drill is required.
  Live Hub/NFS, installed-host and extra build-marker suites did not run.

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

Implementation continues under Tyler's authorized active plan after API-007
completed in `ad661f6`; git and the current selector were reconciled before
starting. API-008 was the sole task in progress. Collaborators shared this work
package: bounded runner/service/lock hooks; private verifier protocol/client/
entry point and app/config wiring; adversarial tests; and all Markdown records.
Contract-first review covers AD-17/19, FS-19, TX-07, INV-002/003/007/014/015,
FW-01/FW-02, decisions 109–114 and new decision 115, and plan §§5–6, loading only affected records.
Actual decision 115 is allocated from the current log, not a reserved draft ID.

This package implements one bounded execution lane and private verifier
delegation primitives. Public command submission remains API-009/010; shipped
systemd units and OS egress acceptance remain API-014. A startup-only Hub offline
flag alone is not a no-IP sandbox. No production in-process verification fallback,
new dependency, MCP work, host/archive operation, deployment, push, merge or tag
was authorized. The definitive completed gate is recorded above.

Contract-first decision 115 preserves service-owned flock acquisition and passes
trusted deadline/policy hooks instead of pre-locking a command. One absolute
host-monotonic deadline crosses the queue and private verification IPC; it is
not reset after delegation. The private verifier reuses OperationStore schema 1
under a separate protected local state directory, with trusted exact operation-ID
admission and no new durable JSON family. Its strictly bounded probe/status/submit
protocol exposes no arbitrary command/path/credential. HFAPI016 classifies an
unavailable/untrusted executor as HTTP 503 / exit 20. Architecture §7.8.2 and the
operations/recovery instructions now require proof of the actual executor's
termination before supervised recovery; stopping an API client is insufficient.

The reconciliation audit found that treating unavailable worker status like
trusted missing history would lose the barrier on the next restart. Decision 115
therefore requires preserving active receipts and closing fresh execution when
status is unsafe/unavailable; metadata/exact healthy reads remain available.
Trusted missing/interrupted status may classify the parent interrupted, exact
terminal results complete it, and a live monitor reserves the lane without
submitting. No completed domain outcome is replaced by a fabricated failure if
API result persistence fails. Deadline checks occur before each flock retry so a
poll overshoot cannot acquire after the original waiting budget.
Fresh verification admission probes the configured executor before durable
acceptance; a missing adapter refuses HFAPI016 without writing a new receipt.
Matching retries bypass the fresh-only probe. A trusted private running update
propagates domain-run identity to the parent receipt; a stale durable label with
no owned live thread is never liveness proof. Wrong-archive/operation/fingerprint
evidence is unsafe and must preserve the execution barrier rather than be
collapsed into trusted missing history.

Early focused HTTP history tests found five assertions tied to API-007's former
no-classification startup. Tests now inspect post-startup state and admit live
pagination entries during the lifespan; unsafe-history startup closes admission
without taking metadata/exact reads down. These were focused integration fixes,
not a failed full-gate attempt. Final gate evidence is recorded above.

Final private-reply review binds the startup archive UUID before progress/result
updates and validates the exact serialized Envelope hash/byte count against its
durable reference. Wrong-archive status raises HFAPI016 and cannot mutate parent
history or reopen execution. Worker status proves an owned live thread rather
than trusting a durable label. Repeated ASGI lifespan cancellation remains
shielded until runner/metadata work joins and store/instance ownership can close.

Focused evidence before the gate: final owned runner/locking/service/adversarial
selection 71 passed in 5.98 seconds; root's final HTTP/real-verifier selection
63 passed in 6.60 seconds. The broader owned selection previously passed 187 in
52.70 seconds before its final cases. Actual sync-producer drain integration
passed (1 selected, 119 deselected in 1.24 seconds). These are separate selections;
the full-gate history below distinguishes the first pass from final acceptance.

The first full gate passed 2,307 Python tests (40 deselected in 124.45 seconds),
plus every build/install/Cockpit stage. Its log is preserved as
`.scratch/api-008-gate-first-green.log`. A subsequent positive inherited-FD-3
entry-point probe found a real bootstrap ordering defect: shared runtime imports
opened `/dev/urandom` at FD 4 before the inherited-descriptor audit, so the audit
rejected a library-owned descriptor. The fix moves activation/credential-env/FD
validation before those imports without weakening the checks. Actual activated
process success and extra-inherited-descriptor refusal regressions are added.
No archive was touched by the probe. The first gate did not fail, but its result
was not final evidence for the changed source; the definitive gate therefore had to rerun.

Corrected real entry-point probe:
`rtk uv run --locked --extra server python .scratch/api-008-bootstrap.py` reported
`probe=available`, graceful exit `0`, `archive_created=false`, operation records
`0`, stdout bytes `0` and stderr bytes `0`. Automated actual inherited-FD-3 /
`LISTEN_PID` / `LISTEN_FDS` success plus extra inherited synthetic-credential-FD
refusal tests passed: 3 selected, 42 deselected in 1.84 seconds. Ruff and whole-
project types pass. The definitive full gate passed with the two added cases;
no production archive/listener or host operation occurred.

## Completion evidence

Completed 2026-10-17, API-008, this commit. One bounded FIFO heavyweight lane
persists admission before work becomes runnable, carries frozen policy/context
and one absolute host-monotonic queue/lock deadline, and retains service-owned
archive locking with fresh under-lock fingerprint validation before mutation.
Matching retries do not create work or repeat availability probes. Zero wait is
an idle single attempt; metadata uses its independent bounded pool.

Private peer-checked bounded verification delegates all modes to the real shared
service with complete target/hash/report/catalog ownership, exact trusted
operation identity and durable results. Startup imports exact terminal evidence
or reattaches a proved live worker without resubmission. Unsafe/unavailable
status preserves active receipts and closes the lane across restarts; trusted
missing/interrupted evidence permits interruption. Drain, producer lifetime,
observer loss and repeated cancellation preserve safety ownership. The real
activated-process probe/regressions verify the corrected pre-import descriptor
boundary without claiming installed no-IP enforcement.

Decision 115 and amendments to 109/110/114, AD-17/19, FW-01/FW-02 and offline
verification retain FS-19/TX-07, domain algorithms and immutable archive formats.
INV-002/003/007/014/015 enforcement, architecture §7.8.2, API/server/configuration/
CLI/security/operations/recovery/schema, README, Unreleased and plan records were
reviewed and updated. Final record/link/dependency/decision/parity/whitespace
reviews pass; the completed [progress audit](../../progress.md) accompanies this
package. No new runtime dependency or durable family is introduced.

API-009/010 retain public submission routes, API-011–013 client migration and
API-014 socket-activated units, credential-free environment/no-IP hardening and
installed-host acceptance. The startup offline flag alone does not deny IP.
No MCP, production archive/listener operation, host policy change, deployment,
push, merge or tag occurred. The current selector advances to API-009 pending.
