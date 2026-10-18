# Decision 126 — Guard a local rollout without NAS writes or false acceptance

- Status: Accepted; host guard implemented and NAS-isolated repository gate
  passed by OPS-014 on 2026-10-18. Rootless rollout/release acceptance remains later work.
- Date: 2026-10-18.
- Work package: OPS-014, this commit.
- Source: [progress decision 126](../progress.md#decisions),
  [local rollout plan](../plans/2026-10-18-plan-local-rootless-rollout.md),
  [task](../plans/tasks/ops-014-local-rollout-guardrails.md).

## Context and decision

The completed REST/MCP plan authorized implementation without production changes.
Tyler now authorizes review, local release and rollout on this host, requires
Caddy and rootless Podman runtime, and absolutely forbids NAS content/metadata
writes and changes to other hosts. This is new scoped authority, not retroactive
permission or a claim that the earlier host holds passed.

Before any rollout mutation, root records local configuration/service/timer/
process/cgroup/mount/state metadata without secret values or NAS file I/O. Pause,
disable and block legacy writer activation; keep verification scheduling disabled
and sync stopped. Establish actual executor quiescence plus a noncreating local
archive-flock guard, retaining its ownership through the protected transition.
Unknown activity or unexplained lock/state refuses further work; do not kill,
unlink locks, clear pending evidence or stop the lifecycle target to force it.

Enforce a client-side read-only remount of the existing NFS mount without unmount
or disconnect, plus a persistent local mount-unit override. This changes only
this client's mount configuration, never NAS files, labels, ownership, exports,
snapshots or server policy. All subsequent runtime NAS binds must remain
read-only without recursive chown/relabel/copyup options. Local state, secrets,
images and logs stay on reviewed local storage. Root alone makes privileged
changes, records reversible local backups and never prints secret values.

The new local authorization permits necessary reviewed local configuration,
packages, account/user-manager setup, secret reuse/provisioning, review/landing,
installation and annotated tagging. It does not permit remote pushes or registry
publication, ACME issuance, NAS/other-host changes or installing trust elsewhere.
The rootless Caddy/API/worker/client architecture is a separate OPS-015 decision
and acceptance package; this record does not declare an implementation chosen
or the actual container boundary proved.

## Honest partial release acceptance

The ordinary release procedure requires live sync, full verification and a real
archive hardening workload. Those write reports/catalogs/probes even when no
published payload changes, so they are forbidden here. Do not execute them,
resume sync scheduling or relabel them as read-only/successful. Do not run
mutation-capable storage/Hub/NFS suites against production. Host-local disposable
fixtures and reviewed checks of actual rootless/proxy/credential/activation/
isolation boundaries may provide scoped evidence, not live storage acceptance.
Production reads also need review for the no-metadata-change constraint; client
read-only flags alone do not certify server access-time behavior.

Retain the deployed-artifact identity principle of decisions 75/79. A local
annotated tag may identify the artifact actually deployed only with explicit
partial acceptance, exact tested/deployed hashes and remaining NAS/full-domain/
other-host/calendar holds. No tag asserts forbidden checks passed; no remote
publication follows under this local-only authority. Version selection remains
REL-010 work, not a claim this plan already cut a release.

## Rationale and alternatives

Reject the normal supervised sync/full-verify acceptance because it contradicts
the new absolute constraint. Reject a green checklist obtained by quietly skipping
those steps. Stopping only clients/timers is also insufficient: surviving actual
executors or another writer path can still mutate NAS. The reviewed mount guard,
blocked legacy activation and container read-only binds provide independent local
barriers while preserving hardening and retained evidence.

No forceful cleanup or archive rewrite makes rollback safe. Preserve both
operation stores, scheduled handles, persistent locks and previous artifacts;
unknown history or unavailable old readers never proves nonexecution. Reject a
rootful/privileged or label-disable shortcut merely to make container startup pass.

## Consequences, relationships and evidence

Narrowly amends release acceptance in [65](decision-065.md),
[75](decision-075.md), [79](decision-079.md) and the actual-executor deployment
boundary in [121](decision-121.md); their identity, quiescence, retention and
historical evidence remain. Preserves INV-002/003/005–007/010–016, AD-16/17/21
and FS/TX semantics. No NAS, durable schema, domain algorithm or runtime dependency
change is authorized by this policy package.

[Environment](../agents/environment.md), [release](../agents/release.md),
[deployment](../deployment-centos-stream-10.md) and
[invariants](../invariants.md) define the current constraints. The task owns exact
host commands, snapshots, read-only guard proof and required gate. These are
planned controls until that evidence is recorded; there is no fabricated host
pass. OPS-015 owns actual rootless packaging/architecture and tests, later tasks
own release artifacts, local rollout and final partial-acceptance handoff.


## OPS-014 implementation evidence

The [task](../plans/tasks/ops-014-local-rollout-guardrails.md) records the actual
protected backup, original-inode flock, blocked legacy activation, persistent
client read-only remount, active target/Enforcing SELinux and post-gate recheck.
The corrected gate ran behind an empty read-only tmpfs covering NAS and exited 0
with 3,624 Python tests and 127 Cockpit tests/build. Preserve the initial launch
refusal and inherited-systemd-prefix failed run separately; no production/test
source or security policy was changed to make assertions pass. NAS/full-domain
write acceptance remains forbidden, not achieved. OPS-015 is next pending until
the guard package commits; no container architecture or release is claimed here.


## 2026-10-18 explicit rootless runtime amendment (OPS-015)

[Decision 127](decision-127.md) selects explicit rootless USER services and a
system-to-user target bridge, fixed immutable runtime/container-client commands,
non-killing drain and actual container peer/FD/secret/isolation proof. It replaces
the initial Quadlet proposal to avoid generated replacement/forced cleanup/timeouts.
Selected-profile Cockpit retains outer privilege/candidate guards but API secret
delivery moves to the fixed Podman client launcher, without host ImportCredential.
NAS/other-host restrictions, exact operation truth and previous evidence remain;
OPS-015 fixtures bind no NAS and perform no production switch or release.

## Permanent host boot guard (OPS-016, 2026-10-18)

Preserve the no-NAS-write restriction across application rollback with a fixed
root-protected host helper, /usr/local/libexec/hfcache-readonly-guard, and system
hfcache-readonly-guard.service. They are intentionally independent of current and
the immutable application image, not an alternate application runtime. The
standard-library helper imports no application code, accepts no arbitrary NAS
path/options and runs as hfcache UID/GID 981. It opens the existing original
local lock without creation, truncation or symlink following, verifies UID/GID
981, mode 0600, single link and descriptor/path inode agreement, and holds an
exclusive flock for its lifetime. READY is sent only after that ownership and
actual host NFS-read-only metadata are proved.

Use fixed /proc/1/mountinfo with the host PID/proc view, not a private guard
namespace's self mountinfo. ProtectSystem=strict may make a private view read-only
even while the host is writable; that must never manufacture host-guard proof.
Root's actual UID/GID-981 strict-sandbox probe distinguishes host rw root from
private ro root and proves the host source readable without NAS file I/O. Retain
strict hardening, private networking, AF_UNIX-only/empty capabilities and no
private PID/proc configuration that hides the host source. This is one mount/
inode check before READY plus lifetime lock ownership, not continuous monitoring.

Host boot policy enables this guard independently of the selected application.
A protected local bridge drop-in Requires/After the guard; the user default
target must not enable the application target. Only the system bridge starts it
after READY. Boot tmpfiles uses nontruncating f rules for original domain/API
locks and d 0700 for public/private runtime directories. Never unlink or replace
a live lock through RuntimeDirectory cleanup.

The bridge retains ProtectHome=yes, which also hides /run/user. A fixed protected
host drop-in exposes only /run/user/981/systemd/private at
/run/hfcache/user-manager/systemd/private and sets that bridge's XDG_RUNTIME_DIR
to /run/hfcache/user-manager. Root's actual hardened probe proves this narrow
manager connection; do not expose the service home or weaken hardening. Boot
tmpfiles protects both alias directories. Syntax review uses a disposable user
runtime directory, never the live manager socket: an actual verify invocation
with live XDG replaced that socket and required a quiescent manager restart.

Root transfers ownership from the old transient guard through the installer and
then this guard under continuous read-only NAS, writer masks and proven executor
quiescence. Selection holds the same original inode; an unknown holder/refusal
stops the transition. Start bridge/application only after the new guard is READY.
Preserve all stores/handles and record the exact handoff; no write-bearing NAS
acceptance or release claim follows from the permanent guard.

Enforcement: [fixed host helper](../../scripts/hold-readonly-guard.py),
[system unit](../../packaging/containers/hfcache-readonly-guard.service),
[nontruncating boot files](../../packaging/containers/hfcache-rootless.conf) and
[notify/flock/host-view/tmpfiles fixtures](../../tests/unit/test_readonly_guard.py).
Actual installed hashes, readiness/handoff and post-activation restrictions remain
OPS-016 task evidence; fixture passes alone are not deployment acceptance.

## Confined listener correction scope (OPS-017, 2026-10-18)

The continuing authorized local rollout includes [decision 128](decision-128.md)'s
worker-owned listener correction. OPS-017 changes source/contracts and uses local
fixtures only; it does not modify the installed 0.2.0 partial release or clear
its SELinux hold. Later clean build and guarded rollout tasks must prove actual
API-container peer access without policy/label/hardening bypass. Fixed host boot
guard, original lock, read-only NAS, writer masks and forbidden live workloads
remain. No NAS file I/O/jobs, other-host action or remote publication is granted.

## OPS-018 installed checkpoint (2026-10-18)

[OPS-018](../plans/tasks/ops-018-container-worker-rollout.md) deploys clean 0.2.1 UBI
artifacts and closes the connection hold with actual installed API-container
PROBE under Enforcing, repeated after non-killing drain/restart. Original host
policy/guard/lock, NAS-ro, masks and stores remain; no live NAS workload is run.
The preserved 0.2.0 failure returns on rollback and grants no cleanup authority.
