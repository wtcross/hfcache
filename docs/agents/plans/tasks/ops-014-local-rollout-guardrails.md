# OPS-014: Establish data-preserving local rollout guardrails

| Field | Value |
| --- | --- |
| Work package | `OPS-014` |
| Status | completed |
| Plan | [2026-10-18-plan-local-rootless-rollout.md](../2026-10-18-plan-local-rootless-rollout.md) |
| Depends on | None |
| Scope | Local host only; no NAS content/metadata writes or other-host changes |

## Scope and acceptance

1. Record exact new local-host authorization, inventory and no-NAS/no-other-host boundaries before any host mutation; amend governing release/environment/deployment contracts and decision 126.
2. Root snapshots local service/timer/mount/config/state metadata without secret values or NAS file I/O. Preserve previous units/drop-ins, activation, release target, state and lock inodes.
3. Pause/disable and block legacy sync/verify scheduling/services without stopping the lifecycle target. Prove no running executor through actual process/cgroup evidence and a retained noncreating local archive flock; unknown activity refuses further mutation.
4. Enforce a client-side read-only remount of the existing NFS mount without unmount/disconnect, and a persistent local mount-unit override. Do not alter NAS files, ownership, modes, labels, exports or server configuration.
5. Record actual commands/outcomes and residual holds, run the required gate, complete this task and commit before OPS-015. Any safe failure preserves evidence and leaves writers blocked.

## Contracts, invariants, and ADRs

Decision 126; INV-003/010/011/014/015, AD-16/17, FS-18/19; environment hard limits, release/deployment quiescence, scheduling and decisions 65/75/79/121. This package establishes policy/guardrails; it does not yet implement the rootless runtime.

Read the [invariant register](../../../invariants.md), [ADR index](../../../adr/README.md),
[environment](../../environment.md), [release](../../release.md),
[planning](../../planning.md) and [workflow](../../workflow.md).
Record actual review/amendments with completion evidence; preserve historical
records rather than silently rewriting their earlier authority.

## Validation

Planned, not execution evidence: `scripts/check.sh` (plus `--with-build` at
release/container boundaries), meaningful scope-specific tests and local
record/link/decision/whitespace audits. Host tests must preserve the absolute
NAS-write ban. Record forbidden storage checks as NOT RUN, never passing.
Only root performs privileged host mutations and never prints secret values.

## Execution notes and handoff

Activated 2026-10-18 under Tyler's new local rollout authorization after clean
feature commit c73822d. This is the sole task in progress; all later tasks remain
pending. Initial root inventory and intended guard actions are in the parent
plan; no action is claimed complete before its actual evidence is recorded.


### Actual local guard execution — 2026-10-18T14:08:47Z

Root ran
`sudo -n /usr/bin/python3 /home/tyler/Projects/hfcache/.scratch/ops-014-guard.py`
with exit 0. The ignored script remains execution evidence; the root-owned 0700
backup is /var/lib/hfcache/deployment/20261018-rootless-guard. It preserves the
original units/drop-ins/target wants/config and before.json/after.json plus the
retained guard helper hold-lock.py. No secret value was printed or NAS file I/O
performed. No UID 981 process existed before mutation.

The guard used `systemctl disable --now` for both timers, moved the four original
unit inodes into the backup and replaced their /etc names with /dev/null masks,
then reloaded the manager. Both sync/verify timers are stopped and masked with
activation links disabled; both services are inactive, MainPID 0, with empty
cgroups and masks. The existing hfcache.target remains active. SELinux remains
Enforcing; no policy was relaxed.

The local srv-hfcache.mount.d/readonly-rollout.conf persists
ro,hard,nosuid,nodev,noexec,vers=4.2,proto=tcp,nconnect=4. The actual
`mount -o remount,ro /srv/hfcache` succeeded without disconnect/unmount. These are
client-local mount changes, not NAS file/content/metadata or server changes.
The transient hfcache-rollout-guard.service remains active with MainPID 653008,
holding O_RDONLY|O_NOFOLLOW on the existing local archive lock and EX|NB flock.
Device 27/inode 2273 is unchanged; an independent conflict check proves ownership.
No lock was created, replaced, truncated or removed. Retain the guard through the
reviewed transitions; later rootless implementation remains pending.

Root also retained guard-transition.py as 0600 inside that protected backup;
its SHA-256 is 54f9dec368b446fd68626d0721ee9bed7d9e2a50444457019d83e24e4ff357e9.
Snapshot SHA-256 values identify the actual local evidence:

| Evidence | SHA-256 |
| --- | --- |
| before.json | 33c9502c8ea6c4606be0c0eed9e620b1eaf4999f2883b190807c8d380f6abef2 |
| after.json | a0ebfe2b1e3390ea058ff6d52ec8b809f2bdf25222b047e10b39c22a89a2c3f9 |

### Required gate isolation and launch history

Default collection imports the live-mount module even when nfs tests are
deselected, so deselection alone cannot establish no NAS file I/O. Root instead
runs the gate as tyler in a transient namespace with
TemporaryFileSystem=/srv/hfcache:ro. /proc/653235/mountinfo confirms an empty
read-only tmpfs covers that path, making the NAS unavailable to collection/tests.

An initial systemd --pipe launch with direct logfile redirection was rejected by
SELinux before startup. It is a failed launch, not a passed test or completed
gate. No policy changed; root corrected the output plumbing to a real pipe/tee.
The first executing command, with shell pipefail, was:

```bash
sudo -n systemd-run --unit=hfcache-ops014-gate --collect --wait --pipe --uid=tyler --property=WorkingDirectory=/home/tyler/Projects/hfcache --property=TemporaryFileSystem=/srv/hfcache:ro --setenv=PATH=/home/tyler/.local/bin:/home/tyler/.local/share/pnpm/bin:/usr/local/bin:/usr/bin:/bin /usr/bin/bash scripts/check.sh 2>&1 | tee .scratch/ops-014-gate.log
```

That run actually exited 1 at Python: 3 failed, 3,621 passed, 40 deselected in
454.50 seconds. The three synchronize event-trail assertions expected interactive
lines beginning event=. The transient gate's INVOCATION_ID legitimately selected
the existing systemd syslog-priority prefix (`<6>event`), so those expectations did
not match. Production logging was correct; no production or test source changed.
The failed log is retained as .scratch/ops-014-gate-systemd-env-failed.log; no
build/install/Cockpit pass is claimed for that stopped run.

Root started a fresh NAS-masked gate (invocation
f84179116ea847dbb8e3a7b9c79c2a50), clearing only the test process's inherited
systemd identity variables. SELinux, the read-only tmpfs namespace, actual runtime
logging and host guard remain unchanged. The corrected command, with pipefail, is:

```bash
sudo -n systemd-run --unit=hfcache-ops014-gate --collect --wait --pipe --uid=tyler --property=WorkingDirectory=/home/tyler/Projects/hfcache --property=TemporaryFileSystem=/srv/hfcache:ro --setenv=PATH=/home/tyler/.local/bin:/home/tyler/.local/share/pnpm/bin:/usr/local/bin:/usr/bin:/bin /usr/bin/env -u INVOCATION_ID -u SYSTEMD_EXEC_PID /usr/bin/bash scripts/check.sh 2>&1 | tee .scratch/ops-014-gate.log
```

The corrected gate confirmed actual exit 0 at 2026-10-18T14:25:55Z; exact results
are below. Future such test gates use the same explicit environment isolation.
Source/container/release work and OPS-015 activation have not begun. Live
sync/full-verify/NFS-write/archive-hardening checks remain forbidden and NOT RUN.

## Completion evidence

Completed 2026-10-18, this commit. The authorized host-local guard is established,
not a rootless deployment or new release. The exact guard command exited 0;
protected backup/transition/snapshot identities and actual before/after state
are recorded above. Both legacy timers/services remain masked and inactive,
sync scheduling disabled, verify scheduling disabled, existing target active,
SELinux Enforcing and actual NFS mount read-only with a persistent local override.
The existing local flock inode remains held by guard PID 653008. Root rechecked
all those barriers after the gate. No NAS file I/O/content/metadata write,
other-host change, secret-value output or hardening relaxation occurred.

The corrected required gate command above confirmed actual process exit 0 at
14:25:55Z, service duration 8 minutes 19.635 seconds. Log
.scratch/ops-014-gate.log SHA-256 is
0f100c6cd220e67029d64cd28199e423aa9aa362d878ebb2c5453e035ab7efa8.
Results: 94-package lock/both-extra sync; 395 files formatted; Ruff clean;
whole Pyrefly 0 errors (11 suppressed, 59 warnings not shown); 3,624 Python tests
passed, 40 deselected in 455.10 seconds. Source distribution/wheel 0.1.10 built,
with actual locked isolated base/server/server+MCP import/help/version smoke
profiles passing. Cockpit lint/style/types, 127 tests in 2.027 seconds and
production build in 1,257 ms passed. No additional build-marked subset was
required for this guard/policy package. Production/test source stayed unchanged.
The initial SELinux-rejected launch and first executing gate's three inherited-
environment assertion failures remain distinct preserved history; the corrected
run changed only the test process identity environment, not runtime behavior.

Review covers INV-003/010/011/014/015, AD-16/17, FS-18/19 and decisions 65/75/79/121.
Decision 126, index/predecessor links, environment/release/deployment/original-plan
amendments establish the stricter current authority and honest partial acceptance.
Five linked task records retain dependency order, OPS-015 remains pending until
this guard package is committed, and the current pointer selects it without
activation. Local record/link/dependency/decision/matrix/whitespace audits pass;
see the completed [progress audit](../../progress.md). No runtime dependency,
durable shape, domain algorithm, release version, container profile or tag changed.

Keep the guard, protected backups, both future operation-store locations and any
existing scheduled evidence. Live sync/full verification, NAS write/probing/
publication/recovery/hardening tests and other-host/NAS/calendar work remain
forbidden and NOT RUN. No production runtime switch, container startup, release,
merge/tag/push or ACME issuance occurred in this package. OPS-015 owns the next
architecture/implementation and disposable local container proof; final rollout
and local release acceptance remain later committed dependencies.
