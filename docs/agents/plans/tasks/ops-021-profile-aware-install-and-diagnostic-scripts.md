# OPS-021: Align installer and diagnostic entrypoints with deployment profiles

| Field | Value |
| --- | --- |
| Status | completed |
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

- [x] Native tools give a specific, early cross-profile refusal for container or ambiguous selections, with tests proving no staging/switch/probe side effect.
- [x] All 17 existing scripts and every new script have a purpose, supported profile, invocation, side-effect class, dependencies and test owner in the human inventory.
- [x] Container/native executable paths, socket paths, service managers, readiness and credentials agree across helpers/templates/docs.
- [x] Dormant socket and native activation tests still pass; no lifecycle/control/lock bypass is added.
- [x] No script is removed solely because the current installation does not use it.

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

Started 2026-10-18 after completed OPS-020 2b51f2b. Work on `feat/rest-api-and-mcp`, preserving existing user changes and
all live-host restrictions. Do not push, merge, tag, deploy, rotate credentials,
run production probes or manipulate NAS/services. If blocked, record the missing
prerequisite and precise unblock condition here and in the current selector.

## Completion evidence

Completed 2026-10-18 in this commit. Shared standard-library positive native
classification validates source/current/existing target before tools, manager,
staging, candidate interpreter or diagnostic effects. Native staging uses the
same parsed TOML version it classified. Fresh prefixes validate existing ancestors;
raw selector grammar refuses aliases/dangling/external paths. Container/mixed/
unknown/partial layouts refuse; fresh native use and managed Python links remain.

Safe help now precedes profile, lock and installation workloads, including nested
fixed-client help. Unsupported fixed-launcher grammar refuses before profile reads.
All 17 existing helpers are retained; `docs/scripts.md` inventories them and the
new classifier with profile, invocation, inputs/dependencies, effects and tests.
Current UBI foundation and worker-service readiness lead the corrected recipes.
Dormant rootless socket binding, native FD3, fixed roles/secrets, actual-executor
drain, handles/stores and original lock behavior are retained.

Validation: the expanded `uv run --locked --extra server --extra mcp pytest`
selection of native installer, hardening, script help, container service/installer,
systemd units, readonly guard and migration tests passed 342 in 38.87s; the final
help suite passed 9 in 0.89s after nested-help cases. Host Python executed the
read-only classifier against the checkout and absent temporary prefix, returning
0.2.1 without creation. The suite enforces Python 3.12 bootstrap grammar. Three
additional disposable masked-unit fixtures (`uv run --locked --extra server
--extra mcp python`, `release_fixture.__wrapped__` + `run_library` with masked
sync timer/API/verification service) passed: refusal, unchanged selector and
original lock inode/content. No real manager was invoked.

`scripts/check.sh` exited 0: 4,148 passed, 40 deselected in 475.21s; wheel/sdist
build; all three locked isolated installation profiles; actual Cockpit lint,
types, 135 tests and production build. Ruff/types, shell syntax and link checks
passed. Log: `/tmp/hfcache-ops021-gate.log`. Review caught and corrected bootstrap
syntax, split version parsing and fresh-ancestor checks before the final gate.

Reviewed AD-17, FS-19, INV-006/010/017 and decisions 121/126/127/128/131;
decision 132 records the new tooling boundary and amends 121/131. Archive formats,
domain behavior, dependencies, deployment and host guards are unaffected. Actual
installed/container/SELinux/NFS acceptance is separate operator work, not claimed.
See [completed progress evidence](../../progress.md#documentation-and-script-alignment).
User-authorized feature-branch pushes follow final plan acceptance only.
