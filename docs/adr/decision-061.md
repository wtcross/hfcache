# Decision 061: `RestrictSUIDSGID=true` is the one §22.5 setting not applied

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.
Executor/client unit roles are amended by [decision 121](decision-121.md).

- Original decision date: 2026-07-26.
- Original work package: `SEL-001`.
- Source: [decision 61 in the append-only Decisions log](../progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

Found by a real sync failing under the hardening
with `HFSYN005`: `staging ... could not be created: Operation not permitted`.

The failing requirement. `publication.create_staging` creates the staging
tree at `PUBLISHED_DIRECTORY_MODE = 0o2750` — setgid — because publication is
a rename and a rename does not change a mode, so that is the only moment the
published directory's mode can be set. The setgid bit is what carries the
group the consumer export's read identity depends on (§5.2), and the
`published/` anchor the NAS was provisioned with is `2750` for the same
reason. `RestrictSUIDSGID=true` is implemented as a seccomp filter on the
mode argument of `mkdir`/`chmod`/`mknod`, so it refuses that call outright.
Attribution was proven rather than assumed: the same `mkdir(0o2750)` on the
archive was run in two transient units differing only in that setting, and it
is `Operation not permitted` under `true` and succeeds under `false`.

The alternative that was rejected: stop asking for setgid and rely on the
parent directory's inheritance. That trades a durable, consumer-visible
on-disk contract for a hardening flag, and it would be silent when it was
wrong — a published tree that quietly lost its group would only surface as a
consumer permission failure, on a different host, later.

The narrower control that replaces it. The escalation `RestrictSUIDSGID`
exists to prevent is closed twice over: `/srv/hfcache` is mounted
`nosuid,nodev,noexec`, so a setuid or setgid file on the only filesystem this
service can write is inert; `NoNewPrivileges=true` means this service and
every child can never gain privileges from such a bit wherever it sits; and
the capability bounding and ambient sets are empty. The systemd-managed
directories are `0750`/`0700` `hfcache:hfcache`, reachable only by this
account and root, and root ignores setgid on exec anyway. It is dropped on
**both** service units rather than only the one that needs it: two units with
different hardening is a trap for whoever next adds a drop-in that runs
`repair`, and the security delta is nil given the above.

The probe missed it, and that is the more useful half of this entry. Its
first version wrote *files* to the archive and never created a directory with
the setgid bit, so the incompatibility surfaced as a failed sync rather than
as a failed check — the exact thing `scripts/hardening-probe.py` exists to
prevent. It now creates a setgid directory and a hardlink on the real archive,
and both are among the 23 checks that pass.

## Later history and current interpretation

[Decision 66](decision-066.md) clarifies that explicit `chmod` is what
establishes setgid on this NFS server. The recorded exception applies to the
sync and verification units; it is not a general authorization to weaken host
hardening.

## Provenance and governing evidence

The source entry first appears in
[657d5a7](https://github.com/wtcross/hfcache/commit/657d5a711bd442a09511915f94c0eebc4359d52f)
(2026-07-26, `SEL-001: validate every archive operation with SELinux
enforcing`). The decision text above preserves the complete reasoning in the
current historical log, including its recorded alternatives and consequences.

Current governing documents: [docs/security.md](../../docs/security.md),
[docs/architecture.md](../../docs/architecture.md).

Implementation or shipped-artifact evidence:
[packaging/systemd/hfcache-sync.service](../../packaging/systemd/hfcache-sync.service),
[packaging/systemd/hfcache-verify.service](../../packaging/systemd/hfcache-verify.service).

Relevant verification:
[scripts/hardening-probe.py](../../scripts/hardening-probe.py).

## API-014 executor/client role amendment (2026-10-18)

[Decision 121](decision-121.md) moves archive execution to API/private-verifier
units. Those actual executors retain the setgid-compatible hardening exception
and archive controls above. The old sync/verify unit names now identify AF_UNIX
observers with archive access masked; `RestrictSUIDSGID=true` is appropriate there
because they cannot publish or invoke local repair. This strengthens client
policy without weakening executor protection or changing published permissions.
Probe actual executors, not wrapper properties; real host acceptance remains held.
