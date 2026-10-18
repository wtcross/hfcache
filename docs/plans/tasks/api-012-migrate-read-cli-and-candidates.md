# API-012: Move CLI reads and candidate validation/planning onto the API

| Field | Value |
| --- | --- |
| Work package | `API-012` |
| Status | pending |
| Plan | [2026-10-17-plan-rest-api-and-mcp.md](../2026-10-17-plan-rest-api-and-mcp.md) |
| Depends on | [API-011](api-011-typed-client-and-client-config.md) |
| Phase | 3 — CLI and REST integration |
| Feature branch | `feat/rest-api-and-mcp` |
| Suggested commit | `API-012: migrate CLI reads and candidate previews to REST` |

## Scope and acceptance

1. Migrate status/list/inspection/estimate, installed config validate, plan, read-only diagnostics, and report/reference reads to the typed client. Preserve names/selectors, existing schema-1 data semantics, warnings, human rendering, and one-envelope output. Walk API pages rather than silently truncating inventory.
2. Keep local version/help and add `version --server`. Implement explicit `config validate --local` for offline bootstrap without an API fallback. Distinguish local failures from server-reported domain failures while retaining the established exit classifications.
3. Implement explicit `--config` candidates for API validate/plan: read bounded local content, submit TOML content, and never send a path for server interpretation. Validate candidate syntax separately from running-writer compatibility. Require installed authority fields to match before Hub planning, resolve only installed credentials, and refuse credential/endpoint redirection.
4. Reject `--config` for other API runtime commands and reject legacy Hub `--token-file` for API operations with actionable migration messages. No reader command reads local archive data when the server is unavailable. Update shipped caller assumptions as the later integration tasks complete.

## Contracts, invariants, and ADRs

`INV-001`/`INV-002`/`INV-006`, `AD-21`, `CP-11`; plan §7.

Use the [invariant register](../../invariants.md) and
[ADR index](../../adr/README.md) to load the cited sections and related records.
Record the review outcome and any explicit lack of impact on completion.

## Documentation in this package

Update CLI option/command examples, candidate contract and intentional restrictions, API-client migration table, configuration docs, consumer setup, and README. Document `--local` as an explicit local bootstrap exception, not an alternate operating backend.

## Validation

Planned checks, not execution evidence:

CLI CliRunner tests backed by HTTP transport and throwaway server; legacy JSON/human snapshots; all selector/type/revisions modes; config missing on reader; all pages included; same candidate preview as installed-authority policy; malicious endpoint/root/credential candidate refusal before any Hub call; version/help offline. Run `scripts/check.sh`.

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
