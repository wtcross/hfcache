# Decision 080: A `DOC` package family, tracked outside §28's phase set

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-28.
- Original work package: `DOC-001`.
- Source: [decision 80 in the append-only Decisions log](../progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

Plan §28's phases end at Phase 8 and Phase 8 ended with
`REL-004`; the repository then gained a public remote (`github`, primary)
and a lab mirror (`forgejo`), which the plan never modelled — §36.2 says
"no remote is configured; do not push", and §7's layout has no
agent-context files. The preparation work is real work and this tracker is
the record of work, so it is tracked the same way as everything else: a
`DOC` family under its own section, one package per commit, a decision for
each deviation as it lands. The alternative — doing it untracked because
the phases are over — would make this file's claim to be authoritative
quietly false at the exact moment the repository becomes visible.

## Later history and current interpretation

The maintenance workflow now governs work-package selection. [Decision
82](decision-082.md) explicitly supersedes the original plan protocol for
sessions after the build-out.

## Provenance and governing evidence

The source entry first appears in
[e23cf90](https://github.com/wtcross/hfcache/commit/e23cf90adab96cfe038169fe1f459669f25eb5a6)
(2026-07-28, `DOC-001: remove stale placeholders and consolidate .gitignore`).
The decision text above preserves the complete reasoning in the current
historical log, including its recorded alternatives and consequences.

Current governing documents:
[docs/agents/workflow.md](../../docs/agents/workflow.md).

Implementation or shipped-artifact evidence: [AGENTS.md](../../AGENTS.md),
[docs/progress.md](../../docs/progress.md).

Relevant verification: [docs/plan.md](../../docs/plan.md).
