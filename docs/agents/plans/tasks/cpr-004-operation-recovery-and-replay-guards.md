# CPR-004: Retain operation handles and prevent uncertain resubmission

| Field | Value |
| --- | --- |
| Status | pending |
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

**Planned, not executed:** Cover V18, V22–V34, V51 and all identified non-streaming submit call sites. Use
component tests with actual unmountOnExit lifecycle, a controlled before-notice
channel failure, key conflicts and hostile storage records. Test option/quote
boundaries and assert zero additional POSTs after uncertainty. Run the full gate.

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
commit use `CPR-004, this commit`; after commit, record only actual git evidence.
