# DOC-014: Replace historical command transcripts with current runbooks

| Field | Value |
| --- | --- |
| Status | completed |
| Plan | [REST/MCP documentation and script alignment](../2026-10-18-plan-rest-mcp-docs-scripts-alignment.md) |
| Depends on | [DOC-013](doc-013-human-mcp-guide-and-tool-contract.md) |
| Phase | 2 — Human-facing guides |
| Review findings | F01, F02, F03, F07, F11, F12 |
| Suggested commit | `DOC-014: update operating and recovery procedures for the API` |

## Scope and implementation requirements

Rewrite `docs/operations.md` and `docs/recovery.md` as instructions for the API-backed system. Preserve any useful historical transcripts as agent-only evidence before removing them from primary runbooks. Do not imply that a historical direct-writer alias remains runnable merely because a paragraph calls it historical.

Replace `$H`/`$D` direct-writer invocations and `/opt/hfcache/current/.venv` assumptions with explicit profile-appropriate client setup. Keep writer-local Unix clients and remote HTTPS readers clear. Every operational command example must identify capability, archive/control-state side effects, live-storage prerequisites and the meaning of its result. Use safe shell arrays/functions rather than string aliases where options/paths can contain spaces.

Build human workflows for inventory/status, planning, sync, verification estimates/reports, actual verification, prune/purge/quarantine preview and apply, repair and recovery. Keep explicit unmanaged scope, exact SHA/publication identity, original-manifest repair and refusal of ambiguous data. Document that previews can create local operation receipts and never authorize later apply.

Put lost acknowledgement, finite client timeout, observer termination, API drain, verifier drain, orphan evidence and scheduled handles before recovery/upgrade steps. Closing a terminal or stopping a client unit cannot prove executor termination. No instructions may clear receipt stores, remove a lock, auto-replay uncertain jobs or stop the archive target as a shortcut.

Provide profile-specific operator diagnosis of daemon unavailable, verifier unavailable, invalid policy, wrong capability, metadata bounds and integrity failure. Keep loopback/disposable corruption rehearsal separate from current installation instructions. Update it to configure disposable API and private worker services/clients rather than passing an alternate `--config` to operational commands.

Link to a human deployment-status/acceptance checklist for current NAS-read-only and unvalidated-live-workload restrictions. A generic runbook describes supported capabilities; it is not permission to exercise them on the restricted local deployment.

## Acceptance

- [x] All runnable operational examples use the current API-only CLI and correctly scoped credentials/settings.
- [x] Historical command transcripts no longer dominate or contradict current instructions; preserved evidence remains traceable internally.
- [x] Recovery distinguishes archive journals, API receipts, verifier receipts and scheduled observation handles without merging their authority.
- [x] The rehearsal can be driven against owned fixtures with no real NAS, secrets or production service access.
- [x] No human task/plan references remain; no procedure implies lifting read-only guards or enables a timer automatically.

## Contracts, invariants and ADRs

CLI/API command semantics; storage/recovery `AD-13`, `AD-16`, `AD-17`, `FS-19`, `TX-06`, `TX-07`; no-replay operation protocol and executor drain; current deployment restrictions.

Paths above use the reviewed repository's names for identification. DOC-011 owns
the authoritative relocation map; after that package use the current path and
preserve the same contract/record identity. Read relevant sections progressively.
Record an explicit no-impact review when no technical invariant changes; do not
create a ceremonial technical ADR for an editorial-only change.

## Documentation in this work package

Rewrite operations/recovery, refresh relevant consumer and CLI links, and maintain a human acceptance/status checklist with evidence scope rather than task-owned "holds".

Human docs describe current behavior, limitations and examples without task IDs,
plans, progress links or implementation chronology. This task file and the agent
progress log contain execution evidence. Keep related code/tests/docs together.

## Validation

Parse all command examples and execute only designated safe fixtures. Add negative tests for operational `--config`, retry-with-new-key advice, premature recovery and data-plane access from a reader client. Run recovery/parity tests and `scripts/check.sh`.

Required checks are planned, not performed. Record exact commands, exit results,
coverage and any explicit skips on completion. Do not replace meaningful tests
with weaker assertions merely to accommodate wording changes.

## Execution notes and handoff

Started 2026-10-18 after DOC-013 8f42935. Work on `feat/rest-api-and-mcp`, preserving existing user changes and
all live-host restrictions. Do not push, merge, tag, deploy, rotate credentials,
run production probes or manipulate NAS/services. If blocked, record the missing
prerequisite and precise unblock condition here and in the current selector.

## Completion evidence

2026-10-18, this commit: rewrote both runbooks around API clients and current
profile restrictions. Preserved original transcripts/source hashes under agent
history and repaired descriptive anchors. Exact transitional entries reduced
983 to 954. Shell arrays replace direct-writer aliases. Every workflow states
capability, control/archive/Hub effects, acceptance prerequisites and outcome.
Uncertainty precedes filesystem recovery; lookup differs from quiescence and
compatible-service reopening. Four evidence domains, original-key/no replay,
original-manifest repair, current-publication quarantine proof, restore/refusal
rules and damaged-current ambiguity are explicit. No timer or guard is enabled.

New tests syntax-check all shell fences and parse 32 operational examples through
the real command tree without invoking callbacks. Existing negative CLI tests
prove legacy config refusal/no local fallback and original-key behavior. Designated
maintenance/private-worker/adversarial fixtures use owned temporary state only.
The focused ordering exposed a fault-injection patch outliving its HTTP fixture;
its ownership now follows that fixture, with an explicit restoration regression.
No runtime application behavior changed.

Focused suites: 180 passed in 22.16s; final parsing/links/fixture regression:
50 passed in 2.93s. Ruff/format/Pyrefly (0 errors) passed. `scripts/check.sh`
exited 0: 4209 passed/40 opt-in deselected in 476.05s, build, all three locked
profiles and actual Cockpit lint/135 tests (0 skipped)/production build. Log:
`/tmp/hfcache-doc014-gate.log`. Initial focused failures (broken storage link and
fixture patch lifetime) were corrected, not counted as acceptance.

Reviewed AD-13/16/17, FS-19, TX-06/07 and receipt/verifier/scheduled invariants.
Corrected stale prose to existing code/contracts; no format, dependency,
architectural decision or new invariant. No live NAS/Hub/host operation ran.
See [completed progress entry](../../progress.md#api-operating-and-recovery-runbooks-2026-10-18).
Next ready task DOC-015; final authorized branch pushes follow plan acceptance.
