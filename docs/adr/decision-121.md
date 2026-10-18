# Decision 121 — Activate one server and retain scheduled observation without replay

- Status: Accepted; implemented by API-014 on 2026-10-18; installed host
  acceptance remains an operator deployment hold.
- Date: 2026-10-18.
- Work package: API-014, this commit.
- Source: [progress decision 121](../progress.md#decisions),
  [active plan](../plans/2026-10-17-plan-rest-api-and-mcp.md),
  [task](../plans/tasks/api-014-systemd-and-deployment-integration.md).

## Context and decision

Package Unix and optional TCP socket activation around one writer application/
lifespan and its existing instance/metadata/execution authority. Package a separate
private verification socket/service with offline startup, IP denial and no Hub/
API/MCP credentials. Keep both unprivileged under the hfcache account. Resolve
expected peer UID from that account or trusted explicit settings, never `%U`
from the system manager. Hide `/run/credentials` and trusted credential-source
stores from the worker; custom development source paths require explicit operator
sandbox restrictions and are not covered by a universal path-isolation claim.

Keep sync/verify service names, calendars, OnFailure hooks, disabled verification
timer and target/mount behavior. Scheduled services become AF_UNIX API clients
with their own API-only credential, distinct from daemon Hub credentials. Preserve
shared runtime lock inodes/lifetime across client/server/worker stops. A stopped
client never proves the writer/verifier stopped; drain/reconciliation must examine
the actual executor before upgrade, mount work or supervised recovery.

An ordinary CLI wait is finite. Scheduled oneshots must remain active through
multi-hour work so later timer ticks cannot create duplicates. Add a private
independent strict schema-1 pending observation handle for fixed `sync` or
`verify-full` only. It binds endpoint, explicit expected archive UUID and coarse
`rest-writer` namespace, generated nonsecret key and optional accepted operation
ID. Persist/fsync the key before the sole POST; persist acknowledged ID. Store
no bearer/digest, request body, policy fingerprint, result or executable queue.

Existing handles permit lookup/observation only, including a crash after key fsync
but before POST. Unknown/malformed/future/mismatched history remains preserved at
exit 20; missing remote history never proves nonexecution. Repeated finite
observation windows keep the oneshot active until the exact terminal Envelope/
exit is obtained. Only exact terminal evidence permits owned handle unlink and
directory fsync; token rotation within the same class can recover the binding.
This is observer continuity, never replay authority or another domain engine.
Local unsafe/malformed/future/mismatched handles widen existing HFAPI014 / exit
20; connection/lost-POST and remote missing/interrupted history keep existing
HFAPI019/020 and HFAPI013/015. No new error code is introduced. The entrypoint is
`python -m hfcache.scheduled_client --client-config PATH --state-directory PATH sync|verify-full`.
Use one API credential name `hfcache.api` for daemon/clients to preserve encrypted
credential-name binding, separate from daemon-only Hub `hf-token`.

Keep signal handling in the scheduled module's entrypoint only: SIGINT/SIGTERM ends
observation with HFAPI019 / exit 20 and retained recovery evidence, then restores
the old handlers. Library import/calls have no signal side effects. The release
guard requires quiescent actual executors and a noncreating flock held through
the switch. Retained scheduled handles refuse a target without observer support;
missing support never proves nonexecution.

## Rationale and alternatives

Socket activation retains one application instead of separate registries for
Unix/TCP. Actual verifier sandboxing must enclose hashing/report/catalog work;
hardening only its client would leave execution outside the offline boundary.
Reject privileged generic workers, network-enabled verification fallback, manager
UID assumptions and discarded locks during unit lifecycle changes.

Letting a scheduled client time out and POST again could duplicate accepted work;
unbounded individual HTTP reads would instead make interruption unsafe. A minimal
durable observation handle plus bounded windows preserves the original active
oneshot scheduling semantics without replaying unknown work. Missing history,
credential rotation and rollback must not silently reset the key.

## Consequences and relationships

Amends [systemd scheduling](systemd-scheduling.md),
[offline verification](offline-verification.md), [AD-17](ad-17.md),
[061](decision-061.md), [065](decision-065.md), [115](decision-115.md), [120](decision-120.md) and
[FW-01–04](fw-01.md). Preserves INV-003/006/010–015,
FS-18/19 and CP-05–08/13. The new private handle has its own version/compatibility
drill; archive and API receipt schemas stay unchanged. No new runtime dependency,
MCP, production operation or deployment is authorized.

Repository unit/installer/protocol/disposable upgrade tests do not prove installed
systemd activation, cgroup no-IP/no-credential enforcement, SELinux or NFS behavior.
Those remain explicit operator deployment holds. [Server](../server.md),
[schemas](../schemas.md), [deployment](../deployment-centos-stream-10.md),
[operations](../operations.md) and [recovery](../recovery.md) own the detailed
contracts; the task records actual acceptance and gate evidence.

Enforcement: [named activation/bootstrap](../../src/hfcache/server.py),
[worker startup](../../src/hfcache/verification_worker.py),
[scheduled observer](../../src/hfcache/scheduled_client.py),
[unit files](../../packaging/systemd/),
[installer](../../scripts/install-release.sh),
[quiescence/switch guard](../../scripts/release-functions.sh) and
[executor-aware probe](../../scripts/check-hardening.sh).
Evidence: [inherited-descriptor tests](../../tests/unit/test_server_activation.py),
[scheduled durability/recovery tests](../../tests/unit/test_scheduled_client.py),
[unit contracts](../../tests/unit/test_systemd_units.py),
[installer fixtures](../../tests/unit/test_release_installer.py) and
[probe contracts](../../tests/unit/test_hardening_probe.py). Installed enforcement
remains separate operator acceptance.
