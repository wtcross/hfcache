# API-015: Preserve Cockpit operations, progress, and candidate configuration flow

| Field | Value |
| --- | --- |
| Work package | `API-015` |
| Status | pending |
| Plan | [2026-10-17-plan-rest-api-and-mcp.md](../2026-10-17-plan-rest-api-and-mcp.md) |
| Depends on | [API-014](api-014-systemd-and-deployment-integration.md) |
| Phase | 3 — CLI and REST integration |
| Feature branch | `feat/rest-api-and-mcp` |
| Suggested commit | `API-015: preserve Cockpit workflows through the API-backed CLI` |

## Scope and acceptance

1. Update Cockpit’s command/transient-unit construction to invoke the API-backed CLI with client configuration/socket and a systemd-imported API credential. Ordinary runtime calls no longer pass archive --config. The browser never reads, stores, or submits a bearer token.
2. Keep full sync/verification attached to their installed service names and preserve schema-1 failure parsing. Preserve selected sync and operation progress through the CLI’s bounded event stream and terminal envelope. Explain that closing a view or stopping a client does not cancel accepted server work.
3. Preserve candidate creation, CLI server-side validation/preview, atomic privileged install/backup, and installed fingerprint confirmation. Show authority-change preview restrictions explicitly. A newly installed policy affects future operations, not an admitted snapshot; stale queued mutations fail safely.
4. Preserve root/admin/service-identity separation, lock/busy reporting, schedule-only sync timer controls, and no archive-init UI. Existing direct run-report browsing may remain its documented exception; do not add new direct archive writes or an in-browser REST credential backend.

## Contracts, invariants, and ADRs

`CP-01`–`CP-14`, `INV-002`/`INV-003`/`INV-006`; plan §§6–7.

Use the [invariant register](../../invariants.md) and
[ADR index](../../adr/README.md) to load the cited sections and related records.
Record the review outcome and any explicit lack of impact on completion.

## Documentation in this package

Update `docs/cockpit.md`, relevant `docs/cockpit-plugin/` install/usage/acceptance pages, API-client integration examples, security/Cockpit invariant notes, and changed command/credential ADR statuses. Preserve all CP controls or amend their precise mechanism explicitly.

## Validation

Planned checks, not execution evidence:

Cockpit command/envelope/config/schedule tests plus integration fixtures for candidate preview/install, API auth failure, busy/stale operation, streaming failure envelope, and page closure. Search built/source UI for bearer/Hub-secret handling. Run the full `make -C cockpit check` stage and `scripts/check.sh`; skipped plugin coverage blocks completion.

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
