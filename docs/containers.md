# Rootless container runtime

This is the selected local profile defined by [decision 127](adr/decision-127.md)
under the [data-preserving rollout](plans/2026-10-18-plan-local-rootless-rollout.md).
OPS-015 packages and proves it using owned local fixtures. Release/version
selection and production switch remain REL-010 and OPS-016. The
[OPS-014 guard](plans/tasks/ops-014-local-rollout-guardrails.md) keeps NAS read-only,
legacy writers blocked and the original local lock held. No command here grants
NAS writes, other-host changes, ACME issuance or remote publication.

## Roles and lifecycle

| Role | Boundary |
| --- | --- |
| Caddy | Rootless TLS on 8443, existing protected certificate/key, Unix API upstream; no ACME/admin/file server/raw-header logging |
| API | One application/registry/pool/lifespan, intended Hub/REST/MCP sources, local stores/cache; NAS read-only |
| Private worker | Separate Network=none, baseline-preserving Unix-only socket creation, Python PID1 and named FD3/peer proof; no secrets or host credential stores |
| Runtime client | Finite API-only rootless observer; exact CLI results/handles, no host operation/scheduled-state mounts or cancellation |

System hfcache.target starts a reviewed bridge to user hfcache.target, which starts
Caddy/API/private-worker socket. These are distinct managers. Legacy system-bus
controls stay blocked; never redirect them to identically named user services or
stop the archive target.

Persistent containers never pull at startup, replace a name, add an init process
or auto-remove. Unknown running/image/label/state refuses start or cleanup.
Explicit infinite Podman/application drain and systemd stop allowance replace
default timed killing. Failed/unknown stop stays blocked; remove non-forcibly only
after confirmed stopped. Inspect actual containers/libpod cgroups, not only bridge
PIDs. Finite API observers alone may auto-remove their stateless container; server
receipts and caller handles remain and accepted work is never cancelled.

API/worker share the original local flock inode, with separate public/private
socket directories and stores. Read-only policy-directory binds preserve atomic
config replacement visibility; admitted snapshots remain immutable.

## Build and image identity

[Containerfile](../packaging/containers/Containerfile),
[platform pins](../packaging/containers/images.json),
[Caddy derivative](../packaging/containers/Containerfile.caddy) and
[builder](../scripts/build-container.py) are authoritative. Python is pinned to
3.14.6 slim-trixie/linux-amd64; pinned uv 0.11.32 is build-only. Runtime contains
the exact wheel and locked hashed server+MCP closure without uv or dependency
resolution. Caddy uses its pinned upstream platform manifest plus a reviewed
derivative that removes the unused cap_net_bind_service file capability and
asserts no file capability remains. Runtime keeps cap-drop ALL/NoNewPrivileges;
8443 needs no privileged-port capability. Record source,
wheel/closure/base/final image identities; version strings/tags alone are not
artifact identity. The historical native profile is not an implicit fallback.

Build as a rootless login/service account, never root. The builder refuses
NAS/nonlocal filesystems, symlinked input/output paths, an existing context, wrong
wheel hash/name/metadata or unpinned/unhashed closure. It never pulls/pushes;
immutable bases must already exist in that user's local engine. Failed contexts
remain. UBI inputs are --python-archive (required verified portable artifact),
--wheel, --wheel-sha256, --context (new local directory) and
--tag (localhost/hfcache:...). inputs.json/build.json record commit/dirty status,
version, wheel/lock/closure/requirements/Containerfile hashes, base refs and final
image ID. A dirty-fixture build proves that snapshot, not a clean release artifact.

The [actual worker probe](../scripts/check-container-worker.py) takes --image
(exact local image ID), --workspace (new short local path) and --seccomp-profile
(derived baseline-preserving file). It retains known containers, logs and
proof.json or safe failure.json. Failed/partial activation is not isolation proof;
exact peer/FD/rootless/secret/network/cleanup evidence remains task-owned.
In the 0.2.1 proof design, a separate ordinary container_t API-role peer fixture
uses the same app image/UID mapping and a read-only private-directory view for a
fixed VerificationClient PROBE. It is not an HTTP API server or verification
admission. Actual installed API-container PROBE remains OPS-018. A separate
direct-PID1 companion tests seccomp; podman exec is not evidence of PID1 filter
inheritance. Actual worker PID1 metadata and manager notify attribution are
recorded separately from that companion.

## Protected runtime profile

The selected release's rendered/runtime.json is independent deployment schema 1,
visible inside containers as /etc/hfcache/containers/runtime.json, with exactly
these fields:

| Field | Requirement |
| --- | --- |
| schema_version | Explicit integer 1 |
| service_uid, service_gid | Positive actual host IDs, matching helper caller |
| app_image, caddy_image | sha256: plus 64 lowercase hexadecimal image IDs |

The profile contains no secret and is staged root-owned 0644. Require root
ownership, no group/other writes, single-link regular data, at most 16 KiB,
duplicate-free JSON, no-follow open and stable descriptor metadata excluding
read-induced access time.
XDG_RUNTIME_DIR must match /run/user/<service_uid>. Profile fields cannot supply
arbitrary paths/executables/engine options: role paths, names and secret references
are fixed in [the helper](../scripts/container-service.py). The protected release
artifact manifest is separate. Unknown schema/image/identity/state fails closed.

The helper is exposed as /usr/local/libexec/hfcache-container-service through
the selected immutable release. It resolves its physical release root once,
then pins that root's rendered/runtime.json and host seccomp/Caddy sources. The fixed
[client launcher](../scripts/hfcache-client) installs as
/usr/local/libexec/hfcache-client, using explicit client settings and
/run/hfcache/api/api.sock. Cockpit retains outer identity/UMask/MemoryHigh and
candidate guards, without host ImportCredential; Podman delivers the API-only
secret inside the client. No generic engine/executable authority or bare-host
fallback is exposed. See [Cockpit](cockpit.md).

For API/worker, the helper explicitly forwards only a canonical non-secret
32-lowercase-hex systemd INVOCATION_ID when present; Podman does not inherit it
automatically. This preserves executing-service metadata/log framing, not timer
or client provenance. Other ambient environment is not forwarded.

## Bind selection to actual execution

The two libexec entrypoints, system hfcache.target/bridge and five user unit
files under /etc/systemd/user are exact root-owned symlinks through
/opt/hfcache/current to indexed release files. The installer verifies every
binding before switch and refuses missing paths, static copies or drift without
overwriting them. OPS-016 provisions links under quiescence and daemon-reloads
both managers after every selection before activation. A selector that leaves
old helpers/profiles/images running is not a valid switch or rollback.

| Binding directory | Required names |
| --- | --- |
| /usr/local/libexec | hfcache-client, hfcache-container-service |
| /etc/systemd/system | hfcache.target, hfcache-containers.service |
| /etc/systemd/user | hfcache.target, hfcache-api.service, hfcache-caddy.service, hfcache-verification.service, hfcache-verification.socket |

Before activation, inspect actual manager FragmentPath and effective drop-ins
after reload; refuse home/runtime overrides or drift. Static links alone do not
prove the manager's effective unit choice.

Each helper invocation pins one physical release. After binding the base
/etc/hfcache policy directory read-only, overlay that release's rendered directory
at /etc/hfcache/containers and its client.toml at /etc/hfcache/client.toml,
read-only over root-owned real placeholders. Caddy/worker host inputs pin the same
tree; there is no disconnected /etc runtime-profile copy. Mutable archive policy
still supports atomic directory-based reload. The system bridge Requires the
archive mount; the target Wants the bridge, so a bounded mount failure refuses
runtime startup without requiring that bridge for successful target activation.
These links and actual manager activation are later guarded rollout work.

## Protected host boot guard

The selected data-preserving deployment also needs the fixed root-owned
/usr/local/libexec/hfcache-readonly-guard and system
hfcache-readonly-guard.service, independent of current. They are host control
policy, not application code in the image. Type=notify runs as UID/GID 981;
READY follows strict original-lock ownership/inode checks and a host NFS-ro
observation from /proc/1/mountinfo. The guard retains its noncreating flock until
reviewed stop; it does not continuously monitor mount/inode changes. Keep strict
sandboxing while exposing the actual host PID/proc view, since the guard's own
private mount namespace may be read-only regardless of host state.

Enable the static host guard independently of application selection with
`systemctl add-wants multi-user.target hfcache-readonly-guard.service`; verify its
root-owned link resolves to the fixed /etc/systemd/system unit outside current.
Require it from the bridge's protected local drop-in. Never enable the app target from the user
default target: only the bridge starts it after READY. Boot tmpfiles f rules
create missing domain/API locks without truncation and d 0700 protects runtime
socket directories; no unit cleanup removes live locks. Root alone performs the
old transient guard→installer-held original lock→permanent guard handoff with
NAS-ro/masked writers/quiescence maintained. Application activation waits the new
READY signal; failures/unknown holders refuse progression. See
[decision 126](adr/decision-126.md#permanent-host-boot-guard-ops-016-2026-10-18).

The system bridge keeps ProtectHome=yes. Its protected host drop-in binds only
/run/user/981/systemd/private to /run/hfcache/user-manager/systemd/private and
uses /run/hfcache/user-manager as bridge-only XDG_RUNTIME_DIR. Protected boot
directories support this narrow connection without exposing the service home.
Verify syntax with a disposable user runtime directory; never aim verification
at the live manager socket. Inspect the actual bridge drop-in and prove its
hardened connection before claiming target readiness.

### 0.2.0 partial acceptance and historical worker hold

OPS-016 starts the local 0.2.0 Caddy/API runtime and proves verified TLS, API/MCP
authentication/registry, container client, isolation and non-killing drain.
However, SELinux refuses API container_t connectto to the user-manager-created
unconfined_t verification socket. The actual host UID-981 FD3 peer probe succeeds;
earlier NAS-free VerificationClient fixtures also used a host process. Neither
proves API-container-to-worker connectivity. End-to-end verification is not
accepted. Keep Enforcing policy, container labels and execution boundaries; no
allow rule, label-disable or host execution bypass is an approved quick fix.
At OPS-016 conclusion, a reviewed label-at-creation/container-activation design
was unselected operator backlog. **2026-10-18 update:** decisions 128/129 and
committed source 4088994/REL-013 clean UBI artifacts support completed OPS-018.
Actual installed API-container PROBE now closes connection hold 22 for 0.2.1;
source/fixture evidence alone never supplied that proof. Preserve the
[explicit hold](progress.md#operator-handoff) and all NAS-write/full-domain holds.

### 0.2.1 listener correction (OPS-017)

[Decision 128](adr/decision-128.md) selects explicit --container-listener in the
direct PID1 worker. Before own resources/NSS/shared imports, reject inherited FDs
above stderr, any LISTEN_* activation field and known credential environment.
Preserve separate strict native named-FD3 activation without fallback. Acquire
worker instance ownership before listener creation; no-follow pin an effective-
UID/GID-owned 0700 private parent, refuse every existing pathname, bind via its
proc-fd address and enforce socket 0600/exact-created-inode identity. Validate
the trusted bound spelling and filesystem identity; internally use FD3 without
shell/init. Join active work before closing/removing only that exact owned inode,
holding parent and instance through cleanup. A crash's stale socket remains
evidence and refuses restart until reviewed handling; no automatic unlink/replay.
Before opening its parent or binding, refuse socket/archive-root lexical overlap
and require a known local filesystem from bounded fixed /proc/self/mountinfo.
Unknown/network mounts refuse without realpath/NAS stat or parent traversal;
this new IPC authority never permits NAS access through misconfiguration.

Only the worker private-directory bind becomes writable. API's bind remains
read-only; keep all root/network/seccomp/secret/capability/cgroup/lock boundaries.
Rootless worker.service uses Type=notify, NotifyAccess=all and
--sdnotify=container; the worker sends READY only after listener/instance/store/
worker initialization. The user target starts worker.service, API Requires+After
it, and no target/API/service automatically references the .socket. Keep that
artifact/binding dormant RefuseManualStart=yes, preserving nine bindings; native
socket activation stays unchanged. Infinite non-killing drain and stop ordering
remain. Actual container-proxied notification and separate API-container PROBE
under Enforcing SELinux are proof obligations, not supplied by host probes or
podman exec isolation alone. At the source-package boundary 0.2.0 remained
selected; completed REL-013/OPS-018 now record clean UBI 0.2.1 and actual installed
acceptance. No NAS job is authorized; 0.2.0 rollback retains its old hold.

## Filesystem, secrets and resource limits

All writable graphroot/image/Caddy/state/cache/temporary paths are local. Actual
payload cgroups use 4 GiB memory.high for API/worker/client and 512 MiB for Caddy;
a launcher limit alone would not enclose libpod payloads. Read-only root filesystems
have only reviewed local writable exceptions. No Podman control socket, host
PID/network/credential/home stores, privileged or label-disable shortcut.

Mount intended secrets as UID 981/mode 0400 files, never image/env/argv/browser/log
values. API alone receives Hub plus distinct REST/optional MCP authority, Caddy TLS
only, client API only. Worker/client additionally mask /run/credentials,
/etc/credstore, /etc/credstore.encrypted and /etc/hfcache/credentials with empty
inaccessible read-only mounts; custom sources need explicit review/masking.
Read-only config access alone is not secret isolation. No NAS chown, relabel,
copyup or attempted write-denial probe is allowed.

Actual rootless/UID/peer/FD3/TLS/secret/seccomp/SELinux/drain proof uses owned local
fixtures with no NAS bind in OPS-015. Root may prepare necessary local proof
infrastructure; changes/failures remain task evidence. Earlier bare-host tests or
configuration alone do not prove containers. Live NAS publication/report/catalog/
hardening/full verification acceptance remains forbidden and NOT RUN; see
[deployment](deployment-centos-stream-10.md#19-rootless-runtime-architecture-ops-015)
and [release](agents/release.md).


## Staging and selection

[The protected installer](../scripts/install-container-release.py) has separate
render, stage and switch modes. It never pulls images, provisions credentials,
starts services or opens archive files. Deployment paths must be proven local;
no /srv, NFS aliases, unreviewed symlinks, unexplained prior stages or mutable
artifacts. Only the current selector and nine exact protected execution bindings
are the reviewed symlink exceptions; artifact reads remain no-follow.
A bounded root-protected container-release.json authenticates fixed input files
and immutable identities; [schema 16](schemas.md#16-rootless-release-manifest-and-artifact-index-ops-015)
defines it and the independent artifact-index.json.

Staging under /opt/hfcache/releases/<version> copies authenticated sources and
rendered units/config/runtime/default+derived seccomp/provenance, fsyncs files and
directories, verifies exact indexed bytes, then atomically renames and fsyncs the
parent. The index covers everything except itself; unknown artifacts/links/dirs
refuse selection and remain. switch rechecks source digests, entire index and
recomputed rendering under the original noncreating local flock, then atomically
updates /opt/hfcache/current and fsyncs its parent. No running/unknown executor,
libpod cgroup or activation state may be ignored. Previous native/container
releases and all retained state remain; no force cleanup or implicit migration.
Production staging/version selection/switch remains later tasks, not OPS-015 proof.

A refusal after current-link replacement but failed parent-directory fsync is an
uncertain acknowledgement: exit 20 may leave the new selector in place. Both trees
remain; inspect current under the normal guard before retrying. Do not infer
unchanged selection, auto-roll back or clean partial stage/evidence.

The worker policy must remove socket/socketcall from every base ALLOW and then
allow native socket only for AF_UNIX/domain 1, retaining all other baseline
restrictions. Appended same-default ERRNO rules were insufficient in actual proof;
Network=none alone also does not deny socket creation. No AF_NETLINK allow rule.
Explicit --remote=false selects the local engine for build/probe/runtime actions.
Before API/worker startup the runtime guard checks kernel mount metadata only and
requires actual NFS read-only; it never opens the archive to test this boundary.


The worker's recognized architecture map is native-only, matching prior
SystemCallArchitectures=native. Preserve all other baseline restrictions and
original/derived hashes; reject unknown base shapes. Container execution errors
or merely available activation are not successful isolation. The task preserves
failed attempts and distinguishes fixture corrections, actual policy defects and
final corrected proof.

## UBI 10 foundation amendment (OPS-019)

[Decision 129](adr/decision-129.md) supersedes Debian/Alpine candidate bases. Every
FROM stage in app/Caddy builds uses pinned UBI 10 micro. Actual micro supplies
required tools and is not shell-free; no package transaction or larger tooling
stage is needed. Minimal is only a pinned Red Hat CA-PEM donor; external uv/Caddy
images supply only verified executables, never foreign OS/CA/defaults or FROM
stages. Portable pinned CPython 3.14.6 and locked app versions stay unchanged.
Verify contained extraction, native linkage, fresh-inode Caddy/empty getcap and
explicit ENV/user/entrypoint/mask mountpoints. Normal build/start never pulls;
explicit host prefetch obtains only pinned public inputs without app secrets.
Record every base/donor/interpreter/binary/CA/source/wheel/closure hash. Repeat
fresh dirty then clean UBI proofs; old candidate results are superseded, not UBI
or installed acceptance. At OPS-019 completion production 0.2.0/hold 22 remained;
completed OPS-018 now records installed 0.2.1/connection-hold closure below. All
confinement/NAS limits remain.

### Protected portable-Python fetch

Run the host build-tool environment's
`scripts/fetch-container-python.py --images-json packaging/containers/images.json --output NEW_LOCAL_FILE`
only for explicit public input preparation. The trusted pin is nested
python_distribution(version, url, sha256); no CLI URL override or extraction.
The fetch ignores ambient proxy/auth/SSL_CERT_* inputs, uses verified HTTPS and
at most five manual HTTPS redirects without draining rejected redirect bodies.
Bounds are 128 MiB, 300 seconds overall and 10-second socket waits. Publish the
complete verified artifact exclusively; retain failed partials. Schema-1 output
contains only python_version/url/sha256/bytes/artifact. The image builder requires
--python-archive and independently verifies hash/safe extraction; a fetched file
or successful fetch alone is not image/runtime acceptance.

### Caddy UBI build

Run `scripts/build-caddy-container.py --context NEW_LOCAL_DIR --tag localhost/hfcache:TAG`
from the project build-tool environment. The fixed helper uses trusted images.json,
all-micro stages, a CA-only minimal donor and the verified static Caddy binary.
It records source/dirty/platform, caddy_base/build_base/ca_bundle_image/
caddy_binary_image, binary/CA/Containerfile hashes and tag. A successful build.json
also records image_id/caddy_version, empty file_capabilities and exact retained
probe container identity/exit. The finite UID-981/no-network/caps-0/NNP/read-only
probe checks hash/getcap/version without starting Caddy. Preserve its named
container/CID file on success, failure or timeout; unknown identity/state never
authorizes removal or a passing build. Actual served TLS is a separate proof.

### UBI foundation proof

`scripts/check-container-foundation.py --image EXACT_ID --workspace NEW_LOCAL_DIR --images-json packaging/containers/images.json [--build-record PATH]`
verifies the selected micro manifest's config ID and ordered RootFS diff-ID prefix
against the actual app image; os-release alone is insufficient. It then runs a
bind-free/no-network/read-only/caps-0/NNP PID1 check for native imports, NSS, CA,
SSL and glibc. Retain the stopped named container and proof.json, including safe
source/build-record hash and pins. This foundation proof is separate from actual
worker confinement/notification/peer or served Caddy TLS acceptance; never infer
those results from successful imports or a base label.

The runtime image's intended SSL_CERT_FILE=/etc/ssl/cert.pem names verified
public Red Hat CA data. Foundation proof must accept that exact fixed value and
verify the CA hash, while rejecting unexplained trust overrides. This does not
relax the host fetcher's independent rule to ignore ambient SSL_CERT_* inputs.

Use supported normal caio package/backend imports under unchanged seccomp.
An unavailable optional linux_uring module is recorded, with the actual preferred
linux_aio/thread fallback; it is not grounds to force CAIO_IMPL or allow io_uring.
The proof process alone sets HF_XET_LOG_DEST=/dev/null to keep native diagnostics
out of its single JSON result, without changing image/application defaults.
All other foundation assertions remain required.

### Exact runtime installer omission

[Decision 129](adr/decision-129.md#exact-optional-installer-pruning) permits only
the inspected PBS prefix's bin/pip, bin/pip3, bin/pip3.14,
lib/python3.14/site-packages/pip, pip-26.1.2.dist-info in that same directory and
lib/python3.14/ensurepip (including its bundled wheel) to be omitted inside the
UBI build layer before final COPY. Keep original verified archive/context bytes.
No wildcard/system cleanup or domain-required library/app change. Foundation
must prove PATH and module absence of pip/ensurepip/uv; failed previews stay
preserved and new contexts/images are built, never relabelled as passing.

### Installed0.2.1 acceptance (OPS-018, 2026-10-18)

[OPS-018](plans/tasks/ops-018-container-worker-rollout.md) selects clean source 4088994
UBI app/Caddy artifacts and proves actual installed API-container PROBE under
Enforcing before/after clean drain/restart. Connection hold 22 closes for this
listener; 0.2.0 failure remains a rollback limitation. Verified TLS/auth/MCP/client,
worker READY/effective confinement and unchanged locks/stores/secrets pass.
The independent host guard/NAS-ro/writer masks remain. No live NAS job, storage
verification or general NFS/other-host acceptance follows from these checks.
