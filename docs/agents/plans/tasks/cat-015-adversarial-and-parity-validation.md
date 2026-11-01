# CAT-015: Prove read-only, bounded and cross-transport discovery behavior

Interface-only instructions and source references have been omitted from this
retained shared record. Exact original text remains in Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`;
original document path SHA-256 `608d706aaefb6aef6bf9fd109e340730114cce468837ed3eb0d787346b952319`,
original content SHA-256 `2b0d691cfbf8457dd9d483b5cab314abf41e5725fae61451a919c39111f77d93`.
Historical proof hashes identify the original artifacts, not this edited record.

| Field | Value |
| --- | --- |
| Status | complete |
| Plan | [Tags and discovery](../2026-10-19-plan-tags-and-discovery.md) |
| Phase | 6 — Acceptance |
| Depends on | [CAT-003](../support/tags-and-discovery/retirements.json), [CAT-008](cat-008-sync-metadata-lifecycle.md), [CAT-014](cat-014-read-only-mcp-catalog-tools.md) |
| Implementation branch | `feat/tags-and-discovery` |
| Commit boundary | One package / one commit: `CAT-015: <completed outcome>` |

## Required context

Follow `AGENTS.md` and `docs/agents/workflow.md`. Read relevant sections of the
[design](../support/tags-and-discovery/design.md),
[source review](../support/tags-and-discovery/source-review.md) and
[validation matrix](../support/tags-and-discovery/validation-matrix.md).
Tasks own execution status; this file is pending, not a claim of implementation.

## Likely implementation touchpoints

Inspect actual callers and tests before editing. Suggested new module names are
not requirements to create redundant layers when an existing small abstraction fits.

## Scope and requirements

Complete matrix adversarial coverage across shared services, REST, CLI and MCP rather than relying only on unit happy paths. Use generated offline fixtures for hostile card/JSON/GGUF inputs, huge counts, ambiguous bundles, duplicate/shard identities, wrong-archive records and exact publication races.

Prove queries cannot open payloads, hash model bytes, contact the Hub, acquire archive mutation locks, persist tags/observations or schedule refresh. Validate cancellation/worker lease and wire/scan/serialization budgets, including a tiny page on a large source and one oversized variant row. Budget exhaustion must fail explicitly.

Exercise prompt-injection-like card content, hostile filenames/tags and terminal/browser rendering. Metadata is data, not executable advice; no URLs are followed or shell strings evaluated. Check known-secret sanitization before matching/facets/cursor hashing so redacted substitutions cannot be probed through output/count changes.

Prove REST/MCP normalized filter and full pagination parity, same-variant conjunction, distinct repository facets, disabled/unmanaged/current-history states and explicit missing coverage. Add regression tests for every defect found and update its current contract if an ambiguity was resolved. Do not weaken an invariant solely to make a test pass.

## Acceptance criteria

Adversarial matrix cases and cross-layer negative assertions pass with real enforcement evidence. Read-only annotations are not the sole proof. All identified fixes are in scope, documented and tested; unresolved failures are recorded as blockers, not waived acceptance.

## Contracts, invariants and ADRs

Review the affected current human contracts and `docs/invariants.md` through its
index; consult related technical ADRs listed in the source review. Record explicit
changes or an explicit no-impact finding in completion evidence. Amend contracts
in the same commit as behavior; add required ADR/index/progress decision entries
without copying agent task narration into human guides. Do not silently override
a filesystem, security, format, candidate, read-budget or MCP boundary.

## Validation

Matrix coverage: V47, V48, V49, V50

Every package requires `scripts/check.sh` exit 0, including docs-only work. Required
frontend checks must actually execute for frontend changes. Offline fixture success
does not imply live Hub/NFS or deployed acceptance. Missing prerequisites and failing
tests remain blockers, with their exact unblock condition recorded below.

## Execution notes and handoff

CAT-014 is committed with a green full gate. Reviewing INV-002/006/012/016/018
and decisions 111/113/125/133 before adversarial acceptance. Existing extractor,
record, query and transport negative fixtures are retained; new integration cases
will target normalized secret representations, whole walks, source-open/lock/
network/runtime spies, cancellation ownership and oversized individual variants.

Reproduced a normalized-secret regression before its fix (one focused failure):
a registered mixed-case value became a visible lowercase tag, changing results
and cursor identity. Catalog checks now explicitly suppress casefolded registered
literals before projection; default literal redaction stays unchanged. INV-002/
018 and decision 133 document the normalization rationale. Public-label changes
still invalidate cursors; hidden substitutions cannot change results, facets,
counts or continuation. Actual REST/MCP and API-backed CLI confirm this behavior.

New integration tests complete REST/CLI/MCP walks and compare full rows, coverage
and identity. File-open, import, archive-lock, credential, hash, writer, refresh,
network and shell spies reject effectful/source capabilities across all five MCP
reads and REST. Actual filesystem snapshots remain unchanged. Prompt-like source
values and shell-looking filenames remain data; terminal controls escape. A
frontend negative-label test rejects script/shell/URL/control input without echo.
Oversized 512-member variant rows refuse on both actual transports with bounded
HFAPI005, never a successful truncation. Shared 1-worker/1-queue fixtures prove
saturation, responsive non-pool metadata and retained MCP leases after observer
cancellation, with eventual zero leases and unchanged archive/control state.

Focused adversarial/extraction/storage/query/MCP/CLI/logging selection: 396 passed
Historical execution summary: the recorded gate included the retired interface; exact invocation and original proof remain in Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`.
HTTP parameter typing and frontend whitespace defects were fixed before this
passing selection. All-source lint/types and documentation alignment pass.
Full gate passed as recorded below. No new dependencies or production/live/credential/host/push work.

## Completion evidence

Completed 2026-10-19 (CAT-015, this commit). Full `scripts/check.sh` exited 0:
4999 passed/40 deselected in 583.75s; wheel/sdist, all three locked profiles,
actual historical frontend lint/types/170 tests/build passed. Focused expanded selection:
396 passed in 25.81s; standalone frontend gate also exited 0. V47-V50 have
actual effect/import/file-open guards, inert display/input, complete transport
walks, blocked/canceled worker leases, oversized-row refusals and hidden-secret
substitution evidence. Reviewed INV-002/006/012/016/018 and decisions 111/113/125/
133; human discovery/security, invariant and ADR rationale updated. No unresolved
failures, runtime dependencies, production/live/credential/host/push work.
[Progress](../../progress.md#tags-and-discovery-2026-10-19) records completion;
CAT-016 remains for lifecycle, actual installed old binaries and final acceptance.
