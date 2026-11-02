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
No durable archive-format change is intended. The discovered fixed account-home
compatibility correction adds decision 162 and narrowly widens the protected
host deployment index, preserving the existing runtime and archive schemas.

## Tasks

| Order | Work package and task file | Depends on |
| --- | --- | --- |
| 1 | [REL-016 — prepare clean release source](tasks/rel-016-web-release-source.md) | None |
| 2 | [OPS-025 — preserved rootless account home](tasks/ops-025-preserved-rootless-account-home.md) | REL-016 |
| 3 | [OPS-024 — guarded local migration](tasks/ops-024-production-web-migration.md) | REL-016, OPS-025 |

Agents may perform independent read-only inventory, contract review and build
preparation within these task boundaries. Only the primary agent coordinates
host mutations and selection.

OPS-024's local backup and read-only/isolated preparation may proceed in parallel
with source validation. Its release construction, staging and selection depend
on the completed REL-016 and OPS-025 source commits. Do not edit tracked inputs
during a gate.

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
- 2026-11-01: REL-016 completes as `bcfd7d3`. Independent actual-host evidence
  establishes the guard was deliberately disabled under the user's October 22
  instruction. Preserve that setting by default after temporary guarded switch;
  no permanent guard restoration is inferred. Verified protected backup and
  byte/inode continuity pass. Activate necessary OPS-025 before immutable
  construction: the helper's previous fixed home does not match the preserved
  production account/store. Its independently reviewed bounded correction avoids
  moving or replacing persistent state. All NAS/workload/calendar holds remain.
- 2026-11-01: OPS-025 passes focused, actual old/current host-index parser and
  strict full web/build gates; source construction is ready after this commit.
  Current selects OPS-024 for immutable build and actual migration. Its enabled
  web startup still requires the user's protected administrator hash. No
  production selection, archive mutation, tag or publication has occurred.
