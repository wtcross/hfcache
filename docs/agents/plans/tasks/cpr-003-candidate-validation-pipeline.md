# CPR-003: Preserve validation evidence and reconcile configuration stages

| Field | Value |
| --- | --- |
| Status | pending |
| Plan | [Cockpit REST repair](../2026-10-19-plan-cockpit-rest-repair.md) |
| Depends on | [CPR-002 — Classify bridge failures and repair connection lifecycle](cpr-002-bridge-errors-and-reconnect.md) |
| Work package / commit | `CPR-003` — one complete package per commit |
| Implementation branch | `fix/cockpit-rest-api-alignment` |
| Authorization | Scoped source implementation authorized by the user on 2026-10-19; plan activated on the dedicated branch. Local-host development authority is qualified by the plan’s later amendment; no NAS/live workload authority. |

## Scope

Separate failed request Envelopes from candidate assessment parsing. Store and
render a valid failed Envelope even without assessment data; apply strict
candidateAssessment only to appropriate assessment output. Preserve explicit
negative assessments and field locations. Missing successful fields, unknown
schemas and inconsistent fingerprints remain refusals, not invented success.

Make read, write, validate, preview, install and confirm explicit phases with
acknowledgement and uncertainty. Preserve exact captured draft/base in memory
across bridge interruptions; add guarded read-only inspection only as needed to
reconcile the fixed files. A lost candidate-write acknowledgement must not lead to
blind cleanup or another write. Changed/unknown candidate or base invalidates
readiness and explains how to reload safely.

Keep all existing lock, ownership, byte bound, no-follow, fsync and atomic backup /
rename invariants. Never replace exact comparisons with the policy fingerprint:
tag-only edits can share it. Enforce exact installed content before and after API
validation and required successful confirmation process/postchecks.

Retain cause and phase under the unconfirmed-installation warning. Never retry
installation, roll back, delete a candidate or restore readiness automatically after
lost acknowledgement. Keep user-visible validation errors separate from preview
and install errors. Integrate the operation registry for sizing when CPR-004 lands;
this task must expose a clear callback/record seam rather than silently discarding
preview handle evidence. A synchronous validation receives no artificial key/ID.

## Acceptance criteria

F02 and F03 are fixed without relaxing assessment or filesystem guards. Valid
candidates, invalid candidates, API/client refusals, incompatible/unknown authority
and missing installed policy have distinct observable results. Every failure
prevents installation. Reconnect/reconciliation, concurrent edits and uncertain
install preserve exact bytes/backup and require fresh proof. Original error codes
remain visible instead of being replaced with an “update plugin” schema error.

## Contracts, invariants and ADRs

Update docs/cockpit.md configuration/error sections, docs/configuration.md and
Cockpit usage/troubleshooting. Review CP-11, INV-006, decision 122's exact installed
confirmation amendment, and the tag-only identity boundary from decision 133.
No REST install endpoint or restart requirement for ordinary policy changes is
introduced.

Use [the design](../support/cockpit-rest-repair/design.md),
[the audit](../support/cockpit-rest-repair/audit.md) and
[the validation matrix](../support/cockpit-rest-repair/validation-matrix.md).
Review the current [invariant register](../../../invariants.md) and
[ADR index](../../../adr/README.md), not only this draft's summary. Update relevant
human contracts, ADR status/links and invariant text in the same implementation
commit. No live-host privilege or workload authority is granted by a task status.

## Validation

**Planned, not executed:** Extend config-pipeline, guarded-filesystem and rendered Configuration tests for
V09–V21 plus V01/V11. Use temporary private fixtures, including symlink/link/mode,
concurrent editor and failed postcheck cases. Test authentic CLI failure-Envelope
shapes, not only successful mocked assessments. Preserve server candidate tests
and run the complete gate.

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
commit use `CPR-003, this commit`; after commit, record only actual git evidence.
