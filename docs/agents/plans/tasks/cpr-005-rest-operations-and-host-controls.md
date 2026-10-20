# CPR-005: Align manual operations and guarded host controls

| Field | Value |
| --- | --- |
| Status | pending |
| Plan | [Cockpit REST repair](../2026-10-19-plan-cockpit-rest-repair.md) |
| Depends on | [CPR-004 — Retain operation handles and prevent uncertain resubmission](cpr-004-operation-recovery-and-replay-guards.md) |
| Work package / commit | `CPR-005` — one complete package per commit |
| Implementation branch | `fix/cockpit-rest-api-alignment` |
| Authorization | Scoped source implementation authorized by the user on 2026-10-19; plan activated on the dedicated branch. Local-host development authority is qualified by the plan’s later amendment; no NAS/live workload authority. |

## Scope

Replace manual full sync and full verification service-start paths with the
existing shared REST-backed CLI job flow (`sync`, `verify --full`), only after
amending CP-04 and recording the architectural distinction. Preserve scheduled
observers as separate host objects; a manual job is not their service process.
Display operation receipts/results/events as execution evidence, not systemd
ExecMainStatus or journal text.

Introduce or reuse a minimal trusted read-only profile/host-state adapter to expose
supported deployment identity, fixed launcher binding, system-unit availability
and current restriction facts without secrets. Unknown/mixed/drifted state refuses;
absence of a mask/guard does not grant write approval. Explicit permitted-profile
evidence must be provisioned by trusted host configuration, not a browser toggle.
No live provisioning occurs as part of this source task.

Disable prohibited archive-effecting actions consistently on the selected guarded
profile, including full/selected sync, actual verification and maintenance apply.
Explain the retained holds. Differentiate ordinary metadata/validation from sizing
and diagnostics which may contact Hub or write control receipts. Server capability,
policy, lock and storage checks remain final authority.

Keep timer/drop-in operations on the fixed system bus. Masked or unavailable
profiles refuse schedule changes before writing files. Do not retarget to user
units, unmask timers, operate hfcache.target or enable the verification timer.
Stop observing a manual job only detaches its view; it never stops API/worker or
promises cancellation. Tests for the permitted profile use isolated explicit
fixtures, never the production guard as a test surface.

## Acceptance criteria

Manual full jobs and selected jobs share operation recovery semantics in a
supported permitted fixture. The guarded real profile remains restricted; unknown
state cannot enable workload or schedule effects. Full verification remains the
server's offline private executor. Legacy system-unit masks stay intact and no
user-manager redirection or cancellation shortcut exists.

## Contracts, invariants and ADRs

Amend CP-04 operation tables, related register entries, ADR122 and relevant
older Cockpit ADR status/links; preserve CP-05/06/07/08/10/13 and decision127
boundaries. Update operations/deployment/Cockpit guides so source support does not
claim installed workload acceptance.

Use [the design](../support/cockpit-rest-repair/design.md),
[the audit](../support/cockpit-rest-repair/audit.md) and
[the validation matrix](../support/cockpit-rest-repair/validation-matrix.md).
Review the current [invariant register](../../../invariants.md) and
[ADR index](../../../adr/README.md), not only this draft's summary. Update relevant
human contracts, ADR status/links and invariant text in the same implementation
commit. No live-host privilege or workload authority is granted by a task status.

## Validation

**Planned, not executed:** Cover V35–V40, V49 and V51 with exact argv/request route assertions and denied /
unknown/permitted profile fixtures. Assert fixed-manager and target/timer allowlist
rules at adapter level, not just disabled buttons. Verify full job receipt/result
parity through the actual client and run the complete gate.

Each package must pass the repository gate with the Cockpit portion actually run.
Do not report test counts, exit codes or commit hashes until observed. Record
commands/environment and any separately blocked disposable/installed checks.

## Execution notes and handoff

Not started. On activation/resumption, record source drift, exact implementation
scope, relevant runtime cause evidence, and any blocker with its unblock condition.
Do not rewrite this section as completed merely because the plan was extracted.

## Completion evidence

Pending. Replace with the completion date, accepted test/fixture results, executed
gate evidence, invariant/ADR review outcome, changed docs, remaining operator
handoff, and the corresponding completed `docs/agents/progress.md` entry. Before
commit use `CPR-005, this commit`; after commit, record only actual git evidence.
