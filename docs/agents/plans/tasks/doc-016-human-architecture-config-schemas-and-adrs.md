# DOC-016: Consolidate living technical contracts and architectural rationale

| Field | Value |
| --- | --- |
| Status | pending |
| Plan | [REST/MCP documentation and script alignment](../2026-10-18-plan-rest-mcp-docs-scripts-alignment.md) |
| Depends on | [DOC-015](doc-015-deployment-runtime-and-cockpit-guide-alignment.md) |
| Phase | 2 — Human-facing guides |
| Review findings | F01, F02, F07, F10, F14 |
| Suggested commit | `DOC-016: consolidate human technical contracts and ADRs` |

## Scope and implementation requirements

Consolidate architecture, invariants, configuration, schemas, security and human ADRs into current technical contracts. Remove agent process metadata, task/plan/progress provenance, implementation-package headings and superseded "not implemented yet" blocks. Keep actual requirements, threat controls, format compatibility and architectural rationale.

Keep product-relevant requirement/error/schema identifiers: `AD-17`, `FS-19`, `HFAPI019`, schema versions, operation state names and tool names are not task IDs. Human architectural ADRs may retain decision identity, dates, alternatives, consequences, implementation/test references and commit provenance. Replace numeric/task-centric introductions with descriptive technical summaries. Purely planning/workflow/router decisions live in the agent area; mixed records must preserve the technical part without sending humans to execution tracking.

Clarify the three configuration domains (archive policy, server configuration, API client settings), plus protected rendered container profile. Document source precedence and role-specific credentials without ambiguous generic "token-file" instructions. Correct the current server text asserting an unbounded local operational CLI.

Keep archive format, HTTP wrapper/Envelope, MCP protocol, MCP metadata shape, operation receipts and scheduled handles as separate compatibility domains. Preserve deterministic serialization, strict rejection, scope/publication identity, no-replay and audit authority. Document no-IP/no-credential verification, read-only MCP and shared lock lifetimes accurately. Do not change durable formats merely to clean documentation.

Preserve transaction checkpoint table shapes and relevant headings expected by tests, or update parsers to stable descriptive anchors with equivalent assertions. Complete the mapping from the archived historical plan to current contracts and repair source/test links. Human documents must not need the historical plan as hidden normative authority.

Remove duplicate status/progress sections only after their technical requirements have an explicit home. Update the technical ADR index and internal migration manifest in the same package.

## Acceptance

- [ ] Human technical docs have no implementation tracking links, work-package IDs or agent workflow instructions.
- [ ] All standing invariants and old-plan-only technical requirements are represented in current human contracts with no silent weakening.
- [ ] Schema/version/path-base/credential domains are distinct and match implementation.
- [ ] Technical ADR alternatives and consequences remain; purely agent records are confined to agents and no human link points to them.
- [ ] Checkpoint/taxonomy/format tests retain equivalent coverage and all links/anchors resolve.

## Contracts, invariants and ADRs

All affected current invariant sections and ADR topic indexes; strict formats/configuration, authentication/capabilities, single-writer/verification/read-only boundaries and journal checkpoints. Follow the revised agent maintenance workflow.

Paths above use the reviewed repository's names for identification. DOC-011 owns
the authoritative relocation map; after that package use the current path and
preserve the same contract/record identity. Read relevant sections progressively.
Record an explicit no-impact review when no technical invariant changes; do not
create a ceremonial technical ADR for an editorial-only change.

## Documentation in this work package

Rewrite `docs/architecture.md`, `docs/invariants.md`, `docs/configuration.md`, `docs/schemas.md`, `docs/security.md`, remaining `docs/server.md` history and `docs/adr/` indexes/records. Keep agent-process rationale separately.

Human docs describe current behavior, limitations and examples without task IDs,
plans, progress links or implementation chronology. This task file and the agent
progress log contain execution evidence. Keep related code/tests/docs together.

## Validation

Run transaction table, error taxonomy, schema golden fixture, config, auth, lock and side-effect contract tests. Check migrated provenance and requirement coverage rather than matching obsolete task-specific prose. Run `scripts/check.sh`.

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
