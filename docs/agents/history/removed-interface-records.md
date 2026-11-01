# Removed interface records and historical provenance

WEB-027 removes superseded interface-only source and documentation from the
current repository under [decision161](../../adr/decision-161.md). Git at
`c692d7ae4b866fefd8a743a21afdb729da0f39c4` retains the complete pre-removal records,
original filenames, exact historical commands, original test identities and
original artifact hashes. This changes repository documentation only; installed
files, protected deployment evidence, service state and archives are untouched.

Retained plans, shared decisions, snapshots and acceptance records are current
sanitized projections. A historical execution summary is not a newly executed
command. Existing source/artifact hashes identify the original recorded proofs;
they are not hashes of rewritten prose or evidence JSON. Shared web authority,
confinement, original-operation and rollback evidence remains scoped as recorded.

The [host rollout record](../plans/support/host-rollout/acceptance-record.md)
retains relevant production deployment facts. Its original Git blob is
`d042efd7c7a544451d65c6ac989515be879c041a` at the commit above. Root-private
live evidence paths are not renamed by this documentation cleanup.

History manifests retain original Git hashes and separately bind each sanitized
snapshot with its current snapshot hash. Dedicated removed snapshots are omitted.
The documentation inventory now inventories retained current documents; complete
pre-removal inventory and removed historical provenance remain in Git above.
