# CAT-016: Complete lifecycle compatibility drills, documentation and plan handoff

| Field | Value |
| --- | --- |
| Status | complete |
| Plan | [Tags and discovery](../2026-10-19-plan-tags-and-discovery.md) |
| Phase | 6 — Acceptance |
| Depends on | [CAT-008](cat-008-sync-metadata-lifecycle.md), [CAT-009](cat-009-offline-refresh-service.md), [CAT-015](cat-015-adversarial-and-parity-validation.md) |
| Implementation branch | `feat/tags-and-discovery` |
| Commit boundary | One package / one commit: `CAT-016: <completed outcome>` |

## Required context

Follow `AGENTS.md` and `docs/agents/workflow.md`. Read relevant sections of the
[design](../support/tags-and-discovery/design.md),
[source review](../support/tags-and-discovery/source-review.md) and
[validation matrix](../support/tags-and-discovery/validation-matrix.md).
The status table and completion evidence below record actual execution; scope
requirements alone are not successful-check evidence.

## Likely implementation touchpoints

All affected product guides and ADRs; schema/install compatibility fixtures; release handoff docs; all task evidence/current selector.

Inspect actual callers and tests before editing. Suggested new module names are
not requirements to create redundant layers when an existing small abstraction fits.

## Scope and requirements

Run synthetic lifecycle coverage for config edit/disable/removal/re-add, sync no-op, refresh, repair, prune and purge. Inert supplemental files cannot override reference/manifests or revive removed inventory; verification confidence remains keyed to exact publication. Document last-observed capture limits, missing observations and metadata growth without inventing automatic cleanup.

Test old config and durable artifact goldens plus actual supported old-binary refusals around tags, new directory layout and new operation kinds. Preserve unsupported state, and document a guarded non-destructive operator rollback and backup procedure. Do not run it on production or make a universal compatibility claim solely because schema_version stayed 1.

Finish the human documentation matrix in the parent plan, with executable fictional examples, exact route/tool/CLI names, normalization, provenance/coverage, variant evidence limits, dataset declarations, auth, budgets, offline refresh and compatibility. Ensure docs outside agents contain no CAT package links or execution narration. Run the existing documentation checker rather than replacing it with an allow-all rule.

Run full offline, frontend, build and supported installation-profile gates. Verify base reader excludes optional frameworks and extraction runtimes, REST-only remains usable, and MCP profile has only authorized tools. State precisely which live/NFS/deployment acceptances were not run. No push/merge/tag/deploy/credential action is authorized.

Audit every matrix scenario and task acceptance against actual evidence/commits. Close the plan only when all scoped packages pass (or an explicitly authorized scope amendment disposes of canceled work), clear the active selector, keep completed files at original paths, update progress/decisions/handoff and commit the final package. Report branch and incremental commit summary with remaining operator prerequisites.

## Acceptance criteria

All sixteen work packages and plan acceptance criteria have actual evidence. scripts/check.sh --with-build passes and the frontend gate ran. Documentation/current selector/progress agree, old evidence stays intact and rollback limits are accurate. No unperformed production acceptance or undeclared scope omission is presented as complete.

## Contracts, invariants and ADRs

Review the affected current human contracts and `docs/invariants.md` through its
index; consult related technical ADRs listed in the source review. Record explicit
changes or an explicit no-impact finding in completion evidence. Amend contracts
in the same commit as behavior; add required ADR/index/progress decision entries
without copying agent task narration into human guides. Do not silently override
a filesystem, security, format, candidate, read-budget or MCP boundary.

## Validation

Matrix coverage: V51, V52, V53, V54, V55

Run scripts/check.sh --with-build, verify frontend execution and install-profile results, run compatibility/lifecycle fixtures and documentation audit, inspect complete git diff/log/status and task graph.

Every package requires `scripts/check.sh` exit 0, including docs-only work. Required
frontend checks must actually execute for frontend changes. Offline fixture success
does not imply live Hub/NFS or deployed acceptance. Missing prerequisites and failing
tests remain blockers, with their exact unblock condition recorded below.

## Execution notes and handoff

CAT-001 through CAT-015 are committed with green per-package gates. Final scope
is synthetic lifecycle acceptance, actual isolated installed wheels from reviewed
pre-feature 75d93a5 and recorded deployed application source 4088994, complete
V01-V55 evidence, human documentation and scripts/check.sh --with-build. Both
targets use package version 0.2.1; source/wheel identity will distinguish them.
Reviewed INV-002/006/012/014-016/018, FS/TX/AD and decisions 65/78/114-125/133;
no deployment, live/credential/host/push operation is authorized.

Actual end-to-end repair/prune/purge/config-history and all visible cursor-change
cases: 7 passed in 3.39s. New evidence-reference/workflow audit plus lifecycle:
9 passed in 3.51s. The audit resolves every V01-V55 reference to actual Python or
frontend tests and verifies the fifteen predecessor commits each contain their
completed task, progress and selector records. Both accepted historical spellings
of completed status are preserved. No unrelated backlog is activated.

Actual installed compatibility targets 75d93a5 and 4088994: 2 passed in 14.28s.
All 69 installed Python source files match each exact old source export, all 17
original goldens remain byte-identical/parseable, and actual old factories retain
nine tools. Tag-free/empty-tag/nonempty-tag CLI validation exits are 0/10/10.
Controlled empty layouts isolate HFMNT014 for the optional namespace; ordinary
inventory still reads. Old strict client routes refuse refresh, while generic
stores preserve completed Envelopes and old runners interrupt queued work without
replay. [Observed artifact hashes/results](../support/tags-and-discovery/compatibility-results.json)
retain exact focused evidence. Version strings alone are not binary identity.

Early focused fixture failures exposed a stale pre-no-op observation comparison
and incorrect InstalledPolicy/Path argument construction (two old-target failures
in 11.17s, then two in 13.93s). Fixtures were corrected; no product behavior was
weakened. Initial audit assumptions about a test name/completed spelling were
corrected before the passing audit. All-source lint/format/types and human
alignment pass. The final extended gate passed as recorded below. Human navigation/release notes,
current discovery, lifecycle/backups and observed guarded rollback are updated;
INV-018/decision 133 enforcement and rationale link the actual target probes.

## Completion evidence

Completed 2026-10-19 (CAT-016, this commit). Final
`scripts/check.sh --with-build` exited 0: 5008 offline tests passed/42 opt-in tests
deselected in 583.36s; all three locked isolated installation profiles passed;
actual Cockpit lint/types/170 tests/production build passed with zero skips;
extended build stage passed 6 tests/5044 deselected in 18.26s, including both
actual installed-old-wheel targets and current clean-wheel smoke. Earlier focused
lifecycle/cursor/evidence selection passed 9 in 3.51s; installed target probes
passed 2 in 14.28s with preserved artifact hashes/results. No required gate is
skipped or red. Live Hub/NFS, deployed/browser/host acceptance was not run.

All V01-V55 references resolve to concrete tests in
[acceptance evidence](../support/tags-and-discovery/acceptance-evidence.json), with
per-package gates retained in their task records and incremental commits.
All sixteen packages are complete; the dated plan is complete and current.md is
inactive. Human README/navigation/release/development/discovery/schema/operations/
recovery/rollback guidance is current; original 17 evidence goldens remain intact.
INV-002/006/012/014-016/018, FS/TX/AD and decisions 65/78/114-125/133 were reviewed;
INV-018/decision 133 record lifecycle and actual compatibility enforcement.
[Completed progress](../../progress.md#tags-and-discovery-2026-10-19) and
[operator handoff 24](../../progress.md#operator-handoff) retain verification,
rollback and separate deployment prerequisites. No runtime dependency, production
archive/service/timer/hardening/credential action, live workload, deployment,
push/merge/release tag or registry publication was performed. Source remains
on feat/tags-and-discovery; no old backlog or production authority is activated.
