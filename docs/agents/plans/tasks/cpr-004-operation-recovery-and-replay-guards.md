# CPR-004: Retain operation handles and prevent uncertain resubmission

| Field | Value |
| --- | --- |
| Status | completed |
| Plan | [Cockpit REST repair](../2026-10-19-plan-cockpit-rest-repair.md) |
| Depends on | [CPR-003 — Preserve validation evidence and reconcile configuration stages](cpr-003-candidate-validation-pipeline.md) |
| Work package / commit | `CPR-004` — one complete package per commit |
| Implementation branch | `fix/cockpit-rest-api-alignment` |
| Authorization | Scoped source implementation authorized by the user on 2026-10-19; plan activated on the dedicated branch. Local-host development authority is qualified by the plan’s later amendment; no NAS/live workload authority. |

## Scope

Implement the application-scoped operation registry and validated, bounded
session persistence described in the design. Generate and durably record a safe
idempotency key before the submit process starts; pass that exact key using the
existing global CLI option, then validate matching key/ID notices independently
of display-log truncation. No arbitrary argv, raw TOML, token or log storage.
Handle storage failure/corruption explicitly rather than silently submitting
without promised recovery durability.

Scope records to trusted host/client-profile/endpoint and credential-class evidence,
plus validated archive identity when known. Treat unconfirmed scope as such. Do
not follow saved handles through a changed or unknown API authority. Preserve
original records on timeout, expired history, unknown result, detach, or conflict.

Integrate every keyed call site: candidate/installed sizing, diagnostics, all sync
and actual verification modes, maintenance dry runs/applies and repair. Fix
DryRunApplyCard's exact stale-successful-preview plus apply-spawn-failure path:
caught-error/registry uncertainty must block a repeat, even when no applied
Envelope exists. Ensure modal confirmation cannot race a second submit.

Move recovery controls outside tab lifetime and add explicit lookup/wait using
the same fixed adapter. Correct copied commands to the shipped rootless profile,
including service identity, selected settings/socket and safe key quoting/`--`.
Do not automatically generate a replacement key or POST replay, including when
lookup returns missing history. Observing may be resumed only within valid scope;
no server cancellation or recovery action is added.

## Acceptance criteria

F04/F05/F10 and candidate preview handle loss are repaired. Keys survive failure
before the first CLI notice; tab switch, remount and reload retain recoverable
records. An uncertain maintenance Apply remains blocked rather than relying on an
old dry run. Every retained handle is safe data and original authority is checked.
Lookup/wait cannot submit or cancel. Non-job reads/validation create no fake jobs.

## Contracts, invariants and ADRs

Update Cockpit operation/recovery docs, CLI integration guidance and affected
ADR122 semantics. Review CP-02/08/10/11, INV-006 and API idempotency/receipt
contracts. Browser storage is a recovery convenience, never domain authority or
a place for credentials/configuration.

Use [the design](../support/cockpit-rest-repair/design.md),
[the audit](../support/cockpit-rest-repair/audit.md) and
[the validation matrix](../support/cockpit-rest-repair/validation-matrix.md).
Review the current [invariant register](../../../invariants.md) and
[ADR index](../../../adr/README.md), not only this draft's summary. Update relevant
human contracts, ADR status/links and invariant text in the same implementation
commit. No live-host privilege or workload authority is granted by a task status.

## Validation

Executed focused evidence: 106 registry/runner cases, 47 mounted Firefox cases,
152 CLI/client metadata/secret-collision/launcher cases and 87 guarded
filesystem/command/Envelope cases passed. These include actual Application
unmountOnExit/reload, browser quota, before-notice failure, original lookup/wait,
candidate original-sizing recovery, stale acknowledgement and conflicting
observation notices. See [core evidence](../support/cockpit-rest-repair/gates/cpr-004-registry.txt),
[components](../support/cockpit-rest-repair/gates/cpr-004-components.txt) and
[acceptance](../support/cockpit-rest-repair/acceptance-record.md).
First full gate passed with 5088 Python/42 deselected, three wheel profiles,
409 frontend unit/45 mounted cases and production build. Eleven new launcher
regressions were added after its collection; a full retry selected5099.
A help-text line-length error stopped the first retry at lint;
corrected without changing behavior, then restarted the complete gate. That run
finished 1 failed/5098 passed/42 deselected in673.08s: the real truncated Unix
response fixture received ReadError during response headers instead of the intended
body-truncation RemoteProtocolError. No frontend stage ran in that failed retry.
Investigation reproduced the exact empty-write → BrokenPipe → premature close →
EBADF/ReadError chain. Empty writes now match the locked backend's no-op contract;
the unchanged original truncated fixture passes200/200 repeats, deterministic
actual-socket regressions were red before and green after, and all20 transport
tests pass. This is an actual source defect, not a timeout or fixture relaxation.
The final full gate passed from the frozen corrected source,5101 selected.
Separate `make -C cockpit check` passed412 unit/47 mounted cases, lint/style/types
and production build. Final log: /tmp/hfcache-cpr004-accepted-gate.log.

Latest additional source evidence: 106 core cases and47 mounted cases pass,
including failed captured revalidation retaining its original cause and restored
terminal summaries remaining unverified until authenticated original observation.
A valid-looking forged summary cannot resolve uncertainty; contradictory/missing
history retains handles and blocks another submission. The owned test coordinator
was briefly paused before frontend to keep deliberate red regressions out of the
acceptance run, then resumed; no application/guest process was paused or cancelled.

Each package must pass the repository gate with the Cockpit portion actually run.
Do not report test counts, exit codes or commit hashes until observed. Record
commands/environment and any separately blocked disposable/installed checks.

## Execution notes and handoff

Started after CPR-003 commit65b12d9. Sole active task, on the same dedicated
branch with clean source after the prior full gate. Implement bounded scoped
original-key recovery before transmission, every keyed call site, maintenance
uncertain Apply gating and actual Application tab/reload regressions. Add only
narrow validated read-only client authority metadata where needed; no new API
route or arbitrary forwarding. Isolated runtime setup may continue from the
exact retained prerequisite in runtime-003, preserving all failed evidence and
guards; no production/NAS effect or installed-cause claim.

Implemented safe seven-field authenticated `client describe` plus compare-only
same-process scope pin; no new REST route, credential input or routing selector.
The bounded session registry persists original keys before spawning, preserves
late IDs across detached views and blocks further keyed submissions on the same
host while uncertain. Explicit recovery never POSTs. All current keyed page calls
share this path; full-service/report exceptions remain for CPR-005/006.
Review fixed stale configuration acknowledgement after authority drift and
recovery observations that ignored a single conflicting notice. Both fixed
launcher hops now honor positional -- rather than consuming --help/-h handles.
Readonly pin/confirmation never adds a fake job key. Exact classified Envelopes,
original handles and prior summaries remain independent of later boundary faults.

The isolated older-artifact runtime now passes actual rootless launcher/UDS and
guarded candidate validation. [Exact runtime record](../support/cockpit-rest-repair/runtime-004.md)
retains failed starts, original guard and staged candidate. Current immutable
artifact and real Cockpit/PAM/reconnect acceptance remain CPR-008; no production
installation, service/configuration, NAS or original-symptom acceptance is claimed.

## Completion evidence

Completed 2026-10-20, CPR-004, this commit. Final `scripts/check.sh` exit0:
5101 Python passed/42 deselected in606.10s, all three locked wheel installation
profiles, actual Cockpit lint/style/types,412 unit/47 mounted Firefox cases and
production build. Explicit `make -C cockpit check` also exit0. Final log SHA256
fc6b29adf0906f7f367f280ca7186355998517bca24478ece6ae045e8ebf6038;
[gate record](../support/cockpit-rest-repair/gates/cpr-004.txt),
[components](../support/cockpit-rest-repair/gates/cpr-004-components.txt).
Behavioral red/green covers original pre-send keys, detached identity capture,
actual tab/reload/quota, uncertain maintenance Apply, original candidate sizing,
authority invalidation, conflicting recovery notices and untrusted terminal
summaries. Both fixed launcher hops honor --; actual Unix response ownership now
survives empty end-of-message writes with20 focused socket tests/200 repeated
original-case passes. Earlier failures remain evidence; no mocked runtime pass.

Reviewed/amended CP02/08/10/11, INV006 and ADR119/122/134, including index and human
CLI/client/Cockpit/usage/troubleshooting contracts. No new dependency/API route/
archive format or credential/guard permission. CP04/09 exceptions remain for the
next packages. Completed progress entry and next pointer CPR-005 accompany this
commit. Required current-source disposable Cockpit/PAM acceptance remains unpassed;
runtime-004 pins the older isolated fixture. Original installed cause is unknown,
production/NAS untouched. Continue directly with CPR-005 on this branch.
