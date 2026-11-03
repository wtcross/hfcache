# Run reviewed rootless containers without forced executor cleanup

- Decision identity: 127.

- Status: Amended; current profile is qualified by the recorded deployment scope.
- Replacement design: see the 2026-10-20 amendment below; executable conformance remains pending.
- Date: 2026-10-18.

## 2026-10-21 protected-reader amendment

[Decision150](decision-150.md) adds an explicit opt-in API-only read-only helper
parent projection from independently verified host launcher facts. Other roles
receive neither mount nor attestation; no generic volume/engine selector, default
grant or runtime-schema widening follows. Original nine rootless stage/execution
bindings, keep-id confinement, actual drain and historical acceptance stand.

## Context, decision and rationale

Use the service account’s USER systemd manager for a fixed rootless
Caddy/API/private-worker/client role set with protected
runtime metadata and immutable image IDs. Actual host UID/GID match the helper
caller; keep-id maps them to container 981:981. API/Caddy use pasta; worker/client
use network none, with worker socket creation restricted to native AF_UNIX under
a baseline-preserving derived seccomp profile. Read-only roots, cap-drop ALL and
NoNewPrivileges remain; no privileged, rootful, host-network/PID, control-socket,
label-disable or generic executable/engine escape is available.

API alone receives Hub plus distinct REST/MCP file-mounted secrets; Caddy TLS only,
client REST writer only, worker none. Secret files use container981/mode0400.
Worker/client mask standard host credential stores; custom locations require explicit
review. Archive binds are read-only without relabel/chown/copyup; local graphroot,
state/cache/temp and actual payload memory.high (4GiB app roles/512MiB Caddy) bound
writable/cgroup authority. Read-only policy-directory mounts permit atomic reload.

A reviewed system-to-user target bridge connects host orchestration to that
manager; the user default target must not start the application. Rootful system
units would change the authority boundary. Quadlet-generated replacement, short
stop timeouts and forced cleanup were rejected because they can destroy executor
accounting before real work drains.

Persistent roles never auto-pull, replace, add init or auto-remove. Infinite
non-killing drain and systemd stop allowance join real payloads; unknown labels,
image/PID/state/cgroup refuses start/removal. Finite stateless clients alone may
use --rm, without canceling server work or discarding handles. Appended permissive
seccomp rules and Network=none alone do not prove socket denial: remove socket/
socketcall from all baseline allows, allow native AF_UNIX only and preserve every
other restriction/architecture mapping. Incomplete or unrelated errors are not proof.

Protected release/index/rendered policy and nine root-owned helper/system/user-unit
bindings select one physical tree. Recompute rendering/hash/index under the original
noncreating flock, atomically select and fsync, reload both managers and inspect
effective units/drop-ins. A selector change with unrelated running images/profile
is invalid. Independent host guard and original stores/locks survive rollback.
Worker-created listener/notify replaces rootless host-created activation; the socket
artifact stays indexed/dormant and native activation remains separate. Explicit
UBI-only image inputs govern current builds. Actual installed scope is narrower
than general NAS/isolation/other-host acceptance.

## Relationships and technical evidence

See [deployment status](../deployment-status.md) for recorded scope and remaining acceptance.

## Replacement UI design amendment (2026-10-20)

[Decision 141](decision-141.md) amends this record for the accepted
replacement design. Accepted future narrow host helper preserves unprivileged API and protected rootless bindings. Unproved rootless schedule/observer permissions remain denied; no manager/control-socket fallback is accepted.

## Original-intent and writer amendment (2026-11-03)

Accepted design in [decision 165](decision-165.md); implementation and installed conformance remain
pending. A closed runtime schema-2 archive mode, immutable rendering/index and independently protected helper binding select fixed API/worker writer mounts and dedicated confined writer process domains. Schema 1 remains guarded-readonly; other roles, stores, images, account mappings and isolation remain unchanged.
See the [executable recovery contract](../job-recovery.md). Original rationale
and unrelated requirements above remain in force.
