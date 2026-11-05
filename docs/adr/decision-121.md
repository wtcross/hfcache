# Activate one server and retain scheduled observation without replay

- Decision identity: 121.

## Context, decision and rationale

Native services adopt the exact configured Unix/optional TCP API listener set
into one application/lifespan, and a separate strict named-FD3 private worker.
Activation metadata, peer/account identity and descriptor/socket/address proof are
all-or-nothing; malformed activation never falls back to binding. Keep persistent
original runtime locks through service stops. Native systemd credentials separate
API/observer REST authority from API-only Hub and optional MCP sources; worker
sources/stores are masked and no credentials imported.

Selected rootless services instead use fixed file-mounted Podman sources, a
worker-created listener and notify readiness before API start; its indexed socket
artifact remains dormant. Same-named system/user services are not interchangeable.
Neither profile permits a host/credential/network fallback.

Fixed native scheduled sync/verify-full observers fsync an original key before
the sole POST, then retain a strict private handle through finite observation
windows. Existing handles permit observation only, using original-key lookup or a
known exact operation ID. Only matching exact terminal evidence
permits owned unlink/fsync; missing/malformed/future state stays uncertain. Preserve
both operation stores/handles through rollback and reject incompatible targets.
Pause timers without stopping the archive target. Drain API while worker handoff
remains available, then worker; a stopped observer is never executor termination.

## Relationships and technical evidence

- [decision 122](decision-122.md)
- [decision 123](decision-123.md)
- [systemd scheduling](systemd-scheduling.md)
- [offline verification](offline-verification.md)
- [AD-17](ad-17.md)
- [061](decision-061.md)
- [065](decision-065.md)
- [115](decision-115.md)
- [120](decision-120.md)
- [FW-01–04](fw-01.md)
- [Server](../server.md)
- [schemas](../schemas.md)
- [deployment](../deployment-centos-stream-10.md)
- [operations](../operations.md)
- [recovery](../recovery.md)
- [named activation/bootstrap](../../src/hfcache/server.py)
- [worker startup](../../src/hfcache/verification_worker.py)
- [scheduled observer](../../src/hfcache/scheduled_client.py)
- [unit files](../../packaging/systemd)
- [installer](../../scripts/install-release.sh)
- [quiescence/switch guard](../../scripts/release-functions.sh)
- [executor-aware probe](../../scripts/check-hardening.sh)
- [inherited-descriptor tests](../../tests/unit/test_server_activation.py)
- [scheduled durability/recovery tests](../../tests/unit/test_scheduled_client.py)
- [unit contracts](../../tests/unit/test_systemd_units.py)
- [installer fixtures](../../tests/unit/test_release_installer.py)
- [probe contracts](../../tests/unit/test_hardening_probe.py)
- [Decision 126](decision-126.md)
- [Decision 127](decision-127.md)
- [Decision 128](decision-128.md)
- [Decision 132](decision-132.md)
- [Decision 148](decision-148.md)

Recorded installed scope and remaining acceptance are described in
[deployment status](../deployment-status.md).

## 2026-10-26: Cooperative scheduled-observer interruption

Raising KeyboardInterrupt from a signal handler immediately after the HTTP
transport acquires a lock can leave shutdown blocked re-acquiring it. Latching
the stop request avoids asynchronous exceptions inside transport critical sections.

The entrypoint instead latches SIGINT/SIGTERM and classifies interruption at owned
safe request/observation and persistence checkpoints, before a fresh submission
or terminal pending-file removal. Poll/retry waits remain stop-aware; current
HTTP exchanges retain their existing finite budgets. Restore prior handlers,
retain exact original handles and never replay or cancel accepted work. The
ordinary imported client has no signal side effects or new default behavior.
This adds no executor, thread framework, lock, runtime dependency, wire format or
host permission. The [client contract](../api-client.md) states the observable
behavior; [real signal and ownership regressions](../../tests/unit/test_scheduled_client.py)
cover the interruption and original-handle boundaries.

## Fixed host-effect amendment (2026-10-27)

[Decision156](decision-156.md) adds a bounded fixed-route host-action lane,
original-process observer stop, independent durable outcomes and finite diagnostic
reads. It preserves archive serialization, original operation identity and this
record's unrelated requirements. Implementation and actual installed conformance
are separately required.

## Masked native inactivity conformance (2026-11-03)

An actual native switch refuses an intentionally masked, inactive legacy
timer because the quiescence guard recognizes only loaded and absent units.
Accept masked units only in the inactive state; apply the existing zero-process,
task and cgroup checks to masked services as well. Keep the original noncreating
flock and every other drain check. Unmasking legacy writers or calendars to make
the installer pass would violate their deliberate disabled state. This corrects
the implementation's recognition of an explained inactive unit; it adds no
startup, scheduling, execution or rollback authority. Source regression and the
actual installed switch remain distinct evidence.
