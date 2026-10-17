# Decision 066: A setgid directory on this mount is made by `chmod`, not by `mkdir`'s mode argument

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-27.
- Original work package: `HARD-001`.
- Source: [decision 66 in the append-only Decisions log](../progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

Not a deviation from a plan sentence —
the plan never says *how* `0o2750` is achieved — but a durable fact about the
archive's mode contract that two documents imply the opposite of, and that
the standing guard on that contract was silently wrong about.

`docs/architecture.md` §5.2 describes directories under `published/` as
"inherited setgid plus `UMask=0027`", which is true of the *children* of a
published tree and false of its root. The root is created in
`.store/staging/<txn>/`, which is `0o700` and carries no setgid to inherit,
and it reaches `published/` by rename — and a rename does not change a mode.
So the one moment the bit can be set is at creation, and
`publication.create_staging` has always set it with `mkdir` **followed by
`chmod`** (`publication.py:139-140`). The `chmod` reads as belt-and-braces
beside the `mkdir(mode=...)`. It is not: it is the line that works.

Measured as the service identity on `/srv/hfcache/.store/health`, `mkdir`
alone yields `0o750` and `mkdir`+`chmod` yields `0o2750`. POSIX does not
guarantee `mkdir` honours setgid in its mode argument, and this NFSv4 server
does not; `umask` is not the cause, since the bit is absent under a umask that
does not mask it. Nothing was broken by this — the live published tree is
`2750`/`2755` throughout — because the application had the `chmod` from the
start. What was broken was the *probe*, which had only the `mkdir` and
therefore tested a call the application does not depend on.

Two consequences worth attaching to the fact rather than rediscovering.
Removing that `chmod` as redundant would silently drop the group the consumer
export's read identity depends on, and it would surface as a consumer
permission failure on a different host, later — the same shape of failure
decision 61 rejected when it declined to trade the bit for a hardening flag.
And decision 61's watch item is now genuinely checkable: `RestrictSUIDSGID`
filters the mode argument of `chmod` as well as `mkdir`, so if that setting
ever becomes applicable again, this check is what fails first.

## Later history and current interpretation

This supplies the correction to the probe and the implementation detail
underlying [decision 61](decision-061.md). Preserving the published group
contract remains the reason for the unit exception.

## Provenance and governing evidence

The source entry first appears in
[a919c35](https://github.com/wtcross/hfcache/commit/a919c35e66aaebd67ee97963f16cf3e39f83d421)
(2026-07-27, `HARD-001: make the setgid probe test the call the application
makes`). The decision text above preserves the complete reasoning in the current
historical log, including its recorded alternatives and consequences.

Current governing documents: [docs/architecture.md](../../docs/architecture.md),
[docs/security.md](../../docs/security.md).

Implementation or shipped-artifact evidence:
[src/hfcache/publication.py](../../src/hfcache/publication.py).

Relevant verification:
[scripts/hardening-probe.py](../../scripts/hardening-probe.py),
[tests/system/test_live_mount.py](../../tests/system/test_live_mount.py).
