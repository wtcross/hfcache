# API-017: Close the plan with integrated evidence and an operator rollout handoff

| Field | Value |
| --- | --- |
| Work package | `API-017` |
| Status | pending |
| Plan | [2026-10-17-plan-rest-api-and-mcp.md](../2026-10-17-plan-rest-api-and-mcp.md) |
| Depends on | [MCP-004](mcp-004-mcp-client-docs-and-acceptance.md) |
| Phase | 5 — Closure |
| Feature branch | `feat/rest-api-and-mcp` |
| Suggested commit | `API-017: complete REST and MCP integration and operator handoff` |

## Scope and acceptance

1. Review the complete feature-branch diff and incremental commit history. Verify every scoped task is complete or explicitly dispositioned, every behavior change has same-package docs/evidence, and no unintended direct CLI backend, public file server, generic MCP dispatch, secret leak, or unrelated RET-011 fix slipped in.
2. Run full integration across REST writer/read credentials, writer-local and remote-style CLI, systemd wrapper protocols, Cockpit, read-only MCP, interrupted jobs, verification worker isolation, and large results. Re-run the durable/config compatibility drill and document rollback constraints for service-state records.
3. Produce a concrete operator rollout checklist: credentials/permissions, TLS/proxy/firewall, frozen dependencies, server/worker socket units, no-IP worker probe, real NFS/hardening acceptance, drain and rollback, existing client-unit monitoring, and verification timer still disabled. Do not perform these production changes under draft/implementation authority alone.
4. Record all actual gate results and explicitly pending host checks. Close the dated plan and clear only its current active selection. Preserve task/ADR/progress evidence and deliver the local work-package commit series. Do not merge, squash, push, tag, or deploy without separate instruction.

## Contracts, invariants, and ADRs

All affected invariant/ADR sections; `INV-010`/`INV-011`; planning/workflow/environment/release rules; plan §§11–12.

Use the [invariant register](../../invariants.md) and
[ADR index](../../adr/README.md) to load the cited sections and related records.
Record the review outcome and any explicit lack of impact on completion.

## Documentation in this package

Final consistency sweep across newly created and affected docs, with no deferral of earlier packages’ documentation. Complete plan lifecycle/task evidence/progress and Operator handoff links, retaining deployment holds and historical records.

## Validation

Planned checks, not execution evidence:

`scripts/check.sh --with-build` with all implemented extras and the Cockpit toolchain; all real throwaway transport/integration tests; docs/OpenAPI/tool-schema/examples/link checks; no secret artifacts; branch/history/status audit. Explicitly state which opt-in live/NFS/host probes were not run and why.

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
