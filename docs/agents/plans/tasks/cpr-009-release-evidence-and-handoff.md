# CPR-009: Complete release evidence, documentation, and operator handoff

| Field | Value |
| --- | --- |
| Status | completed |
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
No merge, tag, deployment or live operation occurs as a side effect. Later user
authorization allows only the completed branch push to Forgejo and GitHub after
final commit, with explicit ref verification and no tags/force push.

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

Final actual commands pass, frontend executed:

- `rtk proxy scripts/check.sh --with-build --require-cockpit`: exit0;
  5299Python/52deselected in757.36s, all3locked wheel profiles, actual frontend
  lint/style/types/570unit0skip/110mounted/fresh production build, then16build
  cases/5335deselected in45.18s (old-wheel2/smoke4/installedCLI-UDS10).
- Separate final `rtk proxy make -C cockpit check`: exit0,570unit/110mounted,
  lint/style/types/fresh production build. Earlier new-test literal formatting
  failure remains recorded; corrected before final runs.
- Focused docs/config/CLI/routes/releases/runtime/profile578passed79.47s;
  identity/command45passed; Diagnostics4/4 including intentional identity skew;
  scoped ESLint/types and independent human install/acceptance/handoff review pass.
- Two owned DESTDIR make installs verify exactly five asset bytes and documented
 077vs022 modes, retaining private outer0700; no host installation.
- Final installed wheel638a3274…cec1b matches all90source runtime modules and current
  README metadata; native fixture wheel578fd699…8392d remains separately identified.

[Complete V01–V60 acceptance](../support/cockpit-rest-repair/acceptance-record.md),
[commands/hashes](../support/cockpit-rest-repair/gates/cpr-009.txt),
[operator handoff](../support/cockpit-rest-repair/operator-handoff.md).
Final closeout metadata/documentation checks pass: lockedcheck-docs188human/
19helpers, docs/config/historical acceptance65tests in6.22s, rawdiffcheck0 and
direct9task/plan/selector/V01–V60/link consistency. Evidence includes log hashes.

## Execution notes and handoff

Started2026-10-20 after clean CPR-008 commit
0dc2c93da04bd38f28770e2f3576f30720cf1533. Re-read git/current/task, release,
INV011 and technical-record authority. One active package; source/runtime gates
through8 pass, no mandatory blocker. Preserve all five isolated fixtures and
unknown/unconfirmed history. Native actual timer/NUL/PID1stdout defects are fixed;
production installation and original installed cause/symptom remain unproven.
Review F01–F11/V01–V60, correct stale human installation/report/manual-operation
and historical release-authority text, record exact clean-build/deploy/rollback
handoff, and execute final explicitmake plus extendedstrictgate (including old
wheel/durable compatibility). No runtime feature, dependency, version bump,
registry, install, production/NAS operation, push/merge/tag or unrelated backlog
activation is authorized by this package. Existing public install helpers require
reviewed readable asset modes; verify in owned DESTDIR only, never host install.
Next: finish docs/parity review and safe artifact/install-path evidence, then final
gates, precise operator handoff and scoped selector closeout.

## Completion evidence

2026-10-20, CPR-009, this commit: all acceptance and required source/disposable
checks pass. F01–F11 and exactly V01–V60 are traceable. All nine tasks complete;
plan completed/current selector cleared, historical records/backlog retained.
Reviewed CP01–14/INV005/006/agentINV011 and actualADR134–139 plus affected older
amendments. No new architectural decision/invariant edit, runtime feature,
dependency, durable schema, API/MCP capability or version change in this package.
Human docs now agree on REST manual jobs/reports, fresh public install modes,
identity/cache distinctions and preservation-safe recovery/removal. Five owned
native guests, original locks/handles/backups and unknown/unconfirmed attempts
are preserved. Production parity/original installed symptom and NAS/workload
holds remain separate. Later user explicitly authorizes completed branch pushes
to both configured remotes after commit; no merge/tag/force/registry/deployment.
[Completed progress](../../progress.md#cockpit-rest-repair-2026-10-19) and
[operator handoff](../support/cockpit-rest-repair/operator-handoff.md).

Final review adds one planned V55 controlled mounted identity-skew regression; it
asserts selected image/index and distinct authenticated public profile/API identity
without inventing a running API source/image comparison. Existing109case explicit
frontend pass is a prefocused snapshot; final expanded gate passes above.
Owned DESTDIR probes under077/022 both exit0 and observe the documented unreadable
vs public modes, with exact five-asset byte equality. Private fixture parent stays
0700; no host install or production ownership/readability proof is claimed.

2026-10-20 later user steering explicitly authorizes final completed branch pushes
to Forgejo and GitHub after commit. Both exact remote branch refs were absent
at read-only preflight (exit0). Preserve nine commits; push only the explicit
branch without tags/force and verify both advertised refs. Earlier no-push
execution note records startup authority; the dated plan amendment owns this
narrow subsequent exception. All production/NAS/merge/tag/registry limits remain.
