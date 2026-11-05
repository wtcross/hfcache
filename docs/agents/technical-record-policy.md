# Technical contract maintenance

For agents changing invariants, contracts and architecture decision records.
Review affected sections of `docs/invariants.md` and relevant records in
`docs/adr/README.md` before implementing. Update contracts, invariant register,
ADRs and index in the same coherent change. A documentation correction that
introduces no architectural choice needs no placeholder ADR.

Preserve technical identifiers. Explicitly retire, amend or supersede a changed
rule; never reuse or renumber its ID. New architectural choices get individual
ADRs. Continue the existing `decision-NNN.md` namespace using the next unused
number; a new `AD-nn` rule also receives its matching `ad-nn.md` record and
architecture section. No progress log or task record establishes authority.

An ADR identifies:

- Stable ID, title, original date and decision status.
- Context, selected approach, rationale and alternatives. Say when an original
  source documents no alternative rather than inventing one.
- Consequences, tradeoffs, compatibility requirements and limitations.
- Relevant contracts, source, tests, actual introducing/amending commits when
  known, and predecessor or replacement decisions.

When a decision evolves, retain useful original rationale and link the amendment
or superseding record in both directions. Cite code and tests directly; avoid
unexplained "this commit", mutable task references and implementation-stage
summaries. Record execution evidence externally, in agent records or in change
descriptions.

Preserve agent execution artifacts, snapshots and provenance manifests under
`docs/agents/`. Giving their durable requirements a current contract, test or ADR
home does not authorize deleting the original records. Removal requires explicit
user authorization. Age or length alone is not a reason to delete a document.
Preserve licensing and attribution; Git history supplements retained records.
