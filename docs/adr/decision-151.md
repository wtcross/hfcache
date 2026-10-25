# Retain mapped-inode read and search only inside the verified engine USER namespace

- Decision identity: 151.
- Status: Accepted; implemented and proved in owned native/rootless fixtures.
- Date: 2026-10-21.
- Introducing change: this commit.
- Supersedes only the SYS_ADMIN-only engine capability-retention rule in
  [decision150](decision-150.md#revised-engine-capability-boundary-2026-10-21).

## Context and decision

The fixed stock Podman inspection must retain the helper's original masked MNT
while entering only the independently proved engine USER namespace. Its earlier
capless design failed Podman's effective-SYS_ADMIN setup/storage gates. The
SYS_ADMIN-only successor passed that boundary but failed when fixed inspection
read overlay lower metadata through a subordinate-ID-owned0700 layer directory.
These earlier failures remain evidence; neither establishes installed support.

An owned fixture measured a165536:1655360700 layer directory whose lower metadata
leaves were983:9830644. The live verified keeper maps USER UID/GID0 to host983
and USER IDs1..65536 to host165536..231071, so that ancestor maps to UID/GID1.
Actual kernel checks allowed the relevant SELinux directory-search and file
open/read operations; DAC traversal remained the independent obstacle. The
numeric values describe this fixture, not new fixed account or mapping defaults.

Retain DAC_READ_SEARCH in addition to SYS_ADMIN only in the separate engine
child after it joins the existing, independently verified engine USER namespace.
At fixed Podman exec, require effective/permitted/bounding bits2 and21 exactly
(mask0x200004), empty inheritable/ambient sets, NoNewPrivileges and locked
securebits0xCE: NOROOT false, NO_SETUID_FIXUP true, NO_CAP_AMBIENT_RAISE true.
While namespace-only SETPCAP is still effective, drop every other bounding bit
and verify the exact result; then clear ambient state, set/lock securebits and
drop SETPCAP while establishing the required final sets.

The initial-USER daemon's effective/permitted/bounding ceiling stays exactly
SETUID/SETGID (0xc0) with empty inheritable/ambient sets after startup repair.
The original account observer stays in initial USER with empty effective,
permitted, inheritable and ambient sets, its original bounding ceiling and no
supplementary groups. Add no initial-USER DAC_READ_SEARCH, DAC_OVERRIDE,
SYS_ADMIN, SYS_PTRACE or SETPCAP. SELinux must never authorize DAC_OVERRIDE in
either capability class; its process bit must be absent after trusted reduction
and at every verified steady/fixed-exec boundary. USER entry can transiently
reset namespace capability bits before that immediate trusted reduction, so no
all-instructions bit-absence or lifetime-exactness claim follows.
Native and mixed-ID guard branches retain their separate existing contracts.

Before USER entry, retain positive keeper PID/start, original pidfd liveness,
namespace FD/owner and exact protected UID/GID mappings. Independently prove
the retained masked MNT belongs to initial USER using NS_GET_USERNS; recheck
the unchanged MNT after entry and close all namespace proof FDs before exec.
Never join or create MNT, PID or NET. Keep the original seccomp/filter count,
USER-only namespace restriction, AF_UNIX, archive/Hub/credential masks and fixed
read-only API-container inspection argv. No new module, dependency, request
selector, engine socket or public effect operation follows from this decision.

## Rationale and alternatives

Linux checks both mount-transformed inode UID and GID for mappings before
current-USER capability authority can bypass inode DAC; see the pinned
[mapping predicate](https://github.com/torvalds/linux/blob/v6.12/kernel/capability.c#L475-L499).
[Generic permission checks](https://github.com/torvalds/linux/blob/v6.12/fs/namei.c#L406-L448)
use DAC_READ_SEARCH for directory read/search and regular-file read, with no
separate directory-search-only capability. DAC_OVERRIDE also bypasses writes
and is excluded. SELinux remains an independent
[subsequent permission check](https://github.com/torvalds/linux/blob/v6.12/fs/namei.c#L535-L543).

The fixed stock [inspection path](https://github.com/podman-container-tools/podman/blob/cade97a52ebdf9dbf9e81de8009015776837a074/libpod/container_inspect.go#L23-L35)
collects graph-driver metadata; changing output formatting does not establish
a bypass of overlay metadata traversal. Keeping SYS_ADMIN alone therefore
does not solve the measured0700 search failure. Switching to mapped UID1 loses
the original account's0700 directory/engine access; groups cannot bypass
owner-only0700. The stock CLI has no reviewed input for preopened metadata FDs,
so an unused inherited FD is not an alternative consumer interface.

A separate FD broker or root-provisioned read-only idmapped metadata projection
could define a different design, but requires new consumer or privileged mount,
identity and lifecycle authority not established here. Neither is a proved
smaller stock-compatible change. Joining the engine MNT or using an unconfined
engine broker would abandon the retained masked-MNT boundary. Initial-USER DAC,
namespace DAC_OVERRIDE, chmod/ACL changes and payload/secret label-access
expansion are excluded. A naive Landlock layer can also block required proc/ns
proof and is not an established replacement for the existing isolation model.

## Consequences and required proof

DAC_READ_SEARCH covers every reachable inode whose UID and GID both map through
the actual mount idmap into the engine USER namespace. It is not restricted to
the fixed lower metadata path, one image or a declared label. It bypasses read
and directory read/search DAC checks, not write or regular-file execute checks;
it does not bypass SELinux or authorize new namespace entry. Existing exact
capability observations are controlled pre-exec/readback and actual sampled
states, not a lifetime guarantee after arbitrary further USER transitions.

Do not claim file handles universally require initial-USER DAC_READ_SEARCH.
Linux6.12 has a [conditional directory-handle path](https://github.com/torvalds/linux/blob/v6.12/fs/fhandle.c#L252-L299)
requiring filesystem or eligible mount-owner SYS_ADMIN, current-USER read/search
authority and mapped ancestry. Engine-USER SYS_ADMIN does not supply authority
over the retained initial-USER-owned MNT or host filesystem; other reachable
mounts/superblocks need their own assessment. READ_SEARCH also participates in
an [empty-path link check](https://github.com/torvalds/linux/blob/v6.12/fs/namei.c#L2512-L2517)
without bypassing destination write or SELinux mutation checks. No generic
handle, path or descriptor selector is added; actual syscall restrictions and
relevant owned negatives must be checked rather than assuming no ancillary
effects.

The mandatory first-exec Enforcing helper domain, archive/NFS/Hub/credential
object denials, process-attachment-class denials and domain-escape prohibitions
remain unchanged. The corresponding SELinux capability permission applies only
to `cap_userns`; the initial-USER capability class must continue to deny DAC
authority. Changing the retained bit set does not authorize another object-type
read/search grant, initial capability or permission/ACL change.

Before support is accepted, require source tests for wrong namespaces/mappings,
extra bits and nonempty inheritable/ambient sets; actual fixed inspection under
the exact retained state; unchanged MNT/PID/NET and refused MNT unshare/typed and
zero-flag entry; all owned child/FD drain; and the applicable actual archive/Hub/
credential inode/FD-alias and attachment-class negative proofs under the revised
state. Use owned nonsecret sentinels with inode and kernel-event attribution
where required; never read a real secret. Kernel permission queries and earlier
SYS_ADMIN-only negatives do not replace these observations. Preserve original
lock/SHM identity and metadata-effect requirements and actual denied-IP proof.

Full isolated native/rootless helper, API and real-browser acceptance remains
separate from a successful prototype or source test. Missing or unproved
authority must still produce unavailable/denied status; no automatic grant,
replay, unconfined fallback or claimed cleanup of an undrained process is valid.

## Relationships and evidence

This decision amends only the engine capability-retention policy in
[decision150](decision-150.md); its authentication, transport, policy/index,
bounded inspection, native observer, mixed-ID guard and mandatory SELinux
contracts remain in force. See the [current host contract](../host-administration.md#managed-startup-and-fixed-engine-observation),
[security contract](../security.md) and [invariant register](../invariants.md).
The introducing implementation is this commit. The relevant source and tests
are [the indexed peer module](../../src/hfcache/host_peer.py),
[engine proof tests](../../tests/unit/test_host_engine.py),
[engine runtime tests](../../tests/unit/test_host_engine_runtime.py) and
[SELinux policy tests](../../tests/unit/test_host_selinux_policy.py). Acceptance
of this design is not evidence that those changes or an installed cohort pass.
