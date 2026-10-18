# API-018: Align CLI help and output; remove obsolete rendering paths

| Field | Value |
| --- | --- |
| Status | pending |
| Plan | [REST/MCP documentation and script alignment](../2026-10-18-plan-rest-mcp-docs-scripts-alignment.md) |
| Depends on | [OPS-021](ops-021-profile-aware-install-and-diagnostic-scripts.md) |
| Phase | 1 — Correctness before editorial cleanup |
| Review findings | F07, F08, F09, F11 |
| Suggested commit | `API-018: align CLI diagnostics and remove migration remnants` |

## Scope and implementation requirements

Review every registered Typer command and option against its actual dispatch. Rewrite user-visible docstrings/help to distinguish the local observer, writer service and private verifier. `config validate` is remote by default; `config validate --local` is the explicit bootstrap exception. `version --server` is remote. Planning/maintenance preview jobs can leave local control receipts even when they do not mutate archived content. Actual verification updates reports/catalog through the private worker.

Correct output behavior rather than weakening the promised diagnostics. `_show_result` can suppress partial-failure errors in quiet human mode and does not consistently render warnings. Emit warnings/errors on stderr in quiet mode without losing nonzero exits or partial results. Keep stdout's exact server Envelope semantics, admission-vs-completion distinction, retained keys/IDs and redaction. Test default, quiet, JSON and combined forms.

Make `--no-color` affect the actual human/help renderers through supported Typer/Click controls, including explicit help, without process-wide daemon changes. The current `GlobalOptions.color` field is assigned but not consumed by the reviewed renderers. Remove the inert field once the option is correctly wired. Document `--verbose` as client-local detail unless the protocol truly supplies different server events; do not pretend it changes server logging. Reconcile the claimed non-TTY progress policy with `_progress`, which currently checks quiet only. Choose the existing contract: suppress ordinary live progress on non-TTY output while always retaining safety handles and diagnostics; document bounded scheduled observation output separately.

Prove and remove migration remnants: `cli._emit` has no caller in the reviewed CLI; examine `cli_client.run_job`, the old `ServiceResult` input path in `_show_result`, and `UNPROVABLE_READ_ONLY`'s CLI re-export. Search all source, tests, examples and supported entrypoints before deleting candidates. Migrate tests that only preserve an unused implementation seam to public behavior tests. Keep bootstrap `emit_envelope`, real service functions and any legitimately used compatibility API. Do not infer dead code from underscores, file length or static coverage alone.

No CLI fallback to local operational execution, no auto-daemon startup and no change to the nine MCP tools.

## Acceptance

- [ ] Every CLI help example describes its actual local/remote dispatch and side effects; no stage/task IDs reach generated help.
- [ ] Quiet failed/partial and warning-only results retain stderr diagnostics, correct exit status and safety handles; JSON stdout stays one valid result or explicitly typed admission.
- [ ] `--no-color` is behaviorally tested for supported help/output cases; unused color state is gone.
- [ ] Ordinary non-TTY progress behavior matches the revised human contract; server logging is not implied to change with client verbosity.
- [ ] Each removal has a call-site/disposition record; public result, argument and transport tests replace any implementation-only coverage lost.

## Contracts, invariants and ADRs

CLI output/failure invariant `INV-006`; API-only operational client boundary; credential separation; service result and observer semantics. Keep schema versions and error taxonomy stable unless a separately justified contract correction is required.

Paths above use the reviewed repository's names for identification. DOC-011 owns
the authoritative relocation map; after that package use the current path and
preserve the same contract/record identity. Read relevant sections progressively.
Record an explicit no-impact review when no technical invariant changes; do not
create a ceremonial technical ADR for an editorial-only change.

## Documentation in this work package

Update `docs/cli.md` command/flag/output sections in the same commit, using current-tense semantics. Update the code-removal ledger under agents, not human docs.

Human docs describe current behavior, limitations and examples without task IDs,
plans, progress links or implementation chronology. This task file and the agent
progress log contain execution evidence. Keep related code/tests/docs together.

## Validation

Add public CliRunner/transport-fake cases for warnings, partial errors, quiet+JSON, color/help, remote/local validation, progress and timeout/uncertain submission. Search all candidate symbol uses and run relevant CLI/parity tests plus `scripts/check.sh`.

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
