# Decision 082: `docs/agents/workflow.md` supersedes plan §36 for sessions after the build-out; pushing joins the loop

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-28.
- Original work package: `DOC-002`.
- Source: [decision 82 in the append-only Decisions log](../progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

§36 was written
for one long autonomous run: startup meant reading the plan in full, no
remote existed, and "do not push" was correct. All three are wrong for
maintenance sessions on a public repository. `workflow.md` starts from the
tracker tail and `AGENTS.md`'s map; `github`
(`git@github.com:wtcross/hfcache.git`) is the primary public repository
and `forgejo` (`ssh://git@git.lab.example.com:2222/<user>/hfcache.git`)
the lab mirror, pushed with `--follow-tags` at package boundaries and
never force-pushed — the history is the audit trail this tracker cites.
What does **not** change: §36.4–§36.5's hard limits, which continue in
`docs/agents/environment.md` and bind any session on the writer, and the
tracker discipline itself. §36 keeps a dated amendment and remains the
build-out's record.

## Later history and current interpretation

The current workflow distinguishes maintainer push access from contributor work;
this historical adoption of remotes does not itself grant push authorization.
The plan remains the original build-out record.

2026-10-17 (`DOC-010`): [Decision 107](decision-107.md) supersedes the
progress-only selection and tracker-authority part of this decision.
`docs/agents/plans/current.md` now selects the active plan, individual task files
own execution status, and progress retains completed evidence, Decisions,
Operator handoff, and unmigrated backlog. The workflow, commit discipline,
host limits, and maintainer push rules remain in force.

## Provenance and governing evidence

The source entry first appears in
[0aff907](https://github.com/wtcross/hfcache/commit/0aff907b66788a70b54937b441808c32d560272c)
(2026-07-28, `DOC-002: AGENTS.md router, CLAUDE.md symlink, and docs/agents/`).
The decision text above preserves the complete reasoning in the current
historical log, including its recorded alternatives and consequences.

The source entry was subsequently amended in
[a0bcee4](https://github.com/wtcross/hfcache/commit/a0bcee4f3facf69c12f3f3d61f70a50417b5c2be)
(2026-07-28, `DOC-005: scrub environment specifics into placeholders`); the
backfill retains the amended text rather than restoring superseded wording or
private environment values.

Current governing documents:
[docs/agents/workflow.md](../workflow.md),
[docs/agents/environment.md](../environment.md).

Implementation or shipped-artifact evidence: [AGENTS.md](../../../AGENTS.md),
[docs/agents/history/plan.md](../history/plan.md).

Verification or recorded operational evidence:
[docs/agents/progress.md](../progress.md).

## Authority-path amendment (2026-10-18)

[Decision 130](decision-130.md) explicitly permits the one-time record
relocation and replaces historical paths with the agent namespace. Original
identity, rationale and completed evidence remain; no host authorization is
renewed. Current technical authority resides in human contracts.
