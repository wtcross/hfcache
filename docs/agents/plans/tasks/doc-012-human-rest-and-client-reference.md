# DOC-012: Rewrite REST and client documentation as current references

| Field | Value |
| --- | --- |
| Status | pending |
| Plan | [REST/MCP documentation and script alignment](../2026-10-18-plan-rest-mcp-docs-scripts-alignment.md) |
| Depends on | [API-018](api-018-cli-help-output-and-migration-remnants.md) |
| Phase | 2 — Human-facing guides |
| Review findings | F01, F07, F10, F11 |
| Suggested commit | `DOC-012: publish current REST and client guides` |

## Scope and implementation requirements

Rewrite `docs/api.md` and `docs/api-client.md` around how a reader or writer actually uses the interface. Remove incremental implementation chronologies, status-by-package tables, task/plan/progress links and provisional text contradicted by the completed implementation. Retain technical decisions, constraints and precise failure semantics in the current reference.

Provide one canonical route/mode/capability/side-effect matrix derived from registered FastAPI routes and their request models, then cross-check the public CLI mapping. Distinguish synchronous metadata/validation from keyed jobs; archive writes from control-state writes; Hub contact from archive-only reads; and initiation from observation. Include all existing maintenance, diagnostics, verification, candidate and initialization variants without inventing endpoints.

Document authentication for normal/error/health/schema/docs paths, REST reader/writer capabilities, the separate MCP-only bearer, protected source precedence, HTTPS trust, Unix sockets and public prefixes. Do not expose tokens in shell command literals, process arguments or screenshots. Provide protected-file/SDK examples whose emitted headers match the implementation.

Explain 202 acceptance, lookup by original key, observation deadlines, event gaps, terminal HTTP status versus domain exit status, immutable snapshots, uncertain submission, interrupted receipts, no automatic replay and restart/drain. Make common recovery steps usable without reading a task or ADR.

Correct the claim in the server guide that the local CLI is free of HTTP ceilings: public operational commands use HTTP and client aggregation is bounded. State complete-results-or-explicit-failure behavior, configured byte/page/scan limits, identity checks and what pagination does not guarantee under concurrent publication. Do not silently return partial inventory as success.

Document reference locator bases and exact publication identity separately from bulk transfer; REST is not an arbitrary file server. Preserve existing response schemas and deterministic error taxonomy.

## Acceptance

- [ ] Every implemented route/mode is documented once and tested against the live application registry in fixtures; no nonexistent convenience endpoint is shown.
- [ ] Auth, credentials, local/remote bootstrap exceptions and side-effect classifications match code.
- [ ] Lost acknowledgement/reconnect, failed terminal outcomes and bounded collection have complete human instructions.
- [ ] The two guides and related server corrections contain no agent implementation references or human-to-agent links.
- [ ] Examples use only synthetic secrets/data and are parse-/fixture-tested without production access.

## Contracts, invariants and ADRs

API route/model/auth modules, typed client/config/errors, service request models, operation receipt and scheduled handle schemas; `INV-002`, `INV-005`, `INV-006` and read-only metadata boundaries.

Paths above use the reviewed repository's names for identification. DOC-011 owns
the authoritative relocation map; after that package use the current path and
preserve the same contract/record identity. Read relevant sections progressively.
Record an explicit no-impact review when no technical invariant changes; do not
create a ceremonial technical ADR for an editorial-only change.

## Documentation in this work package

Rewrite `docs/api.md` and `docs/api-client.md`; update affected `docs/cli.md`/`docs/server.md` statements and stable descriptive anchors. Keep process history only in migrated agent records.

Human docs describe current behavior, limitations and examples without task IDs,
plans, progress links or implementation chronology. This task file and the agent
progress log contain execution evidence. Keep related code/tests/docs together.

## Validation

Compare documented routes/capabilities to fixture app routing/OpenAPI and typed request models; test protected-file client examples, pagination errors, native/public prefix URLs and unknown versions. Run contract/parity tests and `scripts/check.sh`.

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
