# Decision 106 — Current invariants and individual ADRs accompany implementation

| Field | Value |
| --- | --- |
| Status | Accepted; tracking authority amended by decision 107 |
| Date | 2026-10-17 |
| Work package | `DOC-009` |
| Provenance | This commit; [progress decision 106](../progress.md#decisions) |

## Context

The architectural requirements and their rationale already existed across
architecture sections, area contracts, 105 numbered progress decisions, code,
tests, and git history. There was no single register of current invariants or
individual decision files. The agent router supported progressive loading,
so adding another mandatory full-history read would work against its design.

## Decision

Maintain [the invariant register](../../invariants.md) and individual ADRs in this
directory. Preserve existing requirement IDs and the two legacy source
namespaces. Backfill every existing architecture and numbered progress decision
with original provenance, plus distinct framework, verification, and scheduling
choices. Index by topic and source ID so agents load only relevant records.

Every change or new plan being implemented reviews affected invariants and ADRs.
New invariants and architectural choices, amended constraints, and explicit
supersessions accompany implementation in the same work package. Contracts
remain the detailed specifications; progress remains the chronological tracker.

## Rationale and alternatives

A single growing decision document hides related reasoning across work
packages. Requiring the full ADR history in every session defeats progressive
loading. Renumbering existing IDs or replacing the progress log breaks source
and test citations. Reconstructing plausible reasoning without documentary or
git evidence invents provenance. The indexed register and standalone records
retain the audit trail while making current constraints and relevant reasons
available together.

## Consequences

Documentation review becomes an explicit completion step in
[the workflow](../workflow.md#the-loop-for-each-package),
[conventions](../conventions.md#documentation), and
[agent router](../../../AGENTS.md#context-map). New decisions receive a progress
number and matching record; older records retain their original reasoning and
link to amendments or replacements. Changes that affect no invariant or
architectural choice require review but no artificial documentation edit.

Backfill reconciles stale standing prose with existing decisions 20, 60, 61,
66, 96, 98, and 102. It changes no application behaviour, durable schema,
service setting, or authorization policy.

The audit also found that the declared lifetime-generation/audit-union rule
in `AD-05` / `FS-20` is stronger than the current allocator and returning-SHA
regression behavior. [AD-05](../../adr/ad-05.md) and the invariant register identify
that existing conformance gap, tracked as `RET-011`. Resolving it requires a
separate, explicit contract/code decision; this backfill does not silently
weaken the requirement or claim the implementation satisfies it.

## Evidence and related records

**2026-10-17 amendment (`DOC-010`).**
[Decision 107](decision-107.md) refines the tracker role: dated plans and task
files own active execution, selected by `docs/agents/plans/current.md`; progress
retains the chronological completed audit, Decisions, and Operator handoff.
Invariant/ADR review and upkeep remain required for every implementation.

- [ADR upkeep and required fields](../../adr/README.md#identity-and-authority).
- [Current invariants and their implementation/test evidence](../../invariants.md).
- [Plan layout amendment](../history/plan.md#7-project-layout).
- [Architecture companion register](../../architecture.md),
  [journal unknown-key contract](../../schemas.md#11-version-compatibility), and
  [security reconciliation](../../security.md#5-systemd-hardening-posture).
- [Original router choice](decision-081.md) and
  [workflow supersession](decision-082.md) establish the preserved loading
  and work-package model.
- The original record is progress decision 106 in this commit. Historical
  introducing and amending commits are cited in each backfilled record;
  this package does not claim to have originated those decisions.

## Authority-path amendment (2026-10-18)

[Decision 130](decision-130.md) explicitly permits the one-time record
relocation and replaces historical paths with the agent namespace. Original
identity, rationale and completed evidence remain; no host authorization is
renewed. Current technical authority resides in human contracts.
