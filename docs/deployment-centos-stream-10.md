# Deploying hfcache on CentOS Stream 10

Choose a deployment profile before selecting tools, paths or service managers.
The [recorded local deployment](deployment-status.md) is rootless 0.2.1 and remains
guarded/read-only. This guide describes supported provisioning and acceptance;
it does not authorize changing that installation, running NAS workloads, enabling
calendars or initializing its existing archive. Historical observed output is not
an acceptance result for a different profile or release.

## Deployment profiles

| Profile | Host executable | Manager and listeners | Credential delivery |
| --- | --- | --- | --- |
| Selected rootless | `/usr/local/libexec/hfcache-container-service`, `/usr/local/libexec/hfcache-client` | System bridge to service account user manager; API `/run/hfcache/api/api.sock`, worker `/run/hfcache/verification/verification.sock`, Caddy TLS 8443 | Fixed named Podman secrets mounted as files; no host credential import into clients |
| Native service | `/opt/hfcache/current/.venv/bin/hfcache` and release Python | System manager; API `/run/hfcache/api.sock` plus optional TCP, worker `/run/hfcache/verification.sock`; strict socket activation | Named systemd credentials or explicit protected server-local files |
| Reader | Installed API-only client | Explicit authenticated Unix endpoint or verified HTTPS/public prefix | Protected REST reader file or named API credential; no archive/Hub access |
| Consumer | Independent copy helper | Read-only NFS `published/` export and consumer-owned destination | Whole-export entitlement; no writer/API credential needed for copying |

Inside application images, executables live at `/opt/hfcache/.venv/bin`; that is
not the host native release path. Native and user units can share names but have
different managers and authority. Never redirect legacy system-bus controls into
the user manager. [Container role matrix](containers.md#role-profile-matrix)
records actual UID/network/mount/state/secret boundaries.

## Prerequisites and identities

Provision the NAS dataset, exact-host writer export, disjoint read-only consumer
export, quota, snapshots/replication/scrub and service identities first; see
[storage requirements](storage-requirements.md). Use deployment-specific hostname,
IP, UUID and repository policy. Examples use documentation-only names/addresses.
The immutable sentinel UUID must equal `storage.archive_id`; keep it outside the
writer's backup domain and never regenerate it to bypass a mismatch.

Keep SELinux enforcing, systemd/container hardening intact and the bare unmounted
`/srv/hfcache` root-owned/unwritable to the service account. Missing NFS must not
silently redirect writes onto the VM filesystem. NFS Mapall ownership can appear
unknown locally; effective writability is proven through the application in a
separately accepted write window, not by comparing host `st_uid`.

Native services use a locked nologin service account. Rootless services additionally
need a protected local service home, subordinate IDs, local graphroot/runroot and
user runtime/manager access. Derive actual host UID/GID from protected runtime
metadata; keep-id maps them to container 981:981. Do not copy a recorded numeric
host UID into another deployment. Application/config/release trees are root-owned;
service state/cache are local and owned by the intended service identity.

## Shared host integration

Install/review `git`, `nfs-utils` and time synchronization for the writer host.
Container tooling is a separate rootless-profile prerequisite; the native installer
uses pinned uv 0.11.32 and the source `.python-version` value (`3.14`),
which uv resolves into its managed installation. The container input separately
pins an authenticated CPython 3.14.6 artifact. Host helper scripts support the
system Python 3.12; the application uses its pinned interpreter.

Use either explicit `srv-hfcache.mount`/`.automount` units or an fstab-generated
pair, never both. Network ordering belongs on the mount, not the automount:
`After=network-online.target` on an automount can form a local-fs ordering cycle.
Review `systemd-analyze verify` output, not just exit status, because it can report
cycles with exit 0. If the archive path changes, rename mount units with
`systemd-escape --path`, update `Where=`, every `RequiresMountsFor`/read-write path
and archive policy together. The selected host retains its protected read-only
mount and independent guard.

Review the shipped tmpfiles, journald and dirty-page policy fragments before
separately authorized installation. Boot `f` rules create missing local locks
without truncation; service cleanup must not unlink them. Persistent journald
(1 GiB/one year) retains refusals/crashes that have no domain report. The optional
failure-hook template integrates monitoring. MemoryHigh plus dirty-page bounds
limit working set; hypervisor free-page reporting or reserved memory is a separate
operator responsibility. Never change kernel settings merely to test a denial.

## Rootless preparation and staging

The selected profile uses pinned UBI 10 micro for every app/Caddy FROM stage.
Pinned UBI minimal donates only Red Hat CA data; uv/Caddy donor images contribute
verified binaries only. The authenticated portable CPython artifact and locked
hashed server+MCP wheel closure are explicit build inputs. See
[build identities](containers.md#build-and-image-identity) and [scripts](scripts.md).
Version, source commit/dirty state, wheel hash, closure hash, base/donor digest,
final image ID and selected release are independent facts.

Build helpers run as the rootless service/login identity against new local contexts
and already-present immutable images. They never pull/push automatically. Fetching
pinned public inputs is a separate explicit preparation step without app secrets.
No NAS path, symlinked input/output, partial context or unknown artifact may be
silently reused/deleted. Failed proof contexts and named containers remain evidence.

The protected rootless installer provides distinct modes. These syntax examples
require reviewed local source, authenticated manifest and explicit operator
approval; they do not activate services or provision secrets:

```bash
python3 scripts/install-container-release.py render --manifest /path/to/container-release.json --output /path/to/new-render
sudo python3 scripts/install-container-release.py stage --manifest /path/to/container-release.json
sudo python3 scripts/install-container-release.py switch --version 0.2.1
```

Render creates a new local artifact tree. Stage authenticates sources/recomputed
rendering, fsyncs a complete immutable release and index under `/opt/hfcache/releases`.
Switch additionally inspects both managers, containers/cgroups and protected
bindings under the original noncreating local flock before changing `current`.
Neither operation fixes unknown processes or auto-cleans unexplained artifacts.
A selector replacement followed by parent-fsync failure is uncertain: inspect the
actual link under the guard; exit 20 does not prove selection stayed unchanged.

Before either manager activates the selected release, verify service access to
the public directories and persistent SELinux contexts as described in
[staging prerequisites](containers.md#staging-and-selection). Index/hash parity
does not prove traversal permission or an allowed unit/launcher label. The
rootless installer performs neither host fcontext provisioning nor a policy
exception. Keep secrets/state private and SELinux Enforcing. Run administrative
rootless diagnostics from an accessible working directory such as `/`; an
inherited inaccessible operator home is a diagnostic invocation failure, not
evidence that the API or container failed.

Two libexec links, the system target/bridge and five user unit files bind through
the selected release. Verify all nine exact root-owned symlinks, physical helper
root, authenticated profile/index, effective FragmentPath/drop-ins and both manager
reloads before activation. A changed selector with old running images/helpers is
not a valid upgrade. Rootless worker.socket remains indexed/bound but dormant with
`RefuseManualStart=yes`; targets/API depend on worker.service readiness instead.

The worker is direct Python PID1, creates its protected local private listener and
sends READY only after instance/store/worker setup. User unit Type=notify,
NotifyAccess=all and Podman --sdnotify=container carry readiness; API Requires/After
that service. No inherited LISTEN fields/extra descriptors or credentials are
accepted. Native named-FD3 activation is a different supported mode.

Protect the independent static host read-only guard outside `current`. READY
requires original-lock identity/ownership and the host PID1 NFS-ro observation;
it retains the original flock. It is not continuous mount monitoring. The system
bridge starts the user target only after guard readiness through its protected
local manager connection. Never enable the application from the user default
target or weaken ProtectHome to reach the manager. Any guard handoff requires a
separately reviewed root-held original-lock transition, not a documentation step.

API/worker archive binds remain read-only, without chown/relabel/copyup or write
probes. All graphroot, image, state, cache, Caddy and temporary writes are local.
API gets Hub/REST/MCP sources, client REST writer only, Caddy TLS only, worker none.
API/Caddy use pasta; worker/client use network none, and the worker additionally
permits only native AF_UNIX socket creation under baseline-preserving seccomp.

## Native installation

Use `scripts/install-release.sh` only for a positively classified native prefix.
It refuses container/mixed/partial/unknown selection before manager access,
staging or candidate-code execution. Switch requires an installed built native release; static `--list` bypasses
classification and needs neither source nor runtime. Source-only staging
requires positive project metadata. See the
[script profile contract](scripts.md). Do not point it at the selected container
prefix as an alternative deployment tool.

For an explicitly native provisioning/staging window:

```bash
sudo scripts/install-release.sh --no-switch
scripts/install-release.sh --list
sudo scripts/install-release.sh --switch 0.2.1
```

The installer verifies the uv pin, obtains the pinned interpreter under
`/opt/hfcache/python`, builds the environment in its final release path, syncs the
locked server closure, applies ownership/modes, runs service-independent smoke
checks and relabels local code. A venv built elsewhere and moved retains broken
absolute shebang/home paths. Do not use a service interpreter under `/home` with
ProtectHome. Environment overrides select deliberate trusted layouts/tools;
they never waive classification, quiescence, original locks or retained handles.

Explicit `--with-mcp` stages server+MCP only during build/stage. It is refused with
list/switch, does not enable config/provision credentials/start services and cannot
add dependencies to an existing target. Before enabling native MCP, deliberately
deliver its distinct source as described in [MCP profiles](mcp.md#deployment-profiles).
Base and REST-only installations remain supported.

Install native archive policy as `0640 root:hfcache` at `/etc/hfcache/config.toml`;
server and independent client settings are separate. Validate policy with the
strict loader or `--config PATH config validate --local` without using operational
commands as a local fallback. Deliver `hfcache.api` to API/scheduled observers;
Hub `hf-token` is API-only. Optional MCP-reader is distinct and explicitly enabled.
During a native upgrade, inspect legacy scheduled-client drop-ins for Hub
`ImportCredential=hf-token`. The uninstalled
[legacy reset example](../packaging/systemd/hfcache-sync.service.d/legacy-hub-credential-reset.conf.example)
only clears inherited imports; it provisions no token and is not a normal
installation step. Review/remove obsolete Hub delivery while preserving the
separate API credential. Rootless Podman secret delivery is unaffected.

The verifier imports no credentials and masks standard source/cache stores;
custom source paths require explicit additional isolation proof.

Install/review the native API and verification service/socket pairs plus scheduled
client services/timers and target/mount integration. API activation requires the
exact configured Unix/optional TCP listener set named `hfcache-api`; worker
activation requires the named FD3 listener `hfcache-verification`. Peer identity
comes from the service account or trusted explicit settings, never manager `%U`.
Disabling TCP requires both server policy and a socket drop-in resetting listeners
consistently. One API application adopts all configured descriptors.

Existing archives must not be initialized again. Initialization is a separately
confirmed writer operation behind a disabled-by-default initialization-only gate,
with installed root/UUID equality and known-layout proof. Startup, missing sentinel,
health and recovery never initialize. See [CLI initialization](cli.md#archive-init).

## Upgrade and drain

Stage beside the retained predecessor and verify compatible policy/artifacts before
selection. Record timer state, keys/operation IDs, both stores, pending handles,
archive/sentinel identity, config backup and actual executors.

1. Pause only the applicable schedules under their correct manager, preserving the
   disabled verification calendar and writer masks. Never stop `hfcache.target`
   as a pause shortcut: the native mount is PartOf it.
2. Stop fresh API activation/admission and drain the actual API while the verifier
   stays available for exact surviving outcome handoff. Stopping clients only
   ends observation and retains handles.
3. Drain the verifier and prove actual processes/cgroups/activation ended. Check
   both rootless managers and libpod payloads, or the complete native service/socket
   set. Unknown accounting/status is refusal, not quiescence.
4. Prove no orphan common-lock holder using the original noncreating flock and
   retain it through selection. Never unlink any lock inode or use a free flock
   as sole execution proof. Preserve malformed/uncertain evidence.
5. Select only the matching native/container profile using its installer. Reload
   required managers; verify effective units/drop-ins, helpers/profile/image identity
   and retained-state compatibility together.
6. Reopen compatible services only under the accepted profile/guard. Reconcile exact
   receipts, verify local listener/readiness/auth/identity and deliberate observation
   before any separately authorized workload or schedule restoration.

Forced termination is not clean drain and needs exact incident/run/transaction
handling through [recovery](recovery.md#establish-execution-state). Do not clear
stores/handles or auto-replay. Infinite non-killing drain preserves active work;
a wrapper or client exit alone does not prove payload termination.

## Rollback compatibility

Rollback selects retained application artifacts through the same guarded mechanism;
it does not roll back archive data, erase control history or restore deleted
revisions. Keep at least the predecessor tree. Resolve transactions with compatible
readers before switching. Preserve all independent compatibility domains:

| Boundary | Rollback condition |
| --- | --- |
| Prune checkpoint `containers_removed` (0.1.2) | No prune transaction in flight before rollback across 0.1.2; completed journals remain compatible |
| Nullable corrupt-current findings (0.1.3) | Before 0.1.3, no outstanding null-SHA finding; older derived-catalog readers can lose the degraded signal |
| Failed sync plus warnings (0.1.4) | Before 0.1.4, newest sync report must have an older-valid combination or be superseded by a compatible later report; preserve the mixed report |
| Purge plan/reason (0.1.5) | No purge in flight before 0.1.5; older direct record parsers reject the purge reason even when ordinary post-completion reads work |
| Required Hub scope (0.1.6) | Before 0.1.6, validate explicit optional/public policy and disable restricted fetches; retained restricted publications stay protected/readable |
| Three-revision policy (0.1.7) | Before 0.1.7, explicitly validate maximum_revisions=5; this cannot restore pruned revisions |
| Quarantine cleanup (0.1.8–0.1.10) | Formats remain compatible; older tools lack cleanup and do not restore removed redundant entries |
| API receipts and scheduled handles | Retain separate stores/handles and a compatible observer/reconciler; absent old commands/modules never prove nonexecution |
| Tags and supplemental discovery | Old strict configs refuse even empty tags; old initialization inspection flags the optional namespace, while ordinary inventory can remain readable. Old client receipt allowlists refuse refresh kinds although generic stores preserve them. Require actual target validation, preserved backups/handles and a compatible observer; never delete evidence to force acceptance. See [observed compatibility](discovery.md#observed-pre-feature-compatibility). |
| Optional MCP | Disable deliberately before server-only/pre-MCP startup; no automatic fallback or schema migration |
| Rootless 0.2.0 | Recorded API-to-worker SELinux connection limitation returns; do not weaken policy to bypass it |

Native switch refuses retained scheduled handles if target Python lacks
`hfcache.scheduled_client`; unknown/future/temp/symlink evidence stays preserved.
Custom state/runtime/control-tool paths are trusted operator settings, not a
waiver. A compatible observer unlinks its pending handle only after exact terminal
validation/fsync. See [schemas](schemas.md) and [client lifecycle](api-client.md).

## Acceptance checklist

Repository fixtures establish source behavior under owned conditions. Before an
installed profile is accepted, collect actual evidence for its applicable rows:

| Check | Required evidence |
| --- | --- |
| Artifact/selection | Immutable source/wheel/closure/base/image identities, correct protected index/bindings and effective manager units |
| Listener/readiness | Exact native activation or rootless worker-created listener/notify; actual API-role peer connection, not only a host probe |
| Auth/TLS/prefix | Protected distinct sources, wrong-class refusal, verified off-host HTTPS/public prefix, native Unix trust boundary |
| Isolation | Actual worker PID1 no-IP/credential masks, cgroups, seccomp and enforcing SELinux; no inference from import failure or podman exec alone |
| State/drain | Original lock inodes, both receipt stores and handles preserved; real executor shutdown/result handoff and restart reconciliation |
| NAS/domain | Separately approved mount/sentinel/probe/sync/report/catalog/full-verification and interruption/reconnect workloads |
| Consumer/host | Disjoint export/write refusal, complete copy on another host, reboot/NAS-down behavior, snapshot restore and memory reclamation |
| Cockpit | Actual PAM/privileged bridge, fixed launcher, bounded output and candidate/base/confirmation behavior; blocked controls remain blocked |
| Scheduling | Calendar approved against NAS maintenance and long-run costs; verification remains disabled until that approval |

Start hardening diagnostics with static help/dry-run or selected-property inventory,
not a live-default probe. Native workload mode requires an explicitly owned
disposable target/UUID/lock/acknowledgement and positive native profile. Guarded
read-only profile refuses archive-write probes. Inventory and transient probes do
not certify installed PID1, peer, SELinux, NFS or workload behavior. See
[hardening diagnostics](security.md#hardening-diagnostics).

The [dated deployment status](deployment-status.md) records the narrower local
0.2.1 evidence and outstanding acceptance. No repository gate substitutes for
those host checks. [Cockpit installation](cockpit-plugin/installation.md) and
[operations](operations.md) use the same profile distinctions and safety rules.
