# Deploying hfcache on CentOS Stream 10

Choose a deployment profile before selecting tools, paths or service managers.
The [recorded local deployment](deployment-status.md) is rootless 0.3.0 with NFS
read-only and its separately recorded guard setting. This guide describes supported provisioning and acceptance;
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

The web UI's [administrator provisioning guide](web-ui/deployment.md)
describes its optional protected hash source, exact HTTPS origin, explicit
`[web]` asset selection and separate native/rootless delivery. Version 0.3.0
serves authenticated `/ui/` only when enabled with a matching protected
artifact and manifest hash. Static assets belong in the existing pinned UBI 10
micro API image behind the same existing Caddy and Unix upstream; no frontend
image/server or runtime Node is introduced. Caddy must not acquire a global
Basic gate or administrator record. These source requirements do not alter the
installed release or authorize credential/service changes. Basic and web remain
disabled when unconfigured. The indexed native/rootless installers
stage paired UI/backend/helper artifacts only when explicitly selected; the
actual production selection and acceptance are recorded separately. See
[indexed construction and staging](web-ui/deployment.md#build-and-select-a-clean-release).

For a reviewed candidate, use a local immutable artifact disjoint from archive,
configuration, credentials, state, sockets, locks and configured application TLS
material, with root/service-owned nonwritable ancestors and no symlinks. The API
validates identity and captures bytes before operation-store/runner admission;
missing or changed enabled artifacts refuse startup. Replacement requires a
drained restart. See the [shared-Caddy/prefix procedure](web-ui/deployment.md#keep-the-existing-caddy-boundary)
and [startup troubleshooting](web-ui/troubleshooting.md#interface-startup-and-release-changes).
An owned fixture result binds its exact source/wheel/assets/profile. Clean release
packaging, migration and production rollout remain separate.

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
uses pinned uv 0.11.32 and the source `.python-version` value (`3.14.6`),
which uv resolves into its managed installation. The container input separately
pins an authenticated CPython 3.14.6 artifact. Host helper scripts support the
system Python 3.12; the application uses its pinned interpreter.
Explicit full web native installs build against a separate protected
version/source copy of that interpreter with pip/ensurepip omitted; the shared
managed donor and retained runtimes remain untouched. See
[the runtime decision](adr/decision-158.md) and
[web staging](web-ui/deployment.md#select-a-matching-immutable-asset-artifact).

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

Protected web host controls use an independently provisioned fixed policy,
authenticated selected-release facts and the confined helper; the application
never creates its own grants. Missing policy, unsupported target or drift denies
effects. See [web provisioning](web-ui/deployment.md) and the
[host administration contract](host-administration.md).

The selected guarded profile retains archive denial. Explicit permissions in a
disposable fixture permit only submission; existing read-only mounts and API
gates may still refuse the operation. Current rootless bindings do not prove the
system scheduled observer/timer, so schedule and observer permissions remain
denied even if requested by policy. Do not install a native `.venv` client,
redirect to a user unit, alter masks or clear the guard to satisfy this check.
Source implementation does not provision policy, select a release or change
the recorded installed holds. Any deployment/provisioning remains a separate
operator action with its own evidence and authorization.

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

Switching, same-version rebuilding and offline intent activation accept an
intentionally masked unit only when it is inactive. A masked service must still
prove zero main/control processes and no remaining tasks, with the same cgroup
checks as a loaded service. Other unexplained states refuse. Keep legacy writers
and calendars masked; never unmask them to satisfy the installer.

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
and filesystem socket ownership are independently configured below, never
inferred from manager `%U` or a universal numeric service UID.
Disabling TCP requires both server policy and a socket drop-in resetting listeners
consistently. One API application adopts all configured descriptors.

### Native verifier identity

The system manager creates the private listener, then passes it to the original
unprivileged worker. The socket file remains owned by `SocketUser`; Linux kernel
peer credentials identify the listener creator. In this native profile, configure
both server settings deliberately:

| Server setting | Required native value |
| --- | --- |
| `verification.expected_peer_uid` | `0`, the system manager's kernel peer UID |
| `verification.expected_socket_owner_uid` | The measured numeric UID of the actual worker/`SocketUser` account |

Inspect the effective service and socket units, including drop-ins, before
choosing the owner. For the shipped `hfcache` account, the following are read-only
checks; substitute the actual account and path when the reviewed units differ:

```bash
systemctl show hfcache-verification.service --property=User --property=Group --no-pager
systemctl cat hfcache-verification.socket
id -u hfcache
stat -c 'socket owner UID=%u mode=%a' /run/hfcache/verification.sock
```

Use the numeric account result, and verify that the existing socket agrees.
Setting only peer UID `0` while omitting the owner still expects a root-owned
node: omission preserves the previous resolved-peer ownership rule. Do not
change the node to root ownership, replace the acceptor or relax no-follow,
mode, peer or SELinux checks to hide a mismatch. The original worker requires
its own ownership of the manager-created node and its exact named FD3.

These settings require a reviewed drained restart and a server version that
supports the explicit owner field. They do not modify running configuration.
Rootless worker-created listeners retain their existing equal owner/peer policy
and can leave the new setting omitted. Require an actual connection from the
API process to the original worker; a host-side probe or account lookup alone
does not establish installed connectivity. See
[client policy](server.md#private-verifier-client-settings),
[private IPC security](security.md#confined-private-listener-ownership) and
[decision 148](adr/decision-148.md).

Existing archives must not be initialized again. Initialization is a separately
confirmed writer operation behind a disabled-by-default initialization-only gate,
with installed root/UUID equality and known-layout proof. Startup, missing sentinel,
health and recovery never initialize. See [CLI initialization](cli.md#archive-init).

## Protected administrative reader

The optional [host reader](host-administration.md) has a separate root system
service and independent index/policy/key provisioning. Follow the
[operator installation procedure](web-ui/deployment.md#install-the-protected-host-reader)
for exact protected bootstrap copies, native/rootless binding differences,
SELinux runtime-parent labeling and helper-before-API startup. Source availability
does not enable it in the recorded deployment or authorize a host change.

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
Rootless preparation also labels only the two existing fixed64B persistent image/
layer locks, the zero-byte fixed stock runtime alive lock and fixed64B
`/run/user/<protected host UID>/containers/overlay-layers/mountpoints.lock` with
the separate engine-lock type after descriptor-bound metadata proof. Reboot or
recreation of either runtime lock requires fresh root provisioning after genuine
stock prewarming. The four ordinary leaves share one existing role and acquire
no new type permissions or generic temporary-file write authority.
Independent default-runtime/configuration/database-epoch proof is required;
the fixed-path guard does not authenticate `LibpodTmp` database overrides. Preserve image-type mutation denials and refuse absent or
wrong/default-type-recreated locks until reprovisioning. The type-only receipt
does not attest historical inode identity; do not relabel the storage tree or create locks on a
read. The fixed receipt's `engine_locks` role introduces no path selector or
Podman prerequisite for native-only use. See the exact operator procedure.
The distinct `engine_shared_memory` role also needs independent fixed-inode
provisioning after stock prewarm: only the existing account-owned single-link
0600/82488B stock2048-lock segment at its UID-derived `/dev/shm` name. Exact
root:root01777 sticky `/dev/shm` is the sole writable ancestor exception. Keep
ordinary-lock mapping denied; shared mutex coordination alone receives read/
write/map on its separate type. Reboot/recreation requires fresh root labeling,
with no automatic object creation or generic tmpfs grant. Full intra-capture
joins and stable command-wide identity/label checks do not claim unchanged shared
contents or timestamps. The receipt has fifteen base roles and no path selector or
historical inode pin; native-only use acquires no engine prerequisite.
Owned nonsecret alias-denial and full installed API/helper proof remain required;
earlier source/INFO checks alone do not close this requirement.

Optional native schedule/observer effects require the separate
[version2 provisioning procedure](web-ui/deployment.md#optional-native-schedule-and-observer-provisioning):
four fixed labels, the same-bind schedule predecessor directory, an original
host-action guard and a fresh receipt/index. Existing read/configuration-only
profiles keep version1 without new host-effect grants. Neither unit installation
nor label provisioning enables a calendar or authorizes an effect. Guarded
rootless schedule/observer denial and all existing engine evidence remain intact.
Observer stop additionally requires the explicitly installed/indexed fixed
`50-hfcache-observer.conf` context fragment, dedicated confined SDK domain and
optional receipt2 `observer_state` role. Base native units do not explicitly
select that domain, and journal stream context is not process proof. Missing
observer proof denies only that control;
it cannot disable an independently proved schedule grant. Preserve all SDK
pending/lock state during quiescent provisioning and prove the actual manager
and original process contexts before acceptance.

Only the API receives `/run/hfcache-host-helper/api` and only the actual indexed
API process may exchange fixed reads. Caddy/verifier/client have no mount or
administrative capability. Rootless launch uses measured keep-id projection,
never an assumed host UID981. The helper cannot read archive payloads, Hub
secrets or credential stores or create IP sockets. A missing/unsafe helper makes
status unavailable and new Basic jobs denied; original observation stays usable.
Enabled rootless API and worker additionally require independent provisioning of
the original `/run/hfcache/hfcache.lock` as
`hfcache_host_helper_archive_lock_t`, preserving its original inode and
service-owned single-link0600 metadata. Both launchers preserve that bind without
`:z`; helper inspection remains metadata-only. Missing/unsafe labels refuse
rather than creating or repairing the lock. Refresh the selected CIL installation
receipt and deployment/policy bindings before restart. Native labels and existing
receipt roles remain unchanged. Follow the
[fixed-lock provisioning procedure](web-ui/deployment.md#install-the-protected-host-reader)
and [host contract](host-administration.md).
The exact selected helper unit and entry must implement the
[startup capability and engine-observer contract](host-administration.md#managed-startup-and-fixed-engine-observation).
Only bounded ambient SETUID is carried into the managed entry; it must clear
all ambient/inheritable bits before threads or children. Its separate fixed
engine child enters the proved existing USER only. At fixed read-only API
container exec it retains only namespace-local DAC_READ_SEARCH and SYS_ADMIN
in effective/permitted/bounding sets (bits2+21, mask0x200004), with empty
inheritable/ambient sets and securebits0xCE. [Decision151](adr/decision-151.md)
supersedes the SYS_ADMIN-only successor to the capless proposal. Read/search
DAC bypass covers all reachable inodes with mapped UID and GID, not only fixed
metadata; it grants no write or regular-file execute bypass and does not replace
SELinux. Add no initial-USER DAC/SYS_ADMIN; SELinux must never authorize
DAC_OVERRIDE and its bit must be absent at verified steady/fixed-exec boundaries. Use
no chmod, ACL or payload/secret label-access workaround. Prove the masked MNT's
initial-USER owner and actual MNT unshare/entry, archive/Hub/IP and required
inode/FD-alias denials under the revised bits. Never join MNT/PID/NET; keep the
original host observer's initial USER and masked MNT view. Do not
substitute a broader unit, ambient grant or command selector to make inspection
pass. Prototype/source tests do not establish installed helper/API support.
The existing UBI10 micro API image serves the UI, REST and MCP through the same
Caddy; there is no frontend image/server or runtime Node installation.

For guarded managed configuration application, install the matching protected
`host_configuration.py` module and refreshed helper unit/CIL/index/SELinux receipt
as part of the same reviewed helper upgrade. Provision the narrow configuration
directory, private-state and guard contexts, retaining the original flock inode
and any pending/history evidence. The helper adds the existing `hfcache`
supplementary group and fixed `/etc/hfcache` writable bind, without new capabilities
or API writable mounts. Never recursively relabel or clean private outcomes to
unblock an upgrade. Follow the [helper provisioning procedure](web-ui/deployment.md#install-the-protected-host-reader)
and [application interruption procedure](web-ui/configuration-and-tags.md#observe-an-interrupted-application).

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
   set. If the protected host reader is enabled, also stop it and prove its
   original helper/inspector cohort drained before replacing fixed bootstrap
   bindings. Unknown accounting/status is refusal, not quiescence.
4. Prove no orphan common-lock holder using the original noncreating flock and
   retain it through selection. Never unlink any lock inode or use a free flock
   as sole execution proof. Preserve malformed/uncertain evidence.
5. Select only the matching native/container profile using its installer. Reload
   required managers; verify effective units/drop-ins, helpers/profile/image identity
   and retained-state compatibility together. For an enabled host reader,
   explicitly refresh/revalidate the selected release's fixed protected bootstrap
   copies, then prepare/review its index and independent policy binding before
   helper/API startup. The release installers do not perform this bootstrap step;
   follow the [protected host-reader procedure](web-ui/deployment.md#install-the-protected-host-reader).
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
| RepositoryCard schema1 (unreleased) | The isolated 0.2.2 released-source drill preserves cards and keeps status/inventory readable, but its catalog read refuses the new namespace with `HFVER007`/exit40. Preserve adjuncts and a compatible catalog reader before rollback; never delete cards to make the old reader accept the archive. |
| Optional MCP | Disable deliberately before server-only/pre-MCP startup; no automatic fallback or schema migration |
| Protected host reader | For a predecessor with host-reader support, preserve current bootstrap inodes before restoring matching copies/labels and the reviewed release/index/policy binding; retain the original key and six explicit permission values. For a pre-helper target, restore a preserved target-compatible server configuration and keep the helper stopped while retaining its files, policy, receipt, key and evidence. Review SELinux policy compatibility separately; a selector rollback alone is insufficient. |
| Web administration configuration | The exact released0.2.2 / source `1c68501` strict server model rejects newer `host_helper`, `basic` and `web` fields. Preserve the installed original and validate a separate target-compatible server configuration; never discard newer metadata, receipts or private helper outcomes to force old startup. |
| Explicit verifier socket owner | An older strict server rejects the new configuration key. Validate the intended target with a preserved compatible server configuration before selection; do not change socket ownership or discard operation state to force rollback. |
| Rootless 0.2.0 | Recorded API-to-worker SELinux connection limitation returns; do not weaken policy to bypass it |

The README throwaway-archive drill rebuilt the exact recorded released source
`1c685018803a365bbb8b0c1aad4b94709f60e7d7` offline. The rebuilt0.2.2 wheel is
`b88ffd0f8605d2410a16aa17379eb8a31362310f7143ca07dfab8ebf17bb6503`,
with90 installed package files matching that commit. It is not a claim about the
deployed artifact. Actual old CLI status, inventory and catalog reads pass before
the card is added; afterward status/inventory still pass while catalog refuses.
All archive file bytes and full metadata remain unchanged. The fixture's separate
initialization inspection already refuses its populated layout before cards, so
that result is not attributed to the card extension. Exact commands/results:
`/var/tmp/hfcache-web009-format-_h1hjuvg/RESULT.json` (SHA256
`b4c2e6d525f6060aea6e6fb8e92ccd2d1cd8706705388d0b749557f5cf7453d2`).
This is an isolated read/format drill, not production, NFS workload or old-writer
effect acceptance. The [card guide](web-ui/readme-cards.md) describes preservation.

The [interface migration guide](web-ui/migration-and-rollback.md#compatibility-and-backups)
records the later retained-wheel copied-state results, actual old-client TLS
successes/refusals and disposable indexed77/78 rollback scope. Old generic receipt
readability does not supply missing private helper readers or establish safe
rollback with unresolved outcomes; retain their original evidence and a compatible
observer. These observations grant no production selection or data migration.

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
| Scheduling | Calendar approved against NAS maintenance and long-run costs; verification remains disabled until that approval |

Start hardening diagnostics with static help/dry-run or selected-property inventory,
not a live-default probe. Native workload mode requires an explicitly owned
disposable target/UUID/lock/acknowledgement and positive native profile. Guarded
read-only profile refuses archive-write probes. Inventory and transient probes do
not certify installed PID1, peer, SELinux, NFS or workload behavior. See
[hardening diagnostics](security.md#hardening-diagnostics).

The [dated deployment status](deployment-status.md) records the narrower local
0.2.1 evidence and outstanding acceptance. No repository gate substitutes for
those host checks. [Web deployment](web-ui/deployment.md) and
[operations](operations.md) use the same profile distinctions and safety rules.

## Manual writer transition

The accepted [protected writer design](adr/decision-165.md) keeps installation
and selection NFS-read-only. It is not current writer acceptance. Before any
authorized transition, back up/inventory configuration, candidates, credentials'
identities, both stores, dispositions, helper outcomes, browser handles, prior
artifacts and original locks. Stop API admission, drain actual API work while
worker/helper remain available, then drain worker/helper/inspector cohorts and
prove real cgroup/libpod/process quiescence. Retain the original noncreating
archive flock throughout protected selection and mount/guard handoff.

Provision original-intent state offline only through the installer's explicit
prepare-intent-state step; normal startup never creates missing authority and
keeps admission/review closed while safe exact-ID observation remains. Preserve
predecessor data. Bind new immutable runtime mode, independent helper index,
bootstrap, policy and exact Enforcing policy receipt before helper READY. The
writer mode is a separate protected selection, never a browser or ambient flag.

Stage both immutable manifest2 release IDs `<version>-guarded-readonly` and
`<version>-manual-writer`, with identical source/app-image/UI and distinct
runtime/index hashes. Initial deployment and historical-key review run in the
guarded sibling. Before the write transition drain again and select the staged
writer sibling, still NFS-read-only under the original flock. Bind current,
physical release, index, runtime and helper selector_target to that release_id;
never rewrite rendered artifacts in a shared version directory. Compatible
rollback selects the retained guarded sibling with matching helper bindings.

Only then may root change the local persistent mount override and bridge/guard
dependencies and remount the existing connection read/write. Prove exact writer
host/export, mapped ownership, sentinel UUID, reserve/capacity and application
preflight. No archive initialization, manual probe, NAS change, disconnection,
relabel/chown/copyup or confinement relaxation is permitted. Missing prerequisites
stop the transition. Preserve deliberate inactive guard state; a running writer
cannot share its original flock with the lock-holding guard. Calendars remain
disabled and legacy writers masked. Rootless schedule/observer/control grants
remain denied. Startup is current-boot manual: provision runtime parents/lock
labels, verify mode/mount/guard, start helper to READY, then bridge/worker/API/
Caddy and verify actual role rights. Do not claim unattended boot support.

Rollback drains real executors and detached helper cohorts, retains the original
flock, restores NFS-read-only and reviewed mount/bridge/guard settings, and
selects a compatible retained release. Preserve dispositions and a capable
recovery reader; 0.3.1 cannot regain admission by removing new state. Runtime
schema 2 and browser recovery schema 2 must be tested against exact predecessor
source c23abba45f8967d058983043b96843bef62e899a. Unknown effects forbid automatic
rollback/replay. Application rollback cannot undo archive writes or normal Sync
retention. See the [original-intent protocol](job-recovery.md).


### Current-boot protected writer procedure

This is a reviewed procedure, not evidence that a deployment has run it. The
operator must supply fresh host-specific commands and identity receipts.
Stop on missing or contradictory facts; retain every failed/partial artifact.

1. Record the deliberate guard enablement/active state, effective bridge and
   guard fragments/drop-ins, persistent local mount override, actual NFS row
   (excluding autofs), export/host/label, service passwd/home/mapping and original
   archive/configuration/API/worker lock device/inodes. Take the coordinated
   protected backup/inventory described above; retain both stores and browser
   handles without printing secret values. Keep calendars disabled and native
   writers masked. A historical observation or free flock is insufficient.
2. Close admission and stop API activation, drain the real API while worker and
   helper can still report outcomes, then drain worker/Caddy/helper/inspector.
   Inspect actual system/user unit fragments, PID/start/cgroup/libpod cohorts,
   all pending protected effects and detached children. Unknown activity stops
   the procedure. Transfer ownership of the same noncreating archive flock only
   through a freshly proven zero-executor handoff; an installer invocation must
   acquire that flock itself, rather than compete with a separately held open
   description. NFS remains read-only throughout staging/selection.
3. Prepare root-protected manifest2 siblings whose only mode-dependent manifest
   fields are archive_mode/release_id. Compare package version, source commit,
   image IDs, wheel/UI/source bytes exactly. Use the existing installer `stage`
   for each and `switch --version <version>-guarded-readonly` for initial
   selection. Each protected step freshly retains the original flock and proves
   drain/NFS-ro. Verify physical-root/current/index/rendered identity after the
   operation; never edit immutable artifacts or remove a prior release.
4. Before first effect admission, independently install the reviewed CIL and a
   fresh exact helper receipt/index/bootstrap/policy. Provision persistent exact
   fcontexts for both `/run/hfcache/hfcache.lock` and
   `/run/hfcache/hfcache.lock.intent` as
   `hfcache_host_helper_archive_lock_t:s0`, preserving the existing original inode.
   With all executors/helper still drained and NFS-ro, run the matching installer
   `prepare-intent-state --archive-id <configured UUID>` once. Native uses
   `install-release.sh --prepare-intent-state --archive-id <UUID>`; rootless uses
   `install-container-release.py prepare-intent-state --archive-id <UUID>`.
   Native preparation reads the fixed API service's typed credential arrays
   through `busctl` from the existing systemd package: no unencrypted loads and
   exactly the packaged encrypted writer credential are accepted. Human
   `systemctl show` may print those arrays as `[unprintable]`; that rendering
   never proves credential delivery. Missing/unsupported typed metadata refuses
   before state effects, with the canonical startup/no-dropin/source-mask and
   before/after revision checks retained.
   Native preparation accepts only fixed packaged/cached API startup and covered
   credential sources under the reviewed effective verifier masks; custom source
   masks are retained and absent standard stores are optional. Nonstandard native
   archive roots/control-store paths and unsupported API overrides refuse before
   effects. Preserve the exact config/unit/mask/account revision across invocation
   and companion publication. The transient's private runtime bind must hide the
   original archive/API/worker runtime sources. Do not infer real mask/bind
   enforcement from source checks; installed qualification must prove it.
   Inspect coordinated backup hashes, both original store-lock inodes, empty
   disposition authority, new companion ownership/mode/link/label, and original
   archive-lock identity. Missing/partial/prior evidence refuses repair/retry.
5. Under the guarded sibling, provision current-boot runtime parents, preserve
   all fixed labels, reload both managers and inspect effective fragments/drop-ins.
   Start the exact matching helper to READY before bridge/worker/API/Caddy, then
   perform initial installed read-only/recovery acceptance. A no-longer-compatible
   predecessor must remain observation-only; retain every disposition permanently.
6. Before enabling writes, repeat the independent full drain/backup/lock handoff.
   Select the already staged manual-writer sibling through `switch` while NFS-ro,
   rebind the protected helper/index/policy/receipt to its exact release_id, and
   reacquire/retain the same original flock for the separate mount transition.
   If starting through the bridge, remove only its reviewed dependency that would
   start the lock-holding guard, retaining its original bytes and unrelated
   dependencies. Alternatively, preserve that dependency byte-for-byte, keep
   bridge/targets/guard inactive and start the fixed roles individually. Keep the
   guard available. Do not activate the user default target or infer readiness
   from an exited bridge.
7. Root adjusts only the protected local persistent mount override and remounts
   the existing NFS connection rw without unmount/disconnect/NAS changes. Prove
   host/export/mount identity, mapped ownership, unchanged sentinel UUID, actual
   nfs_t label, Enforcing state, available/reserved capacity and application
   preflight through the application path. No manual archive probe or initialization
   is permitted. Provision matching current-boot helper/runtime objects, establish
   helper READY, transfer the retained original lock to actual executors, and
   start fixed roles. Verify API/worker rw archive binds and exact writer/MCS
   domains; worker remains network-none, AF_UNIX-only and secret-free. Caddy/client
   have no archive. Fresh independent archive permission is still required per job.
8. For rollback, first stop admission and drain actual executors and detached
   helper cohorts; preserve unknown outcomes. Reacquire the same original flock,
   restore the reviewed local NFS-ro override/remount and original bridge/guard
   settings, and select a retained compatible guarded sibling with matching
   bootstrap/index/policy/receipt. Preserve the deliberate original guard state,
   dispositions, stores, handles, backups and artifact/inode identities. Recheck
   effective units and helper READY before safe observation. Unknown archive
   effects forbid automatic rollback/replay; application rollback cannot undo
   archive publications or retention.

Runtime/companion recreation after a reboot is a separate manual provisioning
operation under the same fresh drain and protected authority review. An existing
healthy disposition file is preserved; first-activation preparation is never
rerun to recreate a missing companion. No unattended startup claim is made.

### Rootless namespace handoff

A host rw remount can leave an existing rootless pause namespace's archive
mount read-only. Check the actual keeper and payload mountinfo, including both
VFS and superblock access; an intended rw bind or READY notification is not
proof. Preserve a failed container and stop the transition before jobs.

Under a fresh coordinated backup, stop admission and gracefully drain every
application/helper/engine client. Preserve original domain/companion/store/runtime
and engine lock inodes, credentials, all operation history, stopped containers,
images and original namespace evidence. Prove the old pause PID/birth/executable,
namespace ownership and absence of workloads in that namespace. Keep independent
job permissions denied. Never use forced termination to drain a job.

For the observed Podman 6.1 implementation, a separately reviewed, no-option
`podman system migrate` can retire the known inert pause namespace. Its
[implementation](https://raw.githubusercontent.com/containers/podman/v6.1.0/libpod/runtime_migrate_linux.go)
removes namespace handles and the pause record and kills that inert keeper;
it must run only after the workload drain, not to accomplish that drain.
It also has
[container-configuration migration logic](https://raw.githubusercontent.com/containers/podman/v6.1.0/libpod/runtime_migrate.go).
Before effects, retain a coherent private database/sidecar/configuration backup
and review the exact changed fields. Permit only the specifically reviewed
Conmon PID-file path migration when necessary; retain original configuration
records and every stopped CID. No runtime change, database migration, renumber,
reset or prune flag is authorized. Recheck the installed version and its actual
semantics; unexpected changes or incomplete backup/closure stop the procedure.

Do not manually unlink the canonical pause record, signal arbitrary PIDs,
remount inside a container, or weaken capabilities, seccomp or SELinux. After
turnover, verify original engine lock/SHM inodes and labels by metadata only;
never read, hash or map those bodies. Create the replacement namespace through
normal rootless engine startup from the proven host mount view. Authenticate
its new PID/birth/maps/namespace, preserve the old evidence and supersede the old
actor snapshot explicitly. Rejoin actual mount flags before helper READY and
ordered role startup. A mount change is not a durable-format activation or
permission grant; do not repeat disposition provisioning or replay any job.
