# Keep host scheduling in systemd timers and drop-ins

- Status: accepted; an existing locked plan decision without an AD number;
  provenance clarified by [111](decision-111.md), API client lifecycle amended by
  [121](decision-121.md).
- Original record: 2026-07-24, `87323c2` (original architectural decision).

## Context

Unattended sync and full verification require host lifecycle management,
mount ordering, credentials, hardening, and visible command exit status.
The application TOML describes archive and sync policy; a second scheduler
inside the process would duplicate host-level authority.

## Decision

Use distinct systemd oneshot services and calendar timers for sync and full
verification. Keep scheduling in timer units and local drop-ins, outside
application TOML. Use `hfcache.target` to group the scheduled lifecycle and
archive automount. Attach timers through their own `[Install] WantedBy=` so
an installed-but-disabled verification timer stays disabled when the target
starts.

## Rationale and alternatives

The original locked table explicitly selects systemd timers and drop-ins
and distinguishes scheduling from TOML policy; it does not enumerate
competing scheduler products. Systemd supplies the host lifecycle and
status boundary already required by the deployment.

Decision 58 rejects putting timers directly in the target's `Wants=`,
which would start disabled timers, and retaining an fstab entry shadowed
by explicit units. It also records that network ordering belongs on the
mount, since the automount's implicit local-filesystem ordering otherwise
creates a boot cycle. CP-12 rejects editing packaged timer units for local
schedule changes.

## Consequences

An elapsed timer while the same oneshot service is running merges into
that active run; it does not create parallel syncs or queue every missed
observation. Persistent catch-up covers elapsed events while the host was
down. Manual invocations and different services remain serialized by the
shared application lock (AD-17). The verification timer still requires
operator coordination before activation. Judge `systemd-analyze verify`
by its output, since an ordering diagnostic can accompany exit zero.

## History and evidence

**scheduled observation amendment (2026-10-18, [decision 121](decision-121.md)).**
The named sync/verify oneshots now observe fixed API jobs through AF_UNIX with a
distinct API credential. Keep calendars, disabled verify timer, OnFailure and
target/mount behavior. A private schema-1 pending handle persists the key before
the sole POST and accepted operation ID; existing state permits lookup/observation
only. Repeated finite windows keep the oneshot active until exact terminal
Envelope/exit, preserving timer overlap semantics without replaying unknown work.
Same-class credential rotation can recover; missing/malformed/future/mismatched
history is retained rather than reset. No bearer/digest/body/queue is stored.
Server/worker drain, not client-service exit, proves executor termination. Shared
runtime locks must survive unit stops. Repository fixtures do not establish real
systemd/cgroup/SELinux/NFS acceptance; those remain deployment holds.
