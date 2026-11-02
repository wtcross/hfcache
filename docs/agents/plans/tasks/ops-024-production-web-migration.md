# OPS-024: Migrate the guarded local deployment and remove its obsolete plugin

| Field | Value |
| --- | --- |
| Status | in_progress |
| Plan | [Production web migration](../2026-11-01-plan-production-web-migration.md) |
| Depends on | [REL-016](rel-016-web-release-source.md) for build/stage/selection; independent preflight/backup may run in parallel |

## Scope and acceptance

Build clean full-web artifacts, final rootless image and immutable staged release.
Capture verified root-private coordinated backup and actual config inventory.
Provision the user's hidden-prompt administrator hash separately. Preserve all
configured repositories and protected authority exactly. Reconcile guard drift
after actual executor drain, retain original local locks and restore independent
readiness gating before guarded selection. Deploy web UI, REST and MCP through
the existing HTTPS endpoint. Preserve then remove only the installed public
Cockpit plugin entrypoint, retaining old release and local rollback evidence.

No archive mutation, workload, timer enablement, forced termination, unknown state
cleanup, permission expansion, security weakening or remote publication occurs.
Unknown execution/identity blocks the switch. Optional privileged host-helper
activation is separately reviewed and never inferred from legacy grants.

## Contracts, invariants, and ADRs

The parent plan lists current contracts, invariant IDs and applicable decisions.
Record current-state review and any required contract change in this package.

## Validation

Planned: protected backup/hash and original inode comparison, clean artifacts and
actual final image foundation, actual drain/cgroups/lock custody, NFS-ro and masks,
installed TLS/UI/authentication/REST/MCP/private worker/confinement, original
operation observation and final strict gate. Tag only the accepted deployment.

## Execution notes and handoff

Initial actual configuration has 165 enabled model entries and zero dataset
entries; preserve the complete actual bytes and any private retired candidates.
The independent guard is inactive and bridge readiness dependency is absent,
although the NFS mount remains ro. Historical guard evidence is stale and cannot
authorize assuming readiness. No host mutation has occurred.

## Completion evidence

Pending.
