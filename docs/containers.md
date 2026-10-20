# Rootless container runtime

The selected local profile uses rootless Caddy, an API server and a separately
confined private verifier. It remains guarded/read-only. See the dated
[deployment status](deployment-status.md) before any operational change; source
and fixture checks do not authorize NAS workloads or lifting the host guard.
[Runtime rationale](adr/decision-127.md) explains the isolation/lifecycle choices.

## Roles and lifecycle

| Role | Boundary |
| --- | --- |
| Caddy | Rootless TLS on 8443, existing protected certificate/key, Unix API upstream; no ACME/admin/file server/raw-header logging |
| API | One application/registry/pool/lifespan, intended Hub/REST/MCP sources, local stores/cache; NAS read-only |
| Private worker | Separate Network=none, baseline-preserving Unix-only socket creation, Python PID1, worker-created listener and peer proof; no secrets or host credential stores |
| Runtime client | Finite API-only rootless observer; exact CLI results/handles, no host operation/scheduled-state mounts or cancellation |

### Role profile matrix

Host service UID/GID come from protected runtime metadata and the helper caller.
`keep-id` maps them to container `981:981`; 981 is not a universal host UID.
Persistent roles run under the service account's user manager, reached through
the protected system bridge. The finite client is launched by the fixed host
wrapper (including Cockpit's service-identity transient unit).

| Role | Network | Secrets | Executable | Persistent/writable state |
| --- | --- | --- | --- | --- |
| `api` | `pasta` | `hfcache.api`, `hfcache.api-reader`, `hfcache.mcp-reader`, `hf-token` | `/opt/hfcache/.venv/bin/hfcache` inside image | API store, HF home/cache, runtime socket; archive read-only |
| `worker` | `none` | none | `/opt/hfcache/.venv/bin/python` inside image | Distinct verifier store/instance lock and private listener; archive read-only |
| `caddy` | `pasta` | `hfcache.tls-cert`, `hfcache.tls-key` | `/usr/bin/caddy` inside image | Local `/data`, `/config`, runtime paths; no archive |
| `client` | `none` | `hfcache.api` | `/opt/hfcache/.venv/bin/hfcache` inside image | Finite local temporary state; no server stores/archive/worker socket |

The selected template sets `mcp_enabled=true` and the helper always supplies
the four API-role sources above; this is not a per-invocation enablement option.
Secret files are container UID/GID 981 and mode 0400, under `/run/secrets`.
The API socket is `/run/hfcache/api/api.sock`; the private listener is
`/run/hfcache/verification/verification.sock`. Persistent server/worker evidence
outlives finite clients. See [native differences](server.md#deployment-profiles).

System hfcache.target starts a reviewed bridge to user hfcache.target, which starts
Caddy/API/private-worker service. API Requires/After the worker service's
notify-ready state; the indexed rootless socket artifact stays dormant. These are distinct managers. Legacy system-bus
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

### Selected runtime facts

These values are checked against image pins, rendered configuration templates and
unit artifacts. Native activation uses its separate profile.

| Runtime fact | Selected value |
| --- | --- |
| Application/build base | `registry.access.redhat.com/ubi10/ubi-micro` |
| Caddy base | `registry.access.redhat.com/ubi10/ubi-micro` |
| CA donor | `registry.access.redhat.com/ubi10/ubi-minimal` |
| Application Python | `3.14.6` |
| API socket | `/run/hfcache/api/api.sock` |
| Private worker socket | `/run/hfcache/verification/verification.sock` |
| Worker service type | `notify` |
| Rootless socket manual start | `RefuseManualStart=yes` |

[Containerfile](../packaging/containers/Containerfile),
[platform pins](../packaging/containers/images.json),
[Caddy derivative](../packaging/containers/Containerfile.caddy) and
[builder](../scripts/build-container.py) are authoritative. Python is pinned to
3.14.6 via the authenticated portable-Python input on linux-amd64. All service
FROM stages use pinned UBI 10 micro; UBI minimal contributes only Red Hat CA
data, and pinned uv/Caddy donors contribute only their executables. uv 0.11.32
is build-only. Runtime contains
the exact wheel and locked hashed server+MCP closure without uv or dependency
resolution. Caddy uses its pinned upstream platform manifest plus a reviewed
derivative that removes the unused cap_net_bind_service file capability and
asserts no file capability remains. Runtime keeps cap-drop ALL/NoNewPrivileges;
8443 needs no privileged-port capability. Record source,
wheel/closure/base/final image identities; version strings/tags alone are not
artifact identity. The supported native profile uses its own installer and system services.
See the [script inventory](scripts.md) for profile-specific entrypoints.

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
require complete peer/FD/rootless/secret/network/cleanup evidence; a partial
probe cannot establish acceptance.
The disposable proof uses a separate ordinary container_t API-role peer fixture
uses the same app image/UID mapping and a read-only private-directory view for a
fixed VerificationClient PROBE. It is not an HTTP API server or verification
admission. Installed API-container connectivity is a separate acceptance check. A separate
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

### Read-only Cockpit host permission inspection

The existing helper accepts the exact additional role `inspect-cockpit`, with no
arguments. Run it as root through the privileged Cockpit bridge. It starts no
container, acquires no lock, changes no host files or units, and reads neither
archive contents nor credential values. The normal service/client roles retain
their service-account identity and fixed launcher behavior.

Inspection requires an independently administrator-provisioned
`/etc/hfcache/cockpit-policy.json`. The application never creates or edits it.
It must be a root-owned, single-link regular file of at most 4 KiB, with no
group/other writes or symlinked parents. JSON is duplicate-free and permits
exactly this schema:

```json
{
  "schema_version": 1,
  "source_commit": "cccccccccccccccccccccccccccccccccccccccc",
  "index_sha256": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
  "permissions": {
    "archive": false,
    "hub": false,
    "control": false,
    "schedule": false,
    "configuration": false,
    "observer": false
  }
}
```

The source and index values must identify the selected immutable release; these
example values grant nothing. Permissions distinguish archive-effecting jobs,
Hub-capable sizing/diagnostic jobs, other keyed control jobs, fixed sync scheduling, guarded host
configuration changes, and stopping a proven scheduled sync observer. Permission
to submit is not proof of writable storage or workload readiness. Server
authentication, policy, capacity, identity, executor and archive locks remain
final, and the runtime archive binds remain read-only.

The selected release must include `scripts/install-container-release.py` as an
indexed, authenticated required artifact. Inspection verifies captured bytes of
that fixed script against the policy-pinned index before using only its
read-only stage and nine-binding verifiers. Releases lacking that proof are
unsupported. Root-owned protected descriptor reads, manifest/rendered hashes and
the physical helper root must match the selected `releases/VERSION` target.
Selection, policy, index and host mount facts are checked again before returning.

Host facts come from bounded `/proc/1/mountinfo`, `/proc/locks`, metadata of the
existing local domain lock, and fixed system-manager unit properties. A held
guard requires its actual main PID to own the exclusive flock on that same
device/inode. Inspection never opens the lock for content or attempts to acquire
it. It never invokes Podman as root or queries a different manager. A held guard
forces archive permission false; missing or unconfirmed facts deny effects.
An absent guard or mask does not create permission.

The current nine rootless bindings do not prove a system scheduled observer or
timer binding. Native `.venv` scheduled-client units are insufficient for this
profile. Effective `observer` and `schedule` permissions therefore remain false,
including when the policy requests them. No scheduler, alternate direct client,
user-manager redirection, unit unmasking or binding is installed by inspection.

Output is one JSON object, bounded to 16 KiB. A supported result has exactly
`schema_version=1`, `state` (`guarded` or `permitted`), `deployment=rootless`,
`source_commit`, `index_sha256`, selected `image`, `policy_sha256`, the six
effective `permissions`, and `facts`. Facts contain `guard` (`held`, `inactive`,
`absent`), `archive_mount` (`nfs-ro`, `local-ro`, `local-rw`, `absent`) and `units`.
The units object has exactly the sync/verify system services and timers; each
has `load`, `active` and `unit_file`. Load is `loaded`, `masked` or `not-found`;
active is `active`, `inactive` or `failed`. Unit-file states are `enabled`,
`enabled-runtime`, `disabled`, `static`, `linked`, `linked-runtime`, `masked`,
`masked-runtime` or `not-found`.

An unavailable result has exactly `schema_version=1`, `state=unknown` and a
`reason`: `privilege-required`, `policy-missing`, `policy-invalid`,
`deployment-unverified` or `facts-unavailable`. It includes no permissions or
partial facts. Every valid inspection result exits zero, including denied
inspection; this is not successful workload acceptance. Invalid arguments or
bridge/process failures remain separate failures. No raw diagnostics are emitted.

## Bind selection to actual execution

The two libexec entrypoints, system hfcache.target/bridge and five user unit
files under /etc/systemd/user are exact root-owned symlinks through
/opt/hfcache/current to indexed release files. The installer verifies every
binding before switch and refuses missing paths, static copies or drift without
overwriting them. Provision links under quiescence and daemon-reload
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
read-only over root-owned real placeholders. The effective client settings and
any archive UUID pin belong in authenticated template/rendering; changing a host
placeholder alone does not change them. Caddy/worker host inputs pin the same
tree; there is no disconnected /etc runtime-profile copy. Mutable archive policy
still supports atomic directory-based reload. The system bridge Requires the
archive mount; the target Wants the bridge, so a bounded mount failure refuses
runtime startup without requiring that bridge for successful target activation.
Verify these bindings and the effective manager state before activation.

## Protected host boot guard

The selected data-preserving deployment also needs the fixed root-owned
/usr/local/libexec/hfcache-readonly-guard and system
hfcache-readonly-guard.service, independent of current. They are host control
policy, not application code in the image. The recorded host guard uses UID/GID 981; this host-specific identity must
match the protected service identity. Type=notify
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
[decision 126](adr/decision-126.md).

The system bridge keeps ProtectHome=yes. Its protected host drop-in binds only
/run/user/<service_uid>/systemd/private to /run/hfcache/user-manager/systemd/private and
uses /run/hfcache/user-manager as bridge-only XDG_RUNTIME_DIR. Protected boot
directories support this narrow connection without exposing the service home.
Verify syntax with a disposable user runtime directory; never aim verification
at the live manager socket. Inspect the actual bridge drop-in and prove its
hardened connection before claiming target readiness.

### Worker-created private listener

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
podman exec isolation alone. See the recorded deployment scope below. No NAS job is authorized; rollback
to 0.2.0 retains its connection limitation.


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
For a newly provisioned fixture, OCI setup must be able to traverse an empty host
placeholder before installing its inaccessible mask. Verify the exact directory
is root-owned, empty and not a symlink before assigning the intended public
placeholder mode; the in-container tmpfs remains read-only mode `000`. An existing
credential directory is not a placeholder: preserve its permissions/content and
review the bind setup rather than changing it. OCI permission refusal before a
payload PID exists is launcher failure, even if a created container reports a
default zero exit code.
Read-only config access alone is not secret isolation. No NAS chown, relabel,
copyup or attempted write-denial probe is allowed.

Rootless/UID/peer/listener/TLS/secret/seccomp/SELinux/drain acceptance requires
owned local fixtures without a NAS bind and checks of actual installed executors.
Bare-host success and configuration alone do not prove containers. Live NAS
publication/report/catalog/hardening/full-verification workloads remain unaccepted;
see [deployment acceptance](deployment-status.md).

## Staging and selection

[The protected installer](../scripts/install-container-release.py) has separate
render, stage and switch modes. It never pulls images, provisions credentials,
starts services or opens archive files. Deployment paths must be proven local;
no /srv, NFS aliases, unreviewed symlinks, unexplained prior stages or mutable
artifacts. Only the current selector and nine exact protected execution bindings
are the reviewed symlink exceptions; artifact reads remain no-follow.
A bounded root-protected container-release.json authenticates fixed input files
and immutable identities; [schema 16](schemas.md#16-rootless-release-manifest-and-artifact-index)
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
Staging and selection require explicit operator authorization and quiescence.

Before activation, verify the public release directories are root-owned,
service-readable/searchable and not group/world writable (normally `0755`). A
restrictive inherited staging umask can make otherwise valid indexed files
unreachable. Keep credential, engine and control-state directories private; do
not solve this by opening service homes or secret directories. Administrative
`runuser`/rootless diagnostics must start from an accessible working directory
such as `/`, rather than inheriting a private operator home.

Host SELinux labeling is a separate provisioning prerequisite; the rootless
installer authenticates bytes and bindings but does not install fcontext rules.
Under Enforcing, verify persistent, narrowly scoped rules and actual contexts for
the new authenticated artifacts: `systemd_unit_file_t` for system/user unit files
(including the target and bridge), `bin_t` for executable public launchers, and
the reviewed container-readable contexts for local bind inputs. Apply only the
reviewed local rules with `restorecon -F`, then inspect actual target contexts and
manager logs. Preserve denial evidence and correct a proven missing label before
another explicit activation. Never relabel the NAS, relax policy, disable labels
or infer launcher health from successful index checks. These provisioning
prerequisites do not identify the cause of a later browser `reconnected` failure.

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
or merely available activation are not successful isolation. Preserve failed attempts and distinguish prerequisite failures from actual
policy enforcement; unrelated errors never constitute passing isolation.

## UBI 10 image inputs

[Decision 129](adr/decision-129.md) supersedes Debian/Alpine candidate bases. Every
FROM stage in app/Caddy builds uses pinned UBI 10 micro. Actual micro supplies
required tools and is not shell-free; no package transaction or larger tooling
stage is needed. Minimal is only a pinned Red Hat CA-PEM donor; external uv/Caddy
images supply only verified executables, never foreign OS/CA/defaults or FROM
stages. Portable pinned CPython 3.14.6 and locked app versions stay unchanged.
Verify contained extraction, native linkage, fresh-inode Caddy/empty getcap and
explicit ENV/user/entrypoint/mask mountpoints. Normal build/start never pulls;
explicit host prefetch obtains only pinned public inputs without app secrets.
Record every base/donor/interpreter/binary/CA/source/wheel/closure hash. Use fresh proof contexts for each reviewed image; a dirty snapshot proves only
that snapshot. Base/import checks do not establish installed or NAS acceptance.
All confinement and NAS limits remain.

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

[Decision 129](adr/decision-129.md#context-decision-and-rationale) permits only
the inspected PBS prefix's bin/pip, bin/pip3, bin/pip3.14,
lib/python3.14/site-packages/pip, pip-26.1.2.dist-info in that same directory and
lib/python3.14/ensurepip (including its bundled wheel) to be omitted inside the
UBI build layer before final COPY. Keep original verified archive/context bytes.
No wildcard/system cleanup or domain-required library/app change. Foundation
must prove PATH and module absence of pip/ensurepip/uv; failed previews stay
preserved and new contexts/images are built, never relabelled as passing.

### Recorded installed scope

Recorded 0.2.1 checks include the installed API-container private PROBE under
Enforcing SELinux before and after drain/restart, verified TLS/authentication,
MCP/client connectivity, worker readiness and confinement observations. This
closes the listener connection limitation for 0.2.1; rollback to 0.2.0 retains it.
The independent guard, NAS read-only mount and writer masks remain. No general
NAS workload, NFS interruption or other-host acceptance follows from these checks.
See [deployment status](deployment-status.md) for outstanding acceptance.
