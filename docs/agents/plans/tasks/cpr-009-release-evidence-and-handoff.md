# CPR-009: Complete release evidence, documentation, and operator handoff

| Field | Value |
| --- | --- |
| Status | pending |
| Plan | [Cockpit REST repair](../2026-10-19-plan-cockpit-rest-repair.md) |
| Depends on | [CPR-008 — Prove the browser, launcher, CLI, and API boundaries](cpr-008-cross-boundary-regressions.md) |
| Work package / commit | `CPR-009` — one complete package per commit |
| Implementation branch | `fix/cockpit-rest-api-alignment` |
| Authorization | Scoped source implementation authorized by the user on 2026-10-19; plan activated on the dedicated branch. Local-host development authority is qualified by the plan’s later amendment; no NAS/live workload authority. |

## Scope

Review every finding against its fix and evidence, and every V01–V60 case against
the final source/fixture results. Close omissions within the authorized scope
through a separately recorded additional package if needed; do not squeeze
unrelated changes into this final commit or fabricate completion.

Finish human documentation as needed, including installation/profile prerequisites,
real candidate troubleshooting, manual-vs-scheduled operation semantics, reports,
recovery commands, security boundaries and source/deployment status. Preserve the
historical record; add release notes and a precise operator handoff rather than
rewriting old completed evidence. Update executable/help/route maps for new report
CLI commands and all affected ADR/invariant references.

Produce a reviewed build/install/rollback handoff identifying browser bundle,
application commit, physical launcher/profile tree and image digest. Check static
package release consistency, install paths, caching/version diagnostics and profile
compatibility with existing protected installers. The handoff must preserve old
receipts, backup and unknown execution; source rollback cannot declare jobs stopped.
Do not run the installation or publish artifacts to a registry in this task.

Run final full/extended gates, including actual frontend checks. Fill the acceptance
record with real output and explicit source vs disposable vs installed vs workload
gates. Leave production symptom acceptance and retained NAS/workload restrictions
with the operator, without claiming that the reported host has already been fixed.
Complete task/plan and clear current only after scoped source and required
disposable-runtime acceptance passes; do not activate old backlog.

## Acceptance criteria

The source-remediation plan is traceably complete, required gates and disposable
runtime proof are green, documentation agrees with code, and source/install identity
and rollback requirements are recorded. Production installation, original-host
symptom verification and NAS/workload acceptance remain separately unauthorized /
pending unless a later explicit instruction supplies that authority and evidence.
No push, merge, tag, deployment or live operation occurs as a side effect.

## Contracts, invariants and ADRs

Review all touched register/ADR sections, planning/workflow INV-011, technical
record policy, release/deployment status and current operator handoff. Record which
requirements were unchanged as well as which were amended. Preserve historical
plans, receipts and acceptance holds.

Use [the design](../support/cockpit-rest-repair/design.md),
[the audit](../support/cockpit-rest-repair/audit.md) and
[the validation matrix](../support/cockpit-rest-repair/validation-matrix.md).
Review the current [invariant register](../../../invariants.md) and
[ADR index](../../../adr/README.md), not only this draft's summary. Update relevant
human contracts, ADR status/links and invariant text in the same implementation
commit. No live-host privilege or workload authority is granted by a task status.

## Validation

**Planned, not executed:** Run scripts/check.sh --with-build and make -C cockpit check with no frontend skip;
run documentation alignment and release-artifact consistency checks required by
existing tooling. Audit V55–V60, the manifest/source comparison, all task evidence
and progress/current links. Record actual results in acceptance-record.md and
link them here and in the completed progress entry.

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
commit use `CPR-009, this commit`; after commit, record only actual git evidence.
