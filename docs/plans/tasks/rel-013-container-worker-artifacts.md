# REL-013: Build clean 0.2.1 artifacts and prove container peer access

| Field | Value |
| --- | --- |
| Work package | `REL-013` |
| Status | pending |
| Plan | [Container worker listener](../2026-10-18-plan-container-worker-listener.md) |
| Depends on | [OPS-019](ops-019-ubi10-runtime-images.md), committed before activation |
| Scope | Clean local artifacts and disposable container proof; no NAS bind or production switch |

## Scope and acceptance

1. Build from the exact clean committed OPS-019 UBI source, version 0.2.1. Record
   wheel/sdist, locked dependency closure, base and final application image
   hashes. Build both service images under decision 129's all-FROM UBI micro
   contract; old Alpine Caddy is ineligible. Verify only the approved external
   binary/Red Hat CA donors. Do not pull or publish unrelated runtime inputs.
2. Stage the protected immutable release/profile/index with explicit usable
   modes and root/service access proof, preserving every old stage and failed
   artifact. Confirm selected helper/profile/config/seccomp/unit provenance and
   the unchanged nine-binding/index shape. No switch occurs in this package.
3. Use an actual worker and separate ordinary container_t API-role peer fixture
   with the exact app image/UID mapping and read-only private-directory view.
   Prove fixed framed PROBE with the expected UID and actual user-manager notify
   attribution before the peer connects; this is not an HTTP API server or job
   admission. Source Requires+After/readiness contracts remain, while actual
   installed API/target ordering and peer acceptance belong to OPS-018. A host
   probe or type-rule query alone is insufficient. Run all complete modes only
   on a local disposable archive using the reviewed driver's sole simulated-NFS
   seam, fixture storage.MOUNT_TABLE, after cold audit/FD3/offline setup. Preserve
   exact receipt/result IDs, failure semantics and non-canceling observations;
   that simulated-NFS domain proof is separate from the unmodified worker's
   actual PID1/notify/SELinux/isolation proof, never real-NAS acceptance.
4. Prove worker PID1/internal FD3, real denial of IPv4/IPv6 creation, no secrets,
   offline startup, masks, capabilities, NoNewPrivileges, read-only root, cgroup
   limits, original fixture-lock contention and graceful socket cleanup/drain.
   Preserve stale/replaced socket evidence and all failed attempts. Never use
   label-disable, custom allow policy, privileged/host-network/PID shortcuts or
   forced container deletion to turn a failure green.
5. Run a fresh predecessor/current format compatibility drill with real
   installed binaries/images, preserving unsupported/malformed/future data.
   Record operational 0.2.0 rollback limits, including its known container-peer
   SELinux hold. Archive/receipt/observer schema versions remain unchanged.

## Contracts, invariants, and ADRs

Review the accepted OPS-017 listener decision and decisions
[65](../../adr/decision-065.md), [75](../../adr/decision-075.md),
[79](../../adr/decision-079.md), [115](../../adr/decision-115.md),
[121](../../adr/decision-121.md), [126](../../adr/decision-126.md),
[127](../../adr/decision-127.md), [release](../../agents/release.md),
[containers](../../containers.md), environment and format contracts.
Preserve INV-002/003/005–007/010–016, AD-16/17/21 and FS/TX truth. Do not replace
an architecture change with an evidence-only amendment; return it to an
explicit source task if new behavior is necessary.

## Validation

Planned, not execution evidence: exact clean-source/build checks; isolated
installed wheel profiles; strict stage/index/profile checks; actual two-container
peer and local-domain/isolation/drain proof; predecessor/current format drill;
record/link/whitespace audits and NAS-masked `scripts/check.sh --with-build`.
All complete archive fixtures are local; no production NAS pathname is opened.

## Execution notes and handoff

**SUPERSEDED initial Debian candidate; returned pending under the new user UBI 10
requirement.** All genuine build/proof/compatibility results below are preserved,
but are not UBI/current-release acceptance. The gate was deliberately stopped
with TERM 15 after 4m25.945s; wrapper exit 0 is NOT a pass and no complete suite/
build result exists. Log .scratch/rel-013-gate.log SHA256
a47542f1df083a4225f8506b4d594e084f2f1876c782edf628a3b8667c0174d6.
The domain driver never executed. OPS-019 must commit UBI source before fresh
REL-013 activation/artifacts. Production 0.2.0/hold22 remain unchanged.
Retain this original gate log/hash; use a distinct new log or preserve the old
bytes before any future gate launch, never overwrite superseded evidence.

The candidate OCI export .scratch/rel-013-app.oci.tar was not root-copied or
loaded into the service engine. Only the root-0700 evidence directory
/opt/hfcache/deployment/20261018-worker-0.2.1 was created; no protected
/opt/hfcache/releases/0.2.1 stage exists and no selector switched.

The initial superseded attempt activated after OPS-017 committed as
03a986fa934fc00f07d031b77dcb23ea4fa6d664.
Root uses clean detached /var/tmp/hfcache-rel013-source at that exact source;
final build/context/proof outputs stay outside it. Main-workspace evidence edits
do not contaminate artifact provenance. Normal ignored gate outputs may remain
inside the checkout while tracked Git status stays clean. Root owns privileged
local engine and stage operations; preserve nonsecret ledgers and failed attempts.
Artifact readiness is not production deployment or live NAS verification.

Root's actual clean wheel/sdist build exits 0 from that unchanged source.
Final artifacts under .scratch/rel-013-artifacts are version 0.2.1:
wheel SHA256 8ef1b5aa4973bbaa24f6de288e1504b40b256117b7015605e08197db1d6fbb08;
sdist SHA256 a09dce6ab7614a302a2ade16900917e7f8c417872a17a4ad15ff030d6c203f39.
They are separate actual builds from the earlier dirty previews; changed README/
source-ready metadata can change the wheel identity without changing app modules.
Never promote a preview by assuming equal source version or application bytes.

The actual clean image build exits 0:
sha256:1a4b6b17dd164160f1da8d4481b212aabb7873440a6b004893d39c4ac015e77f.
Provenance .scratch/rel-013-image-build/build.json records exact source 03a986f,
source_dirty=false and unchanged locked closure. Requirements SHA256 is
2d39476506a1ebc994a9623a7b70e673830bf38f5c8fbcae687a1d180ff79587.
Actual clean-image proof is next, not yet accepted; compatibility/domain drivers
remain subject to root review.
The clean-source NAS-masked --with-build gate is running, unit hfcache-rel013-gate,
invocation 53307915afa5443db3f2a75366183a79, log .scratch/rel-013-gate.log.
Initial 415-file format and lint stages pass; no final gate/image or fixture
acceptance is claimed yet. Production selection, guard, states and hold 22 stay
unchanged. Delegated compatibility/domain drivers execute only after root review.

### Actual clean-image confinement fixture

The committed-source harness exits 0 against exact clean image 1a4b6b17… at
/var/tmp/hfcache-rel013-worker. Real user notify/all reports active/running with
MainPID 763057 equal to ConmonPid; readiness follows main start. Separate ordinary
container_t API-role PROBE passes under Enforcing SELinux, without an HTTP server
or admission in this unmodified harness. Actual worker PID1/internal FD3,
CapEff 0/NNP/Seccomp 2 pass; separate companion PID1 denies IPv4/IPv6 with errno 38
and proves masks/offline/read-only root/private namespaces/fixture-lock contention.
Protected-file reader proof is separate. Direct validated-ID drain completes,
created socket inode 71837944 is removed and store retains only .lock. All four
containers remain stopped/exit 0, worker log empty; no NAS bind/job occurs.

Proof.json SHA256
66dc0737d3b02514a8ca4fa49e9454f6c76e146c5889b629383abb6869150c63;
capture .scratch/rel-013-worker-harness.log SHA256
bbbd9d165ee53d2029f3ec8de42fc9716c6e849947f733e58c9a1d431448b55b.
This is fresh clean-artifact fixture acceptance, separate from the dirty preview
and installed OPS-018/API-server/target-drain acceptance, but it is now superseded
Debian-candidate evidence only. Hold 22 remains; no UBI acceptance follows.

The actual compatibility driver passes against old 0.2.0 image 869da6ef… and
the Debian candidate 1a4b6b17…: each has 42 schema-1/future-2 reader observations
and 21 malformed cases, 126 total, with all bytes preserved and 18 shared golden
files identical. Four one-shot containers are retained stopped. Summary
/var/tmp/hfcache-rel013-compat/summary.json SHA256
985e324871265e2e6b7e4628aee3caf3b1dbd9df57f6440184a8186f3a3d11f5;
log .scratch/rel-013-compatibility.log. No NAS/credentials/listeners/archive jobs.
This genuine result is superseded candidate evidence, not a future UBI drill.

## Completion evidence

Not started. Record exact source/artifact/image/index identities, actual fixture
peer/isolation/domain results, compatibility results, gate exit and completed
[progress audit](../../progress.md) in this work-package commit.
