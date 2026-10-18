# MCP-002: Expose a curated, structurally read-only archive toolset

| Field | Value |
| --- | --- |
| Work package | `MCP-002` |
| Status | pending |
| Plan | [2026-10-17-plan-rest-api-and-mcp.md](../2026-10-17-plan-rest-api-and-mcp.md) |
| Depends on | [MCP-001](mcp-001-mount-authenticated-fastmcp.md) |
| Phase | 4 — Read-only MCP |
| Feature branch | `feat/rest-api-and-mcp` |
| Suggested commit | `MCP-002: expose curated read-only archive tools` |

## Scope and acceptance

1. Implement exactly the initial tool allowlist in plan §8 using the narrow read-service interface: status; repository/revision inventory; exact current reference and manifest; existing run/verification evidence; and estimate-only verification cost. Register stable descriptive names, typed inputs/outputs, bounded pagination, and honest unknown/stale results.
2. Pin publication identity when resolving refs/manifests. Do not substitute a newer instance when a requested publication vanishes. Read authoritative evidence and never repair/rebuild a catalog as part of a read. Treat metadata/content-derived strings as untrusted data.
3. Make command submission, writable helpers, Hub clients, credential resolution, and arbitrary path/URL reads unavailable to tool adapters. No automatic full-OpenAPI conversion, generic dispatch, doctor probes, actual verify, download, mutation, recovery, or cleanup tools.
4. Add read-only/non-destructive annotations as descriptions, not enforcement. Enumerate the complete registry and test exact equality to the approved allowlist. Any new resource/prompt handler must receive the same structural and side-effect review rather than becoming a hidden bypass.

## Contracts, invariants, and ADRs

`AD-15`/`AD-21`, `FS-08`–`FS-12`/`FS-16`, `INV-005`/`INV-007`/`INV-008`; plan §8.

Use the [invariant register](../../invariants.md) and
[ADR index](../../adr/README.md) to load the cited sections and related records.
Record the review outcome and any explicit lack of impact on completion.

## Documentation in this package

Document every tool’s inputs, output, ordering/bounds, source of truth, cost, confidence limitations, and error cases in MCP docs. Update API/consumer cross-references and the invariant/ADR rationale for whitelist-only exposure.

## Validation

Planned checks, not execution evidence:

Tool schema/registry snapshots, parity with REST/shared read service results, pagination and large manifests/reports, corrupt/missing catalogs, unmanaged data, partial archives, traversal/identity mismatch, stale publication, and unknown verification confidence. Assert no Hub/command/mutation adapters are called. Run `scripts/check.sh`.

## Execution and completion rules

Follow the [parent plan](../2026-10-17-plan-rest-api-and-mcp.md) and
[repository workflow](../../agents/workflow.md). Work only on
`feat/rest-api-and-mcp`. A task may include several related subtasks, but this
work package owns one implementation commit. Read the affected invariant and ADR
sections before editing; update their enforcement/decision links where behavior
changes. Include code, tests, documentation, task evidence, the current pointer,
and completed progress audit together. Do not run production operations or weaken
host controls. Do not push, merge, tag, or deploy.

Mark `in_progress` only when authorized and dependencies are complete. On a real
blocker, record the exact missing prerequisite and unblock condition. A skipped
required test is not passing evidence. Use `this commit` until a real commit exists.

## Execution notes and handoff

Not started. The draft does not authorize implementation. Record actual changes,
resolved design issues, scope amendments, and any blocker/unblock condition here.
Operator-only deployment checks remain explicit handoff items, not asserted passes.

## Completion evidence

Not executed. On completion record the date; acceptance results; exact commands
and outcomes; invariant/ADR review and amendments; documentation changes; a link
to this package's completed [progress audit](../../progress.md); and any operator
handoff. Then set Status to `completed` in the same commit as the work.
