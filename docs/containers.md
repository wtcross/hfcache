# Rootless container runtime

The selected local profile uses rootless Caddy, an API server and a separately
confined private verifier. It remains guarded/read-only. See the dated
[deployment status](deployment-status.md) before any operational change; source
and fixture checks do not authorize NAS workloads or lifting the host guard.
[Runtime rationale](adr/decision-127.md) explains the isolation/lifecycle choices.
The selected installed release is 0.2.2 from clean source
`1c685018803a365bbb8b0c1aad4b94709f60e7d7`.

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
wrapper running under the selected service identity.

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

For an explicitly selected web release, pass both `--web-assets DIR` and
`--web-manifest-sha256 HEX` to the app builder. It verifies the canonical bounded
asset tree, hashes and backend version/wire/lock identity, then copies its bytes
to `/opt/hfcache/ui` in the existing app image. Its input/build records bind the
UI manifest and member hashes to the image construction. Omitting both options
keeps the Python-only image path; partial options refuse. Construct clean
backend/UI/helper artifacts with the
[clean release builder](web-ui/deployment.md#build-and-select-a-clean-release).
The actual foundation probe verifies ordered pinned base ancestry, final image
size and absence of Node/npm/pnpm/corepack, Python/system package managers,
compilers and browsers. Labels or source recipes alone are insufficient.

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
/run/hfcache/api/api.sock. The wrapper retains the service identity and fixed
client settings without host ImportCredential; Podman delivers the API-only
secret inside the client. No generic engine/executable authority or bare-host
fallback is exposed.

For API/worker, the helper explicitly forwards only a canonical non-secret
32-lowercase-hex systemd INVOCATION_ID when present; Podman does not inherit it
automatically. This preserves executing-service metadata/log framing, not timer
or client provenance. Other ambient environment is not forwarded.

### Protected host permission inspection

The web API uses the separately confined fixed host helper for bounded selected-
release, mount, original-lock and manager observations. Permissions, actual
storage writability and workload readiness remain independent. A held guard
forces archive denial; missing, unsafe or unconfirmed evidence denies effects.
The guarded rootless profile does not establish native scheduled-observer or
timer bindings, so schedule/observer effects stay denied. Inspection does not
start containers, alter units, acquire the archive lock or read credential values.
See the current [host contract](host-administration.md) for the fixed protocol,
protected policy, captured-byte validation and deployment-specific proofs.

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

### Static user-unit verification

Never run `systemd-analyze --user verify` with a live `XDG_RUNTIME_DIR`. In
systemd 257 its test manager can replace the live `systemd/private` socket.
Static verification must use a fully owned disposable runtime directory,
isolated bus endpoints and isolated unit/generator search and output paths.
No path may resolve to a live manager socket or generator directory. Successful
syntax verification does not prove that the running manager remains reachable.

If a private endpoint becomes stale, preserve the endpoint and actual manager
PID/starttime/invocation evidence; do not blindly unlink the socket or restart
the manager. Restoration requires reviewed actual executor quiescence and
authenticated observation through the existing user bus. The scoped 0.2.2
restoration used an explicit no-reply `Reexecute` only after zero-executor proof,
retaining the service manager's PID and invocation. It is not an automatic retry
procedure; an unrelated stale login-user manager was left unchanged.

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
Use the [isolated static verification procedure](#static-user-unit-verification);
never aim verification at the live manager socket. Inspect the actual bridge drop-in and prove its
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
The optional Basic provider in unreleased source can read its protected hash
record at `/etc/hfcache/credentials/ui-administrator.json` through the API's
existing policy-directory bind. Provision its actual mapped service owner and
mode0400/0600; it is not a plaintext password or bearer. Worker/client masks hide
this fixed directory, and Caddy has no `/etc/hfcache` bind. Keep the record inside
that reviewed directory. No additional secret or source read is required when
Basic is disabled. See [protected provisioning](web-ui/deployment.md). Actual
installed role isolation remains a release-acceptance obligation.
The optional `[web]` artifact is public release material rather than a secret,
but only the API captures/serves it after administrator authentication. It must
remain separate from policy/credential delivery, API writable state, archive,
sockets and locks, including physical bind aliases. Mounting a credential
directory inside an asset tree is refused. Protected asset ancestors must be
root or the actual mapped API identity and not group/other writable; host numeric
UID assumptions are insufficient. Keep the established read-only root filesystem,
SELinux and role mounts intact. Caddy receives neither an asset bind nor the
administrator record, and worker/client roles need no asset authority.
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

### Optional web release input

The optional authenticated `packaging/containers/web.toml` enables the built UI
without changing the deployment schema's top-level fields. Include its exact
digest, `scripts/web-release.py` and every `ui/` artifact, including
`ui/manifest.json`, in `container-release.json`'s existing `files` map. The input
is at most 4 KiB, with exactly integer `schema_version = 1`, boolean
`enabled = true` and lowercase SHA256 `manifest_sha256`. An explicit disabled
input has exactly `schema_version = 1` and `enabled = false`; an absent or disabled
input leaves Basic/web configuration disabled.

Before render/stage directory effects, enabled input requires the complete
canonical asset tree, its clean source commit and application version, member
hashes and exact indexed verifier bytes matching the trusted installer's sibling
verifier. Unknown/extra/missing/mismatched assets refuse. Rendering appends only
`[web]` with `/opt/hfcache/ui` and the exact manifest digest, plus `[basic]` for
`https://<hostname>:8443` and the fixed
`/etc/hfcache/credentials/ui-administrator.json`. The hostname must be canonical
lowercase and the exact origin must already be in the listener policy. Existing
Basic/web template sections refuse this opt-in. Caddy routing, port and TLS stay
unchanged; assets are served only by the authenticated API.

The manifest permits at most 1,000 non-UI source entries plus 4,097 UI entries
(4,096 members and their manifest), with an 8 MiB release/index bound. UI byte,
path and tree limits remain the separate
[asset contract](schemas.md#183-web-release-manifest-and-ui-bootstrap).
Valid zero-byte members are preserved; non-UI artifact reads retain their
nonempty requirement. All copied bytes remain in the immutable artifact index.
The independently protected host reader retains its own smaller inspection
budgets; the release-index ceiling grants no larger helper-read authority.

This input provisions no hash record, helper policy, credential, SELinux label,
timer or manager. The API refuses enabled startup if the hash record or assets
are missing or incompatible. Preserve the existing API-only policy bind,
worker/client credential masks, no Caddy policy bind and helper opt-in below.
Staging never installs the separate protected helper bootstrap copies or starts
services. Source packaging and disposable acceptance do not authorize production
deployment or live service removal.

### Optional host reader input

The fixed optional source file `packaging/containers/host-helper.toml` enables
the replacement host reader without editing a rendered release. If present,
include its exact digest in `container-release.json`'s existing `files` map; it
is then copied and indexed like every other authenticated input. Its complete
TOML shape is `schema_version = 1` and `enabled = true` or `false`, with no other
keys and at most 4 KiB. An unlisted file is not an input. An absent or false
input preserves the original rendered `server.toml` bytes.

True appends exactly a rootless `[host_helper]` configuration with `enabled =
true`, `profile = "rootless"` and `api_host_gid` from the manifest's existing
service group. Existing helper configuration in the server template refuses
this opt-in instead of introducing a second authority. No deployment digest is
embedded: the fixed protected helper startup binding supplies it after the
independent index is provisioned. This avoids an index hashing its own digest.
The original runtime schema 1, manifest keys, stage verification and nine
execution bindings remain intact. This input enables the endpoint dependency;
only the independent six-category policy can grant actions. Helper paths are
mounted read-only into the API alone, with no unprivileged relabel option;
worker, Caddy and client roles receive no helper mount or projection.

When the validated API helper projection is present, its existing
`/var/lib/hfcache/hf-home` and `/var/cache/hfcache` binds omit shared `:z`
relabeling. Preserve their fixed writable mount scope, the separately provisioned
Hub-state type, and original/default and other-role argv, except the archive-lock
bind described next. Both enabled API and worker preserve the independently
provisioned `hfcache_host_helper_archive_lock_t` label on the original fixed
`/run/hfcache/hfcache.lock` without `:z`. Both validate its service ownership,
ordinary single-link0600 metadata and `object_r`/type/`s0` context. Worker reads
only the protected rendered server opt-in and receives no helper authority
projection. Missing/unsafe labels refuse; no launch repairs or creates the lock.
The helper can inspect only its metadata; generic container payload permissions
remain unchanged. Native/disabled profiles and the fifteen-role receipt remain
unchanged. See [the fixed-lock decision](adr/decision-159.md). The application
`config.toml` leaf has its own application-readable type; the privileged helper
may write that type only through its fixed guarded configuration workflow. The
API bind remains read-only. `/etc/hfcache` has a separate directory type for
fixed-name publication; private root0700 outcome directories and configuration
guards have distinct container-denied types. Private helper authority
types remain unreadable to containers. Prove actual config reads, Hub-state
operations and new leaf labels under Enforcing before support is accepted.
Native opt-in uses its separately protected server configuration. The host helper's
managed entry clears temporary ambient/inheritable startup state before any
observer. Its separate engine child enters only the proved existing USER
namespace and at fixed API-container exec retains only namespace-local
DAC_READ_SEARCH and SYS_ADMIN in effective/permitted/bounding sets (bits2+21,
mask0x200004), with empty inheritable/ambient sets and securebits0xCE.
[Decision151](adr/decision-151.md) supersedes the earlier SYS_ADMIN-only rule
after mapped-ID layer metadata traversal failed. Read/search DAC bypass covers
all reachable mapped-UID-and-GID inodes, not one path; it grants no write or
regular-file execute bypass and never replaces SELinux. It never enters the
engine MNT namespace. Retain the original masked MNT and prove its initial-USER
ownership and actual MNT-entry/unshare, archive/Hub/IP and required inode/FD-alias
denials. The host observer keeps its initial USER and masked MNT view; no
initial-USER SYS_ADMIN or DAC capability is granted. SELinux never authorizes
DAC_OVERRIDE; require its bit absent at verified steady/fixed-exec boundaries.
Neither opt-in nor a successful diagnostic grants a category or establishes
installed support. See the [host reader contract](host-administration.md) and
[decision150](adr/decision-150.md).

The host reader additionally requires the separately installed, enforcing
`hfcache_host_helper_t` SELinux policy from first exec, inherited by every helper
child. Install the exact selected CIL and fixed object labels, then independently
record the actual loaded module/kernel-policy and label facts in root-owned
`/etc/hfcache/host-helper-selinux.json`; the neutral index pins that receipt.
Archive/Hub/credential/container-secret object types must deny helper reads through
aliases as well as direct paths. Retain all masks, capability/namespace limits and
NoNewPrivileges. No policy/label installation or permission grant occurs on a
status read. Unsupported or stale policy/labels refuse. See the
[mandatory SELinux contract](host-administration.md#mandatory-selinux-isolation).
Owned nonsecret alias-denial and full installed API/helper proof remain required;
earlier source/INFO checks alone do not close this requirement.

### Read-only helper index preparation

Install the reviewed root-protected helper bootstrap copies before running
`scripts/prepare-host-helper.py`. It accepts only `--profile native` or
`--profile rootless`, a genuine measured `--source-commit` and
`--source-snapshot`, and an explicit `--source-dirty` or `--source-clean`.
These source assertions must come from the build receipt; layout, a version
string or a dirty checkout does not establish a clean commit. The tool reads
the fixed `/opt/hfcache/current` selection, actual ordinary protected evidence
and fixed execution bindings, then prints a proposed neutral deployment index.
It performs no installation, policy/key generation, service activation,
configuration/credential/archive read or automatic permission grant.

Native preparation includes every actual installed application leaf, including
existing bytecode, the installed entry point, fixed unit/helper copies and the
actual pinned interpreter bytes. Compile application bytecode during the build
before freezing this inventory, keep the installed package root protected, and
prevent later cache creation from silently changing its declared leaves.
Rootless preparation retains the original stage/rendering and nine-binding
checks. Both branches share the finite protected-reader budget. A proposal is
not conformance: review the index and independent policy, install them through
an explicitly authorized protected operation, then require the helper's full
fresh inspection and deployment acceptance evidence.

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

The web UI replacement retains this image boundary: built static UI assets must
ship inside the existing API image based on pinned UBI 10 micro, with no separate
frontend image or runtime Node/package manager. Optional source serving now
requires an explicit matching artifact directory and pinned manifest hash; it
does not add an asset COPY step to the current release builder. Release packaging
must still bind a clean source build to the independently verified backend wheel
and prove ancestry, installed asset identity and runtime contents before claiming
release acceptance. Dirty owned fixtures remain labeled as such. Browser test
tooling is unshipped and does not determine the application base.

The configured canonical hostname is also Caddy's default TLS server name for
clients that omit SNI, including IP-address clients behind the rootless port
forwarder. The existing certificate still has to cover that hostname or address;
client certificate verification and the API's explicit Host/Origin policy remain
required.

The same Caddy process forwards UI, REST and MCP to the existing Unix API
upstream. Application-owned authentication protects every enabled UI path,
including assets and errors; no Caddy-wide Basic gate or static file server is
introduced. The API captures bounded immutable bytes at startup and does no
request-time asset pathname reads. Disabled web reads no asset/mount information.
See [artifact selection and deployment](web-ui/deployment.md) for ownership,
identity, prefix and stream limits. Source checks or direct-TLS authentication
tests alone do not establish installed shared-Caddy/native/rootless acceptance.

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

Current 0.2.2 host acceptance includes verified TLS, thirteen authentication/class
checks, the exact fourteen read-only MCP tools, an API-container-origin private
PROBE and actual worker PID1 offline/mask/capability/read-only-root observations
under Enforcing SELinux. The new notify guard holds the original domain inode;
NAS read-only, writer masks, disabled calendars and original configuration,
candidate, backup, locks and durable stores remain. Historical protected policy
grants remain unchanged. This does not prove an original production browser
candidate flow or permit a NAS workload. The [deployment status](deployment-status.md) records
the installed identities, local tag and remaining holds.

Historical 0.2.1 checks include the installed API-container private PROBE under
Enforcing SELinux before and after drain/restart, verified TLS/authentication,
MCP/client connectivity, worker readiness and confinement observations. This
closes the listener connection limitation for 0.2.1; rollback to 0.2.0 retains it.
The independent guard, NAS read-only mount and writer masks remain. No general
NAS workload, NFS interruption or other-host acceptance follows from these checks.
See [deployment status](deployment-status.md) for outstanding acceptance.

### Managed configuration reads and previews

The API-only helper connection also supports editable configuration reads and
read-only managed reconstruction. No additional host mount, manager/engine
socket, capability, writable root or container environment authority is needed.
Caddy and worker remain excluded. Private candidate text is independently bounded
and never becomes a public operation payload. The existing shared API/UI image
continues to use pinned UBI10 micro without a frontend runtime.

Managed previews preserve the configured Hub/credential authority and use existing
API networking only when the helper-derived repository scope is nonempty and
explicit Hub permission is freshly proved. An empty scope contacts no Hub.
Preparation and sizing cannot install configuration. See the [API contract](api.md#managed-configuration-read-and-assessment-responses)
and [configuration guide](web-ui/configuration-and-tags.md).


### Managed configuration writer provisioning

Helper-enabled releases additionally capture `host-helper/host_configuration.py`
as the fourth standard-library module beside the entry, unit, policy/protocol/
peer modules and CIL. Its exact installed copy is an independent deployment
binding for both native and rootless profiles. The helper service's fixed
`SupplementaryGroups=hfcache` permits owned0640 creation without CAP_CHOWN; only
its `/etc/hfcache` bind becomes writable. No application container receives a
writable configuration mount or private history mount. Keep all existing helper
masks, rootless namespace/capability proofs and no-network restrictions.

Provision the dedicated configuration-directory, private-state and guard types
and persistent exact fcontexts before preparing new indexes. A reviewed first
upgrade may assign the new guard SID to the **same original lock inode**, recording
before/after contexts without changing its mode, ownership or identity. Never
replace that lock. Preserve private history inodes and their recorded full SIDs;
unknown evidence is not permission to relabel it. Application
containers retain read-only config access; private outcome/guard types remain
denied. See [label roles](host-administration.md#mandatory-selinux-isolation) and
[helper deployment](web-ui/deployment.md#install-the-protected-host-reader).

Helper-enabled releases also capture `host-helper/host_actions.py` and
`host-helper/host_selinux.py`, independently bound as `helper_actions_module` and
`helper_selinux_module`. Their presence grants no host permission. Optional native
effect labels use the closed version2 receipt; the rootless read/configuration
profile may retain version1 without those objects. It continues to deny system
schedule and observer effects, with no same-name user-manager fallback. New
schedule history stays inside the sole optional fixed timer-directory writable
bind; no application container receives that bind, private outcomes or a manager
socket. See [native provisioning](web-ui/deployment.md#optional-native-schedule-and-observer-provisioning).
The optional native observer context fragment/domain/state label is not a
rootless binding or a container escape hatch. Rootless rejects that optional
deployment role and continues to deny system schedule/observer effects even
when Basic administrator feature availability is true.
