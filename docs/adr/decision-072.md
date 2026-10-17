# Decision 072: A throwaway archive has to be a real NFS mount, so the writer exports one to itself

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-27.
- Original work package: `OPS-003`.
- Source: [decision 72 in the append-only Decisions log](../progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

Plan §28 says the corruption and repair
runbook is "exercised on a **throwaway archive**, never on `/srv/hfcache`",
and does not say what a throwaway archive is. It cannot be a directory.

§19's preflight requires the archive root to be a **mount point whose
filesystem type is `nfs` or `nfs4`**, read from `/proc/self/mountinfo`, and
there is no configuration escape hatch and no environment override — the test
suite substitutes the mount table by monkeypatching a module constant, which
is not available to a CLI invocation. So the options were to add an override
to production safety code so a document could be written, to run the drill
through Python and bypass the preflight the runbook is supposed to
demonstrate, or to provide a real NFS mount.

The third is the only one that leaves the application alone, and it is
cheaper than it sounds: `nfs-utils` is already installed as the client,
`nfs-server` was disabled and inactive with nothing on port 2049, and a
one-line export to `127.0.0.1` gives a genuine NFSv4.2 mount that the
preflight, the hardlink probe, and the atomic-rename probe all accept. It
touches no TrueNAS state, needs no second host, and cannot reach
`/srv/hfcache` — the export is a different directory with a different archive
UUID. The live mount was checked after each step of standing it up.

Two things about it are worth writing down because both cost a cycle.
Mounting `127.0.0.1:/` gets the NFSv4 **pseudo-root**, which is read-only; the
export path itself is what you mount. And the throwaway needs its **own
`archive_id`** in its own config, because the sentinel is what stops a
misdirected command, and reusing the real UUID would defeat exactly the check
that protects the real archive.

The runbook ships the recipe (`docs/recovery.md` §6) rather than leaving it
implicit, because a repair rehearsal an operator cannot perform is a repair
procedure nobody has tested — which is the same argument `SEC-001` and
`OBS-001` made for exercising the credential drop-in and the failure hook.

## Later history and current interpretation

This is the rationale for the isolated rehearsal recipe, not standing
authorization to create mounts or exports on a production writer. The
environment hard limits and the current recovery runbook govern any execution.

## Provenance and governing evidence

The source entry first appears in
[9bd269a](https://github.com/wtcross/hfcache/commit/9bd269a925222c720d0e9b815d04b9648eac3513)
(2026-07-27, `OPS-003: corruption and repair runbook, exercised on a throwaway
archive`). The decision text above preserves the complete reasoning in the
current historical log, including its recorded alternatives and consequences.

Current governing documents: [docs/recovery.md](../../docs/recovery.md),
[docs/storage-requirements.md](../../docs/storage-requirements.md),
[docs/agents/environment.md](../../docs/agents/environment.md).

Implementation or shipped-artifact evidence:
[src/hfcache/storage.py](../../src/hfcache/storage.py),
[src/hfcache/preflight.py](../../src/hfcache/preflight.py).

Relevant verification:
[tests/system/test_live_mount.py](../../tests/system/test_live_mount.py).
