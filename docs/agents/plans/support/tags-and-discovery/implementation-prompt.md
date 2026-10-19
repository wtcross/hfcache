# Implementation instruction

Use the following instruction after extracting the bundle into the checkout:

```text
Implement docs/agents/plans/2026-10-19-plan-tags-and-discovery.md.

This instruction authorizes activating that draft plan and implementing its
scoped code, tests, contracts, documentation and agent records. Work on
feat/tags-and-discovery, never main. Read AGENTS.md and follow the current
repository workflow. Reconcile the actual checkout, current plan selector,
working tree and any changes since the reviewed baseline before proceeding.
Do not reset unrelated work or silently replace another active plan.

Use tags as the only operator-managed organizational field. Do not add
categories, groups, curated use_cases, expected_variants, an independent tagging
store for current configuration, or remote configuration installation. Keep
technical format/quantization/availability metadata separate from tags.

Read the linked design and validation matrix as needed. Execute the linked
CAT work packages in dependency order, completing REST and its API-backed CLI
before adding the read-only MCP tools. Make one incremental commit per completed
work package, using the repository's <ID>: <summary> convention. Each commit must
include its tests, human documentation/contract changes, invariant and ADR review,
task evidence, progress entry and appropriate plan/current selector updates.
Run scripts/check.sh for every package; do not record a skipped or failed
required check as passing. Cockpit work requires an actually executed frontend
gate. Record genuine blockers and continue only with other authorized ready work.

Use offline temporary fixtures. No production deployment, live Hub/NFS workloads,
archive initialization, service/timer/hardening changes, credential access,
push, merge, release tag, or registry publication is authorized. Do not inherit
those permissions from historical work. Leave the implementation committed on
the feature branch, with a precise completion summary and operator handoff.
```

## Resumption

After interruption, inspect git and the active selector before selecting work.
Preserve uncommitted changes and completed evidence. Continue the task that is
actually in progress; do not reconstruct progress from this original prompt or
from delivery-time hashes. Update task status and the current selector together.
A substantive change outside the authorized product boundary needs a scope
amendment; necessary implementation decomposition inside that boundary does not
require another approval. Allocate new work-package IDs for any split package,
checking for collisions, and preserve every completed task's identity.
