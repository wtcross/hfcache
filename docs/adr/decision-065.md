# Decision 065: Plan §30 step 1 would have unmounted the archive; and a rollback needs two releases

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.
API-backed quiescence is amended by [decision 121](decision-121.md).

- Original decision date: 2026-07-27.
- Original work package: `OPS-001`.
- Source: [decision 65 in the append-only Decisions log](../agents/progress.md#decisions).
- Backfilled: 2026-10-17 (`DOC-009`).

## Decision, context, and consequences

Two things found by performing §30
instead of describing it, which is the entire argument for the requirement
that a runbook be exercised.

**The unmount.** §30's upgrade step 1 said "stop `hfcache.target`". §22.4
puts `PartOf=hfcache.target` on `srv-hfcache.mount`, and `PartOf=` propagates
stops — so the documented first step of every upgrade takes `/srv/hfcache`
away. For an operator that is recoverable and nearly invisible, because the
automount re-triggers on the next access. For this session it is fatal
(§36.4), which is how it was noticed rather than performed.

What step 1 is *for* is that no job is running when `current` moves, and
stopping the two timers achieves exactly that. §30 is amended to say so and
to keep the reason attached, because "stop the target" is the obvious thing
to write again in six months. The `PartOf=` on the mount is deliberate and
stays: it is what makes `systemctl stop hfcache.target` mean "stop using the
archive", which is the right meaning for every purpose except this one.

**The second release.** A rollback exercised against a single installed
release is not a rollback; `--switch 0.1.0` when `current` is already 0.1.0
proves only that the symlink can be rewritten. So the version was moved to
**0.1.1** — which `OBS-001` and `OBS-002` had earned anyway, the event log
being a new observable surface — 0.1.1 was installed and switched to, and the
rollback went genuinely backwards to 0.1.0 and then forward again.

The step worth keeping from that is the third one, not the switch:
`recover --dry-run` on **0.1.0** against an archive **0.1.1** had written
reported `actionable 0`, `blocked 0`. That is the property rollback actually
depends on — durable formats are versioned and a newer one is refused rather
than read speculatively — and it is worth re-checking whenever a release
touches a durable format. This one did not; the event log writes nothing
durable.

0.1.1 is not a release in the `REL-003` sense and is not tagged. It exists so
that two releases exist.

## Later history and current interpretation

The 0.1.0/0.1.1 switches are the original deployment drill, not current release
targets. Current release and rollback procedures, including later durable-format
barriers, are in the release and deployment documents.

## Provenance and governing evidence

The source entry first appears in
[428366b](https://github.com/wtcross/hfcache/commit/428366b2fa45312563c1df2940e6201c7e5e510d)
(2026-07-27, `OPS-001: installation and upgrade runbooks`). The decision text
above preserves the complete reasoning in the current historical log, including
its recorded alternatives and consequences.

Current governing documents:
[docs/deployment-centos-stream-10.md](../deployment-centos-stream-10.md),
[docs/agents/release.md](../agents/release.md).

Implementation or shipped-artifact evidence:
[scripts/install-release.sh](../../scripts/install-release.sh),
[packaging/systemd/hfcache.target](../../packaging/systemd/hfcache.target).

Relevant verification:
[tests/system/test_wheel_smoke.py](../../tests/system/test_wheel_smoke.py).

## API-014 quiescence and compatibility amendment (2026-10-18)

[Decision 121](decision-121.md) requires actual API/worker sockets/services,
scheduled clients and timers inactive before switch/rebuild, with a noncreating
archive-flock guard retained through the switch. Unknown quiescence refuses;
installer never auto-stops/kills or clears locks. Stop admission/activation and
drain API work while private outcome handoff remains available, then drain the
private worker. Stopped client wrappers alone prove nothing about execution.
Never stop the lifecycle target for upgrades.

Writer release smoke installs locked server dependencies, parses real archive
policy without credentials/archive/network and exercises CLI local validation
using synthetic disabled-token policy. Real daemon credential validation stays
operator/API preflight. Preserve pending observation/operation stores and perform
the new independent handle's actual old/current binary drill. Disposable two-tree
switch/drain/rollback fixtures do not constitute production deployment or real
systemd/cgroup/SELinux/NFS acceptance.


## 2026-10-18 data-preserving local rollout amendment (OPS-014)

[Decision 126](decision-126.md) records new local-host release/rollout authority
with an absolute NAS content/metadata-write ban and no other-host changes. Retain
artifact identity, actual-executor quiescence and state/lock preservation; live
sync/full verification/archive-write acceptance is forbidden and remains NOT RUN.
Any local deployed tag records this partial acceptance explicitly. No remote push
or ACME issuance is authorized. Rootless runtime design/proof belongs to OPS-015.
