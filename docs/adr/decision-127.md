# Run reviewed rootless containers without forced executor cleanup

- Decision identity: 127.

- Status: Accepted; current profile is qualified by the recorded deployment scope.
- Date: 2026-10-18.


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

- [Decision 126](decision-126.md)
- [decision 111](decision-111.md)
- [121](decision-121.md)
- [122](decision-122.md)
- [115](decision-115.md)
- [120](decision-120.md)
- [123](decision-123.md)
- [124](decision-124.md)
- [server](../server.md)
- [security](../security.md)
- [Cockpit](../cockpit.md)
- [deployment](../deployment-centos-stream-10.md)
- [invariants](../invariants.md)
- [Podman run](https://docs.podman.io/en/latest/markdown/podman-run.1.html)
- [rootless/systemd distinctions](https://docs.podman.io/en/latest/markdown/podman-systemd.unit.5.html)
- [Caddy Unix upstreams](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy)
- [TLS automation/trust](https://caddyserver.com/docs/automatic-https)
- [image recipe](../../packaging/containers/Containerfile)
- [build/authenticated input evidence](../../scripts/build-container.py)
- [fixed runtime helper](../../scripts/container-service.py)
- [client launcher](../../scripts/hfcache-client)
- [rendered unit templates](../../packaging/containers)
- [actual worker probe](../../scripts/check-container-worker.py)
- [boundary unit tests](../../tests/unit/test_container_service.py)
- [build/probe tests](../../tests/unit/test_container_runtime.py)
- [decision 126's permanent guard](decision-126.md#context-decision-and-rationale)
- [Decision 128](decision-128.md)
- [Decision 129](decision-129.md)

See [deployment status](../deployment-status.md) for recorded scope and remaining acceptance.
