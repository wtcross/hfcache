# DOC-013: Rewrite the MCP guide for users and administrators

| Field | Value |
| --- | --- |
| Status | completed |
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

- [x] A reader can understand enablement, connect, list tools and interpret a result without following any implementation-history link.
- [x] The documented nine names and schemas match actual mounted `tools/list`; no execution capability appears.
- [x] Native and rootless credential/setup instructions are explicitly distinct and match templates/helpers.
- [x] The guide explains finite JSON/stateless/authentication/rotation/limits accurately and contains no task or plan references.
- [x] The protected-file example remains bounded, secret-safe and tested against disposable mounted HTTP fixtures.

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

Started 2026-10-18 after DOC-012 75cbea1. Work on `feat/rest-api-and-mcp`, preserving existing user changes and
all live-host restrictions. Do not push, merge, tag, deploy, rotate credentials,
run production probes or manipulate NAS/services. If blocked, record the missing
prerequisite and precise unblock condition here and in the current selector.

## Completion evidence

2026-10-18, this commit: the entire guide now leads with connection, nine tools,
identity/pagination, rotation, bounds and distinct installation profiles. Prior
MCP/consumer bodies and hashes remain under agent history. Descriptive anchors
and inbound links are repaired; ten transitional entries removed (993 to 983).
Native optional staging/named-source delivery is distinct from the selected
MCP-enabled rootless template's Podman file source. Exact allowlist, schemas,
full-source cursor binding, finite/stateless negotiation, ignored optional task
metadata without execution authority, no-write/no-Hub and whole-archive trust
remain unchanged. Example help describes protected paths and bounded options.

Focused mounted transport/tools/client/security/acceptance/links/migration:
223 passed in 41.19s. Tool-table equality and actual disposable HTTP/TLS example
output now supplement independent registry/schema/bounds checks. Ruff/Pyrefly
(0 errors) passed. Full `scripts/check.sh` exited 0: 4173 passed/40 opt-in
deselected in 482.75s, build, three locked installation profiles, actual Cockpit
lint/135 tests (0 skipped)/production build. Log `/tmp/hfcache-doc013-gate.log`.
Independent read-only review found no material omissions. Reviewed INV-002/003/
007/010/016 and ADR124/125: no technical invariant, schema, dependency or runtime
change; no new ADR needed. No production operation or credential access ran.

See [completed progress entry](../../progress.md#mcp-user-guide-2026-10-18).
Next ready task: DOC-014. Final authorized branch pushes follow plan acceptance.
