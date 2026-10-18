# Decision 081: `AGENTS.md`, `CLAUDE.md`, and `docs/agents/` added beyond plan §7's layout

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-28.
- Original work package: `DOC-002`.
- Source: [decision 81 in the append-only Decisions log](../progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

Four shapes were settled together. **A
router, not a manual:** the three load-bearing documents (`docs/agents/history/plan.md`,
`docs/agents/progress.md`, `docs/architecture.md`) total about 410 KB — an entry
file that embedded or force-loaded them would spend an agent's context
before the task started, so the router maps task to document and stops.
**Backticked paths, not `@`-imports:** Claude Code inlines `@path`
references from `CLAUDE.md` eagerly at session start, which is the exact
opposite of the progressive loading the router exists for; a code-span
path is inert there and reads identically in every other tool. **A
symlink, not a copy:** `CLAUDE.md` and `AGENTS.md` are one file so the two
entry conventions cannot drift; divergence becomes impossible rather than
reviewed-for. **`docs/agents/`, not the contract set:** workflow,
conventions, environment, and release are about how the repository is
worked on; the `docs/` root set is normative for the application, and
mixing the two would blur which documents bind the implementation.

## Later history and current interpretation

The progressive-loading router remains the entry point. The DOC-009 backfill
adds the invariant register and ADR index to that routing and maintenance loop
without requiring every record to be loaded at startup.

## Provenance and governing evidence

The source entry first appears in
[0aff907](https://github.com/wtcross/hfcache/commit/0aff907b66788a70b54937b441808c32d560272c)
(2026-07-28, `DOC-002: AGENTS.md router, CLAUDE.md symlink, and docs/agents/`).
The decision text above preserves the complete reasoning in the current
historical log, including its recorded alternatives and consequences.

Current governing documents:
[docs/agents/workflow.md](../workflow.md),
[docs/agents/conventions.md](../conventions.md).

Implementation or shipped-artifact evidence: [AGENTS.md](../../../AGENTS.md),
[CLAUDE.md](../../../CLAUDE.md).

Relevant verification:
[docs/agents/environment.md](../environment.md).
