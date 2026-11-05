# Select rootless archive writes through independent protected authority

- Decision identity: 165.
- Status: Source implementation; installed and actual NFS conformance pending.
- Date: 2026-11-03.
- Introducing change: `60d086931dc03d8582751c6a3c9b17eeb6f93715` (accepted design); source implementation amendment below.

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


## Source implementation and qualification (2026-11-03)

The [installer](../../scripts/install-container-release.py),
[launcher](../../scripts/container-service.py),
[protected preparer](../../scripts/prepare-host-helper.py),
[host authority](../../src/hfcache/host_policy.py),
[peer review](../../src/hfcache/host_peer.py) and
[SELinux source](../../packaging/selinux/hfcache-host-helper.cil) implement the
finite mode/sibling identity joins. Helper `release.release_id` binds the exact
physical sibling while `profile_evidence.archive_mode` independently binds mode.
Legacy runtime/manifest readers remain strict, and new metadata inspection does
not require a new function in an old launcher. Protected staging now retains
fresh original-lock/NFS-ro/executor/helper/cgroup/libpod proof before effects,
matching the accepted selection window; local rendering remains manager-free.

Fixed rootless and native installer entrypoints run the selected application's
real config/store validator offline after independent drain and original flock.
Existing-only store opens cannot create missing original lock inodes. Rootless
preparation exposes neither archive, original archive lock, sockets, network nor
credentials: a new isolated local runtime parent supplies only the new companion.
Non-replacing publication preserves its inode, followed by exact independently
provisioned label/owner/mode verification. Normal role binds preserve that label.
Native preparation uses its fixed selected venv and offline system-manager
sandbox. It reuses the verifier's effective custom masks and canonical grammar,
with optional standard masks and real server-model source coverage; exact
packaged/cached native API command/credential delivery and no API drop-ins exclude
unmodelled sources. Unsupported native roots/store layouts refuse. A bound exact
config/unit/mask/account revision is checked before effects and again before
non-replacing companion publication; a private runtime bind hides original
archive/API/worker runtime sources. No bytecode or inherited stdin is supplied; fixed offline HF_HOME/Xet paths use
that private runtime and the legacy service token cache is masked.
Partial/prior authority is preserved, never repaired automatically.

Native credential delivery is measured from the fixed API service's two typed
system-bus `a(ss)` arrays, using `busctl` from the already required systemd
package. Human `systemctl show` output can render these arrays as
`[unprintable]` and cannot establish their contents. Require no unencrypted
loads and exactly the canonical encrypted writer-name/path pair; malformed,
unsupported or additional entries refuse. Preserve the canonical executable,
API no-dropin, imported Hub-credential and source-mask checks, and bind the
measured arrays into the same before/after revision. This changes metadata
inspection only and adds no package, credential source or grant.

The writer derives the actual target's stable stock container attributes,
including network/image/MCS and required proc exception markers, excluding
compiler-generated private attributes. Its new explicit archive symlink rule
contains only getattr/read/create/unlink for the canonical `.store/hub` cache;
ordinary publication trees remain symlink-free. The explicit rule does not bound
broader inherited stock NFS policy at independently administered boolean values.
No generic container grant, capability, helper/observer payload permission or
boolean is added. API/worker fixed role mounts/masks/network/seccomp remain the
worker's narrower secret-free/offline boundary; the common type alone is not.
Schema2 startup proves exact immutable selector/index/rendering, host NFS mode
and nosuid/nodev/noexec, Enforcing state and fresh known guard/original-lock facts.
Writer review additionally binds real payload PID/start/cgroup/command/domain.

Owned schema2 sibling/identity/mount/guard/lock/refusal fixtures and goldens cover
source behavior. Exact 0.3.1 c23abba parser execution preserves legacy schema1
and refuses both schema2 modes with explicitly modeled protected metadata. The
owned target-policy binary compiles using the exact copied host configuration;
28 bounded allow-vector checks use freshly observed active booleans, including
helper/observer payload denials, unchanged generic archive rights, existing role
prerequisites and writer kernel-core/message rights no greater than stock.
Actual kernel policy, original policy store/root and Enforcing state remain
unchanged. This is neither an installed policy change nor workload acceptance.

Strict expansion remains explicitly unqualified: the retained baseline fails33
clauses, and the initial candidate fails40 (five new writer history/guard
constraints matching inherited map/search patterns plus two proc-marker conflicts
subsequently addressed through stock markers). All failures and assertions stay
preserved. Existing `virt_use_nfs=true` already gives stock containers broader NFS
rights; `domain_can_mmap_files=false` is part of the measured snapshot, not a
permanent proof. No strict-neverallow pass or sole-systemwide-writer claim is made.
Actual owned Enforcing role/mount/MCS/secret/network and recovery/rollback drills
remain with the installed acceptance task; actual production nfs_t transactional
writes and current-boot transition/pilots remain later. No unattended boot claim
is added. Source gate and retained proof identities accompany the implementation commit
evidence.


### Observed rootless mount view (2026-11-04)

The actual owned writer worker reached READY under the dedicated writer domain,
with a requested rw archive bind, while its archive VFS mount remained ro.
Host aliases and the shared NFS superblock were rw. The authenticated existing
pause namespace retained the inherited ro VFS view; this failed acceptance and
is preserved, not counted as writer success. No archive job ran.

The manual transition therefore requires actual keeper and payload mount proof,
and, when stale, a reviewed drained namespace handoff. The
[procedure](../deployment-centos-stream-10.md#rootless-namespace-handoff) retains
all original locks/state/history and before/after engine configuration evidence.
The supported engine's known-inert pause retirement is separate from graceful
workload drain; it cannot terminate an unknown executor. Old actor snapshots are
retained and superseded by authenticated new namespace evidence. No capability,
SELinux, seccomp or mount-sandbox bypass, new durable epoch, automatic retry or
job replay follows. Owned turnover and positive writer qualification remain
pending; production is unchanged. The existing decision's independently protected
mode, original-lock and actual NFS acceptance requirements remain in force.

### Confined proxy connection (2026-11-05)

The owned writer startup retained separate private MCS labels for ordinary
`container_t` Caddy and the `hfcache_archive_writer_t` API. Its first TLS
bootstrap GET returned 502; the actual policy lacked their directed Unix stream
connection permission. Add only `container_t` to `hfcache_archive_writer_t`
`unix_stream_socket connectto`. This narrowly amends the earlier no-generic-
container-grant statement for IPC; generic container archive rights remain
unchanged. No reverse connection or cross-type socket I/O permission is added.

Linux checks the client socket against the listening socket for `connectto`;
I/O and options use each process's own socket rights. The accepted server socket
retains the server type with the client MLS range, without changing either
process label ([Linux 6.12 SELinux hooks](https://github.com/torvalds/linux/blob/v6.12/security/selinux/hooks.c)).
The grant is type-wide, not a Caddy or pathname MAC selector. Fixed runtime
mounts, DAC, namespaces and API authentication retain the deployed upstream
boundary. Keep independent MCS categories and constraints, archive exclusion,
helper/observer payload neverallows and all role hardening unchanged. Actual
Enforcing proxy/API acceptance remains separate from policy source tests.
