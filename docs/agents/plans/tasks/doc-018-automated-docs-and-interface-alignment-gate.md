# DOC-018: Add executable documentation and script-alignment checks

| Field | Value |
| --- | --- |
| Status | completed |
| Plan | [REST/MCP documentation and script alignment](../2026-10-18-plan-rest-mcp-docs-scripts-alignment.md) |
| Depends on | [DOC-017](doc-017-reader-first-onboarding-and-human-navigation.md) |
| Phase | 3 — Prevent recurrence and close |
| Review findings | F01, F04, F06, F07, F09, F10, F11, F13, F14 |
| Suggested commit | `DOC-018: enforce documentation and interface alignment` |

## Scope and implementation requirements

Add a deterministic documentation alignment checker to `scripts/check.sh` and the relevant test suite. Use the standard library/existing dependencies unless a material new dependency is explicitly justified. It must run offline, with no service-manager, Podman, credential or archive access.

Enumerate human surfaces: `README.md`, `CHANGELOG.md`, all `docs/**` outside `docs/agents/**`, `cockpit/README.md`, other human package/example guides, and generated public CLI/OpenAPI/MCP/script help. Agent roots are `AGENTS.md`, its symlink, and `docs/agents/**`; do not exclude all docs or all ADRs to make the check pass.

Reject human references to planning/task/progress/agent-process records, actual work-package IDs and stage-chronology patterns. Detect links in prose, tables, reference-style links, literal paths and relevant HTML, not just inline markdown. Do not ban legitimate product concepts such as `hfcache plan`, retention/recovery plans, JSON-RPC, MCP clients, technical invariants or stable error codes. Include tests proving those are allowed. Remove the transitional leakage baseline entirely before completion.

Check internal link targets and stable anchors after relocation. Compare route/mode/auth documentation with an application fixture and typed models; compare the nine-tool table with an actual mounted registry; compare configuration defaults/constraints with Pydantic models and packaged examples. Validate script inventory coverage against tracked helpers and ensure each executable's help/dry-run is safe or explicitly classified as non-executable library code.

Use parse-only checks for dangerous shell recipes and separate explicit fixture execution for safe examples. Never execute all markdown code fences indiscriminately. Any installed-image/systemd/SELinux test retains opt-in/operator boundaries and cannot be counted as an offline pass.

Add targeted regression tests for the review's actual problems: wrong base/listener descriptions, obsolete operational `--config`, local-CLI-unbounded wording, quiet diagnostics, task-centric MCP introduction, generic-exception isolation passes and script-profile misuse. Prefer registry/value/behavior assertions over brittle prose snapshots. Keep supporting generator/source ownership clear so manually editing generated references cannot hide divergence.

## Acceptance

- [x] A representative leaked task ID, plan link, literal old selector path, stage introduction or missing documentation/script entry fails the gate.
- [x] Legitimate runtime errors/invariants, `hfcache plan` and domain recovery plans are not false positives.
- [x] Actual API/MCP/config/script facts are checked with executable fixtures rather than only searching for words.
- [x] Human references to agent tracking are zero, with no broad or leftover baseline exemptions.
- [x] The documentation gate cannot touch the real host/archive/network or execute an arbitrary snippet; its own failure tests are included.

## Contracts, invariants and ADRs

Revised human-document policy, current human technical contracts, optional dependency boundaries and offline/hermetic test invariant. Preserve the repository gate and single-work-package evidence requirements.

Paths above use the reviewed repository's names for identification. DOC-011 owns
the authoritative relocation map; after that package use the current path and
preserve the same contract/record identity. Read relevant sections progressively.
Record an explicit no-impact review when no technical invariant changes; do not
create a ceremonial technical ADR for an editorial-only change.

## Documentation in this work package

Document the checker and source-of-truth rules in human development/scripts guides without agent-process discussion. Agent guides record how to maintain planning evidence and the separate audience boundary.

Human docs describe current behavior, limitations and examples without task IDs,
plans, progress links or implementation chronology. This task file and the agent
progress log contain execution evidence. Keep related code/tests/docs together.

## Validation

Run checker unit tests including intentional-bad fixtures, route/tool/config/inventory checks, safe-help subprocess isolation, markdown link tests and `scripts/check.sh --with-build`. Run Cockpit gate when affected; an unrun required stage is not a pass.

Required checks are planned, not performed. Record exact commands, exit results,
coverage and any explicit skips on completion. Do not replace meaningful tests
with weaker assertions merely to accommodate wording changes.

## Execution notes and handoff

Started 2026-10-18 after DOC-017 23d7c6c. Work on `feat/rest-api-and-mcp`, preserving existing user changes and
all live-host restrictions. Do not push, merge, tag, deploy, rotate credentials,
run production probes or manipulate NAS/services. If blocked, record the missing
prerequisite and precise unblock condition here and in the current selector.

## Completion evidence

Completed 2026-10-18, this commit. Added import-safe `scripts/check-docs.py` to
the provider-neutral gate using the existing locked Markdown parser. It discovers
180 human Markdown documents, validates CommonMark/reference/image/HTML links and
real heading/explicit anchors, refuses repository/symlink escapes and agent-target
aliases, and requires all 19 helpers once with explicit inspection modes. Raw and
rendered audience checks reject encoded/literal paths, mixed-case/formatted IDs
and stage introductions while permitting runtime/technical identifiers and domain
plans. The transitional baseline field is removed entirely.

Bad fixtures cover links, duplicate headings, escapes, aliases, stale/missing/
duplicate/unclassified helper rows, inert recipes and caught import-time access.
All approved Python/shell helper and example help paths are checked with file,
manager/engine/process/network guards; ordinary interpreter metadata and reviewed
pins remain permitted. CLI help and generated OpenAPI/MCP descriptions are clean.
Model comparisons cover server/client/archive defaults, required fields, numeric
bounds/inclusivity, retention choices, mandatory hashing and repair floor.
Selected base/listener/readiness facts match artifacts; actual mounted MCP
argument fields match the new reference. Independent REST route/mode/security
and role fixtures remain intact. All 177 preserved snapshots now have tested
original Git hashes and current snapshot hashes.

Validation: integrated focused 246 passed in 27.57s; final reviewed boundary,
configuration and help 95 passed in 6.02s; Ruff and Pyrefly passed. One running gate
was deliberately interrupted to include the final boundary fixes. Full final
`scripts/check.sh --with-build` exited 0: 4315 passed/40 deselected in 483.90s;
distributions, three locked profiles, actual Cockpit lint/types/135 tests/build
and four opt-in wheel smoke tests (5.94s) passed. Checker reports 180 human docs,
19 helpers and zero errors. No external host/NAS/manager/image operation ran.
Reviewed INV-010, existing dependency exceptions, all affected source-of-truth
contracts and migrated authority policy. No runtime dependency, archive format,
application behavior or architectural authority changed.

See [completed progress evidence](../../progress.md#documentation-and-interface-gate-2026-10-18).
