# Protected host administration contract

The host reader ships in 0.3.0. Installed support
requires the native and rootless acceptance described here. Status is a bounded
administrative observation; it does not establish archive health, writable
storage, workload permission or operation completion. Human setup and use are
covered by the [administration guide](web-ui/administration.md).

## Fixed authority and compatibility

The online API remains unprivileged. One direct foreground host helper owns
`/run/hfcache-host-helper/api/helper.sock`. Only the actual fixed API process
can use it. No request selects a path, manager, unit, engine, UID, credential,
archive or executable. Caddy and the verifier have neither its mount nor peer
permission. Host scheduling remains the system manager. Rootless scheduling
and observer changes remain denied while their fixed bindings are unproved.

The root-owned web policy is independent of historical interface policy. There
is no automatic migration or grant. Existing fixed inspection response and
profile schemas remain unchanged. An unavailable helper never supplies a local fallback
or a bearer administrative grant. Login, static assets, bootstrap, ordinary
metadata and original operation observations do not call the helper.

## One protected exchange

Protocol1 uses AF_UNIX/SOCK_STREAM and exactly one request and response per
connection. A frame is a four-byte unsigned network-order length followed by
strict UTF-8 JSON, with encoded length1..2097152. Client half-closes its write
side after the request; server must observe EOF at the exact boundary before
dispatch. Early EOF, trailing bytes and additional frames refuse. The client
requires exact response identity and final EOF and never retries automatically.

Request keys are exactly `schema_version`, `request_id`, `operation`, `body`.
Version is integer1, never a boolean; request_id is32 lowercase hexadecimal
characters. Implemented `status` has an exact empty-object body. `config-read`
accepts either the legacy empty object or exactly
`{expected_archive_id,expected_archive_root}`: a canonical lowercase UUID and a
bounded absolute root spelling, both strict strings. The pair supplies comparison
values only; it never selects a path to open or adds filesystem authority.
Read-only `config-prepare` accepts exactly `{base_revision,edits}`, using the
closed managed edit grammar and bounds in the [API contract](api.md#managed-configuration-form).
Fixed `config-apply` accepts only the bound application identity/managed edits
specified below; `config-outcome` accepts only operation ID and request digest.
Unknown keys, versions and operations refuse. Fixed `schedule-validate`,
`schedule-change`, `schedule-outcome`, `observer-status`, `observer-stop`,
`observer-outcome` and `journal-read` use the separately specified strict bodies
and independent protected grants below. No descriptor passing is supported.

Response keys are exactly `schema_version`, `request_id`, `operation`, `outcome`,
`body`, `reason`; identity equals the original request. Outcomes are `ok`,
`denied`, `unavailable`. Only ok carries an operation-specific body and null
reason. Other outcomes carry `{}` and a fixed reason from `peer-refused`,
`invalid-request`, `busy`, `timeout`, `policy-missing`, `policy-invalid`,
`deployment-unverified`, `facts-unavailable`, `operation-denied`,
`config-unavailable`, `config-conflict`, `internal-unavailable`. Malformed unauthenticated input
may be closed without a response; never echo it or raw exceptions.

Decoding rejects duplicate keys, nonfinite numbers, invalid Unicode, nonobject
roots, coercion and unknown fields. Bound nesting to32 and total JSON nodes to
100000 before expensive model validation. Numeric tokens have at most128 characters; integers fit signed64 bits and
floats are finite. Strings remain within the encoded frame limit. One absolute20-second server deadline covers the
exchange, with at most3 seconds receive,15 seconds aggregate inspection and2 seconds
response, all capped by the remaining overall time. The receive budget starts
after first peer inspection; both peer inspections and dispatch share the15
seconds, rather than receiving independent inspection budgets. Partial I/O never resets a
budget. The client has one22-second overall deadline including connect/EOF.

Each side admits at most8 exchanges with no queued exchange jobs. Separate
helper inspection/client execution capacity must not consume the API metadata
or authentication pool. Reserve before submitting private executor work. On
cancellation close the exact owned socket promptly; retain its slot until the
actual worker exits. A timeout does not prove a nonpreemptible local read drained.
Shutdown joins owned jobs and exposes uncertain ownership rather than claiming
quiescence. Aggregate incoming frame buffers cannot exceed8 frames.

## Kernel identity and protected address

Set SO_PASSCRED on the listener before accept and verify it on accepted sockets.
Use recvmsg with MSG_CMSG_CLOEXEC for every header/body/EOF receive. Every
nonempty fragment requires exactly one native SCM_CREDENTIALS matching the
independently authenticated API TGID/UID/GID. EOF may carry synthetic kernel
credentials; inspect its ancillary shape but do not treat them as a writer.
Dispose every actually received SCM_RIGHTS descriptor before refusing rights,
malformed credentials, truncation, unknown ancillary controls or later errors.
Unexpected SCM_PIDFD descriptors are closed and refused. Never enable descriptor
passing or interpret unknown bytes as descriptor numbers.

SO_PEERPIDFD (Linux UAPI77) must return the socket's original peer object; no
numeric pidfd_open fallback is permitted. Retain its non-inheritable FD through
the exchange. Check poll liveness and fdinfo namespace PID against SO_PEERCRED,
actual process start identity and the fixed manager/container facts before
parsing and immediately before dispatch. Unsupported kernel or unreadable
required facts refuse. Do not signal/reap the peer, use pidfd_getfd, add
initial-USER SYS_PTRACE, perform process attachment/memory access, dereference
proc-root or weaken API/worker hardening.

Rootless fixed manager inspection runs as the independently indexed service
account. Its closed environment sets `SYSTEMCTL_FORCE_BUS=1`,
`XDG_RUNTIME_DIR=/run/user/<UID>` and
`DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/<UID>/bus`. Ambient bus or
storage variables do not select another endpoint. Native inspection keeps
its system-manager transport. This avoids the private user-manager socket;
it adds no manager operation, SELinux grant or socket mount.

The session bus is the existing service-account transport, not new peer
authority. Its claims are accepted only after the indexed unit fragment,
invocation, kernel process/container facts and original API socket pidfd
agree. The protected-file no-follow rules below remain mandatory; stock
systemctl opens the fixed bus path, so do not describe that connection as
an additional no-follow inode authentication check. The rootless engine
owner remains inside the existing trusted administrator boundary.

Native proof binds the fixed system hfcache-api.service MainPID/start,
InvocationID, cgroup, exact selected indexed entry point, applied fragment and
allowlisted drop-ins. Rootless proof binds the fixed hfcache-api user service
and actual hfcache-api container State.Pid/start/CID/image/role/mount/security
facts, kernel NSpid/UID/GID maps, cgroup and namespaces. The Podman MainPID is
not the API PID. A separate podman-exec TGID fails even inside the same container.
The API init's cgroup must end in the complete inspected
`libpod-<64-character CID>.scope` component, optionally followed by the single
fixed `container` component used by the supported stock Podman layout. Preserve
the original path in the peer proof. Other children, deeper descendants, CID
prefixes and another container's scope refuse; a matching path alone is never
sufficient process authority.
Engine-owner administration is trusted; this boundary cannot prevent that
administrator injecting into an already authorized API process.
Native proof likewise authenticates the original API process, not the integrity
of its in-process code. A compromised native same-account process that can
already inject into that API through host debugging/memory permissions crosses
that trust boundary. Do not describe direct same-UID socket refusal as protection
against code injection into the authorized TGID. Root-owned native inspection
prevents a separate caller from forging its own manager proof; no Yama setting
or SELinux denial is assumed without actual installed evidence.

The client pins all no-follow directory components with Linux `O_PATH` handles
and retains the exact helper parent for its API lifetime. These handles need
search access without permission to read or list directory contents. Binding
files still use readable descriptors and their complete metadata checks.
Native root ownership and rootless projected ownership are
explicit protected startup facts. A projected root helper may have PID0 and
UID/GID65534; that tuple is only a consistency check. The protected deployment
index and actual API-only read-only directory mount establish its provenance.
Only the exact mount root may use the projected owner, never arbitrary ancestors.
Check the socket's type/owner/group/mode/dev/inode before and after connect.
Legitimate helper restart may replace its leaf in the same pinned parent.
Parent replacement, boot/index drift or fake overflow-UID endpoints refuse and
require a fresh trusted API startup. Both client profiles also retain the original socket peer pidfd and require
liveness through completion. The rootless client permits only its independently
attested exact PID0/UID65534/GID65534 tuple and fdinfo Pid0; the server continues
to require positive API host PID. Never perform numeric pidfd_open(0). Native
client identity uses the protected binding PID and kernel original live peer
object; it does not read another UID's masked /proc/PID/stat. Start ticks in that
binding are root-attested diagnostics. The verifier transport remains unchanged.

## Managed startup and fixed engine observation

The system unit bounds capabilities to SETUID/SETGID and requests only ambient
SETUID to preserve that intended bit through manager startup. The fixed root
entry must clear all ambient and inheritable bits before protected dispatch,
threads or children. Verify steady root effective/permitted/bounding
SETUID+SETGID, empty ambient/inheritable sets, NoNewPrivileges and the original
seccomp/masks. A bounding ceiling alone is insufficient. Native observations
remain in the initial USER namespace; every delegated branch retains empty
ambient/inheritable sets. The mixed-ID guard observer keeps its separate
real/saved-root and effective-service-account contract below.

Only a separate fixed engine child may join USER, through a retained FD for
the actual existing pause process of the independently indexed service account.
Require its positive PID/start identity, pidfd liveness, namespace owner and
exact protected subuid/subgid mappings before and after capture. No caller
selects that process, account, path or namespace. Never join MNT, PID or NET;
the original host observer remains in its initial USER namespace and the
helper's masked MNT namespace. The helper unit permits only typed USER entry.

The earlier all-zero and SYS_ADMIN-only engine capability rules are superseded
only at the separate engine execution boundary by
[decision151](adr/decision-151.md). Stock Podman needs effective SYS_ADMIN for
already-entered setup/storage and DAC_READ_SEARCH for metadata traversal through
mapped subordinate-ID-owned0700 layer directories. Initial-USER authority stays
unchanged: root has only SETUID/SETGID; the account observer has empty effective,
permitted, inheritable and ambient sets. Neither receives initial-USER
DAC_READ_SEARCH, DAC_OVERRIDE or SYS_ADMIN.

Before joining USER, capture the masked MNT identity and use NS_GET_USERNS to
prove its owner equals initial USER. Recheck that the same masked MNT remains
after the transition; close all namespace proof FDs before fixed exec. After
entry, drop every bounding bit except DAC_READ_SEARCH and SYS_ADMIN while
namespace-only SETPCAP remains effective, then verify exactly bits2 and21
(mask0x200004). Clear ambient capabilities. Lock NOROOT false, NO_SETUID_FIXUP
true and NO_CAP_AMBIENT_RAISE true (securebits0xCE) before dropping SETPCAP.
Establish and verify that exact effective/permitted/bounding mask with empty
inheritable/ambient sets before fixed Podman exec. These capabilities exist only
in the proved service-account USER namespace, never in the MNT owner's initial
USER. SELinux never authorizes DAC_OVERRIDE; require its bit absent after
trusted reduction and at every verified steady/fixed-exec boundary.

NoNewPrivileges, seccomp/filter count and the original masks remain unchanged.
Required actual negative observations include unshare(MNT), typed MNT and
zero-flag setns refusal, unchanged MNT/PID/NET and archive/Hub/IP denial.
An exact two-bit execution snapshot is not a lifetime claim against arbitrary
later USER transitions, which can reset capability state. Unknown or unproved
state refuses; do not widen host capabilities, MNT permissions or command
authority. Prototype success does not establish installed support.

### Mapped inode read and search amendment (2026-10-21)

DAC_READ_SEARCH bypasses directory read/search and regular-file read DAC checks
for every reachable inode whose mount-transformed UID and GID both map into
the current USER namespace. Its scope is not limited to one path, layer or
metadata file. It does not bypass write or regular-file execute DAC checks,
and SELinux checks still apply. Require the retained exact UID/GID mappings;
ownership by an unmapped ID supplies no such authority. See the pinned
[mapping checks](https://github.com/torvalds/linux/blob/v6.12/kernel/capability.c#L475-L499)
and [DAC checks](https://github.com/torvalds/linux/blob/v6.12/fs/namei.c#L406-L448).
Do not change filesystem ownership, chmod/ACLs or payload/secret label access
to avoid this rule. No initial-USER DAC capability is introduced.

Do not describe file-handle access as universally requiring an initial-USER
capability. Linux6.12 has a conditional directory-handle path involving
filesystem or eligible mount-owner SYS_ADMIN, current-USER DAC_READ_SEARCH and
mapped ancestry. The retained initial-USER-owned MNT and host filesystem do
not acquire engine-USER ownership through this join; other reachable objects
still need separate review. The capability also participates in an empty-path
link check without granting destination write or MAC authority. These are
ancillary syscall limits, not new command or descriptor selectors; see
[decision151](adr/decision-151.md#consequences-and-required-proof).

Keep Enforcing helper-domain archive/Hub/secret inode denials and attachment-class
process denials. After changing the retained bits, repeat the applicable owned
nonsecret direct/inode-alias/FD and process-read negative observations, with
kernel-event attribution where required. No actual secret may be probed. A
kernel permission query, source test or earlier SYS_ADMIN-only result does not
establish these actual denials or complete native/rootless helper/API acceptance.

The internal fixed engine branch replaces only that child with the base
invocation `/usr/bin/podman --remote=false container inspect hfcache-api`.
Its sole supported extra housekeeping option is
`--storage-opt=overlay.skip_mount_home=true`, which suppresses storage's private
bind-mount attempt without permitting that mount. Because CLI storage options
replace the effective driver-option list, independently prove and preserve the
original effective options exactly in the fixed invocation. For a supported
stock configuration whose sole effective option is `overlay.mountopt=nodev`,
include `--storage-opt=overlay.mountopt=nodev` as well. Do not assume that
configuration for other hosts. Unknown/custom options, unavailable configuration
or a changed configuration refuse; never discard or normalize them. No new
configuration path selector, graphroot, backend, daemon setting or MNT
permission follows. These fixed options require actual engine read proof before
installed adoption.

The protected rootless deployment index may additionally bind `account_home`
inside `profile_evidence`. Its only accepted values are `/var/lib/hfcache` and
`/var/lib/hfcache/container-home`; omission retains the first value. This is a
closed compatibility choice, not a path or engine-store selector. Native remains
fixed to `/var/lib/hfcache`. The measured `hfcache` passwd UID, GID and home must
match the protected principal/home and indexed runtime principal before bootstrap,
peer observation, engine preparation and fixed execution; the original observer
rechecks the same home after its owned child drains. Unknown, mismatched or changed
account inputs refuse before another store or Podman fallback is attempted.

The fixed clean `HOME`, two user override paths and two persistent engine-lock
paths derive only from that bound value. Four engine locks retain their exact
owner, mode, size, inode and dedicated label checks. The helper masks both exact
possible secret-store directories and permits only the two fixed optional engine
coordination roots; it never grants all of HOME. Independently provision the
existing secret/lock labels on the selected store without moving, rewriting,
cleaning or probing an unselected store. Preserve current account/store data.
The fifteen-role receipt and runtime/container-release schema remain unchanged.
Older helpers refuse the additional protected index field; rollback requires
preserving/restoring the exact predecessor index/bootstrap and its compatible
account home, not dropping the field to make an incompatible account pass.

The initial supported storage configuration is the independently measured
Podman6.1 stock `/usr/share/containers/storage.conf`, SHA256
`322dffd5a543bb9e1ca9c67cc56999c62b746118674d004180fe60dddfc21979`,
whose effective driver option is exactly `overlay.mountopt=nodev`. The supported
bundle also requires both measured vendor directories from
`containers-common-6.0-3.el10.noarch`:

| Fixed vendor directory | Sole ordinary leaf | Bytes | SHA256 |
| --- | --- | --- | --- |
| `/usr/share/containers/storage.conf.d` | `00-vendor.conf` | 29 | `358b7ba3201aea7dba1d8e0e42c8a11e21acdff1b2ca71a4f8b826f41ae5bc80` |
| `/usr/share/containers/storage.rootless.conf.d` | `00-vendor-rootless.conf` | 186 | `f346071a81b5fdb96796397b08f9dc40c9f450166c7f041ddcaa92f115e92ca8` |

The preserved production host uses Podman6.0.2 with all three exact stock hashes
above. Its 0.3.0 migration passes actual confined API-origin HostStatus and managed
configuration reads with the bound existing home/store. This qualifies that
observed fixed profile; matching configuration bytes alone would not establish it.
No package update, broader version guarantee or relaxed source check follows.
New-host all-phase IP/inode-alias negative companion acceptance remains separate;
see the [recorded deployment scope](deployment-status.md).

Both directories must be root0:0/0755, each with exactly its named root0:0/0644,
single-link leaf. Fresh bounded no-follow capture checks every entry, exact
bytes/hash and stable directory/leaf identities before and after the command.
Missing or empty vendor directories, extra names, links, different bytes, unsafe
metadata or drift refuse. These fixed files preserve the stock overlay driver
and `nodev` setting; they do not authorize arbitrary drop-ins or discard options.
The other seven applicable main-file/user/system/account-specific override paths
remain absent, including the proved host UID's subdirectory beneath each
`storage.rootless.conf.d`. The fixed clean environment excludes storage/config
path and option overrides. This initial exact bundle is not a claim about all
Podman installations. A different stock revision, custom configuration or
unproved input is unsupported and refuses the read. Preserve operator
configuration; never remove or rewrite it to make status pass.

No shipped info operation, command/container selector, mount-namespace entry or unconfined
fallback is permitted. Before exec, retain bounded private accounting and
kernel/source proof; the host observer validates it, removes it from the raw
inspect bytes and applies the unchanged fixed container predicates. Bootstrap,
metadata, subprocess bytes and elapsed time remain in the original shared
budget. This uses the existing indexed peer module and helper entry, adding no
module role, public protocol operation or policy grant. Prototype diagnostics
are separate evidence; installed API/helper functional acceptance is mandatory.

## Mandatory SELinux isolation

Every supported helper execution requires SELinux Enforcing and exact context
`system_u:system_r:hfcache_host_helper_t:s0` from the first managed exec. Check
this before protected module loading or listener creation, including every
internal observer entry. All helper children and the fixed Podman exec retain
that domain. Preserve masks, NoNewPrivileges, the account-switch ceiling and the
USER-only namespace restriction; no unconfined/permissive fallback is allowed.
The policy denies read/open/map of archive/NFS payload and separately labelled
Hub, credential and container-secret objects, including aliases. It grants only
required fixed helper inputs, local engine/runtime and manager/proc metadata.
No arbitrary domain transition, relabel or policy-administration right follows.

Protected systemd bindings may be symlinks. The helper requires only
`systemd_unit_file_t:lnk_file` `getattr` and `read` to inspect their metadata and
target text. It still verifies root ownership, unchanged inode metadata and the
exact indexed target. The permission applies to that SELinux type generally;
the fixed verifier supplies the pathname restriction. The link `read` right also
mediates following a symlink, with separate target-file permissions. It grants no link
creation/change or additional target-file access. Preserve a valid binding's
type and spelling when diagnosing startup refusal.

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

The existing service-account session bus may have a broker in
`unconfined_dbusd_t`. Permit only helper-to-that-domain
`unix_stream_socket connectto` and `dbus send_msg`, retaining the existing
`session_dbusd_tmp_t` socket-file rights. Linux checks the
[peer socket SID independently](https://github.com/torvalds/linux/blob/v6.12/security/selinux/hooks.c#L5009-L5038);
the broker separately checks
[message authorization](https://github.com/bus1/dbus-broker/blob/v36/src/util/selinux.c#L277-L303),
including its driver/fallback destination before method dispatch. These are
type-wide connection and message rights: SELinux does not select a pathname,
UID, unit, method or read-only operation. The protected indexed UID/bus address,
closed metadata argv, strict parser and original independent peer/manager/
process/container proofs supply the application restrictions. There is no
generic message dispatch, reverse message or service-acquisition grant.
Private-manager `user_tmp_t` socket access, file/ioctl rights, capabilities and
transitions stay unchanged. A changed CIL requires fresh root installation
evidence, matching selected index and helper restart; actual confined reads
and payload/attachment denials remain required. When the broker cannot write
audit records, original service-journal SELinux messages may carry the denial;
absence of `USER_AVC` alone does not show that a request was allowed. A journal
reporter PID does not identify the sending client or its method.

The trusted system manager must install every inaccessible-directory mask and
the existing writable runtime bind before helper exec. For those attachments, permit only `init_t`
directory `mounton` on `hfcache_host_helper_secret_t`,
`hfcache_host_helper_hub_state_t`, `hfcache_archive_t` and
`hfcache_host_helper_runtime_t`. This authorizes the manager to attach a required
mask or runtime bind over a target; it grants the helper no additional mount,
payload or runtime-object right. The permission applies to each type, while
the protected unit fixes the credential/container-secret, Hub home/cache and
archive masks plus `/run/hfcache-host-helper` writable runtime. Preserve the
masks, object types, existing runtime rights and helper denials rather than
removing a bind or reverting a label to make startup pass. The system manager
remains a trusted root authority. This rule alone proves neither that namespace
setup completed nor that the helper or an installed role is supported.
See the pinned [inaccessible-node selection](https://github.com/systemd/systemd/blob/70bae7648f2c18010187c9cf20093155eaa26029/src/core/namespace.c#L1677-L1708),
[writable-path preparation](https://github.com/systemd/systemd/blob/70bae7648f2c18010187c9cf20093155eaa26029/src/core/namespace.c#L1711-L1727),
[bind mount](https://github.com/systemd/systemd/blob/70bae7648f2c18010187c9cf20093155eaa26029/src/core/namespace.c#L1871-L1897)
and [kernel target permission](https://github.com/torvalds/linux/blob/v6.12/security/selinux/hooks.c#L2755-L2768).

Native service setup also runs in the trusted manager's `init_t` domain before
application exec. Retain the Hub-state label on the entire cache root and the
secret label on credential sources. The module additionally grants only
`init_t` directory `setattr` on `hfcache_host_helper_hub_state_t` for systemd's
`CacheDirectory` mode/ownership setup, and file `read`/`open` on
`hfcache_host_helper_secret_t` for fixed credential delivery. These grants are
type-wide: manager metadata changes cover every directory of the Hub-state type,
and manager opens/reads cover every file of the secret type, including container-secret
objects. The protected units and root provisioning supply the intended paths;
SELinux does not encode those paths or limit these grants to one service.
Existing target-policy metadata permissions remain separate; this module
adds no further directory search/open or file getattr permission for this
setup. It grants the helper no Hub/secret access and adds no manager file write,
creation, relabel, service-control or capability right. Do not replace these
labels, remove credential delivery or alter unit hardening to bypass a startup
refusal. Diagnose the actual inode and executor/credential-child lineage before
attributing an AVC. See the pinned
[directory setup](https://github.com/systemd/systemd/blob/70bae7648f2c18010187c9cf20093155eaa26029/src/core/exec-invoke.c#L2675-L2731)
and [credential source read](https://github.com/systemd/systemd/blob/70bae7648f2c18010187c9cf20093155eaa26029/src/core/exec-credential.c#L592-L653).
A native `243/CREDENTIALS` failure can result from a separate file `open`
denial even when `read` is allowed. Join the credential loader's PID/PPID,
invocation window and exact source inode/context before changing permissions.
Kernel file-open AVCs carry the source in `path=`; a separate audit `PATH`
record is not guaranteed. Compare the exact field and device to the protected
source metadata. See the [kernel file-open check](https://github.com/torvalds/linux/blob/v6.12/security/selinux/hooks.c#L3971-L3995)
and [AVC path formatting](https://github.com/torvalds/linux/blob/v6.12/security/lsm_audit.c#L234-L242).
Actual enforcing service startup and helper inode denials remain required.

Fixed rootless command initialization also recognizes the existing
`/run/user/UID/containers/networks/rootless-netns` directory, derived from the
verified account and stock runroot. This directory can retain
`ifconfig_var_run_t`; permit only directory `getattr` for that type.
The unconditional `MkdirAll` first stats an existing directory and returns
without creating it. A denied stat can instead reach its mkdir fallback and
report `file exists`; that is not authority to create, replace or relabel the
directory. The type grant is broader than the fixed pathname, so retain the
independent stock configuration proof and fixed code. It grants no directory
search/enumeration, write/create, file access, network authority or NET/MNT entry.
See the pinned [global network initialization](https://github.com/podman-container-tools/podman/blob/cade97a52ebdf9dbf9e81de8009015776837a074/libpod/runtime.go#L554-L561),
[rootless directory constructor](https://github.com/podman-container-tools/podman/blob/cade97a52ebdf9dbf9e81de8009015776837a074/vendor/go.podman.io/common/libnetwork/internal/rootlessnetns/netns_linux.go#L90-L98)
and [existing-directory recognition](https://github.com/golang/go/blob/go1.25.9/src/os/path.go#L19-L64).

The stock rootless keeper record `/run/user/UID/libpod/tmp/pause.pid` may retain
`user_tmp_t`. The helper policy permits only file `getattr`, `open` and `read`
for that type. SELinux type permissions do not encode a pathname: the fixed
reader separately derives the account's path, bounds it to64bytes, refuses
symlinks, and verifies owner/group, single link, mode, stable identity and the
recorded live process/namespace. This grants no arbitrary temporary-file
operation. Archive and secret payload inodes must still carry the distinct
denied types below; allowing keeper metadata never substitutes for that label
provisioning or the separate actual inode/FD denial proof.

Stock Podman also calls `chmod(01700)` on the fixed existing
`/run/user/UID/libpod` directory during shared configuration initialization,
before parsing operator configuration. The call occurs even when the mode is
already correct. The policy therefore permits directory `setattr` for
`user_tmp_t`, in addition to its existing directory observation rights. This is
local runtime metadata housekeeping, not an assertion that a read command has
no effects. The SELinux permission applies to the type; it does not encode this
pathname or mode. Protected fixed code and the separately verified account/runtime
binding constrain its use. No temporary-file write, creation, relabel or new
capability follows. See the pinned [default runtime-directory initialization](https://github.com/podman-container-tools/podman/blob/cade97a52ebdf9dbf9e81de8009015776837a074/vendor/go.podman.io/common/pkg/config/default.go#L506-L529).

Local Podman command initialization also identifies cgroup mode by fixed
`statfs("/sys/fs/cgroup")`. Linux mediates this superblock metadata query as
`filesystem getattr`, separately from ordinary file/directory observation. The
policy permits only that filesystem permission for `cgroup_t`; it adds no
mount/remount, namespace or cgroup write right. This type permission covers
accessible superblocks with that SID, not a pathname or expected filesystem
magic value. Fixed code verifies those separately. See the pinned
[cgroup-mode query](https://github.com/podman-container-tools/podman/blob/cade97a52ebdf9dbf9e81de8009015776837a074/vendor/go.podman.io/common/pkg/cgroups/cgroups_linux.go#L475-L485)
and Linux's [superblock permission check](https://github.com/torvalds/linux/blob/v6.12/security/selinux/hooks.c#L2745-L2753).

Overlay initialization also identifies the existing graph root's backing
filesystem with `statfs`, before the supported `skip_mount_home` option takes
effect. Permit only `fs_t:filesystem getattr` for this superblock metadata;
this grants no file access, directory write/create, mount or relabel permission.
The type grant covers accessible superblocks with that SID, while fixed code
and the protected storage proof determine the graph root. The separate runroot
`W_OK` check can warn and continue on permission denial; that warning does not
authorize a directory-write grant or a different runtime label. See the pinned
[backing-filesystem query](https://github.com/podman-container-tools/podman/blob/cade97a52ebdf9dbf9e81de8009015776837a074/vendor/go.podman.io/storage/drivers/driver_linux.go#L127-L138),
[overlay initialization](https://github.com/podman-container-tools/podman/blob/cade97a52ebdf9dbf9e81de8009015776837a074/vendor/go.podman.io/storage/drivers/overlay/overlay.go#L331-L334)
and [runroot warning](https://github.com/podman-container-tools/podman/blob/cade97a52ebdf9dbf9e81de8009015776837a074/libpod/runtime_linux.go#L17-L33).

The stock overlay backend also checks its existing `overlay` and `overlay/l`
directories. These can carry the engine-managed `container_ro_file_t` type; for
that type, traversal/stat require directory `getattr` and `search`. This metadata grant
adds no write/create, relabel or file-content permission; the type grant
is broader than a pathname, so protected code and the stock storage proof keep
the target fixed. `MkdirAll` first stats an existing directory and returns
without creating it. A denied metadata check can instead enter its mkdir
fallback and report `file exists` when the later stat is also denied; that is
not authority to delete, replace or relabel existing engine directories. See
[overlay initialization](https://github.com/podman-container-tools/podman/blob/cade97a52ebdf9dbf9e81de8009015776837a074/vendor/go.podman.io/storage/drivers/overlay/overlay.go#L343-L355)
and the [existing-directory algorithm](https://github.com/golang/go/blob/go1.25.9/src/os/path.go#L19-L64).

The same backend reads its existing `.has-mount-program` flag with `ReadFile`.
Permit only `container_ro_file_t` file `getattr`, `open` and `read`. The
`getattr` right also supports fixed inspection loading its layer metadata:
[the layer-store reader](https://github.com/podman-container-tools/podman/blob/cade97a52ebdf9dbf9e81de8009015776837a074/vendor/go.podman.io/storage/layers.go#L919-L936)
stats `overlay-layers/layers.json` and rejects a non-ENOENT failure before
reading the file. Add no file write/create, map/execute or relabel permission
through that file rule.
This is a type-level read grant: it also permits reading any image-layer file
with that type, regardless of its content. It is not a fixed-path MAC boundary
and supplies no image-payload confidentiality claim. Protected code selects the
fixed public flag. Do not add further recursive-scan or mutation rights to
compensate for a denied flag read, or invent, rewrite or relabel backend state.
The directory enumeration below is required independently of that fallback. See the pinned
[flag read and fallback](https://github.com/podman-container-tools/podman/blob/cade97a52ebdf9dbf9e81de8009015776837a074/vendor/go.podman.io/storage/drivers/overlay/overlay.go#L680-L718).

The same fixed backend startup also enumerates `overlay/tempdirs` through
`RecoverStaleDirs`, independently of the flag-read fallback. Permit directory
`open` and `read` in addition to the existing metadata/traversal rights for
`container_ro_file_t`. This exposes directory names throughout that type,
not only the fixed temporary-directory root; it supplies no filename-secrecy
claim. The [startup call](https://github.com/podman-container-tools/podman/blob/cade97a52ebdf9dbf9e81de8009015776837a074/vendor/go.podman.io/storage/drivers/overlay/overlay.go#L446-L449)
and [enumeration/recovery](https://github.com/podman-container-tools/podman/blob/cade97a52ebdf9dbf9e81de8009015776837a074/vendor/go.podman.io/storage/internal/tempdir/tempdir.go#L119-L182)
also show why the command cannot be described as universally effect-free:
matching stale entries cause attempted locking/removal. This directory grant
adds no write, create, unlink, lock, remove-name, rmdir or relabel authority.
Keep unsupported mutation authority denied; the backend can skip entries when
locking fails, so a successful command does not prove that cleanup occurred.
Do not grant mutation rights or fabricate an empty backend to make it pass. Any actual absence of effects or
stale candidates requires its own measured proof.

Archive/NFS, Hub-state and credential/secret inode denials remain independent
and mandatory. Every actual such inode, including newly created and delivered
copies, must have a denied type with fresh proof before acceptance; a secret
carrying the allowed image type is outside this supported boundary. Source
review does not establish that an image contains no secrets or that deployed
credential delivery preserves the required labels. No universal environment,
process-memory or inherited-FD secrecy claim follows.

The stock image and layer stores open their persistent lock files read/write,
even for fixed container inspection. Permit this only through the separately
provisioned `hfcache_host_helper_engine_lock_t` type on four fixed existing
leaves: `overlay-images/images.lock` and `overlay-layers/layers.lock` under
`/var/lib/hfcache/.local/share/containers/storage`, and
`/run/user/<protected host UID>/libpod/tmp/alive.lck`, and
`/run/user/<protected host UID>/containers/overlay-layers/mountpoints.lock`.
The alive lock coordinates stock runtime initialization and must be0B. The two
persistent records and the runtime mountpoints record must each be64B. The
[fixed inspection](https://github.com/podman-container-tools/podman/blob/cade97a52ebdf9dbf9e81de8009015776837a074/libpod/container_inspect.go#L23-L31)
loads a layer store whose
[constructor](https://github.com/podman-container-tools/podman/blob/cade97a52ebdf9dbf9e81de8009015776837a074/vendor/go.podman.io/storage/layers.go#L1280-L1297)
opens that mountpoints lock read/write. The helper and legitimate
`container_runtime_t` receive only file `getattr`, `open`, `read`, `write` and
`lock` for that type. No image-type write grant, parent-directory mutation,
creation transition or runtime relabeling follows. Compile-check helper-to-
`container_ro_file_t` file and directory mutation denials. These preserve image
payload/JSON identity while allowing lock coordination; the lock-type grant
applies to whole labeled inodes, not a pathname or kernel-enforced byte range.
See the pinned [store constructor](https://github.com/podman-container-tools/podman/blob/cade97a52ebdf9dbf9e81de8009015776837a074/vendor/go.podman.io/storage/images.go#L592-L620)
and [open flags](https://github.com/podman-container-tools/podman/blob/cade97a52ebdf9dbf9e81de8009015776837a074/vendor/go.podman.io/storage/internal/rawfilelock/rawfilelock.go#L21-L35).

Independent root provisioning captures and labels each existing ordinary,
single-link service-account-owned0644 inode with the required64B/64B/0B/64B size
through its held descriptor, then rejoins the exact fixed path. Persistent
contexts name only these four leaves. Both ephemeral runtime locks need fresh
independent root provisioning after reboot or recreation following genuine
stock engine prewarming; an fcontext rule alone does not label its new inode. Absent, incorrectly labeled, default-type-recreated or unexpected locks
refuse until fresh provisioning; a directory label or fcontext rule alone does
not prove a newly created leaf. Never relabel the image tree, arbitrary lock
paths or payloads. The rootless observer freshly checks all four fixed labels and
stable inode/ancestor metadata before and after the fixed engine command under
the original aggregate budget, without reading lock bodies. This detects changes
within inspection; the type-only receipt does not identify historical inodes or
detect an otherwise-valid same-type replacement predating capture. Trust in
independent root provisioning and the engine account remains explicit. Native-only
preparation/use has no Podman or lock-path prerequisite.

The runtime paths support only the independently established stock temporary
state. The guard does not parse or authenticate the database's `LibpodTmp`
setting. In pinned Podman6.1, [the flag option](https://github.com/podman-container-tools/podman/blob/cade97a52ebdf9dbf9e81de8009015776837a074/libpod/options.go#L326-L338)
assigns the temporary directory without setting `TmpDirSet`, so
[database merge](https://github.com/podman-container-tools/podman/blob/cade97a52ebdf9dbf9e81de8009015776837a074/libpod/runtime.go#L1137-L1142)
can replace it before validation. A fixed `--tmpdir` flag would therefore not
prove override refusal. Independent root provisioning and installed acceptance
must establish the default runtime/configuration/database epoch; nondefault
state is unsupported. The engine account and its state remain trusted, and
these fixed-path checks alone do not detect every database override or concurrent
change. No ineffective flag, database parser or new runtime dependency is added.

Lock coordination is an allowed metadata effect, not an absence-of-writes
claim. Store initialization can update a lock record before a later unsupported
JSON repair fails; preserve that evidence and keep image/JSON mutation denied.
Do not repair storage, create replacement locks, grant generic write rights or
silently change the stock backend to make a status read succeed.

Stock container inspection also opens the existing POSIX shared-memory lock
segment read/write and maps shared writable mutex state. Use a distinct
`hfcache_host_helper_engine_shm_t` type and the closed `engine_shared_memory`
receipt role for only `/dev/shm/libpod_rootless_lock_<protected host UID>`.
Support the independently measured stock2048-lock x86_64 segment only: ordinary,
single-link, service-account-owned0600/82488B. Grant helper and legitimate
`container_runtime_t` only file `getattr`, `open`, `read`, `write` and `map` for
that type. Keep ordinary-lock mapping compile-denied; add no generic tmpfs grant,
creation, append, setattr, replacement, relabeling or execution authority.
The type covers the whole segment, not a pathname or individual mutex. This is
writable coordination, not a payload-integrity or mutation-free read claim. See
[existing-segment open/mapping](https://github.com/podman-container-tools/podman/blob/cade97a52ebdf9dbf9e81de8009015776837a074/libpod/lock/shm/shm_lock.c#L222-L285)
and [runtime lock-manager selection](https://github.com/podman-container-tools/podman/blob/cade97a52ebdf9dbf9e81de8009015776837a074/libpod/runtime.go#L249-L282).

Independent root provisioning labels only the existing held inode after genuine
stock prewarming and rejoins its fixed path. The sole writable ancestor exception
is exact root:root01777 `/dev/shm`, including its sticky bit, reached no-follow;
no other writable ancestry is accepted. Persistent contexts name only the fixed
account's exact segment. Missing, default-type or recreated segments refuse
until fresh root provisioning, including after reboot; a context rule alone
proves no new leaf. Fresh O_PATH/xattr checks consume the same aggregate budget
and rejoin full inode/ancestor metadata, including timestamps, within each
capture. Across the command compare device/inode, owner/group, mode, links,
size, context and ancestor identity while excluding mtime/ctime: legitimate
shared mutex writes can change timestamps. Do not claim unchanged contents or
whole-command timestamps. The type-only role supplies no historical inode pin;
prior valid same-type replacements and engine-account trust retain their stated
limits. Native-only use has no engine/shared-memory prerequisite.

Shared Podman runtime initialization must also locate the stock conmon binary
through file metadata. Permit only `conmon_exec_t` file `getattr` for this
selection; no read, open, map, execute or transition permission follows. The
grant applies to that type, while protected code and configuration determine
the candidate paths. Fixed container inspect uses this initialization; INFO's
separate `conmon --version` reporting is not a reason to grant execution rights.
See the pinned [metadata selection](https://github.com/podman-container-tools/podman/blob/cade97a52ebdf9dbf9e81de8009015776837a074/vendor/go.podman.io/common/pkg/config/config.go#L972-L997)
and [INFO-only version command](https://github.com/podman-container-tools/podman/blob/cade97a52ebdf9dbf9e81de8009015776837a074/libpod/oci_conmon_common.go#L1507-L1512).

Fixed process metadata reads also require file `getattr`, `open` and `read`
for the existing manager/native/API/keeper process types: `init_t`,
`unconfined_t`, `unconfined_service_t`, `container_t` and `container_runtime_t`.
These are type permissions; source validation still fixes the process role,
PID/start identity and bounded metadata paths. They add no process-attach right,
file write/map/execute permission or general process-memory operation. Linux
separates its [read-mode and attach checks](https://github.com/torvalds/linux/blob/v6.12/security/selinux/hooks.c#L2095-L2106);
[`/proc/PID/mem` uses attach mode](https://github.com/torvalds/linux/blob/v6.12/fs/proc/base.c#L863-L869).
Reading proc metadata does not establish payload access: resolved aliases still
require permission for the actual archive/secret inode's denied type.

The fixed cross-USER keeper descriptor read also requires SELinux
`cap_userns sys_ptrace` mediation. Linux recognizes the parent namespace's owner
EUID as capable in that child namespace independently of the caller's current
capability bit sets. This adds no SYS_PTRACE bit to initial-USER effective,
permitted or bounding sets. The SELinux class permission itself is not a
READ-only or path/namespace selector; the fixed keeper/PID/start/map/owner proof
and kernel checks remain required. Initial-USER SYS_PTRACE stays forbidden and
the policy must never allow helper-to-domain `process ptrace`, checked with
neverallow validation enabled and the actual target types covered. No attachment,
process-memory or arbitrary-proc operation is exposed. Actual enforcing
attachment-class memory-read denial against an owned same-UID initial-USER
counterpart and separate archive-inode/FD denial must pass before acceptance.
This addresses new attachment-class access, not same-TGID introspection or
memory FDs authorized elsewhere. Fixed child launches close unrelated FDs and
the protocol refuses descriptor transfer; no general daemon-startup FD cleanup
is claimed. Verify the actual managed launch's declared inherited channels.

Read-gated proc environment access is not covered by attachment denial:
`/proc/PID/environ` can read target address-space bytes after a read-mode check.
Do not claim universal process-memory secrecy. Supported API, worker, Caddy and
helper processes must keep authentication/Hub secret values out of environments/argv
and use the fixed credential files. Require actual private environment-hygiene
proof for all four roles and an owned public environment-sentinel observation;
publish only safe facts/digests, never raw environment values. Inode labels do
not protect a secret copied into proc-visible memory.

The selected source has an additional `helper_selinux_policy` binding: native
`packaging/selinux/hfcache-host-helper.cil`, rootless
`host-helper/hfcache-host-helper.cil`. Its exact bytes must match root-owned0644,
single-link local `/usr/local/lib/hfcache-host-helper/hfcache-host-helper.cil`.
The neutral deployment1 index additionally requires exact
`selinux_installation_sha256`, the SHA256 of the complete fixed receipt below.

Fixed `/etc/hfcache/host-helper-selinux.json` is root-owned0644, single-link,
local and at most16384 bytes. Its closed keys are `schema_version`, `module`,
`domain`, `kernel_policy_sha256`, `labels`. Version is integer1 for existing
read/configuration provisioning or integer2 for optional native host-effect
labels below; domain is the
exact context above. Module has exactly `name`, `version`, `priority`,
`source_sha256`, `loaded_sha256`: name `hfcache_host_helper`, integer policy
version1, integer priority400 and two SHA256 strings. Source digest matches the
selected/installed CIL; loaded checksum is the actual installed module checksum
captured by root provisioning. `kernel_policy_sha256` records the actual kernel
policy at provisioning. Unknown/missing/duplicate fields or loose types refuse.

Labels has exactly these role/type entries; it contains no path selector:

| Role | Required type | Fixed objects |
| --- | --- | --- |
| `helper_exec` | `hfcache_host_helper_exec_t` | `/usr/local/libexec/hfcache-host-helper` |
| `helper_code` | `hfcache_host_helper_code_t` | `/usr/local/lib/hfcache-host-helper` and its six modules/CIL |
| `application_config` | `hfcache_host_helper_application_conf_t` | Installed configuration, owned fixed candidate/backup and preserved original predecessor/backup leaves; helper guarded write, application read-only |
| `configuration_directory` | `hfcache_host_helper_configuration_dir_t` | Exactly `/etc/hfcache`, helper fixed-name publication; application directory reads only |
| `application_state` | `hfcache_host_helper_application_state_t` | Root0700 `.configuration-applications` directories and newly created root0600 private files |
| `configuration_guard` | `hfcache_host_helper_configuration_guard_t` | Original `.configuration.lock` and fixed `.configuration.pending` |
| `configuration` | `hfcache_host_helper_conf_t` | Fixed policy, deployment, SELinux receipt and key leaves under `/etc/hfcache`; no container access |
| `runtime` | `hfcache_host_helper_runtime_t` | `/run/hfcache-host-helper` and its API subtree |
| `api_credentials` | `hfcache_host_helper_secret_t` | `/etc/hfcache/credentials` |
| `hub_home` | `hfcache_host_helper_hub_state_t` | `/var/lib/hfcache/hf-home` and all Hub-state leaves |
| `hub_cache` | `hfcache_host_helper_hub_state_t` | Entire `/var/cache/hfcache` root and subtree, including `xet` |
| `container_secrets` | `hfcache_host_helper_secret_t` | Selected bound account home's `.local/share/containers/storage/secrets` tree; both fixed paths are masked |
| `engine_locks` | `hfcache_host_helper_engine_lock_t` | Only the existing rootless image/layer locks under the fixed graphroot, `/run/user/<protected host UID>/libpod/tmp/alive.lck` and `/run/user/<protected host UID>/containers/overlay-layers/mountpoints.lock`;64B/64B/0B/64B, unused for native |
| `engine_shared_memory` | `hfcache_host_helper_engine_shm_t` | Only the existing stock2048-lock0600/82488B `/dev/shm/libpod_rootless_lock_<protected host UID>` segment; unused for native |
| `archive` | `nfs_t` or `hfcache_archive_t` | `/srv/hfcache` |

Version1 has exactly those fifteen base roles. Version2 has the same base roles
plus all four roles below. It may additionally contain exactly `observer_state`
for the separate optional observer profile; partial groups, other roles and
boolean versions refuse:

| Additional version2 role | Required type | Fixed objects |
| --- | --- | --- |
| `schedule_directory` | `hfcache_host_helper_schedule_dir_t` | `/etc/systemd/system/hfcache-sync.timer.d`, root:root0755 |
| `schedule_file` | `hfcache_host_helper_schedule_file_t` | Only the fixed managed sync-timer override, its staged replacement and retained original schedule inodes |
| `host_action_state` | `hfcache_host_helper_host_action_state_t` | Root0700 `/etc/hfcache/.host-actions` and same-bind `.hfcache-actions` schedule history; root0600 private records |
| `sync_timer_unit` | `hfcache_host_helper_sync_timer_unit_t` | Selected immutable `packaging/systemd/hfcache-sync.timer` ordinary file, root:root0644 |

The optional version2 `observer_state` role is exactly
`hfcache_sync_observer_state_t`, for the indexed native account's0700 fixed
`/var/lib/hfcache/scheduled/sync` directory and its newly created SDK state.
Inspection checks its owner/mode/label without reading observation handles or
changing the directory. Schedule-only version2 provisioning omits this role.

New native effects require version2, fresh live fixed-object labels and independent
schedule/observer permission. Version1 read/configuration-only profiles remain
valid without these objects or labels. Neither a newer receipt nor installed type
permissions grants an action. The selected timer's dedicated label permits only
timer start/stop, while generic unit types retain status-only service rights.
Manager reload is a separate type-level right; protected code fixes every argv.
The helper has no CAP_KILL and grants only SIGTERM's process permission to
`hfcache_sync_observer_t`. Stock native units do not explicitly provision this
domain, and journal stream metadata cannot attest a live SDK process SID.
`init_t` is not a supported signal target. Observer opt-in requires
the exact context fragment described below and its dedicated state label. Missing
proof denies observer permission before admission without changing a separately
proved schedule grant. Actual manager and original process context/pidfd joins
remain required before use. Journal executable and volatile/persistent log types
receive read-only access; their whole-type permissions are not source filters.
Only the helper's fixed source enum and closed projection select exposed events.

No role accepts another path or arbitrary type from the receipt. Root provisioning
captures the loaded module and original object labels without reading secret
contents. Label every existing relevant leaf, not just its directory; persistent
fixed fcontext rules and actual creation proof must cover new runtime/secret
objects. A directory label alone does not attest its children's labels. Where
fixed inspection needs nonsecret secret-store metadata, it must have a separate
supported label from secret bodies; otherwise that configuration refuses.
Root independently provisions the fixed `/run/hfcache-host-helper` parent as an
ordinary root:root0755 directory with the runtime type before first start and
after each boot. Its fixed `api` child is root-owned0750 with the actual indexed
service group and the same runtime type. Existing unsafe objects refuse rather
than being repaired. The helper proves these parents before publishing its
socket/binding; the system manager's runtime-type mount permission does not
grant parent creation. `RuntimeDirectory=` therefore does not replace this
explicit provisioning step.
The shared application-config type permits guarded helper writes and read-only
application file access; it does
not make private policy/index/key/receipt types container-readable. Mutable Hub
state has its own helper-denied type with the application role's required
read/write/create/rename/lock permissions. Credential/container-secret types
remain read-only to application containers. For validated rootless helper
opt-in, only the two existing API Hub-state mounts omit `:z`; other/default
arguments remain unchanged. Never relabel Hub state back to a generic container
type on start. Persistent fixed labels and actual newly created leaf labels
must survive original application operations and restart. The helper masks the
whole cache root as well as Hub home; file payload neverallows remain required
for aliases and preopened-inode tests.
Known absent secret stores require protected nearest-parent and absence
proof; absence is not an allow rule. Archive proof uses original proc1 mountinfo:
standard `nfs_t` or an explicitly approved uniform `hfcache_archive_t` NFS mount
context, with no unknown override or labelled-NFS assumption. The owned local
synthetic archive uses `hfcache_archive_t`; it does not prove production NFS.

Capture/revalidate the receipt, index/source and visible fixed label metadata
under the existing aggregate inspection budget. The helper's masked archive and
secret paths expose inaccessible placeholders; do not treat those labels as the
original object labels or open aliases to re-read hidden content. Original hidden
label facts remain root-admin installation attestation. The receipt's kernel
policy SHA is provisioning evidence, not a continuously rehashed current policy.
Administrative policy/label changes require new receipt/index and helper restart.
Root administration remains trusted; no policy or label is auto-installed on a
status/config read, and no installation implies a permission grant.

The fixed-code allowlist alone does not satisfy process-level secret isolation.
The demonstrated pre-entry owned proc-root route is a retained conformance gap
until mandatory domain/object enforcement and actual owned-sentinel negatives
pass. Do not probe real secrets to close it. Full enforcing native/rootless
helper/API acceptance remains required after the final source gate.

## Independent policy and deployment evidence

Fixed `/etc/hfcache/host-helper-policy.json` is a root-owned0600 single-link
regular local file, at most4096 bytes. Its exact keys are `schema_version`,
`deployment_sha256`, `permissions`; version is integer1, digest is SHA256 of
complete deployment-index bytes, and permissions contains exactly six strict
booleans: `archive`, `hub`, `control`, `schedule`, `configuration`, `observer`.
No omitted bit, default true, inferred grant or automatic provisioning is valid.

Fixed `/etc/hfcache/host-helper-deployment.json` is root-owned0644, single-link,
at most1MiB. Exact common keys are `schema_version`, `profile`, `release`,
`source`, `api_principal`, `bindings`, `authority_files`, `profile_evidence`,
`selinux_installation_sha256`.
The profile is exactly native or rootless. Release binds the exact
`releases/VERSION` selector under `/opt/hfcache/current`: original native
`[0-9][A-Za-z0-9.+-]*`, rootless three numeric components. Source records genuine
parent commit, snapshot SHA256 and strict dirty boolean. API principal records
measured positive host UID/GID. Bindings name fixed roles, never arbitrary host
paths. Authority files describe only finite ordinary selected-release evidence
with exact relative name, SHA256, byte size and mode. No symlinks, path traversal,
archive paths or nonlocal mounts are allowed. Native profile_evidence has exactly package_root_relative,
python_link_relative, python_target_relative and python_target_sha256. The
package is the fixed selected .venv Python site-packages/hfcache tree, including
all actual bytecode leaves; extras, omissions and altered modes refuse. The
Python link is .venv/bin/python, with its exact raw target and protected ordinary
executable bound below fixed /opt/hfcache/python. The original uv-created
python3 and python3.MINOR entry aliases, when present, must point exactly to
python; capture their raw links and absence and recheck them. The primary link
may point directly to the indexed ordinary interpreter or through uv's one
fixed cpython-3.MINOR-linux-ARCH-gnu selector below that directory. The selector
must itself be a protected captured link with an exact absolute target to the
indexed cpython-3.MINOR.PATCH-linux-ARCH-gnu directory; reject other link chains.
The installed entry shebang uses only the selected-release Python name or one
of those verified fixed aliases. No general symlink resolution is permitted.
Authenticate installed entry
point, pyvenv.cfg, Python pin/lock/project metadata and units/helper sources too;
layout classification alone is insufficient. This authenticates application
authority and the interpreter executable, not the complete dependency/stdlib
tree. Rootless profile_evidence requires exactly artifact_index_sha256,
runtime_profile_sha256, app_image_sha256 and caddy_image_sha256, with only the
optional closed `account_home` compatibility field described above. Rootless
retains the captured indexed original stage verification and all nine execution
bindings, in addition to new helper bindings. Exact branch schemas are validated
before any grants and documented with provisioning examples.

Native bindings may additionally contain only the optional
`sync_observer_context` role. It binds the root:root0644, single-link ordinary
`/etc/systemd/system/hfcache-sync.service.d/50-hfcache-observer.conf` to selected
`packaging/systemd/hfcache-sync.service.d/50-hfcache-observer.conf`, with its exact
authority-file digest. Its protected root0755 parent contains only that fixed
fragment; unknown entries, symlinks, altered bytes or labels refuse observer
authority. The fixed fragment selects
`system_u:system_r:hfcache_sync_observer_t:s0` without an ignore-failure prefix.
Read-only preparation captures it only when safely present and never installs
or adopts a fragment. Old native indexes without the role remain valid for
independent read/configuration/schedule use. Rootless never accepts the role.
Fresh effective manager context and original process SID checks precede observer
authority and signal; the native base units require no context opt-in.

Read parents through pinned no-follow descriptors, require root-owned
nonwritable ancestors, stable leaf metadata and exact modes. Recheck original
selection/index/policy after inspection and before publishing an admission proof.
Each directory and authority table contains at most1024 entries. Aggregate
inspection charges at most4096 file/metadata operations and64MiB within15 seconds,
including repeated reads, child bootstrap/preparation and final revalidation;
subprocess output and each fixed command remain bounded by that remaining time.
Root code uses trusted standard-library modules only. Bootstrap policy/protocol/peer copies at
`/usr/local/lib/hfcache-host-helper` are root protected and independently bound
to the selected release; no source-tree or API-written module is executable
privileged authority. Host module syntax also supports the host Python3.12; explicit per-file
Ruff targets preserve that grammar in the ordinary gate.

Known absent or inactive guard states require no access to the private service
directory. For a held guard, the fixed internal `observe-guard` child retains
real/saved UID/GID0 and uses only the independently indexed service account as
effective UID/GID while evaluating the original indexed guard predicate. This
permits its private0700-directory metadata checks without DAC capabilities or
permission changes, and prevents same-UID native API ptrace/proc-memory
tampering. There is no caller UID, path, manager or Podman selector. The root
parent independently brackets fixed unit MainPID, InvocationID and process
start ticks before/after the closed child proof; original lock-inode and kernel
FLOCK accounting remain required. Child bootstrap, metadata and output are
charged to the original aggregate budget, with at most5 seconds of remaining
work. Deadline expiry refuses the proof and retains the owned child/inspection
slot until actual normal exit. This internal observer adds no private effect
opcode and reads no configuration, key, credential or archive contents.

Enabled rootless profiles additionally require independent provisioning of
`hfcache_host_helper_archive_lock_t` on exactly the existing
`/run/hfcache/hfcache.lock`: ordinary, single-link,0600 and owned by the indexed
service UID/GID. Preserve its original device/inode and permissions. Before
launch, both API and worker validate no-follow metadata and the `object_r` role,
fixed type and `s0` range, then preserve this bind without `:z`. The worker reads
only captured protected rendered server helper opt-in; it never receives helper
authority files or projection. Disabled launch arguments remain unchanged.
The rootless mixed-ID observer brackets its original guard predicate with the
same fixed-lock metadata/context proof. Native observation is unchanged.

The dedicated type grants the helper file `getattr` only; payload access,
mapping, writes and locking remain forbidden. Exact `container_t` retains only
the fixed lock's `getattr`/`open`/`read`/`write`/`lock` rights. No path is selected
by a caller and no launcher/observer creates, repairs or relabels the lock.
This fixed direct proof introduces no receipt role or protocol field: selected
CIL, installed module and kernel-policy bindings remain mandatory. Fresh policy
provisioning and receipt/deployment bindings precede restart; recreated locks
require independent provisioning. See [the rationale](adr/decision-159.md).

A root-owned0600 fixed32-byte `/etc/hfcache/host-helper.key` authenticates opaque
configuration/schedule revisions. It is independently provisioned, never created
or rotated by reads, never returned or logged. Revisions are not raw configuration
hashes. Safe config-base reads are bounded to1MiB strict UTF-8 installed bytes.
They additionally require effective configuration permission after fresh
revalidation. A bound read preserves API check order: valid supported/guarded
status and a nonnull binding first; effective configuration permission next;
then nonnull profile and exact equality between the supplied archive ID/root
and that fresh binding. Unproved or mismatched authority returns
`config-unavailable`; denied permission returns `operation-denied`, including
when the supplied tuple also mismatches. No refusal returns revision data.
The API always binds the pair to its immutable lifespan policy and uses this one
exchange instead of a preceding status exchange. Empty-body private callers
retain their existing behavior. Both peer inspections and all configuration
revalidations remain mandatory; inspection/client deadlines, admission limits
and owned-child drain are unchanged.
Return only approved editable fields and opaque exact-byte binding, with no Hub,
listener, secret, credential-path or arbitrary document projection. No read
creates a configuration lock, candidate, backup or outcome record.

Read-only managed preparation compares the opaque full-byte base against the
same captured configuration, preserves protected fields and reconstructs exact
canonical TOML privately. It creates no persistent staging/outcome and uses
bracketed descriptor/byte/metadata revalidation without creating or taking a
configuration lock. The original lock remains mandatory for later persistent
staging and installation. Unknown removal targets, duplicate touches, unsupported
settings, coercions and byte/frame expansion refuse. Candidate text is at most1MiB;
the complete private reply is independently at most2MiB. The API alone receives
this text for independent strict validation; public results contain only an opaque
candidate revision, safe editable projection and server-derived required scope.
Neither revision is a secret-dependent raw configuration hash. See
[decision153](adr/decision-153.md). All other host/installation opcodes stay denied.

A current-boot root-owned runtime binding in the fixed helper parent records
its boot/generation, deployment/policy hashes, parent dev/inode/owner/group/mode
and original helper process identity. It grants no permissions. For rootless, the fixed host launcher verifies actual root ownership and
selected index before injecting the nonsecret HFCACHE_HOST_HELPER_PARENT
attestation into the API alone: exact schema_version1, profile rootless,
deployment_sha256, boot_id, parent device/inode/projected uid/gid/mode and peer
projected pid/uid/gid. This independently captured parent identity, not a record
learned from an untrusted socket, pins startup address provenance. Other roles
receive no attestation. Native clients verify actual root-owned parent directly.
The optional server deployment SHA is an additional pin. When omitted, native
startup derives it only from the protected root-owned address binding; rootless
startup derives it only from the independently verified launcher attestation.
Never derive rootless expected identity from the socket's own claims. Keeping
this boot binding outside indexed server-template bytes avoids a self-hashing
release index. A helper generation pins its startup deployment digest and refuses
later index drift; a changed deployment requires reviewed helper/API restart.
The API pins
this independent address evidence; a policy or helper restart cannot replace
its trusted parent. Parent is root:API-group0750, socket root:API-group0660,
binding root:API-group0440, with actual rootless group projection verified.
The helper lacks archive/Hub-secret access and IP socket authority. Its narrow
account-switch capability supports only fixed read-only rootless observers and
the held-guard child in both native and rootless profiles. The initial helper
retains only SETUID/SETGID in its permitted/effective sets and clears its
inheritable/ambient sets before loading modules or delegated code.

## Effective permissions and safe status

GET /api/v1/host/status requires the internal host-read capability before helper
work. It returns a typed bounded projection with supported, guarded, unknown or
unavailable state, fixed reasons, authenticated release/policy binding, six
explicit effective booleans/reasons, fixed service/timer facts and bounded sync
schedule view/revision. Its exact state/reason/revision/source/on_calendar/
randomized_delay_sec fields distinguish unavailable from observed fixed-source
values. Source is default or managed; use the fixed managed sync-timer drop-in
selected by the [host action module](../src/hfcache/host_actions.py), preserving
its original path and clear-then-last-value semantics and reject ambiguous extra drop-ins. This source view does not validate
a newly entered calendar or establish rootless scheduling authority. The verification timer is display-only. Unknown or
unavailable authority has no partial true grants. A held original guard denies
archive. Known absent/inactive guard is reported distinctly and grants nothing
by itself. Rootless schedule/observer remain false regardless of requested bits.
No daemon/worker crash is inferred from helper unavailability.

Expected unavailability for action admission uses HFAPI022/HTTP503/exit20;
known policy denial uses the existing HFAPI002/HTTP403. GET status instead
returns an explicit typed unavailable projection after successful administrator
authentication. No raw third-party exception message is returned.

The fixed helper entry retains its generic failure line on operator stderr and
adds at most8192 bytes of structured metadata: the fixed operation, at most four
exception records with builtin class and bounded integer errno, and at most
eight protected-module function/line frames per record. Follow both explicit
causes and implicit contexts, including a context suppressed by `raise ... from
None`; inspect at most64 traceback frames per exception. Module names are fixed
labels, never filenames. No exception text, paths, argv, PID, payload or local
variables enter this record. Fixed observer stderr inherits the daemon journal;
engine CLI stderr remains discarded. Unexpected per-request failures also emit
this bounded metadata before closing the exchange; expected invalid-input/peer
refusals and already-answered policy denials remain quiet. An interrupted apply
must still be observed by its original handle, regardless of journal output.
This operator diagnostic changes no public
response or permission and does not establish a failed operation's cause by
itself.

The exact public schema and per-operation read body are maintained in
[schemas](schemas.md) and the API source authority. Protected configuration read
is implemented at the private boundary first; its public editable workflow has
a separate contract. No write opcode is enabled by displaying its policy bit.

## Fresh Basic admission and uncertainty

Use the actual internal Basic principal, never a header or public credential
class, to require the following categories in addition to normal API rules:

| Keyed request | Required host categories |
| --- | --- |
| plans, including candidate | hub |
| read-only diagnostics | hub |
| non-read-only diagnostics | hub and archive |
| sync, non-estimate verification, repair | archive |
| prune/recovery/purge/quarantine previews | control |
| prune/recovery/purge/quarantine application, catalog refresh | archive |
| archive initialization | always denied for Basic |

Ordinary metadata, verification estimates, operation observation and synchronous
configuration validation preserve their existing capability rules. An unmapped
Basic effect denies by default. Bearer/MCP behavior is unchanged. The new internal
administration capabilities do not widen public credential/capability schemas.

Check fresh helper/policy before metadata offload/admission, and again at queue
dispatch before domain lock or verifier handoff. Pure snapshot comparison binds
the observed archive UUID and selected deployment; no helper I/O runs under the
store, runner-condition, archive or configuration locks. Existing installed-policy
fingerprint and final domain guard checks remain. Duplicate Basic POSTs perform
fresh admission checks; GET original-key/ID/result recovery remains available
when policy/helper is down. Body conflicts and at-most-once enqueue retain their
original rules. Checks are not an atomic revocation lease across lock waiting.

A known denial before any verifier handoff records one failed original receipt
and calls neither execute nor reconciliation. After a request may have reached
the verifier, retain exact original worker reconciliation/unknown semantics.
Never resubmit recovered work, replace an original handle, cancel accepted work,
or infer nonexecution from a disconnected client or failed policy observation.


## Guarded configuration application

[Decision154](adr/decision-154.md) adds fixed `config-apply` and read-only
`config-outcome` to the same peer-authenticated helper. The fifth protected
bootstrap input is `host_configuration.py`, indexed as
`helper_configuration_module` from native `src/hfcache/` or rootless
`host-helper/`. No application package import or request-selected module is
permitted. Apply reconstructs the closed managed candidate, checks original
preview/request identity and expected operational fingerprint independently, then
uses the original `.configuration.lock` inode. The API supplies validated complete
preview evidence; the helper does not read API receipt storage or acquire API
admission/store/archive locks. No helper Hub request is introduced.

Within that original configuration flock, Apply may reuse the pure managed
reconstruction over its captured bytes without nesting the read-only preparation
opcode's two full inspections. It must still fully revalidate the original
authority before the first durable pending marker, again before exchanging the
installed configuration, and after installation with only the intended
configuration leaf changed. Public `config-prepare` retains both of its
bracketing inspections. Every remaining check and file operation shares the
original work and time budget; no result is cached across requests.

The unit adds only `SupplementaryGroups=hfcache` and the fixed writable
`/etc/hfcache` bind. The group permits root:hfcache0640 creation without CAP_CHOWN
or per-thread credential switching. Preserve SETUID/SETGID ceiling, existing
namespace/capability proofs, network denial and every archive/credential mask.
Directory, state and guard types above carry only fixed configuration publication
rights; no generic `etc_t` writes or relabel permission is granted. Root
provisioning may narrowly assign the new guard SID to the original lock inode
on first upgrade, recording the transition without replacing it or changing
mode/ownership. The helper cannot perform this provisioning action. Creation
transitions assign application-config files, private directories/files and the
two named guards their separate types. The legacy root `unconfined_t` publisher
has the same file/guard creation transitions under that exact labelled directory;
this assigns types without adding an allow rule. Verify the actual legacy
publisher launch domain and inherited labels before accepting coexistence.
Container roles cannot traverse/read private state or read guards. The system manager separately has directory `mounton` on
the configuration-directory type to establish that fixed writable bind.

Private same-device root0700 `.configuration-applications/<operation-id>` holds
HMAC-authenticated state and bounded root0600 new material. Retained original
predecessor/backup inodes keep exact0640 root:hfcache metadata and original SID
inside that private directory. The pending root0600 guard is authenticated
minimal original-ID/request-digest intent, durable before even creating an
operation workspace or its private material. Full private intent/material then
become durable before candidate/backup changes. This closes the early crash
window for every participating legacy writer; marker-only history is unknown
and remains blocking. No unknown backup or candidate is adopted. History
records, original inodes and ambiguous outcomes are never evicted or repaired by
reads. See [private schema](schemas.md#182-private-helper-protocol-and-outcomes)
and [operator workflow](web-ui/configuration-and-tags.md#observe-an-interrupted-application).


## Fixed schedule, observer and journal operations

[Decision156](adr/decision-156.md) specifies the independently bounded fixed host
lane, exact original-process stop, native schedule semantics, private state,
confinement and outcome rules. New public DTOs are independent of HostStatus1;
its existing enum remains closed. Internal inspection retains truthful transient
oneshot state and new host-action authorization uses dedicated observer authority.
The protected stdlib `host_actions.py` module is indexed as
`helper_actions_module`, from native `src/hfcache/` or rootless `host-helper/`.
It accepts only the seven fixed operations above. Its signal child uses the same
protected helper entry and one inherited original pidfd, never a process selector.

Only schedule changes and observer stops use the host lane: one executing plus
one queued action, no archive flock. Startup reconciles only that lane's receipts
as interrupted, never as executable requests. Domain startup excludes those two
routes. Stop both admissions and drain both lanes before closing helper/store.
No API store, runner-condition, archive or configuration lock is held during IPC.
Host outcomes use a separate root-provisioned original `.host-actions.lock`,
root0600 authenticated `.host-actions.pending` and root0700 `.host-actions` under
`/etc/hfcache`. No read creates, repairs or removes these objects. Maximum128
history records/8MiB refuses new effects without eviction. Schedule predecessors
are retained under the same-bind private `.hfcache-actions` directory inside the
fixed timer drop-in parent. Unknown entries, marker-only history and mismatched
ID/digest remain blocking and cannot be adopted. Older installed privileged calls
may use separate file/D-Bus paths without this guard. Require safe absence or a
strict protected policy at the fixed historical compatibility path retained by
[host label validation](../src/hfcache/host_selinux.py), with both legacy schedule
and observer permissions false before new native host grants. Capture/revalidate
its bytes or absence before effects. Unsafe, malformed or
enabled legacy policy refuses new activation, without rewriting that policy.
Drain older already-authorized privileged calls before provisioning;
this operator prerequisite is not proved by a disabled policy. Legacy read and
configuration behavior is unchanged.

Validation allows printable ASCII calendar1..4096 and optional delay1..256,
without backslash/control characters or all-whitespace values. Fixed
systemd-analyze children have at most2 seconds and16KiB output each, capped by the
existing15-second aggregate inspection/20-second exchange limits. No shell,
network, arbitrary executable or caller unit is involved. Schedule changes
independently revalidate exact revision and protected grant before effects.
Reload follows replace/reset; restart follows only if the timer was active.
Pause/resume never enable/disable a timer. Observer stop uses one original pidfd
and SIGTERM; a replacement invocation is untouched. Accepted API/worker jobs and
pending observer handles are preserved independently.

Capture the fixed native SDK's exact systemd credential mount at
`/run/credentials/hfcache-sync.service`, including full raw mount identity, before
signaling. Require one mount rooted at `/`, filesystem/source `tmpfs`, and
`ro,nosuid,nodev,noexec`; malformed, duplicate, writable or non-tmpfs targets
permit no exception. Capture optional flags without requiring `noswap` or
`nosymfollow`. Only after the original-stop flow proves exit through its retained
original pidfd may its post-effect capture accept removal of that one original
mount. An unchanged table still requires the same raw credential-mount identity;
an equal projected path/filesystem/flags row cannot stand in for a replacement.
Every other ordered captured mount observation must remain identical. Missing or
ambiguous original proof permits no delta; additions, changed/replaced/duplicate
mounts and unrelated removals refuse. Keep the original capture strict and all
other policy/index/release/configuration/key/receipt/label, peer, helper namespace/
mask, unrelated-unit, guard and time/work checks active. No generic mount refresh,
credential-path exclusion, payload read, helper mount/unmount or cleanup follows.
This expected systemd teardown cannot settle backend work or an unknown original
Stop, clear pending state or grant rootless observer control.

Journal defaults to80 entries, maximum80,8KiB/entry and64KiB displayed bytes,
256KiB raw output and a4-second child window within the existing inspection
budget. At most two journal jobs share the existing eight unqueued exchanges.
Opaque cursors have at most2048 ASCII characters, source/boot/archive/deployment
HMAC binding and a five-minute expiry. Invalid bindings refuse; authenticated
expired/vanished history produces an explicit gap. Newest-to-oldest continuation
must exclude the last returned record; never silently skip an unavailable cursor.
Return only closed event/level/run-ID diagnostic projection, never arbitrary
MESSAGE prose, credentials, exception text, argv or environments. The two fixed
sources are system sync and verification observers; no user-manager control or
unbounded journal follower is introduced. Journal evidence cannot settle an API
operation. See [schemas](schemas.md) for exact required fields and coherence.
