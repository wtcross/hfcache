# Decision 130 — Human contracts and agent records have separate homes

| Field | Value |
| --- | --- |
| Status | Accepted |
| Date | 2026-10-18 |
| Work package | DOC-011 |
| Amends | [82](decision-082.md), [106](decision-106.md), [107](decision-107.md) |
| Provenance | User implementation instruction; this commit |

## Context and decision

The user requires all human documentation to explain current product behavior,
without implementation tracking. Preserve the implementation audit under
`docs/agents/`; keep technical contracts and architectural rationale human-facing.
The planning guide explicitly permits a single collision-checked migration before
moving any record. The sole selector is now `docs/agents/plans/current.md`.

Move the five pure process ADRs (80, 81, 82, 106, 107) and INV-011, retaining
their identities and rationale. Other ADRs remain technical even when their
original provenance needs editorial cleanup. Original hashes and git baseline
in the migration manifest preserve verifiable provenance. Stable paths apply
again after this one-time exception.

## Rationale and alternatives

Keeping parallel selectors risks conflicting execution authority. Human redirect
pages into agent records would retain the unwanted audience dependency. Deleting
history loses evidence. Rehome still-normative historical requirements into living
contracts before archiving the plan; repair source/test authority references too.
The old cross-dataset fallback remains a separately approved design alternative,
not a claim that current FS-04 permits cross-device promotion.

## Consequences and evidence

No application behavior, dependency, durable format or technical invariant changes.
Single-writer, immutable publication, no replay, exact MCP allowlist and host
restrictions remain. Historical rollout authorization is evidence only. The human
status page retains operational restrictions without execution transcripts.

See [migration manifest](../migration-manifest.json),
[normative coverage map](../historical-contract-map.md),
[human-document policy](../human-docs-policy.md), and
[DOC-011 evidence](../plans/tasks/doc-011-human-docs-authority-and-record-migration.md).
