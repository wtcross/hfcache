# Authenticate a fixed host reader independently of the online API

- Decision identity: 150.
- Status: Amended; [decision151](decision-151.md) supersedes only the
  SYS_ADMIN-only engine capability-retention rule. [Decision159](decision-159.md)
  adds a dedicated rootless archive-lock type and preserved API/worker binds.
- Date: 2026-10-21.

## Context and decision

The replacement browser needs the former guarded administrator boundary without
turning the online executor into a privileged host process. Decision141 fixes
that separation. Add one direct foreground root helper, a fixed protected Unix
endpoint, an independent six-category policy and selected-release index, and a
separate bounded unprivileged client. This package implements status and safe
configuration-base reads only. Every write operation remains denied until its
owning package supplies its durable admission, effect and outcome contract.

The [host administration contract](../host-administration.md) defines exact
transport, peer, policy/index, budgets, failure and status requirements. The
helper admits only the actual current API process. Native system MainPID and
rootless container init PID are separate authorities. A same-UID worker,
container exec process, copied index, caller identity claim or matching cgroup
alone grants nothing. Retain a kernel peer pidfd and validate credentials on
every data-bearing fragment, including connected-descriptor handoff attacks.
Rootless projected root credentials require separately established address and
read-only mount provenance; overflow UID alone cannot authenticate an endpoint.

Only Basic human archive/Hub/control admissions gain a fresh helper-policy
requirement, using the former Cockpit category map and an explicit closed map
for previously unexposed maintenance routes. The original bearer and read-only
MCP boundaries remain unchanged. Recheck Basic authority at queue dispatch,
before domain locks or verifier handoff. Keep all helper I/O outside metadata,
operation-store, runner-condition and archive/configuration locks. Fresh checks
are not a lease across later lock waiting; final domain guards remain decisive.
A known pre-handoff denial records a failed original receipt without invoking
worker reconciliation; after possible handoff original uncertainty rules apply.
Original-key/status/result observation remains available when the helper is down.

## Rationale and alternatives

### Dedicated rootless archive-lock metadata (2026-10-29)

[Decision159](decision-159.md) addresses the installed confined guard observer's
metadata refusal after the API/worker shared bind assigned `container_file_t` to
the original lock. Independently label that fixed original inode with its own
coordination type, preserve it in both enabled launchers and permit the helper
only `getattr`. Keep original mixed-ID, inode/FLOCK, manager and process checks,
native behavior and the existing receipt/protocol unchanged. Generic container
payload permissions and automatic repair remain forbidden.

### Separate cardinality and cumulative work bounds (2026-10-25)

The fresh rootless status read completed its fixed container inspection but
exhausted the1024 cumulative file-work counter during final process
revalidation. The original host observer prepares engine authority before and
after the separate child; the child also charges its own bootstrap, preparation
and namespace-entry work. These are real repeated operations, not additional
authority-table entries. Preserve every check and charge. Keep each directory
and authority table limited to1024 entries and allow at most4096 cumulative
file/metadata operations across the original request and its children. The64MiB
byte ceiling,15-second aggregate deadline, individual command deadlines and
eight unqueued exchanges remain unchanged. Do not make repeated reads free or
omit final revalidation to fit the old counter. Fresh installed rootless
acceptance remains required; this changes no operation, permission or hardening.

### Bounded operator failure metadata (2026-10-25)

The generic helper failure and browser acceptance assertion erased the typed
status reason and protected-code failure location needed to distinguish a
failed fixed read from an optional runtime warning. Preserve the browser's
allowlisted status state/reason/profile before applying its unchanged acceptance
assertion. On helper entry failure, keep the generic stderr line and append
bounded builtin error classes, errnos and protected-module function/line frames.
Include explicit causes and suppressed implicit contexts without exception text,
filenames, argv, PIDs, payloads or locals. The host administration contract fixes
the bounds. Observer stderr inherits the daemon journal; engine CLI stderr stays
discarded. Full exception logging would disclose untrusted diagnostics and is
not permitted. These observations change no helper operation, protocol,
endpoint, capability or SELinux permission and do not establish rootless support.

WEB008 extends the same bounded logger to unexpected per-request failures,
including escaped inspection failures after an effect. Invalid-input/peer
protocol refusals and already-answered policy denials remain quiet. Closing an
exchange still preserves the original uncertain operation; logging neither
confirms nor replays it.

### Fixed rootless payload-cgroup refinement (2026-10-24)

The isolated installed Podman6.1 API's original container init and independently
captured exact CID join to a cgroup ending in `libpod-<CID>.scope/container`.
The former scope-only predicate rejects this measured layout. Accept only the
exact inspected full-CID scope or that scope's single fixed `container` child,
without normalizing the retained proof. Arbitrary descendants, CID prefixes,
other scopes and sibling processes remain refused. The original socket pidfd,
API init PID/start, manager, image, argv, UID/GID maps, mounts, namespaces and
security checks remain mandatory. This changes no capability, SELinux or
service-manager grant. Source regressions must cover both allowed layouts and
their independent security denials; fresh installed acceptance remains required.

### Fixed rootless manager session-bus transport (2026-10-24)

The original isolated rootless33 run authenticated the browser and started
its API, but all three baseline browsers received unavailable host status.
Matching Enforcing audit events identify denied writes to the private
user-manager socket. Setting DBUS_SESSION_BUS_ADDRESS alone does not select
the session bus for systemctl show: its local manager transport uses
XDG_RUNTIME_DIR/systemd/private. The fixed observer must set
`SYSTEMCTL_FORCE_BUS=1` for its validated nonzero service UID, retaining
the fixed `/run/user/<UID>/bus` address and the existing native transport.

The source is the systemd v257
[manager selection](https://github.com/systemd/systemd/blob/v257/src/systemctl/systemctl-util.c#L32-L50)
and [private-manager connection](https://github.com/systemd/systemd/blob/v257/src/shared/bus-util.c#L232-L264).
This selects an already configured local metadata transport. It introduces
no manager operation, socket exposure, fallback, SELinux grant or relabel.
The indexed service account remains trusted within its existing rootless
administration boundary; bus claims still require the original fixed-unit,
indexed fragment, invocation, proc, container and socket-pidfd proofs.
Preserve the failed run. Test the actual child environment against ambient
overrides and retain native behavior; require fresh confined manager reads
and installed native/rootless acceptance before completion.

### Fixed session-broker domain compatibility (2026-10-25)

The later [message-authorization amendment](#session-broker-message-authorization-2026-10-25)
supersedes only the prohibition on an unobserved broker `dbus send_msg` grant
below; the connection decision and its original evidence remain unchanged.

The retained isolated rootless34 run selected the session bus, but its baseline
browsers still received unavailable host status. The bounded original audit
window records seven Enforcing `unix_stream_socket connectto` denials from
`hfcache_host_helper_t` to the stock `unconfined_dbusd_t` broker domain. Each
retained event joins an original fixed `systemctl` connect syscall returning
`EACCES`. Current fixed-bus/broker metadata independently show the correct
session-bus inode label and service-account broker in the same target domain.
These observations identify a transport refusal; they do not establish later
manager/peer guards or successful native/rootless acceptance. Keep the failed
run unchanged; unrelated ioctl and certificate-lookup denials do not justify
permissions.

Permit only helper-to-`unconfined_dbusd_t` `unix_stream_socket connectto` for
compatibility with this existing service-account session-broker type. Linux
checks the [peer socket security identity](https://github.com/torvalds/linux/blob/v6.12/security/selinux/hooks.c#L5009-L5038),
separately from the already allowed session-bus socket-file label. The broker's
[separate message authorization](https://github.com/bus1/dbus-broker/blob/v36/src/util/selinux.c#L277-L303)
is not a reason to add an unobserved `dbus send_msg` permission.
This is a type-wide peer-domain permission, not an SELinux restriction to one
pathname or command. The protected fixed account/address, metadata-only argv,
strict parser and independent manager/process/container/socket-pidfd proofs
continue to constrain the application boundary.

Do not add a broker `dbus send_msg` rule, private-manager `user_tmp_t` socket
access, ioctl/certificate permissions, domain transition or capability. Archive,
Hub and credential/secret payload denials and existing helper hardening remain
mandatory. The revised CIL requires the existing fresh root installation
receipt, selected index binding and restart procedure. Source policy tests must
reject extra broker classes/permissions and additional peer types; source tests
alone do not establish confined manager reads or native/rootless acceptance.

### Session-broker message authorization (2026-10-25)

A later retained isolated rootless run uses the corrected inventory and
installed connection rule, yet all three baseline browsers still receive
unavailable host status before recording cases. Its original fixed broker's
journal records seven Enforcing `hfcache_host_helper_t` to
`unconfined_dbusd_t:dbus send_msg` denials in the exact run window. The journal
reporter is the fixed service-account broker; neither the client PID nor the
method is attributed. Current broker effective/permitted capabilities are zero,
including `CAP_AUDIT_WRITE`; that is current metadata, not a historical capability
claim. The failed run, original process handles and other denials remain evidence.

Permit only the additional helper-to-`unconfined_dbusd_t` `dbus send_msg` rule.
The pinned broker [message check](https://github.com/bus1/dbus-broker/blob/v36/src/util/selinux.c#L277-L303)
uses the registry fallback context when no receiver context is supplied and
passes no audit data. Its [driver path](https://github.com/bus1/dbus-broker/blob/v36/src/bus/driver.c#L2439-L2470)
checks authorization before dispatch; `Hello` is a
[driver method](https://github.com/bus1/dbus-broker/blob/v36/src/bus/driver.c#L2348-L2358).
This explains the scope of a possible handshake refusal, not the observed
method. The [message policy](https://github.com/bus1/dbus-broker/blob/v36/src/bus/policy.c#L1076-L1096)
still checks the remaining broker policy after SELinux. The
[audit callback](https://github.com/bus1/dbus-broker/blob/v36/src/util/selinux.c#L306-L339)
and [audit writer](https://github.com/bus1/dbus-broker/blob/v36/src/util/audit.c#L104-L166)
can route denials to stderr when no audit descriptor was opened; zero
`USER_AVC` records therefore do not establish that a message was allowed.

This is type-wide message authority, not a MAC restriction to the selected
UID, bus address, unit, method or read-only request. The protected fixed UID and
address, closed metadata-only argv, strict output parser, original peer pidfd
and indexed manager/process/container checks remain the application boundary;
there is no generic message dispatcher. Do not add reverse message permission,
`acquire_svc`, private-manager socket access, certificate/ioctl rights, capability
or transition. Archive, Hub and credential/secret payload denials and all helper
hardening remain mandatory. Source tests reject the previous connection-only
policy and mutated targets, classes and rights. Fresh policy installation,
receipt/index binding and helper restart precede actual confined manager and
alias/attachment acceptance; these observations alone prove no later guard.

### Search-only endpoint traversal refinement (2026-10-24)

An isolated container using the actual shared UBI10 micro API image and original
helper-parent inode reproduces `EACCES` from the client's `O_RDONLY` directory
open. `O_PATH` succeeds on the same inode under unchanged `container_t` and
`hfcache_host_helper_runtime_t` labels; the probe reads no binding or secret
payload. The intended rule grants directory search, while the client needs only
descriptor-relative lookups and metadata. Use `O_PATH|O_DIRECTORY|O_NOFOLLOW|
O_CLOEXEC` for directory traversal. Preserve every owner/group/mode, inode,
attestation, binding-leaf and peer check. This grants no directory-read, listing,
socket or policy authority and adds no dependency. Retain the original failed
rootless run, require search-only regression tests and fresh installed acceptance.

A direct foreground listener avoids confusing manager-created listener peers
with the accepting helper. A protected API-only directory mount supports exact
parent pinning and normal leaf replacement on helper restart. Independent policy
provisioning avoids automatic expansion of legacy Cockpit grants. Kernel peer
objects and per-fragment credentials resist PID reuse and descriptor transfer;
UID-only checks or browser-supplied process identities do not provide that proof.
No generic manager, engine, shell, filesystem or credential selector is added.

The helper uses only captured trusted standard-library modules. It cannot open
archive payloads or Hub credentials and cannot create IP sockets. Account-switch
capabilities, if required for the fixed rootless read-only observer, are confined
to that measured purpose; initial-USER SYS_PTRACE, process attachment and broader
engine/API mounts are excluded. The namespace-owner read mediation amendment
below does not add a process capability bit or attachment permission.
The existing Cockpit inspection and policy schema remain backward compatible.

A fixed internal guard observer may temporarily use the verified service
account's effective UID/GID to inspect its private lock directory. Its real and
saved IDs remain root, preventing a same-UID native API from tracing or rewriting
the observer. It runs only the indexed original guard predicate, with no Podman,
archive-content or effect operation. The root parent independently brackets the
fixed guard unit's MainPID, invocation and process start identity, and retains
the shared finite inspection budget. No DAC capability or directory permission
expansion is required. A late observer retains its owned slot until actual exit
and supplies no accepted proof.

Rootless helper opt-in is an optional captured build input at the fixed source
path `packaging/containers/host-helper.toml`. If included, its bytes are bound in
the existing release manifest and artifact index. Its exact keys are
`schema_version = 1` and a strict boolean `enabled`, with a 4 KiB limit. Absence
or false preserves the original rendered server bytes. True appends only the
fixed rootless helper configuration and the release's existing service group.
It does not grant a policy category. The independent deployment digest stays
outside indexed server bytes, avoiding a self-hashing release. Runtime schema 1
and original release manifest keys remain unchanged.

## Managed startup and engine observation amendment (2026-10-21)

The system manager must preserve the intended account-switch capabilities into
this fixed entry point. In systemd v257, the seccomp setup path can temporarily
retain privileges and then drop SETUID unless it is in the ambient request;
restoring the bounding ceiling does not restore that permitted/effective bit.
See the immutable upstream [temporary-privilege path](https://github.com/systemd/systemd/blob/70bae7648f2c18010187c9cf20093155eaa26029/src/core/exec-invoke.c#L5274-L5289),
[SETUID drop](https://github.com/systemd/systemd/blob/70bae7648f2c18010187c9cf20093155eaa26029/src/core/exec-invoke.c#L5335-L5344)
and [ceiling restoration](https://github.com/systemd/systemd/blob/70bae7648f2c18010187c9cf20093155eaa26029/src/core/exec-invoke.c#L5550-L5582).
A declared ceiling alone therefore cannot establish the actual process sets.

The managed unit may request only ambient SETUID, within its existing
SETUID/SETGID bounding ceiling. The fixed root entry must clear every ambient
and inheritable bit before protected dispatch, threads or children. Its steady
root effective, permitted and bounding sets are exactly SETUID/SETGID; ambient
and inheritable sets are empty. Native and delegated account observers must
also have empty ambient/inheritable sets. Keep NoNewPrivileges, the namespace
filter, credential/archive masks and AF_UNIX restriction; add no DAC, ptrace,
SYS_ADMIN or SETPCAP capability in the host USER namespace.

### Revised engine capability boundary (2026-10-21)

The initial capless engine proposal below is superseded, not an installed
acceptance result:

> A separate fixed engine child may join only the independently proved service
> account's existing engine USER namespace. It must pin that pause process and
> namespace FD, actual start identity, namespace owner and exact UID/GID maps.
> It never joins MNT, PID or NET. The original host observer stays in the initial
> USER namespace and the helper's masked MNT namespace. Because entering USER can
> reset the bounding set, the engine child must explicitly drop every defined
> bounding bit while SETPCAP exists only in that joined namespace, verify zero
> readback, lock NOROOT/no-setuid-fixup, and clear all effective, permitted,
> inheritable and ambient bits before its fixed Podman exec. Required bounding
> state is zero, never an inferred inheritance of the host ceiling.

The measured capless command failed at Podman's internal namespace setup. The
pinned v6.1.0 [already-entered gate](https://github.com/podman-container-tools/podman/blob/cade97a52ebdf9dbf9e81de8009015776837a074/pkg/domain/infra/abi/system_linux.go#L37-L43)
requires EUID0 and effective SYS_ADMIN, while its independent
[storage initialization gate](https://github.com/podman-container-tools/podman/blob/cade97a52ebdf9dbf9e81de8009015776837a074/libpod/runtime.go#L466-L476)
also depends on effective SYS_ADMIN. Environment markers cannot supply that
kernel fact. Unconfined engine execution, MNT entry, broader host capabilities
and guesses that change keeper/re-exec state are not alternatives.

The following SYS_ADMIN-only replacement requirement is retained as historical
rationale. [Decision151](decision-151.md), dated2026-10-21, supersedes only its
engine capability-retention rule after actual mapped-ID metadata traversal
failed. Its original initial-USER ceiling, USER/MNT ownership proof, masks,
filters, fixed command and separate installed-proof requirements remain current:

> The replacement requirement retains only namespace-local SYS_ADMIN in the
> separate engine child's effective, permitted and bounding sets at its fixed
> Podman execution boundary. It first proves the existing service-account USER
> namespace, pause PID/start/liveness, owner and exact mappings. Before entry it
> captures the helper's masked MNT identity and uses NS_GET_USERNS to prove that
> MNT is owned by the initial USER namespace. Recheck the unchanged MNT after
> entry and close all namespace proof FDs before fixed exec. Never enter or
> create MNT, PID or NET. The original host observer stays in initial USER and
> its original masked MNT; the root daemon still has only SETUID/SETGID there.
>
> After the verified USER join, drop every other bounding bit while namespace
> SETPCAP is available. Lock NOROOT false, NO_SETUID_FIXUP true and
> NO_CAP_AMBIENT_RAISE true (securebits0xCE); then establish effective/permitted/
> bounding SYS_ADMIN only and empty inheritable/ambient sets before fixed exec.
> Retain NoNewPrivileges and all existing filters/masks. Actual tests must show
> MNT unshare and typed/zero-flag MNT entry refused, unchanged MNT/PID/NET and
> archive/Hub/IP denial. These are measured controlled execution boundaries,
> not a claim that arbitrary further USER transitions cannot reset capabilities.
> This revised design still requires prototype and installed functional proof;
> no failed capless result or successful boundary observation establishes support.

Keep this code in the existing indexed peer module and fixed helper entry; no
new module authority, request selector or effect opcode follows. The sole
shipped engine command is read-only inspection of the fixed API container,
with the original predicates and remaining aggregate budget. The fixed engine
invocation may add only the supported `overlay.skip_mount_home=true` storage
option to suppress the storage driver's private-mount housekeeping; it must
preserve independently proved original effective storage options exactly.
The pinned [overlay initialization guard](https://github.com/podman-container-tools/podman/blob/cade97a52ebdf9dbf9e81de8009015776837a074/vendor/go.podman.io/storage/drivers/overlay/overlay.go#L451-L455)
skips that mount, while [CLI option handling](https://github.com/podman-container-tools/podman/blob/cade97a52ebdf9dbf9e81de8009015776837a074/pkg/domain/infra/runtime_libpod.go#L119-L125)
replaces the driver-option list. Therefore an unknown/custom option set refuses
rather than being discarded or silently replaced. This supplies no graphroot,
driver, namespace or daemon change and no generic configuration selector.
Initial support binds the exact measured stock main file plus both protected
RPM vendor directories and their single pinned leaves, with full bounded entry
closure and before/after identities. The seven other applicable override paths
remain absent. Missing/empty vendor bundles and unknown additions refuse; the
presence of a distribution-provided drop-in is not itself custom configuration,
and absence of all vendor inputs is not the supported stock assumption. See the
[exact storage bundle](../host-administration.md) for bytes, modes and digests.
Do not delete or normalize operator inputs to fit this profile.
Diagnostic info
commands, namespace experiments and local source tests do not establish
installed helper/API support; the complete native/rootless acceptance remains
required.

## Mandatory SELinux process isolation amendment (2026-10-21)

Direct systemd masks are necessary but do not establish the required whole-helper
payload isolation. An owned nonsecret fixture demonstrated that the trusted
service-account observer could reach its archive sentinel through the verified
pause process's proc-root link before USER entry, while the direct masked path
was denied. No credential or Hub-secret alias was probed. A successful fixed
engine read is therefore not whole-helper isolation or installed acceptance.

Require SELinux Enforcing and exact
`system_u:system_r:hfcache_host_helper_t:s0` from the first managed exec, before
protected module loading or listener creation. Preserve that domain through all
root, native, mixed-ID, rootless and fixed Podman children. Retain all current
systemd masks, NoNewPrivileges, AF_UNIX, the initial SETUID/SETGID ceiling and the
USER-only namespace restriction. No permissive or unconfined fallback, arbitrary
exec/domain transition, policy administration or relabel permission is valid.

The separately installed policy must deny helper read/open/map of archive/NFS
payload and distinctly typed Hub, API credential and container-secret objects.
This is object-label enforcement, including proc-root/path aliases, rather than
a claim about a path spelling. Native/container roles retain only their required
credential/archive access. Only required helper code, protected configuration,
local runtime/engine and fixed manager/proc metadata permissions are allowed.

The fixed binding verifier needs `systemd_unit_file_t:lnk_file` `getattr` and
`read` to validate a protected unit symlink. It checks root ownership, stable
metadata and the exact indexed `/opt/hfcache/current/…` target spelling before
accepting the binding. These type-wide rights also mediate following a symlink;
SELinux does not encode the fixed pathname. Keep the closed binding list and target-file
permissions, and add no symlink mutation, target-content, execution or manager
control right. Replacing or relabelling a valid installed binding to avoid its
check is rejected. Linux separately checks [symlink target reads and following](https://github.com/torvalds/linux/blob/v6.12/security/selinux/hooks.c#L3054-L3075)
and [inode metadata](https://github.com/torvalds/linux/blob/v6.12/security/selinux/hooks.c#L3161-L3164).

The fixed manager reads require `init_t:system status` when systemd has no
unit-file access context, and `systemd_unit_file_t:service status` when the unit
fragment carries that file type. These are type-wide metadata authorizations,
not unit-name or property-name restrictions. Systemctl requests
[all unit properties](https://github.com/systemd/systemd/blob/70bae7648f2c18010187c9cf20093155eaa26029/src/shared/bus-map-properties.c#L228-L240)
and applies its
[selected-output filter afterward](https://github.com/systemd/systemd/blob/70bae7648f2c18010187c9cf20093155eaa26029/src/systemctl/systemctl-show.c#L2256-L2265).
The protected fixed argv and strict output parser supply the closed application
surface. Permit no additional manager control, reload, start/stop, unit-file
mutation, capability or domain transition. Systemd's
[status access check](https://github.com/systemd/systemd/blob/70bae7648f2c18010187c9cf20093155eaa26029/src/core/selinux-access.c#L224-L265)
uses the unit-file context when known and its own context otherwise. A denied
manager read must be diagnosed from `USER_AVC` as well as kernel `AVC` records;
an unrelated ioctl or certificate lookup denial does not justify a grant.

The mandatory masks and existing writable runtime bind also require the trusted
system manager to attach namespace binds before exec. Add only `init_t:dir
mounton` for the custom secret, Hub-state, archive and runtime object types.
The permission targets an existing directory inode; it does not read its payload
or transfer mount authority to the helper. Existing helper runtime permissions
remain unchanged. This type-wide manager grant is constrained operationally by
the fixed protected unit and root provisioning, rather than by a pathname encoded
in SELinux. Reject startup workarounds that remove a required mask/bind,
revert an object label or grant the helper mount authority.
Keep all helper object/attachment/transition denials and capability/namespace
restrictions. Actual enforcing startup and installed role checks remain mandatory.
Systemd selects an [inaccessible node](https://github.com/systemd/systemd/blob/70bae7648f2c18010187c9cf20093155eaa26029/src/core/namespace.c#L1677-L1708)
or prepares the [existing writable path](https://github.com/systemd/systemd/blob/70bae7648f2c18010187c9cf20093155eaa26029/src/core/namespace.c#L1711-L1727)
and [bind-mounts it](https://github.com/systemd/systemd/blob/70bae7648f2c18010187c9cf20093155eaa26029/src/core/namespace.c#L1871-L1897);
Linux checks [mounton at the target](https://github.com/torvalds/linux/blob/v6.12/security/selinux/hooks.c#L2755-L2768).

Native service compatibility additionally requires the trusted `init_t` manager
to perform directory `setattr` on `hfcache_host_helper_hub_state_t` and file
`read`/`open` on `hfcache_host_helper_secret_t`. Systemd applies `CacheDirectory`
mode/ownership before application exec and reads fixed credential sources in its
credential setup child. Preserve the entire Hub cache label and credential-source
labels. These are type-wide manager rights: metadata changes apply to all
directories with the Hub-state type and opens/reads to all files with the secret type,
including container-secret files. They are not limited to one pathname or unit;
protected units and root provisioning supply the operational restriction. Add no
other manager metadata, directory opens, payload writes, relabeling, capability
or service-control rights, and preserve every helper Hub/secret neverallow and hardening property.
Existing target-policy manager permissions remain separate. Source tests close
this module's explicit manager grants; actual inode/lineage attribution, effective
kernel decisions and enforcing service/negative checks are independent proof.
See [directory setup](https://github.com/systemd/systemd/blob/70bae7648f2c18010187c9cf20093155eaa26029/src/core/exec-invoke.c#L2675-L2731)
and [credential loading](https://github.com/systemd/systemd/blob/70bae7648f2c18010187c9cf20093155eaa26029/src/core/exec-credential.c#L592-L653).
The kernel separately checks file `open` after pathname access checks. Actual
credential-child AVCs, fixed source metadata/device, executor parent lineage and
invocation windows establish the missing `open` right. Effective kernel queries
already allow manager `getattr` and `read`; add only `open`. The AVC's exact
`path=` field supplies source attribution when no separate audit `PATH` record
exists; retain earlier incomplete diagnostic results. This changes no helper
grant or neverallow. See the [kernel file-open check](https://github.com/torvalds/linux/blob/v6.12/security/selinux/hooks.c#L3971-L3995)
and [AVC path formatting](https://github.com/torvalds/linux/blob/v6.12/security/lsm_audit.c#L234-L242).

Shared command initialization constructs the network interface even for fixed
container inspect. Its rootless constructor calls `MkdirAll` for the existing
network-state directory under the proved stock runroot. Permit only
`ifconfig_var_run_t:dir getattr` so it can recognize that directory; a denied
stat must not be worked around with a create/write grant or relabel. This is
type-wide metadata permission, not a pathname restriction or a claim that
network setup is allowed. Keep fixed account/runroot proof, USER-only entry,
INET denial and all file/object/attachment restrictions unchanged. See the
[global initialization](https://github.com/podman-container-tools/podman/blob/cade97a52ebdf9dbf9e81de8009015776837a074/libpod/runtime.go#L554-L561)
and [rootless constructor](https://github.com/podman-container-tools/podman/blob/cade97a52ebdf9dbf9e81de8009015776837a074/vendor/go.podman.io/common/libnetwork/internal/rootlessnetns/netns_linux.go#L90-L98).

The fixed stock Podman command initializes its runtime directory before operator
configuration parsing. Its [shared default initialization](https://github.com/podman-container-tools/podman/blob/cade97a52ebdf9dbf9e81de8009015776837a074/vendor/go.podman.io/common/pkg/config/default.go#L506-L529)
unconditionally calls `chmod(01700)` after finding the existing `libpod`
directory. Correct prewarming cannot eliminate that syscall. Permit only the
additional `user_tmp_t` directory `setattr` needed for this metadata housekeeping;
retain the existing read-only file permissions and all payload/attach/transition
denials. This type permission is broader than the fixed source pathname and is
not a general mutation-free claim about engine read commands. Relabelling the
stock runtime or selecting another directory merely to evade this check is not
the supported alternative. Source review and actual confined execution remain
separate prerequisites.

The same fixed local command's shared initialization requires cgroup-mode
`statfs` metadata. Permit only `cgroup_t:filesystem getattr`: Linux checks the
superblock SID for this operation, so ordinary directory observation does not
authorize it. This adds no cgroup write, mount/remount or namespace permission;
the type grant is not a pathname selector. Retain the fixed cgroup-mode source
query and all existing object denials. See the
[command initialization](https://github.com/podman-container-tools/podman/blob/cade97a52ebdf9dbf9e81de8009015776837a074/cmd/podman/root_cgroups_linux.go#L11-L23)
and [kernel filesystem check](https://github.com/torvalds/linux/blob/v6.12/security/selinux/hooks.c#L2745-L2753).

Overlay initialization likewise needs `statfs` of the existing graph root's
backing filesystem. Permit only `fs_t:filesystem getattr`, retaining every file,
directory-write/create, mount and relabel restriction. This query precedes
`skip_mount_home`; that option skips mount housekeeping, not backing-filesystem
identification. A separate runroot `W_OK` denial only warns and continues, so it
does not justify directory-write permission or relabeling the runtime to avoid
the warning. The grant is type-level superblock metadata access, not a new path
selector. See the pinned
[backing-filesystem query](https://github.com/podman-container-tools/podman/blob/cade97a52ebdf9dbf9e81de8009015776837a074/vendor/go.podman.io/storage/drivers/driver_linux.go#L127-L138),
[overlay call](https://github.com/podman-container-tools/podman/blob/cade97a52ebdf9dbf9e81de8009015776837a074/vendor/go.podman.io/storage/drivers/overlay/overlay.go#L331-L334)
and [warning-only access check](https://github.com/podman-container-tools/podman/blob/cade97a52ebdf9dbf9e81de8009015776837a074/libpod/runtime_linux.go#L17-L33).

Where existing overlay directories carry the engine-managed
`container_ro_file_t` label, preserve it. Existing-directory metadata needs `getattr` and
`search`, with no directory
creation/write, relabel or file-content grant from that metadata rule. The fixed
[overlay initialization](https://github.com/podman-container-tools/podman/blob/cade97a52ebdf9dbf9e81de8009015776837a074/vendor/go.podman.io/storage/drivers/overlay/overlay.go#L343-L355)
uses `MkdirAll` for its existing link directory; its
[existing-directory stat and fallback](https://github.com/golang/go/blob/go1.25.9/src/os/path.go#L19-L64)
can otherwise report `file exists` after denied metadata checks. Changing labels
or deleting/recreating the storage tree to avoid the check would replace the
supported stock input. The type-level traversal grant supplies no generic path
selector and leaves every archive, secret and attachment-class denial intact.

The supported stock backend also requires reading its public mount-program
flag. Permit only `container_ro_file_t:file {getattr open read}`. File metadata
is also required when fixed inspection opens the layer store: its
[metadata reload](https://github.com/podman-container-tools/podman/blob/cade97a52ebdf9dbf9e81de8009015776837a074/vendor/go.podman.io/storage/layers.go#L919-L936)
stats `overlay-layers/layers.json` before reading it and rejects a non-ENOENT
stat failure. No file write/create, map/execute or relabel right follows from
this file grant. This deliberately
allows reading the whole image-file type, not only that flag. Do not describe
it as path-restricted metadata access or a promise that image payloads remain
unreadable. The fixed
[flag reader](https://github.com/podman-container-tools/podman/blob/cade97a52ebdf9dbf9e81de8009015776837a074/vendor/go.podman.io/storage/drivers/overlay/overlay.go#L680-L718)
otherwise falls back to a recursive scan. Do not add further scan/mutation
rights or change stock backend state to evade the flag read; the independent
startup enumeration below has its own required type-wide scope.

Fixed overlay initialization independently calls
[RecoverStaleDirs](https://github.com/podman-container-tools/podman/blob/cade97a52ebdf9dbf9e81de8009015776837a074/vendor/go.podman.io/storage/drivers/overlay/overlay.go#L446-L449).
Its [directory enumeration](https://github.com/podman-container-tools/podman/blob/cade97a52ebdf9dbf9e81de8009015776837a074/vendor/go.podman.io/storage/internal/tempdir/tempdir.go#L119-L182)
requires `container_ro_file_t:dir {open read}` beyond traversal/stat. Accept
this type-wide directory-name exposure explicitly; it is not a fixed-path MAC
rule or a promise of secret filenames. No directory write/create, unlink,
locking, remove-name, rmdir or relabel permission follows. Recovery can attempt
cleanup of matching stale entries, so do not label the underlying command
universally effect-free. Unsupported mutation authority stays denied; locking
errors can be skipped, so command success is not proof of cleanup. Require
actual state/effect evidence; do not add cleanup rights or change stock state
just to satisfy the installed read path.

Retain the categorical archive/NFS, private-secret and Hub-state file
neverallows. This choice is valid only with independent actual-inode proof
that all such data, including future creations and delivered copies, retains
a denied type. Secrets under the permitted image type are unsupported; fixed
source and an image digest alone do not prove their absence. A separate
metadata-only type would require a new stock-file labeling and creation
contract, which this grant does not introduce. Source/class analysis and
installed confinement/credential acceptance remain distinct prerequisites.

Keep image-file and image-directory mutation compile-denied. Stock writable
store construction opens `images.lock`/`layers.lock` with read/write flags before
locking, so blanket `container_ro_file_t` writes would permit payload changes.
Instead, independently provision the separate `hfcache_host_helper_engine_lock_t`
type on exactly the two existing fixed persistent leaves, the existing
zero-byte `/run/user/<protected host UID>/libpod/tmp/alive.lck`, and the existing
64B `/run/user/<protected host UID>/containers/overlay-layers/mountpoints.lock`.
The persistent records remain64B. Both runtime locks are independently
reprovisioned after stock engine prewarming whenever reboot or recreation
produces a new inode. Fixed inspection
[reads the container layer](https://github.com/podman-container-tools/podman/blob/cade97a52ebdf9dbf9e81de8009015776837a074/libpod/container_inspect.go#L23-L31);
[storage chooses the current runroot layer directory](https://github.com/podman-container-tools/podman/blob/cade97a52ebdf9dbf9e81de8009015776837a074/vendor/go.podman.io/storage/store.go#L1165-L1185),
and its [constructor opens the mountpoints lock](https://github.com/podman-container-tools/podman/blob/cade97a52ebdf9dbf9e81de8009015776837a074/vendor/go.podman.io/storage/layers.go#L1280-L1297).
This fourth ordinary leaf uses the same type/receipt role and existing rights;
it adds no general temporary-file write authority. The helper and stock
`container_runtime_t` get only file getattr/open/read/write/lock there, with no
creation, replacement, execution or parent mutation authority. A type grant
covers whole inodes, not an offset range or filename. All four labels and stable
no-follow inode/ancestor identities must be freshly checked before/after the
fixed rootless command; absent, wrong-type/default-recreated objects or changes
observed during inspection refuse. The type-only receipt carries no historical
inode pin, so an otherwise-valid same-type substitution predating capture is not
detected by that receipt; root provisioning and engine-account trust remain. The receipt's single `engine_locks` role accepts no paths, and
native-only use does not require these rootless objects. No generic engine
relabel, alternative store, lock bypass or automatic permission grant is valid.
The [constructor](https://github.com/podman-container-tools/podman/blob/cade97a52ebdf9dbf9e81de8009015776837a074/vendor/go.podman.io/storage/images.go#L592-L620)
and [open implementation](https://github.com/podman-container-tools/podman/blob/cade97a52ebdf9dbf9e81de8009015776837a074/vendor/go.podman.io/storage/internal/rawfilelock/rawfilelock.go#L21-L35)
require this even for existing unchanged lock contents. Lock-record updates are
explicitly allowed metadata effects: later unsupported store repair may still
fail, and neither successful reads nor source inspection prove no writes.

The runtime paths support only an independently established stock runtime epoch.
It does not authenticate the database's `LibpodTmp` field or imply universal
nondefault-path refusal. Pinned Podman6.1's
[`WithTmpDir`](https://github.com/podman-container-tools/podman/blob/cade97a52ebdf9dbf9e81de8009015776837a074/libpod/options.go#L326-L338)
does not set `TmpDirSet`; the
[database merge](https://github.com/podman-container-tools/podman/blob/cade97a52ebdf9dbf9e81de8009015776837a074/libpod/runtime.go#L408-L442)
can override the flag value before validating the merged configuration. Reject
the ineffective-flag alternative. Root provisioning/installed acceptance must
establish the default configuration/database epoch; nondefault state is
unsupported and engine-account trust remains explicit. No database parser,
new dependency, generic temporary-file write or alternate store follows.

Keep shared-memory coordination separate from ordinary lock-file rights. Stock
runtime initialization opens and maps an existing2048-lock segment read/write;
[the pinned C implementation](https://github.com/podman-container-tools/podman/blob/cade97a52ebdf9dbf9e81de8009015776837a074/libpod/lock/shm/shm_lock.c#L222-L285)
uses shared writable mutex state. The twelfth closed type-only receipt role,
`engine_shared_memory`, binds `hfcache_host_helper_engine_shm_t`. Independent root
provisioning labels only the existing fixed
`/dev/shm/libpod_rootless_lock_<protected host UID>` ordinary single-link0600/
82488B segment after genuine stock prewarming. Exact root:root01777 `/dev/shm`
is the only writable ancestor exception, with sticky bit required. Missing,
wrong/default-type or reboot/recreated segments refuse until fresh provisioning.
No automatic creation/relabeling, generic tmpfs rights or backend switch follows.

Only helper and legitimate `container_runtime_t` receive file getattr/open/read/
write/map on the new type. Ordinary-lock map and all payload/image/process/
transition denials remain compile-checked. The type permits whole-segment
coordination writes, not a per-mutex range, filename-only MAC or content-integrity
claim. The observer strictly rejoins full metadata within each bounded O_PATH/
xattr capture; command comparison excludes mtime/ctime while retaining stable
inode, principal, mode, size, link, context and ancestor identity. Mutex writes
may change timestamps. The receipt adds no historical inode pin, and default
runtime/database-epoch and engine-account trust limits remain. Native requires
no shared-memory object. Target compilation, actual prototype and full installed
role acceptance remain separate evidence.

The shared runtime also selects its stock conmon path through file metadata.
Permit only `conmon_exec_t:file getattr`, with no read/open/map/execute or domain
transition grant. The [selection source](https://github.com/podman-container-tools/podman/blob/cade97a52ebdf9dbf9e81de8009015776837a074/vendor/go.podman.io/common/pkg/config/config.go#L972-L997)
applies before fixed container inspection. INFO has a separate version-reporting
command; satisfying that diagnostic is not authority to execute conmon. Keep
the shipped operation fixed to container inspection and distinguish type-level
metadata permission from the protected source's candidate-path selection.
Initial-USER and namespace-local capability classes stay separate. No new host
capability or command selector follows.

The application configuration leaf has a separate shared read-only type;
private helper policy/index/key/receipt objects keep their private type. Do not
make the entire private helper configuration type readable by containers merely
to support `/etc/hfcache/config.toml`. Mutable Hub home and the entire cache root
have a separate helper-denied state type, with only the application's required
state operations. Credential/container-secret types remain read-only inputs.
Validated helper opt-in removes `:z` from exactly the API's existing Hub home
and cache binds, preserving stock/default argv and every other role. This avoids
runtime relabeling away from the independent object-label proof. Require fixed
persistent contexts and actual original/new leaf-label proof across operations
and restart; directory labels alone and source argv tests are insufficient.

### Namespace-owner process-read mediation (2026-10-21)

Opening the independently verified rootless keeper's USER namespace descriptor
uses the kernel's process read check. Across USER namespaces, Linux commoncap
requires SYS_PTRACE authority in the target namespace even when the caller's
effective/permitted/inheritable/ambient sets are empty. The owner EUID in the
parent USER namespace has that implicit target-namespace authority; this does
not add SYS_PTRACE to the caller's initial-USER process sets. See the kernel's
[namespace-owner capability rule](https://github.com/torvalds/linux/blob/v6.12/security/commoncap.c)
and [process namespace read path](https://github.com/torvalds/linux/blob/v6.12/fs/proc/namespaces.c).
An owned enforcing probe reached this exact check with unchanged initial-USER
sets and was refused by SELinux `cap_userns` mediation.

Allow `sys_ptrace` only in the helper domain's non-initial `cap_userns` class,
alongside the existing namespace setup permissions. Keep the initial
`capability` SYS_PTRACE prohibition. This class permission itself is neither a
READ-only nor a pathname/namespace-owner selector; kernel capability rules and
the fixed, bounded keeper/PID/start/map/owner proof remain independent checks.
Add a mandatory neverallow for helper-domain `process ptrace` against every
domain. Linux separately mediates read mode as file read and attachment mode as
process ptrace; opening another process's proc-memory file requires attachment
mode. Require neverallow checks during policy compilation, and verify the actual
target task types belong to the covered domain attribute. This choice avoids
an initial-USER SYS_PTRACE grant or an unconfined observer outside the mandatory
domain. It adds no attach, process-memory, arbitrary-proc or effect operation.
The distinction does not promise denial for same-TGID introspection or a memory
FD authorized elsewhere and inherited earlier. Fixed child launches close
unrelated FDs and the private protocol refuses descriptor transfer. This is not
a general daemon-startup FD-sanitization claim: the actual managed launch's
inherited-FD inventory must contain only its declared channels.

Read-gated proc information remains a separate limitation. In particular,
`/proc/PID/environ` uses read mode and then reads the target address space; a
`process ptrace` prohibition is not universal process-memory secrecy. Supported
API, worker, Caddy and helper processes must deliver authentication/Hub secrets
through the fixed credential files, without secret values in their environments or argv.
Require source checks and actual private environment-hygiene proof for those
roles. An owned public environment sentinel must report permitted or refused
read behavior honestly; raw environment values are never published. Distinct
payload inode labels do not protect a secret copied into proc-visible memory.

The distinction is an architectural requirement, not installed acceptance.
Actual enforcing attachment-class memory-read denial against a positively owned
same-UID initial-USER counterpart and actual resolved archive-inode/FD denial
remain mandatory. No real API/keeper is attached and no real secret is probed.
Preserve every archive/secret object denial, domain-escape prohibition, mask,
namespace restriction and measured capability-set bound.

The selected authority includes `helper_selinux_policy`: native
`packaging/selinux/hfcache-host-helper.cil`, rootless
`host-helper/hfcache-host-helper.cil`, byte-identical to fixed root-owned0644
`/usr/local/lib/hfcache-host-helper/hfcache-host-helper.cil`. The independent
root-owned installation receipt and exact fixed label roles are specified by the
[host contract](../host-administration.md#mandatory-selinux-isolation).
The neutral deployment index pins the receipt SHA. Policy installation or labels
do not grant any of the six independent permissions.

The receipt attests root-admin provisioning, including a kernel-policy SHA at
that time; it is not a current full-kernel-policy hash checked per exchange.
Administrative policy or protected-label changes require a fresh receipt/index
and helper restart. Runtime checks pin the current domain/Enforcing state,
visible fixed labels and captured authority. Hidden original-object label facts
come from that trusted provisioning evidence, not the mask's inaccessible inode.
A naive inherited Landlock layer also denies required cross-domain proc/ns
observations; a layer applied only after proof leaves the earlier gap. Neither
is a substitute for the whole-helper requirement in this design.

Actual enforcing proof must deny direct and alternate proc-root reads of owned
nonsecret sentinels from every relevant helper phase while original peer/namespace
checks, fixed container inspection and full native/rootless API/helper acceptance
succeed. Source policy/tests or earlier INFO results do not establish this.

## Consequences and evidence

Missing, unsafe, stale, unsupported or timed-out authority produces explicit
unavailable/unknown denial, while login/static/bootstrap/ordinary observation
remain usable. A known absent guard confers no permission; independent policy
and actual deployment checks are required. Rootless schedule/observer remain
false. Status does not establish archive health or writable storage.

Unit, actual Unix fragmentation/credential/FD cleanup, API race and real installed
native/rootless tests are required before conformance. No installed support is
claimed by accepting this record. Existing production/NAS/rollout limits stand.
Amends [141](decision-141.md), [135](decision-135.md),
[122](decision-122.md), [127](decision-127.md), [119](decision-119.md),
[138](decision-138.md) and [139](decision-139.md) only for the replacement
transport. Archive/verification, original operation and no-replay invariants
remain unchanged. See [security](../security.md), [server](../server.md),
[API](../api.md) and [container roles](../containers.md).

## Guarded application amendment (2026-10-25)

[Decision154](decision-154.md) defines the narrow configuration writer, shared
legacy guard, durable private outcomes and original-handle read-only observation.
It supersedes earlier assumptions of a wholly read-only helper for this fixed
operation; all unrelated authority and original reasoning remain.


## Fixed host-effect amendment (2026-10-27)

[Decision156](decision-156.md) adds a bounded fixed-route host-action lane,
original-process observer stop, independent durable outcomes and finite diagnostic
reads. It preserves archive serialization, original operation identity and this
record's unrelated requirements. Implementation and actual installed conformance
are separately required.
