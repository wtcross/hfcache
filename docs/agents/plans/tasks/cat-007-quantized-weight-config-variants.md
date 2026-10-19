# CAT-007: Detect scoped AWQ/GPTQ weight-bundle declarations

| Field | Value |
| --- | --- |
| Status | completed |
| Plan | [Tags and discovery](../2026-10-19-plan-tags-and-discovery.md) |
| Phase | 2 — Metadata foundation |
| Depends on | [CAT-005](cat-005-bounded-static-metadata-extraction.md), [CAT-006](cat-006-gguf-variants-and-shards.md) |
| Implementation branch | `feat/tags-and-discovery` |
| Commit boundary | One package / one commit: `CAT-007: <completed outcome>` |

## Required context

Follow `AGENTS.md` and `docs/agents/workflow.md`. Read relevant sections of the
[design](../support/tags-and-discovery/design.md),
[source review](../support/tags-and-discovery/source-review.md) and
[validation matrix](../support/tags-and-discovery/validation-matrix.md).
Tasks own execution status; evidence below records the current implementation.

## Likely implementation touchpoints

Static config/weight-index extractors; variant evidence types; known producer schemas and synthetic directory fixtures.

Inspect actual callers and tests before editing. Suggested new module names are
not requirements to create redundant layers when an existing small abstraction fits.

## Scope and requirements

Verify supported AWQ/GPTQ static fields against current primary source/docs and record exact producer/schema assumptions. Implement quantization_config method/bits/group_size extraction without importing those runtimes. Separate format, quantization method and nominal bits; missing declaration is unknown, not unquantized.

Associate declarations with an unambiguous weight bundle in the same logical directory scope. Parse recognized weight-index maps with safe bounded JSON, require every referenced member in the manifest and keep unrelated quantized subdirectories separate. Do not apply a root configuration indiscriminately to all weights.

Identify configured-only and obvious pointer/incomplete cases as non-available or unknown. Do not unpickle .bin files or scan safetensors bodies; technical claims remain attributed static declarations plus known member sets, not runtime/tensor proof. Include exact member paths, role, known bytes and completeness in variant observations.

Resolve contradictions through explicit evidence state/diagnostics, never arbitrary merging. Preserve malformed input evidence within sanitized limits. Document which layouts are supported and where a future extractor is needed.

## Acceptance criteria

At least representative supported AWQ and GPTQ fixtures work without runtime imports. Conflicting/missing/escaping members and ambiguous scopes cannot produce false available variants. Size/method predicates are representable on a single variant. Technical metadata remains distinct from curated tags.

## Contracts, invariants and ADRs

Review the affected current human contracts and `docs/invariants.md` through its
index; consult related technical ADRs listed in the source review. Record explicit
changes or an explicit no-impact finding in completion evidence. Amend contracts
in the same commit as behavior; add required ADR/index/progress decision entries
without copying agent task narration into human guides. Do not silently override
a filesystem, security, format, candidate, read-budget or MCP boundary.

## Validation

Matrix coverage: V20, V21, V22

Known config/index fixtures plus cross-directory, pointer, missing-member, duplicate, traversal and mixed-format counterexamples; full gate.

Every package requires `scripts/check.sh` exit 0, including docs-only work. Required
frontend checks must actually execute for frontend changes. Offline fixture success
does not imply live Hub/NFS or deployed acceptance. Missing prerequisites and failing
tests remain blockers, with their exact unblock condition recorded below.

## Execution notes and handoff

Implemented explicit config.json nested quantization_config declarations using
pinned Transformers configuration `0bc252863a4e5c0e709893664cc57369ebcd7353` and
index-resolution f4410762062c274fb53471e551e62b377df44cc1. Conservative AWQ4 and
GPTQ2/3/4/8 widths, strict nullable group fields (-1 means per-column with fixed
diagnostic), no runtime defaults. Legacy sidecars/custom unindexed/nested/dynamic
layouts remain unsupported, never arbitrarily merged into a positive claim.

Same-directory canonical singletons or one recognized authoritative index own
unique manifest members; repeated tensor-to-filename values deduplicate normally.
Unsafe/alias/escaping/nested/missing/mixed/known-training members, malformed
indexes, multiple alternatives and unindexed shards cannot become available.
No root-policy inheritance into child directories. Primary model types, adapter/
auxiliary role downgrades, exact source paths, per-variant bytes and explicit
unsupported/failed/partial statuses preserve the chosen discovery boundary.

Unbuffered safetensors reads stop after bounded JSON headers; shapes/products,
known dtypes, exact nonoverlapping extents/full declared buffer coverage are
checked without tensor data. Quantized declarations require nonempty integer
storage, excluding float-only/empty-integer contradictions. Binary files use only
bounded LFS detection/eight-byte sniff and a conservative 128-byte minimum, never
unpickle/load/ZIP extraction. Primary format pin:
safetensors `62e4d8b86063a6e5f8967547fa09a09f67420e2a`. Global candidate/member,
source-byte and shared actual-read/work bounds apply across scopes.

Review fixed optimizer-index promotion, tiny binary stubs, float/empty-integer
storage contradictions, integer product preallocation, error classification and
failed-index/config provenance. Independent 4,394-case malformed-type probing found
no unexpected exception classes. Focused 248 passed in 4.57s; lint/types/docs pass.
Required full gate passed. Final independent review is clear. No host, production, credential, live Hub/NFS, service,
archive CLI initialization, push or runtime dependency action.

Reviewed INV-018, AD-01/07/12/15/17/18, FS-09/11/15/19 and decision 133. Human
discovery/schemas and invariant/ADR enforcement links updated. No new architectural
exception, archive evidence format change or broader reader/writer authority.
Writer lifecycle/query/transport integration remains in later selected tasks.

## Validation mapping

- V20: supported explicit AWQ/GPTQ fields, nullable absent/per-column group,
  unknown widths/methods/dynamic layouts and strict malformed types. No runtime
  defaults/imports/deserialization/network; integer-storage contradictions refuse.
- V21: complete canonical index/deduplicated references and bytes, duplicate keys,
  traversal/aliases/foreign/missing/mixed/training members, ambiguous alternatives,
  unindexed shards, LFS/empty/truncated/unsafe members and malformed headers;
  exact header boundary/read/work/count and integer arithmetic checks.
- V22: independent AWQ/GPTQ subdirectories keep method/bits/bytes separate; root
  config cannot lend declarations or primary role to child weights. Unsupported
  legacy or invalid indexes cannot fall back to a positive available singleton.

## Completion evidence

Completed 2026-10-19 (CAT-007, this commit). V20-V22 have the concrete fixture
mapping above. Expanded focused `rtk uv run --locked --extra server --extra mcp
pytest -q tests/unit/test_catalog_weights.py tests/unit/test_catalog_gguf.py
tests/unit/test_catalog_extractors.py tests/unit/test_catalog_storage.py`:
248 passed in 4.57s; this includes 54 scoped weight cases. Lint/types/docs pass.
Full `rtk proxy scripts/check.sh` exited 0: 4605 passed, 40 opt-in deselected
in 485.32s; format/lint/types/docs, build, all three locked installation profiles
and actual Cockpit lint/types/169 tests/build passed. Complete local ignored log:
`.git/cat-007-check.log`. Final docs and whitespace checks passed.

Independent read-only review is clear, including a 4,394-case malformed-field probe
with no unexpected exception classes; all findings have regressions. Reviewed
INV-018, AD-01/07/12/15/17/18, FS-09/11/15/19 and decision 133; no new architecture,
dependency or broader authority exception. Discovery/schemas and ADR/invariant
links document supported producer/layout/format assumptions and explicit limits.
[Progress entry](../../progress.md#tags-and-discovery-2026-10-19) records completion.
No production, live Hub/NFS, credential, host/service, archive CLI initialization or
push operation. Writer lifecycle/query/transports remain in later selected tasks.
