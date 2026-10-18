# API-006: Serve authenticated REST resources with a controlled lifespan

| Field | Value |
| --- | --- |
| Work package | `API-006` |
| Status | pending |
| Plan | [2026-10-17-plan-rest-api-and-mcp.md](../2026-10-17-plan-rest-api-and-mcp.md) |
| Depends on | [API-005](api-005-server-config-and-bearer-auth.md) |
| Phase | 2 — REST implementation |
| Feature branch | `feat/rest-api-and-mcp` |
| Suggested commit | `API-006: serve authenticated FastAPI metadata resources` |

## Scope and acceptance

1. Build an injectable FastAPI app factory and `hfcache serve` bootstrap. Use one lifespan for dependencies, read-pool bounds, instance locking, startup checks, and shutdown. Importing the app must not start listeners, contact the Hub, mutate an archive, or initialize storage.
2. Expose version/capabilities/health, status, inventory/revision pages, exact references/manifests, existing report reads, verification estimates, and archive inspection through shared query services. Handle an uninitialized/unreachable archive diagnostically; authenticated health never repairs it.
3. Protect every REST route, error surface, OpenAPI document, and optionally enabled docs UI. Configure request/body/response limits, safe headers, trusted proxy/Host/Origin rules, and typed HTTP error translation. Test both path components of namespace/name repository IDs.
4. Offload blocking filesystem queries to a bounded pool so event-loop responsiveness is independent of archive scanning. Define deterministic pagination, identity checks, stale/vanished publication errors, and safe large-report streaming. Use one registry for Unix/TCP serving, not independent writer apps.

## Contracts, invariants, and ADRs

`FS-01`–`FS-03`, `FS-08`–`FS-12`, `FS-16`, `INV-003`, `INV-005`–`INV-008`; plan §§3–4.

Use the [invariant register](../../invariants.md) and
[ADR index](../../adr/README.md) to load the cited sections and related records.
Record the review outcome and any explicit lack of impact on completion.

## Documentation in this package

Expand API resources/errors/pagination and server lifespan/listener documentation. Update README and consumers for published-relative locators and authenticated reader discovery. Document current route availability honestly before job routes land.

## Validation

Planned checks, not execution evidence:

ASGI factory/lifespan and real ephemeral local-socket smoke tests; auth across all routes including docs; no startup archive writes; missing/corrupt catalog; mount unavailable; malicious IDs/path traversal; concurrent read responsiveness; page boundary and large-report tests. Run `scripts/check.sh`.

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
