> Historical technical reference preserved before consolidation. Current authority is the living contract.

# Decision 128 — Create the rootless verifier listener inside its confinement

- Status: Accepted; implemented by OPS-017, with clean UBI artifacts in REL-013
  and actual installed API-container peer/notify/drain acceptance in OPS-018.
  Hold 22 closes for 0.2.1;0.2.0 failure remains historical and returns on rollback.
  Live NAS verification/storage acceptance remains unrun.
- Date: 2026-10-18.
- Work package: OPS-017, this commit.
- Source: [progress decision 128](../../../../progress.md#decisions),
  [listener plan](../../../../plans/2026-10-18-plan-container-worker-listener.md),
  [task](../../../../plans/tasks/ops-017-container-worker-listener.md).

## Context and decision

The actual 0.2.0 rollout proves local Caddy/API metadata readiness and worker
isolation, but SELinux refuses API container_t connectto to the private socket
created by the unconfined user manager. A successful host-origin VerificationClient
probe does not prove that container connection. Keep the failure and partial
release history. Correct socket ownership at creation instead of adding an allow,
changing container labels, disabling labelling or executing verification on the
host. No SELinux policy, seccomp, credential or domain authority is widened.

Add explicit `--container-listener` to the private verification entrypoint. It
is PID1-only and creates the AF_UNIX listener in the already confined worker
process, giving the kernel socket the ordinary process context. Native named
inherited-FD3 activation remains the default, strict separate mode: it never
falls back to binding and retains its canonical listener checks.

Before NSS/shared imports, policy/state access or opening bootstrap resources,
owned mode rejects every inherited descriptor above stderr, every LISTEN_*
activation field and the existing forbidden credential environment sources.
Offline initialization still precedes shared Hub/runtime imports. Descriptors
opened after this audit by the bootstrap are owned resources, not inherited
authority; distinguish them without relaxing the initial audit.
Reserve the owned unbound AF_UNIX socket as FD3 immediately after this audit,
before NSS/shared imports can claim that descriptor. Bind it only later under
instance/parent ownership; this reservation grants no pathname cleanup authority.
In owned mode, install SIGTERM/SIGINT handlers immediately after the cold
inheritance audit and before FD3 reservation/NSS/imports. Carry one stop Event
through initialization and runtime so a stop during initialization cannot be
forgotten and later reported READY. Native handler placement stays unchanged.

## Listener ownership and shutdown

Hold the existing worker instance lock before creating the listener and through
joined shutdown and socket cleanup. Pin the private parent by no-follow directory
opens; require its final directory to be effective-UID/GID-owned mode 0700.
Before parent traversal or bind, refuse lexical overlap between the socket path
and configured archive root in either direction. Check bounded fixed
/proc/self/mountinfo and require a recognized local filesystem for the socket
parent; unknown/network filesystem evidence refuses without realpath, NAS stat
or directory access. New IPC creation must not gain NAS authority through a bad
trusted startup path. Native inherited-listener behavior is unchanged.
Refuse and preserve any pre-existing final pathname, including a stale socket,
symlink or regular file. Never infer permission to remove it from a stopped PID.

Bind through the pinned parent's /proc/self/fd address with restrictive umask,
set exact socket mode 0600 and retain the created pathname device/inode. Owned
mode validates that exact trusted bound spelling plus the pinned-parent socket
path's owner/mode/inode. A proc-fd spelling must not bypass validation; native
mode's configured canonical getsockname check stays unchanged. Normalize this
owned listener to internal FD3 without a shell, supervisor or init process.

Stop accepting, join active VerificationWorker work and close the listener before
removing only the exact socket inode created by this invocation. Retain parent
and instance lock until that comparison/cleanup is complete. Preserve a changed
pathname, store, instance lock and shared archive lock. A crash may leave a stale
socket; startup refuses it pending explained operator handling. This creates no
automatic stale cleanup, result replay or resume authority.

## Container and readiness boundary

Only the worker's private socket-directory bind becomes writable; the API's view
remains read-only. Keep Network=none, native AF_UNIX-only seccomp, no secrets,
credential-store masks, read-only root, empty capabilities, NoNewPrivileges,
UID mapping, memory limits, separate stores and the original shared flock inode.
No `+` execution prefix, privileged/host-PID/network/control socket or label
override is part of this design.

The rootless target starts worker.service. API Requires+After worker.service;
worker.service no longer Requires or takes Sockets from the host .socket unit.
Keep the rootless .socket artifact/binding dormant with RefuseManualStart=yes
and no target/API/service automatic reference, preserving nine-binding and index
shapes. Native socket/service packaging is unchanged.

Use worker Type=notify, NotifyAccess=all and Podman's `--sdnotify=container`.
The direct worker sends standard-library AF_UNIX READY=1 only after secure
listener ownership, instance lock, operation store and VerificationWorker
initialization succeed, before serving. Prove the proxy under actual confinement;
sleep, conmon-start notification and Type=exec ordering are not readiness proof.
Owned mode requires a valid NOTIFY_SOCKET and skips READY if shutdown was already
requested; native activation ignores that notification mechanism.
Preserve infinite non-killing drain and API-before-worker stop ordering. Fresh
verification admission still probes the private peer; readiness does not bypass
that check or exact surviving-worker reconciliation.

## Consequences and alternatives

Amends the rootless portions of [115](../../../../../adr/decision-115.md), [121](../../../../../adr/decision-121.md),
[126](../../../../../adr/decision-126.md), [127](../../../../../adr/decision-127.md) and
[offline verification](../../../../../adr/offline-verification.md). It preserves native inherited
activation, strict private frames/peer UID, exact operation/result identities,
no replay, command lock/preflight and complete report/catalog persistence.
No dependency or durable config/receipt/observer format change is intended.
Application metadata 0.2.1 identifies the correction; clean artifacts follow its
committed source in REL-013, with actual rollout in OPS-018 and release in REL-014.

The installed 0.2.0 hold remains until actual new production API-container-to-
worker-container PROBE succeeds under Enforcing SELinux. Source/helper tests or
host-origin probes cannot close it. Rollback to 0.2.0 deliberately restores its
known connection hold, while fixed host guard, NAS-ro, writer masks and retained
stores/handles/lock inodes remain. No NAS file I/O, jobs, writes, remote publication
or other-host changes are authorized. Full NAS verification acceptance remains
NOT RUN even after a private non-executing PROBE passes.

The supported interface is documented in
[Podman 6.0.2 --sdnotify](https://docs.podman.io/en/v6.0.2/markdown/podman-run.1.html#sdnotifycontainer-conmon-healthy-ignore)
(container mode proxies the notification socket, while conmon mode reports
process start) and [systemd 257 service readiness](https://www.freedesktop.org/software/systemd/man/257/systemd.service.html#Type=).
These primary references justify the interface choice, not actual confinement,
message attribution or installed readiness; those require the dependent proofs.

Implementation: [owned-listener helpers](../../../../../../src/hfcache/verification_listener.py),
[explicit bootstrap modes](../../../../../../src/hfcache/verification_worker.py),
[private runtime validation](../../../../../../src/hfcache/verification_executor.py),
[rootless launcher](../../../../../../scripts/container-service.py) and
[retained-container proof harness](../../../../../../scripts/check-container-worker.py).
Evidence: [listener/kernel/cleanup tests](../../../../../../tests/unit/test_verification_listener.py),
[native bootstrap tests](../../../../../../tests/unit/test_verification_worker_bootstrap.py),
[unit readiness](../../../../../../tests/unit/test_systemd_units.py) and
[proof/readiness refusal tests](../../../../../../tests/unit/test_container_runtime.py).
OPS-017 records 162 focused app and 197 runtime/unit/installer cases, actual
explicitly dirty preview container-origin PROBE/notify/isolation/drain and the
full --with-build exit 0 (3,912 Python tests, 135 Cockpit tests and four wheel
smokes). Clean release-artifact and installed acceptance belong to dependent
tasks; the actual dirty preview is not a deployed release or closure of hold 22.

## UBI source prerequisite (OPS-019, 2026-10-18)

[Decision 129](../../../../../adr/decision-129.md) changes only the planned service foundation to
UBI 10 micro, including all FROM stages, with pinned interpreter/binary/CA inputs.
This decision's listener/readiness/confinement/native compatibility rules remain.
The initial Debian REL-013 candidate proof is genuine but superseded; REL-013
must rebuild/repeat acceptance after committed OPS-019 before any OPS-018 switch.
