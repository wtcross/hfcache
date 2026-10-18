# Quiesce executors without unmounting the archive

- Decision identity: 065.

Status: accepted when recorded; retained as historical evidence. Dated
implementation and deployment details are not independent current requirements.
Current contracts and later qualifications below govern.
API-backed quiescence is amended by [decision 121](decision-121.md).

- Original decision date: 2026-07-27.

## Context, decision and consequences

Stopping hfcache.target propagates PartOf to the native archive mount and can
unmount active storage. Pause only the applicable timers; preserve the target/
mount boundary. Timers alone are not quiescence in the current API design: stop
fresh admission/activation, drain the real API with verifier handoff available,
then drain the verifier and inspect actual processes/cgroups. Retain original
flock ownership through release selection; client exit/free-lock/PID alone is
insufficient. Decisions 120/121 extend the original lifecycle rationale.

A genuine rollback needs two distinct retained artifact trees, followed by compatible
state inspection; selecting an already-current version proves only a selector
rewrite. Cross-version format/refusal assessment is independent of release-number
cosmetics and must preserve journals, receipts and scheduled handles. The original
0.1.0/0.1.1 drill established that distinction; current deployment procedures and
compatibility barriers govern new switches.

## Provenance and governing evidence

The source entry first appears in
[428366b](https://github.com/wtcross/hfcache/commit/428366b2fa45312563c1df2940e6201c7e5e510d)
(2026-07-27, `operational tooling: installation and upgrade runbooks`). The decision text
above preserves the complete reasoning in the current historical log, including
its recorded alternatives and consequences.

Current governing documents:
[docs/deployment-centos-stream-10.md](../deployment-centos-stream-10.md)

Implementation or shipped-artifact evidence:
[scripts/install-release.sh](../../scripts/install-release.sh),
[packaging/systemd/hfcache.target](../../packaging/systemd/hfcache.target).

Relevant verification:
[tests/system/test_wheel_smoke.py](../../tests/system/test_wheel_smoke.py).

## scheduled observation quiescence and compatibility amendment (2026-10-18)

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


## 2026-10-18 data-preserving local rollout amendment

[Decision 126](decision-126.md) records new local-host release/rollout authority
with an absolute NAS content/metadata-write ban and no other-host changes. Retain
artifact identity, actual-executor quiescence and state/lock preservation; live
sync/full verification/archive-write acceptance is forbidden and remains NOT RUN.
Any local deployed tag records this partial acceptance explicitly. No remote push
or ACME issuance is authorized. Rootless runtime design/proof belongs to rootless runtime.
