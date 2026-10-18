# DOC-019: Audit final alignment and close the correction plan

| Field | Value |
| --- | --- |
| Status | pending |
| Plan | [REST/MCP documentation and script alignment](../2026-10-18-plan-rest-mcp-docs-scripts-alignment.md) |
| Depends on | [DOC-018](doc-018-automated-docs-and-interface-alignment-gate.md) |
| Phase | 3 — Prevent recurrence and close |
| Review findings | F01, F02, F03, F04, F05, F06, F07, F08, F09, F10, F11, F12, F13, F14 |
| Suggested commit | `DOC-019: complete documentation and script alignment audit` |

## Scope and implementation requirements

Re-read the final human documentation from the reader, writer administrator, MCP client user and contributor perspectives. The user should not need to reconstruct the implementation sequence or open an agent record to use the system. Audit every confirmed finding and every candidate disposition against the final source.

Require a final removal/retention ledger: removed dead symbols with search/coverage evidence; removed obsolete prose with a current replacement or preserved evidence location; retained scripts with supported purpose; unchanged intentional compatibility artifacts. Do not label a remaining candidate completed without recording a justified retention or implementation outcome.

Verify all migration hashes/path mappings, preserved completed records, current contracts and active task pointers. All human guides must be free of agentic-implementation references. Keep operator prerequisites/current restricted-deployment facts in human form, while all work-package evidence stays under agents.

Run the full repository gate with required optional profiles, build smoke, documentation/interface checks and affected Cockpit checks. Record exact commands/results and any explicitly unrun live/host cases. Verify the diff contains no changes to live deployment, credentials, NAS state, release selection, tags or remote publication. No version bump is required for a documentation alignment plan unless independently authorized release work is added.

Complete this task and plan only after their acceptance criteria pass. Clear `docs/agents/plans/current.md` to no active plan, retaining the completed plan/tasks at their migrated stable paths. Do not activate unrelated backlog or claim live NAS acceptance from fixture success.

## Acceptance

- [ ] Every finding is corrected or has a technically justified, explicit disposition within scope; no unexplained deletion/candidate remains.
- [ ] Human docs and public help contain zero agent implementation references, and no required behavior was removed with historical prose.
- [ ] All supported scripts/profiles and the exact REST/MCP/CLI contract are covered by passing offline checks.
- [ ] Full required gate/build/Cockpit results are recorded honestly; live host/NAS validation remains not run unless separately authorized.
- [ ] Final commit includes task/plan/selector/progress evidence, then leaves no active plan; feature branch history remains incremental and unpushed.

## Contracts, invariants and ADRs

All acceptance criteria in this plan, the revised documentation/agent authority split and unchanged storage/security/deployment invariants.

Paths above use the reviewed repository's names for identification. DOC-011 owns
the authoritative relocation map; after that package use the current path and
preserve the same contract/record identity. Read relevant sections progressively.
Record an explicit no-impact review when no technical invariant changes; do not
create a ceremonial technical ADR for an editorial-only change.

## Documentation in this work package

Finish concise user-facing compatibility/release-note corrections if needed. Put completion counts, per-task validation and unrun operator work in the appropriate separate human-status/agent-evidence surfaces.

Human docs describe current behavior, limitations and examples without task IDs,
plans, progress links or implementation chronology. This task file and the agent
progress log contain execution evidence. Keep related code/tests/docs together.

## Validation

`scripts/check.sh --with-build`, required Cockpit check, documentation alignment checker, final file/symbol/reference inventory, DAG/selector/history checks and `git diff --check`. Review results rather than trusting a wrapper exit alone.

Required checks are planned, not performed. Record exact commands, exit results,
coverage and any explicit skips on completion. Do not replace meaningful tests
with weaker assertions merely to accommodate wording changes.

## Execution notes and handoff

Not started. Work on `feat/rest-api-and-mcp`, preserving existing user changes and
all live-host restrictions. Do not push, merge, tag, deploy, rotate credentials,
run production probes or manipulate NAS/services. If blocked, record the missing
prerequisite and precise unblock condition here and in the current selector.

## Completion evidence

Pending. On completion record: date; accepted behavior and removal/retention
results; focused test/gate evidence; documentation/link checks; invariant/ADR review;
any remaining operator prerequisite; and a link to the completed agent progress
entry. Update this task, plan/selector as needed and progress in the same commit.
Use "this commit" until the actual commit exists; do not invent a hash.
