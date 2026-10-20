# CPR-005: Align manual operations and guarded host controls

| Field | Value |
| --- | --- |
| Status | completed |
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

Executed source fixtures cover V35–V40 and scoped V49/V51 with exact argv/request route assertions and denied /
unknown/permitted profile fixtures. Assert fixed-manager and target/timer allowlist
rules at adapter level, not just disabled buttons. Verify full job receipt/result
parity through the actual client and run the complete gate.

Each package must pass the repository gate with the Cockpit portion actually run.
Do not report test counts, exit codes or commit hashes until observed. Record
commands/environment and any separately blocked disposable/installed checks.

## Execution notes and handoff

Started2026-10-20 after CPR-004 ca034e3 with clean source and full gate5101 Python,
412 unit/47 mounted frontend green. Sole active task on the existing branch.
Revalidated service-start full-job paths and schedule writes lacking an adapter
profile gate. Amend CP04 before changing full jobs; retain fixed rootless client,
system-manager schedule/observer identities, all guards/masks/hardening and final
server policy/lock authority. Introduce only narrow read-only selected-profile
facts plus explicit root-provisioned permissions, never inferred approval from an
absent guard. Missing/mixed/unsafe facts fail closed. No production/runtime
provisioning or guard transition is part of this source package.
Decision 135 was allocated after actual decision 134 and accepted before source
changes. It amends CP-04 while retaining the direct-report exception for CPR-006.
Current-source real Cockpit/PAM fixture acceptance remains unpassed for CPR-008;
the prior guest/guards/candidate/evidence stay unchanged.

Source now implements manual keyed full jobs, fresh six-category permission gates,
bounded protected root-only inspection and denied current-rootless schedule/observer
permissions. The existing nine bindings and normal launcher/service roles remain.
Actual subprocess CLI/private Unix socket tests pass three full-job/result/recovery
cases; 61 protected host-inspection tests pass. Mounted direct-call bypass tests
were observed red, then green; final62 component cases pass. Full
`rtk proxy scripts/check.sh` passed with actual frontend execution; output is
`/tmp/hfcache-cpr005-gate.log`. Review findings additionally reproduced/fixed
mutable/unknown sender dispatch and post-acknowledgement schedule uncertainty,
including pending/failed component remounts. Next specific action: commit this
accepted package, then start CPR-006. Real current-source Cockpit/PAM remains V54.

## Completion evidence

Completed 2026-10-20, CPR-005, this commit. [Accepted gate](../support/cockpit-rest-repair/gates/cpr-005.txt):
`rtk proxy scripts/check.sh` exit0; 5165 Python passed/42 deselected in829.52s,
all three locked wheel profiles, actual Cockpit lint/style/types,436 unit tests,
62 mounted Firefox cases and production build. No frontend skip. Focused actual
CLI/private Unix socket/private verifier3 cases and protected host proof61 cases
pass; component/pure regressions preserve fail-before evidence for direct gates,
immutable/closed dispatch, calendar injection, partial host mutations and remounts.

Manual full jobs now share original-key REST recovery; scheduled observers remain
separate. Fresh root-provisioned six-category permissions, indexed release proof,
bounded host facts and guarded configuration checks enforce effects. Current
rootless scheduled bindings remain unsupported, so schedule/observer permissions
are effectively denied. Bounded app-memory schedule attempts retain pending and
uncertain effects across tabs; explicit exact read/ack never reloads/restarts.

CP04/related CP boundaries and INV006 reviewed; actual next ADR135 allocated and
accepted, ADR89/122/134/index/invariant register and human Cockpit/usage/container/
deployment/operations docs amended. CP09 report exception remains for CPR-006.
No dependency, archive schema, REST route, credential, scheduler or binding change.
Completed progress entry and operator handoff accompany this package. Required
current-source Cockpit/PAM V54 and original installed cause remain unproven; no
production/NAS/old-guest changes. Continue CPR-006; no unrelated backlog activation.
