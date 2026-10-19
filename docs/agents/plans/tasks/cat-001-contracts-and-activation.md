# CAT-001: Activate the feature plan and establish technical contracts

| Field | Value |
| --- | --- |
| Status | completed |
| Plan | [Tags and discovery](../2026-10-19-plan-tags-and-discovery.md) |
| Phase | 1 — Foundation |
| Depends on | None |
| Implementation branch | `feat/tags-and-discovery` |
| Commit boundary | One package / one commit: `CAT-001: <completed outcome>` |

## Required context

Follow `AGENTS.md` and `docs/agents/workflow.md`. Read relevant sections of the
[design](../support/tags-and-discovery/design.md),
[source review](../support/tags-and-discovery/source-review.md) and
[validation matrix](../support/tags-and-discovery/validation-matrix.md).
Tasks own execution status; this file is pending, not a claim of implementation.

## Likely implementation touchpoints

AGENTS.md routing; docs/agents/plans/current.md; affected human contracts, docs/invariants.md and technical ADR index; source/caller review.

Inspect actual callers and tests before editing. Suggested new module names are
not requirements to create redundant layers when an existing small abstraction fits.

## Scope and requirements

Inspect git log/status, the active selector, relevant progress decisions/handoff, environment and workflow before any implementation. This supplied request is draft-only; the separate implementation instruction is sufficient activation authority. Create or safely reuse feat/tags-and-discovery from the reviewed current checkout; never reset unrelated work or implement on main. Record newer-source differences and reconcile another active plan explicitly.

Open the CAT work-package family deliberately and check that CAT-001 through CAT-016 do not collide with existing records outside this bundle. If a collision exists before activation, allocate unused IDs and update all cross-links as one documented draft amendment; never renumber historical work. Activate the parent plan/current selector before code changes. Do not overwrite current.md merely because the bundle was extracted.

Review the design against current config/fingerprint, publication identity, FS-16 derived-catalog authority, layout, TX-01/FS-17 journaling, initialization, server admission and MCP allowlist contracts. Record the narrow independently atomic auxiliary-record exception and historical-tag authority explicitly; keep every existing archive transaction unchanged. Allocate new ADR/decision/invariant identifiers from the current index, not invented numbers in this draft.

Specify strict new record and catalog payload schemas, exact query/coverage semantics, compatibility and protected behavior in living human contracts before dependent implementation. Establish docs/discovery.md as the human feature contract, clearly proposed until corresponding support exists. Do not mark a feature implemented merely because its design is written.

Document tag-free old-config compatibility versus new-layout/operation rollback barriers, no config-install API, no MCP writes, no extra runtime dependency, and the whole-archive authorization boundary. Keep human docs free of CAT/task links. Capture baseline gate results and blockers; do not claim production acceptance.

## Acceptance criteria

The parent plan is active on the feature branch, with a reconciled selector and no lost prior work. Scope, ADR amendments, record authority and compatibility are explicit and noncontradictory. All sixteen tasks remain linked and pending except the task being completed. The baseline/source review distinguishes inspected facts from untested assumptions. New architectural constraints have planned enforcement/tests, not fictional proof.

## Contracts, invariants and ADRs

Review the affected current human contracts and `docs/invariants.md` through its
index; consult related technical ADRs listed in the source review. Record explicit
changes or an explicit no-impact finding in completion evidence. Amend contracts
in the same commit as behavior; add required ADR/index/progress decision entries
without copying agent task narration into human guides. Do not silently override
a filesystem, security, format, candidate, read-budget or MCP boundary.

## Validation

Matrix coverage: Activation and contract review; full plan/graph/gate baseline.

Read all design sections and matrix; run scripts/check.sh for this documentation/activation package; inspect git diff for accidental implementation, selector overwrite, unrelated permission or human/agent boundary changes.

Every package requires `scripts/check.sh` exit 0, including docs-only work. Required
frontend checks must actually execute for frontend changes. Offline fixture success
does not imply live Hub/NFS or deployed acceptance. Missing prerequisites and failing
tests remain blockers, with their exact unblock condition recorded below.

## Execution notes and handoff

Activated from `75d93a5` on the required feature branch. Source matches the
reviewed `45f91c3`; later Timestral evidence and handoff are preserved. CAT IDs,
decision 133 and INV-018 are unused. Independent read-only review identified
FS-16, TX-01/FS-17 and optional-layout conflicts; the narrow amendments below
resolve them before implementation. Baseline gate is running; no live actions.
When work starts, record any relevant newer-source reconciliation, implementation
choices, blockers and scope amendments here. Preserve prior completed evidence.

## Completion evidence

Completed 2026-10-19 (CAT-001, this commit). Activated the reconciled feature
branch/selector; preserved the complete supplied bundle and Timestral history.
Established proposed human discovery and exact schema-1 record/payload contracts,
optional layout, historical authority, atomic-file exception and compatibility
barriers. Reviewed AD-01/06/07/12/13/14/15/17/18, FS-01/02/03/05–12/15–17/19/21–23,
TX-01/07 and INV-001/002/005/016; added INV-018 and indexed decision 133, amending
AD-12/14/17 and decisions 119/122/125. Existing transactions and nine MCP tools
remain unchanged. Independent read-only review corrections are incorporated.

`rtk proxy scripts/check.sh` exited 0: 4315 passed, 40 opt-in deselected in
489.31s; lock, format/lint/types, build, three locked wheel profiles and actual
Cockpit lint/types/135 tests/build passed. It began as the baseline gate before
contract edits; final documentation alignment independently passed (182 human
documents/19 helpers), and final affected document-parsing suites passed 173/173.
`rtk proxy git diff --check` passed. No implementation, credential, live archive,
network workload, production action or push occurred. Remaining feature behavior
is explicitly proposed, with storage/parser/query/capability/compatibility evidence
required by the pending tasks. See completed progress entry and decision 133.
