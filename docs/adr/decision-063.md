# Ship bounded persistent journald settings and an optional read-only failure hook

- Decision identity: 063.

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-27.

## Decision, context, and consequences

The host logging requirements could have been discharged as
instructions in `operational tooling` — "enable persistent journald", "consider an
`OnFailure=` hook". They are shipped artifacts instead, for two different
reasons.

The journald setting, because deployment requires a fresh VM be reproducible **from
documentation** and a setting that lives only in prose is one an operator
silently skips. It is host-wide policy set by an application package, which
would be presumptuous on a shared machine; this is a dedicated
single-purpose writer, so it is merely explicit. The values are
bounded on both axes because they protect different things —
`SystemMaxUse=1G` bounds the root filesystem the Xet cache shares, and
`MaxRetentionSec=1year` bounds how far back an operator can look, at four
quarterly verifications. `SystemKeepFree` is left at its 15% default, which
is already the setting that stops the journal filling the disk under a
download.

The hook ships **uninstalled**, and the two halves of that are worth
separating. The logging contract asks that a hook be *left* for future monitoring, and this
deployment has nobody to notify: a handler that only reprints what systemd
already logged is a seam, not a control, and installing one adds a unit that
fires on every failure to no end. So it ships like
`credential.conf.example` beside it — complete, with the matching
`OnFailure=` commented in both units, so activating it is two documented
steps.

But an example nobody has run is the thing decision 59 warns about, so it
was installed and fired against a real failed unit first, and withdrawn
afterwards. Two properties are load-bearing and both were confirmed rather
than assumed: `ExecMainStatus` carries the application’s CLI exit
classification through systemd unchanged (`10` observed for an `HFCFG001`),
and `InvocationID` resolves through `journalctl _SYSTEMD_INVOCATION_ID=` to
that run's output and nothing else. The handler deliberately only reads. A
failure handler that restarts or resets turns one bad run into a loop, and
there is no hfcache failure mode where the right response is to try again
immediately — `AD-16` says ambiguity stops the machine.

**Why this preceded the runbooks rather than following them.** `operational tooling`
would otherwise have had to write two instructions that were false: "check
the journal for the failure", against a store that did not survive a reboot,
and any statement that a failed run is noticed. The ordering is the point,
not a preference.

**What is deliberately still open.** The durable run report remains the
record of what a run *did*; the journal is the record of what happened when
a run could not get far enough to write one. `reporting` closes the gap
between them by making the journal structured — today it carries systemd's
start/stop lines and the CLI's human table rows, and nothing carrying a
`run_id`.

## Later history and current interpretation

The source was amended in 4a82b01 to ship the exercised failure hook as an
uninstalled example. The later [decision 64](decision-064.md) completes the
structured event log described as open in the historical record.

## Provenance and governing evidence

The source entry first appears in
[4728f68](https://github.com/wtcross/hfcache/commit/4728f689eac5d95d947a14d79fa263bfd549fc32)
(2026-07-27, `reporting: close §24's host half`). The decision text above
preserves the complete reasoning in the current historical log, including its
recorded alternatives and consequences.

The source entry was subsequently amended in
[4a82b01](https://github.com/wtcross/hfcache/commit/4a82b015a3ffd501f131043244f440abe7a032af)
(2026-07-27, `reporting: ship the failure hook as an example rather than wiring
it`); the backfill retains the amended text rather than restoring superseded
wording or private environment values.

Current governing documents: [docs/operations.md](../operations.md),
[docs/deployment-centos-stream-10.md](../deployment-centos-stream-10.md).

Implementation or shipped-artifact evidence:
[packaging/journald.conf.d/hfcache.conf](../../packaging/journald.conf.d/hfcache.conf),
[packaging/systemd/hfcache-failure@.service.example](../../packaging/systemd/hfcache-failure@.service.example).

Verification or recorded operational evidence:
[recorded deployment scope](../deployment-status.md).
