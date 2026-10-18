# OPS-020: Make hardening probes explicit, safe and evidence-based

| Field | Value |
| --- | --- |
| Status | pending |
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

- [ ] Import, help and dry-run have zero effects; fixtures fail if they attempt host/credential/archive access.
- [ ] Read-only profile and missing/ambiguous authority refuse invasive checks before any filesystem write or service call.
- [ ] Injected ImportError, DNS failure, timeout and unrelated OSError cannot produce an isolation pass.
- [ ] No real kernel setting is written, no archive-root scratch file is created, and every created fixture artifact has provable cleanup ownership.
- [ ] Native and container evidence identify the actual tested process/control and cannot be mislabeled as production acceptance.

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
