# OPS-021: Align installer and diagnostic entrypoints with deployment profiles

| Field | Value |
| --- | --- |
| Status | pending |
| Plan | [REST/MCP documentation and script alignment](../2026-10-18-plan-rest-mcp-docs-scripts-alignment.md) |
| Depends on | [OPS-020](ops-020-safe-explicit-hardening-probes.md) |
| Phase | 1 — Correctness before editorial cleanup |
| Review findings | F03, F04, F10, F13 |
| Suggested commit | `OPS-021: make deployment helpers profile aware` |

## Scope and implementation requirements

Use the script disposition inventory to classify every shipped helper as selected rootless runtime, supported native profile, independent consumer tooling, build/test tooling, or a deprecated artifact with an explicit replacement. Do not call the native installer dead merely because the selected deployment is rootless.

Add an early, positive profile check to native installation/switch and native hardening paths. They must refuse an identified container release/profile before staging into it, selecting it or probing it. An explicit native-profile acknowledgement alone must not permit operating on a rootless target. Unknown/mixed release metadata must remain a refusal, not an inferred native profile. Validate both current and proposed release layouts. Preserve native fresh-install use and non-mutating list/help/dry-run modes, with documented behavior.

Keep the selected rootless `install-container-release.py`, `container-service.py`, client wrapper, fixed host guard and actual container probes as the authoritative rootless path. Improve argument help and errors to identify manager, executable location, credential delivery, side effects and expected input artifacts. Do not silently route identical unit names to a different manager. Do not add a generic engine/executable escape to the fixed role launcher.

Preserve the dormant rootless verification socket artifact and its installer binding: it is deliberately not the active container listener. Native named-FD3 activation remains supported. Verify that the container target/API prerequisites use worker service readiness rather than activating that socket.

Keep the scheduled-client implementation and native units, while documenting that the selected guarded rootless profile does not enable legacy schedules. Preserve all pending handles and both operation stores, non-killing executor drain, exact lock inodes and immutable release inputs. Help/dry-run must be safe to invoke without root, Podman, systemd, a configured archive or credentials.

Create or update human `docs/scripts.md` with a maintained inventory. Delete a whole helper only after a recorded branch-wide reference/install/build/rollback analysis proves it unsupported and unused. At this review no whole script meets that bar; do not manufacture a deletion quota.

## Acceptance

- [ ] Native tools give a specific, early cross-profile refusal for container or ambiguous selections, with tests proving no staging/switch/probe side effect.
- [ ] All 17 existing scripts and every new script have a purpose, supported profile, invocation, side-effect class, dependencies and test owner in the human inventory.
- [ ] Container/native executable paths, socket paths, service managers, readiness and credentials agree across helpers/templates/docs.
- [ ] Dormant socket and native activation tests still pass; no lifecycle/control/lock bypass is added.
- [ ] No script is removed solely because the current installation does not use it.

## Contracts, invariants and ADRs

Native release and container profile contracts; fixed role authority; `AD-17`, `FS-19`; observer/operation-state retention; systemd scheduling and container readiness decisions. Preserve both supported deployment mechanisms.

Paths above use the reviewed repository's names for identification. DOC-011 owns
the authoritative relocation map; after that package use the current path and
preserve the same contract/record identity. Read relevant sections progressively.
Record an explicit no-impact review when no technical invariant changes; do not
create a ceremonial technical ADR for an editorial-only change.

## Documentation in this work package

Write `docs/scripts.md`; add concise profile labels to human install/probe recipes and script help. Refresh `docs/agents/environment.md` and release guidance so selected-profile facts lead, not superseded native commands.

Human docs describe current behavior, limitations and examples without task IDs,
plans, progress links or implementation chronology. This task file and the agent
progress log contain execution evidence. Keep related code/tests/docs together.

## Validation

Exercise installers with fake systemctl/Podman and immutable temporary release trees, including native→container, container→native, unknown, masked units, pending handles and safe dry-run. Validate shipped units in disposable directories only. Run relevant installer/container tests and `scripts/check.sh`.

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
