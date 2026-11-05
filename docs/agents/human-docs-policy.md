# Documentation audiences

For agents editing documentation or public help. Every retained human document
has a primary reader and a useful task or reference purpose. Start with the
reader's outcome and prerequisites, then link to deeper reference and rationale.
Keep examples coherent and trace behavior to source and tests.

Human documentation includes every documentation file outside `docs/agents/`,
except `AGENTS.md` and its `CLAUDE.md` symlink. Public CLI help has the same
boundary: no task identifiers, agent tracking paths, execution chronology,
handoffs or task-owned availability claims. Technical IDs, ADR status, schema
versions, transaction checkpoints, runtime progress and `hfcache plan` remain
valid product concepts.

The agent directory is the home for agent instructions and retained planning
and execution history. Preserve its implementation plans, task records,
selectors, progress logs, inventories, reviews and historical snapshots.
Human-document cleanup does not authorize removing those records. Short-lived
coordination may stay in the external execution system. Human guides must remain
understandable without depending on agent records.

README orients readers and links to task guides; it has no Status section or
replacement deployment ledger. Release notes describe user-visible changes and
compatibility, without selected-host state or rollout instructions. Reusable
deployment procedures state prerequisites and verification, never old permission
as standing authority. Preserve licensing, attribution, safety and compatibility
when consolidating content. Git retains original execution history.

`scripts/check-docs.py` discovers documentation and checks links, audience
boundaries and the helper catalog offline. It has no count quota or transitional
tracking exemptions. Semantic review must also catch misleading examples,
stale availability claims and unexplained terminology.
