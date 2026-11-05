# Agent documentation constraints

For agents maintaining contribution policy. Product constraints live in
`docs/invariants.md`; architectural rationale lives in `docs/adr/`.

**`INV-011` — Preserve agent planning and execution records.** Repository plans,
task records, selectors, progress logs and historical snapshots remain under
`docs/agents/`. Task records own their recorded status; selectors identify work
when repository planning is used. Historical backlog does not authorize new work.
Removing these records requires explicit user authorization.

Reusable guidance and retained execution history share the agent directory.
Short-lived coordination may remain external. Human contracts do not depend on
agent records; technical invariants and ADRs retain their own authority. Git
history supplements preserved records rather than replacing them.
