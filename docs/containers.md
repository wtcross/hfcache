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
remain. Inputs are --wheel, --wheel-sha256, --context (new local directory) and
--tag (localhost/hfcache:...). inputs.json/build.json record commit/dirty status,
version, wheel/lock/closure/requirements/Containerfile hashes, base refs and final
image ID. A dirty-fixture build proves that snapshot, not a clean release artifact.

The [actual worker probe](../scripts/check-container-worker.py) takes --image
(exact local image ID), --workspace (new short local path) and --seccomp-profile
(derived baseline-preserving file). It retains known containers, logs and
proof.json or safe failure.json. Failed/partial activation is not isolation proof;
exact peer/FD/rootless/secret/network/cleanup evidence remains task-owned.

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
