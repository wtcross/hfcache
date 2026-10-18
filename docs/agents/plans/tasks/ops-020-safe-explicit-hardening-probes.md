# OPS-020: Make hardening probes explicit, safe and evidence-based

| Field | Value |
| --- | --- |
| Status | completed |
| Plan | [REST/MCP documentation and script alignment](../2026-10-18-plan-rest-mcp-docs-scripts-alignment.md) |
| Depends on | [DOC-011](doc-011-human-docs-authority-and-record-migration.md) |
| Phase | 1 — Correctness before editorial cleanup |
| Review findings | F05, F06 |
| Suggested commit | `OPS-020: make hardening probes explicit and fail closed` |

## Scope and implementation requirements

Refactor `scripts/check-hardening.sh` and `scripts/hardening-probe.py` so help/import/inspection cannot launch a workload. The current decorators execute checks at import, the archive write probes run before the identity check, and the denial wrapper accepts any exception as a pass.

Separate a non-invasive inventory mode from explicitly selected destructive/disposable workload modes. Require an explicit supported deployment profile, target and applicable authorization for invasive checks; never default an archive-writing workload to `/srv/hfcache`. Reject the selected guarded read-only profile for all archive-write probes. Default/help/dry-run must perform no network, service-manager, credential or archive access. Make the actual probe a `main()`-guarded program with pure functions and injectable I/O where practical.

Perform strict target/identity/sentinel/locality/ownership checks before any allowable test write, using existing validated application primitives where appropriate. Keep all archive workload artifacts inside the application-owned health area, under applicable locking, with uniquely owned, no-follow creation and exact cleanup. Never create `.hfcache-hardening-probe` directly under the archive root. Never use a missing/malformed sentinel as permission to initialize. Reconcile the permission to run a disposable probe with the environment's stricter no-live-NAS-I/O boundary; source implementation does not authorize running it.

Remove real host-configuration mutation as a denial test: attempting to write `/proc/sys/vm/swappiness` must not become an actual host change when confinement is broken. Replace such checks with safe observations or an isolated fixture that cannot alter host settings. Track and clean only artifacts this probe demonstrably owns; preserve unexplained files.

Replace generic exception-means-denied logic with per-check expected failure categories, prerequisite checks and explicit `pass`, `fail`, or `not_proven` results. Import failure, DNS outage, missing executable, timeout or unexpected exception must never certify seccomp/egress/credential isolation. Distinguish an observed blocked action from proof of the specific enforcing control. A loaded seccomp filter does not prove every intended syscall rule. Sanitize all output instead of printing raw dependency exceptions, signed URLs or arbitrary configuration values.

Keep actual container PID1/peer/cgroup checks distinct from native transient-unit probes. Do not claim a host-origin probe or `podman exec` establishes the installed API-to-worker boundary.

## Acceptance

- [x] Import, help and dry-run have zero effects; fixtures fail if they attempt host/credential/archive access.
- [x] Read-only profile and missing/ambiguous authority refuse invasive checks before any filesystem write or service call.
- [x] Injected ImportError, DNS failure, timeout and unrelated OSError cannot produce an isolation pass.
- [x] No real kernel setting is written, no archive-root scratch file is created, and every created fixture artifact has provable cleanup ownership.
- [x] Native and container evidence identify the actual tested process/control and cannot be mislabeled as production acceptance.

## Contracts, invariants and ADRs

Storage `FS-02`, `FS-03`, `FS-19`; `AD-17`; security/host hardening invariants; current read-only deployment restrictions; native and container isolation requirements. Do not weaken a sandbox to make a probe pass.

Paths above use the reviewed repository's names for identification. DOC-011 owns
the authoritative relocation map; after that package use the current path and
preserve the same contract/record identity. Read relevant sections progressively.
Record an explicit no-impact review when no technical invariant changes; do not
create a ceremonial technical ADR for an editorial-only change.

## Documentation in this work package

Replace unsafe probe recipes in deployment/operations guidance when the script behavior changes. Document modes, prerequisites, side effects, limitations and result meanings without task labels. Update agent restrictions separately.

Human docs describe current behavior, limitations and examples without task IDs,
plans, progress links or implementation chronology. This task file and the agent
progress log contain execution evidence. Keep related code/tests/docs together.

## Validation

Use fixture targets, injected syscall results and fake manager/engine commands. Add tests for ordering, failure classification, sanitization, duplicate artifacts, symlinks and refusal of live defaults. Run shell syntax checks, relevant Python tests and `scripts/check.sh`. Do not run a live hardening workload.

Required checks are planned, not performed. Record exact commands, exit results,
coverage and any explicit skips on completion. Do not replace meaningful tests
with weaker assertions merely to accommodate wording changes.

## Execution notes and handoff

Started 2026-10-18 after committed DOC-011 c3f5b5c. Work on `feat/rest-api-and-mcp`, preserving existing user changes and
all live-host restrictions. Do not push, merge, tag, deploy, rotate credentials,
run production probes or manipulate NAS/services. If blocked, record the missing
prerequisite and precise unblock condition here and in the current selector.

## Completion evidence

Completed 2026-10-18 in this commit. Static default/help/dry-run precede
all effects. Explicit native disposable workloads prove mount locality (including
ancestors/submounts), strict sentinel identity, ownership and original lock before
exclusive health-child writes; under-lock rechecks and exact-inode cleanup preserve
unknown artifacts. Production/read-only/ambiguous targets refuse. Kernel settings
are never written. Dependency/prerequisite failures remain not proven; output
suppression and complete bounded result projection prevent false success/leaks.

Validation: `uv run --locked --extra server --extra mcp pytest
tests/unit/test_hardening_probe.py --no-cov` exited 0, 74 passed. Shell syntax,
Ruff, types and migration-link checks passed. `scripts/check.sh` exited 0:
4,107 passed, 40 deselected in 473.88s; wheel build; all three isolated locked
installation profiles; actual Cockpit lint/types, 135 tests and production build.
The earlier fixture type-inference failure was corrected before this final gate;
interrupted review runs are not acceptance evidence. Log:
`/tmp/hfcache-ops020-gate.log`.

Reviewed FS-02/03/19, AD-17, INV-010 and native/container boundaries;
added INV-017 and decision 131, amended decisions 59/60 and current recipes.
No application format, dependency or sandbox weakening. Actual installed/container/
SELinux/NFS acceptance remains separate operator work; none was run here.
Positive installed-native profile classification follows in OPS-021.
See [completed progress evidence](../../progress.md#documentation-and-script-alignment).
The user's later feature-branch push authorization applies only after final plan
acceptance; all host/deploy/tag/merge restrictions remain.
