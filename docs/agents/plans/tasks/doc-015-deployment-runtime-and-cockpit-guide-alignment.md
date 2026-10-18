# DOC-015: Unify deployment, runtime and Cockpit guidance

| Field | Value |
| --- | --- |
| Status | completed |
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

- [x] No current runtime/build paragraph contradicts selected templates, image pins or worker listener lifecycle.
- [x] Every install/upgrade/rollback/probe command identifies the applicable profile, process/manager and expected artifact.
- [x] Human deployment status separates recorded local verification from unperformed NAS/other-host work and does not rely on task links.
- [x] Cockpit claims match active code and rootless restrictions; direct report reads are accurately identified as a host-local exception.
- [x] Detailed historical rollout transcripts and provisional stage status are absent from primary guides, with technical compatibility caveats preserved.

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

Started 2026-10-18 after DOC-014 bffdce0. Work on `feat/rest-api-and-mcp`, preserving existing user changes and
all live-host restrictions. Do not push, merge, tag, deploy, rotate credentials,
run production probes or manipulate NAS/services. If blocked, record the missing
prerequisite and precise unblock condition here and in the current selector.

## Completion evidence

2026-10-18, this commit: deployment now starts with explicit rootless/native/
reader/consumer profiles, separate manager/socket/credential authority, safe
staging/drain/rollback and actual acceptance scope. Container guidance retains
UBI micro/binary/CA/portable-Python/locked-closure identities, complete lifecycle
and no-killing/unknown-state refusal, independent guard, worker-created listener/
notify and dormant indexed socket. Added a role matrix checked against actual
helper argv for networks, secret sets, executables and archive mounts.

Cockpit contract/operator/README guidance now identifies the fixed rootless
launcher, mounted API-only secret, authenticated rendered client settings,
blocked legacy system-bus controls and privileged host-local report/journal
exception. Exact candidate/base/flock/backup/confirmation and bounded stream/
handle rules survive. Native source pin (3.14) is distinguished from container
artifact (3.14.6), static list from native switch, and no-prune-in-flight rollback
is explicit. Dated status retains narrower recorded 0.2.1 scope/0.2.0 limitation,
with no inferred remote publication or host acceptance.

Eight prior guide bodies/source hashes preserved under agent history; descriptive
anchors/inbound references repaired. Transitional entries reduced 954 to 899.
Focused source/template/helper/installer/guard/probe/link suites: 417 passed in
42.04s; final matrix/link checks 14 passed in 3.62s. Ruff/format/Pyrefly passed.
`scripts/check.sh` exited 0: 4210 passed/40 opt-in deselected in 473.44s, build,
all three locked profiles and actual Cockpit lint/135 tests (0 skipped)/production
build. Log `/tmp/hfcache-doc015-gate.log`. Independent review corrections above
were incorporated before the full gate.

Reviewed CP-01–14, credential/single-lock/worker/MCP invariants and decisions
121/126–129/131/132: current-contract alignment only, no runtime, format,
dependency, architectural decision or new invariant. No production manager,
engine, NAS, archive, credential or host operation ran. See
[completed progress entry](../../progress.md#deployment-and-cockpit-profiles-2026-10-18).
Next ready task DOC-016; final authorized branch pushes follow plan acceptance.
