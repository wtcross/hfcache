# REL-013: Build clean 0.2.1 artifacts and prove container peer access

| Field | Value |
| --- | --- |
| Work package | `REL-013` |
| Status | completed |
| Plan | [Container worker listener](../2026-10-18-plan-container-worker-listener.md) |
| Depends on | [OPS-019](ops-019-ubi10-runtime-images.md), committed 4088994 |
| Scope | Clean local artifacts and disposable container proof; no NAS bind or production switch |

## Scope and acceptance

1. Build from exact clean committed OPS-019 source 4088994, version 0.2.1. Record
   wheel/sdist, locked dependency closure, base and final application image
   hashes. Build both service images under decision 129's all-FROM UBI micro
   contract; old Alpine Caddy is ineligible. Verify only the approved external
   binary/Red Hat CA donors. The app builder independently authenticates required
   --python-archive; the dedicated Caddy builder verifies fresh-inode binary and
   empty capabilities. Repeat actual app foundation and Caddy ancestry/hash/CA
   acceptance against these clean images; dirty preview results cannot replace
   it. Do not pull or publish unrelated runtime inputs.
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
   Separately repeat served verified fixture TLS/Unix upstream, REST/MCP class
   denials, exact registry and protected-reader container CLI checks against the
   clean app/Caddy pair, preserving unchanged local state and no admitted jobs.
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
[127](../../adr/decision-127.md), [128](../../adr/decision-128.md),
[129](../../adr/decision-129.md), [release](../../agents/release.md),
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

### Fresh UBI activation

2026-10-18: Reactivated only after OPS-019 committed as
4088994f2b1e02f00a3c1e47cb8ebe662ca64a1b. Root uses clean detached checkout
/var/tmp/hfcache-rel013-ubi-source at that exact source; all final artifacts,
contexts, proof captures and new gate logs use .scratch/rel-013-ubi-* outside it.
Normal ignored gate environments/build outputs may remain inside the clean
checkout; tracked Git state and immutable app/package inputs must stay unchanged.
Main-workspace Markdown records activation/evidence only. Root reviews delegated
actual proof scripts before execution and owns protected stage operations.

Repeat both clean UBI builds and every accepted foundation, notify/container-peer,
isolation, served-TLS, compatibility, simulated-NFS complete-domain and full-gate
check. Superseded Debian outputs below remain untouched and ineligible. No
production switch or NAS I/O/jobs; OPS-018 and hold 22 stay pending.

### Superseded Debian execution history

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

## Fresh UBI build and acceptance evidence

Actual clean wheel/sdist builds exit 0 from immutable source 4088994:

| Artifact | SHA256 |
| --- | --- |
| .scratch/rel-013-ubi-artifacts/hfcache-0.2.1-py3-none-any.whl | 2ffc0980a76603b5eeafec2a4f0a1fe2151fc58135b7c7107aec3bbf8cc2be7d |
| .scratch/rel-013-ubi-artifacts/hfcache-0.2.1.tar.gz | 2ee02fdb80e6a3c87b6f250b69d1bf54bb613ac50fffc71939e1689ddc215ac8 |

The dedicated Caddy builder is actually rerun from clean4088994, with new context,
tag and finite probe, and exits 0. It produces cached exact image
sha256:fa2a5634a525af798ce6da2855d365f7cdf0f9a2d6d0eb56d461626e226acc10;
this is a new clean build/proof, not promotion of a dirty preview. Record
.scratch/rel-013-ubi-caddy-build/build.json states source_dirty=false; retained
probe1ce6ba35a53856d07c0f56d19cc69e1fdc14565b13eb39368c48b04bacb8335b
is stopped/exit0. The app build and all remaining clean acceptance are pending.

Fresh clean-source NAS-masked --with-build gate starts as
hfcache-rel013-ubi-gate, invocation 87e859d2ebd041919601316404af726c,
log .scratch/rel-013-ubi-gate.log. No final gate result is claimed until its actual
process exit. Earlier superseded gate/artifacts remain intact.

### Clean app and actual UBI fixture acceptance

Actual app build exits 0: image
sha256:e0ddb59be54236ba0853fe73578a9af0ec7b454159af511ea6d620c9f7b2e030,
source 4088994/source_dirty=false. Locked closure remains f1c9…; requirements
SHA256 74ce95cbb7237bd2aaa575b9b8f82ff8b1da0015ac5afa063bf536955bf38cc7.
Every proof below actually exits 0 against the clean app/Caddy pair:

| Evidence path | SHA256 |
| --- | --- |
| /var/tmp/hfcache-rel013-ubi-foundation/proof.json | 76c6a3e0dd22027fdf49f8350b5dfde7aae99a13c7504ad5d518b966f45a49e3 |
| /var/tmp/hfcache-rel013-ubi-worker/proof.json | 8d36a2907ca67d65f1f7754b8e3c6813624b9cef97b068905afdf49add6ff862 |
| /var/tmp/hfcache-rel013-ubi-stack/proof.json | 9917cec5447be43ab3318a4eb0e46d255c3cf351a1229736b6c8315652cf3eec |
| /var/tmp/hfcache-rel013-ubi-compat/summary.json | 5cc7f88eadfd1d15f6ee85d89c2efb7d7abd1f28cd10b36e7f79b44087ce6c4a |
| /var/tmp/hfcache-rel013-ubi-caddy-foundation.json | 12d6e261095588d2e182567524ed0d17a6b8d74952a2186d5e0125e4e2c3f219 |
| .scratch/rel-013-ubi-stack-proof.py | 4d44c90189e90e25cc92cbd2af91fc30b3d8dcb379e2ffb2f40fa1dd992f4865 |

Foundation repeats actual micro ancestry/native/NSS/CA/installer/confinement
checks. Worker proves real notifyPID792984, ordinary container-origin peer under
Enforcing, PID1/FD3/isolation and IPv4/IPv6 denial errno38; exact drain removes
only owned socket inode138320199. Stack proves verified synthetic-CA TLS/Unix
REST, class denials, nine MCP tools and protected-reader CLI, with unchanged
state/no admitted jobs/NAS and all three stack roles stopped/exit0. Its reviewed
script checks clean source/provenance before importing helpers. Caddy's actual
micro RootFS diff-ID prefix is independently verified. Compatibility repeats
126 actual observations with all 18 shared golden inputs preserved.

These clean fixture results replace no historical failure and do not close
installed hold22. Simulated-NFS complete-domain, protected staging/host-control
readers and actual full-gate completion still await results.

### Local OCI export and pending protected stage

Local-only OCI exports complete:

| Export | SHA256 |
| --- | --- |
| .scratch/rel-013-ubi-app.oci.tar | e0557e1d6762bd268a28e2982e672189ab57004f0db783a45425dbb6074ee9ad |
| .scratch/rel-013-ubi-caddy.oci.tar | e6abb602dca62792fc9f4881001239d37e8fb41f8527244567a31a0062034c15 |

They are not yet root-copied, loaded into the service engine or selected. Five
fresh proof files are copied byte-for-byte under
.scratch/rel-013-ubi-artifacts/proofs. Protected staging awaits the remaining
domain/gate/build outputs. Reviewed domain-driver execution uses local fixtures
only; no application source change or production acceptance follows from it.

### Simulated-NFS complete-domain proof

The first actual clean-UBI domain attempt exits 0 against app e0ddb59b…:
/var/tmp/hfcache-rel013-ubi-domain/proof.json SHA256
f0ebb24f85c1fc6a32886b51ae2c981aa3fc4f92f25198ab0d143ae43e6a26dd;
.scratch/rel-013-ubi-domain.log SHA256
f7dfd0dc36cbc7b318d852d9edadd38bab459c40422e09fdfbefee365d1e0c42.
Real HTTP API/private-worker new/full/revision modes each succeed/exit0; deliberate
damage to the owned local fixture yields exact terminal integrity exit40. All
four cases preserve receipt/domain IDs, archive UUID/fingerprint, same-key retry
without new admission, lookup and exact result. API and worker stores each retain
four receipts/four results/.lock. Seven containers remain stopped/exit0; five
mode0600 lock inodes remain and both sockets are removed after joined drain.
Worker/API/setup diagnostics are empty.

Root reviews both driver scripts before execution. The sole simulated-NFS
storage.MOUNT_TABLE seam occurs after actual cold audit/FD3/offline setup, with
Hub/credential tripwires retained; proof-only HF_XET_LOG_DEST=/dev/null changes no
image/default environment. This proves local domain behavior, not real NAS,
deterministic active-observer drop/restart or user-manager readiness attribution.
The separate unmodified worker proof establishes actual notify/SELinux/isolation;
source/full-suite observer/reconciliation proofs remain distinct. No production
archive operation, read or job is submitted.

### Protected staging and control-reader proof

Root reviews/runs the assembler: 50 files, 1,607,808 bytes, with exact manifest
SHA256 ab6c094292b05d99abbf5b8fb852b1a57a43e845041f00cc0cb94dcb8ef2e042.
Actual protected stage exits 0 using the reviewed installer and umask 022 under
/opt/hfcache/releases/0.2.1. Index covers 64 files, SHA256
5baaa5e1cfc5a7d6b84a96ecb5c5ceac80ee56af0bd0f65b74b18d921efa9c9e;
worker policy remains unchanged 08f97…. Actual UID/GID 981 opens and verifies all
64 indexed files and 15 mode 0755 directories. Current remains 0.2.0; images are
not loaded into its service engine and no selector/runtime change occurs.

| Protected evidence under /opt/hfcache/deployment/20261018-worker-0.2.1 | SHA256 |
| --- | --- |
| service-access.json | 21f66c69e99b3d4e2e5ee56a97b83f83f4c65a3b1bebabb332608c2e5fa037c0 |
| control-readers.json | 5e4a2e37c56b26810d6452c1d7d56a07990c2be4fb98907330d270ecefd7b3da |
| stage.log | 2cf1f028a0444f0f0d112dca7fc98831d32b2aae32b6a84092c073402a85a6e4 |

The actual protected control-reader matrix passes 36 cases: previous 0.2.0/current
0.2.1 × both origins × schema 1/future 2/malformed × three families. Entire old/new
stages and fixture bytes remain preserved. Root reviews the driver before
execution; this host-control proof grants no application/NAS operations.

## Completion evidence

Completed 2026-10-18, REL-013, this commit. Exact clean committed source is
4088994f2b1e02f00a3c1e47cb8ebe662ca64a1b, not this later evidence commit.
Wheel/sdist, both UBI images, closure/foundation/CA/binary/provenance, protected
manifest/index and service access identities are recorded above. Fresh actual
foundation, notify/container-origin peer/isolation/cleanup, served fixtureTLS,
126 compatibility observations and separately labeled simulated-NFS HTTP domain
proof all pass. All prior Debian/dirty/stopped/failed evidence remains distinct.
Clean source stays Git-clean; immutable application/package inputs do not change.

Fresh clean-source NAS-masked `scripts/check.sh --with-build` actually exits 0,
invocation 87e859d2ebd041919601316404af726c, elapsed 9m38.319s:

- 423 formatted files; Ruff/lint and whole types 0;
- 4,057 Python passed, 40 deselected in 510.38s;
- actual locked base/server/server+MCP wheel installation/import/help profiles;
- Cockpit lint/style/types, 135 tests in 2,290.408886ms and production build 1,422ms;
- four extra wheel smokes in 7.32s.

Log .scratch/rel-013-ubi-gate.log SHA256
17c19e61f1c4fd4afb7a5a78d9b6650c2d41efc72c23a2b48f58b89764675c83.
Reviewed INV-002/003/005–007/010–016, AD-16/17/21, FS/TX and decisions 65/75/79/
115/121/126–129; no new architecture, dependency, schema or domain change.
[Progress audit](../../progress.md), task/plan/current, local links and whitespace
reconcile. OPS-018 stays pending until this evidence package commits.

These are clean artifact/disposable-fixture/stage results, not installed worker
acceptance or a 0.2.1 deployment/tag. Production 0.2.0/hold 22, permanent guard
PID 717169/original locks, system target, NAS-ro/writer masks/stores/handles and
all forbidden NAS file I/O/jobs, other-host and remote actions remain unchanged.
