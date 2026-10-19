# CAT-008: Integrate supplemental metadata capture with existing sync and repair

| Field | Value |
| --- | --- |
| Status | completed |
| Plan | [Tags and discovery](../2026-10-19-plan-tags-and-discovery.md) |
| Phase | 3 — Writer lifecycle |
| Depends on | [CAT-004](cat-004-metadata-records-and-storage.md), [CAT-005](cat-005-bounded-static-metadata-extraction.md), [CAT-006](cat-006-gguf-variants-and-shards.md), [CAT-007](cat-007-quantized-weight-config-variants.md) |
| Implementation branch | `feat/tags-and-discovery` |
| Commit boundary | One package / one commit: `CAT-008: <completed outcome>` |

## Required context

Follow `AGENTS.md` and `docs/agents/workflow.md`. Read relevant sections of the
[design](../support/tags-and-discovery/design.md),
[source review](../support/tags-and-discovery/source-review.md) and
[validation matrix](../support/tags-and-discovery/validation-matrix.md).
Tasks own execution status; completion requires the recorded checks below.

## Likely implementation touchpoints

src/hfcache/sync.py, publication.py, repair.py and shared command boundaries; observation writer; sync/repair offline fixtures.

Inspect actual callers and tests before editing. Suggested new module names are
not requirements to create redundant layers when an existing small abstraction fits.

## Scope and requirements

Integrate metadata generation after an exact valid publication is durable, under the existing service-owned archive lock. Obtain safe current installed curation for tag snapshot capture without changing admitted operational policy/credentials. Record the actually observed curation identity/time.

Cover ordinary new publication, retained-SHA/no-new-publication paths, metadata-only config changes and repair with a new publication ID. A no-op archive sync may still refresh adjunct metadata without creating a new publication/generation or redownloading a retained model. Do not rewrite immutable trees/manifests or propagate old verification confidence.

Keep supplemental parser/storage errors safe and visible. An already valid publication must not be rolled back or called absent because enrichment failed; classify warnings and missing/failed coverage truthfully. Preserve existing domain failure/exit semantics and do not swallow unrelated archive failures. Reuse existing warnings/result extension points or explicitly version any necessary change.

Bound aggregate extraction work and preserve joined producer lifetime, common lock ownership, recovery/preflight, capacity and continue-on-repository-error behavior. Do not introduce callbacks that write metadata after lock release or daemon background threads without ownership. Metadata cannot trigger dependency downloads, partial sync or pruning.

## Acceptance criteria

Sync/repair tests show exact observation identity, original manifest bytes unchanged and no extra publication on tag edits. Failure injection preserves valid archive state and reports incomplete metadata. Producer/lock/capacity and retention regressions remain green.

## Contracts, invariants and ADRs

Review the affected current human contracts and `docs/invariants.md` through its
index; consult related technical ADRs listed in the source review. Record explicit
changes or an explicit no-impact finding in completion evidence. Amend contracts
in the same commit as behavior; add required ADR/index/progress decision entries
without copying agent task narration into human guides. Do not silently override
a filesystem, security, format, candidate, read-budget or MCP boundary.

## Validation

Matrix coverage: V23, V24, V25

Focused synchronize/repair/retained-SHA and failure-injection tests; metadata write and Hub call counts; full gate. No live archive work.

Every package requires `scripts/check.sh` exit 0, including docs-only work. Required
frontend checks must actually execute for frontend changes. Offline fixture success
does not imply live Hub/NFS or deployed acceptance. Missing prerequisites and failing
tests remain blockers, with their exact unblock condition recorded below.

## Execution notes and handoff

2026-10-19: resumed from completed CAT-007 on `feat/tags-and-discovery` with no
unrelated working-tree changes. Sync capture runs after producer shutdown and
deferred retention, before result/report checkpoints. Repair capture runs after
the durable replacement inside the existing guard. The original live lock token,
complete storage proof, bounded journal scans, exact active sync identity and
canonical committed-repair retirement evidence guard independent writes.

The API supplies a fresh installed-policy curation provider. Only current tags,
curation fingerprint/time are projected under the lock; admitted operational
policy, selection and credentials remain frozen. Failed or removed source
entries never fall back to admitted tags. Each invocation shares extraction
budgets plus 4096 write attempts/128 MiB serialized records, and each write checks
capacity with 64 KiB directory allowance. Optional failures yield HFWRN011 and
missing/failed evidence without changing domain success; near-reserve HFWRN005
is preserved. No new durable schema, runtime dependency or transaction replay.

Read-only independent review found and resolved the committed-repair grace
exception, checkpoint-order validation and canonical-before-read retirement
guard. Actual repair and payload open-spy fixtures cover those boundaries.
Earlier focused regressions exposed old service fixture expectations of
`published`/`success`; those unsupported arbitrary weight fixtures now correctly
expect supplemental warnings, while direct domain seams keep their behavior.
Two intermediate gates were interrupted (exit 2) for final canonical-path and
retirement identity corrections; neither is counted as passing. The first full
suite reported 3 failed/4625 passed/40 deselected in 495.38s: the closed logging
vocabulary fixture and two MCP on/off sync acceptance expectations needed the new
warning event/status. Those expectations were corrected without changing the
nine-tool boundary. Final required gate evidence follows at completion.

## Completion evidence

Completed 2026-10-19 (CAT-008, this commit). V23 binds exact new-publication
observations/tags and raw immutable manifest digest. V24's four retained-SHA
cases preserve downloads, references, generations and manifest bytes through
empty/disabled/tag-only changes; removed/unavailable current curation has no stale
fallback. V25 injects extractor/store/capacity/budget failures, proves a shared
invocation budget, original-lock capture after joined producers, and existing
real runner drain. Actual repair preserves original manifest/observation and
generation while binding the replacement; four corrupted retirement path/identity/
SHA/publication cases refuse without opening payloads. Capacity warnings remain
visible. Independent read-only review found no remaining material acceptance gap.

Final focused command: `rtk uv run --locked --extra server --extra mcp pytest -q
tests/unit/test_catalog_lifecycle.py tests/unit/test_catalog_storage.py
tests/unit/test_command_services.py tests/unit/test_api_commands.py
tests/unit/test_synchronize.py`: 221 passed in 91.94s. Corrected logging/MCP
expectations: `rtk uv run --locked --extra server --extra mcp pytest -q
tests/unit/test_logging.py tests/unit/test_mcp_acceptance.py`: 73 passed in 4.47s.
Full `rtk proxy scripts/check.sh` exited 0: 4628 passed/40 opt-in deselected in
494.66s, format/lint/types/docs, build, three locked installation profiles and
actual Cockpit lint/types/169 tests/build. Ignored log: `.git/cat-008-check.log`.

Reviewed INV-018, AD-12/13/14/17/18/19, TX-01/02/07, FS-06/07/09/17/19 and
decision 133. Discovery, CLI event/warning and report schema semantics plus
invariant/ADR enforcement links are current; no new architecture exception,
schema, runtime dependency or broadened authority. [Progress entry](../../progress.md#tags-and-discovery-2026-10-19)
records completion. No production, live Hub/NFS, credential, host/service,
archive CLI initialization or push action. Next: CAT-009; final compatibility
and operator handoff remain within the active plan.
