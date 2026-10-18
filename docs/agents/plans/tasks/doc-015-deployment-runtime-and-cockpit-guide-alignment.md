# DOC-015: Unify deployment, runtime and Cockpit guidance

| Field | Value |
| --- | --- |
| Status | pending |
| Plan | [REST/MCP documentation and script alignment](../2026-10-18-plan-rest-mcp-docs-scripts-alignment.md) |
| Depends on | [DOC-014](doc-014-current-operations-and-recovery-runbooks.md) |
| Phase | 2 — Human-facing guides |
| Review findings | F02, F03, F04, F10, F12, F13 |
| Suggested commit | `DOC-015: align deployment and Cockpit guides with runtime profiles` |

## Scope and implementation requirements

Rewrite deployment and container guidance around explicit profiles and responsibilities. The selected guarded rootless deployment is not the same as the historical native systemd deployment, and neither is the archive-writing production capability automatically accepted on the current NAS.

Align build guidance with actual pinned UBI 10 micro Containerfiles, portable Python input, reviewed binary/CA donors, locked server+MCP closure and immutable image identity. Remove slim-trixie/Debian-as-current claims and stale build/listener chronology. Describe version, source commit, wheel hash, dependency closure, image digest and deployment selection as distinct facts without embedding work-package narratives.

Align the current container lifecycle with worker-created private listener, readiness notification, API service prerequisites and dormant socket binding; explain native socket activation separately. Publish a compact matrix for each role's executable, manager, UID mapping, network, writable paths, credential sources and persistent state. Derive facts from templates/helpers and validate them instead of copying 981/path constants into unrelated generic instructions.

Create human `docs/deployment-status.md` (or an equivalently concise dedicated acceptance page) recording what the repository says was validated for the dated local 0.2.1 deployment and what remains unvalidated: live NAS/domain workloads and other-host acceptance remain separate. This review did not inspect that host. Remove claims that a remotely readable feature branch has never been published; do not assert current remote tag state without querying it. Move detailed implementation chronology to agent evidence.

Update Cockpit contract/operator docs and `cockpit/README.md`. Clearly describe the rootless fixed client launcher, candidate-file pipeline and intentionally blocked legacy system-manager controls. Do not present these controls as active user-manager operations. The report-browser direct `runuser`/`ls`/`cat` path in `cockpit/src/api/archive.ts` is an existing host-local exception, not dead code and not a remote API reader. Keep that limitation explicit; do not remove it without a separate replacement design and coverage.

Coordinate native installer/hardening guidance with the script safeguards already completed. Do not remove dormant/native/consumer tooling, deploy units, change credentials or run acceptance checks on the production host.

## Acceptance

- [ ] No current runtime/build paragraph contradicts selected templates, image pins or worker listener lifecycle.
- [ ] Every install/upgrade/rollback/probe command identifies the applicable profile, process/manager and expected artifact.
- [ ] Human deployment status separates recorded local verification from unperformed NAS/other-host work and does not rely on task links.
- [ ] Cockpit claims match active code and rootless restrictions; direct report reads are accurately identified as a host-local exception.
- [ ] Detailed historical rollout transcripts and provisional stage status are absent from primary guides, with technical compatibility caveats preserved.

## Contracts, invariants and ADRs

Current container/native deployment contracts, release binding and non-killing drain; Cockpit CP rules; credential and NFS trust boundaries; UBI image/runtime identity and worker readiness decisions.

Paths above use the reviewed repository's names for identification. DOC-011 owns
the authoritative relocation map; after that package use the current path and
preserve the same contract/record identity. Read relevant sections progressively.
Record an explicit no-impact review when no technical invariant changes; do not
create a ceremonial technical ADR for an editorial-only change.

## Documentation in this work package

Rewrite `docs/containers.md`, `docs/deployment-centos-stream-10.md`, `docs/cockpit.md`, operator files under `docs/cockpit-plugin/`, `cockpit/README.md` and scripts inventory. Create the human deployment acceptance/status page; fix agent environment/release routes separately.

Human docs describe current behavior, limitations and examples without task IDs,
plans, progress links or implementation chronology. This task file and the agent
progress log contain execution evidence. Keep related code/tests/docs together.

## Validation

Cross-check documentation values with container/native templates and helper argv fixtures, validate example configs after safe placeholder rendering, and run Cockpit gate wherever that surface changes. Run `scripts/check.sh`; record any live acceptance as not run.

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
