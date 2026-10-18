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
