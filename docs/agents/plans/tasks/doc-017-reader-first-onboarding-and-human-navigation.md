# DOC-017: Make onboarding, examples and navigation reader-first

| Field | Value |
| --- | --- |
| Status | pending |
| Plan | [REST/MCP documentation and script alignment](../2026-10-18-plan-rest-mcp-docs-scripts-alignment.md) |
| Depends on | [DOC-016](doc-016-human-architecture-config-schemas-and-adrs.md) |
| Phase | 2 — Human-facing guides |
| Review findings | F01, F02, F03, F04, F11, F12, F13 |
| Suggested commit | `DOC-017: make documentation navigation and onboarding reader first` |

## Scope and implementation requirements

Rewrite the root README and documentation navigation for people evaluating, using, operating or developing hfcache. Start with what it does, API reader quickstart, writer administration, MCP metadata and storage/consumer boundaries. Remove implementation-stage walkthroughs, work-package references, current-plan/task tables and agent-router promotion from human documentation. `AGENTS.md` remains independently discoverable for agents.

Provide a human `docs/README.md` index and concise `docs/development.md` where necessary. Keep current version/release notes concise and product-focused; move local deployment facts to the human status page and execution history to agents. Rewrite CHANGELOG entries without work-package IDs/agent phases while preserving version/date, feature/fix details, breaking changes and rollback warnings. Do not fabricate new release/tag/deployment state.

Update `docs/quickstart.md` to use separate API configuration and protected reader credentials with a provisioned endpoint, no archive mount/config/Hub token and no local fallback. Give writer and MCP users their own links. Native and fixed rootless client examples must be clearly separated. Never suggest operational writes against the guarded local deployment.

Retain `examples/copy-revision.py`, consumer-store setup and serving helpers: REST/MCP metadata do not replace NFS bulk copy and independent verification. Improve `docs/consumers.md` to explain exact publication discovery, locator bases, full local verification, retry on vanished identity, permissions and immutable promotion without implying an HTTP file-transfer API.

Update development setup and examples to match all-extra test collection, optional base/server/MCP installation profiles, gate commands and actual script inventory. Rewrite example/script help and top-level human introductions without task-centered wording. Safe example checks must not run build/install/probe workloads just because a file is in an examples directory.

## Acceptance

- [ ] Human navigation contains no link to task/plan/progress/agent-process records; each audience has a clear starting point.
- [ ] Reader quickstart requires only a provisioned API endpoint and protected API credentials, with verified TLS and explicit uncertainty handling.
- [ ] README, changelog and directory descriptions match current implemented profiles and helpers rather than stage chronology.
- [ ] Consumer tools remain documented as an independent data path; no false API-file-serving promise appears.
- [ ] Development commands collect the right optional dependencies and distinguish safe offline tests from opt-in network/NFS/build work.

## Contracts, invariants and ADRs

Reader/client and MCP setup, consumer invariants `FS-12`, `INV-008`, `INV-009`; base/optional dependency profiles; scripts quality gate and release compatibility constraints.

Paths above use the reviewed repository's names for identification. DOC-011 owns
the authoritative relocation map; after that package use the current path and
preserve the same contract/record identity. Read relevant sections progressively.
Record an explicit no-impact review when no technical invariant changes; do not
create a ceremonial technical ADR for an editorial-only change.

## Documentation in this work package

Rewrite README/CHANGELOG, quickstart, consumers, examples/help and human indexes; create `docs/README.md` and `docs/development.md` as needed without duplicating normative references.

Human docs describe current behavior, limitations and examples without task IDs,
plans, progress links or implementation chronology. This task file and the agent
progress log contain execution evidence. Keep related code/tests/docs together.

## Validation

Validate every local link and all example invocation grammar. Exercise safe examples against synthetic API/MCP fixtures and consumer temporary trees only. Verify dependency-profile installation tests and `scripts/check.sh`.

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
