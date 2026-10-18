# Guard a local rollout without NAS writes or false acceptance

- Decision identity: 126.

- Status: Accepted; current profile is qualified by the recorded deployment scope.
- Date: 2026-10-18.


## Context, decision and rationale

A local rollout can establish listener/client behavior without authorizing NAS
writes. Keep a root-owned independent read-only guard outside application selection,
the original shared lock inode, read-only host/archive binds, writer masks,
disabled verification calendar, separate receipt stores and pending handles. A
version bump or successful endpoint is not acceptance of archive workloads.

The guard holds a noncreating original flock, validates ownership/inode and host
PID1 NFS-ro mount view before READY, and retains ownership until reviewed stop.
Its own private read-only namespace would be insufficient evidence; it is not
continuous monitoring. Nontruncating boot files preserve locks. Root-only holder
handoff must remain quiescent and guarded; application startup waits readiness.
The bridge reaches only the protected service-user manager socket without weakening
ProtectHome. Never start the application from the user default target.

Native package tools cannot manage the selected rootless profile. Stage/authenticate
immutable artifacts, inspect actual system/user fragments/drop-ins and libpod tasks,
then retain the original lock through a guarded switch. Unknown process/accounting
state refuses. Client/wrapper exit is not executor death; API drain keeps verifier
handoff available before worker drain. Forced cleanup, arbitrary SELinux allow or
label changes and pretending partial acceptance is full acceptance were rejected.

Recorded 0.2.1 closes its prior 0.2.0 API-container peer connection limitation.
NAS/domain/consumer/other-host/browser/calendar acceptance remains separate; rollback
to 0.2.0 retains its narrower limitation. No release selection lifts the guard. Under a no-metadata-write restriction,
even production reads require review: client-side read-only mounts do not certify
NAS access-time behavior.

## Relationships and technical evidence

- [65](decision-065.md)
- [75](decision-075.md)
- [79](decision-079.md)
- [121](decision-121.md)
- [deployment](../deployment-centos-stream-10.md)
- [invariants](../invariants.md)
- [Decision 127](decision-127.md)
- [fixed host helper](../../scripts/hold-readonly-guard.py)
- [system unit](../../packaging/containers/hfcache-readonly-guard.service)
- [nontruncating boot files](../../packaging/containers/hfcache-rootless.conf)
- [notify/flock/host-view/tmpfiles fixtures](../../tests/unit/test_readonly_guard.py)
- [decision 128](decision-128.md)

See [deployment status](../deployment-status.md) for recorded scope and remaining acceptance.
