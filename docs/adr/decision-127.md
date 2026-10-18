# Decision 127 — Run reviewed rootless containers without forced executor cleanup

- Status: Accepted and implemented in OPS-015 on 2026-10-18, with actual local
  container/selection and corrected full-build gate evidence. Production manager/
  target and NAS-workload acceptance remain separate holds.
- Date: 2026-10-18.
- Work package: OPS-015, this commit.
- Source: [progress decision 127](../agents/progress.md#decisions),
  [local rollout plan](../agents/plans/2026-10-18-plan-local-rootless-rollout.md),
  [task](../agents/plans/tasks/ops-015-rootless-container-runtime.md).

## Context and decision

Tyler requires Caddy and rootless Podman for Caddy/API/private-worker/runtime
clients, with hfcache.target starting Caddy and API, reuse of appropriate existing
secrets and no NAS or other-host changes. [Decision 126](decision-126.md) first
established read-only NAS and blocked-writer guardrails. Preserve those barriers
through implementation, local-only disposable proof and later rollout.

Use explicit **rootless USER systemd services**, not a root-owned container daemon
or a system Quadlet with User=. A reviewed system-manager bridge connects the
existing system hfcache.target to a user-manager hfcache.target. The user target
starts Caddy, one API application and the private worker socket under service
UID/GID 981 with deliberate keep-id mapping. System and user managers remain
separate authorities; an identically spelled unit is not the other manager's
unit. Preserve the existing archive target/mount and blocked legacy writers.

Prefer explicit fixed `podman run --pull=never` argv over the initial Quadlet
proposal. Persistent Caddy/API/worker containers do not use --replace, --init,
--rm, automatic image updates or unreviewed runtime pulls. Refuse an unknown existing/running container instead of replacing,
attaching to or deleting it. Stop accepted work through the application's normal
drain using an explicit non-killing `podman stop --time -1` and systemd
TimeoutStopSec=infinity. No generated/default 10-second kill, KillMode fallback
or forceful ExecStopPost removal may erase an executor whose outcome is unknown.
Remove a container non-forcibly only after actual stopped state is established;
failed/ambiguous cleanup preserves evidence. If stop state is unknown or a stop
command fails, retain blocked deactivation/infinite waiting rather than return
control to a systemd fallback kill. Release guards inspect owned libpod cgroups
and containers as well as user-unit PIDs; an inactive bridge alone proves nothing.
Reconcile exact surviving worker
receipts before classifying interrupted work as in decision 115.

## Images, identity and activation

Build the application image from an immutable platform-specific Python 3.14.6
slim-trixie manifest, exact built wheel and locked hashed server+MCP dependency
closure. uv is build-only; runtime performs no dependency resolution. Pin Caddy's
actual upstream platform digest and derived runtime image ID as well. The upstream
binary's cap_net_bind_service file capability is unnecessary for 8443 and conflicts
with cap-drop ALL/NoNewPrivileges; strip it in the derivative image and verify no
file capability remains instead of weakening runtime hardening. Source/wheel/closure/base/final-image identities
must be recorded; version strings/tags alone are not artifact identity. The local
runtime installer validates a protected immutable release manifest and reviewed
current selector before use, preserves previous artifacts/state and applies
actual executor/read-only/drain guards. Exact manifest fields and tests belong
to this package's settled source, not an invented generic command runner.

API and private worker mount the same existing local archive-flock inode and
separate local operation stores; do not create per-container lock copies. Mount
policy **directories** read-only so atomic installed policy/candidate replacement
is visible to fresh admissions. Keep public API and private worker socket
directories separate and preserve the exact absolute peer-checked worker socket
pathname across namespaces. No worker socket is exposed through Caddy.

The private worker starts the actual Python entrypoint as PID 1 with its named
inherited FD 3 and matching LISTEN_PID/FDS/FDNAMES. Preserve the supported Podman
FD mechanism without an init wrapper; clear inappropriate inherited PIDFD identity
before the worker's strict activation check. Account/namespace mappings must make
SO_PEERCRED identify the expected API UID. Container capability claims require
real inherited-FD/peer/result/drain tests, not reuse of bare-host process evidence.

Podman does not implicitly propagate the systemd invocation environment. Forward
only a canonical non-secret 32-lowercase-hex INVOCATION_ID to API/worker when the
launcher has one; do not forward arbitrary ambient variables. This preserves
executing-process invocation metadata and classified log framing. It grants no
authority and does not prove timer or submitting-client origin; see
[decision 111](decision-111.md).

## Network, TLS, secrets and filesystem isolation

Caddy terminates verified TLS on local port 8443 with the existing appropriate
protected certificate/key, proxies to the API Unix socket, and has no ACME
issuance, admin listener, arbitrary file server or raw-header/bearer logging.
Do not disable certificate verification for clients. Preserve Host/Origin/public
prefix/proxy rules and exact native Unix evidence; forwarded headers alone never
grant native authority. Proxy retries must not replay command admission.

The API may use rootless pasta networking for its legitimate future online Hub
work, but all actual NAS binds remain read-only. The private worker uses a
separate Network=none namespace, retains the default runtime seccomp restrictions
and narrows native socket creation to AF_UNIX only. It gets
no API/MCP/Hub secret, host credential store/home or host PID/network namespace.
Offline flags supplement actual OS isolation; they do not prove no-IP themselves.
Do not weaken SELinux, use label-disable/privileged/host-socket shortcuts or widen
namespace/credential access to make a probe pass.

Use protected Podman-mounted secrets, UID 981/mode 0400, only in their intended
containers. Existing Hub source goes only to API; distinct REST/MCP sources stay
separate; Caddy receives only TLS material. Runtime clients get only the API
credential. No bearer goes into image layers, environment, argv, browser, logs,
manifest/hash inputs or the private worker. Do not mount the Podman control socket
inside application containers. Keep graphroot, images, Caddy state, stores/cache
and all writable paths local. NAS binds are read-only without :U, :z/:Z,
chown/relabel/copyup or any NAS file I/O during OPS-015 disposable proofs.

## Clients, Cockpit and protected installation

A narrow observer-only exception permits --rm for a finite API-only client
container. It mounts no host operation/scheduled state and can neither cancel
server execution nor discard its durable receipt. Validated handles remain in
caller output. This exception never applies to persistent Caddy/API/worker
containers, unknown work or release cleanup.

Keep CLI wire/Envelope/retained-handle and exact candidate/base/flock contracts.
Replace only the inner Cockpit CLI executable with a fixed allowlisted rootless
container-client launcher. Retain the outer privileged systemd-run boundary,
API-only credential delivery to the container, candidate lock/byte guards and
bounded output. Remove obsolete host ImportCredential: the fixed Podman launcher
owns API secret delivery, so the host transient unit needs no bearer source. Do not
add generic executable/Podman argv or a browser token surface. Existing system-bus
legacy controls remain blocked during this rollout; user-manager services are not
silently substituted into system-bus calls. The bridge must safely refuse an
unavailable/mismatched installed runtime rather than use a bare-host fallback.
The fixed inner executable is /usr/local/libexec/hfcache-client, with explicit
client configuration and /run/hfcache/api/api.sock; the helper source is
scripts/hfcache-client. Runtime lifecycle helper scripts/container-service.py is
exposed as /usr/local/libexec/hfcache-container-service through the selected
immutable release, never a disconnected static copy. The helper resolves its
physical release root once and reads rendered/runtime.json there with a no-follow
final-file open. That profile validates fixed immutable image IDs and reviewed
paths/options; it is not an arbitrary Podman/executable dispatcher.
Its independent integer schema 1 has exactly service_uid/service_gid (positive
host IDs) and app_image/caddy_image (exact sha256 image IDs). The non-secret
profile is staged root-owned 0644. Require root ownership, no group/other writes,
single-link regular bounded 16 KiB data, duplicate-free JSON, a no-follow descriptor
and stable metadata excluding read-induced access time. Caller UID/GID and XDG_RUNTIME_DIR
must match. Role paths, container IDs and secret names are fixed in the helper,
not profile-supplied executable/options. The release artifact manifest is separate.
Worker/client additionally mask /run/credentials, /etc/credstore,
/etc/credstore.encrypted and /etc/hfcache/credentials with empty inaccessible
read-only mounts; mounting policy directories read-only does not itself hide
credential sources. Limit actual payload/libpod cgroup memory, not only the host
launcher: 4 GiB high watermark for API/worker/client and 512 MiB for Caddy.

The two fixed libexec entrypoints, system hfcache.target/bridge and five user
units under /etc/systemd/user must be exact root-owned symlinks through
/opt/hfcache/current to indexed release artifacts. Before switch, the installer
refuses missing, copied, drifted or differently targeted bindings; it never
overwrites unknown paths. OPS-016 provisions these once under quiescence and
reloads both managers after each selection before activation. A switch/rollback
must change actual helper/profile/image selection together, not only a marker.
Before activation, OPS-016 must also inspect the managers' actual FragmentPath
and effective drop-ins after reload, refusing home/runtime overrides or drift.
Static link checks alone do not prove future manager selection.

After the base policy-directory bind, overlay the same physical release's
rendered directory read-only at /etc/hfcache/containers and its client.toml at
/etc/hfcache/client.toml. Host mountpoints are root-owned real placeholders.
Caddy configuration and worker seccomp sources also pin that physical tree, so
one invocation cannot mix releases while the current link changes. Mutable
installed archive policy still uses its read-only directory bind for hot reload;
no static runtime profile/config copy bypasses selection. The system bridge
requires srv-hfcache.mount, while the system target only Wants the bridge: a
bounded mount failure refuses runtime startup without making that target a boot
requirement. No mount probe opens an archive file.

The new rootless installer is a separate explicit profile; the historical native
installer/profile is retained without silently changing its behavior. Root alone
may prepare necessary local account/home/subordinate IDs/linger and actual local
rootless proof infrastructure. OPS-015 tests use owned local fixtures, no NAS bind
and no production switch. REL-010 selects the version and release artifacts;
OPS-016 owns production profile enablement. Live NAS/full-domain acceptance stays
forbidden and explicitly partial under decision 126.

## Rationale and relationships

Quadlet's generated replacement/short-stop/forced-cleanup behavior would require
fragile overrides for the central unknown-executor safety property. Explicit user
units make argv, inherited descriptors and non-killing lifecycle reviewable.
Reject rootful Podman, a generic privileged dispatcher, an init wrapper that breaks
activation, secret-bearing images or copied locks. Containers change deployment,
not domain algorithms, whole-archive authority or durable operation truth.

Amends deployment/activation details in [121](decision-121.md),
Cockpit client execution in [122](decision-122.md), and local rollout policy in
[126](decision-126.md), preserving decisions [115](decision-115.md),
[120](decision-120.md), [123](decision-123.md) and [124](decision-124.md).
Preserve INV-002/003/005/006/010–016, AD-16/17/21, FS/TX and CP-01–14 boundaries.
No new Python runtime dependency, archive schema, job authority or release version
is selected by this architecture. Host checks and NAS acceptance remain distinct.

Contracts: [server](../server.md), [security](../security.md),
[Cockpit](../cockpit.md), [deployment](../deployment-centos-stream-10.md),
[release](../agents/release.md) and [invariants](../invariants.md).
The task links settled implementation, successful local rendered-unit/container
proof, preserved failed/partial attempts and the required full --with-build result.
Actual production manager/target and NAS-workload acceptance are separate holds.

Official primary interfaces reviewed:
[Podman run](https://docs.podman.io/en/latest/markdown/podman-run.1.html),
[rootless/systemd distinctions](https://docs.podman.io/en/latest/markdown/podman-systemd.unit.5.html),
[Caddy Unix upstreams](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy)
and [TLS automation/trust](https://caddyserver.com/docs/automatic-https).
Installed Podman 6.0.2 interfaces and actual generated command behavior must be
verified by implementation; current upstream docs are not that host proof.


Enforcement: [image recipe](../../packaging/containers/Containerfile),
[build/authenticated input evidence](../../scripts/build-container.py),
[fixed runtime helper](../../scripts/container-service.py),
[client launcher](../../scripts/hfcache-client),
[rendered unit templates](../../packaging/containers),
[actual worker probe](../../scripts/check-container-worker.py),
[boundary unit tests](../../tests/unit/test_container_service.py) and
[build/probe tests](../../tests/unit/test_container_runtime.py). These links
identify implemented enforcement; the task distinguishes hermetic passes,
retained failed/partial actual attempts, successful local container proofs and
the corrected --with-build gate from pending production acceptance.


## Seccomp implementation correction from actual proof

An appended ERRNO rule did not override the base policy's unconditional socket
ALLOW: the actual container still permitted IPv4. Do not claim that approach
establishes isolation. Derivation now removes socket/socketcall from every base
ALLOW, requires proven unconditional native socket permission, then allows native
socket only for AF_UNIX/domain 1. Other defaults/deny rules remain; no AF_NETLINK
permission is introduced. Reject an unrecognized base rather than weaken it.
The task records the decisive actual negative control and corrected real-container
rerun separately from the failed original policy.
All engine exchanges explicitly select --remote=false; inherited remote connection
settings cannot redirect lifecycle/build/probe work to another host. Runtime
API/worker guard reads only /proc/self/mountinfo and refuses unless the actual
archive mount is NFS and read-only, before any archive access.


Actual policy loading also requires a recognized native-only architecture map,
matching the prior SystemCallArchitectures=native restriction; compatibility ABI
mappings must not introduce socketcall aliases/conflicts. This tightens supported
architectures rather than adding syscall permission. Preserve original/default
and derived policy hashes and all other baseline restrictions; unknown policy
shape refuses. Corrected actual load/isolation evidence remains task-owned.


A selector rename followed by directory-fsync failure refuses with exit 20 but may
leave new current in place. Preserve both release trees and require inspection
before retry; no automatic rollback/cleanup or assertion that refusal means no
change. This acknowledgement boundary is covered by actual temporary-file tests,
not a production switch.


The corrected native policy preserves defaultErrnoRet (measured ENOSYS 38 in actual
PID1 control); valid denial may be EPERM/EACCES/ENOSYS. Proof must reject successful
IP socket creation rather than assume a single refusal errno. The task retains
all failed/partial attempts and fresh actual acceptance separately from hermetic
policy/build/installer passes.

## Host boot policy refinement (OPS-016, 2026-10-18)

The application images/helper artifacts stay at clean source 481fcc4. A fixed
root-owned host readonly guard and local bridge Requires/After drop-in implement
[decision 126's permanent guard](decision-126.md#permanent-host-boot-guard-ops-016-2026-10-18)
outside current so an application rollback cannot remove the NAS-write barrier.
This standard-library host control imports no app code. Its Type=notify system
service runs UID/GID 981, proves the original noncreating flock and host NFS-ro
mount view before READY, then holds the descriptor until reviewed stop. The
fixed /proc/1/mountinfo source avoids a strict sandbox's fabricated private-ro
view; it is not continuous mount/inode monitoring.

Do not enable the app target from the user default target: only the system
bridge starts it after guard readiness. Nontruncating boot tmpfiles preserves
domain/API lock inodes and creates protected runtime directories. Root alone
performs the quiescent old-guard→installer→permanent-guard handoff with NAS-ro and
writer masks maintained; bridge/application activation follows READY. Both-
manager reload/effective-fragment/drop-in checks remain mandatory. These host
policy files are distinct from unchanged selected release artifacts and need
their own actual source/hash/unit/handoff evidence, without a new application
schema, dependency or architectural authority.

ProtectHome=yes also hides the user manager's /run/user socket. Keep that
hardening and bind only its fixed private socket to the protected
/run/hfcache/user-manager/systemd/private alias, with bridge-only XDG_RUNTIME_DIR
pointing to /run/hfcache/user-manager. This host drop-in is separate from the
selected immutable bridge unit. Require actual effective-drop-in and connection
proof; run syntax checks with a disposable XDG runtime, not the live socket.

Actual OPS-016 acceptance is partial: Caddy/API/CLI, local isolation and drain
pass, but SELinux refuses the API container_t connection to the user-manager's
unconfined_t worker socket. A successful host UID-981 peer probe and earlier
host-origin VerificationClient fixtures do not prove that container connection.
Keep this release hold and review a label-at-creation/container-activation design
under a future authorized task; do not add an allow, change container labels or
bypass the isolated executor to force a pass. The existing data-preserving plan
permits honest partial rollout, not end-to-end verification acceptance.

## Worker-owned listener amendment (OPS-017, 2026-10-18)

[Decision 128](decision-128.md) supersedes rootless host-created socket activation
for the planned 0.2.1 profile. The direct confined PID1 worker binds its protected
private pathname after strict inheritance audit, retains instance/parent/socket
identity through joined cleanup and sends container-proxied READY only after
listener/store/runtime initialization. Only its private directory becomes writable;
API mounts it read-only. API Requires+After worker.service; the target starts that
service and the indexed .socket stays dormant RefuseManualStart=yes without any
automatic reference. Nine bindings/native activation and all secret/network/
seccomp/SELinux/drain/lock restrictions remain. Installed 0.2.0 evidence and hold
stay unchanged until actual OPS-018 production container-peer acceptance.

## UBI 10 image-foundation amendment (OPS-019, 2026-10-18)

[Decision 129](decision-129.md) supersedes Debian app/Alpine-derived Caddy bases
for all new 0.2.1 candidates under Tyler's UBI 10 requirement. Every FROM stage
uses pinned UBI micro; minimal contributes only Red Hat CA PEM and pinned external
uv/Caddy images contribute only executables, never foreign OS defaults/libraries.
Portable pinned CPython preserves version 3.14.6 and locked application versions.
Actual micro includes required tools; no shell-free claim or package transaction.
All runtime/SELinux/secret/lock/drain boundaries stand. Preserve old artifact/
proof/tag history as superseded or deployed evidence; repeat fresh clean REL-013
acceptance after OPS-019 commits. No production/NAS change follows from this source.

## OPS-018 installed checkpoint (2026-10-18)

[OPS-018](../agents/plans/tasks/ops-018-container-worker-rollout.md) records actual installed
notify ordering/API-container peer/TLS and non-killing drain/restart on the clean
UBI artifacts. Hold 22 closes for the owned listener; nine bindings, independent
guard, masks/locks/stores/secrets and confinement stay intact. NAS workloads and
other-host acceptance remain unrun;0.2.0 rollback restores its old peer limitation.
