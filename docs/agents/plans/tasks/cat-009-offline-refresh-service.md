# CAT-009: Add a typed writer-only offline catalog refresh service

| Field | Value |
| --- | --- |
| Status | completed |
| Plan | [Tags and discovery](../2026-10-19-plan-tags-and-discovery.md) |
| Phase | 3 — Writer lifecycle |
| Depends on | [CAT-004](cat-004-metadata-records-and-storage.md), [CAT-005](cat-005-bounded-static-metadata-extraction.md), [CAT-006](cat-006-gguf-variants-and-shards.md), [CAT-007](cat-007-quantized-weight-config-variants.md) |
| Implementation branch | `feat/tags-and-discovery` |
| Commit boundary | One package / one commit: `CAT-009: <completed outcome>` |

## Required context

Follow `AGENTS.md` and `docs/agents/workflow.md`. Read relevant sections of the
[design](../support/tags-and-discovery/design.md),
[source review](../support/tags-and-discovery/source-review.md) and
[validation matrix](../support/tags-and-discovery/validation-matrix.md).
Tasks own execution status; completion requires the recorded checks below.

## Likely implementation touchpoints

services command/request layer; catalog refresh orchestrator; typed ServiceResult/Envelope/operation result compatibility; configuration snapshot providers.

Inspect actual callers and tests before editing. Suggested new module names are
not requirements to create redundant layers when an existing small abstraction fits.

## Scope and requirements

Implement the explicit refresh domain service for canonical whole-repository selectors, current/retained revision scope, tags/technical flags and at least one enabled output. Scope is configured-plus-retained union; disabled and unarchived configured entries may have tags captured, while technical work without a publication is explicitly skipped.

Use fresh installed scope/authority after waiting, normal lock/preflight/recovery guards and safe record writes; do not double-acquire the lock. No Hub/network, model download, configuration write, integrity hashing, verification confidence change, repair or pruning. Do not silently fall back to a source path supplied by a caller.

Return exact typed per-repository progress/counts, warnings, failures, skipped states and recorded identity within bounded work/result budgets. Independent atomic records may partly succeed; overall classification must distinguish that from a complete refresh. An unsupported/corrupt existing record cannot be overwritten under the label refresh.

Capture last observed tags truthfully; never claim that a removed uncaptured edit was saved. Respect empty/re-added config precedence and keep unmanaged snapshots only as history. Prepare a new typed command kind for standard keyed admission without adding a new scheduler or changing existing verification worker authority.

## Acceptance criteria

Offline temporary fixtures can refresh current and retained observations and tag-only unarchived entries. All side effects stay in approved adjunct records and normal command evidence. Scoped failures are visible, no archive authority is broadened, and unsupported state is preserved.

## Contracts, invariants and ADRs

Review the affected current human contracts and `docs/invariants.md` through its
index; consult related technical ADRs listed in the source review. Record explicit
changes or an explicit no-impact finding in completion evidence. Amend contracts
in the same commit as behavior; add required ADR/index/progress decision entries
without copying agent task narration into human guides. Do not silently override
a filesystem, security, format, candidate, read-budget or MCP boundary.

## Validation

Matrix coverage: V26, V27, V28

Service unit tests for scope/flags/lock/preflight, no-network/no-hash spies, capture/removal races, partial write results and version refusal; full gate.

Every package requires `scripts/check.sh` exit 0, including docs-only work. Required
frontend checks must actually execute for frontend changes. Offline fixture success
does not imply live Hub/NFS or deployed acceptance. Missing prerequisites and failing
tests remain blockers, with their exact unblock condition recorded below.

## Execution notes and handoff

2026-10-19: selected after CAT-008 `d98b1ec`, clean tree on
`feat/tags-and-discovery`. Added strict canonical whole-repository intent,
bounded authoritative no-follow reference inventory, and schema-1 typed per-record
refresh progress. Existing capture methods share curation/source/record budgets
across sync, repair and refresh; source projection and output identities remain
separate from admitted storage/operational policy.

Explicit refresh uses one existing guard and fresh installed curation. It refuses
unresolved/operator journals without applying recovery, because automatic repair,
prune or cleanup would exceed this metadata-only command. TX-07, INV-018 and
decision 133 document this stronger refusal boundary. Membership comes only from
current config and authoritative retained refs; inert metadata/orphans do not add
scope. Scope and conservative complete-result reservation precede all writes,
including actual generation widths. Per-record failure/coverage and exact counts
are distinct; no successful truncation or unsupported record overwrite.

Read-only review found a malformed-selector diagnostic bypass: parse_selector
raises ConfigurationError, so catching only CodedError echoed unbounded input.
Added the canonical 201-character maximum before parsing, fixed-message handlers,
long/private-input and longest-valid-selector regressions. Other review findings
are clear. Same-key/new-key capture is tested through the real OperationRunner /
OperationStore without adding a public route or scheduler. No framework/runtime
dependency, credential resolver, Hub call, config write, payload integrity hashing,
repair, prune, verification catalog or immutable publication change is introduced.

New focused refresh/replay tests: 49 passed in 8.77s. Expanded earlier focused
tests passed 177 in 16.57s before the final request/budget fixtures. Final expanded
and full gate evidence follows below. Public admission and transport compatibility
remain in the later authorized tasks; no live or operator action is performed.

## Completion evidence

Completed 2026-10-19 (CAT-009, this commit). V26 covers strict scope/flags,
disabled/unpublished/tag-only/technical-only rows, explicit current versus retained
refs, no Hub/credentials/network/payload hashing or non-adjunct mutation, and
unresolved-journal refusal without recovery. V27 covers independent successful,
partial and failed record writes; incomplete interpretations remain separate from
write failures. Actual generation widths and complete scope/reader/result/write
budgets refuse before hidden work or report visible partial progress. Real keyed
runner/store replay returns the exact original result and snapshot after edits;
only a new key performs a fresh capture. V28 covers removed uncaptured entries,
preserved unmanaged history, re-added empty tags and actual post-lock curation.
Strict result fixtures reject false counts, versions, states and recorded identity.

Final focused: `rtk uv run --locked --extra server --extra mcp pytest -q
tests/unit/test_catalog_refresh.py tests/unit/test_catalog_refresh_replay.py
tests/unit/test_catalog_lifecycle.py tests/unit/test_catalog_storage.py
tests/unit/test_command_services.py tests/unit/test_command_models.py`:
184 passed in 19.09s. New refresh/replay subset: 49 passed in 8.77s. Lint,
types, docs and whitespace pass. Full `rtk proxy scripts/check.sh` exited 0:
4677 passed/40 opt-in deselected in 507.48s, build, three locked installation
profiles and actual Cockpit lint/types/169 tests/build. Ignored complete log:
`.git/cat-009-check.log`. Independent current-package review is clear after
the bounded malformed-selector diagnostic fix and its regressions.

Reviewed INV-018, AD-12/14/15/16/17, TX-01/02/07 and FS-06/09/11/17/19.
Architecture/invariant TX-07 text and decision 133 explicitly retain refusal
instead of applying unrelated work for this metadata-only command. Discovery,
schema-1 service payload and invariant/ADR enforcement links are current; existing
archive evidence formats and runtime dependencies remain unchanged.
[Progress entry](../../progress.md#tags-and-discovery-2026-10-19) records completion.
No production, live Hub/NFS, credential, host/service, archive CLI initialization,
push or public route activation. Next: CAT-010; keyed public admission and
compatibility drills remain within later selected work.
