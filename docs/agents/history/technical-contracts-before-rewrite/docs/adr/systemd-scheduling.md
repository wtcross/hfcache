> Historical technical reference preserved before consolidation. Current authority is the living contract.

Interface-only instructions and source references have been omitted from this
retained shared record. Exact original text remains in Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`;
original document path SHA-256 `b94313c565fc9421c5db6f77a8e57c9a3bcf36f922b5a9b531d859301b4185b5`,
original content SHA-256 `7a46554512eb7db42d947d07a3603cbf2924fd43e9c3061b352aac1f7bb5f700`.
Historical proof hashes identify the original artifacts, not this edited record.

# Keep host scheduling in systemd timers and drop-ins

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

**API-014 amendment (2026-10-18, [decision 121](../../../../../adr/decision-121.md)).**
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
