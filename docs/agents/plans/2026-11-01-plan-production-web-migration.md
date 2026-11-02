# Migrate the local deployment without archive loss

| Field | Value |
| --- | --- |
| Status | active |
| Created | 2026-11-01 |
| Authorization | User requests replacing this host's deployment with the completed version, including web UI, REST API, MCP and removal of the installed Cockpit plugin; preserve sync configuration and NFS data. |
| Tracker | `docs/agents/plans/current.md` |

## Outcome and scope

Prepare a fresh immutable full-web release and replace the existing rootless
installation. Preserve the actual archive configuration byte-for-byte, including
all model/dataset selections, archive identity and Hub policy. Preserve both
operation stores, original handles, private predecessors/outcomes, credentials,
configuration lock and retained releases. Back up protected local state before
host changes. Remove only the reviewed public plugin entrypoint after preserving
its original identity and rollback material.

Keep the host NFS mount read-only, writers masked, calendars disabled and SELinux
enforcing. No NAS writes, initialization, payload migration, sync, retention,
repair, relabel/chown, archive test workload, reboot or remote publication is
authorized. Build/test with the production archive shadowed. Establish actual
executor drain and original noncreating local-lock custody before selection;
unknown execution blocks effects. The current host guard/dependency drift must
be reconciled before selection, with preserved before/after evidence. Do not
infer current state from historical records.

The browser administrator is separately provisioned through hidden terminal
input. Existing bearer credentials remain separate. The optional new privileged
host helper is a distinct reviewed opt-in; no legacy permission is automatically
migrated or expanded. Web/API/MCP deployment alone does not release storage or
calendar holds.

## Contracts and decisions

Review `docs/agents/environment.md`, `release.md`, `workflow.md`, the selected
rootless profile in `docs/containers.md`, `docs/deployment-centos-stream-10.md`,
`docs/web-ui/deployment.md`, `docs/web-ui/migration-and-rollback.md`, and
configuration/security invariants INV-001–003, FS-19, FS-21–23. Existing decisions
121, 124, 126–129, 140, 146–147, 150, 153–154, 158–159 and 161 govern the scope.
No new architectural or durable archive-format change is intended.

## Tasks

| Order | Work package and task file | Depends on |
| --- | --- | --- |
| 1 | [REL-016 — prepare clean release source](tasks/rel-016-web-release-source.md) | None |
| 2 | [OPS-024 — guarded local migration](tasks/ops-024-production-web-migration.md) | REL-016 |

Agents may perform independent read-only inventory, contract review and build
preparation within these task boundaries. Only the primary agent coordinates
host mutations and selection.

OPS-024's local backup and read-only/isolated preparation may proceed in parallel
with REL-016's gate. Its release construction, staging and selection depend on
the completed REL-016 source commit. Do not edit tracked inputs during a gate.

## Acceptance and validation

Strict `scripts/check.sh --require-web --with-build` passes for release inputs.
Clean captured backend/UI artifacts and authenticated final images match a new
immutable version. Verify protected backup, target-compatible configuration,
actual drain, guard/lock continuity, service identity readability, trusted TLS,
web bootstrap/assets/authentication, REST and MCP, original operation observation,
effective confinement and byte-for-byte preservation. Retain predecessor and
target-compatible rollback configuration. Record local tag only after actual
acceptance; record all remaining workload holds honestly. Required gate also
passes for the final evidence commit.

## Lifecycle and amendments

- 2026-11-01: Activated by the user's replacement instruction. Actual host is
  NFS read-only; source still declares installed version 0.2.2, so a fresh
  release identity is required. Read-only inventory found inactive independent
  guard and missing bridge readiness dependency; no host change has occurred.
