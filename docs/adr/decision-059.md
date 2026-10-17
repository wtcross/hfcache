# Decision 059: The hardening is tested by a probe that reads the deployed unit

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.

- Original decision date: 2026-07-26.
- Original work package: `SYS-002`.
- Source: [decision 59 in the append-only Decisions log](../progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

§22.5 says "test each setting against
`huggingface_hub`, `hf_xet`, DNS, TLS, NFS, and Python native extensions",
and a checklist an operator ticks is not a test. `scripts/check-hardening.sh`
and `scripts/hardening-probe.py` are added beyond plan §7's layout, which is
amended in this commit.

One design decision carries the value: the probe does **not** restate the
settings. `check-hardening.sh` reads the `[Service]` properties out of the
installed unit file at run time and passes them to `systemd-run`, so the
thing under test is the thing deployed. A probe holding its own copy would
have gone green while the unit drifted, which is the failure mode of every
security checklist.

It asserts two different things. That the workload still runs — DNS, TLS, a
real Hub API call, a real `hf_xet` download, the native extension imports,
and a create/fsync/rename/unlink on the archive — because a setting that
quietly breaks one of these does not announce itself; `snapshot_download`
failing under `ProcSubset=pid` looks like a network problem at 02:00 on a
Tuesday. And that each setting is *in effect*, because a property systemd
parsed and could not apply reads as protection in the unit file and is not
there.

Two things it deliberately does not claim. `ProtectKernelTunables` and
`ProtectKernelLogs` are confirmed only as *refusals*: `ProcSubset=pid`
already hides `/proc/sys` and `PrivateDevices=true` already removes
`/dev/kmsg`, so the refusal does not prove which line caused it. That is
defence in depth, and reading the unit file rather than a copy is what keeps
a removed line from going unnoticed. And the four network checks **invert**
for the verification unit — reaching the Hub from it is the failure — because
a probe that only ever asserted "the network works" would have to skip the
offline unit entirely, and "the offline unit is actually offline" is the more
valuable assertion of the two, being the one a dependency upgrade can quietly
undo.

The probe also confirms something the sandbox itself put at risk:
`ProtectSystem=strict` bind-mounts the world read-only and `ReadWritePaths=`
re-mounts the archive, and on an autofs path that could have captured the
*trigger* instead of the NFS mount, leaving the service writing into an empty
directory inside its own namespace. It reads the sentinel back to prove
otherwise. All 21 checks pass on both units, and nothing was weakened to get
there — the single failure was the probe's own bug, `ProtectHome=true` making
`/home` inaccessible rather than empty.

## Later history and current interpretation

The 21-check result is dated evidence. [Decision 61](decision-061.md) adds the
setgid/hardlink checks and records the hardening incompatibility; [decision
66](decision-066.md) corrects the setgid probe to match the actual `chmod` call.

## Provenance and governing evidence

The source entry first appears in
[999ed19](https://github.com/wtcross/hfcache/commit/999ed19a88059a155e462b962505e6687c78c786)
(2026-07-26, `SYS-002: apply the §22.5 hardening and test every setting`). The
decision text above preserves the complete reasoning in the current historical
log, including its recorded alternatives and consequences.

Current governing documents: [docs/security.md](../../docs/security.md),
[docs/deployment-centos-stream-10.md](../../docs/deployment-centos-stream-10.md).

Implementation or shipped-artifact evidence:
[scripts/check-hardening.sh](../../scripts/check-hardening.sh),
[scripts/hardening-probe.py](../../scripts/hardening-probe.py).

Verification or recorded operational evidence:
[packaging/systemd/hfcache-sync.service](../../packaging/systemd/hfcache-sync.service),
[packaging/systemd/hfcache-verify.service](../../packaging/systemd/hfcache-verify.service).
