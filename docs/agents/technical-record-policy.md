# Technical contract maintenance

## Maintenance rules

For every change or new plan being implemented:

1. Review the affected invariant sections and relevant ADRs before implementing.
   Record this review in the work-package evidence. When no invariant or
   architectural choice changes, do not create a placeholder ADR.
2. Add every new invariant to `docs/invariants.md` in the same work package;
   update changed constraints and detailed contracts together. Preserve IDs,
   and explicitly record any retirement, replacement, or narrow exception.
3. Record each new architectural choice in the numbered progress Decisions
   log and in `decision-NNN.md`, using the same number, padded to at least
   three digits. Add it to the human ADR index and relevant topic row, or the agent ADR
   index for a purely process decision. A new
   `AD-nn` architectural rule also receives its corresponding `ad-nn.md` and
   architecture section, with links between the rule and its progress record.
4. Amend an existing ADR's status and amendment links when the choice evolves.
   Retain its original context, decision, rationale, and evidence. A replacement
   decision gets a new record; link both directions and identify whether it
   supersedes the whole record or just one policy. Never reuse an identifier.
5. Keep contracts, invariants, ADRs, index, plan amendments where needed, and
   the task/plan/current records and completed `docs/agents/progress.md` evidence
   together in the implementation commit. Run the repository
   gate and verify local documentation links and record coverage before
   committing, as required by [the workflow](workflow.md).

Each new record must identify:

- **Identity and status:** stable source ID, title, original decision date,
  work package, and `Proposed`, `Accepted`, `Amended`, or `Superseded` status
  (qualified historical status is appropriate for backfilled records).
- **Context and decision:** the problem or constraint and the selected approach.
- **Rationale and alternatives:** why it was selected and what was rejected.
  If the historical source does not document an alternative, say so.
- **Consequences:** resulting behaviour, tradeoffs, compatibility, and limits.
- **Evidence and relationships:** source contract/plan/progress links, relevant
  implementation and tests, introducing/amending commits, and any predecessor
  or replacement. A new uncommitted decision cites its work package and
  "this commit"; do not invent a hash before the commit exists.

The human ADR index retains the legacy AD/decision namespaces and named records.
Do not create a third sequence for new decisions; use the progress number.

