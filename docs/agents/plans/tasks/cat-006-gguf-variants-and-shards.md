# CAT-006: Detect GGUF formats, quantization schemes and complete variant sets

| Field | Value |
| --- | --- |
| Status | completed |
| Plan | [Tags and discovery](../2026-10-19-plan-tags-and-discovery.md) |
| Phase | 2 — Metadata foundation |
| Depends on | [CAT-005](cat-005-bounded-static-metadata-extraction.md) |
| Implementation branch | `feat/tags-and-discovery` |
| Commit boundary | One package / one commit: `CAT-006: <completed outcome>` |

## Required context

Follow `AGENTS.md` and `docs/agents/workflow.md`. Read relevant sections of the
[design](../support/tags-and-discovery/design.md),
[source review](../support/tags-and-discovery/source-review.md) and
[validation matrix](../support/tags-and-discovery/validation-matrix.md).
Tasks own execution status; evidence below records the current implementation.

## Likely implementation touchpoints

Proposed bounded GGUF extractor and variant grouping module; synthetic byte fixtures; discovery schema/evidence documentation.

Inspect actual callers and tests before editing. Suggested new module names are
not requirements to create redundant layers when an existing small abstraction fits.

## Scope and requirements

Implement supported GGUF header versions with a pinned primary format mapping and explicit endian/type/count/length checks. Read header metadata only, never tensor bodies. Record GGUF as format and known GGML scheme as quantization; keep F16/F32 encoding and mixed/unknown nominal bit width honest.

Extract known general.file_type and shard identity/count/index fields. Unknown enums/versions or missing distinguishing metadata produce unsupported/candidate state; filenames cannot prove exact schemes or override a header. Do not infer Q4_K_M versus Q4_K_S from a single tensor type or a loose substring.

Group only exact, validated same-publication logical shard sets. Check missing/duplicate/count-conflicting shards, scope collisions, total member sizes and deterministic variant identity. Distinguish auxiliary projectors/adapters/unknown roles; do not advertise them as standalone primary models.

Validate offset/count arithmetic against file size and declared work bounds before reading or allocating; skipping unknown metadata must still respect bounds. Fail safely on hostile headers. Keep the module dependency-light and no execution/inference capability.

## Acceptance criteria

Known positive fixtures expose exact supported schemes and complete weight sets with source evidence. Float, ambiguous, auxiliary, unknown and incomplete cases are distinguished. Every grouping and byte total is publication-specific and deterministic. Hostile synthetic headers stay within configured bounds.

## Contracts, invariants and ADRs

Review the affected current human contracts and `docs/invariants.md` through its
index; consult related technical ADRs listed in the source review. Record explicit
changes or an explicit no-impact finding in completion evidence. Amend contracts
in the same commit as behavior; add required ADR/index/progress decision entries
without copying agent task narration into human guides. Do not silently override
a filesystem, security, format, candidate, read-budget or MCP boundary.

## Validation

Matrix coverage: V15, V16, V17, V18, V19

Unit tests for all supported mappings, split sets and negative grouping; truncated/overflow/type/large-count fuzz-style fixtures; source-read spies prove no tensor body scans; full gate.

Every package requires `scripts/check.sh` exit 0, including docs-only work. Required
frontend checks must actually execute for frontend changes. Offline fixture success
does not imply live Hub/NFS or deployed acceptance. Missing prerequisites and failing
tests remain blockers, with their exact unblock condition recorded below.

## Execution notes and handoff

Implemented bounded GGUFv3 little-endian headers from pinned primary sources:
ggml `6af560d55df03ad92116e3c0a697779584477e85`, llama constants
412a363c655b479279d3050d0d1c67a5733697b4 and split writer
8f97d82da33b5f4262a87b9c4208298378b8a165. Human discovery docs record exact
file-type mappings, unsupported versions/endian/enums, float versus quantized
semantics, unknown mixed bits and conservative role policy. No inference/runtime
dependency, file-type inference from tensor names/types, or tensor-body read.

Exact publication/directory/canonical filename-prefix grouping requires agreeing
explicit split identity/index/count/tensor totals, unique full membership and no
duplicate tensor names. Shard zero owns declarations; later missing metadata is
normal and later conflicting fields refuse completeness. Header-only first shards
are valid. Auxiliary/projector/adapter/LoRA/vocabulary/unknown roles cannot promote
to primary. Tensor dimensions/extents/alignment/overlaps and aggregate contradictory
float/quantized headers are validated without reading padding or tensor bytes.

Review found and fixed shared buffered read-ahead, ignored multiline metadata,
realistic tokenizer array/work bounds, canonical LoRA/vocab and tensor role hints,
ASCII key grammar and minimum alignment, and float-kind contradictions. Source
access now uses unbuffered descriptors with raw read/tell accounting proof. Shared
work caps at 8M plus 100k manifest entries, arrays at 1,048,576, actual bytes 64MiB;
large 151,936-token/score fixtures pass. Final focused 194 passed in 5.14s; lint/types
pass. Initial full gate refused a magic-number lint before tests; fixed with a
named enum constant and restarted from the beginning. Required full gate passed. Final independent review is clear.

Reviewed INV-018, AD-01/07/12/15/17/18, FS-09/11/15/19 and decision 133. Existing
publication/integrity/lock/transaction authority remains; no new architectural
exception/dependency. Updated discovery details and ADR133/invariant enforcement
links. No production, credential, live Hub/NFS, service, archive CLI initialization
or push action. Writer capture and transports remain later packages.

## Validation mapping

- V15: every supported pinned general.file_type mapping; distinct F32/F16/BF16
  encoding, known simple nominal bits and unknown mixed K/IQ bits; deterministic
  member identity, qualified source and logical file-byte totals.
- V16: misleading filenames cannot supply/override a scheme; missing, removed,
  unknown and guessed enums remain unknown candidates; clear tensor-header
  contradictions suppress completeness without inferring a mixed scheme.
- V17: hostile magic/version/endian/count/string/type/Unicode/duplicate/depth,
  boolean/key/alignment/dimension/product/offset/overlap inputs; truncation at
  every header offset; actual FileIO read/tell spy stops at tensor-info end;
  shared work/read exhaustion and realistic 151,936-token arrays are bounded.
- V18: ordinary metadata-light later shards, header-only first shard, full unique
  membership/bytes, missing/duplicate/conflicting indices/counts/totals/identity/
  schemes/tensor names, different directories/prefixes/publications, and single/
  split prefix collisions. Incomplete subsets never satisfy completeness.
- V19: header, canonical filename and tensor adapter/projector/auxiliary evidence
  only downgrades role; unknown architecture and zero-tensor standalone remain
  non-primary candidates. Unknown role is explicit incomplete coverage.

## Completion evidence

Completed 2026-10-19 (CAT-006, this commit). V15-V19 have the concrete fixture
mapping above. Focused `rtk uv run --locked --extra server --extra mcp pytest -q
tests/unit/test_catalog_gguf.py tests/unit/test_catalog_extractors.py
tests/unit/test_catalog_storage.py`: 194 passed in 5.14s. Final lint/types and
human docs alignment pass. Full `rtk proxy scripts/check.sh` exited 0:
4551 passed, 40 opt-in deselected in 486.30s; format/lint/types/docs,
build, all three locked installation profiles and actual Cockpit lint/types/
169 tests/build passed. Complete local log `.git/cat-006-check.log` is ignored.
An initial pre-test lint refusal was fixed and the complete required gate reran;
it is not claimed as green. Final docs/whitespace checks passed.

Independent read-only review is clear; all reported buffer/count/role/validity/
contradiction findings are resolved with fixtures. Reviewed INV-018, AD-01/07/12/
15/17/18, FS-09/11/15/19 and decision 133; no new architecture/dependency or broader
capability exception. Discovery, invariant and ADR133 enforcement links are
updated. [Progress entry](../../progress.md#tags-and-discovery-2026-10-19) records
completion. No production/live/credential/host/service/push action; variant writer
capture, queries and transports remain in later packages.
