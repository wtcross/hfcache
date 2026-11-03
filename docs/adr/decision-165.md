# Select rootless archive writes through independent protected authority

- Decision identity: 165.
- Status: Accepted design; executable and installed conformance pending.
- Date: 2026-11-03.
- Introducing change: this commit.

## Context and decision

The guarded rootless runtime deliberately binds the archive read-only. Manual
Sync and technical refresh require actual NFS writes, fresh archive permission,
original-lock ownership and Enforcing policy. A browser toggle, mount selector or
permission flag alone must not turn that default deployment into a writer.

Add one closed protected runtime mode, `guarded-readonly` or `manual-writer`.
Missing mode in existing schema-1 runtime preserves guarded-readonly; writer
runtime uses independent schema 2 with required mode. Bind the exact mode in
the immutable release manifest/index, recomputed rendering and independent
helper deployment index. Startup compares all of these and actual role mounts.
Writer requires the archive grant independently; a selected mode grants nothing.
No environment, executable, mount/path or browser override selects writes.

Stage two immutable siblings, with manifest schema 2 `release_id` exactly
`<version>-<archive_mode>`: for example `0.3.2-guarded-readonly` and
`0.3.2-manual-writer`. Package/UI version stays `0.3.2`; source, app image and UI
bytes match, while each rendered runtime/artifact index is separately bound.
`/opt/hfcache/current` selects `releases/<release_id>`, and helper
`selector_target` plus physical-root/index checks bind that exact identity.
Schema-1 releases retain version-only directory names. Installation first runs
the guarded sibling; the later write transition drains and selects its already
staged writer sibling while NFS remains read-only. Never rewrite a selected
runtime/manifest or collide two modes under one version directory. Rollback
selects the compatible guarded sibling with its own matching helper bindings.

API and private worker alone receive the configured archive bind read/write in
manual-writer, preserving the existing complete Sync/refresh and verifier report/
catalog/preflight path contracts. The worker's offline/secret-free boundary,
service-owned original archive flock and separate stores remain unchanged.
Caddy/client receive no archive; helper/inspector retain metadata-only authority
and payload neverallows. Default API/worker binds remain read-only.

Use a dedicated explicit writer SELinux process type derived from the reviewed
container confinement, with only required archive NFS directory/file operations;
do not add writes to generic `container_t`. Prove the actual `nfs_t` production
mount and exact writer domains under Enforcing, without relabel/chown/copyup,
label-disable, privileged containers or an assumed distribution boolean. Existing
`hfcache_archive_t` owned fixtures remain separate from actual NFS proof. Preserve
helper/observer archive and secret neverallows against the new writer domain.
Unknown labels, policy, mount/profile or guard evidence refuse startup/effects.

## Transition and rollback

The installer's drained selection window remains NFS-read-only in both modes.
Before selection, stop admission; keep worker/helper available for outcome drain;
then prove actual API/worker/helper/inspector and libpod/cgroup quiescence and
hold the original noncreating archive flock. Preserve both stores, dispositions,
outcomes, handles, candidates, secret identities, old artifacts and original lock
inodes in a coordinated protected backup/inventory. Provision matching helper
bootstrap/index/policy/SELinux receipt before helper READY and API startup.

Writer activation is a separate authorized root operation: retain the original
flock, adjust only the protected local persistent mount override and bridge/guard
dependency selection, remount the existing NFS connection read/write, prove exact
host/export/sentinel/ownership/capacity/reserve and application preflight, then
release the handoff to actual application executors. An intentionally inactive
guard stays inactive outside the handoff. No guard process may hold the original
flock in running writer mode; bridge ordering must not silently start it there.
The independent guard unit remains available and unchanged in purpose.

Acceptance is current-boot manual startup: root provisions existing runtime
parents and fixed lock labels after recreation, verifies matching protected
mode/mount/guard facts, starts helper to READY, then bridge/worker/API/Caddy and
checks actual roles. Missing provisioning/order fails closed; no unattended-boot
claim or reboot test follows. Timers remain disabled and legacy writers masked;
rootless schedule/observer/control grants remain denied.

Rollback stops admission, drains real execution and detached helper cohorts,
reacquires the same original flock, restores NFS-read-only and reviewed local
mount/bridge/guard policy, and selects a retained compatible mode/reader. Preserve
all new state. A predecessor unable to enforce dispositions never regains
admission. No automatic rollback after unknown effects, archive restoration or
undo of normal Sync retention is promised.

## Rationale, consequences and evidence

An independent finite mode plus a dedicated writer domain makes the added
authority reviewable without widening other containers or teaching the installer
to operate on writable NFS. Making all rootless deployments writable, enabling
timers, changing NAS exports, weakening confinement or treating a local synthetic
archive as production qualification were rejected. The complete existing worker
archive bind avoids redesigning verification storage/preflight in this change.
No new runtime dependency, scheduler or generic mount framework is introduced.

Amends the prior read-only-only deployment choice in [126](decision-126.md),
[127](decision-127.md), [141](decision-141.md), [150](decision-150.md),
[159](decision-159.md) and [162](decision-162.md); original lock, mapped identity,
closed account homes, lifecycle, helper isolation and guarded selection survive.
See [containers](../containers.md#protected-manual-writer-profile),
[security](../security.md#protected-manual-writer-authority),
[deployment](../deployment-centos-stream-10.md#manual-writer-transition),
[recovery](../job-recovery.md) and [invariants](../invariants.md).
Source tests, owned enforcing installed fixtures, exact predecessor-format drills
and later separately authorized actual NFS pilots must establish conformance.
