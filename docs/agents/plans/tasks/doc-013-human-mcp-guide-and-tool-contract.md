# DOC-013: Rewrite the MCP guide for users and administrators

| Field | Value |
| --- | --- |
| Status | pending |
| Plan | [REST/MCP documentation and script alignment](../2026-10-18-plan-rest-mcp-docs-scripts-alignment.md) |
| Depends on | [DOC-012](doc-012-human-rest-and-client-reference.md) |
| Phase | 2 — Human-facing guides |
| Review findings | F01, F04, F10 |
| Suggested commit | `DOC-013: make the MCP guide user centered` |

## Scope and implementation requirements

Replace the introduction quoted by the user with a direct description of what MCP exposes, how to connect and what it cannot do. Rewrite the entire guide, not just its first paragraph. Remove task IDs, plans, implementation phases, acceptance-task ownership, "adds" chronology and references to agent-only history.

Keep the exact nine-tool allowlist and describe each tool's inputs, output, pagination, error/cost bounds and identity guarantees. Actual verification is not a tool: only reading existing evidence and estimating cost are exposed. Keep no-job/no-command/no-Hub/no-write/no-arbitrary-file restrictions and whole-archive restricted-metadata authorization explicit.

Document the actual mounted Streamable HTTP endpoint and canonical trailing slash, stateless finite-JSON behavior, negotiation, per-request bearer authentication, no session-based bypass, no OAuth discovery/registration, startup-only source rotation and disabled-mode behavior. Explain that upstream SDK features do not automatically become hfcache features. Match the locked SDK and tests rather than changing dependencies to suit current upstream examples.

Separate setup for a base/REST-only installation, an explicitly enabled native MCP installation, and the selected rootless template. Native `--with-mcp`/systemd credential examples must not appear as universal container installation instructions. The selected rootless helper/template delivers named Podman secrets as files and currently enables MCP; describe that profile accurately without silently making it configurable.

Keep and improve `examples/mcp-client.py` instructions: protected token pathname, CA trust, endpoint/prefix, archive pin, bounded reads, page/deadline failure, deterministic output and safe errors. Include a complete sample workflow using only fixtures. Do not add an agent runtime, dynamic tool execution or writable tooling.

## Acceptance

- [ ] A reader can understand enablement, connect, list tools and interpret a result without following any implementation-history link.
- [ ] The documented nine names and schemas match actual mounted `tools/list`; no execution capability appears.
- [ ] Native and rootless credential/setup instructions are explicitly distinct and match templates/helpers.
- [ ] The guide explains finite JSON/stateless/authentication/rotation/limits accurately and contains no task or plan references.
- [ ] The protected-file example remains bounded, secret-safe and tested against disposable mounted HTTP fixtures.

## Contracts, invariants and ADRs

`mcp.py`, `mcp_tools.py`, `api/mcp_reads.py`, metadata query models, protected token registry and server lifecycle; whole-archive trust, exact-publication and read-only invariants. Keep technical ADR rationale under descriptive human links only.

Paths above use the reviewed repository's names for identification. DOC-011 owns
the authoritative relocation map; after that package use the current path and
preserve the same contract/record identity. Read relevant sections progressively.
Record an explicit no-impact review when no technical invariant changes; do not
create a ceremonial technical ADR for an editorial-only change.

## Documentation in this work package

Rewrite `docs/mcp.md`, relevant consumer/API cross-links and MCP example help/docstrings. Use the sample introduction in the master plan as a style model, not as a substitute for the complete rewrite.

Human docs describe current behavior, limitations and examples without task IDs,
plans, progress links or implementation chronology. This task file and the agent
progress log contain execution evidence. Keep related code/tests/docs together.

## Validation

Exercise actual mounted SDK modern/legacy negotiation as supported by the lock, auth matrix, exact registry, pagination, timeout, prefix/slash behavior and no-side-effect tests. Run `scripts/check.sh`.

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
