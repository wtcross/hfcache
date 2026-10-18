# Create the rootless verifier listener inside its confinement

- Decision identity: 128.

- Status: Accepted; current profile is qualified by the recorded deployment scope.
- Date: 2026-10-18.


## Context, decision and rationale

A user-manager-created socket could carry an SELinux label the confined API
container could not connect to. Create the rootless private listener inside the
worker's own confinement, without broadening SELinux policy, adding a host execution
fallback or changing native activation. Keep native exact named-FD3 and rootless
explicit --container-listener modes separate, with no implicit fallback.

Direct Python PID1 audits inherited descriptors above stderr, LISTEN fields and
known credential environment before NSS/shared resources. Reserve internal FD3,
acquire worker instance ownership, prove lexical archive/socket disjointness and
a bounded known-local mount from fixed mountinfo before parent traversal. No NAS
realpath/stat or arbitrary IPC location is granted. Pin an effective-user/group-owned
0700 no-follow parent, refuse every existing pathname, bind via its proc-fd address,
and prove the exact created 0600 socket inode and trusted bound spelling.

Retain parent/instance/socket ownership through setup, active work, joined shutdown
and exact-inode cleanup. Existing, replaced or crash-stale names remain evidence;
no automatic unlink/replay. Install signal handling before resource acquisition;
setup interruption cannot falsely emit readiness. Rootless Type=notify,
NotifyAccess=all and --sdnotify=container forward READY only after listener/store/
worker initialization. API Requires/After worker.service; its directory view stays
read-only while only the worker's private-directory bind becomes writable.

Keep the indexed/bound .socket dormant RefuseManualStart=yes with no automatic
target/API references, preserving all nine bindings. A host peer probe or podman
exec companion alone cannot establish confined PID1/actual API-container connectivity.
Recorded installed 0.2.1 proves that peer path under Enforcing before/after drain;
NAS workloads and rollback0.2.0's limitation remain separate.

## Relationships and technical evidence

- [115](decision-115.md)
- [121](decision-121.md)
- [126](decision-126.md)
- [127](decision-127.md)
- [offline verification](offline-verification.md)
- [Podman 6.0.2 --sdnotify](https://docs.podman.io/en/v6.0.2/markdown/podman-run.1.html#sdnotifycontainer-conmon-healthy-ignore)
- [systemd 257 service readiness](https://www.freedesktop.org/software/systemd/man/257/systemd.service.html#Type=)
- [owned-listener helpers](../../src/hfcache/verification_listener.py)
- [explicit bootstrap modes](../../src/hfcache/verification_worker.py)
- [private runtime validation](../../src/hfcache/verification_executor.py)
- [rootless launcher](../../scripts/container-service.py)
- [retained-container proof harness](../../scripts/check-container-worker.py)
- [listener/kernel/cleanup tests](../../tests/unit/test_verification_listener.py)
- [native bootstrap tests](../../tests/unit/test_verification_worker_bootstrap.py)
- [unit readiness](../../tests/unit/test_systemd_units.py)
- [proof/readiness refusal tests](../../tests/unit/test_container_runtime.py)
- [Decision 129](decision-129.md)

See [deployment status](../deployment-status.md) for recorded scope and remaining acceptance.
