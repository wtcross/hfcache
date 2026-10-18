# `verify --estimate` reports storage maintenance as `undetectable`

- Decision identity: 050.

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-26.

## Decision, context, and consequences

The verification contract asks the estimator for a "current
TrueNAS scrub overlap warning when detectable", and `HFWRN010` exists for
it. Nothing on the writer can detect it.

The writer holds an NFS mount and nothing else. ZFS scrubs, SMART long
tests, and replication all run on `nas.lab.example.com`, and the archive
dataset exposes no channel that reports them: there is no configured NAS API
endpoint, no credential for one, and changing NAS services is outside writer authority. Inferring maintenance from observed read latency was considered and
rejected — a slow read distinguishes a scrub from a busy sync, a cold ARC,
and a saturated uplink not at all, and a warning that fires on any of those
is a warning an operator learns to ignore.

So the field reports the literal string `undetectable` rather than a
silently absent warning, and `HFWRN010` is never emitted by `--estimate`.
The difference matters: an absent warning reads as "the window is clear",
which this application has no basis to say. The verification contract’s "when detectable"
is what permits this, and `docs/cli.md` §4.1 now lists the estimate's field
set, which is not a `VerificationReport` — `--estimate` verifies nothing, so
there is no verification to report.

`HFWRN010` stays in the taxonomy. The deployment contract requires an
operator to confirm the quarterly calendar does not overlap NAS maintenance
before enabling the timer, which is the same decision made by the party that
can actually see the schedule.

## Provenance and governing evidence

The source entry first appears in
[94949a5](https://github.com/wtcross/hfcache/commit/94949a5c62e0e3d3fb9c39c16b725ba956fa4f83)
(2026-07-26, `verification: cost a full verification without reading anything`). The
decision text above preserves the complete reasoning in the current historical
log, including its recorded alternatives and consequences.

The source entry was subsequently amended in
[a0bcee4](https://github.com/wtcross/hfcache/commit/a0bcee4f3facf69c12f3f3d61f70a50417b5c2be)
(2026-07-28, `documentation maintenance: scrub environment specifics into placeholders`); the
backfill retains the amended text rather than restoring superseded wording or
private environment values.

Current governing documents: [docs/cli.md](../cli.md),
[docs/operations.md](../operations.md).

Implementation or shipped-artifact evidence:
[src/hfcache/verification.py](../../src/hfcache/verification.py),
[src/hfcache/cli.py](../../src/hfcache/cli.py).

Relevant verification:
[tests/unit/test_verify_command.py](../../tests/unit/test_verify_command.py).
