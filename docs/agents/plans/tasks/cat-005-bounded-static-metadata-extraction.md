# CAT-005: Extract bounded static model and dataset declarations

| Field | Value |
| --- | --- |
| Status | completed |
| Plan | [Tags and discovery](../2026-10-19-plan-tags-and-discovery.md) |
| Phase | 2 — Metadata foundation |
| Depends on | [CAT-004](cat-004-metadata-records-and-storage.md) |
| Implementation branch | `feat/tags-and-discovery` |
| Commit boundary | One package / one commit: `CAT-005: <completed outcome>` |

## Required context

Follow `AGENTS.md` and `docs/agents/workflow.md`. Read relevant sections of the
[design](../support/tags-and-discovery/design.md),
[source review](../support/tags-and-discovery/source-review.md) and
[validation matrix](../support/tags-and-discovery/validation-matrix.md).
Tasks own execution status; evidence below records the current implementation.

## Likely implementation touchpoints

Proposed catalog_extractors.py or a small catalog extraction package; dependencies.py patterns; metadata readers; synthetic card/JSON fixtures.

Inspect actual callers and tests before editing. Suggested new module names are
not requirements to create redundant layers when an existing small abstraction fits.

## Scope and requirements

Build a transport-neutral extractor interface with explicit version, actual-read/work limits, manifest-contained source paths, supported/partial/unsupported/failed states and safe diagnostics. Never import repository code, runtime model libraries or dataset loaders; never contact the Hub or follow source URLs.

Read selected model/dataset card front matter and known JSON declarations as untrusted data, with byte/count/depth/alias/Unicode/duplicate-key checks. Safe YAML constructors alone are not a resource bound. Extract only allowlisted useful fields with provenance; do not save or return raw arbitrary cards/config JSON.

Preserve upstream tags as attributed observations separate from the sole curated tags field; they never satisfy operator-tag filters. For datasets, distinguish observed file-format candidates from declared configurations/splits/features and do not infer physical availability, row counts or external payload completeness from a card.

Provide reusable safe file access and budgeting for GGUF/weight configuration extraction. Define exact absent-versus-failed behavior and warning classification. Retain dependency detection semantics and avoid unrelated parser rewrites unless necessary for the safety boundary.

## Acceptance criteria

Small offline model/dataset fixtures produce deterministic bounded observations. Hostile inputs cannot execute or allocate unbounded structures. Parser errors yield truthful partial/failed state, not guessed values. No network, dataset execution or payload-wide scanning occurs.

## Contracts, invariants and ADRs

Review the affected current human contracts and `docs/invariants.md` through its
index; consult related technical ADRs listed in the source review. Record explicit
changes or an explicit no-impact finding in completion evidence. Amend contracts
in the same commit as behavior; add required ADR/index/progress decision entries
without copying agent task narration into human guides. Do not silently override
a filesystem, security, format, candidate, read-budget or MCP boundary.

## Validation

Matrix coverage: V12, V13, V14

Focused parser fixtures, alias/depth/count bombs, no-follow tests and import/network spies; full gate. No live Hub fixtures.

Every package requires `scripts/check.sh` exit 0, including docs-only work. Required
frontend checks must actually execute for frontend changes. Offline fixture success
does not imply live Hub/NFS or deployed acceptance. Missing prerequisites and failing
tests remain blockers, with their exact unblock condition recorded below.

## Execution notes and handoff

Implemented standard-library-only bounded JSON and conservative YAML front matter
parsers, exact manifest-contained no-follow source access and shared actual-read/
work accounting, including truncated and failed reads. Explicit static-1 source
provenance, deterministic selected values and fixed safe diagnostics distinguish
optional absence, unsupported, failed and useful partial extraction. Dataset
formats are filename evidence; config/split/feature names are declarations only.
No model/dataset/loader imports, URLs, network, code execution or dataset payload
reads. Upstream labels remain attributed upstream_tags, never operator tags.

Independent safety review prompted preallocation YAML token/physical-line checks,
length-before-list checks, native scalar preservation, common quoted-list and
apostrophe handling, declared data_files split names and conservative read-error
accounting. Final review found no remaining material issue; its minor mixed-flow-list status
classification was corrected and regression-tested. Focused expanded suites passed 224 tests in
10.18s; final extractor suite passed 37 in 0.88s. A pre-final gate was intentionally stopped (exit 143) for that classification
fix; the required gate was restarted from the beginning and passed.

Reviewed AD-01/07/12/15/17/18, FS-09/11/15/19, INV-018 and decision 133.
AD-15/133 and the invariant enforcement links now document the selected published
metadata source boundary; no broader writer/transaction/credential capability or
new architectural exception/dependency is introduced. Discovery/security/CLI docs
state parser support, bounds, statuses and HFWRN011 warning classification.
Corrected the older security claim that the unchanged dependency detector already
had the new resource bounds; dependency behavior and existing fixtures are retained.
No host, production, credential, live Hub/NFS or push operation.

## Validation mapping

- V12: hostile JSON duplicate/nonfinite/deep/Unicode/large ignored input, YAML
  alias/custom-tag/duplicate/block/flow/deep/node/physical-line cases, predecoder
  allocation spy, strict scalar types, source/output/candidate/work/read budgets,
  symlink leaf/parent and exact/unlisted publication source refusals. Failed and
  truncated read accounting cannot reset the shared actual-read budget.
- V13: selected upstream labels retain exact manifest provenance and original
  values; there is no operator-tags field or config mutation in this interface.
- V14: dataset feature/config/split contexts (including declared external data-file
  splits) and filename format candidates have distinct attribution. Network/import
  spies and an open spy prove no dataset payload, loader or external URL access;
  arbitrary text/row counts/path declarations are not retained as availability.

## Completion evidence

Completed 2026-10-19 (CAT-005, this commit). V12-V14 have the fixture evidence
mapped above. Expanded focused command: `rtk uv run --locked --extra server --extra
mcp pytest -q tests/unit/test_catalog_extractors.py tests/unit/test_dependencies.py
tests/unit/test_catalog_storage.py tests/unit/test_transactions.py
tests/unit/test_verification.py` — 224 passed in 10.18s. Final extractor suite:
37 passed in 0.88s. Full `rtk proxy scripts/check.sh` exited 0: 4452 passed,
40 opt-in deselected in 485.46s; format/lint/types/docs, build, all three locked
installation profiles and actual Cockpit lint/types/169 tests/build passed.
Complete local gate log: `.git/cat-005-check.log` (ignored). The earlier pre-final
run was intentionally stopped for the mixed-list classification correction, and
is not claimed as passing. Final docs/whitespace checks passed.

Independent review is complete with no remaining issue. AD-15/133 and INV-018
now link parser/access enforcement; AD-01/07/12/17/18 and affected filesystem/
capability requirements retain existing authority. No new dependency or broader
architectural exception. Human discovery/security/error documentation is updated;
[progress entry](../../progress.md#tags-and-discovery-2026-10-19) records completion.
No live/production/credential/host/push action; writer integration, variants and
transport/query behavior are still pending in their selected packages.
